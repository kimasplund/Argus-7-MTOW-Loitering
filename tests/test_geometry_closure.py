import math
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

def test_every_geometry_field_has_provenance():
    """Every geometry field under wing/fuselage/booms/tail/propulsion must
    declare where its number came from (report-§2, design_pack-§1, derived,
    or assumption), so a defective-artifact value (e.g. model/argus7_model.scad)
    can never again be silently claimed as report-derived."""
    design = load_design("design/argus7_v1.yaml")
    assert design.provenance is not None
    allowed_tags = {"report-§2", "design_pack-§1", "derived", "assumption"}
    sections = {
        "wing": design.wing,
        "fuselage": design.fuselage,
        "booms": design.booms,
        "tail": design.tail,
        "propulsion": design.propulsion,
    }
    for section_name, model in sections.items():
        assert model is not None, f"{section_name} missing from design"
        for field_name in model.model_dump(exclude_none=True):
            key = f"{section_name}.{field_name}"
            assert key in design.provenance, f"no provenance entry for {key}"
            tag = design.provenance[key]
            assert tag in allowed_tags, f"{key} has invalid provenance tag {tag!r}"
