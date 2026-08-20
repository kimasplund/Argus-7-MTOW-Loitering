"""Blade-element momentum theory propeller model for ARGUS-7.

WHAT THIS MODULE IS FOR
-----------------------
Two jobs, and the second one is the reason it exists.

1. A working BEMT solver: given a blade (diameter, blade count, chord and
   twist distributions), an rpm, an airspeed and an air density, return
   thrust, torque, power and the coefficients C_T, C_P, C_Q, the advance
   ratio J and the propulsive efficiency eta. Prandtl tip loss included.
   Section lift and drag come from NeuralFoil, through
   ``argus7.aero.neural`` when that module is importable, so the propeller
   sees the same 2D aerodynamics as the rest of the stack.

2. Exposing the fact that THE BASELINE PROPULSION SET DOES NOT CLOSE.
   design/argus7_v1.yaml specifies a 0.813 m propeller turning 2100 rpm and
   an engine rated 17 kW. Those three numbers are mutually inconsistent:

       C_P = P / (rho n^3 D^5) = 17000 / (1.225 * 35^3 * 0.813^5) = 0.911

   and 0.911 is not a propeller power coefficient. A conventional two- or
   three-blade propeller tops out near C_P = 0.25 (see
   ``PRACTICAL_CP_CEILING``), which for this disc at this rpm is about
   4.66 kW. Loiter needs roughly 3.4 kW of shaft power and is fine. Climb
   and takeoff are not fine: the propeller is the limit, not the engine.

   ``power_absorbed`` and ``max_power_absorbed`` measure this with the
   blade-element model rather than asserting it, and ``close_propulsion``
   returns the two ways out: a larger diameter (~1.05 m at 2100 rpm) or a
   higher propeller rpm at the diameter as drawn (~3230 rpm, i.e. a
   reduction ratio near 1.5 rather than 2.3).

   Note what the 1.05 m closure collides with -- see
   ``PropulsionClosure.tip_to_boom_clearance_m``. It is reported, not hidden.

FORMULATION
-----------
Standard BEMT with separate axial and tangential induction, solved as a
one-dimensional root find on the local inflow angle phi (Ning's residual
form, which is far more robust than iterating on the induction factors).
With sigma' = B c / (2 pi r), Cn = Cl cos phi - Cd sin phi and
Ct = Cl sin phi + Cd cos phi:

    k  = sigma' Cn / (4 F sin^2 phi)          axial,      a  = k / (1 - k)
    k' = sigma' Ct / (4 F sin phi cos phi)    tangential, a' = k' / (1 + k')
    W_a = V (1 + a) = V / (1 - k)
    W_t = Omega r (1 - a') = Omega r / (1 + k')
    residual(phi) = sin(phi) W_t - cos(phi) W_a          -> 0

The static case V = 0 is a genuinely different limit, not a small number:
W_a = V / (1 - k) collapses and the residual above has no root. There the
axial momentum balance degenerates to k = 1 (thrust is set by the induced
velocity alone), so the residual becomes

    residual_static(phi) = 4 F sin^2 phi - sigma' Cn     -> 0

and the swirl equation then fixes the magnitude via W_t = Omega r / (1 + k'),
W_a = W_t tan(phi). Both branches are solved by the same bracketed
scan-then-bisect, vectorised over radial stations and over whole parameter
sweeps at once.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import numpy as np

__all__ = [
    "RHO_SEA_LEVEL",
    "MU_SEA_LEVEL",
    "SPEED_OF_SOUND_SEA_LEVEL",
    "PRACTICAL_CP_CEILING",
    "BladeGeometry",
    "BEMTResult",
    "AbsorptionPoint",
    "PropulsionClosure",
    "constant_pitch_blade",
    "activity_factor",
    "run_bemt",
    "required_cp",
    "power_absorbed",
    "max_power_absorbed",
    "close_propulsion",
    "baseline_finding_report",
    "section_cl_cd",
    "SECTION_POLAR_SOURCE",
]

REPO = Path(__file__).resolve().parents[2]
DEFAULT_DESIGN = REPO / "design" / "argus7_v1.yaml"

# --- Atmosphere -------------------------------------------------------------
# ISA sea level. Density and viscosity are ARGUMENTS everywhere in the public
# API; these are only the defaults used when a caller does not supply one, and
# the sea-level values are the right defaults because the propulsion closure
# question is a takeoff/climb question.
RHO_SEA_LEVEL = 1.225                 # kg/m^3, ISA sea level
MU_SEA_LEVEL = 1.789e-5               # Pa.s, ISA sea level dynamic viscosity
SPEED_OF_SOUND_SEA_LEVEL = 340.29     # m/s, ISA sea level

# --- The power-coefficient ceiling ------------------------------------------
# PRACTICAL_CP_CEILING is the single most load-bearing assumption in this
# module, so it is stated once, here, and used by name everywhere.
#
# C_P = P / (rho n^3 D^5). Real light-aircraft propellers cruise around
# C_P = 0.05-0.10 (worked example: 134 kW into a 1.88 m two-blade at 2700 rpm
# gives C_P = 0.051). C_P rises with blade angle and blade count, and a
# high-pitch constant-speed two- or three-blade propeller working at high
# advance ratio reaches roughly 0.2-0.3 before blade stall and the sheer
# solidity limit stop it. 0.25 is therefore a GENEROUS design ceiling for a
# conventional 2-3 blade propeller, not a typical operating value -- chosen
# generous on purpose, because it is being used to condemn a design and the
# finding must survive the most favourable assumption available.
#
# ``max_power_absorbed`` measures the blade-element model's own ceiling for a
# given disc and can be compared against this constant; the two agree to
# within about a factor of two, which is the accuracy this claim needs (the
# baseline is short by a factor of ~3.6 in power).
PRACTICAL_CP_CEILING = 0.25

# --- Blade section ----------------------------------------------------------
# Clark Y is the classic propeller section. It is not in data/airfoils (that
# directory holds only the wing's FX 63-137), and adding a data file is
# outside this module's remit, so the blade uses NACA 4412 as a stand-in:
# 4% camber / 12% thick against Clark Y's 3.55% / 11.7%. Section drag and the
# stall angle are close enough that no conclusion here turns on the
# difference -- the propulsion finding is a factor-of-3.6 result.
DEFAULT_BLADE_AIRFOIL = "4412"

# Default chord distribution, c/R against r/R. This is an ASSUMPTION: the
# report specifies a propeller diameter and rpm and nothing about the blade.
# The shape below is a generic light-aircraft two-blade planform -- maximum
# width just inboard of mid-span, rounded tip -- scaled so that the activity
# factor per blade comes out near 95, which is mid-range for general-aviation
# propellers (typical 90-110). ``activity_factor`` recomputes it, and
# tests/test_bemt.py asserts it stays in that band, so this table cannot
# silently drift into being a non-propeller.
DEFAULT_CHORD_TABLE_X = np.array(
    [0.15, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95, 1.00])
DEFAULT_CHORD_TABLE_C = np.array(
    [0.140, 0.154, 0.179, 0.190, 0.189, 0.179, 0.164, 0.141, 0.106, 0.077,
     0.017])

DEFAULT_HUB_R_OVER_R = 0.15   # spinner/root cutout, typical for this class
DEFAULT_N_SECTIONS = 24       # midpoint-rule stations; 24 converges C_P to <0.5%

# --- Section polar handling -------------------------------------------------
# NeuralFoil is trained on attached-flow polars and its own
# analysis_confidence collapses outside roughly -10 to +18 degrees (measured:
# confidence 0.99 at 5 deg, 0.96 at 18 deg, 0.93 at 20 deg, 0.01 at 25 deg).
# Propeller inner sections at low advance ratio sit far outside that, so
# beyond the trusted band the polar is blended into a flat-plate model over
# BLEND_DEG degrees. CD_FLAT_PLATE = 2.0 is the standard fully separated
# normal-force coefficient used in Viterna-type post-stall extensions.
ALPHA_TRUST_LO_DEG = -10.0
ALPHA_TRUST_HI_DEG = 18.0
BLEND_DEG = 12.0
CD_FLAT_PLATE = 2.0
CD_FLAT_PLATE_MIN = 0.02

# Polar lookup table resolution. The table is built once per airfoil by
# evaluating the neural surrogate on this grid; every BEMT query is then a
# bilinear interpolation. At 0.25 deg in alpha the interpolation error is far
# below the surrogate's own error, and it makes a full pitch x advance-ratio
# sweep cost milliseconds instead of minutes.
TABLE_ALPHA_DEG = np.arange(-90.0, 90.0 + 1e-9, 0.25)
TABLE_RE = np.geomspace(2.0e4, 1.0e7, 25)

# --- Solver settings --------------------------------------------------------
PHI_MIN_RAD = math.radians(0.15)
PHI_MAX_RAD = math.radians(89.5)
N_PHI_GRID = 72        # bracketing scan resolution
N_BISECT = 44          # bisection refinement steps (phi to ~1e-12 rad)
V_STATIC_EPS = 1e-6    # below this airspeed the static branch is used
F_MIN = 1e-4           # tip-loss floor, keeps 1/F finite at the tip
MACH_MAX_PG = 0.70     # Prandtl-Glauert is nonsense above this

# --- Operating envelope used when searching for maximum absorbed power ------
# The propeller only absorbs power at flight conditions the aircraft can
# actually reach, so the advance-ratio sweep is capped by the airframe.
# 128 km/h = 35.6 m/s is the top of the report's loiter TAS band (99-128
# km/h); DASH_FACTOR 1.4 allows a dash/descent well above loiter. Anything
# faster is not a condition this aircraft flies, and allowing it would only
# make the propeller look better than it is.
MAX_LOITER_TAS_MS = 128.0 / 3.6
DASH_FACTOR = 1.4
V_MAX_ENVELOPE_MS = MAX_LOITER_TAS_MS * DASH_FACTOR      # 49.8 m/s

# Sweep ranges for max_power_absorbed. pitch/D up to 2.0 corresponds to a
# blade angle at 0.75R of atan(2.0 / (pi*0.75)) = 40 deg, about the coarsest
# any constant-speed propeller runs in normal (non-feathered) operation.
# Blade count 2-3 is what fits this class; 4 blades at 0.8 m diameter would
# need a chord no real blade has and is not offered as an escape hatch.
PITCH_OVER_D_SWEEP = np.linspace(0.30, 2.00, 18)
BLADE_COUNT_SWEEP = (2, 3)
J_SWEEP_POINTS = 16


# ===========================================================================
# Section aerodynamics
# ===========================================================================

SECTION_POLAR_SOURCE = "unresolved"


def _neural_polar():
    """Return a callable (coords, alpha_deg, Re) -> (CL, CD).

    Prefers argus7.aero.neural, the project's batched NeuralFoil surrogate,
    so the propeller sections use exactly the same 2D aerodynamics as the
    wing. Falls back to calling NeuralFoil directly -- same network, same
    weights -- if that module is not importable, which keeps this module
    usable standalone. Which path was taken is recorded in
    SECTION_POLAR_SOURCE.
    """
    global SECTION_POLAR_SOURCE
    try:
        from argus7.aero.neural import polar as _polar   # type: ignore

        def call(coords, alpha_deg, re):
            r = _polar(coords, alpha=alpha_deg, Re=re)
            return np.asarray(r.CL, dtype=float), np.asarray(r.CD, dtype=float)

        # Probe it; if the sibling module's signature is not what we expect
        # we quietly use NeuralFoil directly rather than failing the build.
        call(_blade_coords(DEFAULT_BLADE_AIRFOIL), np.zeros(2), np.full(2, 3e5))
        SECTION_POLAR_SOURCE = "argus7.aero.neural"
        return call
    except Exception:
        import neuralfoil as nf

        def call(coords, alpha_deg, re):
            r = nf.get_aero_from_coordinates(
                coordinates=coords, alpha=alpha_deg, Re=re, model_size="xlarge")
            return np.asarray(r["CL"], dtype=float), np.asarray(r["CD"], dtype=float)

        SECTION_POLAR_SOURCE = "neuralfoil"
        return call


@lru_cache(maxsize=8)
def _blade_coords(airfoil: str) -> np.ndarray:
    """Blade section coordinates, Selig order, via the project's loaders."""
    from argus7.cad.airfoil_coords import load_airfoil, naca4

    if airfoil.isdigit() and len(airfoil) == 4:
        return naca4(airfoil)
    return load_airfoil(airfoil)


def _post_stall(alpha_rad: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Flat-plate lift and drag, used beyond the surrogate's trusted band."""
    cl = 0.5 * CD_FLAT_PLATE * np.sin(2.0 * alpha_rad)
    cd = CD_FLAT_PLATE * np.sin(alpha_rad) ** 2 + CD_FLAT_PLATE_MIN
    return cl, cd


@lru_cache(maxsize=4)
def _polar_table(airfoil: str) -> tuple[np.ndarray, np.ndarray]:
    """(CL, CD) on the TABLE_ALPHA_DEG x TABLE_RE grid, blended post-stall.

    One neural evaluation builds the whole table; everything downstream
    interpolates it.
    """
    coords = _blade_coords(airfoil)
    call = _neural_polar()

    a = TABLE_ALPHA_DEG[:, None] * np.ones_like(TABLE_RE)[None, :]
    re = np.ones_like(TABLE_ALPHA_DEG)[:, None] * TABLE_RE[None, :]

    a_query = np.clip(a, ALPHA_TRUST_LO_DEG, ALPHA_TRUST_HI_DEG)
    cl_nf, cd_nf = call(coords, a_query.ravel(), re.ravel())
    cl_nf = cl_nf.reshape(a.shape)
    cd_nf = cd_nf.reshape(a.shape)

    cl_fp, cd_fp = _post_stall(np.radians(a))

    # Blend weight: 0 inside the trusted band, 1 once BLEND_DEG past it.
    over = np.maximum(a - ALPHA_TRUST_HI_DEG, ALPHA_TRUST_LO_DEG - a)
    w = np.clip(over / BLEND_DEG, 0.0, 1.0)
    cl = (1.0 - w) * cl_nf + w * cl_fp
    cd = (1.0 - w) * cd_nf + w * cd_fp
    return cl, cd


def section_cl_cd(alpha_rad, re, airfoil: str = DEFAULT_BLADE_AIRFOIL,
                  mach=None):
    """2D section lift and drag coefficients, bilinear in (alpha, log Re).

    Optionally applies a Prandtl-Glauert compressibility correction to CL if
    ``mach`` is supplied. Vectorised; shapes broadcast.
    """
    cl_t, cd_t = _polar_table(airfoil)
    a = np.clip(np.degrees(np.asarray(alpha_rad, dtype=float)),
                TABLE_ALPHA_DEG[0], TABLE_ALPHA_DEG[-1])
    r = np.clip(np.asarray(re, dtype=float), TABLE_RE[0], TABLE_RE[-1])

    da = TABLE_ALPHA_DEG[1] - TABLE_ALPHA_DEG[0]
    ia = np.clip(((a - TABLE_ALPHA_DEG[0]) / da).astype(np.int64),
                 0, len(TABLE_ALPHA_DEG) - 2)
    fa = (a - TABLE_ALPHA_DEG[ia]) / da

    lr = np.log(r)
    lgrid = np.log(TABLE_RE)
    ir = np.clip(np.searchsorted(lgrid, lr) - 1, 0, len(TABLE_RE) - 2)
    fr = (lr - lgrid[ir]) / (lgrid[ir + 1] - lgrid[ir])

    def bilinear(t):
        return ((1 - fa) * (1 - fr) * t[ia, ir]
                + fa * (1 - fr) * t[ia + 1, ir]
                + (1 - fa) * fr * t[ia, ir + 1]
                + fa * fr * t[ia + 1, ir + 1])

    cl = bilinear(cl_t)
    cd = bilinear(cd_t)

    if mach is not None:
        m = np.clip(np.asarray(mach, dtype=float), 0.0, MACH_MAX_PG)
        cl = cl / np.sqrt(1.0 - m ** 2)
    return cl, cd


# ===========================================================================
# Blade geometry
# ===========================================================================

@dataclass(frozen=True)
class BladeGeometry:
    """A propeller blade, everything in SI or non-dimensional radius."""
    diameter_m: float
    blades: int
    r_over_R: np.ndarray          # (nsec,) midpoint stations
    chord_over_R: np.ndarray      # (nsec,)
    twist_rad: np.ndarray         # (nsec,) blade angle from the plane of rotation
    hub_r_over_R: float = DEFAULT_HUB_R_OVER_R
    airfoil: str = DEFAULT_BLADE_AIRFOIL
    pitch_m: float | None = None  # set when built by constant_pitch_blade

    @property
    def radius_m(self) -> float:
        return 0.5 * self.diameter_m

    @property
    def pitch_over_d(self) -> float:
        return float("nan") if self.pitch_m is None else self.pitch_m / self.diameter_m


def _stations(hub: float, n: int) -> np.ndarray:
    """Midpoint-rule stations between the hub cutout and the tip.

    Midpoints, not endpoints: the tip station must not land exactly on
    r = R where the Prandtl factor is identically zero.
    """
    edges = np.linspace(hub, 1.0, n + 1)
    return 0.5 * (edges[:-1] + edges[1:])


def constant_pitch_blade(diameter: float, pitch: float, blades: int = 2,
                         n_sections: int = DEFAULT_N_SECTIONS,
                         hub_r_over_R: float = DEFAULT_HUB_R_OVER_R,
                         airfoil: str = DEFAULT_BLADE_AIRFOIL) -> BladeGeometry:
    """Blade of constant geometric pitch ``pitch`` (metres advance per rev).

    theta(r) = atan(pitch / (2 pi r)), the classical definition behind a
    "20 x 10" propeller designation. Chord follows DEFAULT_CHORD_TABLE.
    """
    if diameter <= 0.0:
        raise ValueError("diameter must be positive")
    if pitch <= 0.0:
        raise ValueError("pitch must be positive")
    if blades < 1:
        raise ValueError("blades must be >= 1")
    x = _stations(hub_r_over_R, n_sections)
    c = np.interp(x, DEFAULT_CHORD_TABLE_X, DEFAULT_CHORD_TABLE_C)
    r = x * 0.5 * diameter
    theta = np.arctan2(pitch, 2.0 * math.pi * r)
    return BladeGeometry(diameter_m=float(diameter), blades=int(blades),
                         r_over_R=x, chord_over_R=c, twist_rad=theta,
                         hub_r_over_R=float(hub_r_over_R), airfoil=airfoil,
                         pitch_m=float(pitch))


def activity_factor(blade: BladeGeometry) -> float:
    """Activity factor per blade, AF = (100000/16) * int (c/D) x^3 dx.

    Integrated from the hub cutout to the tip. General-aviation propellers
    run AF ~90-110 per blade; this is the check that the assumed planform is
    a real propeller and not an arbitrary shape.
    """
    x = np.linspace(blade.hub_r_over_R, 1.0, 400)
    c_over_d = 0.5 * np.interp(x, DEFAULT_CHORD_TABLE_X, DEFAULT_CHORD_TABLE_C)
    return float(100000.0 / 16.0 * np.trapezoid(c_over_d * x ** 3, x))


# ===========================================================================
# The solver
# ===========================================================================

@dataclass
class BEMTResult:
    thrust_n: float
    torque_nm: float
    power_w: float
    ct: float
    cp: float
    cq: float
    j: float
    eta: float
    converged: bool
    rpm: float
    v_ms: float
    rho: float
    diameter_m: float
    blades: int
    tip_mach: float
    phi_rad: np.ndarray = field(repr=False, default_factory=lambda: np.array([]))
    alpha_rad: np.ndarray = field(repr=False, default_factory=lambda: np.array([]))
    cl: np.ndarray = field(repr=False, default_factory=lambda: np.array([]))
    cd: np.ndarray = field(repr=False, default_factory=lambda: np.array([]))
    tip_loss_factor: np.ndarray = field(repr=False,
                                        default_factory=lambda: np.array([]))
    reynolds: np.ndarray = field(repr=False, default_factory=lambda: np.array([]))


def _residual(phi, *, theta, sigma_p, r, radius, omega, v, re, mach, blades,
              airfoil, tip_loss, compressibility, static):
    """Signed residual whose root is the local inflow angle.

    Sign convention, both branches: negative means phi is too small.
    """
    sp = np.sin(phi)
    cp_ = np.cos(phi)
    alpha = theta - phi
    cl, cd = section_cl_cd(alpha, re, airfoil,
                           mach=mach if compressibility else None)

    if tip_loss:
        f = blades * (radius - r) / (2.0 * r * np.maximum(sp, 1e-9))
        F = 2.0 / math.pi * np.arccos(np.exp(-np.clip(f, 0.0, 50.0)))
        F = np.maximum(F, F_MIN)
    else:
        F = np.ones_like(phi)

    cn = cl * cp_ - cd * sp
    ct = cl * sp + cd * cp_

    with np.errstate(divide="ignore", invalid="ignore"):
        k = sigma_p * cn / (4.0 * F * sp ** 2)
        kp = sigma_p * ct / (4.0 * F * sp * cp_)

    kp = np.maximum(kp, -0.99)                 # keep 1 + k' safely positive
    wt = omega * r / (1.0 + kp)

    res_static = 4.0 * F * sp ** 2 - sigma_p * cn

    with np.errstate(divide="ignore", invalid="ignore"):
        wa = v / (1.0 - k)
    res_dyn = sp * wt - cp_ * wa
    # k >= 1 is the over-loaded branch where axial momentum cannot supply the
    # blade's demand. Physically the solution lies at larger phi, so force the
    # residual negative there rather than letting it produce a spurious root.
    res_dyn = np.where(k >= 1.0, -np.inf, res_dyn)
    res_dyn = np.where(np.isfinite(res_dyn), res_dyn, -np.inf)

    res = np.where(static, res_static, res_dyn)
    return res, cl, cd, cn, ct, F, kp


def _solve(theta, sigma_p, r, radius, omega, v, re, mach, blades, airfoil,
           tip_loss, compressibility):
    """Bracketed scan then bisection on phi. Fully vectorised."""
    static = np.asarray(np.abs(v) <= V_STATIC_EPS)
    kw = dict(theta=theta, sigma_p=sigma_p, r=r, radius=radius, omega=omega,
              v=v, re=re, mach=mach, blades=blades, airfoil=airfoil,
              tip_loss=tip_loss, compressibility=compressibility, static=static)

    grid = np.linspace(PHI_MIN_RAD, PHI_MAX_RAD, N_PHI_GRID)
    shape = np.broadcast(theta, sigma_p, r, omega, v, re).shape
    phis = grid.reshape((-1,) + (1,) * len(shape))
    res, *_ = _residual(np.broadcast_to(phis, (N_PHI_GRID,) + shape).copy(), **kw)

    neg = res <= 0.0
    cross = neg[:-1] & (~neg[1:])                 # first negative -> positive
    found = cross.any(axis=0)
    idx = np.argmax(cross, axis=0)
    lo = grid[idx]
    hi = grid[np.minimum(idx + 1, N_PHI_GRID - 1)]
    # Where no bracket exists the section is not solvable; park it at the
    # grid point of least residual and report non-convergence.
    fallback = grid[np.argmin(np.abs(res), axis=0)]
    lo = np.where(found, lo, fallback)
    hi = np.where(found, hi, fallback)

    for _ in range(N_BISECT):
        mid = 0.5 * (lo + hi)
        rmid, *_ = _residual(mid, **kw)
        take_lo = rmid <= 0.0
        lo = np.where(take_lo, mid, lo)
        hi = np.where(take_lo, hi, mid)

    phi = 0.5 * (lo + hi)
    _, cl, cd, cn, ct, F, kp = _residual(phi, **kw)
    return phi, cl, cd, cn, ct, F, kp, found


def _bemt_core(*, r_over_R, chord_over_R, theta, blades, diameter, hub,
               omega, v, rho, mu, airfoil, tip_loss, compressibility,
               sound_speed):
    """Batched core. All arrays broadcast against a trailing section axis."""
    radius = 0.5 * diameter
    r = r_over_R * radius
    c = chord_over_R * radius
    sigma_p = blades * c / (2.0 * math.pi * r)

    # Reynolds and Mach use the geometric resultant sqrt(V^2 + (Omega r)^2)
    # rather than the induced W. That decouples the polar lookup from the
    # unknown, which is what makes the residual a clean function of phi. The
    # two differ by a few percent, and section drag depends on Re only
    # logarithmically, so nothing measurable is lost.
    w_ref = np.hypot(v, omega * r)
    re = rho * w_ref * c / mu
    mach = w_ref / sound_speed

    phi, cl, cd, cn, ct, F, kp, found = _solve(
        theta, sigma_p, r, radius, omega, v, re, mach, blades, airfoil,
        tip_loss, compressibility)

    wt = omega * r / (1.0 + kp)
    wa = wt * np.tan(phi)
    w2 = wa ** 2 + wt ** 2

    dr = (1.0 - hub) * radius / r_over_R.shape[-1]     # midpoint rule
    dT = 0.5 * rho * w2 * blades * c * cn
    dQ = 0.5 * rho * w2 * blades * c * ct * r
    thrust = np.sum(dT, axis=-1) * dr
    torque = np.sum(dQ, axis=-1) * dr
    return thrust, torque, phi, cl, cd, F, re, np.all(found, axis=-1), mach


def run_bemt(blade: BladeGeometry, rpm: float, v_ms: float,
             rho: float = RHO_SEA_LEVEL, mu: float = MU_SEA_LEVEL,
             tip_loss: bool = True, compressibility: bool = True,
             sound_speed: float = SPEED_OF_SOUND_SEA_LEVEL) -> BEMTResult:
    """Solve one operating point.

    Parameters are SI: rpm in rev/min, v_ms in m/s, rho in kg/m^3.
    v_ms = 0 selects the static branch (see the module docstring).
    """
    if rpm <= 0.0:
        raise ValueError("rpm must be positive")
    if rho <= 0.0:
        raise ValueError("rho must be positive")
    if v_ms < 0.0:
        raise ValueError("v_ms must be non-negative")

    n = rpm / 60.0
    omega = 2.0 * math.pi * n
    D = blade.diameter_m

    thrust, torque, phi, cl, cd, F, re, ok, mach = _bemt_core(
        r_over_R=blade.r_over_R, chord_over_R=blade.chord_over_R,
        theta=blade.twist_rad, blades=float(blade.blades), diameter=D,
        hub=blade.hub_r_over_R, omega=omega, v=float(v_ms), rho=rho, mu=mu,
        airfoil=blade.airfoil, tip_loss=tip_loss,
        compressibility=compressibility, sound_speed=sound_speed)

    thrust = float(thrust)
    torque = float(torque)
    power = torque * omega
    ct = thrust / (rho * n ** 2 * D ** 4)
    cq = torque / (rho * n ** 2 * D ** 5)
    cp = power / (rho * n ** 3 * D ** 5)
    j = v_ms / (n * D)
    eta = (ct * j / cp) if (cp > 0.0 and j > 0.0) else 0.0

    return BEMTResult(
        thrust_n=thrust, torque_nm=torque, power_w=power, ct=ct, cp=cp, cq=cq,
        j=j, eta=eta, converged=bool(ok), rpm=float(rpm), v_ms=float(v_ms),
        rho=float(rho), diameter_m=D, blades=blade.blades,
        tip_mach=float(np.max(mach)), phi_rad=phi,
        alpha_rad=blade.twist_rad - phi, cl=cl, cd=cd, tip_loss_factor=F,
        reynolds=re)


# ===========================================================================
# The propulsion closure question
# ===========================================================================

def required_cp(power_w: float, rpm: float, rho: float, diameter: float) -> float:
    """C_P = P / (rho n^3 D^5): the power coefficient a design DEMANDS.

    This is pure definition, no aerodynamics. Compare it against
    PRACTICAL_CP_CEILING (or against max_power_absorbed) to find out whether
    a propeller could ever deliver it.
    """
    n = rpm / 60.0
    return power_w / (rho * n ** 3 * diameter ** 5)


def power_absorbed(diameter: float, rpm: float, rho: float, pitch: float,
                   v_ms: float = 0.0, blades: int = 2,
                   mu: float = MU_SEA_LEVEL) -> float:
    """Shaft power in watts that this propeller actually absorbs.

    ``pitch`` is the geometric pitch in METRES (advance per revolution), the
    classical propeller pitch. The default v_ms = 0 is the static/takeoff
    condition -- the one the ARGUS-7 baseline has to pass and does not.
    """
    blade = constant_pitch_blade(diameter, pitch, blades=blades)
    return run_bemt(blade, rpm=rpm, v_ms=v_ms, rho=rho, mu=mu).power_w


@dataclass
class AbsorptionPoint:
    """The best power-absorbing operating point found for a given disc."""
    power_w: float
    cp: float
    ct: float
    j: float
    v_ms: float
    pitch_over_d: float
    pitch_m: float
    blades: int
    thrust_n: float
    eta: float
    tip_mach: float


def max_power_absorbed(diameter: float, rpm: float, rho: float,
                       v_max_ms: float = V_MAX_ENVELOPE_MS,
                       mu: float = MU_SEA_LEVEL,
                       blade_counts=BLADE_COUNT_SWEEP,
                       pitch_over_d=PITCH_OVER_D_SWEEP,
                       ) -> tuple[float, AbsorptionPoint]:
    """Search pitch, blade count and advance ratio for maximum absorbed power.

    This is the measured counterpart to PRACTICAL_CP_CEILING: instead of
    asserting a ceiling it asks the blade-element model how much power this
    disc can be made to take at this rpm, over every blade a real propeller
    could plausibly be, at every speed the airframe can fly.

    The default ``pitch_over_d`` sweep stops at 2.0 because that is already
    the coarsest realistic blade. Widen it to stress-test the answer: the
    ARGUS-7 baseline still falls short of 17 kW at pitch/D = 4.0, a blade
    angle of 59 degrees at 0.75R that no propeller is built with.
    """
    best_w = -np.inf
    best: AbsorptionPoint | None = None
    speeds = np.linspace(0.0, v_max_ms, J_SWEEP_POINTS)

    for b in blade_counts:
        for pod in np.atleast_1d(np.asarray(pitch_over_d, dtype=float)):
            blade = constant_pitch_blade(diameter, pod * diameter, blades=b)
            for v in speeds:
                r = run_bemt(blade, rpm=rpm, v_ms=float(v), rho=rho, mu=mu)
                if not r.converged or r.power_w <= 0.0:
                    continue
                if r.power_w > best_w:
                    best_w = r.power_w
                    best = AbsorptionPoint(
                        power_w=r.power_w, cp=r.cp, ct=r.ct, j=r.j,
                        v_ms=float(v), pitch_over_d=float(pod),
                        pitch_m=float(pod * diameter), blades=int(b),
                        thrust_n=r.thrust_n, eta=r.eta, tip_mach=r.tip_mach)
    if best is None:
        raise RuntimeError("no converged operating point found")
    return float(best_w), best


@dataclass
class PropulsionClosure:
    """Both ways to close a propulsion set that does not close as drawn."""
    power_kw: float
    rpm: float
    rho: float
    cp_ceiling: float
    fixed_diameter_m: float
    required_cp_at_baseline: float
    baseline_closes: bool
    diameter_m: float                       # diameter that closes at this rpm
    rpm_at_fixed_diameter: float            # rpm that closes at this diameter
    reduction_ratio_at_fixed_diameter: float | None
    tip_speed_at_closing_diameter_ms: float
    tip_speed_at_closing_rpm_ms: float
    tip_to_boom_clearance_m: float | None


def close_propulsion(power_kw: float, rpm: float, rho: float = RHO_SEA_LEVEL,
                     diameter_m: float | None = None,
                     cp_ceiling: float = PRACTICAL_CP_CEILING,
                     design_path: str | Path = DEFAULT_DESIGN,
                     ) -> PropulsionClosure:
    """What it would take to make the propulsion set close.

    At a fixed power coefficient ceiling, D scales as P^(1/5) at fixed rpm,
    and n scales as P^(1/3) at fixed diameter, so:

        D_close = (P / (rho n^3 C_P))^(1/5)
        n_close = (P / (rho C_P D^5))^(1/3)

    ``diameter_m`` defaults to the propeller diameter in the design file --
    geometry is never hardcoded here.
    """
    if power_kw <= 0.0 or rpm <= 0.0 or rho <= 0.0 or cp_ceiling <= 0.0:
        raise ValueError("power, rpm, rho and cp_ceiling must be positive")

    design = None
    try:
        from argus7.design.schema import load_design
        design = load_design(design_path)
    except Exception:
        design = None

    if diameter_m is None:
        if design is None or design.propulsion is None:
            raise ValueError("diameter_m not given and the design file has none")
        diameter_m = float(design.propulsion.prop_diameter_m)

    p_w = power_kw * 1000.0
    n = rpm / 60.0

    cp_baseline = required_cp(p_w, rpm, rho, diameter_m)
    d_close = (p_w / (rho * n ** 3 * cp_ceiling)) ** 0.2
    n_close = (p_w / (rho * cp_ceiling * diameter_m ** 5)) ** (1.0 / 3.0)
    rpm_close = n_close * 60.0

    reduction = None
    if design is not None and design.propulsion is not None:
        engine_rpm = (design.propulsion.prop_rpm
                      * design.propulsion.reduction_ratio)
        reduction = engine_rpm / rpm_close

    # Does the bigger propeller still fit between the booms? derive_booms
    # gives the boom lateral station; the boom's inner surface is that minus
    # its radius. This is reported, not enforced -- it is part of the finding.
    clearance = None
    if design is not None and design.booms is not None:
        try:
            from argus7.design.geometry import derive_booms
            booms = derive_booms(design)
            inner = abs(booms.y_station_m) - 0.5 * design.booms.diameter_m
            clearance = float(inner - 0.5 * d_close)
        except Exception:
            clearance = None

    return PropulsionClosure(
        power_kw=float(power_kw), rpm=float(rpm), rho=float(rho),
        cp_ceiling=float(cp_ceiling), fixed_diameter_m=float(diameter_m),
        required_cp_at_baseline=float(cp_baseline),
        baseline_closes=bool(cp_baseline <= cp_ceiling),
        diameter_m=float(d_close), rpm_at_fixed_diameter=float(rpm_close),
        reduction_ratio_at_fixed_diameter=reduction,
        tip_speed_at_closing_diameter_ms=float(math.pi * d_close * n),
        tip_speed_at_closing_rpm_ms=float(math.pi * diameter_m * n_close),
        tip_to_boom_clearance_m=clearance)


def baseline_finding_report(design_path: str | Path = DEFAULT_DESIGN,
                            rho: float = RHO_SEA_LEVEL) -> str:
    """Human-readable statement of the baseline propulsion finding.

    Runs the blade-element model rather than quoting it. Printed by
    ``python -m argus7.prop.bemt``.
    """
    from argus7.design.schema import load_design

    d = load_design(design_path)
    p = d.propulsion
    D, rpm, kw = p.prop_diameter_m, p.prop_rpm, p.power_max_kw
    cp_needed = required_cp(kw * 1000.0, rpm, rho, D)
    ceiling_w = PRACTICAL_CP_CEILING * rho * (rpm / 60.0) ** 3 * D ** 5
    best_w, best = max_power_absorbed(D, rpm, rho)
    c = close_propulsion(kw, rpm, rho)

    lines = [
        "ARGUS-7 PROPULSION CLOSURE -- the baseline set does not close",
        "=" * 62,
        f"design file          : {Path(design_path).name}",
        f"section polar source : {SECTION_POLAR_SOURCE}",
        "",
        f"as drawn             : D = {D:.3f} m, {rpm:.0f} rpm, "
        f"{kw:.1f} kW rated, reduction {p.reduction_ratio:.2f}",
        f"C_P demanded         : {cp_needed:.3f}    "
        f"(= P / rho n^3 D^5 at rho = {rho:.3f})",
        f"practical C_P ceiling: {PRACTICAL_CP_CEILING:.3f}    "
        f"-> {ceiling_w / 1000.0:.2f} kW absorbable",
        f"BEMT best C_P found  : {best.cp:.3f}    "
        f"({best.blades} blades, pitch/D {best.pitch_over_d:.2f}, "
        f"J {best.j:.2f}, V {best.v_ms:.1f} m/s)",
        f"BEMT best power      : {best_w / 1000.0:.2f} kW  "
        f"-- short of rated by a factor of {kw * 1000.0 / best_w:.1f}",
        "",
        "Loiter (~3.4 kW shaft) is inside this. Climb and takeoff are not:",
        "the propeller, not the engine, is the limit.",
        "",
        "TWO CLOSURES",
        f"  1. diameter    : {c.diameter_m:.3f} m at {rpm:.0f} rpm "
        f"(tip speed {c.tip_speed_at_closing_diameter_ms:.0f} m/s)",
    ]
    if c.tip_to_boom_clearance_m is not None:
        lines.append(
            f"     WARNING     : that leaves only "
            f"{c.tip_to_boom_clearance_m * 1000.0:.0f} mm between the prop tip "
            f"and the boom inner surface")
    lines += [
        f"  2. rpm         : {c.rpm_at_fixed_diameter:.0f} rpm at D = "
        f"{c.fixed_diameter_m:.3f} m (tip speed "
        f"{c.tip_speed_at_closing_rpm_ms:.0f} m/s)",
    ]
    if c.reduction_ratio_at_fixed_diameter is not None:
        lines.append(
            f"                   i.e. reduction ratio "
            f"{c.reduction_ratio_at_fixed_diameter:.2f}, not "
            f"{p.reduction_ratio:.2f}")
    return "\n".join(lines)


if __name__ == "__main__":       # pragma: no cover
    print(baseline_finding_report())
