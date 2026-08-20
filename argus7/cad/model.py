from __future__ import annotations
import math
import numpy as np
from build123d import Part, Polyline, make_face, loft, Plane, Vector

from argus7.design.geometry import derive_wing
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


def _section_face(design, y, chord, twist, x_le, dihedral_rad, coords):
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
    faces = [_section_face(design, y, c, t, x, dihedral, coords)
             for (y, c, t, x) in section_stations(design, n_sections)]
    starboard = loft(faces)
    port = starboard.mirror(Plane.XZ)
    return starboard + port
