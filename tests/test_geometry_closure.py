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
