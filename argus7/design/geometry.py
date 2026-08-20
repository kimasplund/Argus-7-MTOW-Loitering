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
