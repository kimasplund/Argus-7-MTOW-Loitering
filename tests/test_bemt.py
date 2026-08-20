"""Tests for argus7.prop.bemt -- blade-element momentum theory propeller model.

Three things are being tested here, in increasing order of importance.

1. DIMENSIONAL CORRECTNESS. C_T, C_P, C_Q are *defined* by
   T = C_T rho n^2 D^4, P = C_P rho n^3 D^5, Q = C_Q rho n^2 D^5, so a
   correctly implemented model must reproduce those identities exactly
   (they are internal consistency, not physics), and must additionally
   reproduce the *similarity* they encode: two geometrically similar
   propellers run at the same advance ratio J = V/(nD) have the same
   coefficients. That second one is real physics and it is the one that
   catches a mis-placed rho or a factor of 2 pi in the torque.

2. PHYSICAL PLAUSIBILITY. Efficiency must peak at a sane advance ratio and
   must never exceed the actuator-disc (Froude/Betz) ideal-propulsive-
   efficiency limit eta_ideal = 2 / (1 + sqrt(1 + C_Tc)) with
   C_Tc = T / (0.5 rho V^2 A) = 8 C_T / (pi J^2). No amount of blade
   cleverness beats that; a model that does is producing energy.

3. THE BASELINE PROPULSION FINDING. The report's 0.813 m propeller at
   2100 rpm cannot absorb the 17 kW the report also specifies. This is not
   a modelling artefact and it is not a rounding problem: it needs
   C_P = 0.911 against a practical ceiling near 0.25, i.e. it is off by a
   factor of ~3.6 in power. These tests pin that finding down so it cannot
   be quietly regressed away, and pin down the two closures (bigger
   diameter, or higher rpm) that would fix it.

Geometry (propeller diameter, rpm, rated power) is read from
design/argus7_v1.yaml through the project loader in the tests that assert
on the baseline, so this file never hardcodes the numbers it is judging.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pytest

from argus7.design.schema import load_design

from argus7.prop.bemt import (
    PRACTICAL_CP_CEILING,
    RHO_SEA_LEVEL,
    BEMTResult,
    BladeGeometry,
    PropulsionClosure,
    activity_factor,
    close_propulsion,
    constant_pitch_blade,
    loiter_propulsion_check,
    max_power_absorbed,
    power_absorbed,
    required_cp,
    run_bemt,
)

REPO = Path(__file__).resolve().parents[1]
DESIGN = REPO / "design" / "argus7_v1.yaml"

# ISA density at the design loiter altitude of 4000 m (the altitude itself
# comes from the design file; only the atmosphere table value is stated here,
# and it is asserted against mission.loiter_altitude_m below).
RHO_4000M = 0.81935          # kg/m^3, ISA
G = 9.80665                  # m/s^2, standard gravity
LOITER_CL = 1.21             # report §4 loiter lift coefficient


@pytest.fixture(scope="module")
def design():
    return load_design(DESIGN)


@pytest.fixture(scope="module")
def baseline_prop(design):
    """Diameter / rpm / rated power straight out of the design file."""
    p = design.propulsion
    return p.prop_diameter_m, p.prop_rpm, p.power_max_kw


@pytest.fixture(scope="module")
def demo_blade() -> BladeGeometry:
    """A 0.8 m two-blade prop at pitch/D = 0.7 -- a generic reference blade."""
    return constant_pitch_blade(diameter=0.8, pitch=0.56, blades=2)


@pytest.fixture(scope="module")
def demo_run(demo_blade) -> BEMTResult:
    return run_bemt(demo_blade, rpm=2400.0, v_ms=25.0, rho=RHO_SEA_LEVEL)


# --- 1. Dimensional correctness ---------------------------------------------

def test_coefficient_identities_hold(demo_run, demo_blade):
    """C_T, C_P, C_Q, J and eta must satisfy their own definitions."""
    r = demo_run
    n = 2400.0 / 60.0
    D = demo_blade.diameter_m
    rho = RHO_SEA_LEVEL
    assert r.ct == pytest.approx(r.thrust_n / (rho * n**2 * D**4), rel=1e-12)
    assert r.cp == pytest.approx(r.power_w / (rho * n**3 * D**5), rel=1e-12)
    assert r.cq == pytest.approx(r.torque_nm / (rho * n**2 * D**5), rel=1e-12)
    assert r.j == pytest.approx(25.0 / (n * D), rel=1e-12)
    # P = 2 pi n Q  =>  C_P = 2 pi C_Q
    assert r.cp == pytest.approx(2.0 * math.pi * r.cq, rel=1e-10)
    # eta = T V / P = C_T J / C_P
    assert r.eta == pytest.approx(r.ct * r.j / r.cp, rel=1e-10)


def test_solution_converged(demo_run):
    assert demo_run.converged
    assert demo_run.thrust_n > 0.0
    assert demo_run.power_w > 0.0


# Propeller similarity (C_T, C_P invariant at fixed J) is exact only when
# Reynolds AND Mach are also matched. Scaling D or n at a fixed speed of
# sound cannot match Mach -- doubling either doubles tip Mach, and the
# Prandtl-Glauert factor then differs by ~10-20%, which is real physics and
# not a defect. These tests therefore run with compressibility off, which
# isolates exactly the invariance being asserted. Reynolds still differs
# (it scales with chord and speed) and that residual sensitivity is what the
# 5% tolerance covers.
#
# They also run at J ~ 0.5, where the blade is properly loaded. Near the
# zero-thrust advance ratio (J ~ 0.87 for this blade) thrust is a small
# difference between two large integrals, so a 1% change in section drag
# moves it by tens of percent -- a numerically meaningless place to assert
# a scaling law.

def test_thrust_scales_as_n2_d4_at_constant_J(demo_blade):
    """Double the diameter and the speed, keep n: same J, thrust x16, power x32.

    This is the propeller similarity law. It only comes out right if rho,
    n and D enter the momentum and blade-element equations in the right
    places.
    """
    small = constant_pitch_blade(diameter=0.8, pitch=0.56, blades=2)
    big = constant_pitch_blade(diameter=1.6, pitch=1.12, blades=2)   # same p/D
    n = 40.0
    rs = run_bemt(small, rpm=n * 60.0, v_ms=16.0, rho=RHO_SEA_LEVEL,
                  compressibility=False)
    rb = run_bemt(big, rpm=n * 60.0, v_ms=32.0, rho=RHO_SEA_LEVEL,
                  compressibility=False)
    assert rb.j == pytest.approx(rs.j, rel=1e-12)
    assert rb.thrust_n / rs.thrust_n == pytest.approx(16.0, rel=0.05)
    assert rb.power_w / rs.power_w == pytest.approx(32.0, rel=0.05)
    # ...which is the same statement as the coefficients matching.
    assert rb.ct == pytest.approx(rs.ct, rel=0.05)
    assert rb.cp == pytest.approx(rs.cp, rel=0.05)


def test_thrust_scales_as_n2_at_constant_J_fixed_diameter(demo_blade):
    """Same prop, double the rpm and the airspeed: thrust x4, power x8."""
    r1 = run_bemt(demo_blade, rpm=2000.0, v_ms=13.3, rho=RHO_SEA_LEVEL,
                  compressibility=False)
    r2 = run_bemt(demo_blade, rpm=4000.0, v_ms=26.6, rho=RHO_SEA_LEVEL,
                  compressibility=False)
    assert r2.j == pytest.approx(r1.j, rel=1e-12)
    assert r2.thrust_n / r1.thrust_n == pytest.approx(4.0, rel=0.05)
    assert r2.power_w / r1.power_w == pytest.approx(8.0, rel=0.05)


def test_thrust_scales_linearly_with_density(demo_blade):
    """Halving rho halves thrust and power (Reynolds effect aside)."""
    r1 = run_bemt(demo_blade, rpm=2400.0, v_ms=15.0, rho=RHO_SEA_LEVEL)
    r2 = run_bemt(demo_blade, rpm=2400.0, v_ms=15.0, rho=0.5 * RHO_SEA_LEVEL)
    assert r2.thrust_n / r1.thrust_n == pytest.approx(0.5, rel=0.05)
    assert r2.power_w / r1.power_w == pytest.approx(0.5, rel=0.05)


# --- 2. Physical plausibility ------------------------------------------------

def test_efficiency_peaks_at_a_sane_advance_ratio(demo_blade):
    """A pitch/D = 0.7 prop should peak somewhere around J ~ 0.5-1.0."""
    js, etas = [], []
    for v in np.linspace(4.0, 44.0, 21):
        r = run_bemt(demo_blade, rpm=2400.0, v_ms=float(v), rho=RHO_SEA_LEVEL)
        if r.thrust_n > 0.0:
            js.append(r.j)
            etas.append(r.eta)
    etas = np.asarray(etas)
    js = np.asarray(js)
    j_peak = float(js[int(np.argmax(etas))])
    eta_peak = float(etas.max())
    assert 0.35 < j_peak < 1.2, f"peak eta at J={j_peak:.3f}, not a sane J"
    assert 0.60 < eta_peak < 0.92, f"peak eta = {eta_peak:.3f} is not plausible"


def test_efficiency_never_exceeds_actuator_disc_limit(demo_blade):
    """eta <= 2 / (1 + sqrt(1 + C_Tc)); the Froude/Betz ideal.

    Violating this means the model is extracting more useful power than the
    momentum it puts into the slipstream can pay for.
    """
    worst = []
    for v in np.linspace(4.0, 44.0, 21):
        r = run_bemt(demo_blade, rpm=2400.0, v_ms=float(v), rho=RHO_SEA_LEVEL)
        if r.thrust_n <= 0.0 or r.j <= 0.0:
            continue
        ctc = 8.0 * r.ct / (math.pi * r.j**2)      # T / (0.5 rho V^2 A)
        eta_ideal = 2.0 / (1.0 + math.sqrt(1.0 + ctc))
        worst.append((r.eta - eta_ideal, r.j, r.eta, eta_ideal))
    assert worst
    margin, j, eta, eta_ideal = max(worst)
    assert margin <= 1e-6, (
        f"eta={eta:.4f} exceeds actuator-disc limit {eta_ideal:.4f} at J={j:.3f}"
    )


def test_prandtl_tip_loss_reduces_thrust(demo_blade):
    with_loss = run_bemt(demo_blade, rpm=2400.0, v_ms=25.0, rho=RHO_SEA_LEVEL)
    without = run_bemt(demo_blade, rpm=2400.0, v_ms=25.0, rho=RHO_SEA_LEVEL,
                       tip_loss=False)
    assert with_loss.thrust_n < without.thrust_n
    # A sane tip loss on a 2-blade prop costs a few percent of thrust, not half.
    assert 0.005 < 1.0 - with_loss.thrust_n / without.thrust_n < 0.25
    assert np.all(with_loss.tip_loss_factor <= 1.0 + 1e-12)
    assert with_loss.tip_loss_factor[-1] < with_loss.tip_loss_factor[0]


def test_static_case_solves_and_figure_of_merit_is_physical(demo_blade):
    """V = 0 is a separate momentum limit; it must still give a sane answer.

    Static figure of merit FM = P_ideal/P with P_ideal = T^1.5/sqrt(2 rho A)
    is bounded by 1 for any real propeller.
    """
    r = run_bemt(demo_blade, rpm=2400.0, v_ms=0.0, rho=RHO_SEA_LEVEL)
    assert r.converged
    assert r.thrust_n > 0.0 and r.power_w > 0.0
    assert r.j == 0.0 and r.eta == 0.0
    area = math.pi * demo_blade.diameter_m**2 / 4.0
    p_ideal = r.thrust_n**1.5 / math.sqrt(2.0 * RHO_SEA_LEVEL * area)
    fm = p_ideal / r.power_w
    assert 0.2 < fm < 1.0, f"static figure of merit {fm:.3f} is not physical"


def test_higher_pitch_absorbs_more_power(design):
    """Monotonic in the useful range -- a basic sanity gradient."""
    D = design.propulsion.prop_diameter_m
    rpm = design.propulsion.prop_rpm
    p_low = power_absorbed(D, rpm, RHO_SEA_LEVEL, 0.4 * D)
    p_mid = power_absorbed(D, rpm, RHO_SEA_LEVEL, 0.7 * D)
    p_high = power_absorbed(D, rpm, RHO_SEA_LEVEL, 1.0 * D)
    assert p_low < p_mid < p_high


def test_assumed_blade_planform_is_a_realistic_propeller(demo_blade):
    """The default chord distribution is an assumption; keep it defensible.

    Activity factor per blade for light-aircraft propellers runs ~90-110.
    """
    af = activity_factor(demo_blade)
    assert 80.0 < af < 120.0, f"assumed planform has AF={af:.1f}, not a real prop"


# --- 3. The baseline propulsion finding --------------------------------------

def test_required_cp_for_the_report_baseline_is_0_911(baseline_prop):
    D, rpm, p_kw = baseline_prop
    cp = required_cp(p_kw * 1000.0, rpm, RHO_SEA_LEVEL, D)
    assert cp == pytest.approx(0.911, abs=0.002), (
        f"design/argus7_v1.yaml asks a {D:.3f} m prop at {rpm:.0f} rpm to take "
        f"{p_kw:.1f} kW, i.e. C_P = {cp:.3f}"
    )


def test_report_propulsion_set_cannot_absorb_rated_power(baseline_prop):
    """THE FINDING. 17 kW into 0.813 m at 2100 rpm does not close.

    Swept across every pitch a real propeller could be built with, and
    across advance ratio, the best C_P this disc can reach is far below
    the C_P = 0.911 the rated power demands.
    """
    D, rpm, p_kw = baseline_prop
    rated_w = p_kw * 1000.0
    cp_needed = required_cp(rated_w, rpm, RHO_SEA_LEVEL, D)
    best_w, best = max_power_absorbed(D, rpm, RHO_SEA_LEVEL)
    assert best_w < rated_w, (
        f"BEMT says the baseline prop CAN absorb {best_w/1000:.2f} kW; the "
        f"infeasibility finding needs re-examining"
    )
    assert best.cp < cp_needed, (
        f"baseline propulsion does not close: {D:.3f} m at {rpm:.0f} rpm needs "
        f"C_P = {cp_needed:.3f} to absorb {p_kw:.1f} kW, but the best C_P this "
        f"disc reaches is {best.cp:.3f} (at J = {best.j:.2f}, pitch/D = "
        f"{best.pitch_over_d:.2f}), i.e. only {best_w/1000:.2f} kW -- short by "
        f"a factor of {cp_needed/best.cp:.1f}"
    )
    # And it is short by a lot, not by a modelling tolerance.
    assert cp_needed / best.cp > 2.0
    # The practical ceiling used by close_propulsion must not be optimistic
    # relative to what the blade-element model can actually reach.
    assert best.cp <= PRACTICAL_CP_CEILING * 1.6


def test_finding_survives_an_absurdly_generous_sweep(baseline_prop):
    """Stress-test: even at pitch/D = 4.0 the baseline disc falls short.

    pitch/D = 4.0 is a blade angle of 59 degrees at 0.75R. No propeller is
    built like that, and the aircraft cannot fly at the top of the speed
    sweep either. The point is that the finding is not an artefact of where
    the default sweep was cut off: nothing inside or outside the realistic
    envelope gets this disc to 17 kW.
    """
    D, rpm, p_kw = baseline_prop
    best_w, best = max_power_absorbed(
        D, rpm, RHO_SEA_LEVEL, pitch_over_d=np.linspace(0.3, 4.0, 16))
    assert best_w < p_kw * 1000.0, (
        f"even at pitch/D {best.pitch_over_d:.1f} with {best.blades} blades "
        f"the disc reaches only {best_w/1000:.2f} kW (C_P {best.cp:.3f})"
    )


def test_loiter_point_is_reproduced_from_the_design_file(design):
    """The loiter speed and drag must fall out of the yaml, not be quoted.

    Guards the airframe side of loiter_propulsion_check: CL 1.21 on the
    design's own wing area, aspect ratio and drag polar at 4000 m must give
    the report's loiter speed (top of the 99-128 km/h TAS band) and an L/D
    close to the report's 27.1.
    """
    lc = loiter_propulsion_check(DESIGN, rho=RHO_4000M, cl=LOITER_CL, g=G)
    assert lc.v_ms == pytest.approx(128.0 / 3.6, rel=0.02)
    assert lc.l_over_d == pytest.approx(27.1, rel=0.02)
    assert lc.drag_n == pytest.approx(design.masses.mtow * G / lc.l_over_d,
                                      rel=1e-9)


def test_loiter_holds_but_only_on_three_coarse_blades(design):
    """Loiter closes -- but not as easily as the report implies.

    The baseline disc has to work at J ~ 1.25 in loiter, which is a very
    high advance ratio for a 0.813 m propeller at 2100 rpm. With the assumed
    AF-95 planform a TWO-blade propeller saturates well below the required
    thrust at every pitch; three coarse blades are needed, and the shaft
    power comes out above the report's ~3.4 kW because that figure implies a
    propulsive efficiency no propeller reaches at this advance ratio.

    (The two-blade result depends on the assumed chord distribution -- a
    much wider blade would change it. The advance ratio does not, and that
    is the part that matters.)
    """
    lc = loiter_propulsion_check(DESIGN, rho=RHO_4000M, cl=LOITER_CL, g=G)
    assert lc.advance_ratio == pytest.approx(1.25, abs=0.05)
    assert lc.shaft_power_w is not None, (
        f"no blade in the sweep makes {lc.drag_n:.1f} N at loiter")
    assert lc.blades == 3, (
        f"a 2-blade of the assumed planform tops out at "
        f"{lc.two_blade_max_thrust_n:.0f} N against {lc.drag_n:.0f} N required"
    )
    assert lc.two_blade_max_thrust_n < lc.drag_n
    assert lc.pitch_over_d > 1.5, "loiter needs a coarse blade at this J"
    assert 3500.0 < lc.shaft_power_w < 5500.0, (
        f"loiter shaft power measures {lc.shaft_power_w/1000:.2f} kW"
    )
    assert lc.eta > 0.75
    # ...and it is still comfortably inside the rated engine power. Loiter is
    # not what fails.
    assert lc.shaft_power_w < design.propulsion.power_max_kw * 1000.0


def test_close_propulsion_diameter_near_1_05_m():
    c = close_propulsion(power_kw=17.0, rpm=2100.0, rho=RHO_SEA_LEVEL)
    assert isinstance(c, PropulsionClosure)
    assert c.diameter_m == pytest.approx(1.05, abs=0.03), (
        f"closing 17 kW at 2100 rpm needs D = {c.diameter_m:.3f} m"
    )
    # The returned diameter must actually satisfy the ceiling by definition.
    assert required_cp(17000.0, 2100.0, RHO_SEA_LEVEL,
                       c.diameter_m) == pytest.approx(c.cp_ceiling, rel=1e-9)


def test_close_propulsion_rpm_at_fixed_baseline_diameter(baseline_prop):
    D, rpm, p_kw = baseline_prop
    c = close_propulsion(power_kw=p_kw, rpm=rpm, rho=RHO_SEA_LEVEL,
                         diameter_m=D)
    assert c.rpm_at_fixed_diameter == pytest.approx(3232.0, rel=0.02)
    assert required_cp(p_kw * 1000.0, c.rpm_at_fixed_diameter,
                       RHO_SEA_LEVEL, D) == pytest.approx(c.cp_ceiling, rel=1e-9)
    assert not c.baseline_closes
    assert c.required_cp_at_baseline == pytest.approx(0.911, abs=0.002)


def test_close_propulsion_defaults_diameter_from_the_design_file(design):
    """No hardcoded geometry: the fixed-diameter closure reads the yaml."""
    c = close_propulsion(power_kw=design.propulsion.power_max_kw,
                         rpm=design.propulsion.prop_rpm, rho=RHO_SEA_LEVEL)
    assert c.fixed_diameter_m == pytest.approx(
        design.propulsion.prop_diameter_m, rel=1e-12)


def test_closure_scales_correctly():
    """D ~ P^(1/5) and n ~ P^(1/3) at fixed C_P; cheap check on the algebra."""
    a = close_propulsion(power_kw=17.0, rpm=2100.0, rho=RHO_SEA_LEVEL,
                         diameter_m=0.813)
    b = close_propulsion(power_kw=34.0, rpm=2100.0, rho=RHO_SEA_LEVEL,
                         diameter_m=0.813)
    assert b.diameter_m / a.diameter_m == pytest.approx(2.0 ** (1 / 5), rel=1e-9)
    assert (b.rpm_at_fixed_diameter / a.rpm_at_fixed_diameter
            == pytest.approx(2.0 ** (1 / 3), rel=1e-9))


def test_closed_diameter_is_actually_achievable_by_bemt():
    """Sanity-check the ceiling: a 1.05 m prop really can take 17 kW.

    The closure is algebra on a C_P ceiling; this test confirms the ceiling
    is not fiction by having the blade-element model find a pitch that
    absorbs the rated power at the closing diameter.
    """
    c = close_propulsion(power_kw=17.0, rpm=2100.0, rho=RHO_SEA_LEVEL)
    best_w, best = max_power_absorbed(c.diameter_m, 2100.0, RHO_SEA_LEVEL)
    assert best_w > 17000.0, (
        f"closing diameter {c.diameter_m:.3f} m only reaches "
        f"{best_w/1000:.2f} kW (C_P {best.cp:.3f}) in BEMT"
    )


def test_loiter_altitude_matches_the_assumed_atmosphere(design):
    """Guard on RHO_4000M: if the design's loiter altitude moves, this fails."""
    assert design.mission.loiter_altitude_m == pytest.approx(4000.0, abs=1.0)


def test_diameter_closure_nearly_collides_with_the_booms(design):
    """Collateral finding: the closing propeller barely fits between the booms.

    The 1.05 m propeller that closes the power balance has a tip radius of
    ~527 mm against a boom inner surface at ~576 mm. That is under 50 mm of
    clearance on an aircraft whose booms sit where they do for tail-arm
    reasons. Fixing the propulsion set by diameter alone therefore forces a
    boom-station change too; the module reports the number rather than
    letting the closure look free.
    """
    c = close_propulsion(power_kw=design.propulsion.power_max_kw,
                         rpm=design.propulsion.prop_rpm, rho=RHO_SEA_LEVEL)
    assert c.tip_to_boom_clearance_m is not None
    assert 0.0 < c.tip_to_boom_clearance_m < 0.06, (
        f"prop tip to boom inner surface = "
        f"{c.tip_to_boom_clearance_m * 1000:.0f} mm at the closing diameter "
        f"{c.diameter_m:.3f} m"
    )
    # The propeller as drawn is comfortably clear -- it is the fix that isn't.
    from argus7.design.geometry import derive_booms
    inner = (abs(derive_booms(design).y_station_m)
             - 0.5 * design.booms.diameter_m)
    assert inner - 0.5 * design.propulsion.prop_diameter_m > 0.15


def test_polar_table_matches_direct_neuralfoil_evaluation():
    """The lookup table is a speed shortcut; it must not change the answer.

    Every BEMT query interpolates a precomputed (alpha, Re) table instead of
    calling the surrogate. Inside the trusted alpha band the interpolated
    polar must agree with a direct evaluation to well inside the surrogate's
    own accuracy, or the shortcut is quietly changing the aerodynamics.
    """
    from argus7.prop.bemt import (DEFAULT_BLADE_AIRFOIL, _blade_coords,
                                  _neural_polar, section_cl_cd)

    coords = _blade_coords(DEFAULT_BLADE_AIRFOIL)
    call = _neural_polar()
    alpha_deg = np.linspace(-8.0, 16.0, 25)
    for re_value in (1.3e5, 4.0e5, 9.0e5, 2.2e6):
        re = np.full_like(alpha_deg, re_value)
        cl_ref, cd_ref = call(coords, alpha_deg, re)
        cl, cd = section_cl_cd(np.radians(alpha_deg), re)
        assert np.max(np.abs(cl - cl_ref)) < 3e-3, f"CL at Re {re_value:.0f}"
        assert np.max(np.abs(cd - cd_ref)) < 3e-4, f"CD at Re {re_value:.0f}"


def test_section_polar_source_is_resolved():
    """Blade sections must come from the project's NeuralFoil stack."""
    import argus7.prop.bemt as bemt

    bemt.section_cl_cd(np.array([0.05]), np.array([4.0e5]))
    assert bemt.SECTION_POLAR_SOURCE in ("argus7.aero.neural", "neuralfoil")


def test_power_absorbed_signature_and_units(design):
    """power_absorbed(diameter, rpm, rho, pitch) -> watts, positionally."""
    D = design.propulsion.prop_diameter_m
    w = power_absorbed(D, design.propulsion.prop_rpm, RHO_SEA_LEVEL, 0.7 * D)
    assert isinstance(w, float)
    assert 100.0 < w < 17000.0
