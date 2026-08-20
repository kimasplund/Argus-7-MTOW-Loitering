from __future__ import annotations
import math
import numpy as np
from build123d import (
    Part, Polyline, make_face, loft, Plane, Vector, Circle,
    Cylinder, Sphere, Box, Location,
)

from argus7.design.geometry import (
    derive_wing, derive_booms, derive_tail_panel, wing_le_x,
)
from argus7.cad.airfoil_coords import load_airfoil, naca4, scale_airfoil


def _section_coords(name: str) -> np.ndarray:
    return naca4(name[4:]) if name.upper().startswith("NACA") else load_airfoil(name)


def section_stations(design, n: int = 9):
    """(y, chord, twist_rad, x_le) at n stations from root to tip.

    twist is the section's TOTAL geometric angle: the wing's rig incidence
    (design.wing.incidence_deg, constant across the span) plus the linear
    washout distribution (design.wing.twist_tip_deg, 0 at the root and full
    at the tip). Positive is nose-up; each section is rotated about its own
    leading edge by argus7.cad.airfoil_coords.scale_airfoil.

    FINAL REVIEW I3: incidence_deg used to be declared in the schema and read
    by nothing at all -- `grep -rn incidence argus7/` returned exactly one
    hit, the declaration itself -- so the built wing had 0 deg incidence
    while the design file declared 2. The provenance test could not catch
    that: it checks a tag EXISTS, not that a field ARRIVES. Phase 2 generates
    AVL from this same YAML and would apply the incidence, while the STEP
    that SU2 meshes would not have carried it -- a 2 deg disagreement across
    the two sides of a three-way C_D0 gate whose threshold is 15%.
    """
    g = derive_wing(design.wing)
    semi = g.span_m / 2.0
    sweep = math.radians(design.wing.sweep_le_deg)
    incidence = math.radians(design.wing.incidence_deg)
    out = []
    for i in range(n):
        f = i / (n - 1)                                  # 0 at root, 1 at tip
        y = f * semi
        chord = g.chord_root_m + f * (g.chord_tip_m - g.chord_root_m)
        twist = incidence + f * math.radians(design.wing.twist_tip_deg)
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
    faces = [Plane(origin=(xf * L, 0, 0), z_dir=(1, 0, 0)) * Circle(max(rf * R, 1e-3))
             for xf, rf in design.fuselage.stations]
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

    FINAL REVIEW I5: the panel's own area/span/chord/MAC/station arithmetic
    used to live here AND, independently, in argus7.cad.to_openscad, kept in
    step only by a comment. Both now call
    argus7.design.geometry.derive_tail_panel, which is where that arithmetic
    (and its "area_h_m2 is the PROJECTED area" and "unswept" reasoning) is
    documented.

    DESIGN NOTE (informational, not actionable here): with 42 deg anhedral
    the inverted-V tail tips sit well below the boom line, below the
    fuselage keel. Ground clearance on launch is a Phase-2 concern.
    """
    y_boom = derive_booms(design).y_station_m
    tp = derive_tail_panel(design)
    coords = _section_coords(design.tail.airfoil)
    parts = []
    for sgn in (+1, -1):
        faces = []
        for f in (0.0, 1.0):
            chord = tp.c_root_m + f * (tp.c_tip_m - tp.c_root_m)
            y = sgn * (y_boom + f * tp.y_tip_offset_m)
            z = f * tp.z_tip_offset_m
            pts = scale_airfoil(coords, chord, 0.0, (tp.x_le_m, y, z))
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


def build_aircraft(design, include_items: bool = True) -> Part:
    """Assembled model. The wing root LE sits at wing_le_x(design) aft and
    design.wing.z_offset_m above the fuselage centreline.

    FINAL REVIEW C1: both of those placements used to be bare literals here
    (0.22 * length inside wing_le_x, and a 0.05 z-lift typed here and again
    in argus7.cad.to_openscad). The z-lift in particular held the wing's
    lower surface 25.8 mm above the top of the booms, so the assembly was
    four disconnected bodies -- booms and tail carried by nothing -- while
    still reporting is_valid True and a watertight STL, because neither test
    can see across a gap between separate closed shells.

    include_items=False returns the STRUCTURE alone: fuselage + wing + booms
    + tail, which must be a single solid (see
    tests/test_cad_airframe.py::test_analysis_solid_is_a_single_body). The
    illustrative gimbal/chute/antenna/prop of build_installed_items are not
    design-contract geometry, and the pusher prop disc genuinely floats 50 mm
    aft of the fuselage; analysis paths that must not see free bodies should
    pass include_items=False.
    """
    wing = Location((wing_le_x(design), 0, design.wing.z_offset_m)) \
        * build_wing(design)
    airframe = wing + build_fuselage(design) + build_booms(design) \
                    + build_tail(design)
    if not include_items:
        return airframe
    return airframe + build_installed_items(design)
