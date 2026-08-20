"""Tests for argus7.prop.engine -- shaft power available, BSFC map, alternator path.

Every geometry/propulsion number comes from design/argus7_v1.yaml via
argus7.design.schema.load_design.  Nothing here hardcodes a rating, a
reduction ratio or a fuel mass; where a test needs a *report* number to
check against (112.8 h, 270 g/kWh, 4.70 d) it is quoted with its section.
"""
from __future__ import annotations

import math
from pathlib import Path

import pytest

from argus7.design.schema import load_design
from argus7.prop import engine as eng
from argus7.prop.engine import Engine, EngineOverloadError

DESIGN_PATH = Path(__file__).resolve().parents[1] / "design" / "argus7_v1.yaml"

# Report numbers under test (docs/argus7_design_report.md).
REPORT_ENDURANCE_H = 112.8          # section 4 mission table, "Local ops"
REPORT_ENDURANCE_D = 4.70           # same row
REPORT_BSFC_FLAT = 270.0            # section 4 table caption, section 6 item 1
REPORT_BSFC_TARGET = 250.0          # section 6 item 1, "target <= 250"
REPORT_WALKAWAY_BSFC = 300.0        # section "kill conditions": walk away if
                                    # dyno BSFC > 300 g/kWh at the loiter point
REPORT_ALTERNATOR_ETA = 0.75        # section 4, "0.5 kW electrical via 0.75
                                    # alternator path"


@pytest.fixture(scope="module")
def design():
    return load_design(DESIGN_PATH)


@pytest.fixture(scope="module")
def e(design):
    return Engine.from_design(design)


# --------------------------------------------------------------------------
# 1. Sea-level power matches the rating
# --------------------------------------------------------------------------

def test_sea_level_power_at_rated_rpm_matches_the_rating(e, design):
    """At rated RPM, sea level, the deck must return exactly the YAML rating."""
    assert e.power_available_w(e.rated_rpm, 0.0) == pytest.approx(
        design.propulsion.power_max_kw * 1e3, rel=1e-12
    )


def test_rating_is_read_from_the_design_not_hardcoded(design):
    """Halve the rating in the design and the deck must halve with it."""
    half = design.model_copy(
        update={"propulsion": design.propulsion.model_copy(update={"power_max_kw": 8.5})},
        deep=True,
    )
    assert Engine.from_design(half).power_available_w(None, 0.0) == pytest.approx(8500.0)


def test_power_rises_monotonically_with_rpm_up_to_rated(e):
    xs = [0.2, 0.4, 0.6, 0.8, 1.0]
    p = [e.power_available_w(x * e.rated_rpm, 0.0) for x in xs]
    assert all(b > a for a, b in zip(p, p[1:]))


def test_power_falls_again_above_rated_rpm(e):
    """Rated RPM is the power peak; past it the cubic must turn over."""
    assert e.power_available_w(1.10 * e.rated_rpm, 0.0) < e.power_available_w(
        e.rated_rpm, 0.0
    )


def test_rpm_outside_the_fitted_band_raises(e):
    with pytest.raises(ValueError):
        e.power_available_w(0.05 * e.rated_rpm, 0.0)
    with pytest.raises(ValueError):
        e.power_available_w(1.5 * e.rated_rpm, 0.0)


# --------------------------------------------------------------------------
# 2. Altitude lapse -- Gagg-Farrar
# --------------------------------------------------------------------------

def test_isa_density_at_4000_m(design):
    assert eng.isa_density(design.mission.loiter_altitude_m) == pytest.approx(
        0.81913, abs=5e-5
    )
    assert eng.isa_density(0.0) == pytest.approx(eng.RHO_SL, rel=1e-9)


def test_power_at_4000_m_lapses_by_gagg_farrar(e, design):
    alt = design.mission.loiter_altitude_m
    sigma = eng.density_ratio(alt)
    ratio = e.power_available_w(e.rated_rpm, alt) / e.power_available_w(e.rated_rpm, 0.0)

    # Hand value: sigma = 0.66868 -> 1.13245*sigma - 0.13245 = 0.62479.
    assert sigma == pytest.approx(0.66868, abs=1e-4)
    assert ratio == pytest.approx(0.62479, abs=5e-4)

    # A naturally-aspirated engine loses MORE than the density ratio, because
    # friction does not lapse with density -- but not dramatically more.
    assert ratio < sigma
    assert ratio > sigma - 0.06


def test_lapse_is_unity_at_sea_level(e):
    assert eng.gagg_farrar_lapse(1.0) == pytest.approx(1.0, rel=1e-12)


def test_absolute_power_at_4000_m(e, design):
    """The lapsed rating in kW, so a regression shows up as a number."""
    alt = design.mission.loiter_altitude_m
    assert e.power_available_w(e.rated_rpm, alt) / 1e3 == pytest.approx(10.62, abs=0.02)


# --------------------------------------------------------------------------
# 3. BSFC map -- part-load penalty
# --------------------------------------------------------------------------

def test_bsfc_anchor_at_the_reference_load(e):
    """The map is calibrated so the report's 270 g/kWh is the 75%-load point."""
    p = eng.BSFC_REF_LOAD_FRACTION * e.rated_power_w
    assert e.bsfc_g_per_kwh(p, e.rated_rpm) == pytest.approx(REPORT_BSFC_FLAT, rel=1e-9)


def test_bsfc_at_20_percent_load_is_materially_worse_than_at_75_percent(e):
    b20 = e.bsfc_g_per_kwh(0.20 * e.rated_power_w, e.rated_rpm)
    b75 = e.bsfc_g_per_kwh(0.75 * e.rated_power_w, e.rated_rpm)
    assert b20 > b75
    # "materially": at least 25% worse. Measured value is ~53% worse
    # (414 vs 270 g/kWh) -- a constant-BSFC assumption is not survivable here.
    assert b20 / b75 > 1.25
    assert b20 == pytest.approx(413.7, abs=1.0)


def test_bsfc_falls_monotonically_as_load_rises(e):
    loads = [0.10, 0.20, 0.40, 0.60, 0.80, 1.00]
    b = [e.bsfc_g_per_kwh(f * e.rated_power_w, e.rated_rpm) for f in loads]
    assert all(y < x for x, y in zip(b, b[1:]))


def test_bsfc_penalty_knee_is_below_about_40_percent_load(e):
    """The curve must bend, not merely slope: the penalty per unit load lost
    below 40% must exceed that above it."""
    b40 = e.bsfc_g_per_kwh(0.40 * e.rated_power_w, e.rated_rpm)
    b20 = e.bsfc_g_per_kwh(0.20 * e.rated_power_w, e.rated_rpm)
    b60 = e.bsfc_g_per_kwh(0.60 * e.rated_power_w, e.rated_rpm)
    assert (b20 - b40) > 2.0 * (b40 - b60)


def test_zero_or_negative_shaft_power_has_no_defined_bsfc(e):
    with pytest.raises(ValueError):
        e.bsfc_g_per_kwh(0.0, e.rated_rpm)
    with pytest.raises(ValueError):
        e.bsfc_g_per_kwh(-100.0, e.rated_rpm)


def test_target_bsfc_is_better_than_the_assumed_bsfc():
    assert eng.BSFC_TARGET_G_PER_KWH == REPORT_BSFC_TARGET
    assert eng.BSFC_REPORT_FLAT_G_PER_KWH == REPORT_BSFC_FLAT
    assert eng.BSFC_TARGET_G_PER_KWH < eng.BSFC_REPORT_FLAT_G_PER_KWH


# --------------------------------------------------------------------------
# 4. Alternator / electrical path
# --------------------------------------------------------------------------

def test_electrical_load_adds_the_right_shaft_power(e, design):
    """500 W payload through a 0.75 alternator is 666.7 W of shaft, not 500 W."""
    expected = design.mission.payload_power_w / REPORT_ALTERNATOR_ETA
    assert e.electrical_shaft_power_w() == pytest.approx(expected, rel=1e-12)
    assert e.electrical_shaft_power_w() == pytest.approx(666.667, abs=1e-3)


def test_electrical_shaft_power_scales_with_the_demanded_watts(e):
    assert e.electrical_shaft_power_w(1000.0) == pytest.approx(1333.333, abs=1e-3)
    assert e.electrical_shaft_power_w(0.0) == 0.0


def test_electrical_draw_is_read_from_the_design(design):
    duty = design.model_copy(
        update={"mission": design.mission.model_copy(update={"payload_power_w": 350.0})},
        deep=True,
    )
    # section 4 mission table's duty-cycled row, 350 W average.
    assert Engine.from_design(duty).electrical_shaft_power_w() == pytest.approx(
        350.0 / REPORT_ALTERNATOR_ETA
    )


def test_total_shaft_demand_sums_propulsive_and_electrical(e):
    total = e.shaft_power_demand_w(propulsive_shaft_power_w=2666.0)
    assert total == pytest.approx(2666.0 + e.electrical_shaft_power_w())


# --------------------------------------------------------------------------
# 5. Fuel flow at the report's loiter condition vs its 4.7-day endurance
# --------------------------------------------------------------------------

def test_report_loiter_shaft_power_back_solves_from_the_report(design):
    """101.5 kg / 112.8 h at 270 g/kWh implies 3.333 kW of shaft -- which is
    the "shaft ~3.4 kW incl. 0.5 kW electrical" of section 4."""
    implied = design.masses.fuel / REPORT_ENDURANCE_H / (REPORT_BSFC_FLAT / 1e3)
    assert eng.REPORT_LOITER_SHAFT_POWER_W / 1e3 == pytest.approx(implied, rel=2e-3)
    assert eng.REPORT_LOITER_SHAFT_POWER_W / 1e3 == pytest.approx(3.4, abs=0.1)


def test_flat_bsfc_fuel_flow_reproduces_the_reports_4_7_days(e, design):
    """TOLERANCE: 1%. With the report's own flat 270 g/kWh the module must
    reproduce 112.8 h / 4.70 d almost exactly -- this pins down what the
    report actually computed before we argue with it."""
    mdot = e.fuel_flow_kg_h(
        eng.REPORT_LOITER_SHAFT_POWER_W,
        rpm=e.loiter_crank_rpm,
        altitude_m=design.mission.loiter_altitude_m,
        bsfc_g_per_kwh=REPORT_BSFC_FLAT,
    )
    hours = design.masses.fuel / mdot
    assert hours == pytest.approx(REPORT_ENDURANCE_H, rel=0.01)
    assert hours / 24.0 == pytest.approx(REPORT_ENDURANCE_D, rel=0.01)


def test_mapped_bsfc_shortens_the_endurance_but_stays_the_same_aircraft(e, design):
    """TOLERANCE: 25%. With the part-load map instead of a flat 270 the
    endurance must come DOWN (deep part load costs fuel) yet stay within 25%
    of the report's figure -- i.e. the report is optimistic, not wrong by an
    order of magnitude."""
    hours = e.endurance_h(
        fuel_mass_kg=design.masses.fuel,
        shaft_power_w=eng.REPORT_LOITER_SHAFT_POWER_W,
        rpm=e.loiter_crank_rpm,
        altitude_m=design.mission.loiter_altitude_m,
    )
    assert hours < REPORT_ENDURANCE_H
    assert hours == pytest.approx(REPORT_ENDURANCE_H, rel=0.25)
    assert hours == pytest.approx(94.8, abs=1.0)      # 3.95 d
    assert hours / 24.0 == pytest.approx(3.95, abs=0.05)


def test_loiter_is_deep_part_load(e, design):
    """~3.3 kW out of 17 kW is 20% of the sea-level rating -- the exact regime
    where a constant BSFC is least defensible."""
    frac = eng.REPORT_LOITER_SHAFT_POWER_W / e.rated_power_w
    assert frac == pytest.approx(0.196, abs=0.005)
    lf = e.load_fraction(
        eng.REPORT_LOITER_SHAFT_POWER_W,
        rpm=e.loiter_crank_rpm,
        altitude_m=design.mission.loiter_altitude_m,
    )
    # Against what the engine can actually make at that RPM and altitude the
    # loiter point is ~44% load, not 20%. Both framings must be available.
    assert 0.35 < lf < 0.55


def test_mapped_loiter_bsfc_lands_in_the_reports_walkaway_band(e):
    """Independent corroboration of the report's own risk register: it says
    'dyno mapping shows 300-320 g/kWh at the 3.5 kW loiter point (not 270)'
    and sets a walk-away at >300. The Willans part-load map lands at ~321."""
    b = e.bsfc_g_per_kwh(eng.REPORT_LOITER_SHAFT_POWER_W, e.loiter_crank_rpm)
    assert b == pytest.approx(321.3, abs=2.0)
    assert b > REPORT_WALKAWAY_BSFC


def test_fuel_flow_units_are_self_consistent(e):
    p_w, rpm = 4000.0, e.loiter_crank_rpm
    b = e.bsfc_g_per_kwh(p_w, rpm)
    kg_h = e.fuel_flow_kg_h(p_w, rpm, 0.0)
    kg_s = e.fuel_flow_kg_s(p_w, rpm, 0.0)
    assert kg_h == pytest.approx(b * (p_w / 1e3) / 1e3)
    assert kg_s == pytest.approx(kg_h / 3600.0)


# --------------------------------------------------------------------------
# 6. Non-closures the module must expose rather than paper over
# --------------------------------------------------------------------------

def test_demanding_more_than_is_available_raises(e, design):
    alt = design.mission.loiter_altitude_m
    avail = e.power_available_w(e.loiter_crank_rpm, alt)
    with pytest.raises(EngineOverloadError):
        e.fuel_flow_kg_h(avail * 1.05, e.loiter_crank_rpm, alt)


def test_the_design_prop_rpm_cannot_reach_the_17_kw_rating(e, design):
    """2100 prop RPM x 2.3 = 4830 crank = 64% of the power-peak RPM, where the
    engine makes ~12.1 kW at sea level, not 17. The 17 kW headline is only
    available by over-speeding the prop past its design point -- the same
    gearing non-closure the BEMT side reports from the C_P direction."""
    assert e.loiter_crank_rpm == pytest.approx(
        design.propulsion.prop_rpm * design.propulsion.reduction_ratio
    )
    assert e.loiter_crank_rpm == pytest.approx(4830.0)
    sl = e.power_available_w(e.loiter_crank_rpm, 0.0)
    assert sl / 1e3 == pytest.approx(12.07, abs=0.05)
    assert sl < design.propulsion.power_max_kw * 1e3


def test_climb_power_at_the_design_prop_rpm_does_not_close(e):
    """Report section 6 needs 12.2 kW for the 3 m/s climb at MTOW. At the
    design gearing, sea level, the engine offers 12.07 kW BEFORE the 0.67 kW
    alternator load -- so the climb case does not close."""
    needed_shaft = 12.2e3 + e.electrical_shaft_power_w()
    assert e.power_available_w(e.loiter_crank_rpm, 0.0) < needed_shaft
