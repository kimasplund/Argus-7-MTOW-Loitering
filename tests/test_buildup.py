"""Tests for argus7.aero.buildup -- the component parasite-drag build-up.

WHAT IS AND IS NOT BEING TESTED HERE
------------------------------------
1. GEOMETRY. Every wetted area is checked against an INDEPENDENTLY computed
   value: a different formula, or a different integration, applied to the
   same design file. These are tight assertions -- a wetted area is pure
   geometry and there is a right answer.

2. THE DRAG METHOD. The Raymer/Hoerner/Torenbeek component build-up is a
   correlation, not a solution of the Navier-Stokes equations. Its output is
   checked only against a band, and the band is stated with its reasoning.
   The build-up's DISAGREEMENT with the report's C_D0 = 0.020 is recorded
   and printed rather than tuned away -- see
   test_total_cd0_against_report_baseline.

Run with -s to see the printed build-up table and the baseline comparison.
"""
import math
from pathlib import Path

import numpy as np
import pytest
import yaml

from argus7.design.geometry import derive_booms, derive_tail_panel, derive_wing
from argus7.design.schema import load_design
from argus7.cad.airfoil_coords import load_airfoil, max_thickness

from argus7.aero import buildup as B

DESIGN_PATH = "design/argus7_v1.yaml"
REPORT_CD0 = 0.020          # design/argus7_v1.yaml aero.cd0, report-§4
REPORT_CD0_BAND = 0.15      # the Phase-2 validation gate stated in the assignment


@pytest.fixture(scope="module")
def design():
    return load_design(DESIGN_PATH)


@pytest.fixture(scope="module")
def flow(design):
    return B.loiter_flow(design)


@pytest.fixture(scope="module")
def bu(design, flow):
    return B.parasite_buildup(design, flow)


# --------------------------------------------------------------------------
# flow condition
# --------------------------------------------------------------------------

def test_local_isa_matches_icao_table():
    """buildup carries its own troposphere-only ISA so it does not depend on
    a package being written in parallel. It still has to be the ISA.
    Reference rows: ICAO Doc 7488/3 (= US Standard Atmosphere 1976),
    tabulated against GEOPOTENTIAL altitude, and independently reproduced here
    with aerosandbox 4.2.10 Atmosphere(method="isa") -- which agrees with these
    rows to <1e-6 relative."""
    for h, (T, p, rho, a) in {
        0.0:     (288.150, 101325.00, 1.224999, 340.2941),
        1000.0:  (281.650,  89874.57, 1.111642, 336.4341),
        4000.0:  (262.150,  61640.24, 0.819129, 324.5787),
        8000.0:  (236.150,  35599.81, 0.525167, 308.0627),
        11000.0: (216.650,  22632.06, 0.363918, 295.0696),
    }.items():
        s = B.isa_troposphere(h)
        assert s.temperature_k == pytest.approx(T,   rel=1e-5)
        assert s.pressure_pa   == pytest.approx(p,   rel=1e-4)
        assert s.density_kgm3  == pytest.approx(rho, rel=1e-4)
        assert s.sound_speed_ms == pytest.approx(a,  rel=1e-4)
    # Sutherland at sea level; aerosandbox gives 1.7893803e-5 Pa.s
    assert B.isa_troposphere(0.0).viscosity_pas == pytest.approx(1.7893803e-5, rel=1e-6)
    assert B.isa_troposphere(4000.0).viscosity_pas == pytest.approx(1.6611075e-5, rel=1e-6)
    with pytest.raises(ValueError):
        B.isa_troposphere(12000.0)      # stratosphere is out of this model's scope


def test_loiter_flow_reproduces_the_report_loiter_speed(design, flow):
    """Report §4 loiter at 4000 m, heavy: 128 km/h TAS. That number is the
    lift equation at MTOW and CL 1.21 -- so it is a check that loiter_flow
    reads mass, area and altitude from the design file, not a new fact."""
    g = derive_wing(design.wing)
    v = math.sqrt(2 * design.masses.mtow * B.GRAVITY_MS2
                  / (flow.density_kgm3 * g.area_m2 * B.LOITER_CL))
    assert flow.velocity_ms == pytest.approx(v, rel=1e-12)
    assert flow.velocity_ms * 3.6 == pytest.approx(128.0, abs=1.5)
    assert flow.mach < 0.15                      # incompressible regime
    assert flow.reynolds_per_m == pytest.approx(1.75e6, rel=0.05)


def test_wing_reynolds_brackets_the_verified_xfoil_runs(design, flow):
    """The established XFOIL result was taken at Re 992372 (root) and 486526
    (tip). Those must be the same order as the Re this module derives from
    the design file, or the transition locations do not belong to this
    aircraft."""
    g = derive_wing(design.wing)
    re_root = g.chord_root_m * flow.reynolds_per_m
    re_tip = g.chord_tip_m * flow.reynolds_per_m
    assert 0.6e6 < re_root < 1.4e6
    assert 0.3e6 < re_tip < 0.7e6
    print(f"\n[Re] root {re_root:.0f}  tip {re_tip:.0f}  "
          f"(XFOIL runs were at 992372 / 486526)")


# --------------------------------------------------------------------------
# wetted areas, each against an independent computation
# --------------------------------------------------------------------------

def test_wing_wetted_area_against_independent_planform(design, bu):
    """Independent check: trapezoidal exposed planform area from the taper
    law, times Raymer's thick-airfoil approximation S_wet = 2(1+0.2 t/c)S_exp
    (Raymer, Aircraft Design 6th ed., eq. 7.11). The module instead integrates
    the REAL FX 63-137 arc length, so the two should agree to a few percent,
    not exactly."""
    g = derive_wing(design.wing)
    y0 = design.fuselage.max_diameter_m / 2.0        # wing root is buried here
    y1 = g.span_m / 2.0
    c = lambda y: g.chord_root_m * (1 - (1 - design.wing.taper_ratio) * 2 * y / g.span_m)
    s_exposed = 2 * 0.5 * (c(y0) + c(y1)) * (y1 - y0)       # linear taper -> exact
    raymer = 2.0 * (1 + 0.2 * design.wing.thickness_ratio) * s_exposed

    w = bu.component("wing")
    assert w.wetted_area_m2 == pytest.approx(raymer, rel=0.05)
    # and it must be the EXPOSED area that drives it, not the reference area
    assert w.wetted_area_m2 < 2.1 * g.area_m2
    print(f"\n[wing] S_exposed {s_exposed:.4f} m2  S_wet {w.wetted_area_m2:.4f} m2  "
          f"(Raymer approx {raymer:.4f})")


def test_fuselage_wetted_area_against_two_independent_integrations(design, bu):
    """Check 1 (tight): the same piecewise-linear body of revolution, but
    integrated numerically as 2*pi*r*sqrt(1+r'^2) dx on a fine grid instead
    of summed as exact frusta. Must agree to <0.5%.
    Check 2 (loose): Torenbeek's fuselage wetted-area correlation
    S_wet ~ pi*d*L*(1-2/f)^(2/3)*(1+1/f^2), which knows nothing about the
    station list. Must agree to 10%."""
    L, R = design.fuselage.length_m, design.fuselage.max_diameter_m / 2.0
    xs = np.array([s[0] for s in design.fuselage.stations]) * L
    rs = np.array([s[1] for s in design.fuselage.stations]) * R
    xf = np.linspace(xs[0], xs[-1], 200001)
    rf = np.interp(xf, xs, rs)
    drdx = np.gradient(rf, xf)
    numeric = np.trapezoid(2 * np.pi * rf * np.sqrt(1 + drdx ** 2), xf)

    f = L / (2 * R)
    torenbeek = np.pi * 2 * R * L * (1 - 2 / f) ** (2 / 3) * (1 + 1 / f ** 2)

    s_wet = bu.component("fuselage").wetted_area_m2
    assert s_wet == pytest.approx(numeric, rel=5e-3)
    assert s_wet == pytest.approx(torenbeek, rel=0.10)
    print(f"\n[fuselage] S_wet {s_wet:.4f} m2  numeric {numeric:.4f}  "
          f"Torenbeek {torenbeek:.4f}")


def test_boom_wetted_area_is_two_cylinders(design, bu):
    bg = derive_booms(design)
    expect = 2 * math.pi * design.booms.diameter_m * bg.length_m
    assert bu.component("booms").wetted_area_m2 == pytest.approx(expect, rel=1e-9)
    assert bg.length_m == pytest.approx(3.6456, abs=1e-3)      # verified baseline


def test_tail_wetted_area_is_both_panels_both_sides(design, bu):
    """The design file states the PROJECTED horizontal area; the wetted area
    must be built from the TRUE panel area of both inverted-V panels
    (derive_tail_panel), both surfaces."""
    tp = derive_tail_panel(design)
    s_wet = bu.component("tail").wetted_area_m2
    two_panels = 2 * tp.panel_area_m2
    assert s_wet == pytest.approx(2.02 * two_panels, rel=0.03)
    # projected area would understate it: cos^2(42 deg) = 0.552
    assert s_wet > 2.0 * design.tail.area_h_m2


def test_wetted_areas_come_from_the_design_file_not_from_constants(tmp_path, design):
    """Perturb the file and the geometry must move with it."""
    data = yaml.safe_load(Path(DESIGN_PATH).read_text())
    data["wing"]["area_m2"] = 1.44 * data["wing"]["area_m2"]      # span x1.2
    data["fuselage"]["length_m"] = 2.0 * data["fuselage"]["length_m"]
    data["booms"]["diameter_m"] = 2.0 * data["booms"]["diameter_m"]
    data["tail"]["area_h_m2"] = 2.0 * data["tail"]["area_h_m2"]
    p = tmp_path / "perturbed.yaml"
    p.write_text(yaml.safe_dump(data))
    pert = load_design(p)

    a = B.parasite_buildup(design, B.loiter_flow(design))
    b = B.parasite_buildup(pert, B.loiter_flow(pert))
    for name, factor in [("wing", 1.4), ("fuselage", 1.8),
                         ("booms", 1.9), ("tail", 1.9)]:
        ra = a.component(name).wetted_area_m2
        rb = b.component(name).wetted_area_m2
        assert rb > factor * ra, f"{name}: {rb:.4f} vs {ra:.4f} (x{rb / ra:.2f})"


def test_measured_airfoil_thickness_matches_the_stated_thickness_ratio(design):
    """The form factors use the thickness MEASURED from the real coordinate
    file, not the digits in the airfoil's name."""
    measured = max_thickness(load_airfoil(design.wing.airfoil))
    assert measured == pytest.approx(design.wing.thickness_ratio, rel=0.03)
    assert B.airfoil_thickness(design.wing.airfoil) == pytest.approx(measured, rel=1e-9)


# --------------------------------------------------------------------------
# the build-up itself
# --------------------------------------------------------------------------

def test_every_component_is_strictly_positive(bu):
    assert len(bu.components) >= 5
    for c in bu.components:
        assert c.drag_area_m2 > 0.0, c.name
        assert c.cd0 > 0.0, c.name
        if c.wetted_area_m2 is not None:
            assert c.wetted_area_m2 > 0.0, c.name
            assert 0.0 < c.cf < 0.02, c.name
            assert 1.0 <= c.form_factor < 2.0, c.name
            assert 1.0 <= c.interference_factor <= 1.5, c.name
            assert 0.0 <= c.laminar_fraction <= 1.0, c.name


def test_components_sum_to_total(bu):
    assert sum(c.drag_area_m2 for c in bu.components) == pytest.approx(
        bu.drag_area_m2, rel=1e-12)
    assert sum(c.cd0 for c in bu.components) == pytest.approx(bu.cd0, rel=1e-12)
    assert bu.cd0 == pytest.approx(bu.drag_area_m2 / bu.s_ref_m2, rel=1e-12)


def test_reference_area_is_the_wing_area(design, bu):
    assert bu.s_ref_m2 == pytest.approx(derive_wing(design.wing).area_m2, rel=1e-12)


def test_form_factors_are_in_published_ranges(bu):
    """Wing/tail: Raymer eq. 12.30 gives ~1.2-1.4 for 10-14% sections.
    Bodies: a fineness-7 pod is ~1.1-1.25, a fineness-40 tube is ~1.0."""
    assert 1.20 < bu.component("wing").form_factor < 1.45
    assert 1.10 < bu.component("tail").form_factor < 1.30
    assert 1.05 < bu.component("fuselage").form_factor < 1.30
    assert 1.00 < bu.component("booms").form_factor < 1.05


def test_wing_transition_defaults_to_the_verified_xfoil_result(design, bu):
    """The whole point of the module: x_tr 0.5023 (root) / 0.6051 (tip),
    measured with the verified XFOIL sequence, must be what drives the wing
    friction -- not an assumption of fully turbulent flow."""
    assert B.X_TR_WING_ROOT == pytest.approx(0.5023, abs=1e-4)
    assert B.X_TR_WING_TIP == pytest.approx(0.6051, abs=1e-4)
    lam = bu.component("wing").laminar_fraction
    assert 0.50 < lam < 0.61, lam


def test_laminar_fraction_moves_cd0_the_right_way_by_a_sane_amount(design, flow):
    """Direction: more laminar run -> less drag, monotonically.
    Magnitude: on a wing that is over half the wetted area, going from fully
    turbulent to the XFOIL transition must be worth a large but not absurd
    fraction -- 10-40% of total C_D0."""
    cds = [B.parasite_buildup(design, flow, x_tr_wing=(x, x)).cd0
           for x in (0.0, 0.2, 0.4, 0.6, 0.8)]
    assert all(b < a for a, b in zip(cds, cds[1:])), cds

    turb = B.parasite_buildup(design, flow, x_tr_wing=(0.0, 0.0)).cd0
    real = B.parasite_buildup(design, flow).cd0
    saving = (turb - real) / turb
    print(f"\n[laminar] fully turbulent wing {turb:.5f} -> XFOIL transition "
          f"{real:.5f}  ({100 * saving:.1f}% of total C_D0)")
    assert 0.10 < saving < 0.40

    # the saving must come from the wing, not leak into other components
    a = B.parasite_buildup(design, flow, x_tr_wing=(0.0, 0.0))
    b = B.parasite_buildup(design, flow)
    for name in ("fuselage", "booms", "tail"):
        assert a.component(name).cd0 == pytest.approx(b.component(name).cd0, rel=1e-12)


def test_wing_is_the_largest_component(bu):
    ranked = sorted(bu.components, key=lambda c: -c.drag_area_m2)
    assert ranked[0].name == "wing"
    assert bu.component("wing").cd0 / bu.cd0 > 0.35


def test_miscellaneous_allowance_is_a_stated_fraction_of_the_clean_sum(bu):
    misc = bu.component("miscellaneous")
    clean = bu.cd0 - misc.cd0
    assert misc.cd0 == pytest.approx(B.MISC_EXCRESCENCE_FRACTION * clean, rel=1e-12)
    assert 0.02 <= B.MISC_EXCRESCENCE_FRACTION <= 0.10


def test_total_cd0_in_a_defensible_band(bu):
    """BAND AND ITS REASONING. The report itself brackets C_D0: 0.016
    optimistic clean build / 0.020 realistic / 0.024 dirty with external
    antennas. This module builds up ONLY the surfaces the design file
    defines, with the measured 50-60% laminar run on the wing, no payload
    turret, no cooling installation and no landing gear -- i.e. exactly the
    optimistic clean build. Anything above 0.020 would mean the clean
    geometry alone had eaten the whole realistic budget; anything below
    0.012 would be beyond a sailplane and mean the wetted areas are wrong.
    """
    print("\n" + bu.table())
    assert 0.012 < bu.cd0 < 0.020


@pytest.mark.xfail(strict=True, reason=(
    "MEASURED, NOT TUNED: the component build-up gives C_D0 = 0.0153 for "
    "argus7_v1.yaml, -23.6% against the design file's stated 0.020, i.e. "
    "outside the +/-15% Phase-2 gate. It is not a coding error and it has not "
    "been dialled out: 0.0153 is what the four wetted bodies the design file "
    "actually defines produce with the XFOIL-measured 50-60% laminar run, and "
    "it lands on the report's own 'optimistic clean build' figure of 0.016. "
    "The missing ~0.0047 (0.018 m2 of drag area) belongs to hardware that is "
    "not in the geometry: the 50 kg payload installation above all, plus "
    "engine cooling, fuselage base drag and recovery/landing hardware. The "
    "fix is to add that hardware to design/*.yaml, not to raise a factor in "
    "argus7.aero.buildup. Run with -rx -s to see the build-up table."))
def test_total_cd0_against_report_baseline(bu):
    """The Phase-2 gate: C_D0 = 0.020 +/- 15%, i.e. [0.0170, 0.0230].

    XFAIL(strict), not a tuned pass, and strict so that it starts failing the
    moment someone makes it agree -- at which point the reason above has to be
    rewritten to say why it now closes.
    """
    print("\n" + bu.table())
    lo, hi = REPORT_CD0 * (1 - REPORT_CD0_BAND), REPORT_CD0 * (1 + REPORT_CD0_BAND)
    gap = bu.cd0 - REPORT_CD0
    assert lo <= bu.cd0 <= hi, (
        f"component build-up gives C_D0 = {bu.cd0:.5f}, the design file states "
        f"{REPORT_CD0:.5f}: {100 * gap / REPORT_CD0:+.1f}%, outside the +/-"
        f"{100 * REPORT_CD0_BAND:.0f}% gate [{lo:.5f}, {hi:.5f}].\n"
        f"NOT A TUNING TARGET. The build-up covers only the wetted surfaces the "
        f"design file defines (wing, pod, booms, tail) with the XFOIL-measured "
        f"laminar run, plus a {100 * B.MISC_EXCRESCENCE_FRACTION:.0f}% "
        f"excrescence allowance. The missing "
        f"{abs(gap):.5f} ({abs(gap) * bu.s_ref_m2:.4f} m2 of drag area) has to "
        f"come from items the design file does not contain: the 50 kg payload "
        f"installation, engine cooling, fuselage base drag, and any landing "
        f"gear or skid.\n" + bu.table())


def test_fully_turbulent_wing_reproduces_the_report_baseline(design, flow):
    """A FINDING, not a calibration.

    Re-run the same build-up with the only change being that the wing is
    assumed fully turbulent -- the conventional-conceptual-design default,
    and what you get if you never run XFOIL -- and C_D0 comes out at 0.0200,
    which is the design file's stated value to three decimal places.

    That is worth recording because it makes the -23.6% gap in
    test_total_cd0_against_report_baseline ambiguous in a way this module
    cannot resolve on its own. Either:

      (a) report §4's 0.020 is a fully-turbulent build-up of this same clean
          geometry, in which case it contains NO allowance for the payload
          installation, cooling or gear, and the true C_D0 of the built
          aircraft is 0.0153 + whatever that hardware costs; or
      (b) 0.020 is a laminar-flow build-up that does include that hardware,
          and the agreement here is a coincidence of two errors of the same
          size in opposite directions.

    Under (a) the endurance model is anti-conservative, because the missing
    hardware drag was never counted anywhere. Distinguishing them needs the
    report's own working, not another correlation.
    """
    turbulent = B.parasite_buildup(design, flow, x_tr_wing=(0.0, 0.0))
    laminar = B.parasite_buildup(design, flow)
    print(f"\n[interpretation] fully-turbulent wing C_D0 = {turbulent.cd0:.5f} "
          f"vs design file {REPORT_CD0:.5f} "
          f"({100 * (turbulent.cd0 - REPORT_CD0) / REPORT_CD0:+.1f}%); "
          f"with the XFOIL laminar run {laminar.cd0:.5f} "
          f"({100 * (laminar.cd0 - REPORT_CD0) / REPORT_CD0:+.1f}%)")
    assert abs(turbulent.cd0 - REPORT_CD0) / REPORT_CD0 < REPORT_CD0_BAND


def test_strip_count_is_converged(design, flow):
    """The wing integration must not be sensitive to its own discretisation."""
    coarse = B.parasite_buildup(design, flow, n_wing_strips=20).cd0
    fine = B.parasite_buildup(design, flow, n_wing_strips=800).cd0
    assert coarse == pytest.approx(fine, rel=1e-5)


def test_roughness_cutoff_does_not_bind_on_a_composite_airframe(design, flow):
    """Raymer's cutoff Reynolds number (eq. 12.28) is part of the method and is
    implemented, but for a smooth moulded composite surface it sits ~90x above
    the flight Reynolds number, so it must be inert here. If a future build
    specifies paint or tape this stops being true."""
    g = derive_wing(design.wing)
    assert B.cutoff_reynolds(g.mac_m) > 50 * g.mac_m * flow.reynolds_per_m
    assert B.cf_mixed(1e5, 0.5, 1.0) == B.cf_mixed(1e5, 0.5, None)
    # ... but a rough surface must actually clip it
    assert B.cf_mixed(1e7, 0.0, 1.0, roughness_m=1e-3) > B.cf_mixed(1e7, 0.0, None)
