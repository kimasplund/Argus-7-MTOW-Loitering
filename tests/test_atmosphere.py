"""Tests for argus7.mission.atmosphere -- differentiable, batched ISA.

Reference values are the ICAO Standard Atmosphere (ICAO Doc 7488/3, identical to
US Standard Atmosphere 1976 below 32 km), tabulated against GEOPOTENTIAL altitude.
Cross-checked independently against aerosandbox 4.2.10 Atmosphere(method="isa"),
which agrees to < 2e-6 relative on p and rho at 0/4000/11000/20000 m.
"""
import math

import numpy as np
import pytest
import torch

from argus7.mission.atmosphere import (
    Atmosphere,
    EARTH_RADIUS_M,
    GRAVITY_MS2,
    ISA_MAX_ALTITUDE_M,
    LAPSE_RATE_K_PER_M,
    R_AIR_JKGK,
    SUTHERLAND_BETA,
    SUTHERLAND_S_K,
    isa,
    isa_numpy,
    geometric_altitude,
    geopotential_altitude,
)

# ICAO ISA table rows, indexed by geopotential altitude [m], quoted verbatim as
# printed (as strings, so the test can derive the tolerance from the number of
# digits actually published):  H -> (T [K], p [Pa], rho [kg/m3], a [m/s])
ISA_TABLE = {
    0.0:     ("288.150", "101325.0", "1.22500", "340.294"),
    1000.0:  ("281.650",  "89874.6", "1.11164", "336.434"),
    4000.0:  ("262.150",  "61640.2", "0.81913", "324.579"),
    5000.0:  ("255.650",  "54019.9", "0.73612", "320.529"),
    10000.0: ("223.150",  "26436.2", "0.41271", "299.463"),
    11000.0: ("216.650",  "22632.0", "0.36392", "295.069"),
    15000.0: ("216.650",  "12044.6", "0.19367", "295.069"),
    20000.0: ("216.650",   "5474.9", "0.088035", "295.069"),
}

# Slack beyond half a unit in the last printed place.  This is ONLY here because
# several rows land at 0.99 half-ulp (a at 11/15/20 km), where a change of dtype
# or of libm rounding would flip the last digit.  It is deliberately small enough
# that it cannot absorb a wrong constant: at p = 101325 Pa it is 0.1 Pa, whereas
# the smallest constant error worth catching (R to 4 decimals) moves p by ~7 Pa.
# It is NOT a licence to accept another implementation's digits -- every row here
# was recomputed to 40 decimal places from the ICAO constants in the module.
CONSTANTS_SLACK = 1e-6


def _table_tol(printed: str) -> float:
    """Half a unit in the last printed place, plus the constants slack."""
    decimals = len(printed.split(".")[1]) if "." in printed else 0
    return 0.5 * 10.0 ** (-decimals) + CONSTANTS_SLACK * abs(float(printed))


# Sutherland at sea level, ISA reference value [Pa s].
MU_SEA_LEVEL = 1.7894e-5

DEV_CUDA = pytest.mark.skipif(not torch.cuda.is_available(), reason="no CUDA device")


def _t(x, dtype=torch.float64, device="cpu"):
    return torch.as_tensor(x, dtype=dtype, device=device)


# --------------------------------------------------------------------------
# value tests
# --------------------------------------------------------------------------

def test_sea_level_to_four_significant_figures():
    a = isa(_t(0.0))
    assert float(a.temperature_K) == pytest.approx(288.15, rel=1e-4)
    assert float(a.pressure_Pa) == pytest.approx(101325.0, rel=1e-4)
    assert float(a.density_kgm3) == pytest.approx(1.225, rel=1e-4)
    assert float(a.speed_of_sound_ms) == pytest.approx(340.29, rel=1e-4)
    assert float(a.dynamic_viscosity_Pas) == pytest.approx(MU_SEA_LEVEL, rel=1e-4)


@pytest.mark.parametrize("H", sorted(ISA_TABLE))
def test_matches_published_isa_table(H):
    row = ISA_TABLE[H]
    got = isa(_t(H))[:4]
    for printed, value, name in zip(row, got, ("T", "p", "rho", "a")):
        assert float(value) == pytest.approx(float(printed), abs=_table_tol(printed)), name


def test_loiter_altitude_4000m_is_the_designs_operating_point():
    """The ARGUS-7 loiter point. Density ratio drives the whole mission model."""
    a = isa(_t(4000.0))
    sigma = float(a.density_kgm3) / float(isa(_t(0.0)).density_kgm3)
    assert sigma == pytest.approx(0.6687, rel=1e-3)


def test_perfect_gas_and_sound_speed_identities_hold_everywhere():
    h = torch.linspace(0.0, ISA_MAX_ALTITUDE_M, 41, dtype=torch.float64)
    a = isa(h)
    assert torch.allclose(a.pressure_Pa, a.density_kgm3 * R_AIR_JKGK * a.temperature_K, rtol=1e-12)
    assert torch.allclose(a.speed_of_sound_ms ** 2, 1.4 * R_AIR_JKGK * a.temperature_K, rtol=1e-12)


def test_pressure_and_density_decrease_monotonically():
    h = torch.linspace(0.0, ISA_MAX_ALTITUDE_M, 201, dtype=torch.float64)
    a = isa(h)
    assert torch.all(torch.diff(a.pressure_Pa) < 0.0)
    assert torch.all(torch.diff(a.density_kgm3) < 0.0)
    # temperature is constant in the stratosphere, decreasing below 11 km
    assert torch.all(torch.diff(a.temperature_K) <= 1e-12)


def test_temperature_is_isothermal_above_the_tropopause():
    a = isa(_t([11000.0, 14000.0, 20000.0]))
    assert torch.allclose(a.temperature_K, _t(216.65).expand(3), atol=1e-9)


def test_kinematic_viscosity_property():
    a = isa(_t(4000.0))
    nu = float(a.kinematic_viscosity_m2s)
    assert nu == pytest.approx(float(a.dynamic_viscosity_Pas) / float(a.density_kgm3), rel=1e-12)
    assert nu == pytest.approx(2.028e-5, rel=1e-3)  # ISA 4 km


def test_dynamic_viscosity_alias_matches_spec_name():
    a = isa(_t(0.0))
    assert torch.equal(a.dynamic_viscosity, a.dynamic_viscosity_Pas)


def test_namedtuple_unpacks_in_documented_order():
    T, p, rho, a_s, mu = isa(_t(0.0))
    assert float(T) == pytest.approx(288.15)
    assert float(p) == pytest.approx(101325.0)
    assert float(rho) == pytest.approx(1.225, rel=1e-4)
    assert float(a_s) == pytest.approx(340.294, rel=1e-5)
    assert float(mu) == pytest.approx(MU_SEA_LEVEL, rel=1e-4)


# --------------------------------------------------------------------------
# geometric vs geopotential altitude
# --------------------------------------------------------------------------

def test_geometric_altitude_row_matches_anderson_geometric_table():
    """Anderson Appendix A (geometric altitude) at 4000 m: T=262.17 K, rho=0.81935."""
    a = isa(_t(4000.0), geometric=True)
    assert float(a.temperature_K) == pytest.approx(262.17, abs=5e-3)
    assert float(a.density_kgm3) == pytest.approx(0.81935, rel=1e-5)
    assert float(a.pressure_Pa) == pytest.approx(61660.4, rel=1e-5)


def test_geopotential_conversion_is_small_but_not_zero():
    # Tight enough to pin EARTH_RADIUS_M itself: the ISA nominal radius 6356766 m
    # gives 10980.9980, the mean Earth radius 6371000 m gives 10981.0404.  A looser
    # tolerance here lets the wrong radius through unnoticed, and the radius is
    # otherwise unconstrained by any test in this file.
    H = float(geopotential_altitude(_t(11000.0)))
    assert H == pytest.approx(10980.9980, abs=1e-3)
    assert float(geopotential_altitude(_t(0.0))) == pytest.approx(0.0, abs=1e-12)


def test_isa_nominal_earth_radius_is_the_defining_constant():
    assert EARTH_RADIUS_M == 6356766.0


def test_altitude_conversions_round_trip():
    h = torch.linspace(-4000.0, 20000.0, 25, dtype=torch.float64)
    assert torch.allclose(geometric_altitude(geopotential_altitude(h)), h, rtol=1e-12)


# --------------------------------------------------------------------------
# batching / dtype / device
# --------------------------------------------------------------------------

@pytest.mark.parametrize("shape", [(), (1,), (5,), (3, 4), (2, 3, 4)])
def test_shape_is_preserved(shape):
    h = torch.rand(shape, dtype=torch.float64) * ISA_MAX_ALTITUDE_M
    for field in isa(h):
        assert field.shape == h.shape
        assert field.dtype == h.dtype
        assert field.device == h.device


def test_batched_values_equal_scalar_values():
    hs = [0.0, 4000.0, 11000.0, 20000.0]
    batched = isa(_t(hs))
    for i, h in enumerate(hs):
        single = isa(_t(h))
        for b, s in zip(batched, single):
            assert float(b[i]) == pytest.approx(float(s), rel=1e-12)


def test_float32_input_gives_float32_output_with_acceptable_accuracy():
    a = isa(torch.tensor([0.0, 4000.0, 11000.0], dtype=torch.float32))
    assert a.pressure_Pa.dtype == torch.float32
    expected = [ISA_TABLE[h][1] for h in (0.0, 4000.0, 11000.0)]
    assert a.pressure_Pa.numpy() == pytest.approx(np.array(expected, dtype=np.float32), rel=1e-5)


def test_integer_and_python_scalar_inputs_are_promoted():
    a = isa(torch.tensor([0, 4000]))
    assert a.temperature_K.dtype.is_floating_point
    assert float(a.temperature_K[1]) == pytest.approx(262.15, rel=1e-9)
    b = isa(4000.0)
    assert float(b.pressure_Pa) == pytest.approx(61640.2, rel=1e-5)


# --------------------------------------------------------------------------
# differentiability
# --------------------------------------------------------------------------

@pytest.mark.parametrize("H", [0.0, 500.0, 4000.0, 10999.0, 11001.0, 15000.0, 20000.0])
def test_gradcheck_all_outputs(H):
    h = torch.tensor([H], dtype=torch.float64, requires_grad=True)
    for i in range(5):
        assert torch.autograd.gradcheck(
            lambda x: isa(x, strict=False)[i], (h,), eps=1e-4, atol=1e-6, rtol=1e-4
        )


def test_pressure_gradient_obeys_hydrostatic_balance():
    """dp/dH = -rho*g0 exactly, in both layers. The strongest physics check on
    the analytic derivative -- it couples the p and rho branches."""
    h = torch.linspace(0.0, ISA_MAX_ALTITUDE_M, 21, dtype=torch.float64, requires_grad=True)
    a = isa(h)
    (dp,) = torch.autograd.grad(a.pressure_Pa.sum(), h)
    expected = -a.density_kgm3.detach() * GRAVITY_MS2
    assert torch.allclose(dp, expected, rtol=1e-10)


def test_temperature_gradient_is_the_lapse_rate():
    h = torch.tensor([0.0, 4000.0, 10999.0, 11001.0, 18000.0], dtype=torch.float64,
                     requires_grad=True)
    (dT,) = torch.autograd.grad(isa(h).temperature_K.sum(), h)
    assert dT[:3].numpy() == pytest.approx(-0.0065, rel=1e-12)
    assert dT[3:].numpy() == pytest.approx(0.0, abs=1e-14)


def test_sound_speed_gradient_matches_analytic():
    h = torch.tensor([2000.0, 8000.0], dtype=torch.float64, requires_grad=True)
    a = isa(h)
    (da,) = torch.autograd.grad(a.speed_of_sound_ms.sum(), h)
    # a = sqrt(gamma R T)  ->  da/dH = 0.5 * gamma * R * (dT/dH) / a
    expected = 0.5 * 1.4 * R_AIR_JKGK * (-0.0065) / a.speed_of_sound_ms.detach()
    assert torch.allclose(da, expected, rtol=1e-10)


def test_gradients_are_finite_at_and_across_the_tropopause():
    h = torch.tensor([10999.0, 11000.0, 11001.0], dtype=torch.float64, requires_grad=True)
    a = isa(h)
    for field in a:
        (g,) = torch.autograd.grad(field.sum(), h, retain_graph=True)
        assert torch.all(torch.isfinite(g)), "non-finite gradient at the 11 km break"


def test_gradients_are_finite_over_the_whole_envelope():
    h = torch.linspace(0.0, ISA_MAX_ALTITUDE_M, 501, dtype=torch.float64, requires_grad=True)
    a = isa(h)
    for field in a:
        (g,) = torch.autograd.grad(field.sum(), h, retain_graph=True)
        assert torch.all(torch.isfinite(g))
        assert torch.all(torch.isfinite(field))


def test_second_derivative_of_pressure_is_finite():
    """p is C1 across the break (d ln p/dH = -g/(RT) with T continuous), so a
    second-order optimiser will not see an infinity."""
    h = torch.tensor([10999.5, 11000.5], dtype=torch.float64, requires_grad=True)
    p = isa(h).pressure_Pa
    (g,) = torch.autograd.grad(p.sum(), h, create_graph=True)
    (gg,) = torch.autograd.grad(g.sum(), h)
    assert torch.all(torch.isfinite(gg))


def test_blend_smooths_the_temperature_kink_without_moving_the_layers():
    """With blend_m > 0 the lapse-rate kink becomes C-infinity; away from the
    break the smoothed model must still agree with the exact ISA."""
    hard = isa(_t([0.0, 4000.0, 20000.0]))
    soft = isa(_t([0.0, 4000.0, 20000.0]), blend_m=50.0)
    for a, b in zip(hard, soft):
        assert torch.allclose(a, b, rtol=1e-6)

    h = torch.tensor([10990.0, 11000.0, 11010.0], dtype=torch.float64, requires_grad=True)
    T = isa(h, blend_m=50.0).temperature_K
    (dT,) = torch.autograd.grad(T.sum(), h, create_graph=True)
    (d2T,) = torch.autograd.grad(dT.sum(), h)
    assert torch.all(torch.isfinite(d2T))
    assert torch.all(d2T > 0.0)  # lapse rate is relaxing to zero through the break
    # ...whereas the hard model has a genuine kink there: the first derivative
    # steps from the lapse rate to zero and is a graph constant, so there is no
    # second derivative to take at all.
    h2 = torch.tensor([10990.0, 11010.0], dtype=torch.float64, requires_grad=True)
    (dT2,) = torch.autograd.grad(isa(h2).temperature_K.sum(), h2, create_graph=True)
    assert dT2[0].item() == pytest.approx(-0.0065, rel=1e-12)
    assert dT2[1].item() == pytest.approx(0.0, abs=1e-15)
    assert dT2.grad_fn is None  # piecewise-constant: d2T/dH2 == 0 off the kink


# --------------------------------------------------------------------------
# CUDA
# --------------------------------------------------------------------------

@DEV_CUDA
def test_cuda_values_match_cpu():
    h = torch.linspace(0.0, ISA_MAX_ALTITUDE_M, 64, dtype=torch.float64)
    cpu = isa(h)
    gpu = isa(h.cuda())
    for c, g in zip(cpu, gpu):
        assert g.is_cuda
        assert torch.allclose(g.cpu(), c, rtol=1e-12, atol=0.0)


@DEV_CUDA
def test_cuda_is_differentiable():
    h = torch.linspace(0.0, ISA_MAX_ALTITUDE_M, 64, dtype=torch.float64,
                       device="cuda", requires_grad=True)
    a = isa(h)
    (dp,) = torch.autograd.grad(a.pressure_Pa.sum(), h)
    assert dp.is_cuda
    assert torch.allclose(dp, -a.density_kgm3.detach() * GRAVITY_MS2, rtol=1e-10)


@DEV_CUDA
def test_cuda_float32_batch_shape():
    h = torch.rand((7, 11), dtype=torch.float32, device="cuda") * 20000.0
    a = isa(h)
    for f in a:
        assert f.shape == (7, 11) and f.dtype == torch.float32 and f.is_cuda


# --------------------------------------------------------------------------
# numpy wrapper
# --------------------------------------------------------------------------

def test_numpy_wrapper_scalar():
    a = isa_numpy(4000.0)
    assert isinstance(a, Atmosphere)
    assert isinstance(a.density_kgm3, float)
    assert a.density_kgm3 == pytest.approx(0.81913, rel=1e-5)


def test_numpy_wrapper_array_shape_and_values():
    h = np.array([[0.0, 4000.0], [11000.0, 20000.0]])
    a = isa_numpy(h)
    assert isinstance(a.pressure_Pa, np.ndarray)
    assert a.pressure_Pa.shape == (2, 2)
    expected = np.array([[101325.0, 61640.2], [22632.0, 5474.9]])
    assert a.pressure_Pa == pytest.approx(expected, rel=1e-5)


def test_numpy_wrapper_agrees_with_torch():
    h = np.linspace(0.0, 20000.0, 17)
    npy = isa_numpy(h)
    tor = isa(torch.as_tensor(h))
    for n, t in zip(npy, tor):
        assert n == pytest.approx(t.numpy(), rel=1e-14)


# --------------------------------------------------------------------------
# range guarding -- silent extrapolation is the dangerous failure mode
# --------------------------------------------------------------------------

def test_altitude_above_model_ceiling_raises_by_default():
    with pytest.raises(ValueError, match="20000"):
        isa(_t([0.0, 25000.0]))


def test_range_check_can_be_disabled_for_hot_loops():
    a = isa(_t(25000.0), strict=False)
    assert torch.isfinite(a.pressure_Pa)


def test_non_finite_altitude_raises():
    with pytest.raises(ValueError):
        isa(_t([float("nan")]))


# --------------------------------------------------------------------------
# gaps found by mutation-testing the suite: things that a wrong implementation
# could previously have got away with
# --------------------------------------------------------------------------

def test_viscosity_matches_the_isa_table_aloft_not_just_at_sea_level():
    """mu(H) was pinned at only one altitude, so a constant-mu model survived.

    ISA tabulated dynamic viscosity: 1.7894e-5 Pa s at 0 m, 1.6612e-5 at 4 km,
    1.4216e-5 at 11 km (and constant above, since T is)."""
    mu = isa(_t([0.0, 4000.0, 11000.0, 20000.0])).dynamic_viscosity_Pas
    assert mu.numpy() == pytest.approx(
        np.array([1.78938e-5, 1.661108e-5, 1.421613e-5, 1.421613e-5]), rel=1e-5
    )


def test_viscosity_gradient_matches_the_analytic_sutherland_derivative():
    """gradcheck cannot see this: dmu/dH is ~3e-10, three thousand times smaller
    than gradcheck's atol=1e-6, so freezing mu passes every gradcheck in the file."""
    h = torch.tensor([0.0, 4000.0, 10999.0, 11001.0, 20000.0], dtype=torch.float64,
                     requires_grad=True)
    a = isa(h)
    (dmu,) = torch.autograd.grad(a.dynamic_viscosity_Pas.sum(), h)
    T = a.temperature_K.detach()
    # mu = b T^1.5/(T+S)  ->  dmu/dT = b sqrt(T) (0.5 T + 1.5 S)/(T+S)^2
    dmu_dT = (SUTHERLAND_BETA * torch.sqrt(T) * (0.5 * T + 1.5 * SUTHERLAND_S_K)
              / (T + SUTHERLAND_S_K) ** 2)
    lapse = torch.tensor([LAPSE_RATE_K_PER_M] * 3 + [0.0, 0.0], dtype=torch.float64)
    assert torch.allclose(dmu, dmu_dT * lapse, rtol=1e-12)
    assert float(dmu[0]) == pytest.approx(-3.1363e-10, rel=1e-4)  # independent value


def test_empty_batch_is_handled_not_crashed():
    """A zero-length altitude batch is a normal slice in a vectorised sweep; the
    range check used to raise RuntimeError from min() on it."""
    out = isa(torch.zeros(0, dtype=torch.float64))
    for field in out:
        assert field.shape == (0,)


def test_negative_blend_width_raises_instead_of_being_ignored():
    with pytest.raises(ValueError, match="blend_m"):
        isa(_t(11000.0), blend_m=-50.0)


def test_blend_error_is_bounded_near_the_break_not_only_far_from_it():
    """The existing blend test samples 0/4000/20000 m -- 140+ blend widths away,
    where the error is identically zero. Pin the near field, where it is not."""
    w = 50.0
    h = _t([10800.0, 11000.0, 11200.0])
    hard, soft = isa(h), isa(h, blend_m=w)
    dT = (soft.temperature_K - hard.temperature_K).abs()
    # worst case is exactly at the break: |dT| = |L| * w * ln 2
    assert float(dT[1]) == pytest.approx(abs(LAPSE_RATE_K_PER_M) * w * math.log(2.0), rel=1e-6)
    # four widths away it has decayed by three orders of magnitude
    assert float(dT[0]) < 1e-2 and float(dT[2]) < 1e-2


def test_blended_model_is_not_hydrostatically_exact_and_the_error_is_bounded():
    """KNOWN LIMITATION of blend_m > 0, pinned here so it cannot grow silently.

    The closed form is the hydrostatic solution only when Hc == min(H, Ht),
    because then (H - Hc) and dHc/dH are never both non-zero.  The softmin makes
    them overlap in a band around the tropopause, leaving a residual

        (dp/dH + rho g) / (rho g) = (H - Hc) * |L| * (dHc/dH) / T

    whose maximum over H is w*|L|/(e*T_tropopause) -- exactly, since
    max_u u*exp(-u) = 1/e.  So rho and dp/dH describe atmospheres that differ by
    ~1.1e-5 per metre of blend width.  Exact ISA (blend_m=0) is hydrostatic to
    machine precision; this is the price of the C-infinity option.
    """
    exact_coeff = abs(LAPSE_RATE_K_PER_M) / (math.e * 216.65)  # 1.1037e-5 per m
    for w in (25.0, 50.0, 200.0):
        h = torch.linspace(10000.0, 12000.0, 2001, dtype=torch.float64, requires_grad=True)
        a = isa(h, blend_m=w)
        (dp,) = torch.autograd.grad(a.pressure_Pa.sum(), h)
        rel = ((dp + a.density_kgm3.detach() * GRAVITY_MS2)
               / (a.density_kgm3.detach() * GRAVITY_MS2)).abs().max()
        # (the few-per-mille slack is because the peak sits slightly above the
        #  tropopause, where the blended T is a shade above 216.65 K)
        assert float(rel) == pytest.approx(w * exact_coeff, rel=5e-3)

    # ...and with blend_m = 0 the same measurement is machine zero.
    h = torch.linspace(10000.0, 12000.0, 2001, dtype=torch.float64, requires_grad=True)
    a = isa(h)
    (dp,) = torch.autograd.grad(a.pressure_Pa.sum(), h)
    assert torch.allclose(dp, -a.density_kgm3.detach() * GRAVITY_MS2, rtol=1e-13)
