import pytest, trimesh
from pathlib import Path
from argus7.design.schema import load_design
from argus7.design.geometry import derive_wing
from argus7.cad.export import export_model, check_watertight
from argus7.cad.to_openscad import emit_openscad


@pytest.fixture(scope="module")
def design(): return load_design("design/argus7_v1.yaml")


@pytest.fixture(scope="module")
def exported(design, tmp_path_factory):
    return export_model(design, tmp_path_factory.mktemp("cad"))


def test_step_and_stl_are_written(exported):
    assert exported["step"].exists() and exported["step"].stat().st_size > 10_000
    assert exported["stl"].exists()  and exported["stl"].stat().st_size > 10_000


def test_stl_is_watertight(exported):
    assert check_watertight(exported["stl"])


def test_stl_span_matches_design(exported, design):
    m = trimesh.load(exported["stl"])
    g = derive_wing(design.wing)
    assert (m.bounds[1][1] - m.bounds[0][1]) == pytest.approx(g.span_m, rel=0.03)


def test_openscad_header_is_generated_not_handwritten(design, tmp_path):
    """Defect 2 was a hand-typed header that drifted from the real geometry."""
    g = derive_wing(design.wing)
    text = emit_openscad(design, tmp_path / "m.scad").read_text()
    assert f"{g.mac_m:.4f}" in text
    assert f"{g.chord_root_m:.4f}" in text
    assert "0.674" not in text, "superseded Gemini root chord reappeared"
    assert "GENERATED" in text.upper()


def test_openscad_output_parses(design, tmp_path):
    import shutil, subprocess
    if shutil.which("openscad") is None:
        pytest.skip("openscad not installed")
    p = emit_openscad(design, tmp_path / "m.scad")
    r = subprocess.run(["openscad", "-o", str(tmp_path / "m.stl"), str(p)],
                       capture_output=True, timeout=300)
    assert r.returncode == 0, r.stderr.decode()[:2000]


def test_openscad_rendered_stl_is_spanwise_in_y(design, tmp_path):
    """RULING P5 regression guard: the brief's original section() module drew
    the airfoil in the XY plane and extruded along Z, so hulling consecutive
    stations swept vertically instead of spanwise -- span would show up on Z,
    not Y. This proves the fix holds in the actual openscad-rendered
    geometry, not merely in the emitted .scad text."""
    import shutil, subprocess
    if shutil.which("openscad") is None:
        pytest.skip("openscad not installed")
    g = derive_wing(design.wing)
    p = emit_openscad(design, tmp_path / "m2.scad")
    stl = tmp_path / "m2.stl"
    r = subprocess.run(["openscad", "-o", str(stl), str(p)],
                       capture_output=True, timeout=300)
    assert r.returncode == 0, r.stderr.decode()[:2000]
    m = trimesh.load(str(stl))
    y_extent = m.bounds[1][1] - m.bounds[0][1]
    assert y_extent == pytest.approx(g.span_m, rel=0.03)
