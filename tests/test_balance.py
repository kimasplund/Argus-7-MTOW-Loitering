"""Longitudinal balance: CG, neutral point, static margin, fuel-burn CG travel.

WHY THIS FILE EXISTS. Before it, a grep for "static margin", "neutral point"
or "cg" across argus7/ returned nothing: the programme published a stability
line ("+14.7% MAC at CG 42%", docs/argus7_design_report.md section 2) that no
code in the repository could either reproduce or contradict. Two research packs
(research/configuration_hypotheses.md section 3,
research/empennage_trade.md open question 8) had already recorded, from hand
build-ups, that "the aircraft does not balance", and it was never followed up
in code. v2.0 then grew the wing 40% and moved the wing AC 25 mm aft with
nothing checking balance at all.

WHAT THIS FILE FOUND, in one paragraph. The NEUTRAL POINT half of the published
stability line reproduces: 52.95% MAC analytically and 58.30% MAC from the
vendored AVL on v1.0, bracketing a published ~55% MAC. The CG half does not, by 55% MAC. On the
committed wing station the CG sits at 97.0% MAC full and 135.1% MAC dry on
v1.0, and 61.9% -> 76.7% MAC on v2.0, i.e. BEHIND the neutral point at every
fuel state on both designs. Static margin is -44.0% MAC (v1.0) and -8.7% MAC
(v2.0) at full fuel and gets worse as fuel burns. The "CG travel <0.5% MAC"
claim is out by 76x on v1.0 and 30x on v2.0. All of it is one root cause --
wing.x_le_frac = 0.22, a value tagged `assumption` and sourced to nothing --
and the fix is a wing station near 0.37-0.40 (v1.0), which is inside the
0.365-0.456 band research/empennage_trade.md finding 8 reached by hand (and
below the 0.446-0.527 of the second build-up quoted alongside it -- the two
published hand build-ups disagree with each other by 33% MAC).

Every failing requirement below is an xfail(strict) carrying its measured
numbers, so it fails loudly in the reason text, and starts ERRORING the moment
someone makes it pass without rewriting the reason.

Run with `-s` to see the CG-travel and mass tables, `-rx` to see the reasons.
"""
from __future__ import annotations

import math
import shutil

import pytest

from argus7.analysis import balance as B
from argus7.design import geometry as G
from argus7.design.schema import load_design

V1_PATH = "design/argus7_v1.yaml"
V2_PATH = "design/argus7_v2.yaml"

# --- published claims under test -------------------------------------------
# docs/argus7_design_report.md section 2, "Static margin" row:
#   "+14.7% MAC at CG 42% (window 38-46% -> +10.7...+18.7%)"
REPORT_SM = 0.147
REPORT_CG_PCT_MAC = 0.42
REPORT_CG_WINDOW = (0.38, 0.46)
# research/design_pack.md line 26 and docs/report_outline.md line 8.
REPORT_NP_PCT_MAC = 0.55
# research/design_pack.md line 27: "Fuel tanks centered at 45% MAC (CG station)
#   -> CG travel <0.5% MAC full->empty (VA001/A330 trim-tank practice)"
REPORT_CG_TRAVEL_CLAIM = 0.005
# The window the programme set for itself:
# docs/superpowers/specs/2026-08-20-argus7-cad-sim-optimisation-design.md
# line 109, "Static margin | 8% <= SM <= 20% MAC". The assignment's window is
# 5-15%; the two overlap on 8-15%, and both verdicts below are identical under
# either, so the tighter conventional one is used and the spec's is asserted
# alongside it.
SM_WINDOW = (0.05, 0.15)
SPEC_SM_WINDOW = (0.08, 0.20)
# research/configuration_hypotheses.md appendix item 4: the fuel-at-the-AC CG
# travel, computed there from the report's own assumed CG, is 11.62% MAC.
PUBLISHED_FUEL_AT_AC_TRAVEL = 0.1162
# research/configuration_hypotheses.md section 3.3(a): "the lofted 0.4105 m3"
PUBLISHED_FUSELAGE_VOLUME_M3 = 0.4105
# same section: the pod moves the NP forward "7.3% MAC by Multhopp and 8.2% by
# Munk". balance.fuselage_np_shift_mac implements Munk.
PUBLISHED_MUNK_NP_SHIFT = 0.082


@pytest.fixture(scope="module")
def v1():
    return load_design(V1_PATH)


@pytest.fixture(scope="module")
def v2():
    return load_design(V2_PATH)


@pytest.fixture(scope="module", params=["v1.0", "v2.0"])
def design(request):
    return load_design(V1_PATH if request.param == "v1.0" else V2_PATH)


# =========================================================================
# 1. The mass build-up
# =========================================================================

def test_component_masses_reproduce_the_design_files_own_lines(design):
    """The build-up may split the airframe line and it may place mass, but it
    may never invent or lose any: it must sum to the design file's own mass
    lines exactly. (Whether THOSE sum to MTOW is a separate question, and on
    v2.0 the answer is no -- see test_v2_mass_budget_closes.)"""
    m = design.masses
    stated = (m.airframe + m.powertrain + m.avionics + m.recovery + m.payload
              + m.fuel)
    total = sum(mass for _, mass, _ in B.component_masses(design))
    assert total == pytest.approx(stated, abs=1e-9), (
        f"build-up sums to {total:.4f} kg against the design file's own lines "
        f"at {stated:.4f} kg\n" + B.mass_table(design))


def test_component_masses_cover_every_budget_line(design):
    """Every line of the report's section-3 budget, exactly once."""
    names = [n for n, _, _ in B.component_masses(design)]
    assert len(names) == len(set(names)), f"duplicate component names: {names}"
    for required in ("wing", "fuselage", "booms", "tail", "powertrain",
                     "avionics", "recovery", "payload", "fuel"):
        assert required in names, f"{required!r} missing from {names}"


def test_component_masses_are_all_positive_and_on_the_aircraft(design):
    """Positive mass, and a station between the nose and the aft end of the
    booms. A negative residual (which is how a bad wing-mass/airframe split
    shows up) must not be carried silently."""
    boom = G.derive_booms(design)
    for name, mass, x in B.component_masses(design):
        assert mass > 0.0, f"{name} has mass {mass:.4f} kg"
        assert 0.0 <= x <= boom.x_aft, (
            f"{name} sits at x = {x:.4f} m, outside [0, {boom.x_aft:.4f}]")


def test_fuel_line_matches_the_design_file(design):
    fuel = dict((n, m) for n, m, _ in B.component_masses(design))["fuel"]
    assert fuel == pytest.approx(design.masses.fuel, abs=1e-9)


def test_v1_mass_budget_closes(v1):
    """report section 3: "MTOW 250.0 | closes"."""
    assert B.mass_budget_residual_kg(v1) == pytest.approx(0.0, abs=1e-9)


@pytest.mark.xfail(strict=True, reason=(
    "MEASURED DEFECT IN design/argus7_v2.yaml, found by this module. The "
    "mass lines sum to 235.34 kg against a stated MTOW of 248.36 kg: 13.02 kg "
    "-- 5.2% of gross mass -- is unallocated. The cause is reconstructible "
    "from opt_runs/final_250kg.json, which records empty_kg = 97.389 for this "
    "design point. argus7.opt.coupled applies the engine-mass credit as "
    "empty = empty_mass_kg(...) + (P - 17)*(25/17)*0.6, i.e. -7.809 kg at "
    "P = 8.1496 kW, ON TOP of a fixed 25.0 kg powertrain. The YAML then wrote "
    "airframe = wing(39.203) + non_wing(28.0) - 7.809 = 59.394 -- the credit "
    "applied once -- AND powertrain = 25*(8.1496/17) = 11.985 -- the credit "
    "applied a second time. The self-consistent budget is airframe 67.20 kg "
    "and powertrain 17.19 kg, which sums to 248.36 kg exactly. THIS MATTERS "
    "FOR BALANCE: the missing 13.02 kg is airframe and powertrain, i.e. it "
    "belongs at x = 1.63-3.05 m, well aft of the CG, so allocating it takes "
    "v2.0's full-fuel static margin from -8.66% MAC to -23.90% MAC, a "
    "further -15.24% MAC "
    "(test_v2_reconciled_mass_budget_is_worse_not_better). Not fixed here: "
    "design/*.yaml is not this task's to edit, and the fix is a re-run of the "
    "optimiser's mass split, not a typo."))
def test_v2_mass_budget_closes(v2):
    residual = B.mass_budget_residual_kg(v2)
    assert residual == pytest.approx(0.0, abs=1e-6), (
        f"v2.0 mass lines sum to {v2.masses.mtow - residual:.2f} kg against a "
        f"stated MTOW of {v2.masses.mtow:.2f} kg: {residual:+.2f} kg "
        f"unallocated\n" + B.mass_table(v2))


def test_fuselage_loft_volume_reproduces_the_published_figure(v1):
    """Independent anchor: research/configuration_hypotheses.md section 3.3(a)
    computes the v1.0 pod volume as 0.4105 m3 from the same loft stations, and
    the Munk neutral-point term is directly proportional to it.

    3% tolerance, stated and justified rather than fitted: the loft here is
    LINEAR between stations (the same reading
    argus7.aero.buildup.fuselage_wetted_area takes) and returns 0.4022 m3,
    while the CAD's SPLINE loft of the identical stations
    (argus7.cad.model.build_fuselage) measures 0.4384 m3. The published figure
    sits between them. The chord of a convex spline always under-reads, so
    this module's Munk term is the OPTIMISTIC end of the range by 2-9% -- it
    understates how far forward the pod drags the neutral point."""
    vol = B.fuselage_volume_m3(v1)
    assert vol == pytest.approx(PUBLISHED_FUSELAGE_VOLUME_M3, rel=0.03), (
        f"linear loft volume {vol:.4f} m3 vs published "
        f"{PUBLISHED_FUSELAGE_VOLUME_M3} m3")


# =========================================================================
# 2. Percent-MAC bookkeeping -- the classic silent defect
# =========================================================================

def test_percent_mac_is_measured_from_the_mac_leading_edge(design):
    """%MAC is measured from the LEADING EDGE OF THE MAC, not from the nose
    and not from the wing root LE. Getting this wrong shifts every number in
    this file by 178% MAC on v1.0 and still 'looks like a percentage'."""
    g = G.derive_wing(design.wing)
    mac_le = G.wing_ac_x(design) - 0.25 * g.mac_m
    assert B.percent_mac(design, mac_le) == pytest.approx(0.0, abs=1e-12)
    assert B.percent_mac(design, mac_le + g.mac_m) == pytest.approx(1.0, abs=1e-12)
    assert B.percent_mac(design, G.wing_ac_x(design)) == pytest.approx(0.25, abs=1e-12)


def test_mac_leading_edge_station_matches_the_published_v1_value(v1):
    """research/configuration_hypotheses.md appendix: MAC LE at x = 0.78331 m,
    MAC 0.44123 m on v1.0."""
    g = G.derive_wing(v1.wing)
    assert B.mac_le_x(v1) == pytest.approx(0.78331, abs=1e-4)
    assert g.mac_m == pytest.approx(0.44123, abs=1e-4)


# =========================================================================
# 3. Neutral point
# =========================================================================

def test_neutral_point_is_the_wing_ac_plus_the_tail_term(design):
    """Algebraic replication of Xnp/MAC = Xac_w/MAC + Vh*(a_t/a_w)*(1-de/da),
    recomputed here from argus7.design.geometry rather than from balance.py's
    own intermediates, so that dropping any factor is caught."""
    np_ = B.neutral_point(design)
    vh = G.tail_volume_h(design)
    expect = 0.25 + vh * (np_.a_tail / np_.a_wing) * (1.0 - np_.downwash_gradient)
    assert np_.percent_mac == pytest.approx(expect, abs=1e-12)
    assert np_.tail_contribution_mac == pytest.approx(expect - 0.25, abs=1e-12)
    assert np_.volume_coefficient == pytest.approx(vh, abs=1e-12)


def test_neutral_point_tail_term_is_actually_present(design):
    """A tail contributing nothing means the formula lost its Vh term."""
    np_ = B.neutral_point(design)
    assert np_.tail_contribution_mac > 0.10, (
        f"tail moves the NP only {100 * np_.tail_contribution_mac:.2f}% MAC aft")


def test_downwash_gradient_is_physical(design):
    np_ = B.neutral_point(design)
    assert 0.0 < np_.downwash_gradient < 1.0
    ar = design.wing.aspect_ratio
    assert np_.downwash_gradient == pytest.approx(
        2.0 * np_.a_wing / (math.pi * ar), rel=1e-12)
    # On AR 22-24 the far-field downwash must be small; 0.3-0.4 would be an
    # AR-6 answer and would mean the aspect ratio never reached the formula.
    assert 0.10 < np_.downwash_gradient < 0.22


def test_lift_curve_slopes_are_sane(design):
    """A high-AR wing approaches 2*pi/rad; the AR-3 tail panel must be well
    below it. A tail slope >= the wing's would inflate the neutral point."""
    np_ = B.neutral_point(design)
    assert 4.5 < np_.a_wing < 2.0 * math.pi
    assert 2.5 < np_.a_tail < np_.a_wing


def test_bigger_tail_moves_the_neutral_point_aft(design):
    """Sign guard: doubling the tail area must move the NP aft, not forward."""
    base = B.neutral_point(design).percent_mac
    bigger = design.model_copy(deep=True)
    bigger.tail.area_h_m2 *= 2.0
    assert B.neutral_point(bigger).percent_mac > base + 0.10


def test_munk_fuselage_term_reproduces_the_published_shift(v1):
    """Independent anchor: the pod is published as moving the NP forward 8.2%
    MAC by Munk. It must be reproduced from the loft, not asserted."""
    shift = B.fuselage_np_shift_mac(v1)
    assert shift < 0.0, "the fuselage must move the neutral point FORWARD"
    assert abs(shift) == pytest.approx(PUBLISHED_MUNK_NP_SHIFT, abs=0.006), (
        f"Munk fuselage shift {100 * shift:+.2f}% MAC vs published -8.2% MAC")


def test_v1_neutral_point_reproduces_the_published_55_percent(v1):
    """research/design_pack.md and docs/report_outline.md both state NP ~= 55%
    MAC. THIS HALF OF THE PUBLISHED STABILITY LINE REPRODUCES -- which is what
    makes the CG half's failure a CG finding and not a modelling error."""
    np_ = B.neutral_point(v1)
    assert np_.percent_mac == pytest.approx(REPORT_NP_PCT_MAC, abs=0.03), (
        f"wing+tail NP = {100 * np_.percent_mac:.2f}% MAC against a published "
        f"{100 * REPORT_NP_PCT_MAC:.0f}% MAC")


@pytest.mark.skipif(shutil.which(B.AVL_BIN) is None
                    and not __import__("pathlib").Path(B.AVL_BIN).exists(),
                    reason="vendor/bin/avl not present")
def test_avl_confirms_the_analytic_neutral_point(design):
    """Independent vortex-lattice cross-check on a wing + inverted-V deck.

    AVL is inviscid and carries no fuselage, so it is the right comparison for
    neutral_point(include_fuselage=False) and NOT for the Munk-corrected
    value.

    Measured: v1.0 AVL 58.30% vs analytic 52.95% MAC;
              v2.0 AVL 57.82% vs analytic 53.20% MAC.
    The published ~55% MAC sits BETWEEN the two methods. 6% MAC tolerance,
    stated with its cause rather than fitted -- and the cause is MEASURED by
    test_avl_decomposition_locates_the_gap_in_the_wing_term rather than
    argued: the entire gap is in the WING term. AVL puts the isolated wing's
    AC at 30.2% MAC, not the 25% MAC of X_AC_WING_FRAC_MAC; the analytic TAIL
    term matches AVL to within 0.8% MAC on both designs, so the downwash
    estimate and the panel-AR tail slope are both vindicated.

    ADVERSARIAL REVIEW: this docstring previously attributed the gap to tail
    height -- the inverted-V hanging 614 mm below the wake plane, which
    downwash_gradient has no term for, supposedly making AVL's tail more
    effective. That explanation is wrong and the decomposition disproves it:
    AVL's tail term is 28.11% MAC against the analytic 27.95% on v1.0, and on
    v2.0 AVL's tail term is SMALLER than the analytic one (27.37% vs 28.20%),
    the opposite of what a tail-height argument predicts.

    Either way the analytic value is the conservative (forward, least stable)
    end of the pair, and every finding below is a CG-aft-of-NP finding, so it
    survives the more favourable AVL value too: see
    test_finding_survives_the_avl_neutral_point.
    """
    avl = B.avl_neutral_point(design)
    ana = B.neutral_point(design)
    print(f"\n{design.variant}: AVL Xnp = {avl.x_np_m:.4f} m "
          f"({100 * avl.percent_mac:.2f}% MAC), analytic "
          f"{100 * ana.percent_mac:.2f}% MAC")
    assert avl.percent_mac > ana.percent_mac - 0.01, (
        "AVL puts the neutral point FORWARD of the analytic estimate -- the "
        "tail-height argument in this docstring is then backwards")
    assert avl.percent_mac == pytest.approx(ana.percent_mac, abs=0.06)


@pytest.mark.skipif(shutil.which(B.AVL_BIN) is None
                    and not __import__("pathlib").Path(B.AVL_BIN).exists(),
                    reason="vendor/bin/avl not present")
def test_avl_decomposition_locates_the_gap_in_the_wing_term(design):
    """ADDED IN ADVERSARIAL REVIEW. Splitting the AVL neutral point into its
    wing and tail parts, by running the same deck a second time with the tail
    SURFACE block deleted, says WHERE the analytic relation differs -- rather
    than leaving a 6% MAC tolerance justified by an untested story.

    Measured:
      v1.0  AVL wing-alone AC 30.19% MAC   AVL tail term 28.11% MAC
            analytic wing AC  25.00% MAC   analytic tail 27.95% MAC
      v2.0  AVL wing-alone AC 30.45% MAC   AVL tail term 27.37% MAC
            analytic wing AC  25.00% MAC   analytic tail 28.20% MAC

    So the TAIL model -- the tail volume coefficient, the panel-AR lift-curve
    slope and the 2*a_w/(pi*AR) downwash gradient together -- is right to
    within 0.8% MAC against a vortex lattice. The whole 4.6-5.4% MAC of
    method difference is the WING AC, which a vortex lattice puts about 5% MAC
    aft of the thin-airfoil quarter-chord on this planform. That is in the
    FAVOURABLE direction (a further-aft NP is more stable), so the analytic
    static margins in this file are understated by ~5% MAC -- and v2.0 is
    still unstable on the AVL value at every fuel state
    (test_finding_survives_the_avl_neutral_point).
    """
    import pathlib
    import subprocess
    import tempfile

    g = G.derive_wing(design.wing)
    with tempfile.TemporaryDirectory() as td:
        deck = B.write_avl_deck(design, f"{td}/full.avl", td)
        text = pathlib.Path(deck).read_text()
        wing_only = pathlib.Path(f"{td}/wing.avl")
        wing_only.write_text(text[:text.index("SURFACE\nTail")])

        def xnp(path):
            proc = subprocess.run(
                [B.AVL_BIN], input=f"load {path}\noper\na a 2.0\nx\nst\n\nquit\n",
                capture_output=True, text=True, timeout=300.0)
            assert "Too many airfoil points" not in proc.stdout
            hits = [ln for ln in proc.stdout.splitlines() if "Xnp" in ln]
            assert hits, proc.stdout[-2000:]
            return float(hits[-1].split("Xnp")[1].split("=")[1].split()[0])

        x_full, x_wing = xnp(deck), xnp(str(wing_only))

    ana = B.neutral_point(design)
    avl_wing_ac = B.percent_mac(design, x_wing)
    avl_tail_term = (x_full - x_wing) / g.mac_m
    print(f"\n{design.variant}: AVL wing-alone AC {100 * avl_wing_ac:.2f}% MAC "
          f"(analytic assumes {100 * B.X_AC_WING_FRAC_MAC:.2f}%); AVL tail term "
          f"{100 * avl_tail_term:.2f}% MAC (analytic "
          f"{100 * ana.tail_contribution_mac:.2f}%)")

    assert avl_tail_term == pytest.approx(ana.tail_contribution_mac, abs=0.015), (
        "the analytic tail term no longer matches AVL -- the downwash "
        "gradient or the tail lift-curve slope has drifted")
    assert avl_wing_ac > B.X_AC_WING_FRAC_MAC + 0.03, (
        "AVL no longer puts the isolated wing AC well aft of the quarter-MAC "
        "-- the tolerance in test_avl_confirms_the_analytic_neutral_point is "
        "then justified by nothing")
    assert avl_wing_ac < 0.35


# =========================================================================
# 4. CG and fuel-burn travel
# =========================================================================

def test_cg_full_and_empty_differ(design):
    assert B.cg_position(design, 1.0).x_cg_m != pytest.approx(
        B.cg_position(design, 0.0).x_cg_m, abs=1e-6)


def test_cg_is_monotonic_in_fuel_fraction(design):
    xs = [B.cg_position(design, f / 20.0).x_cg_m for f in range(21)]
    diffs = [b - a for a, b in zip(xs[:-1], xs[1:])]
    assert all(d > 0 for d in diffs) or all(d < 0 for d in diffs), (
        "CG is not monotonic in fuel fraction -- the moment sum is wrong")


def test_cg_at_zero_fuel_equals_the_dry_build_up(design):
    items = [(n, m, x) for n, m, x in B.component_masses(design) if n != "fuel"]
    m = sum(i[1] for i in items)
    x = sum(i[1] * i[2] for i in items) / m
    assert B.cg_position(design, 0.0).x_cg_m == pytest.approx(x, abs=1e-12)


def test_cg_rejects_a_fuel_fraction_outside_the_unit_interval(design):
    for bad in (-0.01, 1.01):
        with pytest.raises(ValueError):
            B.cg_position(design, bad)


def test_cg_travel_matches_the_published_closed_form(design):
    """research/configuration_hypotheses.md appendix item 4 states the burn
    relation explicitly, including the trap it exists to correct:
        travel = m_fuel * (x_cg_full - x_fuel) / m_empty
    i.e. divided by the EMPTY mass, not by the gross mass. m_empty is taken
    from the build-up rather than from MTOW - m_fuel, because on v2.0 those
    two differ by the 13.02 kg of test_v2_mass_budget_closes."""
    items = B.component_masses(design)
    m_fuel = dict((n, m) for n, m, _ in items)["fuel"]
    m_empty = sum(m for n, m, _ in items if n != "fuel")
    x_fuel = B.fuel_centroid_x(design)
    full = B.cg_position(design, 1.0).x_cg_m
    expect = m_fuel * (full - x_fuel) / m_empty
    got = B.cg_position(design, 0.0).x_cg_m - full
    assert got == pytest.approx(expect, rel=1e-9)


def test_published_fuel_at_ac_cg_travel_reproduces(v1):
    """The one CG-travel number the repository has already published,
    recomputed here from this module's geometry: with the fuel centroid ON the
    wing AC and the CG where the report ASSUMES it (42% MAC), travel is 11.62%
    MAC -- already 23x the "<0.5% MAC" the design pack claims for exactly that
    configuration, before anyone asks where the CG really is."""
    g = G.derive_wing(v1.wing)
    x_cg_full = B.mac_le_x(v1) + REPORT_CG_PCT_MAC * g.mac_m
    x_fuel = G.wing_ac_x(v1)
    m_fuel = v1.masses.fuel
    travel = m_fuel * (x_cg_full - x_fuel) / (v1.masses.mtow - m_fuel) / g.mac_m
    assert travel == pytest.approx(PUBLISHED_FUEL_AT_AC_TRAVEL, abs=0.002)


def test_all_fuel_is_placed_in_a_wing_that_cannot_hold_it(v1, v2):
    """ADDED IN ADVERSARIAL REVIEW: an assumption balance.py makes silently.

    fuel_centroid_x puts 100% of design.masses.fuel at the wing-box centroid.
    That is sound on v2.0 -- argus7.opt.design_space.wing_fuel_capacity_kg
    gives it 138.54 kg of tank against 100.97 kg carried -- but on v1.0 the
    same model gives 66.02 kg against 101.50 kg carried. 35.48 kg of v1.0's
    fuel, 14% of its MTOW, is placed somewhere it cannot physically be.

    This is the repository's standing wing-fuel-volume escalation, not a new
    finding, but it belongs in the assumption register because it bounds the
    v1.0 numbers: a fuselage tank would sit AFT of 41% MAC (the pod's own
    centroid is at 191% MAC), so relocating the surplus can only make v1.0's
    CG worse. The v1.0 verdict is therefore an upper bound on its stability,
    and v2.0 -- the design point the assignment asks about -- is unaffected.
    """
    import torch

    from argus7.opt.design_space import wing_fuel_capacity_kg
    tt = lambda v: torch.tensor(float(v), dtype=torch.float64)
    for d, fits in ((v1, False), (v2, True)):
        w = d.wing
        cap = float(wing_fuel_capacity_kg(tt(w.area_m2), tt(w.aspect_ratio),
                                          tt(w.taper_ratio),
                                          tt(w.thickness_ratio)))
        print(f"\n{d.variant}: wing tank capacity {cap:.2f} kg against "
              f"{d.masses.fuel:.2f} kg carried "
              f"({cap - d.masses.fuel:+.2f} kg); balance.py puts all of it at "
              f"{100 * B.percent_mac(d, B.fuel_centroid_x(d)):.1f}% MAC")
        assert (cap >= d.masses.fuel) is fits, (
            f"{d.variant}: wing tank capacity {cap:.2f} kg vs {d.masses.fuel:.2f} "
            "kg carried -- the docstring of this test is now out of date")


def test_wing_tanks_are_not_at_the_aerodynamic_centre(design):
    """report section 2 says "wing tanks at the AC"; README repeats it as the
    reason CG travel stays small. It is geometrically impossible for a
    conventional wing box: the box lies between a ~15% front spar and a ~65%
    rear spar, so its volume centroid is near 40% of local chord, and the AC is
    at 25%. Measured offset: +71 mm (v1.0) and +88 mm (v2.0) AFT of the AC,
    i.e. 16% MAC. research/design_pack.md's own wording -- "fuel tanks centered
    at 45% MAC (CG station)" -- is the self-consistent one and is what this
    module reproduces; the report's "at the AC" is not."""
    x_fuel = B.fuel_centroid_x(design)
    assert x_fuel > G.wing_ac_x(design), (
        "the wing-box fuel centroid must lie AFT of the quarter-chord AC")
    assert 0.30 < B.percent_mac(design, x_fuel) < 0.50


# =========================================================================
# 5. Static margin -- the questions that decide the aircraft
# =========================================================================

def test_static_margin_sign_convention(design):
    """SM = (Xnp - Xcg)/MAC: positive when the CG is FORWARD of the NP."""
    sm = B.static_margin(design, 1.0)
    np_ = B.neutral_point(design)
    cg = B.cg_position(design, 1.0)
    g = G.derive_wing(design.wing)
    assert sm == pytest.approx((np_.x_np_m - cg.x_cg_m) / g.mac_m, abs=1e-12)
    assert sm == pytest.approx(np_.percent_mac - cg.percent_mac, abs=1e-12)


def test_moving_mass_aft_reduces_the_static_margin(design):
    """Sign guard on the whole chain: a heavier pusher powertrain, which is the
    most aft major mass, must make the aircraft less stable."""
    base = B.static_margin(design, 1.0)
    heavier = design.model_copy(deep=True)
    heavier.masses.powertrain += 10.0
    assert B.static_margin(heavier, 1.0) < base


def test_cg_travel_is_the_static_margin_excursion(design):
    assert B.cg_travel(design) == pytest.approx(
        B.static_margin(design, 0.0) - B.static_margin(design, 1.0), abs=1e-12)


def test_moving_the_wing_aft_increases_the_static_margin(design):
    """The lever the balance fix uses, and the monotonicity
    solve_x_le_frac_for_static_margin's bisection depends on."""
    base = B.static_margin(design, 1.0)
    aft = design.model_copy(deep=True)
    aft.wing.x_le_frac += 0.05
    assert B.static_margin(aft, 1.0) > base


@pytest.mark.xfail(strict=True, reason=(
    "THE FINDING, v1.0. Measured on design/argus7_v1.yaml at the committed "
    "wing station (wing.x_le_frac = 0.22, x_le = 0.748 m): the CG sits at "
    "97.0% MAC at full fuel and 135.1% MAC dry, against a neutral point at "
    "52.95% MAC (AVL, independently: 58.30%). The CG is therefore 194 mm AFT "
    "of the neutral "
    "point at full fuel and 363 mm aft of it dry -- static margin -44.0% MAC "
    "to -82.2% MAC. This is not a marginal aeroplane, it is a divergent one. "
    "CORRECTED IN ADVERSARIAL REVIEW: this reason previously read '380 mm aft "
    "dry' (it is 363 mm) and claimed the dry CG at 135.1% MAC 'lands inside "
    "the 107-153% MAC band' of research/configuration_hypotheses.md section 3. "
    "It does not, and the band is not a CG station: that source says the dry "
    "CG lands 0.47-0.67 m AFT OF THE 42% MAC TARGET, which is what 107-153% "
    "MAC measures. This module's dry CG is 0.411 m aft of that target, i.e. "
    "93.1% MAC of excursion -- 13% BELOW the published band, not inside it. "
    "It corroborates the direction and the order of magnitude of a finding "
    "the programme has recorded twice and acted on zero times; it is not the "
    "same number. (Asserted, not merely claimed, by "
    "test_v1_dry_cg_excursion_against_the_published_band.)"))
def test_v1_neutral_point_is_aft_of_the_cg(v1):
    """THE stability requirement. A CG aft of the neutral point is a
    longitudinally unstable aeroplane."""
    _assert_np_aft_of_cg(v1)


@pytest.mark.xfail(strict=True, reason=(
    "THE FINDING, v2.0 -- and the question this task was set to answer: NO, "
    "v2.0 DOES NOT BALANCE, at any point in the fuel burn. Measured: neutral "
    "point 53.20% MAC (AVL, independently: 57.82%), CG 61.9% MAC at full "
    "fuel moving to "
    "76.7% MAC dry, so the CG is 45 mm aft of the neutral point full and 122 "
    "mm aft of it dry. Static margin -8.7% MAC -> -23.5% MAC. v2.0 is closer "
    "than v1.0 only because its 40% larger wing has a 17% longer MAC and its "
    "wing AC moved 25 mm aft, not because anything about the balance was "
    "addressed -- balance was never in the optimiser's objective or its "
    "constraint set. And this is the OPTIMISTIC reading: 13.02 kg of v2.0's "
    "mass budget is unallocated (test_v2_mass_budget_closes) and it belongs "
    "aft; allocating it takes the full-fuel static margin to -23.90% MAC."))
def test_v2_neutral_point_is_aft_of_the_cg(v2):
    """THE stability requirement, on the optimised design point."""
    _assert_np_aft_of_cg(v2)


def _assert_np_aft_of_cg(design):
    np_ = B.neutral_point(design)
    for ff in (1.0, 0.5, 0.0):
        cg = B.cg_position(design, ff)
        assert np_.x_np_m > cg.x_cg_m, (
            f"{design.variant}: at fuel fraction {ff:.2f} the CG is at "
            f"{100 * cg.percent_mac:.1f}% MAC and the neutral point at "
            f"{100 * np_.percent_mac:.1f}% MAC -- the CG is "
            f"{1000 * (cg.x_cg_m - np_.x_np_m):.0f} mm AFT of the neutral "
            f"point, static margin {100 * B.static_margin(design, ff):+.1f}% "
            f"MAC\n" + B.cg_travel_table(design))


@pytest.mark.xfail(strict=True, reason=(
    "THE PUBLISHED NUMBER DOES NOT REPRODUCE. docs/argus7_design_report.md "
    "section 2 publishes '+14.7% MAC at CG 42%'. Measured at full fuel: "
    "-44.0% MAC at CG 97.0% MAC -- a 58.7% MAC discrepancy, and the sign is "
    "the part that matters. The neutral-point half of the same line DOES "
    "reproduce (52.95% analytic / 58.30% AVL, bracketing the published ~55%, see "
    "test_v1_neutral_point_reproduces_the_published_55_percent), so this is "
    "not a modelling artefact: the report's 42% MAC CG is an assumed target "
    "that no mass build-up on the committed geometry supports. It cannot be "
    "closed by tuning the assumptions in argus7.analysis.balance either -- "
    "moving ALL 63 kg of payload, avionics and recovery to the nose at x = 0 "
    "still leaves the v1.0 CG at 72% MAC. It is the wing station, not the "
    "equipment layout: wing.x_le_frac must be 0.371-0.401 rather than 0.22."))
def test_v1_reproduces_the_published_static_margin(v1):
    """+/-3% MAC tolerance -- generous for a preliminary-design method, and
    still 5x tighter than the report's own 38-46% CG window, which it states
    as +10.7...+18.7% MAC."""
    sm = B.static_margin(v1, 1.0)
    cg = B.cg_position(v1, 1.0)
    assert sm == pytest.approx(REPORT_SM, abs=0.03), (
        f"measured SM {100 * sm:+.1f}% MAC at CG {100 * cg.percent_mac:.1f}% "
        f"MAC, against the published {100 * REPORT_SM:+.1f}% MAC at CG "
        f"{100 * REPORT_CG_PCT_MAC:.0f}% MAC\n" + B.cg_travel_table(v1))


@pytest.mark.xfail(strict=True, reason=(
    "docs/argus7_design_report.md section 2 states a CG window of 38-46% MAC. "
    "Measured v1.0 CG: 97.0% MAC full, 135.1% MAC dry. The window is 35.3 mm "
    "wide; the CG misses it by 189 mm at full fuel and by 383 mm dry."))
def test_v1_cg_lies_in_the_published_window(v1):
    lo, hi = REPORT_CG_WINDOW
    for ff in (1.0, 0.0):
        pct = B.cg_position(v1, ff).percent_mac
        assert lo <= pct <= hi, (
            f"at fuel fraction {ff:.1f} the CG is at {100 * pct:.1f}% MAC, "
            f"outside the published {100 * lo:.0f}-{100 * hi:.0f}% window")


@pytest.mark.xfail(strict=True, reason=(
    "THE ASSIGNED QUESTION, answered with numbers: v2.0's static margin is "
    "OUTSIDE the 5-15% MAC window at EVERY fuel fraction, and outside the "
    "programme's own 8-20% MAC spec window too. It runs -8.7% MAC at full "
    "fuel to -23.5% MAC dry -- negative throughout, i.e. statically unstable "
    "in pitch for the whole 117 h mission, and getting worse for every one of "
    "them. The excursion across the burn is -14.86% MAC, which is 30x the "
    "'<0.5% MAC' the design pack claims for fuel tanks at the AC and is "
    "itself larger than the entire acceptable window."))
def test_v2_static_margin_stays_inside_the_window_across_the_whole_burn(v2):
    """THE QUESTION THAT MATTERS. v2.0 carries 100.97 kg of fuel out of
    248.36 kg -- 40.7% of gross mass."""
    lo, hi = SM_WINDOW
    out = [(1.0 - i / 10.0, B.static_margin(v2, 1.0 - i / 10.0))
           for i in range(11)]
    out = [(ff, sm) for ff, sm in out if not lo <= sm <= hi]
    assert not out, (
        f"v2.0 static margin leaves the {100 * lo:.0f}-{100 * hi:.0f}% MAC "
        "window at fuel fractions "
        + ", ".join(f"{ff:.1f} -> {100 * sm:+.1f}% MAC" for ff, sm in out)
        + "\n" + B.cg_travel_table(v2))


@pytest.mark.xfail(strict=True, reason=(
    "The programme's own pre-registered gate "
    "(docs/superpowers/specs/2026-08-20-argus7-cad-sim-optimisation-design.md "
    "line 109, '8% <= SM <= 20% MAC', and line 178, which makes 'no "
    "regression on static margin validity' a conjunctive adoption gate for "
    "the challenger) is not met by EITHER design point at any fuel state: "
    "v1.0 runs -44.0...-82.2% MAC and v2.0 -8.7...-23.5% MAC. v2.0 was "
    "adopted against a gate that was never evaluated, because until now "
    "nothing in argus7/ could evaluate it."))
def test_both_designs_meet_the_programmes_own_static_margin_gate(design):
    lo, hi = SPEC_SM_WINDOW
    for i in range(11):
        ff = 1.0 - i / 10.0
        sm = B.static_margin(design, ff)
        assert lo <= sm <= hi, (
            f"{design.variant} at fuel fraction {ff:.1f}: SM "
            f"{100 * sm:+.1f}% MAC, outside {100 * lo:.0f}-{100 * hi:.0f}%")


@pytest.mark.xfail(strict=True, reason=(
    "research/design_pack.md: 'Fuel tanks centered at 45% MAC (CG station) -> "
    "CG travel <0.5% MAC full->empty'. Measured static-margin excursion "
    "across the burn: -38.15% MAC on v1.0 (76x the claim) and -14.86% MAC on "
    "v2.0 (30x). The mechanism the claim rests on is sound -- fuel at the CG "
    "moves the CG not at all -- but it is conditional on the CG being where "
    "the report assumes. It is not: the fuel centroid sits at 41.2% MAC "
    "(v1.0) / 42.1% MAC (v2.0), close to the claimed 45%, while the CG sits "
    "at 97.0% / 61.9% MAC. Under the report's OWN assumed 42% MAC CG the "
    "travel would be 0.57% MAC on v1.0 -- still not under 0.5%, but the right "
    "order. The claim fails because the CG assumption fails, not because the "
    "tanks are in the wrong place."))
def test_report_claim_of_half_percent_cg_travel(design):
    travel = abs(B.cg_travel(design))
    assert travel <= REPORT_CG_TRAVEL_CLAIM, (
        f"{design.variant}: CG travel over the burn is {100 * travel:.2f}% "
        f"MAC, {travel / REPORT_CG_TRAVEL_CLAIM:.0f}x the claimed "
        f"{100 * REPORT_CG_TRAVEL_CLAIM:.1f}% MAC\n"
        + B.cg_travel_table(design))


# =========================================================================
# 6. Is the finding robust to the assumptions it rests on?
# =========================================================================

def test_v2_reconciled_mass_budget_is_worse_not_better(v2):
    """The 13.02 kg that v2.0's budget loses belongs to the airframe and the
    powertrain -- both aft of the CG. Allocating it as
    argus7.opt.coupled's own arithmetic implies (airframe 67.20 kg, powertrain
    17.19 kg, which sums to MTOW exactly) must make the balance WORSE, so the
    finding cannot be an artefact of the missing mass."""
    fixed = v2.model_copy(deep=True)
    fixed.masses.airframe = 67.203
    fixed.masses.powertrain = 17.186
    assert B.mass_budget_residual_kg(fixed) == pytest.approx(0.0, abs=0.02)
    before, after = B.static_margin(v2, 1.0), B.static_margin(fixed, 1.0)
    print(f"\nv2.0 SM at full fuel: {100 * before:+.2f}% MAC as committed, "
          f"{100 * after:+.2f}% MAC with the 13.02 kg allocated "
          f"({100 * (after - before):+.2f}% MAC)")
    assert after < before


def _sm_with_group_at(design, x_group: float, fuel_fraction: float = 1.0) -> float:
    """Static margin with payload + avionics + recovery relocated en bloc to
    x_group. 63.0 kg on both designs -- a quarter of the aircraft."""
    grp = ("payload", "avionics", "recovery")
    items = B.component_masses(design)
    m = sum(mass * (fuel_fraction if n == "fuel" else 1.0) for n, mass, _ in items)
    moment = sum(mass * (fuel_fraction if n == "fuel" else 1.0)
                 * (x_group if n in grp else x)
                 for n, mass, x in items)
    return B.neutral_point(design).percent_mac - B.percent_mac(design, moment / m)


def test_how_far_forward_the_equipment_would_have_to_move(v1, v2):
    """The equipment stations in balance.py are its weakest input -- the
    repository has never had an equipment layout
    (research/configuration_hypotheses.md open question 6, "Not resolvable by
    analysis"). So bound it: relocate the whole 63.0 kg of payload, avionics
    and recovery -- a quarter of the aircraft -- and find the station that
    would buy a 10% MAC static margin at full fuel.

    Measured, against a build-up station of 0.5865 m:
      v1.0 needs x = -0.360 m: 360 mm AHEAD OF THE NOSE. There is no
           equipment layout, at all, that balances v1.0 at this wing station
           -- with all 63 kg at x = 0 it is still at -10.5% MAC.
      v2.0 needs x = 0.226 m: 360 mm further forward, inside a nose cone
           264 mm in diameter there, with the 50 kg EO/IR gimbal ahead of
           both the parachute and the avionics.

    QUALIFIED IN ADVERSARIAL REVIEW, because the original wording of this
    docstring ("the imbalance is not an artefact of the assumed layout")
    overstated the v2.0 half. It holds absolutely on v1.0, which cannot be
    balanced by ANY layout. It does NOT hold absolutely on v2.0: with all
    63 kg at the nose v2.0 reaches +21.7% MAC, so v2.0 IS reachable by layout
    alone, and the 300 mm threshold asserted below is only 60 mm clear of
    passing on it. What is true of v2.0 is the weaker, still decisive claim:
    balancing it needs a third of a metre of forward relocation of a quarter
    of the aircraft, into a 264 mm nose cone, whereas 262 mm of wing station
    does the same job. The wing station is the cheap lever, not the only one.
    """
    from scipy.optimize import brentq
    for d in (v1, v2):
        items = B.component_masses(d)
        grp = ("payload", "avionics", "recovery")
        mg = sum(m for n, m, _ in items if n in grp)
        xg = sum(m * x for n, m, x in items if n in grp) / mg
        need = brentq(lambda x: _sm_with_group_at(d, x) - 0.10, -5.0, 5.0)
        print(f"\n{d.variant}: {mg:.1f} kg of payload+avionics+recovery is at "
              f"x = {xg:.4f} m (SM {100 * _sm_with_group_at(d, xg):+.1f}% MAC); "
              f"SM +10% MAC would need x = {need:.4f} m, i.e. "
              f"{1000 * (xg - need):.0f} mm further forward. At the nose "
              f"(x = 0) the SM is {100 * _sm_with_group_at(d, 0.0):+.1f}% MAC.")
        assert need < xg - 0.30, (
            f"{d.variant} would balance on a {1000 * (xg - need):.0f} mm "
            "equipment shift -- the finding is layout-dependent after all")
    assert _sm_with_group_at(v1, 0.0) < 0.0, (
        "v1.0 balances with all 63 kg at the nose -- rewrite the xfail reasons")


@pytest.mark.skipif(shutil.which(B.AVL_BIN) is None
                    and not __import__("pathlib").Path(B.AVL_BIN).exists(),
                    reason="vendor/bin/avl not present")
def test_finding_survives_the_avl_neutral_point(design):
    """The instability finding must not depend on which neutral-point method
    is used. AVL puts the NP 4.6-5.4% MAC further aft than the analytic
    relation -- the friendly direction -- and the CG is still behind it at
    every fuel state on both designs."""
    x_np = B.avl_neutral_point(design).x_np_m
    g = G.derive_wing(design.wing)
    worst = []
    for i in range(11):
        ff = 1.0 - i / 10.0
        sm = (x_np - B.cg_position(design, ff).x_cg_m) / g.mac_m
        worst.append((ff, sm))
    print(f"\n{design.variant}: on the AVL neutral point "
          f"({100 * B.percent_mac(design, x_np):.2f}% MAC), SM runs "
          f"{100 * worst[0][1]:+.1f}% MAC full to {100 * worst[-1][1]:+.1f}% "
          f"MAC dry")
    assert all(sm < 0.0 for _, sm in worst), (
        "on the AVL neutral point this design is stable somewhere in the burn "
        "-- the xfail reasons above must be rewritten")


def test_v1_dry_cg_excursion_against_the_published_band(v1):
    """ADDED IN ADVERSARIAL REVIEW, to make an unasserted prose claim checkable.

    research/configuration_hypotheses.md section 3: the dry CG "lands 0.47-0.67
    m aft of the 42% MAC target, which is 107-153% MAC". That band is an
    EXCURSION from the target, not a CG station -- a reading the xfail reason
    on test_v1_neutral_point_is_aft_of_the_cg originally got wrong, quoting
    this module's 135.1% MAC CG station as though it fell inside it.

    Measured here: 0.411 m / 93.1% MAC of excursion, which is 13% below the
    published band's lower edge. Same direction, same order, different number
    -- and the difference is worth knowing, because this module is the
    OPTIMISTIC one of the three build-ups.
    """
    g = G.derive_wing(v1.wing)
    excursion = B.cg_position(v1, 0.0).percent_mac - REPORT_CG_PCT_MAC
    print(f"\nv1.0 dry CG excursion from the 42% MAC target: "
          f"{excursion * g.mac_m:.3f} m = {100 * excursion:.1f}% MAC, against "
          f"a published 0.47-0.67 m = 107-153% MAC")
    assert excursion > 0.0
    assert excursion < 1.07, (
        "the dry CG excursion has reached the published 107-153% MAC band -- "
        "the xfail reason on test_v1_neutral_point_is_aft_of_the_cg says it "
        "sits below it and must be rewritten")
    assert excursion > 0.80, (
        "the dry CG excursion has fallen well below the published band; this "
        "module would then no longer be corroborating that finding at all")


def test_report_wing_station_required_to_balance(v1, v2):
    """The fix, quantified. Reported and cross-checked, not merely printed:
    research/empennage_trade.md open question 8 puts the required v1.0 wing
    root LE at x = 1.24-1.55 m, i.e. x_le_frac 0.365-0.456 on the 3.4 m pod.
    This module's bisection must land in that band.

    CORRECTED IN ADVERSARIAL REVIEW. This docstring used to present
    "empennage_trade 1.24-1.55 m" and "configuration_hypotheses 0.365-0.456"
    as two independent hand build-ups, and asserted both -- but 1.24/3.4 =
    0.3647 and 1.55/3.4 = 0.4559, so the two assertions were the SAME
    assertion, and configuration_hypotheses open question 6 explicitly
    attributes 0.365-0.456 to empennage_trade finding 8. It is ONE source.
    The same paragraph of configuration_hypotheses records a SECOND build-up
    at 0.446-0.527, which this module's 0.386 does NOT reach; that
    disagreement is reported below rather than quietly dropped. The published
    spread is itself 33% MAC, which is the real state of the evidence.
    """
    for d in (v1, v2):
        for target in (0.05, 0.10, 0.15):
            frac = B.solve_x_le_frac_for_static_margin(d, target, 1.0)
            print(f"{d.variant}: SM {100 * target:4.0f}% MAC at full fuel "
                  f"needs wing.x_le_frac {frac:.4f} "
                  f"(x_le {frac * d.fuselage.length_m:.3f} m), against the "
                  f"committed {d.wing.x_le_frac:.3f}")
    frac = B.solve_x_le_frac_for_static_margin(v1, 0.10, 1.0)
    assert 0.365 <= frac <= 0.456, (
        f"v1.0 needs x_le_frac {frac:.4f}; empennage_trade finding 8 says "
        f"0.365-0.456 (x_le 1.24-1.55 m)")
    print(f"v1.0 bisection {frac:.4f} is inside empennage_trade's 0.365-0.456 "
          f"and BELOW the second build-up's 0.446-0.527 quoted in "
          f"configuration_hypotheses open question 6 -- the two published "
          f"hand build-ups do not agree with each other either.")
    assert not (0.446 <= frac <= 0.527), (
        "this module now also lands in the second published build-up's band; "
        "the docstring above says it does not and must be rewritten")


# =========================================================================
# 7. Reporting -- always runs, always prints
# =========================================================================

# Every number quoted in an xfail reason above, in one place, as an assertion.
# {variant: (NP, CG full, CG dry, SM full, SM dry, SM excursion)}, all % MAC.
HEADLINE_PCT_MAC = {
    "v1.0": (52.95, 96.98, 135.13, -44.03, -82.18, -38.15),
    "v2.0": (53.20, 61.86, 76.73, -8.66, -23.52, -14.86),
}


def test_headline_numbers_quoted_in_the_xfail_reasons(design):
    """ADDED IN ADVERSARIAL REVIEW. The findings of this file are carried in
    xfail(strict) REASON TEXT, and an xfail only ever guards the SIGN of an
    inequality: any defect that leaves the aircraft unstable, however much it
    changes the numbers, leaves every xfail xfailing and every test passing.

    Proven by injection: moving the payload 200 mm aft
    (PAYLOAD_X_GIMBAL_OFFSET_M 0.30 -> 0.50) shifts the static margin by 9.1%
    MAC on v1.0 and 8.2% MAC on v2.0 -- more than v2.0's whole measured
    instability -- and passed all 76 tests of the original file, because the
    numbers it falsified live only in prose.

    Pinned to 0.1% MAC, the precision the reasons are quoted at. A failure
    here is not necessarily a defect; it means the reason texts are now stale
    and must be rewritten with the new numbers.
    """
    got = (B.neutral_point(design).percent_mac,
           B.cg_position(design, 1.0).percent_mac,
           B.cg_position(design, 0.0).percent_mac,
           B.static_margin(design, 1.0), B.static_margin(design, 0.0),
           B.cg_travel(design))
    names = ("neutral point", "CG full", "CG dry", "SM full", "SM dry",
             "SM excursion")
    want = HEADLINE_PCT_MAC[design.variant]
    bad = [(n, 100 * g, w) for n, g, w in zip(names, got, want)
           if abs(100 * g - w) > 0.1]
    assert not bad, (
        f"{design.variant}: the xfail reasons in this file quote numbers this "
        "module no longer produces -- "
        + "; ".join(f"{n} is {g:+.2f}% MAC, quoted as {w:+.2f}%"
                    for n, g, w in bad)
        + "\n" + B.cg_travel_table(design))


def test_report_cg_travel_table(v1, v2):
    """Not a pass/fail gate: the human-readable record. Run with -s."""
    for d in (v1, v2):
        print("\n" + B.cg_travel_table(d))
        print(B.mass_table(d))


# =========================================================================
# 8. The assumption register, and the verdict's sensitivity to it
# =========================================================================
# ADDED AFTER A MUTATION RUN ON THIS MODULE. Eight plausible defects were
# injected into argus7/analysis/balance.py one at a time; seven were killed by
# the tests above. The survivor was WING_GROUP_CG_FRAC_MAC 0.40 -> 0.25, i.e.
# putting the whole 32.5 kg wing group on the quarter-chord: nothing noticed.
# It is worth ~2% MAC of static margin, which does not change any verdict here
# -- but "does not change the verdict" is a thing to demonstrate, not to
# assume, which is what the two tests below do.

def test_assumption_register(design):
    """Every constant in balance.py that the design files do not carry, pinned
    to the value its comment documents. Changing one must be a deliberate,
    visible act with the comment rewritten to match -- not a silent edit."""
    assert B.WING_GROUP_CG_FRAC_MAC == 0.40      # Raymer wing-group CG
    assert B.TAIL_GROUP_CG_FRAC_MAC == 0.40
    assert B.X_AC_WING_FRAC_MAC == 0.25          # thin-airfoil wing AC
    assert B.GEOMETRIC_QUARTER_MAC == 0.25       # geometry.wing_ac_x's own 0.25
    assert B.ETA_TAIL == 1.0                     # boom tail out of the wake
    assert B.TANK_CHORD_CENTROID_FRAC == 0.40    # 15%/65% spar box, midpoint
    # CORRECTED IN ADVERSARIAL REVIEW from 0.940. design_space's span_frac is
    # a fraction of VOLUME held by the inner 80% of span, not a span extent;
    # 0.940 as an extent double-counted it. See balance.TANK_SPAN_FRAC.
    assert B.TANK_SPAN_FRAC == 0.800
    assert B.MISC_FRACTION_OF_NON_WING == pytest.approx(4.0 / 28.0)
    L = design.fuselage.length_m
    assert B.POWERTRAIN_X_FRAC_L * L == pytest.approx(3.05)   # empennage_trade
    assert B.RECOVERY_X_FRAC_L * L == pytest.approx(0.95)     # CAD chute hump
    assert B.AVIONICS_X_FRAC_L * L == pytest.approx(1.45)     # CAD antenna
    # ADDED IN ADVERSARIAL REVIEW. The payload is 50 kg -- 20% of MTOW -- and
    # balance.py calls it "the most FORWARD major mass on the aircraft and
    # therefore the one the balance leans on hardest". It was the ONE major
    # station left out of this register: moving it 200 mm aft
    # (PAYLOAD_X_GIMBAL_OFFSET_M 0.30 -> 0.50) is worth 9.1% MAC of static
    # margin on v1.0 and 8.2% MAC on v2.0 -- more than v2.0's entire measured
    # instability -- and passed the whole of this file untouched.
    assert B.PAYLOAD_X_GIMBAL_R_COEFF == 0.55                 # CAD chin gimbal
    assert B.PAYLOAD_X_GIMBAL_OFFSET_M == 0.30                # CAD chin gimbal
    _assert_every_item_is_placed_by_its_documented_constant(design)


def _assert_every_item_is_placed_by_its_documented_constant(design):
    """Pinning a constant's VALUE is not the same as checking the code uses
    it, and this file used to do only the former for eight of the nine items.

    ADVERSARIAL REVIEW, PROVEN BY INJECTION: deleting the
    TAIL_GROUP_CG_FRAC_MAC term from component_masses -- placing the whole
    tail group on the quarter-MAC instead of 40% of the tail chord -- passed
    all 76 tests, because the register asserted the constant's value and the
    sensitivity sweep below reported its (now identically zero) swing without
    asserting anything about it. Every station is now tied to its constant.
    """
    g = G.derive_wing(design.wing)
    L = design.fuselage.length_m
    R = design.fuselage.max_diameter_m / 2.0
    tp = G.derive_tail_panel(design)
    boom = G.derive_booms(design)
    x = dict((n, xi) for n, _, xi in B.component_masses(design))
    expect = {
        "wing": B.mac_le_x(design) + B.WING_GROUP_CG_FRAC_MAC * g.mac_m,
        "tail": (G.tail_qc_x(design)
                 + (B.TAIL_GROUP_CG_FRAC_MAC - 0.25) * tp.mac_m),
        "booms": 0.5 * (boom.x_fwd + boom.x_aft),
        "fuselage": B.fuselage_centroid_x(design),
        "powertrain": B.POWERTRAIN_X_FRAC_L * L,
        "avionics": B.AVIONICS_X_FRAC_L * L,
        "recovery": B.RECOVERY_X_FRAC_L * L,
        "payload": (B.PAYLOAD_X_GIMBAL_R_COEFF * R
                    + B.PAYLOAD_X_GIMBAL_OFFSET_M),
        "fuel": B.fuel_centroid_x(design),
    }
    assert set(expect) == set(x), f"item set changed: {sorted(x)}"
    for name, want in expect.items():
        assert x[name] == pytest.approx(want, abs=1e-12), (
            f"{name} is at x = {x[name]:.6f} m, not at the "
            f"{want:.6f} m its documented constant gives")


@pytest.mark.parametrize("const,lo,hi", [
    ("WING_GROUP_CG_FRAC_MAC", 0.30, 0.50),
    ("TAIL_GROUP_CG_FRAC_MAC", 0.25, 0.55),
    ("TANK_CHORD_CENTROID_FRAC", 0.30, 0.50),
    ("X_AC_WING_FRAC_MAC", 0.23, 0.27),
    ("ETA_TAIL", 0.85, 1.00),
])
def test_verdict_is_insensitive_to_each_chordwise_assumption(design, monkeypatch,
                                                             const, lo, hi):
    """Sweep each assumption across its credible range and confirm the answer
    -- CG aft of the neutral point at every fuel state -- does not flip.
    Prints the static-margin swing each one buys, so the reader can see which
    assumptions the number is actually sensitive to."""
    swing = []
    for v in (lo, hi):
        monkeypatch.setattr(B, const, v)
        swing.append(B.static_margin(design, 1.0))
        assert B.static_margin(design, 1.0) < 0.0, (
            f"{design.variant} becomes stable at {const} = {v} -- the finding "
            "is assumption-dependent and the xfail reasons must be rewritten")
        assert B.static_margin(design, 0.0) < 0.0
    print(f"\n{design.variant} {const} {lo}->{hi}: SM at full fuel "
          f"{100 * swing[0]:+.2f}% -> {100 * swing[1]:+.2f}% MAC "
          f"({100 * (swing[1] - swing[0]):+.2f}% MAC swing)")
