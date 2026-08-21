"""The mass model and the tank model, pinned against arithmetic done OUTSIDE them.

WHY THIS FILE EXISTS
--------------------
scripts/mutation_test.py injected eight plausible defects one at a time. Two of
the four that SURVIVED live in argus7/opt/design_space.py, which had no test file
at all despite being the module that produced the entire v2.0 recommendation:

  SURVIVOR 3  SIGMA_CAP_PA = 600e6 -> 800e6 ("the spar allowable can be raised
              33% for free"). Every wing gets lighter, fuel fraction rises,
              endurance inflates, nothing objects.

  SURVIVOR 4  k_area=0.6062 -> 0.68 ("the NACA-4 shape factor this project
              already caught twice"): once as a 12.2% error in the Task-3
              wing-area test, once as a 1.68x error in the tank model.

The rule this file follows: NEVER pin the module against itself. Every expected
value below is computed here, from constants written out as literals and from
geometry read out of design/*.yaml, using arithmetic a reviewer can check with a
calculator. A test that calls design_space to compute what design_space should
have computed cannot fail.

WHY SIGMA_CAP_PA NEEDED A SPECIFIC KIND OF TEST
-----------------------------------------------
SIGMA_CAP_PA is invisible to any end-to-end test, and this is not an oversight in
the old suite -- it is structural. m_cap is proportional to k_cal / sigma, and
calibrate() solves for k_cal such that the baseline wing weighs 32.5 kg, so
k_cal is proportional to sigma. The sigma CANCELS EXACTLY at every design point:

    sigma = 600 MPa -> k_cal = 4.225741615220753 -> v2 wing 39.20322 kg
    sigma = 800 MPa -> k_cal = 5.634322153627671 -> v2 wing 39.20322 kg

(measured, identical to 14 significant figures). So "changing it to 800e6 makes
every wing lighter" is true only for a consumer that holds k_cal fixed -- and
the recalibrated pipeline is not one. That makes the mutant WORSE, not better:
the constant is load-bearing documentation of the structural allowable the
report claims, it is quoted to the sponsor, and it is completely unfalsifiable
downstream. The only places it can be caught are the two below, and both are
tested here:

  (a) the un-normalised physics, i.e. wing_mass_kg at k_cal = 1.0, and
  (b) the calibration constant itself, which moves 600 -> 800 as 4.2257 ->
      5.6343.
"""
from __future__ import annotations

import inspect
import math

import numpy as np
import pytest
import torch

import argus7.opt.design_space as ds
from argus7.cad.airfoil_coords import load_airfoil, max_thickness
from argus7.design.schema import load_design
from argus7.opt.design_space import calibrate, wing_fuel_capacity_kg, wing_mass_kg

# ---------------------------------------------------------------------------
# Constants written out as LITERALS, not imported.
#
# Importing them would make every assertion below a tautology: the mutant edits
# the module constant, the test would read the edited value, and both sides of
# the comparison would move together. These are transcribed by hand from
# argus7/opt/design_space.py's own docstring and comments, which cite the design
# report section 5 and the materials pack.
# ---------------------------------------------------------------------------
G = 9.80665                 # standard gravity
SIGMA_CAP_PA = 600e6        # spar-cap compression allowable, report section 5
RHO_CFRP = 1600.0           # kg/m3, UD carbon/epoxy
K_LIFT = 0.40               # spanwise centroid of lift, near-elliptic loading
K_TAPER = 0.55              # integrated cap area as a fraction of root area
FUEL_RELIEF = 0.78          # wing-borne fuel offloads the root moment
N_ULT = 5.7                 # ultimate load factor
SKIN_RIB_KG_PER_M2 = 4.6    # skins, ribs, flaperons, tanks

# Tank model, from wing_fuel_capacity_kg's signature and docstring.
CHORD_FRAC = 0.716          # section AREA fraction of a 15-65% chord spar box
SPAN_FRAC = 0.940           # wing VOLUME fraction inside the inner 80% of span
NET_FRAC = 0.88             # bladder/structure/expansion allowance
FUEL_DENSITY_KGL = 0.78     # kg/L

# The published calibration outputs, from docs/decisions/2026-08-20-gauntlet-audit.md
PUBLISHED_K_CAL = 4.225741615220753
PUBLISHED_BASELINE_WING_KG = 32.5


def _t(v):
    return torch.tensor(float(v), dtype=torch.float64)


def _design_point(path):
    """Geometry comes from the YAML, never from a literal in this file --
    project convention. Only the PHYSICAL constants above are literals."""
    d = load_design(path)
    return dict(S=d.wing.area_m2, AR=d.wing.aspect_ratio, lam=d.wing.taper_ratio,
                mtow=d.masses.mtow, tc=d.wing.thickness_ratio)


V1 = _design_point("design/argus7_v1.yaml")
V2 = _design_point("design/argus7_v2.yaml")
POINTS = {"v1": V1, "v2": V2}


# ===========================================================================
# 1. Hand-computed beam theory
# ===========================================================================

def _hand_wing_mass(S, AR, lam, mtow, tc, k_cal):
    """The five lines of beam theory the module claims to implement, written
    out again from the documented constants.

        b       = sqrt(AR S)                        span
        c_root  = S / ((b/2)(1 + lambda))           root chord
        h_spar  = (t/c) c_root                      cap centroid separation
        M_root  = n_ult W g (b/2) k_lift f_relief   root bending moment
        A_cap   = M_root / (h_spar sigma)           cap area from M = sigma A h
        m_cap   = k_cal rho A_cap (b/2) k_taper * 2 both caps, tapering out
        m_wing  = m_cap + skin_rib * S
    """
    b = math.sqrt(AR * S)
    c_root = S / ((b / 2.0) * (1.0 + lam))
    h_spar = tc * c_root
    m_root = N_ULT * mtow * G * (b / 2.0) * K_LIFT * FUEL_RELIEF
    cap_area = m_root / (h_spar * SIGMA_CAP_PA)
    m_cap = k_cal * RHO_CFRP * cap_area * (b / 2.0) * K_TAPER * 2.0
    return m_cap + SKIN_RIB_KG_PER_M2 * S, m_cap, m_root, cap_area


@pytest.mark.parametrize("name", ["v1", "v2"])
@pytest.mark.parametrize("k_cal", [1.0, PUBLISHED_K_CAL])
def test_wing_mass_matches_hand_computed_beam_theory(name, k_cal):
    """The load-bearing test for SURVIVOR 3.

    At a FIXED k_cal the spar allowable is no longer normalised away, so
    sigma = 800 MPa returns a cap 25% lighter than the hand computation above,
    which still uses 600 MPa. Measured at v1, k_cal = 1: 21.3855 kg becomes
    20.5271 kg -- a 4.0% miss on total wing mass, 25% on the cap alone.
    """
    p = POINTS[name]
    expected, *_ = _hand_wing_mass(p["S"], p["AR"], p["lam"], p["mtow"], p["tc"], k_cal)
    got = float(wing_mass_kg(_t(p["S"]), _t(p["AR"]), _t(p["lam"]), _t(p["mtow"]),
                             _t(p["tc"]), _t(k_cal)))
    assert got == pytest.approx(expected, rel=1e-12)


@pytest.mark.parametrize("name", ["v1", "v2"])
def test_root_bending_moment_and_cap_area_are_the_documented_beam_theory(name):
    """Pin the two intermediates by name, so a failure says WHICH step moved.

    The cap area recovered from the model is
        A_cap = (m_wing - skin_rib S) / (k_cal rho (b/2) k_taper 2)
    and must equal M_root / (h_spar sigma). At v1 that is 20.1931 kN.m and
    423.008 mm2 of cap; at v2, 24.9874 kN.m and 328.709 mm2. (The 422.7 mm2
    and 24.992 kN.m first written here were wrong: 422.7 mm2 is the cap at
    calibrate()'s t/c default of 0.1371, not at the YAML's 0.137, and 24.992
    kN.m does not reproduce at all. Docstring only -- nothing asserted them.)

    NOTE, not asserted: docs/report_outline.md quotes a root bending moment of
    15.2 kN.m. The model's v1 figure is 20.19 kN.m (25.89 kN.m before the 0.78
    fuel-relief factor). Neither reproduces 15.2, so the outline's number comes
    from some third set of assumptions. Flagged, not silently blessed -- pinning
    a number this file cannot derive would be exactly the self-referential test
    this file exists to avoid.
    """
    p = POINTS[name]
    b = math.sqrt(p["AR"] * p["S"])
    _, _, m_root_hand, cap_area_hand = _hand_wing_mass(
        p["S"], p["AR"], p["lam"], p["mtow"], p["tc"], 1.0)

    m_wing = float(wing_mass_kg(_t(p["S"]), _t(p["AR"]), _t(p["lam"]), _t(p["mtow"]),
                                _t(p["tc"]), _t(1.0)))
    cap_area_model = ((m_wing - SKIN_RIB_KG_PER_M2 * p["S"])
                      / (1.0 * RHO_CFRP * (b / 2.0) * K_TAPER * 2.0))
    assert cap_area_model == pytest.approx(cap_area_hand, rel=1e-12)

    # and the moment that implies, at the documented allowable
    c_root = p["S"] / ((b / 2.0) * (1.0 + p["lam"]))
    m_root_model = cap_area_model * p["tc"] * c_root * SIGMA_CAP_PA
    assert m_root_model == pytest.approx(m_root_hand, rel=1e-12)


def test_v1_root_bending_moment_is_20_2_kilonewton_metres():
    """An absolute magnitude, so a reviewer can check the physics without
    re-deriving it: 5.7 g ultimate on 250 kg is 13.97 kN of lift, acting at
    k_lift = 0.40 of the 4.631 m semi-span, relieved 22% by wing fuel."""
    _, _, m_root, _ = _hand_wing_mass(V1["S"], V1["AR"], V1["lam"], V1["mtow"],
                                      V1["tc"], 1.0)
    assert m_root == pytest.approx(20193.1, abs=1.0)


# ===========================================================================
# 2. The calibration
# ===========================================================================

def test_calibration_reproduces_the_published_32_5_kg_wing():
    """The report's section-3 mass budget puts the wing at 32.5 kg (8.6 kg/m2
    on 3.9 m2). calibrate() exists to make the model say exactly that."""
    k = calibrate()
    sig = inspect.signature(calibrate).parameters
    baseline = float(wing_mass_kg(_t(sig["wing_area_m2"].default),
                                  _t(sig["aspect_ratio"].default),
                                  _t(sig["taper_ratio"].default),
                                  _t(sig["mtow_kg"].default),
                                  _t(sig["thickness_ratio"].default), _t(k)))
    assert baseline == pytest.approx(PUBLISHED_BASELINE_WING_KG, rel=1e-12)


def test_the_calibration_constant_itself_is_pinned():
    """The second kill for SURVIVOR 3.

    k_cal is proportional to sigma, so raising the allowable to 800 MPa moves
    k_cal from 4.225741615220753 to 5.634322153627671 -- exactly 4/3. The
    calibration constant is the one published number that still SEES the
    allowable after the normalisation cancels it everywhere else, which is
    why it is pinned to full double precision rather than to 4 dp.

    Recomputed here from the hand beam theory, not read from the module.
    """
    sig = inspect.signature(calibrate).parameters
    S = sig["wing_area_m2"].default
    _, unit_cap, _, _ = _hand_wing_mass(S, sig["aspect_ratio"].default,
                                        sig["taper_ratio"].default,
                                        sig["mtow_kg"].default,
                                        sig["thickness_ratio"].default, 1.0)
    expected = (PUBLISHED_BASELINE_WING_KG - SKIN_RIB_KG_PER_M2 * S) / unit_cap
    assert expected == pytest.approx(PUBLISHED_K_CAL, rel=1e-12)
    assert calibrate() == pytest.approx(expected, rel=1e-12)


def test_calibration_defaults_still_describe_the_v1_design_file():
    """calibrate() hardcodes its baseline point. If design/argus7_v1.yaml ever
    moves, the calibration silently stops describing the aircraft it names.

    thickness_ratio is the one deliberate difference: calibrate() uses 0.1371,
    the value MEASURED off the FX 63-137 coordinates, where the YAML carries
    0.137 from the section designation. Allowed to 1e-3, not to 0."""
    sig = inspect.signature(calibrate).parameters
    assert sig["wing_area_m2"].default == pytest.approx(V1["S"], rel=1e-9)
    assert sig["aspect_ratio"].default == pytest.approx(V1["AR"], rel=1e-9)
    assert sig["taper_ratio"].default == pytest.approx(V1["lam"], rel=1e-9)
    assert sig["mtow_kg"].default == pytest.approx(V1["mtow"], rel=1e-9)
    assert sig["thickness_ratio"].default == pytest.approx(V1["tc"], abs=1e-3)


# ===========================================================================
# 3. The spar allowable, in the right direction and by the right magnitude
# ===========================================================================

@pytest.mark.parametrize("sigma_pa, expected_cap_ratio", [
    (400e6, 600.0 / 400.0),      # weaker cap -> 1.5x the cap mass
    (800e6, 600.0 / 800.0),      # the mutant's value -> 0.75x
    (1200e6, 600.0 / 1200.0),    # 0.5x
])
def test_cap_mass_is_inversely_proportional_to_the_spar_allowable(monkeypatch,
                                                                 sigma_pa,
                                                                 expected_cap_ratio):
    """A_cap = M_root / (h sigma), so cap mass must go as 1/sigma exactly, and
    the skin/rib term must not move at all.

    This is the direction-and-magnitude test SURVIVOR 3 calls for, and it is
    self-killing under the mutant: with the module already at 800e6, the
    800e6 case measures 800 against 800 and returns a ratio of 1.0, not 0.75.
    """
    p = V2
    args = (_t(p["S"]), _t(p["AR"]), _t(p["lam"]), _t(p["mtow"]), _t(p["tc"]), _t(1.0))
    skin = SKIN_RIB_KG_PER_M2 * p["S"]

    cap_ref = float(wing_mass_kg(*args)) - skin
    monkeypatch.setattr(ds, "SIGMA_CAP_PA", sigma_pa)
    cap_new = float(wing_mass_kg(*args)) - skin

    assert cap_new / cap_ref == pytest.approx(expected_cap_ratio, rel=1e-12)
    # the non-spar mass is not a function of the allowable
    assert float(wing_mass_kg(*args)) - cap_new == pytest.approx(skin, rel=1e-12)


def test_the_module_allowable_is_the_600_MPa_the_report_documents(monkeypatch):
    """Direct statement of the same fact, so the failure message names the
    constant rather than a mass ratio. Measured behaviourally -- the cap mass
    at the module's own allowable must equal the cap mass at a monkeypatched
    600 MPa -- rather than by reading ds.SIGMA_CAP_PA, which the mutant edits.
    """
    p = V1
    args = (_t(p["S"]), _t(p["AR"]), _t(p["lam"]), _t(p["mtow"]), _t(p["tc"]), _t(1.0))
    as_shipped = float(wing_mass_kg(*args))
    monkeypatch.setattr(ds, "SIGMA_CAP_PA", 600e6)
    at_600 = float(wing_mass_kg(*args))
    assert as_shipped == pytest.approx(at_600, rel=1e-12), (
        "the module's spar-cap allowable is not 600 MPa -- report section 5's "
        "buckling/damage-knocked-down compression allowable. Raising it makes "
        "every wing lighter and every endurance longer, and the recalibration "
        "in calibrate() hides the change from every downstream test.")


# ===========================================================================
# 4. The scaling exponents that stop the optimiser running away
# ===========================================================================
# m_cap ~ n_ult W (1+lambda) AR^1.5 sqrt(S) / ((t/c) sigma).
# The AR^1.5 is the term the module's docstring says is "what stops the
# optimiser running away to AR 30". Nothing tested it.

@pytest.mark.parametrize("ar_lo, ar_hi", [(14.0, 22.0), (22.0, 30.0), (14.0, 30.0)])
def test_cap_mass_scales_as_aspect_ratio_to_the_three_halves(ar_lo, ar_hi):
    """Ratios across the full Bounds.aspect_ratio range (14 to 30). At fixed
    area, cap mass must rise as (AR_hi/AR_lo)^1.5 -- 3.1368x from AR 14 to 30.
    An exponent of 1.0 would give 2.14x, an exponent of 2.0 would give 4.59x."""
    S, lam, mtow, tc = V1["S"], V1["lam"], V1["mtow"], V1["tc"]
    skin = SKIN_RIB_KG_PER_M2 * S
    cap = lambda ar: float(wing_mass_kg(_t(S), _t(ar), _t(lam), _t(mtow),
                                        _t(tc), _t(1.0))) - skin
    assert cap(ar_hi) / cap(ar_lo) == pytest.approx((ar_hi / ar_lo) ** 1.5, rel=1e-12)


@pytest.mark.parametrize("exponent_of, ratio, expected", [
    ("area",      6.0 / 2.5,  (6.0 / 2.5) ** 0.5),    # sqrt(S) at fixed AR
    ("mtow",      320.0 / 180.0, 320.0 / 180.0),      # linear in weight
    ("thickness", 0.20 / 0.10, 0.10 / 0.20),          # inverse in t/c
])
def test_the_other_cap_mass_exponents(exponent_of, ratio, expected):
    """The remaining three exponents in the derivation. Together with AR^1.5
    they fix the whole cap-mass surface up to one constant -- which is
    precisely k_cal, and which the calibration tests above pin."""
    base = dict(S=V1["S"], AR=V1["AR"], lam=V1["lam"], mtow=V1["mtow"], tc=V1["tc"])
    key = {"area": "S", "mtow": "mtow", "thickness": "tc"}[exponent_of]
    lo = dict(base)
    hi = dict(base)
    lo[key], hi[key] = {"area": (2.5, 6.0), "mtow": (180.0, 320.0),
                        "thickness": (0.10, 0.20)}[exponent_of]

    def cap(p):
        return (float(wing_mass_kg(_t(p["S"]), _t(p["AR"]), _t(p["lam"]),
                                   _t(p["mtow"]), _t(p["tc"]), _t(1.0)))
                - SKIN_RIB_KG_PER_M2 * p["S"])

    assert cap(hi) / cap(lo) == pytest.approx(expected, rel=1e-12)


def test_skin_and_rib_mass_is_4_6_kg_per_square_metre():
    """The area-scaled term, isolated: at k_cal = 0 the cap vanishes and what
    is left must be exactly 4.6 kg/m2 of skins, ribs, flaperons and tanks."""
    for p in (V1, V2):
        m = float(wing_mass_kg(_t(p["S"]), _t(p["AR"]), _t(p["lam"]), _t(p["mtow"]),
                               _t(p["tc"]), _t(0.0)))
        assert m == pytest.approx(SKIN_RIB_KG_PER_M2 * p["S"], rel=1e-12)


# ===========================================================================
# 5. SURVIVOR 4: k_area must equal the shoelace of the coordinates it names
# ===========================================================================

def _shoelace_area(coords: np.ndarray) -> float:
    """Enclosed area of a unit-chord section, from its own coordinates."""
    x, y = coords[:, 0], coords[:, 1]
    return 0.5 * abs(float(np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y)))


def _measured_k_area() -> float:
    """The FX 63-137 section-area coefficient: enclosed area / (t/c), at unit
    chord, so that section area = k_area * (t/c) * chord^2 by definition."""
    c = load_airfoil("fx63137")
    return _shoelace_area(c) / max_thickness(c)


def test_k_area_default_matches_the_real_fx63137_coordinates():
    """The load-bearing test for SURVIVOR 4.

    data/airfoils/fx63137.dat shoelace-integrates to an enclosed area of
    0.083121 at unit chord against a measured t/c of 0.137117, giving
    k_area = 0.606203. The module's default, 0.6062, must be that number and
    not the NACA-4-digit 0.68 -- a value that has already caused two separate
    errors in this project (a 12.2% error in the Task-3 wing-area test, and a
    1.68x error in this very tank model).

    Tolerance 0.005 as specified: tight enough that 0.68 misses by 15x the
    allowance, loose enough that a re-rounding of the constant is not a failure.
    """
    default = inspect.signature(wing_fuel_capacity_kg).parameters["k_area"].default
    measured = _measured_k_area()
    assert measured == pytest.approx(0.606203, abs=1e-5)      # pins the fixture
    assert default == pytest.approx(measured, abs=0.005), (
        f"k_area default {default} does not describe data/airfoils/fx63137.dat, "
        f"whose measured section-area coefficient is {measured:.6f}. The "
        f"NACA-4-digit 0.68 is wrong for this section by 12.2%.")
    assert abs(default - 0.68) > 0.005, (
        "k_area has been reverted to the NACA-4-digit 0.68 -- the third "
        "occurrence of an error this project has already made twice.")


@pytest.mark.parametrize("name", ["v1", "v2"])
def test_wing_fuel_capacity_matches_an_independent_volume_integration(name):
    """Independent numerical integration of the actual wing.

    Section area at spanwise station y is measured by shoelace-integrating the
    REAL fx63137 coordinates, scaled to the local chord and stretched in z to
    the design thickness ratio. Integrated over the span by trapezoid on 20001
    stations, then reduced by the documented spar-box, span and net fractions
    and multiplied by the fuel density. Nothing here calls design_space.

        v1  gross 142.9112 L  ->   84.6428 L usable  ->   66.0214 kg
        v2  gross 299.8932 L  ->  177.6193 L usable  ->  138.5431 kg

    (Recomputed in adversarial review; the figures first written here were
    143.016 / 84.705 / 66.070 and 299.864 / 177.602 / 138.529, which are the
    README's t/c = 0.1371 numbers, not this file's YAML t/c = 0.137 ones.)
    README.md quotes 143.016 L gross for v1 against the 142.9112 L the YAML
    implies, and the 66 kg against the report's 101.5 kg of fuel is the
    wing-fuel escalation.
    """
    p = POINTS[name]
    coords = load_airfoil("fx63137")
    a_unit = _shoelace_area(coords)          # area at unit chord, native t/c
    tc_native = max_thickness(coords)

    b = math.sqrt(p["AR"] * p["S"])
    c_root = p["S"] / ((b / 2.0) * (1.0 + p["lam"]))
    y = np.linspace(0.0, b / 2.0, 20001)
    chord = c_root * (1.0 - (1.0 - p["lam"]) * (2.0 * y / b))
    section_area = a_unit * (p["tc"] / tc_native) * chord**2
    gross_m3 = 2.0 * float(np.trapezoid(section_area, y))

    expected_kg = (gross_m3 * 1000.0 * CHORD_FRAC * SPAN_FRAC * NET_FRAC
                   * FUEL_DENSITY_KGL)
    got = float(wing_fuel_capacity_kg(_t(p["S"]), _t(p["AR"]), _t(p["lam"]), _t(p["tc"])))

    # The only difference between the two is that the module rounds k_area to
    # 4 dp (0.6062 vs 0.60620254). Measured at both points: 4.193e-06. 1e-5
    # leaves 2.4x of headroom; the 1e-4 this was written with left 24x, which
    # is enough slack to hide a real drift in the section.
    assert got == pytest.approx(expected_kg, rel=1e-5)


@pytest.mark.parametrize("name, gross_litres", [("v1", 142.9112), ("v2", 299.8932)])
def test_gross_wing_volume_is_the_figure_the_readme_quotes(name, gross_litres):
    """Absolute magnitudes, so a shape-factor change shows up as a volume a
    reader can recognise rather than only as a ratio.

    142.911 L at v1, not the 143.016 L the README quotes: the README used the
    MEASURED t/c of 0.1371 while design/argus7_v1.yaml carries 0.137 from the
    section designation. A 0.07% difference, recorded here rather than rounded
    away, because volume is linear in t/c and this file reads its geometry from
    the YAML.

    ADVERSARIAL REVIEW: v2 was pinned at 299.864 L against a true 299.8932 L,
    a relative error of 9.74e-05 inside a 1e-4 tolerance -- 2.6% of the
    allowance left. Same failure mode as the 66.07 above: a stale number held
    up by a tolerance wide enough to hide it. Both corrected."""
    p = POINTS[name]
    got_kg = float(wing_fuel_capacity_kg(_t(p["S"]), _t(p["AR"]), _t(p["lam"]),
                                         _t(p["tc"])))
    implied_gross_l = got_kg / (FUEL_DENSITY_KGL * CHORD_FRAC * SPAN_FRAC * NET_FRAC)
    # rel=1e-6, not the 1e-4 this was written with: at 1e-4 the stale 299.864
    # for v2 (true value 299.8932, a relative error of 9.74e-05) sat INSIDE
    # the tolerance, so the pin did not pin anything. Both figures now agree
    # to ~3e-08, so 1e-6 still leaves two orders of headroom.
    assert implied_gross_l == pytest.approx(gross_litres, rel=1e-6)


def test_fuel_capacity_is_proportional_to_the_shape_factor():
    """Second kill for SURVIVOR 4, and the one that states the consequence:
    substituting the NACA-4-digit 0.68 for the measured 0.6062 inflates the
    tank by 12.17%. Under the mutant the default IS 0.68, so this measures
    0.68 against 0.68 and returns 1.0."""
    p = V1
    args = (_t(p["S"]), _t(p["AR"]), _t(p["lam"]), _t(p["tc"]))
    shipped = float(wing_fuel_capacity_kg(*args))
    as_naca4 = float(wing_fuel_capacity_kg(*args, k_area=0.68))
    assert as_naca4 / shipped == pytest.approx(0.68 / 0.6062, rel=1e-6)
    assert as_naca4 / shipped == pytest.approx(1.1217, abs=1e-3)


def test_the_tank_fractions_are_the_corrected_ones_not_the_pre_audit_ones():
    """The 2026-08-21 gauntlet correction replaced chord_frac 0.50 / span_frac
    0.80 (fraction of CHORD and fraction of SPAN) with 0.716 / 0.940 (fraction
    of section AREA and fraction of VOLUME). Reverting either understates
    capacity by 1.68x together. Checked behaviourally against this file's own
    literals rather than by reading the module's defaults."""
    p = V1
    args = (_t(p["S"]), _t(p["AR"]), _t(p["lam"]), _t(p["tc"]))
    shipped = float(wing_fuel_capacity_kg(*args))
    pre_audit = float(wing_fuel_capacity_kg(*args, chord_frac=0.50, span_frac=0.80))
    assert shipped / pre_audit == pytest.approx(
        (CHORD_FRAC * SPAN_FRAC) / (0.50 * 0.80), rel=1e-9)
    assert shipped / pre_audit == pytest.approx(1.6826, abs=1e-3)


def test_the_wing_cannot_hold_the_reports_fuel_load():
    """The escalation, pinned so it cannot be closed by accident: report
    section 3 budgets 101.5 kg of fuel at v1 and the v1 wing holds 66.02 kg.

    ADVERSARIAL REVIEW: this was pinned at 66.07 +/- 0.05 and the true value is
    66.0214 -- a stale figure carried over from the README's 143.016 L (which
    uses the MEASURED t/c 0.1371), riding 0.0487 inside a 0.05 tolerance. It
    passed with 2.7% of the allowance to spare, i.e. the tolerance was doing
    the work the number should have. Corrected to the value this file's own
    geometry implies, at a tolerance 5x tighter.
    If a future edit makes this test fail, the tank model or the mass budget
    changed -- either way the README's 'Known gaps' entry needs revisiting."""
    budgeted = load_design("design/argus7_v1.yaml").masses.fuel
    tank = float(wing_fuel_capacity_kg(_t(V1["S"]), _t(V1["AR"]), _t(V1["lam"]),
                                       _t(V1["tc"])))
    assert tank == pytest.approx(66.021, abs=0.01)
    assert tank < budgeted
    assert tank / budgeted == pytest.approx(0.651, abs=0.005)
