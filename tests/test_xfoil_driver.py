"""Tests for the XFOIL driver.

The numeric expectations here are not free parameters -- they are the
verified reference results recorded in ``research/riblets_pack.md`` (§3 and
the reproducibility appendix), produced with XFOIL 6.99 against this
repository's own pinned ``data/airfoils/fx63137.dat``. If a refactor moves
them, the driver changed the physics, not the tests.

Tests that launch the binary are marked ``slow``. They are slow by intent:
they really run XFOIL. Deselect with ``-m "not slow"``.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import pytest

from argus7.cad.airfoil_coords import load_airfoil, max_thickness
from argus7.aero.xfoil_driver import (
    DEFAULT_PANELS,
    DUMP_COLUMNS,
    H_COLUMN,
    H_TURBULENT,
    MIN_PANELS,
    XFoilError,
    XFoilResult,
    build_script,
    check_log,
    invoke_xfoil,
    parse_dump,
    polar_sweep,
    run_xfoil,
    transition_from_dump,
    write_selig_file,
)

# --- Reference conditions -------------------------------------------------
# Root and tip stations of the ten-station heavy-loiter survey in
# research/riblets_pack.md: Re(y) = 35.62*c(y)/2.028e-5 at 4,000 m ISA.
RE_ROOT = 992372.0
RE_TIP = 486526.0
CL_LOITER = 1.21          # C_Lmax/1.15^2 = 1.60/1.3225, stall-constrained loiter C_L
AIRFOIL = "fx63137"

# Verified x_tr (H < 2.0 criterion), C_L = 1.21, Ncrit 9.
XTR_ROOT_N300 = 0.5023
XTR_TIP_N300 = 0.6051
# The silent error the >= 280 panel floor exists to prevent.
XTR_ROOT_PANEL_SWEEP = {160: 0.4508, 200: 0.4833, 260: 0.4965,
                        300: 0.5023, 360: 0.5010}


def _xtr_upper_at_panels(n_panels: int, reynolds: float = RE_ROOT,
                         cl: float = CL_LOITER, ncrit: float = 9) -> float:
    """Run XFOIL at an arbitrary panel count, going *around* the panel guard.

    run_xfoil() refuses n_panels < MIN_PANELS, so demonstrating why that
    guard exists has to use the documented low-level route. That the low
    level is the only way in is itself the point: there is no back door in
    the safe API.
    """
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        write_selig_file(AIRFOIL, d / "af.dat")
        script = build_script("af.dat", reynolds, [("cl", cl)],
                              ["dump000.txt"], n_panels=n_panels, ncrit=ncrit)
        log = invoke_xfoil(script, d)
        check_log(log, n_panels=n_panels, ncrit=ncrit, n_points=1)
        surface, _wake = parse_dump(d / "dump000.txt")
        assert surface.shape[0] == n_panels
        return transition_from_dump(surface)[0]


# ==========================================================================
# Guards -- these hold without ever launching XFOIL
# ==========================================================================

def test_refuses_xfoils_own_default_panel_count():
    """N=160 is XFOIL's PANE default and it is silently wrong. Refuse it."""
    with pytest.raises(XFoilError) as exc:
        run_xfoil(AIRFOIL, RE_ROOT, cl=CL_LOITER, n_panels=160)
    msg = str(exc.value)
    assert "160" in msg and str(MIN_PANELS) in msg
    # The error must explain *why*, or the next person just lowers the floor.
    assert "silent" in msg.lower()


def test_panel_floor_is_inclusive_and_set_where_documented():
    assert MIN_PANELS == 280
    assert DEFAULT_PANELS == 300
    with pytest.raises(XFoilError) as exc:
        run_xfoil(AIRFOIL, RE_ROOT, cl=CL_LOITER, n_panels=MIN_PANELS - 1)
    assert "279" in str(exc.value)
    # MIN_PANELS itself must pass the guard: the failure it raises for a
    # missing operating point proves it got past the panel check.
    with pytest.raises(XFoilError) as exc2:
        run_xfoil(AIRFOIL, RE_ROOT, n_panels=MIN_PANELS)
    assert "cl" in str(exc2.value).lower()


@pytest.mark.parametrize("bad", [
    "data/airfoils/fx63137.dat",
    "/home/kim/projects/Argus-7-MTOW-Loitering/data/airfoils/fx63137.dat",
    "fx63137.dat",
    "./fx63137.DAT",
])
def test_refuses_a_raw_dat_path(bad):
    """XFOIL 6.99 SIGFPEs on the raw UIUC Lednicer .dat. Never pass one."""
    with pytest.raises(XFoilError) as exc:
        run_xfoil(bad, RE_ROOT, cl=CL_LOITER)
    msg = str(exc.value)
    assert ".dat" in msg.lower()
    assert "load_airfoil" in msg          # names the correct route


def test_write_selig_file_also_refuses_a_raw_dat_path(tmp_path):
    with pytest.raises(XFoilError):
        write_selig_file("data/airfoils/fx63137.dat", tmp_path / "af.dat")


def test_requires_exactly_one_of_cl_or_alpha():
    with pytest.raises(XFoilError):
        run_xfoil(AIRFOIL, RE_ROOT)                             # neither
    with pytest.raises(XFoilError):
        run_xfoil(AIRFOIL, RE_ROOT, cl=CL_LOITER, alpha=2.5)    # both


def test_refuses_nonpositive_or_nonfinite_reynolds():
    for bad in (0.0, -1.0, float("nan")):
        with pytest.raises(XFoilError):
            run_xfoil(AIRFOIL, bad, cl=CL_LOITER)


def test_build_script_refuses_long_paths():
    """XFOIL truncates paths in its command line and then cannot find them."""
    with pytest.raises(XFoilError):
        build_script("/tmp/somewhere/af.dat", RE_ROOT, [("cl", 1.0)],
                     ["d.txt"], n_panels=300)
    with pytest.raises(XFoilError):
        build_script("af.dat", RE_ROOT, [("cl", 1.0)],
                     ["/tmp/somewhere/d.txt"], n_panels=300)


def test_build_script_encodes_the_hard_won_rules():
    script = build_script("af.dat", RE_ROOT, [("cl", CL_LOITER)],
                          ["dump000.txt"], n_panels=300, ncrit=9)
    lines = script.split("\n")
    # (b) PLOP SIGFPEs in this build -- it must never be emitted.
    assert "PLOP" not in script and "G F" not in script
    # (c) PPAR re-displays after every parameter: two blank lines to exit.
    i = lines.index("PPAR")
    assert lines[i + 1] == "N 300"
    assert lines[i + 3] == "" and lines[i + 4] == ""
    # VISC must come after the paneling and Ncrit are settled, and the
    # script must never accumulate a polar (PACC silently blocks VISC).
    assert "PACC" not in script
    assert script.index("VISC") > script.index("PPAR")
    assert "ITER 300" in lines


# ==========================================================================
# Selig temp-file writing
# ==========================================================================

def test_write_selig_file_is_labelled_and_selig_ordered(tmp_path):
    path = write_selig_file(AIRFOIL, tmp_path / "af.dat")
    lines = path.read_text().splitlines()
    # A title line XFOIL cannot mistake for a coordinate, then pure pairs.
    with pytest.raises(ValueError):
        float(lines[0].split()[0])
    coords = np.array([[float(v) for v in ln.split()] for ln in lines[1:]])
    assert coords.shape[1] == 2
    # Selig order: TE -> upper -> LE -> lower -> TE.
    assert coords[0, 0] == pytest.approx(1.0, abs=1e-3)
    assert coords[-1, 0] == pytest.approx(1.0, abs=1e-3)
    le = int(np.argmin(coords[:, 0]))
    assert 0 < le < len(coords) - 1
    # No Lednicer point-count header masquerading as a coordinate.
    assert coords[:, 0].max() <= 1.001


def test_write_selig_file_comes_from_load_airfoil_not_the_raw_bytes(tmp_path):
    path = write_selig_file(AIRFOIL, tmp_path / "af.dat")
    expect = load_airfoil(AIRFOIL)
    got = np.array([[float(v) for v in ln.split()]
                    for ln in path.read_text().splitlines()[1:]])
    assert got.shape == expect.shape
    assert np.allclose(got, expect, atol=1e-6)
    # The pinned .dat is Lednicer with a "49. 49." header; the written file
    # must have exactly two fewer points than the raw file has numeric rows.
    raw = (Path(__file__).resolve().parents[1]
           / "data" / "airfoils" / "fx63137.dat").read_text().splitlines()
    numeric = [ln for ln in raw if len(ln.split()) == 2
               and _is_float(ln.split()[0]) and _is_float(ln.split()[1])]
    assert len(numeric) > len(got)      # header + duplicated LE point dropped


def _is_float(s: str) -> bool:
    try:
        float(s)
    except ValueError:
        return False
    return True


def test_naca_names_are_generated_not_loaded(tmp_path):
    """A naca#### name is generated analytically; there is no .dat to load."""
    path = write_selig_file("naca2412", tmp_path / "af.dat")
    coords = np.array([[float(v) for v in ln.split()]
                       for ln in path.read_text().splitlines()[1:]])
    # naca4() rotates the thickness normal to the camber line, so the upper
    # leading edge sits a few 1e-5 ahead of x=0. That is the section, not a bug.
    assert coords[:, 0].min() == pytest.approx(0.0, abs=1e-3)
    assert coords[:, 0].max() == pytest.approx(1.0, abs=1e-3)
    assert max_thickness(coords) == pytest.approx(0.12, abs=0.005)   # the "12"


# ==========================================================================
# DUMP parsing and the transition criterion, on a synthetic dump
# ==========================================================================

def _synthetic_dump() -> np.ndarray:
    """21 nodes: TE -> upper -> LE (row 10) -> lower -> TE, H laminar."""
    d = np.zeros((21, 12))
    d[:11, 1] = np.linspace(1.0, 0.0, 11)     # upper, TE -> LE
    d[11:, 1] = np.linspace(0.1, 1.0, 10)     # lower, LE -> TE
    d[:, H_COLUMN] = 2.5
    return d


def test_dump_column_layout_puts_H_at_index_7():
    assert DUMP_COLUMNS[H_COLUMN] == "H"
    assert DUMP_COLUMNS[:8] == ("s", "x", "y", "Ue/Vinf", "Dstar", "Theta",
                                "Cf", "H")
    assert H_TURBULENT == 2.0


def test_transition_from_dump_reads_H_at_column_index_7():
    d = _synthetic_dump()
    d[3, H_COLUMN] = 99.0        # decoy on the upper surface, aft of the trip
    for row in (4, 5, 6, 7):     # upper rows at x = 0.6, 0.5, 0.4, 0.3
        d[row, H_COLUMN] = 1.5
    up, lo = transition_from_dump(d)
    # Walking the upper surface from the LE aft, x = 0.3 is the first station
    # below H = 2.0.
    assert up == pytest.approx(0.3, abs=1e-6)
    assert lo == pytest.approx(1.0)          # lower never goes turbulent


def test_transition_from_dump_ignores_every_other_column():
    """Cf (index 6) is always below 2.0. Reading it would break everything."""
    d = _synthetic_dump()
    d[:, 6] = 1.0
    d[:, 8] = 1.0
    up, lo = transition_from_dump(d)
    assert up == pytest.approx(1.0)
    assert lo == pytest.approx(1.0)


def test_transition_from_dump_rejects_a_too_narrow_dump():
    with pytest.raises(XFoilError):
        transition_from_dump(np.zeros((10, 6)))


def test_parse_dump_splits_ragged_surface_and_wake_rows(tmp_path):
    p = tmp_path / "dump.txt"
    p.write_text(
        "#    s        x        y     Ue/Vinf    Dstar     Theta      Cf       H\n"
        + "\n".join(" ".join(f"{v:.5f}" for v in ([i * 0.1] * 12))
                    for i in range(4))
        + "\n"
        + "\n".join(" ".join(f"{v:.5f}" for v in ([i * 0.1] * 8))
                    for i in range(3))
        + "\n")
    surface, wake = parse_dump(p)
    assert surface.shape == (4, 12)
    assert wake.shape == (3, 8)


# ==========================================================================
# Log assertions -- the desynchronisation detectors
# ==========================================================================

def test_check_log_rejects_unrecognised_commands():
    with pytest.raises(XFoilError) as exc:
        check_log("XFOIL c>  VISC command not recognized.  Type a \"?\"",
                  n_panels=300, ncrit=9, n_points=1)
    assert "unrecognised" in str(exc.value).lower() or "out of step" in str(exc.value)


def test_check_log_rejects_a_log_that_never_went_viscous():
    log = "Number of panel nodes       300\nNcritT = 9.00\n.OPERia c>\n   1   rms: 1\n"
    with pytest.raises(XFoilError) as exc:
        check_log(log, n_panels=300, ncrit=9, n_points=1)
    assert "INVISCID" in str(exc.value)


def test_check_log_rejects_a_wrong_panel_count():
    log = ".OPERv\n  N  i   Number of panel nodes       160\nNcritT = 9.00\n   1   rms: 1\n"
    with pytest.raises(XFoilError) as exc:
        check_log(log, n_panels=300, ncrit=9, n_points=1)
    assert "160" in str(exc.value) and "PPAR" in str(exc.value)


def test_check_log_rejects_a_wrong_ncrit():
    log = ".OPERv\n  Number of panel nodes       300\n NcritT    =    9.00\n   1   rms: 1\n"
    with pytest.raises(XFoilError):
        check_log(log, n_panels=300, ncrit=11, n_points=1)


def test_check_log_counts_solves_and_ignores_inner_marching_warnings():
    """MRCHUE/MRCHDU failures are normal noise; only VISCAL means failure."""
    log = (".OPERv\n Number of panel nodes       300\n NcritT    =    9.00\n"
           " MRCHUE: Convergence failed at 157  side 1\n"
           "   1   rms: 0.1\n  12   rms: 0.2\n"
           "   1   rms: 0.1\n VISCAL:  Convergence failed\n")
    segments = check_log(log, n_panels=300, ncrit=9, n_points=2)
    assert len(segments) == 2
    assert "VISCAL" not in segments[0]
    assert "VISCAL" in segments[1]
    with pytest.raises(XFoilError):
        check_log(log, n_panels=300, ncrit=9, n_points=3)


# ==========================================================================
# Real XFOIL runs -- the verified reference results
# ==========================================================================

@pytest.mark.slow
def test_root_station_reproduces_verified_transition():
    r = run_xfoil(AIRFOIL, RE_ROOT, cl=CL_LOITER, n_panels=300, ncrit=9)
    assert isinstance(r, XFoilResult)
    assert r.converged
    assert r.x_tr_upper == pytest.approx(XTR_ROOT_N300, abs=0.01)
    assert r.cl == pytest.approx(CL_LOITER, abs=0.005)
    # C_M about -0.214 by NeuralFoil at this Re; XFOIL agrees to ~0.01.
    assert -0.25 < r.cm < -0.18
    assert 0.006 < r.cd < 0.013
    assert r.cdf + r.cdp == pytest.approx(r.cd, abs=1e-4)
    assert r.dump.shape[0] == 300 and r.dump.shape[1] > H_COLUMN
    assert r.wake.shape[0] > 0
    assert r.n_panels == 300 and r.ncrit == 9 and r.mode == "cl"
    # Lower-surface transition is aft of the upper one on this section.
    assert r.x_tr_lower > r.x_tr_upper
    # The H<2.0 point must lie AFT of XFOIL's own e^N onset, by 3-8 points.
    assert r.xtr_onset_upper < r.x_tr_upper
    assert 0.01 < r.x_tr_upper - r.xtr_onset_upper < 0.10


@pytest.mark.slow
def test_tip_station_reproduces_verified_transition():
    r = run_xfoil(AIRFOIL, RE_TIP, cl=CL_LOITER, n_panels=300, ncrit=9)
    assert r.converged
    assert r.x_tr_upper == pytest.approx(XTR_TIP_N300, abs=0.01)
    # Lower Re -> longer laminar run. Physics, not tuning.
    root = run_xfoil(AIRFOIL, RE_ROOT, cl=CL_LOITER, n_panels=300, ncrit=9)
    assert r.x_tr_upper > root.x_tr_upper


@pytest.mark.slow
def test_panel_count_sensitivity_justifies_the_guard():
    """The guard's own rationale, tested.

    XFOIL's 160-panel default puts transition ~5 points of chord too far
    forward, with no crash and no warning -- the run reports itself as
    perfectly converged.
    """
    coarse = _xtr_upper_at_panels(160)
    fine = _xtr_upper_at_panels(300)
    assert coarse == pytest.approx(XTR_ROOT_PANEL_SWEEP[160], abs=0.01)
    assert fine == pytest.approx(XTR_ROOT_PANEL_SWEEP[300], abs=0.01)
    # "measurably more forward", and in the direction that flatters the drag.
    assert fine - coarse > 0.03


@pytest.mark.slow
def test_panel_refinement_is_monotone_then_converged():
    """160 -> 300 marches transition aft; 300 -> 360 barely moves it."""
    xtr = {n: _xtr_upper_at_panels(n) for n in XTR_ROOT_PANEL_SWEEP}
    for n, expect in XTR_ROOT_PANEL_SWEEP.items():
        assert xtr[n] == pytest.approx(expect, abs=0.01), n
    assert xtr[160] < xtr[200] < xtr[260] < xtr[300]
    assert abs(xtr[360] - xtr[300]) < 0.01          # converged by 300
    # Everything at or above the floor is within tolerance of the answer;
    # everything below it is not.
    assert abs(xtr[160] - xtr[300]) > 0.01
    assert abs(xtr[200] - xtr[300]) > 0.01


@pytest.mark.slow
def test_alpha_mode_runs_and_reports_cl():
    r = run_xfoil(AIRFOIL, RE_ROOT, alpha=2.58, n_panels=300, ncrit=9)
    assert r.converged and r.mode == "alpha"
    assert r.alpha_deg == pytest.approx(2.58, abs=1e-3)
    assert r.cl == pytest.approx(CL_LOITER, abs=0.05)


@pytest.mark.slow
def test_ncrit_is_actually_applied_not_just_requested():
    """VPAR's Ncrit display precedes the change; the driver re-displays it."""
    low = run_xfoil(AIRFOIL, RE_ROOT, cl=CL_LOITER, ncrit=5)
    high = run_xfoil(AIRFOIL, RE_ROOT, cl=CL_LOITER, ncrit=12)
    assert low.ncrit == 5 and high.ncrit == 12
    # A noisier stream (lower Ncrit) trips earlier. If VPAR silently kept
    # Ncrit 9 for both, these would be identical.
    assert low.x_tr_upper < high.x_tr_upper


@pytest.mark.slow
def test_a_script_without_VISC_is_caught_rather_than_answered_inviscidly():
    """The exact failure PACC-before-VISC produces: no error, wrong physics."""
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        write_selig_file(AIRFOIL, d / "af.dat")
        script = build_script("af.dat", RE_ROOT, [("cl", CL_LOITER)],
                              ["dump000.txt"], n_panels=300, ncrit=9)
        broken = "\n".join(ln for ln in script.split("\n")
                           if not ln.startswith("VISC"))
        log = invoke_xfoil(broken, d)
        # XFOIL is perfectly happy: it just answers the wrong question.
        assert "not recognized" not in log
        with pytest.raises(XFoilError) as exc:
            check_log(log, n_panels=300, ncrit=9, n_points=1)
        assert "INVISCID" in str(exc.value)


@pytest.mark.slow
def test_one_blank_line_after_PPAR_is_caught():
    """Rule (c): a single blank leaves the script one prompt out of step."""
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        write_selig_file(AIRFOIL, d / "af.dat")
        script = build_script("af.dat", RE_ROOT, [("cl", CL_LOITER)],
                              ["dump000.txt"], n_panels=300, ncrit=9)
        lines = script.split("\n")
        del lines[lines.index("PPAR") + 3]        # drop one of the two blanks
        log = invoke_xfoil("\n".join(lines), d)
        with pytest.raises(XFoilError):
            check_log(log, n_panels=300, ncrit=9, n_points=1)


@pytest.mark.slow
def test_non_convergence_raises_by_default_and_is_reportable():
    # Deep into the stall on a starved iteration budget: will not converge.
    with pytest.raises(XFoilError) as exc:
        run_xfoil(AIRFOIL, RE_ROOT, cl=2.4, n_panels=300, max_iter=5)
    assert "converge" in str(exc.value).lower()
    r = run_xfoil(AIRFOIL, RE_ROOT, cl=2.4, n_panels=300, max_iter=5,
                  require_converged=False)
    assert r.converged is False


@pytest.mark.slow
def test_polar_sweep_returns_one_result_per_point():
    cls = [0.8, 1.0, CL_LOITER]
    results = polar_sweep(AIRFOIL, RE_ROOT, cl=cls, n_panels=300, ncrit=9)
    assert len(results) == len(cls)
    assert all(r.converged for r in results)
    assert [r.cl for r in results] == pytest.approx(cls, abs=0.005)
    # Transition marches forward as C_L rises on this NLF section.
    xtr = [r.x_tr_upper for r in results]
    assert xtr[0] > xtr[1] > xtr[2]
    # alpha rises monotonically with C_L, well below the stall
    a = [r.alpha_deg for r in results]
    assert a[0] < a[1] < a[2]
    # A sweep point must equal the same point run on its own: sessions are
    # independent, so no warm-start history can leak between points.
    single = run_xfoil(AIRFOIL, RE_ROOT, cl=CL_LOITER, n_panels=300, ncrit=9)
    assert results[-1].x_tr_upper == pytest.approx(single.x_tr_upper, abs=1e-6)


@pytest.mark.slow
def test_polar_sweep_survives_a_point_that_does_not_converge():
    # C_L 2.4 is far past the section's C_Lmax and will not converge at any
    # iteration budget. The sweep must still return the good point.
    results = polar_sweep(AIRFOIL, RE_ROOT, cl=[1.0, 2.4], n_panels=300)
    assert len(results) == 2
    assert results[0].converged is True
    assert results[1].converged is False
    # The failed point still carries numbers -- they are the last Newton
    # iterate, and they are garbage. This is why require_converged is True by
    # default everywhere except a sweep.
    assert results[0].cl == pytest.approx(1.0, abs=0.005)


def test_polar_sweep_rejects_both_cl_and_alpha():
    with pytest.raises(XFoilError):
        polar_sweep(AIRFOIL, RE_ROOT, cl=[1.0], alpha=[2.0])


def test_polar_sweep_enforces_the_panel_floor_too():
    with pytest.raises(XFoilError):
        polar_sweep(AIRFOIL, RE_ROOT, cl=[1.0], n_panels=160)
