import math
import re
from pathlib import Path
import pytest
from argus7.design.geometry import derive_wing, tail_volume_h, ClosureError
from argus7.design.schema import load_design

REPORT = dict(span=9.263, c_root=0.5807, c_tip=0.2613, mac=0.4412)  # report §2

def test_v1_matches_report_section_2():
    """Regression guard for Defect 2: the superseded Gemini chords must never return."""
    g = derive_wing(load_design("design/argus7_v1.yaml").wing)
    assert g.span_m       == pytest.approx(REPORT["span"],   abs=1e-3)
    assert g.chord_root_m == pytest.approx(REPORT["c_root"], abs=1e-3)
    assert g.chord_tip_m  == pytest.approx(REPORT["c_tip"],  abs=1e-3)
    assert g.mac_m        == pytest.approx(REPORT["mac"],    abs=1e-3)

def test_superseded_gemini_chords_are_rejected():
    """c_root=0.674 implies S=4.525 and AR=19.0 - must not validate against S=3.9/AR=22."""
    g = derive_wing(load_design("design/argus7_v1.yaml").wing)
    assert abs(g.chord_root_m - 0.674) > 0.05

def test_closure_identities_hold():
    """Guards derive_wing's formulas (b, c_root, c_tip, MAC) against coding
    regression, not the underlying data against inconsistency: c_tip =
    taper * c_root holds by construction for any input derive_wing accepts,
    so this can never catch a bad design.yaml on its own — that's what
    check_closure / test_inconsistent_design_raises is for."""
    g = derive_wing(load_design("design/argus7_v1.yaml").wing)
    assert abs(g.area_m2 - (g.span_m / 2) * (g.chord_root_m + g.chord_tip_m)) < 1e-9
    assert abs(g.aspect_ratio - g.span_m**2 / g.area_m2) < 1e-9

def test_inconsistent_design_raises(tmp_path):
    """A YAML asserting a chord that contradicts S/AR/taper must fail loudly."""
    bad = tmp_path / "bad.yaml"
    bad.write_text(
        "name: bad\nvariant: test\n"
        "wing: {area_m2: 3.9, aspect_ratio: 22.0, taper_ratio: 0.45,\n"
        "       chord_root_m_assert: 0.674, airfoil: FX63-137, twist_tip_deg: -3.0,\n"
        "       dihedral_deg: 3.0, sweep_le_deg: 1.0, thickness_ratio: 0.137,\n"
        "       incidence_deg: 2.0, x_le_frac: 0.22, z_offset_m: 0.008}\n"
    )
    with pytest.raises(ClosureError):
        load_design(bad)

@pytest.mark.xfail(reason=(
    "Report section 2 tail row does not close: S_h=0.31 m2 with arm=3.2 m gives "
    "V_h=0.577, not the stated 0.68 (17.9% discrepancy). Either S_h should be "
    "0.366 m2 or V_h is 0.577. Transcribed as published; resolved in v2, not by "
    "silently editing v1."))
def test_report_stated_tail_volume():
    assert tail_volume_h(load_design("design/argus7_v1.yaml")) == pytest.approx(0.68, abs=0.005)

def test_tail_volume_actual_value_is_pinned():
    """Pin the real computed value so a future edit cannot drift it unnoticed."""
    assert tail_volume_h(load_design("design/argus7_v1.yaml")) == pytest.approx(0.5765, abs=1e-3)

# --- FINAL REVIEW M7: provenance is a property of every design file --------
# The guard used to be a single test hardcoded to design/argus7_v1.yaml,
# covering only {wing, fuselage, booms, tail, propulsion}. Two holes:
#
#   1. design/argus7_v2.yaml -- a committed deliverable the spec requires,
#      produced by the optimiser -- would have loaded with no provenance block
#      at all. The test is now parameterised over every design/*.yaml, so a
#      new design file is covered the moment it lands.
#   2. masses, mission and aero carried ZERO provenance entries and the test
#      did not ask for any. That included aero.cd0 = 0.020, which report §4
#      itself brackets between a 0.016 clean build and a 0.024 dirty one, and
#      masses.fuel = 101.5, the number at the centre of the unresolved
#      wing-fuel-volume escalation.
#
# Provenance is NOT enforced in load_design: the loader must stay usable for
# the minimal fixtures above (and for any ad-hoc perturbation), so the
# contract is enforced on the committed deliverables, which is where it bites.

DESIGN_FILES = sorted(Path("design").glob("*.yaml"))
PROVENANCE_TAG = re.compile(r"^(report-§\d+|design_pack-§\d+|derived|assumption)$")
PROVENANCED_SECTIONS = ("wing", "fuselage", "booms", "tail", "propulsion",
                        "masses", "mission", "aero")


def test_there_is_at_least_one_design_file():
    """Guard the glob itself: an empty parametrize list silently passes."""
    assert DESIGN_FILES, "no design/*.yaml found -- the provenance sweep is vacuous"


@pytest.mark.parametrize("path", DESIGN_FILES, ids=lambda p: p.name)
def test_every_design_field_has_provenance(path):
    """Every field of every provenanced section must declare where its number
    came from (report-§N, design_pack-§N, derived, or assumption), so a
    defective-artifact value (e.g. model/argus7_model.scad) can never again be
    silently claimed as report-derived."""
    design = load_design(path)
    assert design.provenance is not None, f"{path} has no provenance block"
    sections = {name: getattr(design, name) for name in PROVENANCED_SECTIONS}
    for section_name, model in sections.items():
        assert model is not None, f"{section_name} missing from {path}"
        for field_name in model.model_dump(exclude_none=True):
            key = f"{section_name}.{field_name}"
            assert key in design.provenance, f"{path}: no provenance entry for {key}"
            tag = design.provenance[key]
            assert PROVENANCE_TAG.match(tag), (
                f"{path}: {key} has invalid provenance tag {tag!r}")


@pytest.mark.parametrize("path", DESIGN_FILES, ids=lambda p: p.name)
def test_no_stale_provenance_entries(path):
    """The other direction: a provenance entry for a field that no longer
    exists is rot. booms.length_m was deleted as a Design field by ruling P15;
    an entry left behind for it would claim to document a field nobody can
    set."""
    design = load_design(path)
    assert design.provenance is not None, f"{path} has no provenance block"
    live = {f"{name}.{field}"
            for name in PROVENANCED_SECTIONS
            if getattr(design, name) is not None
            for field in getattr(design, name).model_dump(exclude_none=True)}
    stale = set(design.provenance) - live
    assert not stale, f"{path}: provenance entries for non-existent fields: {sorted(stale)}"


# ============================================================================
# MUTATION SURVIVOR 1: the closure tolerance was unreachable code.
#
# scripts/mutation_test.py changed geometry.TOL from 1e-9 to 1e-1 and the whole
# suite still passed. The reason is not that the tolerance is badly chosen but
# that NOTHING COULD EVER REACH IT: check_closure obtains its WingGeometry from
# derive_wing, and derive_wing *computes* c_root, c_tip and MAC from S, AR and
# taper using exactly the algebra the three identities re-check. All three
# residuals are therefore identically 0.0 (bar ~1e-16 of float rounding) for
# every input the schema accepts. The guard was decorative: an assertion that
# a*b == a*b.
#
# test_closure_identities_hold above says as much in its own docstring and then
# tests the tautology anyway.
#
# To make the tolerance REACHABLE the geometry has to come from somewhere other
# than derive_wing. check_closure is written as a general guard over a
# WingGeometry, so feeding it a hand-built one is a legitimate use, not a trick:
# it is the only way to exercise the branch the tolerance guards. The stub below
# is that second producer. The perturbations are sized so the residual is a
# known, exact number, which is what lets these tests pin the tolerance from
# BOTH sides rather than merely assert "something raised".
# ============================================================================

from types import SimpleNamespace
import argus7.design.geometry as geom
from argus7.design.geometry import WingGeometry, check_closure

# The v1 point. S, AR and taper are READ FROM THE DESIGN FILE -- project
# convention is that geometry lives only in design/*.yaml, and the earlier
# version of this block typed 3.9 / 22.0 / 0.45 straight into the test.
# Everything derived from them (span, chords, MAC) is still computed here BY
# HAND rather than by calling derive_wing, which is the property these tests
# actually need: check_closure must be handed a geometry it did not itself
# produce, or the three identities stay the tautologies they were.
_V1_WING = load_design("design/argus7_v1.yaml").wing
_S, _AR, _LAM = _V1_WING.area_m2, _V1_WING.aspect_ratio, _V1_WING.taper_ratio
_B = math.sqrt(_AR * _S)                       # 9.262828941527529 at v1
_CR = _S / ((_B / 2.0) * (1.0 + _LAM))         # 0.5807416264280583 at v1
_CT = _LAM * _CR                               # 0.2613337318926262 at v1
_MAC = (2.0 / 3.0) * _CR * (1 + _LAM + _LAM**2) / (1 + _LAM)
_MAC_Y = (_B / 6.0) * (1 + 2 * _LAM) / (1 + _LAM)


def _geometry(*, area=_S, ar=_AR, span=_B, c_root=_CR, c_tip=_CT) -> WingGeometry:
    """A WingGeometry assembled from explicit numbers, not from derive_wing."""
    return WingGeometry(span_m=span, chord_root_m=c_root, chord_tip_m=c_tip,
                        mac_m=_MAC, mac_y_m=_MAC_Y, area_m2=area, aspect_ratio=ar)


def _design(taper=_LAM, chord_root_m_assert=None):
    return SimpleNamespace(wing=SimpleNamespace(
        taper_ratio=taper, chord_root_m_assert=chord_root_m_assert))


@pytest.fixture
def stub_derive(monkeypatch):
    """Make check_closure read a caller-supplied geometry instead of deriving one."""
    def install(g: WingGeometry):
        monkeypatch.setattr(geom, "derive_wing", lambda wing: g)
    return install


def test_hand_built_consistent_geometry_passes_closure(stub_derive):
    """Control. Without this, every test below could be passing for the wrong
    reason (e.g. the stub itself breaking check_closure)."""
    stub_derive(_geometry())
    check_closure(_design())            # must not raise


# --- the tolerance is reachable, and it is tight -----------------------------
# Each case perturbs ONE quantity so that exactly one identity's residual takes
# a known value. 1e-3 is 1e6x the real TOL of 1e-9 and 100x SMALLER than the
# mutant's 1e-1, so these three cases are precisely what the mutant survives.

_TAPER_BUMP = 1e-3 / _CR       # makes the c_tip identity's residual exactly -1e-3


@pytest.mark.parametrize("kwargs, design_kwargs, identity, residual", [
    (dict(area=_S + 1e-3),      {},                                "S = (b/2)(c_root + c_tip)",  1e-3),
    (dict(ar=_AR + 1e-3),       {},                                "AR = b^2 / S",               1e-3),
    ({},                        dict(taper=_LAM + _TAPER_BUMP),    "c_tip = taper * c_root",    -1e-3),
])
def test_one_part_in_a_thousand_inconsistency_raises(stub_derive, kwargs, design_kwargs,
                                                     identity, residual):
    """A 1e-3 residual in ANY of the three identities must raise ClosureError.

    Kills the TOL 1e-9 -> 1e-1 mutant: at TOL=1e-1 a residual of 1e-3 sails
    through and no exception is raised."""
    stub_derive(_geometry(**kwargs))
    with pytest.raises(ClosureError, match=re.escape(identity)) as exc:
        check_closure(_design(**design_kwargs))
    # the reported residual must be the one we injected, not an incidental
    # second violation that happened to fire first
    reported = float(str(exc.value).rsplit(" by ", 1)[1])
    assert reported == pytest.approx(residual, rel=1e-6)


def test_tolerance_upper_bound_a_residual_of_1e_8_still_raises(stub_derive):
    """Pins TOL <= 1e-8. Any loosening of the tolerance -- 1e-1, 1e-3, 1e-6 --
    fails here."""
    stub_derive(_geometry(area=_S + 1e-8))
    with pytest.raises(ClosureError):
        check_closure(_design())


def test_tolerance_lower_bound_a_residual_of_1e_10_does_not_raise(stub_derive):
    """Pins the tolerance from below, so it cannot be tightened past float
    rounding either -- at TOL=1e-15 the ~1e-16 noise in derive_wing's own
    output would start throwing on valid designs.

    ADVERSARIAL REVIEW: the bound this actually pins is ~5.6e-10, not 1e-10.
    Perturbing the area by 1e-10 moves the AR identity too (AR - b^2/S picks
    up 5.6e-10, since dAR/dS = -AR/S = -5.6 per unit area), and that is the
    larger of the two residuals. So TOL is boxed into roughly
    [5.6e-10, 1.0e-8] by this test and the one above -- verified by running
    the suite at TOL = 1e-2, 1e-4, 1e-7 and 1e-15, which fail 4, 4, 1 and 3
    tests respectively."""
    stub_derive(_geometry(area=_S + 1e-10))
    check_closure(_design())            # must not raise


# --- the chord_root_m_assert cross-check has its own, separate tolerance -----
# This one IS reachable today (test_inconsistent_design_raises uses it), but
# only with a 0.093 m discrepancy -- 93x its 1e-3 threshold. These two pin the
# threshold itself.

def test_chord_assert_rejects_a_two_millimetre_contradiction():
    d = load_design("design/argus7_v1.yaml")
    derived = derive_wing(d.wing).chord_root_m
    d.wing.chord_root_m_assert = derived + 2e-3
    with pytest.raises(ClosureError, match="chord_root_m_assert"):
        check_closure(d)


def test_chord_assert_accepts_a_half_millimetre_rounding_difference():
    """The other side: the threshold must tolerate a value transcribed to 4 dp
    from the report, or every design file would have to carry full precision."""
    d = load_design("design/argus7_v1.yaml")
    derived = derive_wing(d.wing).chord_root_m
    d.wing.chord_root_m_assert = derived + 5e-4
    check_closure(d)                    # must not raise
