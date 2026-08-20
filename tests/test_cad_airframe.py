import pytest
from argus7.design.schema import load_design
from argus7.design.geometry import derive_wing, derive_booms, wing_le_x, wing_ac_x, tail_qc_x
from argus7.cad.model import (
    build_wing, build_fuselage, build_booms, build_tail, build_aircraft,
)


@pytest.fixture(scope="module")
def design(): return load_design("design/argus7_v1.yaml")


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
