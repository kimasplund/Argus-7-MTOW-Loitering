"""One test per defect found in the original model/argus7_model.scad.
These must never pass by accident again."""
import re, pytest
from pathlib import Path
from argus7.design.schema import load_design
from argus7.design.geometry import derive_wing
from argus7.cad.to_openscad import emit_openscad

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


# --- FINAL REVIEW C2: the committed .scad must not drift from the YAML -----

def test_committed_scad_is_byte_identical_to_a_fresh_emit(tmp_path):
    """The tracked .scad is the only geometry artifact in git (STEP and STL
    are gitignored build output) and the one the README and the report point
    readers at. Until now the ONLY thing tying it to design/argus7_v1.yaml was
    test_committed_model_matches_the_design_file above, which samples exactly
    two derived numbers -- c_root and MAC -- as 4-decimal substrings.

    Demonstrated during the final review: editing wing.dihedral_deg 3.0 -> 6.0
    and booms.diameter_m 0.09 -> 0.14 WITHOUT re-running
    scripts/build_model.py left all 57 tests passing. Every parameter that is
    not c_root or MAC could diverge silently.

    This is a different defect from Defect 4, which P1 genuinely fixed:
    intra-file inconsistency is now unrepresentable because the file is
    generated. What was unguarded is file-versus-SOURCE staleness -- a
    geometry change committed without regenerating the artifact.

    If this fails, the fix is to run `python scripts/build_model.py` and
    commit the regenerated .scad and figures/cad renders. Do not hand-edit
    the .scad: that is the original geometry-drift defect.
    """
    design = load_design("design/argus7_v1.yaml")
    fresh = emit_openscad(design, tmp_path / "argus7_model.scad")
    committed_bytes, fresh_bytes = SCAD.read_bytes(), fresh.read_bytes()
    if committed_bytes != fresh_bytes:
        c_lines = committed_bytes.decode().splitlines()
        f_lines = fresh_bytes.decode().splitlines()
        first = next((i for i, (a, b) in enumerate(zip(c_lines, f_lines))
                      if a != b), min(len(c_lines), len(f_lines)))
        raise AssertionError(
            f"{SCAD} is stale against design/argus7_v1.yaml -- re-run "
            f"scripts/build_model.py and commit the result.\n"
            f"  first difference at line {first + 1}:\n"
            f"    committed: {c_lines[first] if first < len(c_lines) else '<eof>'}\n"
            f"    fresh:     {f_lines[first] if first < len(f_lines) else '<eof>'}")
