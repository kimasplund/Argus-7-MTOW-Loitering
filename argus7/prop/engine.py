"""ARGUS-7 engine deck: shaft power available vs RPM and altitude, and a
load-dependent BSFC map.

Scope
-----
This module answers three questions and refuses to answer them dishonestly:

1. How much shaft power is on offer at a given crank RPM and altitude?
2. What does a kilowatt-hour of that shaft power cost in fuel, *at the load
   it is actually being taken at*?
3. How much extra shaft power does the 500 W payload cost through the
   alternator?

The headline result is that (2) and (3) together move the report's 4.70-day
loiter to ~3.95 days, because the report applied its assumed 270 g/kWh as a
flat constant at a point that is only ~20% of the engine's rating. A
constant BSFC is the single least defensible assumption in a 4.7-day
mission, so it is modelled explicitly here.

Everything SI at the boundary (W, kg/s, m, K, Pa). BSFC is carried in the
engineering unit the report and every engine datasheet use, g/kWh, and is
converted internally.

References
----------
Gagg, R. F. and Farrar, E. V. (1934), "Altitude Performance of Aircraft
    Engines Equipped with Gear-Driven Superchargers", SAE Transactions 29,
    p. 217. The naturally-aspirated limb of that paper is the relation used
    below; it is reproduced as the standard NA altitude lapse in Gudmundsson,
    S. (2014), "General Aviation Aircraft Design", Elsevier, section 7.3, and
    in Torenbeek, E. (1982), "Synthesis of Subsonic Airplane Design", §6.
Willans, P. W. (1888), "On the Efficiency of Steam-Engines", Proc. Inst. Civ.
    Eng. 93. The straight-line fuel-power relation named after him is the
    part-load model used below; see Guzzella, L. and Onder, C. (2010),
    "Introduction to Modeling and Control of Internal Combustion Engine
    Systems", 2nd ed., §2.4 ("Willans approximation"), and Heywood, J. B.
    (1988), "Internal Combustion Engine Fundamentals", §13.4 for the FMEP
    decomposition it rests on.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

__all__ = [
    "Engine",
    "EngineOverloadError",
    "isa_density",
    "density_ratio",
    "gagg_farrar_lapse",
]

# ---------------------------------------------------------------------------
# ISA. Troposphere only; the aircraft loiters at 4 km and never approaches
# the 11 km tropopause, so the model is deliberately not continued above it.
# ---------------------------------------------------------------------------
T_SL = 288.15                  # K
P_SL = 101325.0                # Pa
LAPSE_RATE = 0.0065            # K/m
R_AIR = 287.0528               # J/(kg K)
G0 = 9.80665                   # m/s2
TROPOPAUSE_M = 11000.0
# Derived, not the tabulated 1.225: deriving it from P_SL/(R*T_SL) keeps
# density_ratio(0) exactly 1.0. It agrees with the tabulated ISA value to
# 7 significant figures (1.2250003 vs 1.225); using the rounded constant
# instead made sigma(0) = 1 + 2.6e-7 and tripped the lapse-law domain check.
RHO_SL = P_SL / (R_AIR * T_SL)          # kg/m3

# ---------------------------------------------------------------------------
# Engine constants.
#
# The rating (17 kW), displacement, reduction ratio and prop RPM are NOT here:
# they are read from design/*.yaml through Engine.from_design. Only quantities
# with no home in the design file live as constants, each with its source.
# ---------------------------------------------------------------------------

# ASSUMPTION. Crank speed at which the rated power is developed. The report
# (section 6, shortlist item 1) selects a "Honda PCX160 eSP+ / Forza 250-class
# conversion" but never states the power-peak RPM; the Forza 250 / NSS250-class
# eSP+ single peaks at roughly 7,500-8,000 rpm. 7,500 is taken as the fitted
# reference. THIS MATTERS: the design's own gearing (prop_rpm x reduction_ratio)
# puts the crank at 4,830 rpm, i.e. 64% of this, so the rating is not reachable
# at the design prop speed -- see Engine.rating_reachable_at_design_gearing.
# A different engine choice moves this number and with it the climb case.
RATED_RPM = 7500.0

# Validity band of the normalised power-vs-RPM fit below. Outside it the cubic
# is meaningless (it goes negative past x = 1.5), so it raises rather than
# extrapolating: a silently-extrapolated engine deck is exactly the kind of
# plausible-looking wrong answer this programme has already been burned by.
RPM_FRAC_MIN = 0.15
RPM_FRAC_MAX = 1.15

# ASSUMPTION. Crank speed at which the torque curve peaks, as a fraction of
# the power-peak speed. 0.75 is typical of a modern small four-stroke SI
# single (torque peak ~5,500-6,000 rpm against a ~7,500-8,000 rpm power peak).
# It fixes the shape of the normalised power curve; see _power_fraction.
TORQUE_PEAK_RPM_FRAC = 0.75

# ASSUMPTION. Total mechanical + pumping loss power at rated speed, as a
# fraction of rated power, i.e. FMEP/BMEP at the rating. This single number
# sets how steep the part-load penalty is, and through it the whole endurance
# argument, so its provenance is spelled out in full:
#
# ADVERSARIAL REVIEW, 2026-08-20 -- THE ORIGINAL JUSTIFICATION DID NOT
# RECONSTRUCT THE VALUE, AND THE VALUE CONTRADICTS gagg_farrar_lapse:
#
#  (a) The comment previously read "~1.7 bar FMEP against ~9.5 bar BMEP
#      (Heywood §13.4, fig. 13-14)". BMEP is not free to assume: it follows
#      from the design's own numbers. BMEP = 2*P/(V_d*n) = 2*17 kW /
#      (250e-6 m3 * 125 rev/s) = 10.88 bar, NOT 9.5 -- see
#      Engine.bmep_at_rating_pa, which computes it and is asserted in
#      tests/test_engine.py. At 10.88 bar the quoted 1.7 bar FMEP gives
#      0.156, and 0.18 requires 1.96 bar. The cited source therefore does not
#      produce the cited constant either way.
#  (b) 1/7.55 = 0.1325 inside gagg_farrar_lapse is THE SAME PHYSICAL QUANTITY
#      -- friction power as a fraction of rated brake power -- because the
#      Gagg-Farrar relation is derived from P_b = sigma*P_i - P_f with P_f
#      density-independent, giving P/P0 = sigma - phi*(1 - sigma) with
#      phi = P_f/P_b,rated. This module currently carries phi = 0.1325 in the
#      altitude lapse and phi = 0.18 in the BSFC map: they disagree by 36%.
#
# The value is LEFT AT 0.18 rather than quietly reconciled, because choosing
# between them is a modelling decision with a headline consequence and it
# belongs to whoever owns the engine selection, not to a review pass:
#   phi = 0.1325 (Gagg-Farrar-consistent): loiter BSFC 309.8 g/kWh, 4.10 d,
#                and 10.62 kW at 4,000 m.
#   phi = 0.18   (as coded):               loiter BSFC 321.3 g/kWh, 3.95 d,
#                but a self-consistent lapse would then give 10.35 kW at
#                4,000 m, not the 10.62 kW power_available_w returns.
# Both still clear the report's >300 g/kWh walk-away; the endurance differs
# by 0.15 d. RESOLVE THIS BEFORE THE NUMBER IS QUOTED TO ANYONE.
FRICTION_POWER_FRACTION_AT_RATED = 0.18

# ASSUMPTION. Fraction of the rated-speed FMEP that survives at zero speed
# (boundary friction + the pumping floor). Makes loss power scale as
# n * (F0 + (1 - F0) * n/n_rated) rather than linearly in n, which is the
# usual quadratic-in-piston-speed behaviour of Chen-Flynn style FMEP fits.
FMEP_ZERO_SPEED_FRACTION = 0.45

# The report's numbers (docs/argus7_design_report.md).
BSFC_REPORT_FLAT_G_PER_KWH = 270.0   # section 4 mission-table caption; section 6
                                     # item 1, "design assumes 270 g/kWh".
                                     # APPLIED FLAT BY THE REPORT -- that is the
                                     # assumption this module replaces.
BSFC_TARGET_G_PER_KWH = 250.0        # section 6 item 1, "target <= 250" after
                                     # dyno mapping.
BSFC_WALKAWAY_G_PER_KWH = 300.0      # section "Tripwires": walk away if the
                                     # dyno shows > 300 g/kWh at the loiter
                                     # point.

# Load fraction at which BSFC_REPORT_FLAT_G_PER_KWH is taken to hold. The
# report does not say; 0.75 is the conventional cruise-rating point at which a
# manufacturer's headline BSFC is quoted, and anchoring there rather than at the
# loiter point is the conservative reading -- anchoring 270 g/kWh AT the loiter
# point would imply a 183.0 g/kWh asymptote, i.e. 45.2% INDICATED efficiency
# from a spark-ignition mogas single, which no candidate engine in section 6
# supports. (ADVERSARIAL REVIEW 2026-08-20: this comment previously said
# "~218 g/kWh"; 217.7 is the asymptote this file actually calibrates to at
# 0.75 load, not the one a loiter-point anchor would give. Recomputed:
# 270/(1 + 1584.8/3332.7) = 183.0. The argument is unaffected -- 45% indicated
# is even less defensible than the 38% the mis-stated number implied -- but the
# figure was wrong.)
#
# ADVERSARIAL REVIEW: THIS IS THE MOST LOAD-BEARING UNSOURCED NUMBER IN THE
# FILE. It, not the physics, decides whether the report's >300 g/kWh walk-away
# tripwire fires. Sweeping it at FRICTION_POWER_FRACTION_AT_RATED = 0.18:
#     0.50 -> loiter BSFC 292.9 g/kWh, 4.33 d  -- tripwire does NOT fire
#     0.60 -> 306.5 g/kWh, 4.14 d              -- fires
#     0.75 -> 321.3 g/kWh, 3.95 d              -- fires (as coded)
#     0.90 -> 332.0 g/kWh, 3.82 d              -- fires
# 0.50 is not an absurd alternative reading. Nothing in the report says at what
# load its 270 g/kWh holds, so the walk-away conclusion in
# tests/test_engine.py::test_mapped_loiter_bsfc_lands_in_the_reports_walkaway_band
# is an assumption's output, not a measurement's.
BSFC_REF_LOAD_FRACTION = 0.75

# ASSUMPTION. Alternator/rectifier/regulator chain efficiency from crank to
# payload bus. Report section 4: "0.5 kW electrical via 0.75 alternator path".
# Section 6 notes the stock stator (~343 W) cannot carry the 500 W payload and
# a ~1 kW crank-driven BLDC generator is a required modification; 0.75 is the
# assumed end-to-end efficiency of that modified path, not a measured figure.
ALTERNATOR_EFFICIENCY = 0.75

# Shaft power at the report's loiter point, W. Back-solved from the report's
# own arithmetic rather than read off its prose: section 3 fuel 101.5 kg and
# section 4 endurance 112.8 h at 270 g/kWh require 101.5/112.8/0.270 = 3.3327
# kW. That is the "shaft ~3.4 kW incl. 0.5 kW electrical via 0.75 alternator
# path" of section 4, to the precision the prose was rounded to. Held here as a
# constant because the aero side of it (2.8 kW aero at 250 kg) belongs to the
# aerodynamics module, not this one.
#
# ADVERSARIAL REVIEW 2026-08-20: REPORT_FUEL_MASS_KG DUPLICATES design.masses.fuel.
# A module-level constant cannot read the design file, and this quantity is a
# statement about what the REPORT computed, not about the current design -- but
# if design/*.yaml's fuel mass is ever changed this constant becomes silently
# stale. tests/test_engine.py::test_report_loiter_shaft_power_back_solves_from
# _the_report pins it against design.masses.fuel to 1e-9 so that divergence is
# a loud failure here rather than a quiet 15% error in an endurance number.
# The literal 0.270 was also replaced by BSFC_REPORT_FLAT_G_PER_KWH so the two
# copies of the report's BSFC cannot drift apart.
REPORT_FUEL_MASS_KG = 101.5           # report section 3 mass budget, "Fuel"
REPORT_ENDURANCE_H = 112.8            # report section 4 mission table, "Local ops"
REPORT_LOITER_SHAFT_POWER_W = (
    REPORT_FUEL_MASS_KG / REPORT_ENDURANCE_H
    / (BSFC_REPORT_FLAT_G_PER_KWH / 1e3) * 1e3
)

# Gasoline lower heating value, J/kg (mogas, per report section 6 item 1's fuel
# choice). Used only to report thermal efficiency, never in the fuel-flow path.
FUEL_LHV_J_PER_KG = 43.5e6


class EngineOverloadError(RuntimeError):
    """Raised when more shaft power is demanded than the engine can produce at
    the given RPM and altitude. Never silently clipped: a clipped power demand
    turns an infeasible flight condition into a feasible-looking fuel number."""


# ---------------------------------------------------------------------------
# Atmosphere
# ---------------------------------------------------------------------------

def isa_density(altitude_m: float) -> float:
    """ISA density, kg/m3, troposphere only."""
    if altitude_m < 0.0 or altitude_m > TROPOPAUSE_M:
        raise ValueError(
            f"altitude {altitude_m} m outside the modelled troposphere "
            f"[0, {TROPOPAUSE_M}] m"
        )
    t = T_SL - LAPSE_RATE * altitude_m
    p = P_SL * (t / T_SL) ** (G0 / (LAPSE_RATE * R_AIR))
    return p / (R_AIR * t)


def density_ratio(altitude_m: float) -> float:
    """sigma = rho / rho_sl."""
    return isa_density(altitude_m) / RHO_SL


def gagg_farrar_lapse(sigma: float) -> float:
    """Naturally-aspirated shaft-power lapse, Gagg & Farrar (1934).

        P/P_sl = sigma - (1 - sigma) / 7.55   ==   1.13245*sigma - 0.13245

    The engine loses more than the density ratio because friction and pumping
    losses do not lapse: indicated power scales with sigma, brake power is
    indicated minus a nearly density-independent loss. At 4,000 m, sigma =
    0.6687 but the deliverable power ratio is 0.6248.

    CONSISTENCY WARNING (adversarial review 2026-08-20): writing that
    derivation out gives P/P0 = sigma - phi*(1 - sigma) with
    phi = P_friction / P_brake,rated, so the 1/7.55 = 0.1325 above IS the same
    quantity as FRICTION_POWER_FRACTION_AT_RATED, which this module sets to
    0.18. The two are not reconciled -- see the note on that constant. This
    function is left on the empirical Gagg-Farrar 7.55 because that is what the
    literature reference actually says; the BSFC map is the side that carries
    the unsourced number.
    """
    if not 0.0 < sigma <= 1.0 + 1e-9:      # 1e-9 absorbs float round-trip only
        raise ValueError(f"density ratio {sigma} out of range (0, 1]")
    return sigma - (1.0 - sigma) / 7.55


# ---------------------------------------------------------------------------
# Normalised power vs RPM
# ---------------------------------------------------------------------------

def _power_fraction(rpm_frac: float) -> float:
    """P(n)/P_rated for a normalised crank speed x = n/n_rated.

    Derived, not curve-fitted to a datasheet: take torque quadratic in speed,
    Q/Q_rated = q0 + q1*x + q2*x^2, and impose three conditions --
      Q(1) = 1                         (rated torque at rated speed)
      d(Q*x)/dx = 0 at x = 1           (rated speed IS the power peak)
      dQ/dx = 0 at x = TORQUE_PEAK_RPM_FRAC
    With TORQUE_PEAK_RPM_FRAC = 0.75 this gives q = (0, 3, -2) exactly, i.e.

        Q/Q_rated = 3x - 2x^2          (12.5% torque rise at the torque peak)
        P/P_rated = x^2 * (3 - 2x)

    Valid on [RPM_FRAC_MIN, RPM_FRAC_MAX] and nowhere else.
    """
    x_tq = TORQUE_PEAK_RPM_FRAC
    if not 0.0 < x_tq < 1.0:
        raise ValueError("torque peak must lie below the power peak")
    # Closed-form solution of the three conditions above:
    #   q1 = -2*q2*x_tq  and  q1 = -1 - 2*q2   =>   q2 = -1 / (2*(1 - x_tq))
    q2 = -1.0 / (2.0 * (1.0 - x_tq))
    q1 = -2.0 * q2 * x_tq
    q0 = 1.0 - q1 - q2
    x = rpm_frac
    return (q0 + q1 * x + q2 * x * x) * x


# ---------------------------------------------------------------------------
# Engine deck
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Engine:
    """Shaft-power and fuel-consumption deck for the ARGUS-7 powerplant.

    Construct with Engine.from_design(design); the rating, gearing and
    electrical draw all come from design/*.yaml.
    """

    rated_power_w: float
    rated_rpm: float
    reduction_ratio: float
    design_prop_rpm: float
    payload_power_w: float
    displacement_cc: float

    # -- construction --------------------------------------------------------

    @classmethod
    def from_design(cls, design) -> "Engine":
        p = design.propulsion
        return cls(
            rated_power_w=p.power_max_kw * 1e3,
            rated_rpm=RATED_RPM,
            reduction_ratio=p.reduction_ratio,
            design_prop_rpm=p.prop_rpm,
            payload_power_w=design.mission.payload_power_w,
            displacement_cc=p.engine_displacement_cc,
        )

    # -- gearing -------------------------------------------------------------

    @property
    def loiter_crank_rpm(self) -> float:
        """Crank speed implied by the design's prop RPM and reduction ratio."""
        return self.design_prop_rpm * self.reduction_ratio

    def crank_rpm_for_prop_rpm(self, prop_rpm: float) -> float:
        return prop_rpm * self.reduction_ratio

    def prop_rpm_for_crank_rpm(self, crank_rpm: float) -> float:
        return crank_rpm / self.reduction_ratio

    # -- power available -----------------------------------------------------

    def _check_rpm(self, rpm: float) -> float:
        x = rpm / self.rated_rpm
        if not RPM_FRAC_MIN <= x <= RPM_FRAC_MAX:
            raise ValueError(
                f"crank speed {rpm:.0f} rpm is {x:.3f} of rated; the power fit "
                f"is only valid on [{RPM_FRAC_MIN}, {RPM_FRAC_MAX}] of rated "
                f"({RPM_FRAC_MIN*self.rated_rpm:.0f}-"
                f"{RPM_FRAC_MAX*self.rated_rpm:.0f} rpm)"
            )
        return x

    def power_available_w(self, rpm: float | None = None,
                          altitude_m: float = 0.0) -> float:
        """Maximum shaft power at a crank speed and altitude, W.

        rpm=None means rated speed.
        """
        rpm = self.rated_rpm if rpm is None else rpm
        x = self._check_rpm(rpm)
        return (self.rated_power_w * _power_fraction(x)
                * gagg_farrar_lapse(density_ratio(altitude_m)))

    def load_fraction(self, shaft_power_w: float, rpm: float | None = None,
                      altitude_m: float = 0.0) -> float:
        """Shaft power as a fraction of what is available AT THAT RPM AND
        ALTITUDE -- which is the load the BSFC map actually cares about, and is
        not the same as shaft_power/rated_power."""
        return shaft_power_w / self.power_available_w(rpm, altitude_m)

    @property
    def bmep_at_rating_pa(self) -> float:
        """Brake mean effective pressure at the rating, Pa.

        Four-stroke: BMEP = 2 * P / (V_d * n). Not decoration -- this is the
        arithmetic that shows FRICTION_POWER_FRACTION_AT_RATED's stated
        justification does not reconstruct it: the design's own 250 cc and
        17 kW at RATED_RPM give 10.88 bar, not the ~9.5 bar that comment
        assumed. `displacement_cc` was otherwise a dead field on this
        dataclass, which is why nobody noticed.
        """
        rev_per_s = self.rated_rpm / 60.0
        displacement_m3 = self.displacement_cc * 1e-6
        return 2.0 * self.rated_power_w / (displacement_m3 * rev_per_s)

    def rating_reachable_at_design_gearing(self) -> bool:
        """False, for the v1.0 design: the gearing cannot reach the power peak.
        Exposed as a method so a caller can assert on it instead of discovering
        it in a climb calculation."""
        # A gearing that puts the crank outside the fitted band cannot reach the
        # rating either, and must not make this predicate raise -- that was the
        # behaviour for any prop_rpm above ~3,750 (crank > 1.15 * rated), i.e.
        # exactly the over-geared cases this method exists to diagnose.
        x = self.loiter_crank_rpm / self.rated_rpm
        if not RPM_FRAC_MIN <= x <= RPM_FRAC_MAX:
            return False
        return math.isclose(
            self.power_available_w(self.loiter_crank_rpm, 0.0),
            self.rated_power_w,
            rel_tol=1e-3,
        )

    # -- electrical path -----------------------------------------------------

    def electrical_shaft_power_w(self, electrical_w: float | None = None) -> float:
        """Shaft power absorbed by the alternator to deliver `electrical_w` to
        the bus. Defaults to the design's payload draw.

        This is a real, continuous, 4.7-day-long load: 500 W of payload costs
        667 W of shaft, 20% of the entire loiter shaft power.
        """
        w = self.payload_power_w if electrical_w is None else electrical_w
        if w < 0.0:
            raise ValueError("electrical demand cannot be negative")
        return w / ALTERNATOR_EFFICIENCY

    def shaft_power_demand_w(self, propulsive_shaft_power_w: float,
                             electrical_w: float | None = None) -> float:
        """Total shaft demand = propeller shaft power + alternator shaft power."""
        return propulsive_shaft_power_w + self.electrical_shaft_power_w(electrical_w)

    # -- BSFC map ------------------------------------------------------------

    def _loss_power_w(self, rpm: float) -> float:
        """Mechanical + pumping loss power at a crank speed, W.

        FMEP is taken as FMEP_rated * (F0 + (1-F0)*x), so loss power, which is
        FMEP * V_d * n / 2, scales as x*(F0 + (1-F0)*x): near-quadratic in
        speed, as measured FMEP data are.
        """
        x = rpm / self.rated_rpm
        f0 = FMEP_ZERO_SPEED_FRACTION
        loss_rated = FRICTION_POWER_FRACTION_AT_RATED * self.rated_power_w
        return loss_rated * x * (f0 + (1.0 - f0) * x)

    @property
    def bsfc_asymptote_g_per_kwh(self) -> float:
        """The Willans-line asymptote: BSFC an infinitely-loaded engine of this
        indicated efficiency would show. Calibrated so that BSFC at
        BSFC_REF_LOAD_FRACTION of rating, at rated speed, equals the report's
        270 g/kWh. Works out at 217.7 g/kWh, i.e. 38% indicated thermal
        efficiency -- plausible for a modern SI engine, and the check that the
        calibration has not been pushed into fantasy."""
        p_ref = BSFC_REF_LOAD_FRACTION * self.rated_power_w
        return BSFC_REPORT_FLAT_G_PER_KWH / (
            1.0 + self._loss_power_w(self.rated_rpm) / p_ref
        )

    def bsfc_g_per_kwh(self, shaft_power_w: float,
                       rpm: float | None = None) -> float:
        """Brake specific fuel consumption at a shaft power and crank speed.

        Willans line: fuel power is affine in brake power, because the fuel
        buys INDICATED work and a nearly load-independent loss is subtracted
        from it. Hence

            BSFC(P) = k * (1 + P_loss(n) / P)

        which is flat at high load and blows up hyperbolically as P falls --
        the "worsens markedly below about 40% load" behaviour. At the ARGUS-7
        loiter point (3.33 kW at 4,830 rpm) it returns ~321 g/kWh against the
        report's flat 270, which is above the report's own >300 g/kWh
        walk-away tripwire.

        DOCUMENTED CONSERVATISM: throttling losses are folded into P_loss at a
        speed-dependent but LOAD-INDEPENDENT level. A throttled SI engine's
        PMEP actually grows as load falls, so the true deep-part-load penalty
        is worse than modelled here, not better. This model is the optimistic
        bound.
        """
        rpm = self.rated_rpm if rpm is None else rpm
        self._check_rpm(rpm)
        if shaft_power_w <= 0.0:
            raise ValueError(
                "BSFC is undefined at zero or negative shaft power "
                "(the engine burns fuel while producing none)"
            )
        return self.bsfc_asymptote_g_per_kwh * (
            1.0 + self._loss_power_w(rpm) / shaft_power_w
        )

    def brake_thermal_efficiency(self, shaft_power_w: float,
                                 rpm: float | None = None) -> float:
        """Sanity handle on the BSFC map: eta = 3.6e9 / (LHV * BSFC)."""
        return 3.6e9 / (FUEL_LHV_J_PER_KG * self.bsfc_g_per_kwh(shaft_power_w, rpm))

    # -- fuel flow and endurance --------------------------------------------

    def fuel_flow_kg_h(self, shaft_power_w: float, rpm: float | None = None,
                       altitude_m: float = 0.0,
                       bsfc_g_per_kwh: float | None = None) -> float:
        """Fuel flow, kg/h, at a shaft power / RPM / altitude.

        `bsfc_g_per_kwh` overrides the map with a constant -- used to reproduce
        the report's own flat-270 arithmetic, and for nothing else.

        Raises EngineOverloadError if the demand exceeds what the engine can
        make at that condition.
        """
        rpm = self.rated_rpm if rpm is None else rpm
        # Guarded here as well as in bsfc_g_per_kwh: with a BSFC override the
        # map is bypassed, and a zero shaft power then returned a zero fuel flow
        # that endurance_h turned into a ZeroDivisionError rather than a message.
        if shaft_power_w <= 0.0:
            raise ValueError(
                f"shaft power must be positive, got {shaft_power_w} W"
            )
        available = self.power_available_w(rpm, altitude_m)
        if shaft_power_w > available:
            raise EngineOverloadError(
                f"{shaft_power_w/1e3:.2f} kW demanded at {rpm:.0f} rpm / "
                f"{altitude_m:.0f} m, but only {available/1e3:.2f} kW is "
                f"available there (rating {self.rated_power_w/1e3:.1f} kW at "
                f"{self.rated_rpm:.0f} rpm, sea level)"
            )
        if bsfc_g_per_kwh is None:
            b = self.bsfc_g_per_kwh(shaft_power_w, rpm)
        else:
            # ADVERSARIAL REVIEW 2026-08-20: the override was unvalidated, so a
            # negative BSFC produced a negative fuel flow and endurance_h then
            # returned a negative endurance without complaint (-112.8 h for
            # bsfc=-270). Nonsense in must not become plausible-shaped nonsense
            # out; a zero override was a bare ZeroDivisionError one level up.
            if bsfc_g_per_kwh <= 0.0:
                raise ValueError(
                    f"BSFC override must be positive, got {bsfc_g_per_kwh} g/kWh"
                )
            b = bsfc_g_per_kwh
        return b * (shaft_power_w / 1e3) / 1e3

    def fuel_flow_kg_s(self, shaft_power_w: float, rpm: float | None = None,
                       altitude_m: float = 0.0,
                       bsfc_g_per_kwh: float | None = None) -> float:
        return self.fuel_flow_kg_h(shaft_power_w, rpm, altitude_m,
                                   bsfc_g_per_kwh) / 3600.0

    def endurance_h(self, fuel_mass_kg: float, shaft_power_w: float,
                    rpm: float | None = None, altitude_m: float = 0.0,
                    bsfc_g_per_kwh: float | None = None) -> float:
        """Constant-power, constant-mass endurance, h.

        Deliberately NOT a Breguet integral: the mass-dependent part of the
        loiter power belongs to the aerodynamics module, and this deck must not
        grow a second, divergent copy of the drag polar. Call this per segment
        with the segment's shaft power.
        """
        if fuel_mass_kg <= 0.0:
            raise ValueError("fuel mass must be positive")
        return fuel_mass_kg / self.fuel_flow_kg_h(
            shaft_power_w, rpm, altitude_m, bsfc_g_per_kwh
        )
