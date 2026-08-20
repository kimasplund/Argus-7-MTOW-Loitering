"""One test per defect found in the original model/argus7_model.scad.
These must never pass by accident again."""
import re, pytest
from pathlib import Path
from argus7.design.schema import load_design
from argus7.design.geometry import derive_wing

SCAD = Path("model/argus7_model.scad")

def test_defect2_superseded_chords_absent_from_committed_model():
    text = SCAD.read_text()
    assert "0.674" not in text, "superseded Gemini root chord is back"
    assert "0.303" not in text, "superseded Gemini tip chord is back"

def test_committed_model_matches_the_design_file():
    g = derive_wing(load_design("design/argus7_v1.yaml").wing)
    text = SCAD.read_text()
    assert f"{g.chord_root_m:.4f}" in text
    assert f"{g.mac_m:.4f}" in text

def test_defect3_model_contains_a_real_airfoil():
    text = SCAD.read_text()
    assert "airfoil = [" in text
    n = len(re.findall(r"\[-?\d+\.\d+,-?\d+\.\d+\]", text))
    assert n > 50, f"only {n} section coordinates - not a real airfoil"

def test_model_is_marked_generated():
    assert "GENERATED" in SCAD.read_text().upper()
