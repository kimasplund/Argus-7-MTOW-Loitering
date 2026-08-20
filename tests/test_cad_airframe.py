import pytest
from argus7.design.schema import load_design
from argus7.design.geometry import derive_wing, derive_booms, wing_le_x, wing_ac_x, tail_qc_x
from build123d import Location
from argus7.cad.model import (
    build_wing, build_fuselage, build_booms, build_tail, build_aircraft,
)


@pytest.fixture(scope="module")
def design(): return load_design("design/argus7_v1.yaml")


def test_promoted_geometry_fields_load_from_yaml(design):
    """Fix round 1 findings 1-3: fuselage.stations, tail.panel_aspect_ratio
    and booms.clearance_m used to be bare constants hardcoded in
    argus7/cad/model.py (build_fuselage, build_tail) and
    argus7/design/geometry.py (derive_booms). They are now design-contract
    YAML inputs -- pin the loaded values here so a regression can't
    silently reintroduce a Python-side constant."""
    assert design.fuselage.stations == [
        (0.00, 0.15), (0.08, 0.62), (0.22, 1.00),
        (0.55, 0.96), (0.80, 0.70), (1.00, 0.34),
    ]
    assert design.tail.panel_aspect_ratio == pytest.approx(3.0)
    assert design.booms.clearance_m == pytest.approx(0.15)


def test_fuselage_runs_along_x(design):
    """REGRESSION GUARD FOR DEFECT 1, other half: the fuselage must be the
    long axis in x while the wing is long in y. In the original SCAD both
    ran along y."""
    bb = build_fuselage(design).bounding_box()
    length = bb.max.X - bb.min.X
    width  = bb.max.Y - bb.min.Y
    assert length == pytest.approx(design.fuselage.length_m, rel=0.05)
    assert length > 4 * width


def test_wing_and_fuselage_axes_are_perpendicular(design):
    """The precise defect: wing long axis and fuselage long axis must differ.
    This is the headline regression guard of the whole project: the model
    being replaced had the wing spanning along the SAME axis as the
    fuselage (both ran along y), so the wing lay down the fuselage
    centreline instead of across it."""
    fus = build_fuselage(design).bounding_box()
    wing = build_wing(design).bounding_box()
    fus_long  = "X" if (fus.max.X - fus.min.X) > (fus.max.Y - fus.min.Y) else "Y"
    wing_long = "X" if (wing.max.X - wing.min.X) > (wing.max.Y - wing.min.Y) else "Y"
    assert fus_long == "X" and wing_long == "Y"


def test_derive_booms_matches_hand_computed_stations(design):
    """RULING P15: booms.length_m is deleted as a YAML input; it is derived
    from where the wing and tail actually sit, not from the defective
    SCAD's 3.2 m value (which cannot span wing to tail for this design).

    For design/argus7_v1.yaml these evaluate to exactly: x_fwd=0.5980,
    x_aft=4.2436, length_m=3.6456, y_station_m=0.6206."""
    bg = derive_booms(design)
    assert bg.x_fwd == pytest.approx(0.5980, abs=0.001)
    assert bg.x_aft == pytest.approx(4.2436, abs=0.001)
    assert bg.length_m == pytest.approx(3.6456, abs=0.01)
    assert bg.y_station_m == pytest.approx(0.6206, abs=0.001)


def test_booms_are_spaced_in_y_and_run_along_x(design):
    """Amended per RULING P15: length and separation are now derived
    quantities (3.6456 m and 1.2412 m respectively for this design), not
    the deleted booms.length_m YAML field.

    The Y bounding box of the built solid includes the boom's own
    diameter (each boom is a finite-radius cylinder straddling its
    centreline), so it is subtracted to recover the centreline-to-
    centreline separation before comparing against the tight ± 0.01
    target -- a loose relative tolerance would silently hide a real
    placement error the size of the boom radius."""
    bb = build_booms(design).bounding_box()
    bg = derive_booms(design)
    y_extent = (bb.max.Y - bb.min.Y) - design.booms.diameter_m
    assert y_extent == pytest.approx(2 * bg.y_station_m, rel=0.02)
    assert y_extent == pytest.approx(1.2412, abs=0.01)
    assert (bb.max.X - bb.min.X) == pytest.approx(bg.length_m, rel=0.02)
    assert (bb.max.X - bb.min.X) == pytest.approx(3.6456, abs=0.01)


def test_booms_carry_both_wing_and_tail(design):
    """RULING P15 structural guard: the boom must physically span from
    ahead of the wing root LE to aft of the tail quarter-chord -- this is
    the check the brief lacked, and the direct fix for the defect where
    the boom (x = -0.80..2.40) fell 0.8 m short of the tail (x = 3.2),
    carrying nothing."""
    bg = derive_booms(design)
    x_wing_le = wing_le_x(design)
    x_tail_qc = tail_qc_x(design)
    assert bg.x_fwd < x_wing_le
    assert bg.x_aft > x_tail_qc


def test_tail_quarter_chord_station_is_correct_and_carried(design):
    """RULING P2: tail arm is measured wing-AC -> tail-AC, the standard
    convention and the only reading under which the report's 3.2 m arm and
    its tail volume coefficient are the same quantity. For
    design/argus7_v1.yaml: x_wing_le=0.7480, mac_y=2.0229,
    x_wing_ac=0.8936, x_tail_qc=4.0936.

    Also checks the tail is actually carried by the boom: no gap between
    the boom's aft tip and the tail root, unlike the original defect's
    disjoint 0.8 m gap (boom ending at x=2.4, tail placed at absolute
    x=3.2)."""
    x_qc = tail_qc_x(design)
    assert wing_le_x(design) == pytest.approx(0.7480, abs=0.001)
    assert wing_ac_x(design) == pytest.approx(0.8936, abs=0.001)
    assert x_qc == pytest.approx(4.0936, abs=0.01)

    bg = derive_booms(design)
    assert bg.x_fwd < x_qc < bg.x_aft

    boom_bb = build_booms(design).bounding_box()
    tail_bb = build_tail(design).bounding_box()
    # Must overlap in x -- the boom's aft tip must reach into the tail's
    # own x-extent, not stop short of it.
    assert tail_bb.min.X <= boom_bb.max.X
    assert tail_bb.max.X >= boom_bb.min.X


def test_tail_sits_aft_of_the_wing(design):
    assert build_tail(design).bounding_box().min.X > 0.5 * design.tail.arm_m


def test_inverted_v_tail_dips_below_boom_line(design):
    """Inverted V means the panels angle downward from the boom."""
    assert build_tail(design).bounding_box().min.Z < 0.0


def test_full_aircraft_is_valid_and_within_envelope(design):
    ac = build_aircraft(design)
    g = derive_wing(design.wing)
    bb = ac.bounding_box()
    assert ac.is_valid  # RULING P12: is_valid is a property, not a method.
    assert (bb.max.Y - bb.min.Y) == pytest.approx(g.span_m, rel=0.03)
    assert (bb.max.X - bb.min.X) < 1.5 * design.fuselage.length_m + design.tail.arm_m


# --- FINAL REVIEW C1: the airframe must be ONE connected structure ----------
# The whole-branch review found build_aircraft returned a Compound of FOUR
# disjoint solids: (1) fuselage+wing+items, (2) port boom+tail panel,
# (3) starboard boom+tail panel, (4) the prop disc floating 50 mm aft. The
# booms -- which carry the entire tail load -- touched nothing at all.
#
# The cause was a hardcoded 0.05 m wing z-lift in build_aircraft (typed a
# second time in to_openscad), which put the wing's lower surface 25.9 mm
# ABOVE the boom's top surface at the boom station. Ruling P15 had fixed the
# same class of defect longitudinally (test_booms_carry_both_wing_and_tail
# checks only x_fwd < x_wing_le and x_aft > x_tail_qc); nobody owned the
# vertical axis, so the boom "carried" the wing and tail across an air gap.
#
# Nothing caught it because none of the existing guards can: is_valid is True
# for a disjoint Compound, and trimesh.is_watertight is a per-edge manifold
# test that four separate closed shells pass.

def _wing_lower_z_at_boom_station(design):
    """Measured lower-surface z of the assembled (lifted) wing at the boom
    centreline, taken from the built solid with a thin slab intersection --
    not recomputed from the section formulas, so this cannot agree with the
    model by sharing its arithmetic."""
    from build123d import Box, Location
    bg = derive_booms(design)
    wing = Location((wing_le_x(design), 0, design.wing.z_offset_m)) * build_wing(design)
    slab = Location((design.fuselage.length_m, bg.y_station_m, 0)) * \
        Box(4 * design.fuselage.length_m, 0.002, 4.0)
    return (wing & slab).bounding_box().min.Z


def test_wing_z_offset_reaches_both_geometry_paths(design, tmp_path):
    """C1: the wing z-lift was a bare 0.05 in build_aircraft AND a second
    hand-typed 0.05 in to_openscad. Perturbing the YAML field must move BOTH
    outputs -- a literal surviving in either path shows up here as an output
    that does not move. Behavioural rather than a source-text scan, so it
    still holds if the code is reformatted."""
    from argus7.cad.to_openscad import emit_openscad
    assert design.wing.z_offset_m == pytest.approx(0.008)
    moved = design.model_copy(deep=True)
    moved.wing.z_offset_m = design.wing.z_offset_m + 0.25

    base_z = build_aircraft(design, include_items=False).bounding_box().max.Z
    moved_z = build_aircraft(moved, include_items=False).bounding_box().max.Z
    assert moved_z - base_z == pytest.approx(0.25, abs=1e-6), (
        "build_aircraft ignored design.wing.z_offset_m")

    base_txt = emit_openscad(design, tmp_path / "base.scad").read_text()
    moved_txt = emit_openscad(moved, tmp_path / "moved.scad").read_text()
    assert f"{design.wing.z_offset_m:.5f}]) wing()" in base_txt
    assert f"{moved.wing.z_offset_m:.5f}]) wing()" in moved_txt, (
        "emit_openscad ignored design.wing.z_offset_m")


def test_wing_captures_the_booms(design):
    """C1: the boom must be structurally let into the wing's lower surface,
    with real interference volume -- not floating below an air gap.

    Relational, not pinned: the boom's top must sit inside the wing by a
    usable fraction of its own diameter, and the wing must not reach the boom
    centreline (which would mean the 90 mm tube is more than half swallowed
    by a wing only 73.7 mm thick at that station)."""
    r = design.booms.diameter_m / 2.0
    wing_lower_z = _wing_lower_z_at_boom_station(design)
    overlap = r - wing_lower_z
    assert overlap > 0.010, (
        f"wing lower surface z={wing_lower_z:.4f} m at the boom station is "
        f"only {overlap * 1000:.1f} mm into the boom top (z={r:.4f} m) -- "
        "the boom is not structurally captured")
    assert wing_lower_z > 0.0, (
        "the wing reaches below the boom centreline: a 90 mm tube cannot be "
        "more than half buried in a 73.7 mm thick wing section")


def test_structural_load_path_is_continuous(design):
    """C1: tail -> boom -> wing -> fuselage must be a chain of real solid
    intersections. Each link is checked explicitly; a single missing link is
    what produced four disjoint bodies.

    The boom deliberately does NOT touch the fuselage (y_station 0.62 m
    against a 0.24 m fuselage radius): in a twin-boom layout the booms are
    carried by the WING, so that zero is pinned here as intended, not as a
    second gap."""
    wing = Location((wing_le_x(design), 0, design.wing.z_offset_m)) * build_wing(design)
    fus, booms, tail = build_fuselage(design), build_booms(design), build_tail(design)
    assert (tail & booms).volume > 0, "tail panels are not carried by the booms"
    assert (wing & booms).volume > 0, "booms are not carried by the wing"
    assert (wing & fus).volume > 0, "wing is not attached to the fuselage"
    assert (booms & fus).volume == 0, (
        "booms unexpectedly touch the fuselage -- the twin-boom load path "
        "runs through the wing")


def test_analysis_solid_is_a_single_body(design):
    """C1: with the illustrative installed items excluded, the airframe is
    ONE solid. This is the assertion the review found missing: a Compound of
    four disconnected bodies satisfies is_valid and is_watertight alike."""
    ac = build_aircraft(design, include_items=False)
    assert len(ac.solids()) == 1, (
        f"airframe is {len(ac.solids())} disconnected bodies, not one")
    assert ac.is_valid is True


def test_installed_items_add_exactly_one_free_body(design):
    """C1: the pusher prop disc sits 50 mm aft of the fuselage tail and is
    illustrative, not structure, so it is allowed to stay free -- but only
    because include_items=False can now exclude it. Pin the count so a new
    floating body cannot be added unnoticed."""
    ac = build_aircraft(design, include_items=True)
    assert len(ac.solids()) == 2, (
        f"{len(ac.solids())} bodies with items included; expected 2 "
        "(airframe + free prop disc)")
