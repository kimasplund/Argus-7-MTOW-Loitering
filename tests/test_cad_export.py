import re
import numpy as np
import pytest, trimesh
from pathlib import Path
from argus7.design.schema import load_design
from argus7.design.geometry import derive_wing
from argus7.cad.model import build_aircraft
from argus7.cad.export import export_model, check_watertight
from argus7.cad.to_openscad import emit_openscad


@pytest.fixture(scope="module")
def design(): return load_design("design/argus7_v1.yaml")


@pytest.fixture(scope="module")
def exported(design, tmp_path_factory):
    return export_model(design, tmp_path_factory.mktemp("cad"))


@pytest.fixture(scope="module")
def rendered_openscad_stl(design, tmp_path_factory):
    """Emit the .scad and render it with openscad ONCE, shared by every test
    that needs the actual rendered geometry rather than just the emitted
    text -- avoids paying openscad's render cost per assertion."""
    import shutil, subprocess
    if shutil.which("openscad") is None:
        pytest.skip("openscad not installed")
    tmp = tmp_path_factory.mktemp("scadrender")
    p = emit_openscad(design, tmp / "m.scad")
    stl = tmp / "m.stl"
    r = subprocess.run(["openscad", "-o", str(stl), str(p)],
                       capture_output=True, timeout=300)
    assert r.returncode == 0, r.stderr.decode()[:2000]
    return trimesh.load(str(stl))


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


def test_openscad_output_parses(rendered_openscad_stl):
    """openscad renders the emitted file cleanly to a non-empty mesh."""
    assert len(rendered_openscad_stl.faces) > 0


def test_openscad_rendered_stl_is_spanwise_in_y(rendered_openscad_stl, design):
    """RULING P5 regression guard: the brief's original section() module drew
    the airfoil in the XY plane and extruded along Z, so hulling consecutive
    stations swept vertically instead of spanwise -- span would show up on Z,
    not Y. This proves the fix holds in the actual openscad-rendered
    geometry, not merely in the emitted .scad text."""
    g = derive_wing(design.wing)
    y_extent = rendered_openscad_stl.bounds[1][1] - rendered_openscad_stl.bounds[0][1]
    assert y_extent == pytest.approx(g.span_m, rel=0.03)


# --- FIX ROUND 1 -------------------------------------------------------------
# Review findings 1-4. Finding 1 is the important one: the emitted wing twist
# was sign-inverted (a second occurrence of the same washout/washin sign bug
# RULING P4 fixed in argus7.cad.airfoil_coords.scale_airfoil for Task 2).
# Findings 2 and 3 guard the two judgment calls flagged in the original
# report (STEP unit=Unit.M, STL post-repair) that were, until now, entirely
# untested -- either one silently regressing would be invisible to every
# other test in this file. Finding 4 guards the fuselage hull-of-spheres
# overshoot fix.

def test_openscad_rendered_wing_tip_shows_washout(rendered_openscad_stl, design):
    """FINDING 1: mirrors test_negative_twist_produces_washout in
    test_airfoil_coords.py (RULING P4). OpenSCAD's rotate([0,0,twist]) is a
    CCW rotation in its local XY plane -- the opposite sense from
    scale_airfoil's own rotation (xr = xc*ct + zc*st; zr = -xc*st + zc*ct),
    which was deliberately chosen so a negative twist (this design's
    twist_tip_deg = -3.0) raises the trailing edge above the leading edge
    (washout). Emitting the raw twist angle reproduced the same sign bug a
    second time, backwards: TE below LE (washin) instead of above.

    At the wing tip (max Y in the rendered mesh), the trailing edge (max
    local X within that station) must sit ABOVE the leading edge (min local
    X) in Z."""
    g = derive_wing(design.wing)
    assert design.wing.twist_tip_deg < 0, "this guard assumes washout twist"
    m = rendered_openscad_stl
    y_max = m.bounds[1][1]
    tip = m.vertices[m.vertices[:, 1] > y_max - 0.05]      # wing-tip band only
    assert len(tip) > 0
    le = tip[np.argmin(tip[:, 0])]
    te = tip[np.argmax(tip[:, 0])]
    assert te[2] > le[2], (
        f"tip trailing edge z={te[2]:.5f} is not above leading edge "
        f"z={le[2]:.5f} -- washout sign is inverted (washin instead)")


def _step_bbox_m(step_path: Path) -> tuple[float, float, float]:
    """Parse a STEP file's own declared SI_UNIT length prefix and
    CARTESIAN_POINT coordinates directly from the file text, and return the
    (x, y, z) bounding-box extents converted to metres. Deliberately
    independent of trimesh/build123d re-loading the file: it reads exactly
    what the file itself declares and contains, so a silent unit-scale
    regression cannot hide behind a loader that "helpfully" reinterprets
    units the same way export_model does."""
    text = step_path.read_text(errors="ignore")
    unit_match = re.search(r"SI_UNIT\(\s*\.([A-Z]+)\.\s*,\s*\.METRE\.\s*\)", text)
    prefix = unit_match.group(1) if unit_match else None
    scale = {None: 1.0, "MILLI": 1e-3, "CENTI": 1e-2, "DECI": 1e-1}[prefix]
    pts = re.findall(
        r"CARTESIAN_POINT\('[^']*',\(\s*([-\d.eE+]+)\s*,\s*([-\d.eE+]+)\s*,\s*([-\d.eE+]+)\s*\)\)",
        text)
    assert pts, f"no CARTESIAN_POINT entities found in {step_path}"
    xs = [float(p[0]) for p in pts]
    ys = [float(p[1]) for p in pts]
    zs = [float(p[2]) for p in pts]
    return ((max(xs) - min(xs)) * scale,
            (max(ys) - min(ys)) * scale,
            (max(zs) - min(zs)) * scale)


def test_step_physical_scale_matches_design(exported, design):
    """FINDING 2: guard export_model's unit=Unit.M against a silent
    regression. Phase 4 meshes this STEP file for RANS CFD; without
    unit=Unit.M, build123d writes this design's raw metre-scale numbers
    unscaled under a file that still declares .MILLI.METRE. -- a 1000x-too-
    small model (measured directly: this design's span would read as
    0.00926 m instead of 9.2628 m) that would give a Reynolds number
    ~1000x wrong while looking entirely plausible and being nearly
    untraceable downstream. Parses the STEP file's own text (see
    _step_bbox_m) rather than trusting a loader, and cross-checks against
    both the ground-truth design span AND the independently-exported STL's
    bounding box (a different exporter code path with no unit parameter at
    all, so it cannot share a unit-scale bug with the STEP path)."""
    g = derive_wing(design.wing)
    stl_mesh = trimesh.load(exported["stl"])
    stl_x_ext = stl_mesh.bounds[1][0] - stl_mesh.bounds[0][0]
    stl_y_ext = stl_mesh.bounds[1][1] - stl_mesh.bounds[0][1]

    x_ext, y_ext, _z_ext = _step_bbox_m(exported["step"])
    assert y_ext == pytest.approx(g.span_m, rel=0.03)
    assert y_ext == pytest.approx(stl_y_ext, rel=0.03)
    assert x_ext == pytest.approx(stl_x_ext, rel=0.05)
    assert x_ext > design.fuselage.length_m * 0.9, (
        f"model x-extent {x_ext:.4f} m is not physically plausible against "
        f"a {design.fuselage.length_m} m fuselage -- looks like a scale error")


def test_stl_repair_preserves_volume(exported, design):
    """FINDING 3: guard export.py's post-hoc STL repair (_clean_stl_in_place,
    added to fix test_stl_is_watertight against a real OCCT STL-mesher
    artifact at the gimbal/chute boolean-fuse seam). Post-hoc mesh repair is
    exactly how a genuine geometry defect could hide behind a passing
    is_watertight assertion: if the fuse-seam artifact ever grew from a
    zero-area sliver into a real hole, trimesh.repair.fill_holes would
    silently patch it and every other test in this file would still pass.
    Tying the repaired mesh's enclosed volume to the un-repaired B-rep
    solid's own .volume (computed from the actual BREP, not from any mesh)
    means a genuine hole -- which would measurably change the enclosed
    volume -- cannot hide behind watertightness alone."""
    ac = build_aircraft(design)
    m = trimesh.load(exported["stl"])
    assert m.volume == pytest.approx(ac.volume, rel=0.01)


def test_openscad_fuselage_nose_does_not_overshoot(rendered_openscad_stl):
    """FINDING 4: the fuselage's first station is x=0 (the nose), and
    nothing else in the assembly extends forward of it -- wing_le_x,
    derive_booms().x_fwd and the tail all sit aft of x=0 -- so the rendered
    model's own X-minimum is a direct proxy for the fuselage module's own
    behaviour. The old hull()-of-spheres chain bulged past x=0 by the nose
    sphere's own radius (measured: X min == -0.0360, a 3.6 cm overshoot
    ahead of the nose); hulling thin discs instead should land within
    ~1 mm of the true station."""
    x_min = rendered_openscad_stl.bounds[0][0]
    assert x_min == pytest.approx(0.0, abs=0.01)


# --- FINAL REVIEW C1, end to end -------------------------------------------

def test_exported_analysis_mesh_is_one_connected_body(design, tmp_path):
    """The C1 assertion carried all the way to the artifact Phase 2 actually
    consumes. `trimesh.is_watertight` (test_stl_is_watertight above) is a
    per-edge manifold test: four separate closed shells pass it, which is why
    the four-disconnected-bodies defect survived every previous check. Split
    the mesh into connected components instead and count them.

    include_items=True keeps the illustrative prop disc, which genuinely
    floats 50 mm aft of the fuselage -- two components. include_items=False
    is the analysis solid and must be exactly one."""
    paths = export_model(design, tmp_path, include_items=False)
    m = trimesh.load(paths["stl"])
    parts = m.split(only_watertight=False)
    assert len(parts) == 1, (
        f"analysis STL is {len(parts)} disconnected shells, not one")
    assert m.is_watertight, "analysis STL is not watertight without repair"


def test_default_export_has_only_the_prop_disc_free(exported):
    """Pin the committed deliverable's component count so a NEW floating body
    cannot be introduced unnoticed behind a passing is_watertight."""
    parts = trimesh.load(exported["stl"]).split(only_watertight=False)
    assert len(parts) == 2, (
        f"{len(parts)} disconnected shells in the default export; expected 2 "
        "(airframe + illustrative prop disc)")
