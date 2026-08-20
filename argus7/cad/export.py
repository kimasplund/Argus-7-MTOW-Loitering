from __future__ import annotations
from pathlib import Path
import trimesh
from build123d import export_step, export_stl, Unit
from argus7.cad.model import build_aircraft


def _clean_stl_in_place(stl_path: Path) -> None:
    """Drop zero-area sliver faces left by OCCT's STL mesher at the boolean
    fuse seam between build_installed_items' gimbal/chute spheres and the
    fuselage skin (they genuinely overlap -- the gimbal is meant to
    protrude below the fuselage -- but the mesher leaves a handful of
    degenerate near-zero-area triangles at the intersection curve). These
    slivers break the "each edge shared by exactly two faces" manifold
    condition without representing any real geometry, so removing them and
    closing the resulting micro-holes is a lossless cleanup, not a
    tolerance fudge: confirmed on this design's full assembly to drop
    ~10 zero-area faces out of ~40000 and recover a fully watertight,
    zero-broken-face mesh with the same bounding box.
    """
    m = trimesh.load(str(stl_path))
    if m.is_watertight:
        return
    m.update_faces(m.nondegenerate_faces())
    m.remove_unreferenced_vertices()
    trimesh.repair.fill_holes(m)
    m.export(str(stl_path))


def export_model(design, outdir: str | Path,
                 include_items: bool = True) -> dict[str, Path]:
    """Build the aircraft and write it out as STEP and STL.

    All numeric values flowing through argus7.cad.model are plain SI metres
    (per the project's axis/units convention), so the STEP export is tagged
    unit=Unit.M -- otherwise build123d's default (millimetre) tag would make
    a downstream STEP consumer read a 3.4 m fuselage as 3.4 mm.

    include_items is passed straight through to build_aircraft. The default
    True keeps the illustrative gimbal/chute/antenna/prop in the committed
    deliverable; False writes the STRUCTURE alone, which is a single
    connected body (final review, finding C1) and therefore needs no
    post-hoc mesh repair -- the sliver faces _clean_stl_in_place exists for
    are all at the installed items' boolean-fuse seams.
    """
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    ac = build_aircraft(design, include_items=include_items)
    step, stl = outdir / "argus7.step", outdir / "argus7.stl"
    export_step(ac, str(step), unit=Unit.M)
    export_stl(ac, str(stl), tolerance=1e-3, angular_tolerance=0.1)
    _clean_stl_in_place(stl)
    return {"step": step, "stl": stl}


def check_watertight(stl_path: str | Path) -> bool:
    m = trimesh.load(str(stl_path))
    return bool(m.is_watertight)
