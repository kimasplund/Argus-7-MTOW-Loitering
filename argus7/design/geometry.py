from __future__ import annotations
import math
from dataclasses import dataclass

TOL = 1e-9

class ClosureError(Exception):
    """Raised when a design's stated geometry contradicts its derived geometry."""

@dataclass(frozen=True)
class WingGeometry:
    span_m: float
    chord_root_m: float
    chord_tip_m: float
    mac_m: float
    mac_y_m: float          # spanwise station of the MAC
    area_m2: float
    aspect_ratio: float

def derive_wing(wing) -> WingGeometry:
    S, AR, lam = wing.area_m2, wing.aspect_ratio, wing.taper_ratio
    b  = math.sqrt(AR * S)
    cr = S / ((b / 2.0) * (1.0 + lam))
    ct = lam * cr
    mac = (2.0 / 3.0) * cr * (1.0 + lam + lam**2) / (1.0 + lam)
    mac_y = (b / 6.0) * (1.0 + 2.0 * lam) / (1.0 + lam)
    return WingGeometry(b, cr, ct, mac, mac_y, S, AR)

def tail_volume_h(design) -> float:
    """Horizontal tail volume coefficient V_h = S_h * l_h / (S_w * MAC)."""
    g = derive_wing(design.wing)
    return design.tail.area_h_m2 * design.tail.arm_m / (g.area_m2 * g.mac_m)


def wing_le_x(design) -> float:
    """Fuselage-station x of the wing root leading edge -- the same placement
    build_aircraft uses.

    FINAL REVIEW I4: the fraction was a bare 0.22 typed here. The Task-4
    sweep promoted three constants and declared the hardcoded-geometry class
    closed; it missed this one, which is more load-bearing than any of the
    three, because wing_ac_x, tail_qc_x, all of derive_booms and the tail
    placement are all measured from it.

    COINCIDENCE, NOT A COUPLING: design.fuselage.stations also contains a
    0.22 entry (the max-diameter station). Nothing on record says these were
    ever meant to be the same station -- they are two independent assumptions
    that happen to share a value today, and they are deliberately left
    uncoupled.
    """
    return design.wing.x_le_frac * design.fuselage.length_m


def wing_ac_x(design) -> float:
    """Fuselage-station x of the wing's aerodynamic centre: root LE plus
    the sweep offset to the MAC station, plus 25% of the MAC."""
    g = derive_wing(design.wing)
    sweep = math.radians(design.wing.sweep_le_deg)
    return wing_le_x(design) + g.mac_y_m * math.tan(sweep) + 0.25 * g.mac_m


def tail_qc_x(design) -> float:
    """Fuselage-station x of the tail quarter-chord.

    RULING P2: design.tail.arm_m is the tail arm measured wing-AC to
    tail-AC -- the standard convention, and the only reading under which
    the report's 3.2 m arm and its tail volume coefficient (tail_volume_h,
    which also uses this arm_m against the wing's MAC) are the same
    quantity. It is NOT an absolute nose-referenced x -- treating it as
    one (as the superseded model did) leaves the tail floating past the
    end of the booms, carried by nothing.
    """
    return wing_ac_x(design) + design.tail.arm_m


@dataclass(frozen=True)
class TailPanelGeometry:
    """One panel of the inverted-V tail, plus the station it is placed at."""
    panel_area_m2: float        # true area of ONE panel, not the projection
    panel_span_m: float         # length along the panel, root to tip
    c_root_m: float
    c_tip_m: float
    mac_m: float
    x_le_m: float               # unswept: leading-edge x, constant across span
    dihedral_rad: float         # negative = inverted V
    y_tip_offset_m: float       # tip offset outboard of the boom
    z_tip_offset_m: float       # tip offset below the boom (negative)


def derive_tail_panel(design) -> TailPanelGeometry:
    """Inverted-V tail panel geometry, derived once for every consumer.

    FINAL REVIEW I5: argus7.cad.model.build_tail and
    argus7.cad.to_openscad.emit_openscad each computed panel_area,
    panel_span, c_root, mac and x_le independently, from the same inputs,
    kept in step only by a comment. They agreed; nothing enforced it. The
    wing never had this problem because both paths share section_stations --
    the tail did, because ruling P17 added tail emission after the maths was
    already written.

    design.tail.area_h_m2 is the PROJECTED horizontal area, so each of the
    two panels has true area S_h / (2 cos^2 gamma). The panels are unswept:
    design.tail declares no sweep angle, so the leading-edge x is constant
    across the span, and the panel's own quarter-MAC lands on tail_qc_x
    (RULING P2).
    """
    gam = math.radians(design.tail.dihedral_deg)          # negative = inverted
    lam = design.tail.taper_ratio
    panel_area = design.tail.area_h_m2 / (2.0 * math.cos(gam) ** 2)
    panel_span = math.sqrt(panel_area * design.tail.panel_aspect_ratio)
    c_root = 2 * panel_area / (panel_span * (1 + lam))
    c_tip = c_root * lam
    mac = (2.0 / 3.0) * c_root * (1.0 + lam + lam ** 2) / (1.0 + lam)
    x_le = tail_qc_x(design) - 0.25 * mac
    return TailPanelGeometry(
        panel_area_m2=panel_area, panel_span_m=panel_span,
        c_root_m=c_root, c_tip_m=c_tip, mac_m=mac, x_le_m=x_le,
        dihedral_rad=gam,
        y_tip_offset_m=panel_span * math.cos(gam),
        z_tip_offset_m=panel_span * math.sin(gam))


@dataclass(frozen=True)
class BoomGeometry:
    x_fwd: float
    x_aft: float
    length_m: float
    y_station_m: float


def derive_booms(design) -> BoomGeometry:
    """Twin-boom geometry, derived rather than a YAML input (RULING P15).

    booms.length_m was deleted as a Design field: its old value, 3.2 m,
    came from the defective SCAD this phase replaces, not from any report,
    and cannot physically span from the wing to the tail. Instead the boom
    is sized to actually carry both: it starts booms.clearance_m ahead of
    the wing root LE and ends booms.clearance_m aft of the tail
    quarter-chord.
    """
    g = derive_wing(design.wing)
    clearance = design.booms.clearance_m
    x_fwd = wing_le_x(design) - clearance
    x_aft = tail_qc_x(design) + clearance
    y_station_m = design.booms.y_station_frac * (g.span_m / 2.0)
    return BoomGeometry(x_fwd=x_fwd, x_aft=x_aft,
                         length_m=x_aft - x_fwd, y_station_m=y_station_m)

def check_closure(design) -> None:
    g = derive_wing(design.wing)
    identities = {
        "S = (b/2)(c_root + c_tip)": g.area_m2 - (g.span_m / 2) * (g.chord_root_m + g.chord_tip_m),
        "AR = b^2 / S":              g.aspect_ratio - g.span_m**2 / g.area_m2,
        "c_tip = taper * c_root":    g.chord_tip_m - design.wing.taper_ratio * g.chord_root_m,
    }
    for name, residual in identities.items():
        if abs(residual) > TOL:
            raise ClosureError(f"{name} violated by {residual:.3e}")
    assert_ = design.wing.chord_root_m_assert
    if assert_ is not None and abs(assert_ - g.chord_root_m) > 1e-3:
        raise ClosureError(
            f"stated chord_root_m_assert={assert_:.4f} contradicts derived "
            f"{g.chord_root_m:.4f} from S={g.area_m2}, AR={g.aspect_ratio}, "
            f"taper={design.wing.taper_ratio}")
