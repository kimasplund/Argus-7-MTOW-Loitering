"""Tests for argus7.aero.neural -- the batched, GPU-resident NeuralFoil surrogate.

Two things are being tested here and they must not be confused:

1. CORRECTNESS OF THE PORT. argus7.aero.neural re-implements NeuralFoil's
   forward pass in torch so it can live on the GPU and take large batches.
   That port must agree with the reference `neuralfoil` package to within
   float32 round-off. This is a *tight* assertion -- it is the same network,
   the same weights and the same arithmetic, so any real disagreement is a bug
   in the port.

2. AGREEMENT BETWEEN NEURALFOIL AND XFOIL. This is NOT a correctness test.
   They are different methods (a regression of a viscous panel code vs. the
   viscous panel code itself), and NeuralFoil's own documentation quotes
   errors of order a few percent in CD against XFOIL. The XFOIL test below
   therefore RECORDS the discrepancy, prints it, and asserts only a loose,
   explicitly-stated band. A human reads the printed numbers to judge.

Run with -s to see the printed benchmark and comparison tables.
"""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import pytest
import torch

from argus7.cad.airfoil_coords import load_airfoil
from argus7.design.schema import load_design
from argus7.design.geometry import derive_wing

import argus7.aero.neural as neural
from argus7.aero.neural import (
    CONFIDENCE_WARN_THRESHOLD,
    NeuralFoilSurrogate,
    PolarResult,
    get_surrogate,
    polar,
    validate_against_xfoil,
)

REPO = Path(__file__).resolve().parents[1]
DESIGN = REPO / "design" / "argus7_v1.yaml"

# Baseline loiter point, from the verified baseline in the programme brief:
# CL 1.21 at 4000 m. Root-chord Reynolds number 992372 and mid-span 486526 are
# the two Re values at which the XFOIL x_tr results were verified.
LOITER_CL = 1.21
RE_ROOT = 992372.0
RE_MID = 486526.0

# ISA at the 4000 m loiter altitude: rho = 0.81935 kg/m3, mu = 1.6612e-5 Pa.s
# (Sutherland at T = 262.17 K), so nu = mu/rho. Used only to check that the
# programme's established Reynolds numbers are consistent with the chords the
# design file actually implies -- nothing in argus7.aero.neural needs it.
NU_ISA_4000M = 1.6612e-5 / 0.81935          # m2/s
# Verified baseline loiter TAS band, 99-128 km/h.
TAS_BAND_MS = (99.0 / 3.6, 128.0 / 3.6)


@pytest.fixture(scope="module")
def coords() -> np.ndarray:
    """FX 63-137 in Selig order, via the project's own loader."""
    return load_airfoil("fx63137")


@pytest.fixture(scope="module")
def surrogate(coords) -> NeuralFoilSurrogate:
    return NeuralFoilSurrogate(coords, model_size="xxxlarge")


# --- 1. Shape / batching correctness ----------------------------------------

def test_scalar_inputs_give_zero_d_arrays(coords):
    r = polar(coords, alpha=3.0, Re=RE_ROOT)
    assert isinstance(r, PolarResult)
    for a in (r.CL, r.CD, r.CM, r.analysis_confidence):
        assert isinstance(a, np.ndarray)
        assert a.shape == ()


def test_1d_batch_shape(coords):
    alpha = np.linspace(-2.0, 8.0, 17)
    r = polar(coords, alpha=alpha, Re=RE_ROOT)
    assert r.CL.shape == (17,)
    assert r.CD.shape == (17,)
    assert r.CM.shape == (17,)
    assert r.analysis_confidence.shape == (17,)
    assert r.low_confidence.shape == (17,)


def test_broadcast_grid_shape(coords):
    alpha = np.linspace(-2.0, 8.0, 11)[:, None]     # (11, 1)
    Re = np.geomspace(2e5, 2e6, 7)[None, :]         # (1, 7)
    r = polar(coords, alpha=alpha, Re=Re)
    assert r.CL.shape == (11, 7)
    assert r.CD.shape == (11, 7)
    assert r.CM.shape == (11, 7)
    assert r.analysis_confidence.shape == (11, 7)


def test_list_inputs_accepted(coords):
    r = polar(coords, alpha=[0.0, 2.0, 4.0], Re=[3e5, 6e5, 1.2e6])
    assert r.CL.shape == (3,)


def test_incompatible_shapes_raise(coords):
    with pytest.raises(ValueError):
        polar(coords, alpha=np.zeros(5), Re=np.zeros(4))


def test_chunking_does_not_change_results(surrogate):
    """Chunk size must not change the answer beyond float32 round-off.

    Not bitwise: cuBLAS selects different reduction kernels for different
    batch sizes, so a 10000-case chunk and a 37-case chunk accumulate in a
    different order. Anything above ~1e-5 in CL would be a real bug (e.g. a
    chunk boundary mis-indexing the batch), not arithmetic.
    """
    alpha = np.linspace(-4.0, 10.0, 501)
    a = surrogate.polar(alpha=alpha, Re=RE_ROOT, max_chunk=10_000)
    b = surrogate.polar(alpha=alpha, Re=RE_ROOT, max_chunk=37)
    print("\n[chunking] max |dCL| = %.2e, max |dCD|/CD = %.2e"
          % (np.max(np.abs(a.CL - b.CL)), np.max(np.abs(a.CD / b.CD - 1.0))))
    np.testing.assert_allclose(a.CL, b.CL, rtol=0, atol=1e-5)
    np.testing.assert_allclose(a.CD, b.CD, rtol=1e-4, atol=0)


# --- 2. The torch port must reproduce the reference neuralfoil package ------

def test_port_matches_reference_neuralfoil(coords):
    """Same network, same weights -> agreement to float32 round-off."""
    import neuralfoil as nf

    alpha = np.linspace(-4.0, 12.0, 25)
    ref = nf.get_aero_from_coordinates(
        coordinates=coords, alpha=alpha, Re=RE_ROOT, model_size="xxxlarge"
    )
    got = polar(coords, alpha=alpha, Re=RE_ROOT, model_size="xxxlarge")

    print("\n[port vs reference neuralfoil, FX 63-137, Re %.0f, xxxlarge]" % RE_ROOT)
    print("  max |dCL|   = %.3e" % np.max(np.abs(got.CL - ref["CL"])))
    print("  max |dCD|   = %.3e" % np.max(np.abs(got.CD - ref["CD"])))
    print("  max |dCM|   = %.3e" % np.max(np.abs(got.CM - ref["CM"])))
    print("  max |dconf| = %.3e"
          % np.max(np.abs(got.analysis_confidence - ref["analysis_confidence"])))

    np.testing.assert_allclose(got.CL, ref["CL"], rtol=1e-4, atol=1e-5)
    np.testing.assert_allclose(got.CD, ref["CD"], rtol=1e-3, atol=1e-6)
    np.testing.assert_allclose(got.CM, ref["CM"], rtol=1e-4, atol=1e-5)
    np.testing.assert_allclose(
        got.analysis_confidence, ref["analysis_confidence"], rtol=1e-3, atol=1e-4
    )


def test_port_matches_reference_over_re_range(coords):
    import neuralfoil as nf

    Re = np.geomspace(1e5, 5e6, 12)
    ref = nf.get_aero_from_coordinates(
        coordinates=coords, alpha=4.0, Re=Re, model_size="xxxlarge"
    )
    got = polar(coords, alpha=4.0, Re=Re, model_size="xxxlarge")
    np.testing.assert_allclose(got.CL, ref["CL"], rtol=1e-4, atol=1e-5)
    np.testing.assert_allclose(got.CD, ref["CD"], rtol=1e-3, atol=1e-6)


def test_model_size_is_honoured(coords):
    """A different model_size must actually load a different network."""
    import neuralfoil as nf

    for size in ("medium", "xxxlarge"):
        ref = nf.get_aero_from_coordinates(
            coordinates=coords, alpha=3.0, Re=RE_ROOT, model_size=size
        )
        got = polar(coords, alpha=3.0, Re=RE_ROOT, model_size=size)
        assert got.CL == pytest.approx(float(ref["CL"][0]), rel=1e-4, abs=1e-5)

    a = polar(coords, alpha=3.0, Re=RE_ROOT, model_size="medium").CD
    b = polar(coords, alpha=3.0, Re=RE_ROOT, model_size="xxxlarge").CD
    assert float(a) != float(b), "model_size appears to be ignored"


def test_unknown_model_size_raises(coords):
    with pytest.raises(ValueError):
        polar(coords, alpha=0.0, Re=RE_ROOT, model_size="gargantuan")


# --- 3. CUDA path -----------------------------------------------------------

def test_cuda_path_matches_cpu(coords):
    if not torch.cuda.is_available():
        pytest.skip("no CUDA device available")
    alpha = np.linspace(-2.0, 10.0, 64)
    cpu = polar(coords, alpha=alpha, Re=RE_ROOT, device="cpu")
    gpu = polar(coords, alpha=alpha, Re=RE_ROOT, device="cuda")
    print("\n[cuda] device = %s" % torch.cuda.get_device_name(0))
    print("  max |dCL| cpu-vs-cuda = %.3e" % np.max(np.abs(cpu.CL - gpu.CL)))
    print("  max |dCD| cpu-vs-cuda = %.3e" % np.max(np.abs(cpu.CD - gpu.CD)))
    np.testing.assert_allclose(gpu.CL, cpu.CL, rtol=1e-4, atol=1e-5)
    np.testing.assert_allclose(gpu.CD, cpu.CD, rtol=1e-3, atol=1e-6)


def test_weights_are_resident_on_the_requested_device(coords):
    if not torch.cuda.is_available():
        pytest.skip("no CUDA device available")
    s = NeuralFoilSurrogate(coords, model_size="xxxlarge", device="cuda")
    assert s.device.type == "cuda"
    assert all(w.device.type == "cuda" for w in s.weights)
    # Weights are uploaded once, at construction -- not per call.
    ids_before = [id(w) for w in s.weights]
    s.polar(alpha=np.linspace(0, 5, 32), Re=RE_ROOT)
    assert [id(w) for w in s.weights] == ids_before


# --- 3b. Surrogate reuse: the point of the module ---------------------------

def test_surrogate_is_cached_across_calls(coords):
    """polar() must not refit the CST weights or re-upload the network.

    If this ever regresses the module still gives right answers, just slowly
    -- exactly the kind of silent performance loss an optimiser inner loop
    would absorb without complaining.
    """
    a = get_surrogate(coords, model_size="xxxlarge")
    b = get_surrogate(coords, model_size="xxxlarge")
    assert a is b
    assert get_surrogate(coords, model_size="medium") is not a


def test_surrogate_cache_is_bounded(coords):
    """A geometry-varying optimiser must not accumulate GPU weight sets."""
    rng = np.random.default_rng(1)
    for _ in range(neural._CACHE_MAX_ENTRIES + 4):
        perturbed = coords.copy()
        perturbed[1:-1, 1] += rng.normal(0.0, 1e-4, perturbed.shape[0] - 2)
        get_surrogate(perturbed, model_size="medium")
    assert len(neural._CACHE) <= neural._CACHE_MAX_ENTRIES


# --- 4. Physics sanity: monotonic CL in the linear range --------------------

def test_cl_monotonic_with_alpha_in_linear_range(surrogate):
    alpha = np.linspace(-3.0, 6.0, 37)
    r = surrogate.polar(alpha=alpha, Re=RE_ROOT)
    dCL = np.diff(r.CL)
    assert np.all(dCL > 0.0), f"CL not monotonic: min dCL = {dCL.min()}"
    # Lift slope should be in the ballpark of thin-airfoil 2*pi/rad = 0.11/deg.
    slope = np.polyfit(alpha, r.CL, 1)[0]
    print("\n[linear range] dCL/dalpha = %.4f /deg (thin-airfoil 0.110)" % slope)
    assert 0.08 < slope < 0.16


def test_cm_is_strongly_negative_as_established(surrogate):
    """Established fact: FX 63-137 C_M is about -0.214 (NeuralFoil, Re 992k)."""
    r = surrogate.polar(alpha=_alpha_for_cl(surrogate, LOITER_CL, RE_ROOT), Re=RE_ROOT)
    print("\n[loiter] CL=%.3f -> CM=%.4f (established: about -0.214)"
          % (float(r.CL), float(r.CM)))
    assert -0.30 < float(r.CM) < -0.15


def test_established_reynolds_numbers_are_consistent_with_the_design_file(surrogate):
    """The Re values used above are not free-floating constants.

    Geometry comes from design/argus7_v1.yaml via the loaders, never hardcoded:
    the established root-chord Re of 992372 must imply a loiter TAS inside the
    verified 99-128 km/h band when divided by the root chord the design file
    actually gives.
    """
    wing = derive_wing(load_design(DESIGN).wing)
    v_root = RE_ROOT * NU_ISA_4000M / wing.chord_root_m
    print("\n[design consistency] chord_root = %.4f m, mac = %.4f m"
          % (wing.chord_root_m, wing.mac_m))
    print("  Re_root %.0f -> TAS %.2f m/s (%.1f km/h); band is %.1f-%.1f km/h"
          % (RE_ROOT, v_root, v_root * 3.6,
             TAS_BAND_MS[0] * 3.6, TAS_BAND_MS[1] * 3.6))
    assert TAS_BAND_MS[0] <= v_root <= TAS_BAND_MS[1]

    # Same flight condition, MAC instead of root chord.
    re_mac = v_root * wing.mac_m / NU_ISA_4000M
    a = _alpha_for_cl(surrogate, LOITER_CL, re_mac)
    r = surrogate.polar(alpha=a, Re=re_mac)
    print("  at MAC: Re = %.0f, alpha = %.2f deg for CL = %.2f -> CD = %.5f, "
          "L/D_2D = %.1f, confidence = %.3f"
          % (re_mac, a, LOITER_CL, float(r.CD), LOITER_CL / float(r.CD),
             float(r.analysis_confidence)))
    assert float(r.analysis_confidence) >= CONFIDENCE_WARN_THRESHOLD


# --- 5. Low-confidence flagging --------------------------------------------

def test_low_confidence_is_flagged_not_silently_trusted(coords):
    # Deep stall / far outside the training distribution.
    r = polar(coords, alpha=[2.0, 45.0], Re=[RE_ROOT, RE_ROOT])
    assert r.low_confidence[1], "alpha=45 deg should not be trusted"
    assert r.warnings, "a low-confidence result must carry a warning"
    assert "confidence" in r.warnings[0].lower()
    print("\n[confidence] alpha=2 -> %.3f, alpha=45 -> %.3f; warning: %s"
          % (r.analysis_confidence[0], r.analysis_confidence[1], r.warnings[0]))


def test_loiter_point_is_confident(surrogate):
    a = _alpha_for_cl(surrogate, LOITER_CL, RE_ROOT)
    r = surrogate.polar(alpha=a, Re=RE_ROOT)
    assert float(r.analysis_confidence) >= CONFIDENCE_WARN_THRESHOLD
    assert not r.warnings


# --- 6. Throughput benchmark ------------------------------------------------

def test_throughput_benchmark(surrogate, coords):
    import neuralfoil as nf

    rng = np.random.default_rng(0)
    n = 200_000
    alpha = rng.uniform(-4.0, 10.0, n)
    Re = np.exp(rng.uniform(np.log(2e5), np.log(2e6), n))

    surrogate.polar(alpha=alpha[:1024], Re=Re[:1024])       # warm-up / autotune
    surrogate.synchronize()

    t0 = time.perf_counter()
    r = surrogate.polar(alpha=alpha, Re=Re)
    surrogate.synchronize()
    dt = time.perf_counter() - t0
    rate = n / dt

    n_ref = 2_000
    t0 = time.perf_counter()
    nf.get_aero_from_coordinates(
        coordinates=coords, alpha=alpha[:n_ref], Re=Re[:n_ref], model_size="xxxlarge"
    )
    ref_rate = n_ref / (time.perf_counter() - t0)

    print("\n[throughput] device=%s model=xxxlarge" % surrogate.device)
    print("  argus7.aero.neural : %10.0f evaluations/s  (%d cases in %.3f s)"
          % (rate, n, dt))
    print("  reference neuralfoil: %10.0f evaluations/s  (%d cases)"
          % (ref_rate, n_ref))
    print("  speed-up: %.1fx" % (rate / ref_rate))

    assert r.CL.shape == (n,)
    floor = 20_000.0 if surrogate.device.type == "cuda" else 2_000.0
    assert rate > floor, f"only {rate:.0f} evals/s on {surrogate.device}"


# --- 7. XFOIL comparison (recorded, loosely banded) -------------------------

# Loose acceptance band for a NeuralFoil-vs-XFOIL comparison. These are
# DIFFERENT METHODS: NeuralFoil is a neural regression trained on XFOIL runs,
# so it carries both training error and the scatter of XFOIL's own convergence.
# NeuralFoil's own README quotes ~a few percent CD error for the larger models.
# We allow 30% on CD, 0.15 on CL and 0.06 on CM -- wide enough that this test
# is a smoke test for "the two codes describe the same airfoil", not an
# accuracy assertion. The measured numbers are printed for a human to judge.
XFOIL_CD_REL_BAND = 0.30
XFOIL_CL_ABS_BAND = 0.15
XFOIL_CM_ABS_BAND = 0.06


def test_validate_against_xfoil_records_discrepancies(coords):
    pytest.importorskip("argus7.aero.xfoil_driver")

    alphas = (0.0, 2.0, 4.0, 6.0)
    rows = validate_against_xfoil(
        "fx63137", alpha=alphas, Re=RE_ROOT, model_size="xxxlarge"
    )

    print("\n[NeuralFoil vs XFOIL] FX 63-137, Re %.0f, Ncrit 9, N=%d panels"
          % (RE_ROOT, neural.XFOIL_PANELS))
    print("  %5s | %8s %8s %7s | %9s %9s %8s | %8s %8s | %s"
          % ("alpha", "CL_nf", "CL_xf", "dCL", "CD_nf", "CD_xf", "dCD%",
             "CM_nf", "dCM", "xfoil"))
    for row in rows:
        print("  %5.1f | %8.4f %8.4f %+7.4f | %9.6f %9.6f %+8.2f | %8.4f %+8.4f | %s"
              % (row["alpha"], row["CL_neural"], row["CL_xfoil"], row["dCL"],
                 row["CD_neural"], row["CD_xfoil"], 100.0 * row["dCD_rel"],
                 row["CM_neural"], row["dCM"],
                 "converged" if row["converged"] else "NOT CONVERGED"))

    assert len(rows) == len(alphas)

    # XFOIL itself does not converge at every point on this section: at
    # Re ~1e6 the FX 63-137's upper-surface transition limit-cycles, and some
    # alphas sit at rms ~3e-3 after 300 iterations instead of ~1e-5. That is
    # XFOIL's behaviour, not a defect in this module, so non-converged points
    # are reported and then excluded from the band rather than asserted on.
    ok = [row for row in rows if row["converged"]]
    n_bad = len(rows) - len(ok)
    if n_bad:
        print("  (%d of %d XFOIL points did not converge in 300 iterations and "
              "are excluded from the band)" % (n_bad, len(rows)))
    assert len(ok) >= 3, "too few converged XFOIL points to compare against"

    dCD_rel = np.array([row["dCD_rel"] for row in ok])
    dCL = np.array([row["dCL"] for row in ok])
    dCM = np.array([row["dCM"] for row in ok])
    print("  summary over %d converged points: max|dCD| = %.1f%%, "
          "mean dCD = %+.1f%%, max|dCL| = %.4f, max|dCM| = %.4f"
          % (len(ok), 100 * np.max(np.abs(dCD_rel)), 100 * np.mean(dCD_rel),
             np.max(np.abs(dCL)), np.max(np.abs(dCM))))
    print("  bands asserted (loose, two different methods): |dCD| < %.0f%%, "
          "|dCL| < %.2f, |dCM| < %.3f"
          % (100 * XFOIL_CD_REL_BAND, XFOIL_CL_ABS_BAND, XFOIL_CM_ABS_BAND))

    assert np.max(np.abs(dCD_rel)) < XFOIL_CD_REL_BAND
    assert np.max(np.abs(dCL)) < XFOIL_CL_ABS_BAND
    assert np.max(np.abs(dCM)) < XFOIL_CM_ABS_BAND


def test_validate_against_xfoil_reports_confidence_and_convergence(coords):
    """Every recorded row must carry the caveats, not just the numbers."""
    pytest.importorskip("argus7.aero.xfoil_driver")
    rows = validate_against_xfoil("fx63137", alpha=(4.0,), Re=RE_ROOT)
    assert len(rows) == 1
    for key in ("analysis_confidence", "low_confidence", "converged",
                "dCL", "dCD", "dCD_rel", "dCM"):
        assert key in rows[0]
    assert 0.0 <= rows[0]["analysis_confidence"] <= 1.0


def test_validate_against_xfoil_accepts_an_injected_runner(coords):
    """The XFOIL side is injectable, so the comparison logic is testable
    without spending an XFOIL run and without depending on a sibling module
    that is still under development."""
    def fake(airfoil_name, alphas, Re, n_crit, n_panels):
        assert airfoil_name == "fx63137"
        assert n_panels >= 280            # rule (d) floor must be honoured
        assert n_crit == pytest.approx(9.0)
        return [{"CL": 1.0, "CD": 0.01, "CM": -0.2, "converged": True}
                for _ in alphas]

    rows = validate_against_xfoil("fx63137", alpha=(2.0, 4.0), Re=RE_ROOT,
                                  runner=fake)
    assert len(rows) == 2
    assert rows[0]["CL_xfoil"] == 1.0
    assert rows[0]["dCD"] == pytest.approx(rows[0]["CD_neural"] - 0.01)
    assert rows[0]["dCD_rel"] == pytest.approx((rows[0]["CD_neural"] - 0.01) / 0.01)


def test_validate_against_xfoil_rejects_a_short_runner_result(coords):
    def short(airfoil_name, alphas, Re, n_crit, n_panels):
        return [{"CL": 1.0, "CD": 0.01, "CM": -0.2, "converged": True}]

    with pytest.raises(RuntimeError):
        validate_against_xfoil("fx63137", alpha=(2.0, 4.0), Re=RE_ROOT,
                               runner=short)


# --- helpers ----------------------------------------------------------------

def _alpha_for_cl(surrogate: NeuralFoilSurrogate, cl: float, Re: float) -> float:
    """Invert CL(alpha) by interpolation on a fine, monotonic sweep."""
    a = np.linspace(-4.0, 8.0, 241)
    r = surrogate.polar(alpha=a, Re=Re)
    return float(np.interp(cl, r.CL, a))
