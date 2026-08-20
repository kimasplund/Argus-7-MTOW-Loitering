from __future__ import annotations
import math
import numpy as np
from build123d import (
    Part, Polyline, make_face, loft, Plane, Vector, Circle,
    Cylinder, Sphere, Box, Location,
)

from argus7.design.geometry import derive_wing, derive_booms, wing_le_x, tail_qc_x
from argus7.cad.airfoil_coords import load_airfoil, naca4, scale_airfoil


def _section_coords(name: str) -> np.ndarray:
    return naca4(name[4:]) if name.upper().startswith("NACA") else load_airfoil(name)


def section_stations(design, n: int = 9):
    """(y, chord, twist_rad, x_le) at n stations from root to tip."""
    g = derive_wing(design.wing)
    semi = g.span_m / 2.0
    sweep = math.radians(design.wing.sweep_le_deg)
    out = []
    for i in range(n):
        f = i / (n - 1)                                  # 0 at root, 1 at tip
        y = f * semi
        chord = g.chord_root_m + f * (g.chord_tip_m - g.chord_root_m)
        twist = f * math.radians(design.wing.twist_tip_deg)
        x_le = y * math.tan(sweep)
        out.append((y, chord, twist, x_le))
    return out


def _section_face(y, chord, twist, x_le, dihedral_rad, coords):
    z = y * math.tan(dihedral_rad)
    pts = scale_airfoil(coords, chord, twist, (x_le, y, z))
    verts = [Vector(*p) for p in pts]
    if (verts[0] - verts[-1]).length > 1e-9:
        verts.append(verts[0])                            # close the section
    return make_face(Polyline(*verts))


def build_wing(design, n_sections: int = 9) -> Part:
    """Full wing, both halves, lofted through real airfoil sections.

    Origin is the root leading edge. x aft, y starboard, z up.
    """
    coords = _section_coords(design.wing.airfoil)
    dihedral = math.radians(design.wing.dihedral_deg)
    faces = [_section_face(y, c, t, x, dihedral, coords)
             for (y, c, t, x) in section_stations(design, n_sections)]
    starboard = loft(faces)
    port = starboard.mirror(Plane.XZ)
    return starboard + port


def build_fuselage(design) -> Part:
    """Pod along +x: nose at x=0, engine/prop end at x=length. Lofted from
    circular stations so it is a true solid of revolution, not a sphere
    hull. loft blends smoothly between stations and can bulge slightly
    beyond the max declared radius; that is expected."""
    L, R = design.fuselage.length_m, design.fuselage.max_diameter_m / 2.0
    # (x_fraction, radius_fraction) - nose, max section, aft taper to engine
    stations = [(0.00, 0.15), (0.08, 0.62), (0.22, 1.00), (0.55, 0.96),
                (0.80, 0.70), (1.00, 0.34)]
    faces = [Plane(origin=(xf * L, 0, 0), z_dir=(1, 0, 0)) * Circle(max(rf * R, 1e-3))
             for xf, rf in stations]
    return loft(faces)


def build_booms(design) -> Part:
    """Twin booms: spaced in y, running along x.

    RULING P15: length_m is derived (argus7.design.geometry.derive_booms),
    not a YAML input -- the boom spans from just ahead of the wing root LE
    to just aft of the tail quarter-chord, so it actually carries both.
    """
    bg = derive_booms(design)
    r = design.booms.diameter_m / 2.0
    boom = Cylinder(radius=r, height=bg.length_m, rotation=(0, 90, 0))
    x_mid = (bg.x_fwd + bg.x_aft) / 2.0
    starboard = Location((x_mid, bg.y_station_m, 0)) * boom
    port = Location((x_mid, -bg.y_station_m, 0)) * boom
    return starboard + port


def build_tail(design) -> Part:
    """Inverted-V tail: two panels angled downward from the boom ends.

    RULING P2: the tail arm is measured wing-AC to tail-AC
    (argus7.design.geometry.tail_qc_x), not as an absolute nose-referenced
    x -- the panels' own quarter-MAC is placed at that station, so the
    report's 3.2 m arm and its tail volume coefficient measure the same
    quantity, and the tail is actually carried by the boom rather than
    floating past its aft end.

    area_h_m2 is the projected horizontal area, so each panel's true area
    is S_h / (2 cos^2(dihedral)). The panels are unswept: the leading edge
    x is constant across the span, matching the fact that design.tail
    declares no sweep angle.

    DESIGN NOTE (informational, not actionable here): with 42 deg anhedral
    the inverted-V tail tips sit well below the boom line, below the
    fuselage keel. Ground clearance on launch is a Phase-2 concern.
    """
    g = derive_wing(design.wing)
    y_boom = design.booms.y_station_frac * (g.span_m / 2.0)
    gam = math.radians(design.tail.dihedral_deg)          # negative = inverted
    panel_area = design.tail.area_h_m2 / (2.0 * math.cos(gam) ** 2)
    lam = design.tail.taper_ratio
    panel_span = math.sqrt(panel_area * 3.0)              # AR 3 tail panel
    c_root = 2 * panel_area / (panel_span * (1 + lam))
    mac = (2.0 / 3.0) * c_root * (1.0 + lam + lam ** 2) / (1.0 + lam)
    x_le = tail_qc_x(design) - 0.25 * mac                 # unswept: LE constant across span
    coords = _section_coords(design.tail.airfoil)
    parts = []
    for sgn in (+1, -1):
        faces = []
        for f in (0.0, 1.0):
            chord = c_root * (1 + f * (lam - 1))
            span_off = f * panel_span
            y = sgn * (y_boom + span_off * math.cos(gam))
            z = span_off * math.sin(gam)
            pts = scale_airfoil(coords, chord, 0.0, (x_le, y, z))
            verts = [Vector(*p) for p in pts]
            if (verts[0] - verts[-1]).length > 1e-9:
                verts.append(verts[0])
            faces.append(make_face(Polyline(*verts)))
        parts.append(loft(faces))
    return parts[0] + parts[1]


def build_installed_items(design) -> Part:
    """EO/IR gimbal, parachute bay hump, pusher prop disc, comms antenna
    blade. These are illustrative CAD placements, not design-contract
    geometry -- there is no YAML field for gimbal/chute/antenna position."""
    L, R = design.fuselage.length_m, design.fuselage.max_diameter_m / 2.0
    gimbal = Location((0.55 * R + 0.30, 0, -R - 0.06)) * Sphere(0.15)
    chute = Location((0.95, 0, R * 0.75)) * Sphere(0.14)
    d = design.propulsion.prop_diameter_m
    prop = Location((L + 0.06, 0, 0)) * Cylinder(radius=d / 2, height=0.02,
                                                  rotation=(0, 90, 0))
    ant = Location((1.45, 0, -R - 0.08)) * Box(0.18, 0.012, 0.14)
    return gimbal + chute + prop + ant


def build_aircraft(design) -> Part:
    """Assembled model. Wing root LE is placed at 22% of fuselage length --
    the same x_wing_le used by derive_booms and tail_qc_x."""
    wing = Location((wing_le_x(design), 0, 0.05)) * build_wing(design)
    return wing + build_fuselage(design) + build_booms(design) \
                + build_tail(design) + build_installed_items(design)
