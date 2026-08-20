from __future__ import annotations
import subprocess, shutil
from pathlib import Path

# (rx, ry, rz) rotation angles passed to OpenSCAD's gimbal camera
# (--camera=tx,ty,tz,rx,ry,rz,dist). With --autocenter and --viewall the
# translate/distance components are recomputed to fit the whole model, so
# only the rotation triple actually matters here.
#
# Axes: x aft (nose at x=0), y starboard (span), z up. OpenSCAD's rotation
# (0,0,0) looks straight down -Z (top/plan view: span on one screen axis,
# fuselage length on the other). Empirically verified against the real
# ARGUS-7 mesh (span 9.26 m >> fuselage 3.4 m, so the two axes are easy to
# tell apart from the rendered bounding box):
#   (0,0,0)   -> plan view, length vertical/span horizontal-ish: TOP.
#   (90,0,0)  -> length horizontal, small height, tail visible: SIDE (profile).
#   (90,0,90) -> span horizontal, small height, fuselage nose-on: FRONT.
#   (55,0,25) -> OpenSCAD's standard "home" viewport: a recognizable 3/4 ISO.
# NOTE: a naive reading of OpenSCAD's own axis-rotation docs suggests
# (90,0,0) should be "front" and (90,0,90) "side" -- rendering both and
# inspecting the actual pixel bounding boxes showed that guess was
# backwards for this model, so front/side are assigned by measured result,
# not by that naive expectation.
VIEWS = {"top": (0, 0, 0), "side": (90, 0, 0), "front": (90, 0, 90),
         "iso": (55, 0, 25)}


def render_views(scad_path: str | Path, outdir: str | Path) -> list[Path]:
    """Render top/side/front/isometric PNGs of a .scad file with OpenSCAD's
    headless camera. Orthographic projection is used for the three
    principal views (and iso) so the images are dimensionally faithful,
    not perspective-distorted."""
    if shutil.which("openscad") is None:
        raise RuntimeError("openscad not installed - run scripts/setup_env.sh")
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    out = []
    for name, (rx, ry, rz) in VIEWS.items():
        png = outdir / f"argus7_{name}.png"
        subprocess.run(
            ["openscad", "--autocenter", "--viewall", "--imgsize=1600,1200",
             "--projection=ortho", f"--camera=0,0,0,{rx},{ry},{rz},0",
             "-o", str(png), str(scad_path)],
            check=True, capture_output=True, timeout=600)
        out.append(png)
    return out
