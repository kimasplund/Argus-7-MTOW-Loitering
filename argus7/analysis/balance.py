"""Longitudinal balance: CG, neutral point, static margin and fuel-burn CG travel.

WHY THIS MODULE EXISTS
----------------------
Until it was written, nothing in argus7/ computed a CG, a neutral point or a
static margin -- while docs/argus7_design_report.md section 2 published
"+14.7% MAC at CG 42%" and research/design_pack.md published "neutral point
55% MAC, static margin 10%" and "fuel tanks centered at 45% MAC -> CG travel
<0.5% MAC full->empty". Two research packs
(research/configuration_hypotheses.md section 3, research/empennage_trade.md
open question 8) had already recorded, from hand build-ups, that the aircraft
"does not balance" at the committed wing station. None of it was in code, so
none of it could be regression-tested, and v2.0 then grew the wing 40% without
anything checking.

WHAT IS DERIVED AND WHAT IS ASSUMED
-----------------------------------
Every *station* below is derived from argus7.design.geometry
(wing_ac_x, tail_qc_x, derive_booms, derive_tail_panel) or from the fuselage
loft in design/*.yaml. What cannot be derived is the equipment layout -- the
repository has never had one (research/configuration_hypotheses.md open
question 6: "Not resolvable by analysis -- it needs an equipment layout").
Each such assumption is a named module constant with its source in the
comment beside it, so that the sensitivity of the answer to the assumption can
be read off rather than guessed at.

THE CONVENTION, stated once
---------------------------
x is aft, nose at x = 0, SI, and "% MAC" ALWAYS means the fraction
(x - x_mac_le) / MAC, measured from the leading edge of the mean aerodynamic
chord -- not from the nose and not from the wing root LE. On v1.0 the MAC LE
is at x = 0.78331 m, so confusing the two datums is worth 178% MAC.

Static margin is SM = (Xnp - Xcg) / MAC: POSITIVE when the CG is forward of
the neutral point, which is the stable direction.
"""
from __future__ import annotations

import math
from functools import lru_cache
from typing import NamedTuple

import numpy as np

from argus7.aero.buildup import airfoil_perimeter_ratio, fuselage_wetted_area
from argus7.design.geometry import (derive_booms, derive_tail_panel,
                                    derive_wing, tail_qc_x, tail_volume_h,
                                    wing_ac_x, wing_le_x)

# =========================================================================
# Assumptions. Every one of these is a placement the design files do not
# carry. Sourced where a source exists; flagged where none does.
# =========================================================================

# --- structural group CGs, chordwise ---
# Wing group CG at 40% MAC. Standard preliminary-design value for a cantilever
# wing whose spar caps sit at the max-thickness line and whose skins, ribs,
# tanks and flaperons spread aft of it (Raymer, "Aircraft Design", ch. 15
# component-CG table: 40% MAC for a wing group). NOT derivable from the YAML,
# which carries no spar positions.
WING_GROUP_CG_FRAC_MAC = 0.40
# Tail panel group CG at 40% of the tail MAC, same argument, applied to the
# panel's own chord. derive_tail_panel puts the panel quarter-MAC on
# tail_qc_x, so this is tail_qc_x + 0.15 * tail MAC.
TAIL_GROUP_CG_FRAC_MAC = 0.40

# --- equipment stations, as fractions of fuselage length ---
# NONE of these is in design/*.yaml: argus7.cad.model.build_installed_items
# says in terms, "these are illustrative CAD placements, not design-contract
# geometry -- there is no YAML field for gimbal/chute/antenna position".
# The values below are read off that CAD placement (which is what the figures
# in the report show) and off the one published hand build-up, and expressed
# as fractions of fuselage length so they at least track a changed fuselage.
#
# Powertrain: pusher installation on the aft bulkhead. 3.05 m at L = 3.4 m is
# the station research/empennage_trade.md open question 8 uses ("25 kg of
# pusher powertrain at x ~ 3.05 m"); the CAD's prop disc is at L + 0.06 m, so
# this puts the powertrain CG 0.41 m ahead of the disc, which is about right
# for engine + belt reduction + mounts.
POWERTRAIN_X_FRAC_L = 3.05 / 3.4
# Recovery: parachute bay. build_installed_items puts the chute hump at
# x = 0.95 m on the L = 3.4 m pod.
RECOVERY_X_FRAC_L = 0.95 / 3.4
# Avionics: the only avionics-adjacent placement in the repository is the
# comms blade antenna at x = 1.45 m in build_installed_items. WEAKEST
# assumption in this module; see SENSITIVITY below.
AVIONICS_X_FRAC_L = 1.45 / 3.4
# Payload: 50 kg of "comms + EO/IR + backhaul" (report section 3), lumped at
# the chin gimbal, whose CAD station is 0.55 * R + 0.30 with R the max
# fuselage radius. Kept as that expression rather than a number so it tracks
# the fuselage diameter. This is the most FORWARD major mass on the aircraft
# and therefore the one the balance leans on hardest.
PAYLOAD_X_GIMBAL_R_COEFF = 0.55
PAYLOAD_X_GIMBAL_OFFSET_M = 0.30

# --- mass-budget split ---
# report section 3 splits "Airframe structure 60.5" as "wing 32.5 (UD-carbon
# spar caps + Rohacell web), fuselage/booms/tails 24, misc 4". The wing part is
# recomputed per design point from argus7.opt.design_space (the AR^1.5 spar
# model, calibrated to that same 32.5 kg), so 4/28 of whatever is left over is
# "misc" and 24/28 is primary structure.
MISC_FRACTION_OF_NON_WING = 4.0 / 28.0
# Non-wing primary structure is split between fuselage, booms and tail in
# proportion to WETTED AREA -- i.e. a constant areal mass. Crude for the booms
# (a slender tube is heavier per unit area than a monocoque pod), but it is
# derived from the committed geometry rather than invented, and the booms carry
# only ~7 kg, so a 30% error there is ~2 kg on a 250 kg aircraft.
# "misc" is carried at the fuselage centroid.

# --- fuel tank ---
# The tank is the wing box. Front spar 15% chord, rear spar 65% chord (the
# layout argus7.opt.design_space.wing_fuel_capacity_kg's chord_frac = 0.716
# section-area fraction is measured over), so the tank's chordwise centroid is
# taken at the MIDPOINT of the box, 40% of the local chord. (Strictly the area
# centroid of an FX 63-137 box sits a little forward of the midpoint, because
# the section is thickest near 30% chord; the 0.30-0.50 sweep in
# test_verdict_is_insensitive_to_each_chordwise_assumption covers it.)
TANK_CHORD_CENTROID_FRAC = 0.40
# Spanwise extent of the tank, as a fraction of semi-span. The local volume
# goes as chord^2, which is what fuel_centroid_x integrates.
#
# ADVERSARIAL REVIEW, CORRECTED FROM 0.940. That value was taken from
# wing_fuel_capacity_kg's `span_frac = 0.940` and described in this comment as
# "the tank runs to 94% semi-span". It does not: that function's own docstring
# says span_frac is a fraction of VOLUME, not of span -- "the inner 80% of a
# taper-0.30 span holds 94.0% of wing volume, because volume goes as chord^2
# and weights inboard heavily". Reproduced here by direct integration: the
# inner 80% of semi-span holds 90.7% of volume at v1.0's taper 0.45 and 93.8%
# at v2.0's taper 0.3102. The tank EXTENT that capacity model corresponds to
# is therefore 0.80, and 0.940 as an extent double-counted the same allowance.
# Worth 0.17% MAC (v1.0) and 0.22% MAC (v2.0) of static margin -- it changes
# no verdict, and it was pinned at the wrong value by the assumption register.
TANK_SPAN_FRAC = 0.800

# --- aerodynamics ---
# Tail dynamic-pressure ratio. The inverted-V sits on booms outboard of the
# fuselage wake and ahead of the pusher disc, so it sees close to free-stream
# q. Named rather than silently omitted, and 1.0 leaves the spec's formula
# exactly as written.
ETA_TAIL = 1.0
# Wing aerodynamic centre at the quarter-MAC. Thin-airfoil theory.
#
# ADVERSARIAL REVIEW, MEASURED: the repository's own AVL does NOT agree with
# it. Running the deck of write_avl_deck with the tail SURFACE deleted puts
# the isolated wing's AC at 30.19% MAC (v1.0) and 30.45% MAC (v2.0) -- 5.2 and
# 5.5% MAC AFT of the quarter-chord, on a planform with 1 deg of LE sweep,
# taper and twist. That difference, not any tail effect, is the whole of the
# gap between neutral_point() and avl_neutral_point() (see
# tests/test_balance.py::test_avl_decomposition_locates_the_gap_in_the_wing_term,
# which measures the two terms separately: the analytic TAIL term matches AVL
# to within 0.8% MAC on both designs).
#
# 0.25 is kept because it is the relation the specification and the published
# 55% MAC figure are both written in, and because it is the CONSERVATIVE end:
# the true AC being further aft moves the neutral point AFT, i.e. every static
# margin here is understated by ~5% MAC. That does not change any verdict --
# the AVL neutral point is asserted separately in
# test_finding_survives_the_avl_neutral_point -- but it is a real 5% MAC of
# method bias and it is in the FAVOURABLE direction, so it must be stated.
X_AC_WING_FRAC_MAC = 0.25
# The GEOMETRIC quarter-MAC. Not an assumption and not the same quantity as
# X_AC_WING_FRAC_MAC: argus7.design.geometry.wing_ac_x is constructed as
# "root LE + sweep offset to the MAC station + 0.25 * MAC", so recovering the
# MAC LEADING EDGE from it means subtracting exactly that 0.25 whatever one
# believes about where the aerodynamic centre is.
#
# ADVERSARIAL REVIEW: these two were the same symbol. Because mac_le_x
# subtracted X_AC_WING_FRAC_MAC and neutral_point added it straight back,
# x_np came out ALGEBRAICALLY INDEPENDENT of it -- sweeping the wing-AC
# assumption 0.23...0.27 in
# test_verdict_is_insensitive_to_each_chordwise_assumption moved the neutral
# point by exactly zero and reported a 0.26% MAC sensitivity for an
# assumption whose true worth is 4% MAC, understating it 8x. Separating them
# changes nothing at the committed 0.25/0.25 and makes that sweep honest.
GEOMETRIC_QUARTER_MAC = 0.25


class MassItem(NamedTuple):
    """(name, mass_kg, x_cg_m) -- a plain 3-tuple that also has names."""
    name: str
    mass_kg: float
    x_cg_m: float


class CGResult(NamedTuple):
    x_cg_m: float
    percent_mac: float


class AVLNeutralPoint(NamedTuple):
    x_np_m: float
    percent_mac: float


class NeutralPointResult(NamedTuple):
    x_np_m: float
    percent_mac: float
    tail_contribution_mac: float
    a_wing: float
    a_tail: float
    downwash_gradient: float
    volume_coefficient: float


# =========================================================================
# Geometry helpers
# =========================================================================

def mac_le_x(design) -> float:
    """Fuselage station of the leading edge of the mean aerodynamic chord."""
    g = derive_wing(design.wing)
    return wing_ac_x(design) - GEOMETRIC_QUARTER_MAC * g.mac_m


def percent_mac(design, x_m: float) -> float:
    """Convert a fuselage station to a fraction of MAC aft of the MAC LE."""
    g = derive_wing(design.wing)
    return (x_m - mac_le_x(design)) / g.mac_m


def _loft_stations(design):
    L = design.fuselage.length_m
    R = design.fuselage.max_diameter_m / 2.0
    return [(x * L, r * R) for x, r in design.fuselage.stations]


def fuselage_volume_m3(design) -> float:
    """Enclosed volume of the station loft, as an exact sum of truncated-cone
    volumes pi/3 * (r1^2 + r1 r2 + r2^2) * dx. Linear between stations, the
    same reading argus7.aero.buildup.fuselage_wetted_area takes.

    Cross-check: research/configuration_hypotheses.md section 3.3(a) quotes
    "the lofted 0.4105 m3" for the v1.0 pod.
    """
    st = _loft_stations(design)
    return sum(math.pi / 3.0 * (r1 * r1 + r1 * r2 + r2 * r2) * (x2 - x1)
               for (x1, r1), (x2, r2) in zip(st[:-1], st[1:]))


def fuselage_centroid_x(design) -> float:
    """Wetted-area-weighted centroid of the loft.

    Area-weighted, not volume-weighted: the pod is a shell, so its structural
    mass follows surface area. Each frustum's lateral-area centroid is
    x1 + dx (r1 + 2 r2) / (3 (r1 + r2)); the blunt nose disc is included at
    x = 0, as fuselage_wetted_area includes it.
    """
    st = _loft_stations(design)
    num = 0.0
    den = math.pi * st[0][1] ** 2                      # nose cap at x = 0
    for (x1, r1), (x2, r2) in zip(st[:-1], st[1:]):
        a = math.pi * (r1 + r2) * math.hypot(x2 - x1, r2 - r1)
        xc = x1 + (x2 - x1) * (r1 + 2.0 * r2) / (3.0 * (r1 + r2))
        num += a * xc
        den += a
    return num / den


def boom_wetted_area_m2(design) -> float:
    b = derive_booms(design)
    return 2.0 * math.pi * design.booms.diameter_m * b.length_m


def tail_wetted_area_m2(design) -> float:
    """Both panels, both surfaces -- the same expression
    argus7.aero.buildup.tail_component uses."""
    tp = derive_tail_panel(design)
    return airfoil_perimeter_ratio(design.tail.airfoil) * 2.0 * tp.panel_area_m2


def fuel_centroid_x(design) -> float:
    """Fuselage station of the centroid of the wing-tank fuel.

    Integrated over the span: local tank volume goes as chord^2 (fixed t/c,
    fixed chord fraction), and the local tank centroid sits at
    TANK_CHORD_CENTROID_FRAC of the local chord aft of the local LE, which
    itself moves aft with sweep. Trapezoidal on 2001 stations -- the
    integrand is a cubic polynomial in y, so this is exact to ~1e-9 m.

    This is the number the report's "wing tanks at the AC" claim is about:
    compare it against argus7.design.geometry.wing_ac_x.

    ASSUMPTION, ADDED IN ADVERSARIAL REVIEW: ALL of design.masses.fuel is
    placed here, i.e. every kilogram is assumed to be in the wing box. That is
    true of v2.0 (wing capacity 138.54 kg against 100.97 kg carried) but it is
    NOT true of v1.0, where argus7.opt.design_space.wing_fuel_capacity_kg
    returns 66.02 kg against the 101.50 kg the design file carries. 35.48 kg of
    v1.0's fuel -- 14% of its MTOW -- has nowhere to be, and this module puts
    it in the wing anyway. It is the repository's standing "wing fuel volume"
    escalation (README known gaps, design/argus7_v1.yaml masses.fuel
    provenance), not a new finding, but it means v1.0's fuel STATION is
    fictional: a fuselage tank would sit further aft than 41% MAC and make the
    v1.0 numbers worse, never better. Recorded by
    tests/test_balance.py::test_all_fuel_is_placed_in_a_wing_that_cannot_hold_it.
    """
    g = derive_wing(design.wing)
    semi = g.span_m / 2.0
    y = np.linspace(0.0, TANK_SPAN_FRAC * semi, 2001)
    c = g.chord_root_m + (g.chord_tip_m - g.chord_root_m) * (y / semi)
    x_le = wing_le_x(design) + y * math.tan(math.radians(design.wing.sweep_le_deg))
    x = x_le + TANK_CHORD_CENTROID_FRAC * c
    w = c ** 2
    return float(np.trapezoid(x * w, y) / np.trapezoid(w, y))


# =========================================================================
# Mass build-up
# =========================================================================

@lru_cache(maxsize=1)
def _k_cal() -> float:
    from argus7.opt.design_space import calibrate
    return calibrate()


def wing_group_mass_kg(design) -> float:
    """Wing structural mass from the AR^1.5 spar model in
    argus7.opt.design_space -- the same model the optimiser that produced
    v2.0 was scored on, so the two design points are weighed on one scale.
    Calibrated once to the report's published 32.5 kg at the v1.0 point."""
    import torch

    from argus7.opt.design_space import wing_mass_kg
    t = lambda v: torch.tensor(float(v), dtype=torch.float64)
    return float(wing_mass_kg(t(design.wing.area_m2), t(design.wing.aspect_ratio),
                              t(design.wing.taper_ratio), t(design.masses.mtow),
                              t(design.wing.thickness_ratio), t(_k_cal())))


def component_masses(design) -> list[MassItem]:
    """The full mass build-up: (name, mass_kg, x_cg_m) per group.

    Closes exactly on design.masses.mtow by construction -- the airframe line
    is split, never topped up, and the remaining lines are taken verbatim from
    the design file.
    """
    g = derive_wing(design.wing)
    L = design.fuselage.length_m
    R = design.fuselage.max_diameter_m / 2.0
    boom = derive_booms(design)
    tp = derive_tail_panel(design)

    m_wing = wing_group_mass_kg(design)
    m_non_wing = design.masses.airframe - m_wing
    if m_non_wing <= 0.0:
        raise ValueError(
            f"{design.variant}: the spar model puts the wing at {m_wing:.2f} kg "
            f"against a stated airframe total of {design.masses.airframe:.2f} kg "
            f"-- nothing left for fuselage, booms and tail")
    m_misc = MISC_FRACTION_OF_NON_WING * m_non_wing
    m_struct = m_non_wing - m_misc

    s_fus, s_boom, s_tail = (fuselage_wetted_area(design),
                             boom_wetted_area_m2(design),
                             tail_wetted_area_m2(design))
    s_tot = s_fus + s_boom + s_tail

    x_fus = fuselage_centroid_x(design)
    items = [
        MassItem("wing", m_wing,
                 mac_le_x(design) + WING_GROUP_CG_FRAC_MAC * g.mac_m),
        # misc rides with the fuselage
        MassItem("fuselage", m_struct * s_fus / s_tot + m_misc, x_fus),
        MassItem("booms", m_struct * s_boom / s_tot,
                 0.5 * (boom.x_fwd + boom.x_aft)),
        MassItem("tail", m_struct * s_tail / s_tot,
                 tail_qc_x(design)
                 + (TAIL_GROUP_CG_FRAC_MAC - 0.25) * tp.mac_m),
        MassItem("powertrain", design.masses.powertrain, POWERTRAIN_X_FRAC_L * L),
        MassItem("avionics", design.masses.avionics, AVIONICS_X_FRAC_L * L),
        MassItem("recovery", design.masses.recovery, RECOVERY_X_FRAC_L * L),
        MassItem("payload", design.masses.payload,
                 PAYLOAD_X_GIMBAL_R_COEFF * R + PAYLOAD_X_GIMBAL_OFFSET_M),
        MassItem("fuel", design.masses.fuel, fuel_centroid_x(design)),
    ]
    return items


# =========================================================================
# CG, neutral point, static margin
# =========================================================================

def cg_position(design, fuel_fraction: float = 1.0) -> CGResult:
    """CG at a given fuel state. fuel_fraction 1.0 = full, 0.0 = dry.

    Returns (x_cg_m, percent_mac) -- a plain 2-tuple that also has names.
    """
    if not 0.0 <= fuel_fraction <= 1.0:
        raise ValueError(f"fuel_fraction {fuel_fraction} outside [0, 1]")
    m_tot = 0.0
    moment = 0.0
    for name, mass, x in component_masses(design):
        m = mass * fuel_fraction if name == "fuel" else mass
        m_tot += m
        moment += m * x
    x_cg = moment / m_tot
    return CGResult(x_cg, percent_mac(design, x_cg))


def lift_curve_slope_per_rad(aspect_ratio: float, sweep_le_deg: float = 0.0,
                             taper_ratio: float = 1.0) -> float:
    """Helmbold / DATCOM low-speed finite-wing slope,

        a = 2 pi AR / (2 + sqrt(AR^2 (1 + tan^2 Lambda_c/2) + 4))

    with the half-chord sweep obtained from the leading-edge sweep by the
    standard tan Lambda_n = tan Lambda_le - (4n/AR)(1-lambda)/(1+lambda).
    Compressibility is ignored: loiter Mach here is ~0.1 and beta^2 = 0.99.
    """
    tan_le = math.tan(math.radians(sweep_le_deg))
    tan_half = tan_le - (2.0 / aspect_ratio) * (1.0 - taper_ratio) / (1.0 + taper_ratio)
    return (2.0 * math.pi * aspect_ratio
            / (2.0 + math.sqrt(aspect_ratio ** 2 * (1.0 + tan_half ** 2) + 4.0)))


def downwash_gradient(design) -> float:
    """de/da = 2 a_w / (pi AR).

    The far-field lifting-line result: a wing of lift-curve slope a_w leaves a
    downwash at the tail plane of twice its own induced angle. It is the
    estimate Perkins & Hage and Raymer both give for a tail well aft of a
    high-AR wing, and on AR 22-24 it returns 0.16-0.17 -- small, as it should
    be on a sailplane-like wing, against 0.3-0.4 for an AR-6 wing. It is an
    ESTIMATE: it takes no account of tail height above the wake, which on a
    boom-mounted tail at z ~ 0 is the assumption that the tail sits IN the
    wake plane, i.e. the conservative (largest de/da, smallest stabilising
    contribution) reading.
    """
    a_w = lift_curve_slope_per_rad(design.wing.aspect_ratio,
                                   design.wing.sweep_le_deg,
                                   design.wing.taper_ratio)
    return 2.0 * a_w / (math.pi * design.wing.aspect_ratio)


def fuselage_np_shift_mac(design) -> float:
    """Munk's apparent-mass fuselage term, as a (negative) fraction of MAC.

        dCm/dCL|fus = 2 * Vol / (S * MAC * a_w)   ->   NP moves FORWARD

    A slender body in a flow generates a destabilising free moment
    proportional to its enclosed volume; it does not depend on the body's
    lift, which is why the volume and not the planform appears.

    Cross-check: research/configuration_hypotheses.md section 3.3(a) computes
    the same shift for the v1.0 pod on its lofted 0.4105 m3 as "8.2% by Munk"
    (and 7.3% by the more elaborate Multhopp strip method, which is not
    implemented here -- so this term is the pessimistic end of the published
    7-9% band).

    NOT included in neutral_point() by default: the specification's relation,
    and the report's own 55% MAC figure, are wing-plus-tail only. Call this
    explicitly, or pass include_fuselage=True, to see what the pod costs.
    """
    g = derive_wing(design.wing)
    a_w = lift_curve_slope_per_rad(design.wing.aspect_ratio,
                                   design.wing.sweep_le_deg,
                                   design.wing.taper_ratio)
    return -2.0 * fuselage_volume_m3(design) / (g.area_m2 * g.mac_m * a_w)


def neutral_point(design, include_fuselage: bool = False) -> NeutralPointResult:
    """Stick-fixed neutral point.

        Xnp/MAC = Xac_wing/MAC + Vh * (a_t/a_w) * (1 - de/da) * eta_t

    Vh comes from argus7.design.geometry.tail_volume_h, so the tail arm and
    the effective tail area are exactly the ones the rest of the repository
    uses -- and note (see argus7.aero.buildup.tail_component) that
    tail.area_h_m2 is the EFFECTIVE horizontal area of the inverted V, i.e.
    it already carries the cos^2(dihedral) factor, which is precisely the
    convention a tail volume coefficient is written in. The panel's own
    aspect ratio drives a_t.

    THAT READING IS LOAD-BEARING AND THE REPOSITORY CONTRADICTS ITSELF ON IT.
    argus7.design.geometry.derive_tail_panel's docstring calls area_h_m2 the
    "PROJECTED horizontal area" while its code divides by 2 cos^2(gamma),
    which is the EFFECTIVE convention (a projected area would divide by
    2 cos(gamma)). Taking it as projected instead would shrink the tail term
    by cos(42 deg) = 26% and move the neutral point from 52.95% to 45.8% MAC
    on v1.0 -- i.e. it would make the finding here WORSE. The effective
    reading is the one adopted, and it is not adopted on the strength of a
    docstring: tests/test_balance.py::
    test_avl_decomposition_locates_the_gap_in_the_wing_term measures the tail
    term against AVL, which is fed the ACTUAL dihedral geometry, and gets
    28.11% MAC against this relation's 27.95% on v1.0.

    include_fuselage=True adds the Munk pod term (see fuselage_np_shift_mac).
    """
    g = derive_wing(design.wing)
    a_w = lift_curve_slope_per_rad(design.wing.aspect_ratio,
                                   design.wing.sweep_le_deg,
                                   design.wing.taper_ratio)
    a_t = lift_curve_slope_per_rad(design.tail.panel_aspect_ratio, 0.0,
                                   design.tail.taper_ratio)
    de_da = downwash_gradient(design)
    vh = tail_volume_h(design)
    tail_term = vh * (a_t / a_w) * (1.0 - de_da) * ETA_TAIL
    pct = X_AC_WING_FRAC_MAC + tail_term
    if include_fuselage:
        pct += fuselage_np_shift_mac(design)
    return NeutralPointResult(
        x_np_m=mac_le_x(design) + pct * g.mac_m,
        percent_mac=pct, tail_contribution_mac=tail_term,
        a_wing=a_w, a_tail=a_t, downwash_gradient=de_da,
        volume_coefficient=vh)


def static_margin(design, fuel_fraction: float = 1.0,
                  include_fuselage: bool = False) -> float:
    """(Xnp - Xcg) / MAC, as a FRACTION of MAC. Positive = stable."""
    g = derive_wing(design.wing)
    np_ = neutral_point(design, include_fuselage=include_fuselage)
    cg = cg_position(design, fuel_fraction)
    return (np_.x_np_m - cg.x_cg_m) / g.mac_m


def cg_travel(design, include_fuselage: bool = False) -> float:
    """Total static-margin excursion from full to empty fuel, as a fraction of
    MAC. Signed: positive means the aircraft gets MORE stable as it burns
    (CG moving forward), negative means less.

    The neutral point does not move with fuel state, so this is exactly the
    CG travel divided by the MAC, with the sign flipped.
    """
    return (static_margin(design, 0.0, include_fuselage)
            - static_margin(design, 1.0, include_fuselage))


def solve_x_le_frac_for_static_margin(design, target_sm: float,
                                      fuel_fraction: float = 1.0,
                                      lo: float = 0.02, hi: float = 0.98,
                                      tol: float = 1e-10) -> float:
    """The wing station (wing.x_le_frac) that would give `target_sm`.

    Moving the wing aft moves the neutral point aft 1:1 while moving only the
    wing group and the wing fuel with it, so the static margin rises
    monotonically with x_le_frac and a bisection is safe. The tail rides with
    the wing (tail_qc_x = wing_ac_x + arm), so Vh -- and therefore the tail
    term in the neutral point -- is invariant under the translation, and so is
    boom length.

    Returns NaN if no station in [lo, hi] achieves the target.
    """
    def sm(frac: float) -> float:
        d = design.model_copy(deep=True)
        d.wing.x_le_frac = frac
        return static_margin(d, fuel_fraction)

    f_lo, f_hi = sm(lo) - target_sm, sm(hi) - target_sm
    if f_lo * f_hi > 0.0:
        return float("nan")
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        f_mid = sm(mid) - target_sm
        if f_lo * f_mid <= 0.0:
            hi, f_hi = mid, f_mid
        else:
            lo, f_lo = mid, f_mid
        if hi - lo < tol:
            break
    return 0.5 * (lo + hi)


# =========================================================================
# Reporting
# =========================================================================

def mass_table(design) -> str:
    g = derive_wing(design.wing)
    items = component_masses(design)
    rows = [f"MASS BUILD-UP  {design.name} {design.variant}",
            f"  MAC {g.mac_m:.4f} m, MAC LE x = {mac_le_x(design):.4f} m, "
            f"wing AC x = {wing_ac_x(design):.4f} m",
            "  item          mass kg      x m     %MAC     moment kg.m",
            "  " + "-" * 55]
    for name, mass, x in items:
        rows.append(f"  {name:<12}{mass:8.2f}{x:9.4f}{100 * percent_mac(design, x):9.1f}"
                    f"{mass * x:13.2f}")
    tot = sum(m for _, m, _ in items)
    mom = sum(m * x for _, m, x in items)
    rows.append("  " + "-" * 55)
    rows.append(f"  {'TOTAL':<12}{tot:8.2f}{mom / tot:9.4f}"
                f"{100 * percent_mac(design, mom / tot):9.1f}{mom:13.2f}")
    rows.append(f"  (design file MTOW {design.masses.mtow:.2f} kg; "
                f"UNALLOCATED RESIDUAL {mass_budget_residual_kg(design):+.2f} kg)")
    return "\n".join(rows)


def cg_travel_table(design, n: int = 11) -> str:
    g = derive_wing(design.wing)
    np_ = neutral_point(design)
    np_f = neutral_point(design, include_fuselage=True)
    x_fuel = fuel_centroid_x(design)
    # ADVERSARIAL REVIEW: this column used to print
    # design.masses.mtow - (1 - ff) * fuel, i.e. the design file's STATED
    # gross mass, while every CG beside it was computed from the build-up.
    # On v2.0 those differ by the 13.02 kg of mass_budget_residual_kg, so the
    # table asserted a 248.36 kg aircraft balancing at a 235.34 kg aircraft's
    # CG. Print what the CG was actually computed from.
    m_built = sum(m for _, m, _ in component_masses(design))
    resid = mass_budget_residual_kg(design)
    rows = [
        f"CG TRAVEL  {design.name} {design.variant}",
        f"  MAC {g.mac_m:.4f} m at x_le {mac_le_x(design):.4f} m; "
        f"build-up {m_built:.2f} kg vs stated MTOW {design.masses.mtow:.2f} kg "
        f"(residual {resid:+.2f} kg), fuel {design.masses.fuel:.2f} kg "
        f"({100 * design.masses.fuel / m_built:.1f}% of the build-up)",
        f"  Vh {np_.volume_coefficient:.4f}, a_w {np_.a_wing:.3f}/rad, "
        f"a_t {np_.a_tail:.3f}/rad, de/da {np_.downwash_gradient:.4f}",
        f"  NP (wing+tail) {100 * np_.percent_mac:.2f}% MAC "
        f"(x = {np_.x_np_m:.4f} m); with Munk pod term "
        f"{100 * np_f.percent_mac:.2f}% MAC",
        f"  fuel centroid x = {x_fuel:.4f} m = {100 * percent_mac(design, x_fuel):.2f}% MAC; "
        f"wing AC = {100 * X_AC_WING_FRAC_MAC:.0f}% MAC "
        f"(offset {1000 * (x_fuel - wing_ac_x(design)):+.0f} mm)",
        "  fuel     mass      x_cg      CG        SM       SM (+pod)",
        "  frac       kg         m     %MAC      %MAC          %MAC",
        "  " + "-" * 58,
    ]
    for i in range(n):
        ff = 1.0 - i / (n - 1)
        cg = cg_position(design, ff)
        rows.append(
            f"  {ff:4.2f}{m_built - (1 - ff) * design.masses.fuel:10.2f}"
            f"{cg.x_cg_m:10.4f}{100 * cg.percent_mac:9.1f}"
            f"{100 * static_margin(design, ff):10.1f}"
            f"{100 * static_margin(design, ff, include_fuselage=True):14.1f}")
    rows.append("  " + "-" * 58)
    rows.append(f"  static-margin excursion full->empty: "
                f"{100 * cg_travel(design):+.2f}% MAC")
    return "\n".join(rows)


# =========================================================================
# Independent cross-check: AVL
# =========================================================================
# The recipe is the one docs/decisions/2026-08-20-gauntlet-audit.md section 4
# records as working against vendor/bin/avl ("12 sections, 24 spanwise panels,
# tip-bunched ... `a c 1.21` then `x`"), extended with a second SURFACE for the
# inverted-V tail and with `st`, which prints "Neutral point Xnp = ..." in the
# deck's own x. Two practical notes, both learned the hard way elsewhere in
# this repository:
#   * AVL exits with a NON-ZERO return code after `quit`. Do not check it;
#     parse the output.
#   * the deck must be fed a real AFILE for every section. NACA0010 has no
#     file in data/airfoils, so the coordinates come from
#     argus7.aero.buildup._section, which generates it.
# AVL is inviscid and carries no fuselage, so it is the right comparison for
# neutral_point(include_fuselage=False) and NOT for the Munk-corrected value.

AVL_BIN = "vendor/bin/avl"
AVL_MAX_SECTION_POINTS = 100


def write_avl_deck(design, path, deck_dir=None) -> str:
    """Write a wing + inverted-V-tail AVL deck in fuselage-station x."""
    import pathlib

    from argus7.aero.buildup import _section

    path = pathlib.Path(path)
    deck_dir = pathlib.Path(deck_dir) if deck_dir is not None else path.parent
    g = derive_wing(design.wing)
    tp = derive_tail_panel(design)
    bm = derive_booms(design)

    afiles = {}
    for role, name in (("w", design.wing.airfoil), ("t", design.tail.airfoil)):
        coords = _section(name)
        # AVL's READBL caps a section at IBX points and ABORTS THE SURFACE
        # past it -- and it does so with a "***" line in the middle of a
        # successful-looking load, not a non-zero exit. The generated NACA0010
        # comes out at 481 points and trips it, which silently drops the tail
        # and leaves a WING-ONLY neutral point that still looks plausible.
        # Decimate, keeping the first and last point.
        if len(coords) > AVL_MAX_SECTION_POINTS:
            step = int(math.ceil(len(coords) / AVL_MAX_SECTION_POINTS))
            idx = list(range(0, len(coords), step))
            if idx[-1] != len(coords) - 1:
                idx.append(len(coords) - 1)
            coords = coords[idx]
        f = deck_dir / f"{role}.dat"
        f.write_text(name + "\n" + "".join(f"{x:12.7f}{y:12.7f}\n"
                                          for x, y in coords))
        afiles[role] = str(f)

    semi = g.span_m / 2.0
    sweep = math.radians(design.wing.sweep_le_deg)
    dihedral = math.radians(design.wing.dihedral_deg)
    lines = [f"{design.name}-{design.variant}", "0.0", "0 0 0.0",
             f"{g.area_m2:.5f} {g.mac_m:.5f} {g.span_m:.5f}",
             f"{mac_le_x(design) + 0.25 * g.mac_m:.5f} 0.0 0.0", "0.0", "",
             "SURFACE", "Wing", "12 1.0 24 -2.0", "YDUPLICATE", "0.0",
             "ANGLE", "0.0", ""]
    n = 12
    for i in range(n):
        f = i / (n - 1)
        y = f * semi
        c = g.chord_root_m + f * (g.chord_tip_m - g.chord_root_m)
        lines += ["SECTION",
                  f"{wing_le_x(design) + y * math.tan(sweep):.5f} {y:.5f} "
                  f"{design.wing.z_offset_m + y * math.tan(dihedral):.5f} {c:.5f} "
                  f"{design.wing.incidence_deg + f * design.wing.twist_tip_deg:.4f} 0 0",
                  "AFILE", afiles["w"], ""]
    lines += ["SURFACE", "Tail", "8 1.0 12 -2.0", "YDUPLICATE", "0.0",
              "ANGLE", "0.0", ""]
    for f, c in ((0.0, tp.c_root_m), (1.0, tp.c_tip_m)):
        y = bm.y_station_m + f * tp.y_tip_offset_m
        z = f * tp.z_tip_offset_m
        lines += ["SECTION", f"{tp.x_le_m:.5f} {y:.5f} {z:.5f} {c:.5f} 0.0 0 0",
                  "AFILE", afiles["t"], ""]
    path.write_text("\n".join(lines) + "\n")
    return str(path)


def avl_neutral_point(design, alpha_deg: float = 2.0,
                      avl_bin: str = AVL_BIN,
                      timeout_s: float = 300.0) -> AVLNeutralPoint:
    """Vortex-lattice neutral point, as (x_np_m, percent_mac).

    AVL exits with a NON-ZERO return code after `quit`; the return code is
    deliberately not checked. What IS checked is that a surface was not
    silently dropped -- see write_avl_deck.
    """
    import subprocess
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        deck = write_avl_deck(design, f"{td}/balance.avl", td)
        proc = subprocess.run(
            [avl_bin],
            input=f"load {deck}\noper\na a {alpha_deg}\nx\nst\n\nquit\n",
            capture_output=True, text=True, timeout=timeout_s)
    if "Too many airfoil points" in proc.stdout:
        raise RuntimeError("AVL dropped a surface (READBL point limit) -- the "
                           "neutral point it reports would be wing-only.\n"
                           + proc.stdout[-2000:])
    hits = [ln for ln in proc.stdout.splitlines() if "Xnp" in ln]
    if not hits:
        raise RuntimeError("AVL did not report a neutral point.\n"
                           + proc.stdout[-2000:] + "\n" + proc.stderr[-500:])
    x_np = float(hits[-1].split("Xnp")[1].split("=")[1].split()[0])
    return AVLNeutralPoint(x_np, percent_mac(design, x_np))


def mass_budget_residual_kg(design) -> float:
    """design.masses.mtow minus the sum of the design file's own mass lines.

    Must be zero. It is not zero on v2.0 -- see
    tests/test_balance.py::test_v2_mass_budget_closes.
    """
    m = design.masses
    return m.mtow - (m.airframe + m.powertrain + m.avionics + m.recovery
                     + m.payload + m.fuel)
