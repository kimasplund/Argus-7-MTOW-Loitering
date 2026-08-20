"""Component parasite-drag build-up for ARGUS-7.

METHOD
------
The classical conceptual-design component build-up (Raymer, *Aircraft
Design: A Conceptual Approach*, 6th ed., §12.5.1-12.5.4; Hoerner,
*Fluid-Dynamic Drag*, ch. 6; Torenbeek, *Synthesis of Subsonic Airplane
Design*, App. F):

    C_D0 = ( sum_i  C_f_i * FF_i * Q_i * S_wet_i ) / S_ref   +  misc

per component i, where

  * ``S_wet``  is the wetted area, taken from the ACTUAL geometry the design
    file defines -- the real FX 63-137 arc length, the real fuselage station
    loft, the derived boom length, the true (not projected) tail panel area.
    Nothing here is a chord, span or area typed into Python.
  * ``C_f``    is the flat-plate skin-friction coefficient with a
    laminar/turbulent split at a SUPPLIED transition location (see below).
  * ``FF``     is a form factor (pressure drag of the finite-thickness shape,
    relative to a flat plate of the same wetted area).
  * ``Q``      is an interference factor for the junction the component makes
    with its neighbours.

TRANSITION IS AN INPUT, NOT AN ASSUMPTION
-----------------------------------------
The wing is the majority of the wetted area and it is a laminar-flow section
at a Reynolds number where it actually keeps a laminar run. Assuming fully
turbulent flow -- the usual conceptual-design default -- overstates its
friction drag by about 60%. ``parasite_buildup`` therefore takes the wing
transition location as an argument, defaulting to the values MEASURED with
the project's verified XFOIL sequence (Ncrit 9, 300 panels): x_tr/c = 0.5023
at the root Reynolds number and 0.6051 at the tip. Transition is interpolated
linearly along the span between them, and every strip's friction is computed
at its own local Reynolds number.

WHAT THIS MODULE DOES NOT CONTAIN, AND WHY THE ANSWER IS LOW
------------------------------------------------------------
For design/argus7_v1.yaml this build-up returns C_D0 ~= 0.0154, against the
0.020 the design file states (report §4). That is a real disagreement and it
is deliberately left standing rather than absorbed into a fudge factor. The
report itself brackets C_D0 as 0.016 optimistic clean build / 0.020 realistic
/ 0.024 dirty with external antennas, and what this module computes IS the
optimistic clean build: only the four wetted bodies the design file defines,
with a measured laminar run, plus a leakage-and-protuberance allowance.

PART of the difference is method error in this module, not missing hardware
-- see the NeuralFoil cross-check below, which is worth ~0.0009 -- and part of
it is pressure drag this friction build-up structurally cannot carry. The rest
has to be made of things the design file does not describe:

  * the 50 kg payload installation -- a gimballed EO/IR ball of ~0.3 m
    diameter at C_D 0.4 on frontal area is alone worth ~0.007 in C_D0, more
    than a third of the report's total;
  * engine cooling drag for the 17 kW engine (typically 5-10% of total drag
    on a piston installation);
  * fuselage base drag: the aft station closes to r/R = 0.34, leaving a
    0.021 m2 base;
  * landing gear, skid or launch/recovery hardware (masses.recovery is 7 kg,
    and none of it appears in the geometry).

Adding a payload turret to design/*.yaml is the way to close this, not
raising a factor here.

AND A COMPLICATION, WHICH THIS MODULE CANNOT RESOLVE
----------------------------------------------------
Re-run the identical build-up with the wing assumed FULLY TURBULENT -- the
conceptual-design default, and what you get if you never run XFOIL -- and it
returns C_D0 = 0.0200, the design file's stated value to three decimals. So
the gap above admits two readings that are numerically indistinguishable
here: either report §4's 0.020 is a fully-turbulent build-up of this same
clean geometry and therefore contains no allowance for the payload
installation at all (in which case the endurance model is
anti-conservative), or it is a laminar build-up that does include that
hardware and the agreement is a coincidence. Guarded by
tests/test_buildup.py::test_fully_turbulent_wing_reproduces_the_report_baseline.

CROSS-CHECK AGAINST NEURALFOIL, AND A KNOWN BIAS IN THE WING TERM
-----------------------------------------------------------------
The wing is 48% of the drag area, so it was checked strip-by-strip against
NeuralFoil (xxlarge) on the same FX 63-137 coordinates, at each strip's own
Reynolds number, with the section trimmed to Cl = 1.21. Two results:

  * TRANSITION IS CORROBORATED. NeuralFoil puts upper-surface transition at
    x/c 0.547 (root, Re 991k) to 0.599 (tip, Re 459k), against the 0.5023 to
    0.6051 this module interpolates from the verified XFOIL runs. It also
    confirms the docstring's assumption on X_TR_WING_* that the lower surface
    runs at least as far laminar (0.585 root, 0.634 tip).

  * DRAG IS BIASED LOW AT THE LOITER LIFT COEFFICIENT. Integrated over the
    exposed span, the Cf*FF build-up gives a wing drag area of 0.02884 m2
    against NeuralFoil's 0.03207 m2 -- 11.2% low, i.e. +0.00088 in C_D0. The
    cause is structural, not a coding error: Raymer's form factor (eq. 12.30)
    is a function of t/c and (x/c)_m only, so it is a MINIMUM-DRAG pressure
    correlation with no Cl dependence. At the minimum-drag point it is in fact
    slightly HIGH (0.00784 vs NeuralFoil's 0.00735 at the MAC), which is the
    signature of exactly this: the method is calibrated near zero lift and
    ARGUS-7 loiters at Cl 1.21, where the real section carries considerably
    more pressure drag. Washout shrinks the gap but does not close it -- even
    letting the tip strip run at Cl 0.75 leaves the tip 3% low.

    This module therefore has it both ways: it takes a transition location
    MEASURED at Cl 1.21 (lift-dependent) and pairs it with a form factor valid
    near zero lift, then labels the result C_D0 and compares it to a design
    file whose polar is C_D = C_D0 + C_L^2/(pi AR e) with e = 0.85. Consumers
    should know that the number this returns is neither a clean zero-lift
    C_D0 nor the full profile drag at loiter. A lifting-line or panel module
    that carries section drag as a function of local Cl is the right fix; this
    correlation cannot be repaired by adjusting a constant in it.

The consequence for the headline disagreement is that the -23.6% gap is less
certain than it looks. The wing bias (+0.00088) plus the two base-drag terms
this module names but does not carry (boom end discs +0.00049, fuselage base
+0.00080 at C_Db 0.15, the latter arguable because the pusher propeller works
that base) come to roughly +0.0022, which would put C_D0 near 0.0175 -- INSIDE
the +/-15% gate, with no payload turret invoked at all. Read
test_total_cd0_against_report_baseline with that in mind: the sign of the
disagreement is solid, its size is not.

UNITS: SI throughout.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache

import numpy as np

from argus7.cad.airfoil_coords import load_airfoil, naca4, max_thickness
from argus7.design.geometry import derive_booms, derive_tail_panel, derive_wing

# ---------------------------------------------------------------------------
# constants -- every one of these is an assumption, and carries its source
# ---------------------------------------------------------------------------

GRAVITY_MS2 = 9.80665            # ISO 80000-3 standard gravity
R_AIR_JKGK = 287.05287           # ICAO Doc 7488/3 specific gas constant
GAMMA_AIR = 1.4
T0_K, P0_PA, RHO0_KGM3 = 288.15, 101325.0, 1.225      # ISA sea level
LAPSE_KM = 0.0065                # ISA troposphere lapse rate [K/m]
SUTHERLAND_C1 = 1.458e-6         # [kg/(m s K^0.5)], ICAO/US Std Atm 1976
SUTHERLAND_S_K = 110.4

# Loiter lift coefficient. NOT a design-file field: the file fixes mass, area
# and altitude, and CL is what closes the lift equation at the report's stated
# loiter speed. 1.21 is the established Phase-1 result (report §4: 128 km/h
# TAS heavy at 4000 m -> CL 1.21 at MTOW).
LOITER_CL = 1.21

# Wing transition, MEASURED, not assumed: XFOIL 6.99, Ncrit 9, 300 panels,
# FX 63-137 at CL 1.21 (see research/riblets_pack.md verification note).
# Upper-surface transition; the lower surface of a high-camber section at
# positive CL runs at least as far laminar, so using the upper-surface value
# for the whole section is the conservative choice.
X_TR_WING_ROOT = 0.5023          # at Re 992372
X_TR_WING_TIP = 0.6051           # at Re 486526

# Transition on the other components. ASSUMPTIONS -- there is no XFOIL result
# for a body of revolution and none of these were measured.
#   fuselage: a moulded composite pod with a blunt nose (r/R = 0.15 at x = 0)
#     and a pusher installation; Hoerner ch. 6 and Torenbeek App. F both put
#     natural transition on such a nose within the first tenth of the length.
X_TR_FUSELAGE = 0.10
#   booms: smooth constant-section tubes in clean flow ahead of the wing, but
#     tripped by the wing junction they pass through at 41% of their length.
X_TR_BOOM = 0.15
#   tail: NACA 0010, symmetric, at Re ~5.5e5 and near-zero lift; XFOIL-class
#     natural transition on a 4-digit section at that Re sits near the
#     pressure minimum, x/c ~ 0.3. Held down by the boom wake.
X_TR_TAIL = 0.30

# Interference factors, Raymer table in §12.5.3.
Q_WING = 1.00        # mid-wing, filleted (design has a let-in wing/boom joint)
Q_FUSELAGE = 1.00    # Raymer: Q = 1.0 for the fuselage itself
Q_BOOM = 1.30        # Raymer's rule for a body mounted directly on the wing is
                     # 1.5, relaxed to 1.3 here because a boom pierces the wing
                     # as a faired let-in joint rather than hanging off a pylon.
                     # This is the least defensible constant in the module; the
                     # 1.0-1.5 spread it sits in is worth +/-0.0009 in C_D0.
Q_TAIL = 1.05        # Raymer: conventional tail 1.05, V-tail 1.03. The
                     # inverted V makes two boom junctions, so 1.05 not 1.03.

# Surface roughness for the cutoff Reynolds number (Raymer table 12.4):
# smooth moulded composite, 0.17e-5 ft.
SKIN_ROUGHNESS_M = 0.17e-5 * 0.3048

# Miscellaneous / excrescence allowance, as a fraction of the clean component
# sum. Raymer §12.5.6 gives leakage-and-protuberance as 2-5% for a propeller
# aircraft; 6% is the top of that band plus an allowance for the antennas,
# control-surface gaps, pitot/static and access panels an operational UAV
# carries. It does NOT cover the payload installation, cooling drag or landing
# gear -- see the module docstring.
MISC_EXCRESCENCE_FRACTION = 0.06

# Compressibility: Raymer's form-factor bracket [1.34 M^0.18 (cos L_m)^0.28]
# is fitted to transonic data and evaluates to 0.90 at M = 0.11, i.e. it would
# REDUCE the form factor below its incompressible value. It is therefore not
# applied below this Mach number; the incompressible bracket is used instead.
MACH_COMPRESSIBILITY_FLOOR = 0.20

N_WING_STRIPS = 200      # spanwise strips for the wing friction integration


# ---------------------------------------------------------------------------
# atmosphere (local, troposphere only)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AtmosphereState:
    altitude_m: float
    temperature_k: float
    pressure_pa: float
    density_kgm3: float
    viscosity_pas: float
    sound_speed_ms: float


def isa_troposphere(altitude_m: float) -> AtmosphereState:
    """ICAO standard atmosphere, troposphere only (0 - 11000 m).

    Deliberately local. The project's full differentiable/batched ISA lives in
    the mission package; this module is a geometry+correlation calculator that
    must stay importable without it, and 11 km of troposphere is all a
    4000 m loiter needs. Verified against the ICAO Doc 7488/3 table in
    tests/test_buildup.py::test_local_isa_matches_icao_table.
    """
    if not 0.0 <= altitude_m <= 11000.0:
        raise ValueError(f"troposphere model valid 0-11000 m, got {altitude_m}")
    t = T0_K - LAPSE_KM * altitude_m
    p = P0_PA * (t / T0_K) ** (GRAVITY_MS2 / (LAPSE_KM * R_AIR_JKGK))
    rho = p / (R_AIR_JKGK * t)
    mu = SUTHERLAND_C1 * t ** 1.5 / (t + SUTHERLAND_S_K)     # Sutherland's law
    a = math.sqrt(GAMMA_AIR * R_AIR_JKGK * t)
    return AtmosphereState(altitude_m, t, p, rho, mu, a)


@dataclass(frozen=True)
class FlowCondition:
    velocity_ms: float
    density_kgm3: float
    viscosity_pas: float
    sound_speed_ms: float
    altitude_m: float = 0.0

    @property
    def reynolds_per_m(self) -> float:
        return self.density_kgm3 * self.velocity_ms / self.viscosity_pas

    @property
    def mach(self) -> float:
        return self.velocity_ms / self.sound_speed_ms

    @property
    def dynamic_pressure_pa(self) -> float:
        return 0.5 * self.density_kgm3 * self.velocity_ms ** 2


def flow_at(altitude_m: float, velocity_ms: float) -> FlowCondition:
    a = isa_troposphere(altitude_m)
    return FlowCondition(velocity_ms, a.density_kgm3, a.viscosity_pas,
                         a.sound_speed_ms, altitude_m)


def loiter_flow(design, cl: float = LOITER_CL, mass_kg: float | None = None,
                altitude_m: float | None = None) -> FlowCondition:
    """Loiter condition from the design file: altitude from mission, mass from
    masses.mtow, area from derive_wing, speed from the lift equation at `cl`."""
    h = design.mission.loiter_altitude_m if altitude_m is None else altitude_m
    m = design.masses.mtow if mass_kg is None else mass_kg
    s = derive_wing(design.wing).area_m2
    atm = isa_troposphere(h)
    v = math.sqrt(2.0 * m * GRAVITY_MS2 / (atm.density_kgm3 * s * cl))
    return FlowCondition(v, atm.density_kgm3, atm.viscosity_pas,
                         atm.sound_speed_ms, h)


# ---------------------------------------------------------------------------
# skin friction
# ---------------------------------------------------------------------------

def cf_laminar(re: float) -> float:
    """Blasius flat plate, incompressible: C_f = 1.328 / sqrt(Re)."""
    return 1.328 / math.sqrt(max(re, 1.0))


def cf_turbulent(re: float) -> float:
    """Prandtl-Schlichting / Raymer eq. 12.27: C_f = 0.455 / (log10 Re)^2.58.

    The compressibility divisor (1 + 0.144 M^2)^0.65 is omitted: at M = 0.11 it
    is 1.0011.
    """
    return 0.455 / math.log10(max(re, 10.0)) ** 2.58


def cutoff_reynolds(length_m: float,
                    roughness_m: float = SKIN_ROUGHNESS_M) -> float:
    """Raymer eq. 12.28 (subsonic): above this Reynolds number the surface is
    hydraulically rough and the friction stops falling with Re. For a moulded
    composite ARGUS-7 it evaluates to ~6.7e7 on the wing MAC -- two orders
    above the flight Reynolds number, so it never binds. Kept because it is
    part of the method and because a painted or taped surface would change
    that."""
    return 38.21 * (length_m / roughness_m) ** 1.053


def cf_mixed(re: float, x_tr: float, length_m: float | None = None,
             roughness_m: float = SKIN_ROUGHNESS_M) -> float:
    """Flat-plate skin friction with a laminar run to x_tr, turbulent after.

    Standard superposition (Torenbeek App. F; Hoerner ch. 2): take the fully
    turbulent plate and give back the difference between turbulent and laminar
    friction over the laminar run,

        C_f = C_f_turb(Re_L) + x_tr * [C_f_lam(Re_tr) - C_f_turb(Re_tr)]

    with Re_tr = x_tr * Re_L. The turbulent boundary layer downstream is thus
    treated as starting from a virtual origin ahead of the transition point,
    which is the conservative reading (it does not credit the thinner
    downstream layer).
    """
    if not 0.0 <= x_tr <= 1.0:
        raise ValueError(f"x_tr must be in [0, 1], got {x_tr}")
    re_eff = re if length_m is None else min(re, cutoff_reynolds(length_m, roughness_m))
    cft = cf_turbulent(re_eff)
    if x_tr <= 0.0:
        return cft
    re_tr = max(x_tr * re_eff, 1.0)
    return cft + x_tr * (cf_laminar(re_tr) - cf_turbulent(re_tr))


# ---------------------------------------------------------------------------
# form factors
# ---------------------------------------------------------------------------

def form_factor_airfoil(t_c: float, x_tc: float, mach: float = 0.0,
                        sweep_max_t_rad: float = 0.0) -> float:
    """Raymer eq. 12.30 for a wing/tail/strut:

        FF = [1 + 0.6/(x/c)_m * (t/c) + 100 (t/c)^4]
             * [1.34 M^0.18 (cos L_m)^0.28]

    The second bracket is applied only above MACH_COMPRESSIBILITY_FLOOR; below
    it the correlation is out of its fitted range and drives FF below 1.
    """
    ff = 1.0 + 0.6 / x_tc * t_c + 100.0 * t_c ** 4
    if mach >= MACH_COMPRESSIBILITY_FLOOR:
        ff *= 1.34 * mach ** 0.18 * math.cos(sweep_max_t_rad) ** 0.28
    return ff


def form_factor_body(fineness: float, method: str = "auto") -> float:
    """Form factor of a body of revolution of fineness ratio f = l/d.

    "raymer"  : FF = 1 + 60/f^3 + f/400 (Raymer eq. 12.31). Fitted to
                fuselage-like bodies, f ~ 5-15.
    "hoerner" : FF = 1 + 1.5/f^1.5 + 7/f^3 (Hoerner, Fluid-Dynamic Drag,
                ch. 6, streamline bodies).
    "auto"    : Raymer at f <= 10, Hoerner above.

    The switch is deliberate, not a convenience. ARGUS-7's tail booms have
    f = 40.5, far outside Raymer's fitted range, where its linear f/400 term
    alone adds 10% of pressure drag to what is essentially a rolled-up flat
    plate. Hoerner's form tends correctly to 1 as f -> infinity. The two
    formulas differ by only 2.8% at the f = 10 crossover (1.085 vs 1.055), so
    the switch does not put a step in any sweep that crosses it.
    """
    if method == "auto":
        method = "raymer" if fineness <= 10.0 else "hoerner"
    if method == "raymer":
        return 1.0 + 60.0 / fineness ** 3 + fineness / 400.0
    if method == "hoerner":
        return 1.0 + 1.5 / fineness ** 1.5 + 7.0 / fineness ** 3
    raise ValueError(f"unknown body form-factor method {method!r}")


# ---------------------------------------------------------------------------
# section geometry read off the real coordinates
# ---------------------------------------------------------------------------

def _section(name: str) -> np.ndarray:
    """Selig-ordered coordinates for a named section. NACA 4-digit names are
    generated; everything else comes from data/airfoils via load_airfoil,
    which handles both Selig and Lednicer files."""
    key = name.upper().replace("-", "").replace(" ", "")
    if key.startswith("NACA") and len(key) == 8 and key[4:].isdigit():
        return naca4(key[4:], n=241)
    return load_airfoil(name)


@lru_cache(maxsize=32)
def airfoil_perimeter_ratio(name: str) -> float:
    """Arc length of the section, per unit chord -- i.e. the wetted area of a
    unit-chord, unit-span wing panel, both surfaces.

    This replaces the usual approximation S_wet ~ 2(1 + 0.2 t/c) S_exposed
    (Raymer eq. 7.11) with the real thing. Computed as the polygon length of
    the coordinate file, which underestimates the true arc length by well
    under 0.5% at the point densities in use (97 points for FX 63-137,
    241 for a generated NACA section).
    """
    c = _section(name)
    return float(np.sum(np.hypot(np.diff(c[:, 0]), np.diff(c[:, 1]))))


@lru_cache(maxsize=32)
def airfoil_thickness(name: str) -> float:
    """Maximum thickness/chord, measured from the coordinates."""
    return float(max_thickness(_section(name)))


@lru_cache(maxsize=32)
def airfoil_max_thickness_x(name: str) -> float:
    """Chordwise station of maximum thickness, measured from the coordinates.
    Raymer eq. 12.30 needs it and it is not a digit of the section name."""
    c = _section(name)
    le = int(np.argmin(c[:, 0]))
    upper, lower = c[:le + 1][::-1], c[le:]
    xs = np.linspace(0.0, 1.0, 1001)
    t = np.interp(xs, upper[:, 0], upper[:, 1]) - np.interp(xs, lower[:, 0], lower[:, 1])
    return float(xs[int(np.argmax(t))])


# ---------------------------------------------------------------------------
# components
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Component:
    """One term of the build-up.

    ``drag_area_m2`` is the equivalent flat-plate ("f") area, C_f*FF*Q*S_wet.
    It is the stored quantity because the miscellaneous allowance has a drag
    area but no wetted area of its own; for every geometric component it is
    exactly the product of the fields below it.
    """
    name: str
    drag_area_m2: float
    s_ref_m2: float
    wetted_area_m2: float | None = None
    reference_length_m: float | None = None
    reynolds: float | None = None
    laminar_fraction: float | None = None
    cf: float | None = None
    form_factor: float | None = None
    interference_factor: float | None = None
    note: str = ""

    @property
    def cd0(self) -> float:
        return self.drag_area_m2 / self.s_ref_m2

    @classmethod
    def flat_plate(cls, name, *, s_wet, cf, ff, q, s_ref, length, re,
                   laminar_fraction, note=""):
        return cls(name=name, drag_area_m2=cf * ff * q * s_wet, s_ref_m2=s_ref,
                   wetted_area_m2=s_wet, reference_length_m=length, reynolds=re,
                   laminar_fraction=laminar_fraction, cf=cf, form_factor=ff,
                   interference_factor=q, note=note)


def wing_component(design, flow: FlowCondition,
                   x_tr_root: float = X_TR_WING_ROOT,
                   x_tr_tip: float = X_TR_WING_TIP,
                   n_strips: int = N_WING_STRIPS) -> Component:
    """Exposed wing, integrated strip by strip.

    Each strip carries its own chord, hence its own Reynolds number, and its
    own transition location interpolated linearly in eta = 2y/b between the
    root and tip values. The area-weighted mean friction coefficient and the
    area-weighted mean transition are reported back.

    The root region inside the fuselage is NOT counted: the exposed wing runs
    from the fuselage side (y = max_diameter/2) to the tip. The fuselage's own
    wetted area is not reduced by the wing carry-through in exchange, which
    is the standard convention and slightly conservative.
    """
    g = derive_wing(design.wing)
    y0 = design.fuselage.max_diameter_m / 2.0 if design.fuselage else 0.0
    y1 = g.span_m / 2.0
    lam = design.wing.taper_ratio
    per = airfoil_perimeter_ratio(design.wing.airfoil)

    edges = np.linspace(y0, y1, n_strips + 1)
    yc = 0.5 * (edges[:-1] + edges[1:])
    eta = 2.0 * yc / g.span_m
    chord = g.chord_root_m * (1.0 - (1.0 - lam) * eta)
    dy = np.diff(edges)
    # x2: port and starboard. per * chord = arc length of the section there.
    ds_wet = 2.0 * per * chord * dy
    x_tr = x_tr_root + (x_tr_tip - x_tr_root) * eta
    re = chord * flow.reynolds_per_m
    cf = np.array([cf_mixed(r, x, l) for r, x, l in zip(re, x_tr, chord)])

    s_wet = float(np.sum(ds_wet))
    cf_eff = float(np.sum(cf * ds_wet) / s_wet)
    x_tr_eff = float(np.sum(x_tr * ds_wet) / s_wet)
    t_c = airfoil_thickness(design.wing.airfoil)
    ff = form_factor_airfoil(t_c, airfoil_max_thickness_x(design.wing.airfoil),
                             flow.mach, math.radians(design.wing.sweep_le_deg))
    return Component.flat_plate(
        "wing", s_wet=s_wet, cf=cf_eff, ff=ff, q=Q_WING, s_ref=g.area_m2,
        length=g.mac_m, re=g.mac_m * flow.reynolds_per_m,
        laminar_fraction=x_tr_eff,
        note=f"{n_strips} strips, exposed from y={y0:.3f} m; "
             f"section arc {per:.4f} c, t/c {t_c:.4f} at x/c "
             f"{airfoil_max_thickness_x(design.wing.airfoil):.3f}")


def fuselage_wetted_area(design) -> float:
    """Wetted area of the station loft, as an exact sum of truncated-cone
    lateral areas pi*(r1+r2)*slant. The stations are (x_frac, r_frac) pairs
    and the loft between them is taken as linear -- the CAD lofts them with a
    spline, a difference of well under a percent on a body this smooth.

    The blunt nose disc (r/R = 0.15 at x = 0) is added as a flat cap. The aft
    station does not close either (r/R = 0.34); that base is NOT added as
    wetted area -- base drag is a pressure term, not a friction term, and it
    is one of the items the module docstring lists as missing.
    """
    L = design.fuselage.length_m
    R = design.fuselage.max_diameter_m / 2.0
    st = [(x * L, r * R) for x, r in design.fuselage.stations]
    s = math.pi * st[0][1] ** 2                       # nose cap
    for (x1, r1), (x2, r2) in zip(st[:-1], st[1:]):
        s += math.pi * (r1 + r2) * math.hypot(x2 - x1, r2 - r1)
    return s


def fuselage_component(design, flow: FlowCondition,
                       x_tr: float = X_TR_FUSELAGE) -> Component:
    g = derive_wing(design.wing)
    L = design.fuselage.length_m
    fineness = L / design.fuselage.max_diameter_m
    s_wet = fuselage_wetted_area(design)
    re = L * flow.reynolds_per_m
    return Component.flat_plate(
        "fuselage", s_wet=s_wet, cf=cf_mixed(re, x_tr, L),
        ff=form_factor_body(fineness), q=Q_FUSELAGE, s_ref=g.area_m2,
        length=L, re=re, laminar_fraction=x_tr,
        note=f"fineness {fineness:.2f}, {len(design.fuselage.stations)} loft "
             f"stations, Raymer body FF")


def boom_component(design, flow: FlowCondition,
                   x_tr: float = X_TR_BOOM) -> Component:
    """Both tail booms: plain cylinders of the derived length.

    No deduction is made for the length buried in the wing, nor are the end
    discs added. MEASURED, not asserted: the joint lets the top 19.5 mm of the
    90 mm boom into the wing (burial half-angle 55.5 deg, so 30.8% of the
    circumference) over the local wing chord of ~0.55 m, which is 0.0964 m2 =
    4.68% of the boom wetted area. The two end discs are 0.0127 m2 = 0.62%.
    They are therefore NOT of similar size -- the net is about -4% of boom
    friction, i.e. -0.00009 in C_D0, which is why it is still ignored.

    Separately, and NOT ignorable at the same level: the aft end disc is a
    BASE, and Hoerner ch. 13 gives a blunt base C_D of order 0.1-0.2 on its
    own area. At 0.15 that is +0.00049 in C_D0 for the pair -- a third of the
    booms' entire friction contribution. Like the fuselage base it is a
    pressure term this friction build-up does not carry; see the module
    docstring.
    """
    g = derive_wing(design.wing)
    bg = derive_booms(design)
    d = design.booms.diameter_m
    s_wet = 2.0 * math.pi * d * bg.length_m
    re = bg.length_m * flow.reynolds_per_m
    fineness = bg.length_m / d
    return Component.flat_plate(
        "booms", s_wet=s_wet, cf=cf_mixed(re, x_tr, bg.length_m),
        ff=form_factor_body(fineness), q=Q_BOOM, s_ref=g.area_m2,
        length=bg.length_m, re=re, laminar_fraction=x_tr,
        note=f"2 x {bg.length_m:.4f} m x {d * 1e3:.0f} mm, fineness "
             f"{fineness:.1f}, Hoerner slender-body FF")


def tail_component(design, flow: FlowCondition,
                   x_tr: float = X_TR_TAIL) -> Component:
    """Both panels of the inverted-V tail, both surfaces.

    derive_tail_panel converts design.tail.area_h_m2 into the true panel area
    as S_h / (2 cos^2 gamma). Note the cos^2: that identity means area_h_m2 is
    the EQUIVALENT (effective) horizontal tail area of the V -- the quantity a
    tail-volume coefficient is written in -- and NOT the geometric projection
    of the panels onto the horizontal plane, which would be 2 A cos gamma and
    would give A = S_h / (2 cos gamma) instead. The distinction is worth 1.139
    vs 0.847 m2 of wetted area here (dC_D0 0.00040), so it matters; the
    effective-area reading is the correct one for a V-tail sized by volume
    coefficient, and it is the convention derive_tail_panel and the CAD share.
    Either way, using S_h itself as a wetted area would be badly wrong.
    """
    g = derive_wing(design.wing)
    tp = derive_tail_panel(design)
    per = airfoil_perimeter_ratio(design.tail.airfoil)
    s_wet = per * 2.0 * tp.panel_area_m2
    re = tp.mac_m * flow.reynolds_per_m
    t_c = airfoil_thickness(design.tail.airfoil)
    ff = form_factor_airfoil(t_c, airfoil_max_thickness_x(design.tail.airfoil),
                             flow.mach)
    return Component.flat_plate(
        "tail", s_wet=s_wet, cf=cf_mixed(re, x_tr, tp.mac_m), ff=ff, q=Q_TAIL,
        s_ref=g.area_m2, length=tp.mac_m, re=re, laminar_fraction=x_tr,
        note=f"2 panels x {tp.panel_area_m2:.4f} m2 true area (projected S_h "
             f"{design.tail.area_h_m2:.3f} m2), {design.tail.airfoil}")


def misc_component(clean_drag_area_m2: float, s_ref_m2: float,
                   fraction: float = MISC_EXCRESCENCE_FRACTION) -> Component:
    return Component(
        name="miscellaneous", drag_area_m2=fraction * clean_drag_area_m2,
        s_ref_m2=s_ref_m2,
        note=f"{100 * fraction:.0f}% of the clean sum: leakage, protuberances, "
             f"antennas, control-surface gaps. Excludes payload installation, "
             f"cooling drag, base drag and gear.")


# ---------------------------------------------------------------------------
# the build-up
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DragBuildup:
    components: tuple[Component, ...]
    s_ref_m2: float
    flow: FlowCondition

    @property
    def drag_area_m2(self) -> float:
        return sum(c.drag_area_m2 for c in self.components)

    @property
    def cd0(self) -> float:
        return self.drag_area_m2 / self.s_ref_m2

    @property
    def wetted_area_m2(self) -> float:
        return sum(c.wetted_area_m2 or 0.0 for c in self.components)

    def component(self, name: str) -> Component:
        for c in self.components:
            if c.name == name:
                return c
        raise KeyError(f"no component {name!r} in {[c.name for c in self.components]}")

    def table(self) -> str:
        hdr = (f"{'component':<14}{'S_wet':>8}{'Re':>11}{'x_tr':>7}{'C_f':>9}"
               f"{'FF':>7}{'Q':>6}{'f=CfFFQS':>10}{'C_D0':>9}{'%':>7}")
        lines = [hdr, "-" * len(hdr)]
        for c in self.components:
            g = lambda v, f: format(v, f) if v is not None else ""
            lines.append(
                f"{c.name:<14}{g(c.wetted_area_m2, '8.4f')}{g(c.reynolds, '11.3e')}"
                f"{g(c.laminar_fraction, '7.3f')}{g(c.cf, '9.5f')}"
                f"{g(c.form_factor, '7.3f')}{g(c.interference_factor, '6.2f')}"
                f"{c.drag_area_m2:10.5f}{c.cd0:9.5f}"
                f"{100 * c.drag_area_m2 / self.drag_area_m2:7.1f}")
        lines.append("-" * len(hdr))
        lines.append(f"{'TOTAL':<14}{self.wetted_area_m2:8.4f}"
                     f"{'':11}{'':7}{'':9}{'':7}{'':6}"
                     f"{self.drag_area_m2:10.5f}{self.cd0:9.5f}{100.0:7.1f}")
        lines.append(f"S_ref {self.s_ref_m2:.4f} m2, S_wet/S_ref "
                     f"{self.wetted_area_m2 / self.s_ref_m2:.2f}, "
                     f"V {self.flow.velocity_ms:.2f} m/s at "
                     f"{self.flow.altitude_m:.0f} m, M {self.flow.mach:.3f}, "
                     f"Re/m {self.flow.reynolds_per_m:.3e}")
        return "\n".join(lines)


def parasite_buildup(design, flow: FlowCondition | None = None, *,
                     x_tr_wing: tuple[float, float] = (X_TR_WING_ROOT, X_TR_WING_TIP),
                     x_tr_fuselage: float = X_TR_FUSELAGE,
                     x_tr_boom: float = X_TR_BOOM,
                     x_tr_tail: float = X_TR_TAIL,
                     misc_fraction: float = MISC_EXCRESCENCE_FRACTION,
                     n_wing_strips: int = N_WING_STRIPS) -> DragBuildup:
    """Full component build-up for a loaded Design.

    `flow` defaults to the design's own loiter condition. Components whose
    geometry block is absent from the design file are skipped rather than
    guessed at.
    """
    if flow is None:
        flow = loiter_flow(design)
    s_ref = derive_wing(design.wing).area_m2
    comps = [wing_component(design, flow, x_tr_wing[0], x_tr_wing[1], n_wing_strips)]
    if design.fuselage is not None:
        comps.append(fuselage_component(design, flow, x_tr_fuselage))
    if design.booms is not None:
        comps.append(boom_component(design, flow, x_tr_boom))
    if design.tail is not None:
        comps.append(tail_component(design, flow, x_tr_tail))
    comps.append(misc_component(sum(c.drag_area_m2 for c in comps), s_ref,
                                misc_fraction))
    return DragBuildup(tuple(comps), s_ref, flow)
