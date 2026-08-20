import math, pytest
import numpy as np
from argus7.design.schema import load_design
from argus7.design.geometry import derive_wing
from argus7.cad.model import build_wing, section_stations, _section_coords
from argus7.cad.airfoil_coords import max_thickness

@pytest.fixture(scope="module")
def design(): return load_design("design/argus7_v1.yaml")

@pytest.fixture(scope="module")
def wing(design): return build_wing(design)

def test_wing_spans_along_y_not_x(wing, design):
    """REGRESSION GUARD FOR DEFECT 1: the wing must span across the airframe,
    not along it. The original SCAD spanned the wing along the fuselage axis."""
    bb = wing.bounding_box()
    span_extent  = bb.max.Y - bb.min.Y
    chord_extent = bb.max.X - bb.min.X
    assert span_extent > 8.0, f"wing spans only {span_extent:.2f} m in y"
    assert span_extent > 5 * chord_extent, "wing is not spanwise-dominant in y"

def test_wing_span_matches_derived_geometry(wing, design):
    g = derive_wing(design.wing)
    bb = wing.bounding_box()
    assert (bb.max.Y - bb.min.Y) == pytest.approx(g.span_m, rel=0.02)

def test_wing_is_symmetric_about_centreline(wing):
    bb = wing.bounding_box()
    assert bb.max.Y == pytest.approx(-bb.min.Y, abs=1e-3)

def test_wing_planform_area_matches_spec(wing, design):
    """Loft volume / span / mean-thickness should recover S within meshing tolerance.

    RULING P13 (as given): brief's rel=0.15 is far too loose -- +16% was the
    original defect this phase exists to fix; use rel=0.03.

    DEVIATION BEYOND THE GIVEN RULINGS: the brief's formula divides by a
    hardcoded 0.68 "typical airfoil" shape factor. Measured directly against
    this design (design/argus7_v1.yaml, airfoil FX63-137), that constant is
    wrong: the section's actual normalised cross-sectional area / max
    thickness ratio is ~0.606, not 0.68. With 0.68 hardcoded, approx_area
    comes out ~3.48 m^2 against the true 3.9 m^2 -- a -10.8% bias that fails
    even the loosened rel=0.03 guard, and would keep failing regardless of
    n_sections (verified n=5, 9, 21 all give an identical wing.volume, so
    this is not a meshing artefact).
    This is not an implementation defect: an independent analytic check
    (2 * A0 * semispan * c_root^2 * (1+lambda+lambda^2)/3, where A0 is the
    section's own shoelace area) reproduces wing.volume to 6 significant
    figures, proving the loft is geometrically exact. Only the brief's
    hardcoded constant was wrong for this specific section. Computing the
    shape factor from the actual loaded coordinates instead (rather than a
    hardcoded generic constant) recovers the true area to +0.09% -- almost
    exactly ruling P13's claimed +0.1% accuracy -- which is presumably what
    P13's own verification measured against, rather than the literal 0.68
    constant against this project's actual airfoil. This also matches the
    project-wide convention that no module hardcodes a chord/area/thickness
    figure: the shape factor is derived from data, not typed in.
    """
    g = derive_wing(design.wing)
    coords = _section_coords(design.wing.airfoil)
    t_max = max_thickness(coords)
    x, y = coords[:, 0], coords[:, 1]
    a0 = 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))  # shoelace area, unit chord
    shape_factor = a0 / t_max
    approx_area = wing.volume / (shape_factor * design.wing.thickness_ratio * g.mac_m)
    assert approx_area == pytest.approx(g.area_m2, rel=0.03)

def test_wing_solid_is_valid(wing):
    # RULING P12: is_valid is a PROPERTY in build123d 0.11.1, not a method.
    assert wing.is_valid
    assert wing.volume > 0

def test_stations_apply_linear_taper_and_washout(design):
    """FINAL REVIEW I3 moved two pinned values here, because the wing now
    actually carries its declared 2 deg rig incidence:

      root twist  0.0 rad          -> radians(2.0)  = +0.0349066 rad
      tip twist   radians(-3.0)    -> radians(-1.0) = -0.0174533 rad

    Both moved for the same single physical reason: every section's geometric
    angle is offset by the constant rig incidence. The washout DISTRIBUTION
    is untouched -- tip minus root is still exactly twist_tip_deg -- so the
    assertions are written relationally against incidence_deg and
    twist_tip_deg rather than re-pinned as fresh literals."""
    g = derive_wing(design.wing)
    st = section_stations(design, 9)
    root, tip = st[0], st[-1]
    assert root[1] == pytest.approx(g.chord_root_m, rel=1e-6)
    assert tip[1]  == pytest.approx(g.chord_tip_m,  rel=1e-6)
    assert root[2] == pytest.approx(math.radians(design.wing.incidence_deg), rel=1e-6)
    assert tip[2]  == pytest.approx(
        math.radians(design.wing.incidence_deg + design.wing.twist_tip_deg), rel=1e-6)
    # Sweep coverage: no test anywhere else touches x_le / sweep -- pin the
    # tip station's leading-edge x against the sweep formula directly.
    assert tip[3] == pytest.approx(
        tip[0] * math.tan(math.radians(design.wing.sweep_le_deg)), rel=1e-6)

def test_dihedral_raises_the_tip(design, wing):
    bb = wing.bounding_box()
    g = derive_wing(design.wing)
    expected_rise = (g.span_m / 2) * math.tan(math.radians(design.wing.dihedral_deg))
    assert bb.max.Z > 0.5 * expected_rise


# --- FINAL REVIEW I3: wing.incidence_deg must actually reach the geometry ---
# Before this fix, `grep -rn incidence argus7/` returned exactly ONE hit: the
# schema declaration. section_stations set twist = f * twist_tip_deg, so the
# root station's twist was 0 and the built wing had 0 deg incidence, not the
# 2.0 the design file declares. The provenance test could not catch it: it
# checks that a tag EXISTS, not that the field ARRIVES anywhere.
#
# This matters in Phase 2: AVL is generated from the same YAML and will apply
# incidence; the STEP that SU2 meshes would not have. That is a 2 deg
# disagreement between the two sides of the three-way C_D0 validation gate
# whose threshold is 15% -- about the size of the discrepancy the gate exists
# to detect.

def test_incidence_reaches_the_section_stations(design):
    """Root twist is the incidence; tip twist is incidence + washout."""
    inc = math.radians(design.wing.incidence_deg)
    tip_tw = math.radians(design.wing.incidence_deg + design.wing.twist_tip_deg)
    st = section_stations(design, 9)
    assert design.wing.incidence_deg != 0.0, "this guard assumes non-zero incidence"
    assert st[0][2] == pytest.approx(inc, rel=1e-12)
    assert st[-1][2] == pytest.approx(tip_tw, rel=1e-12)
    # the washout increment between root and tip is unchanged by incidence
    assert st[-1][2] - st[0][2] == pytest.approx(
        math.radians(design.wing.twist_tip_deg), rel=1e-12)


def test_built_wing_root_section_is_at_the_declared_incidence(design, wing):
    """Ground truth, measured from the built solid rather than the station
    list: at the root the trailing edge must sit BELOW the leading edge by
    c_root * sin(incidence) -- positive incidence is nose-up, which by
    scale_airfoil's convention (RULING P4) drops the TE. This is the geometry
    the STEP export hands to Phase 2's mesher."""
    from build123d import Box, Location
    g = derive_wing(design.wing)
    slab = Location((g.chord_root_m, 0.002, 0)) * Box(4 * g.chord_root_m, 0.001, 2.0)
    root = wing & slab
    verts = [(v.X, v.Z) for v in root.vertices()]
    le_z = min(verts, key=lambda p: p[0])[1]
    te_z = max(verts, key=lambda p: p[0])[1]
    expected_drop = g.chord_root_m * math.sin(math.radians(design.wing.incidence_deg))
    assert le_z - te_z == pytest.approx(expected_drop, abs=1e-3), (
        f"root TE sits {(le_z - te_z) * 1000:.2f} mm below the LE; "
        f"{design.wing.incidence_deg} deg incidence requires "
        f"{expected_drop * 1000:.2f} mm")
