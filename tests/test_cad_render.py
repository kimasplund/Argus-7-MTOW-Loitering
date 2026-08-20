"""render_views regression guard.

A test that only checks the PNG files exist is worthless -- OpenSCAD happily
writes a well-formed, background-only PNG for a camera angle that shows
nothing (e.g. looking edge-on through a zero-thickness face, or a camera
rotation that puts the whole model outside frame). Every assertion here
inspects actual pixel content, not just file presence, so a genuinely empty
render fails loudly instead of silently passing.
"""
from __future__ import annotations
import numpy as np
import pytest
from PIL import Image
from pathlib import Path
from argus7.design.schema import load_design
from argus7.cad.to_openscad import emit_openscad
from argus7.cad.render import render_views, VIEWS


@pytest.fixture(scope="module")
def design():
    return load_design("design/argus7_v1.yaml")


@pytest.fixture(scope="module")
def rendered_pngs(design, tmp_path_factory):
    """Emit the .scad and render every view ONCE, shared by every test in
    this module -- avoids paying openscad's render cost per assertion."""
    import shutil
    if shutil.which("openscad") is None:
        pytest.skip("openscad not installed")
    tmp = tmp_path_factory.mktemp("render")
    scad = emit_openscad(design, tmp / "m.scad")
    pngs = render_views(scad, tmp / "views")
    return {p.stem.split("_")[-1]: p for p in pngs}


def _nonbackground_stats(png_path: Path) -> tuple[int, float]:
    """(count of non-background pixels, variance across all channels)."""
    arr = np.asarray(Image.open(png_path).convert("RGB")).astype(int)
    bg = arr[0, 0]                                   # corner pixel = background
    diff = np.abs(arr - bg).sum(axis=2)
    return int((diff > 10).sum()), float(arr.reshape(-1, 3).var())


def test_render_views_returns_all_four_expected_views(rendered_pngs):
    assert set(rendered_pngs) == {"top", "front", "side", "iso"}
    for p in rendered_pngs.values():
        assert p.exists() and p.stat().st_size > 1000


@pytest.mark.parametrize("view", ["top", "front", "side", "iso"])
def test_render_view_is_not_blank(rendered_pngs, view):
    """The core guard: a blank/uniform PNG (wrong camera angle, empty frame)
    must fail this test even though the file exists and is valid PNG data.
    Pixel variance of a truly blank render is ~0; require it be clearly
    non-trivial, and require a meaningful fraction of pixels differ from
    the background corner colour."""
    png = rendered_pngs[view]
    nonbg_px, variance = _nonbackground_stats(png)
    assert variance > 50, f"{view} view looks blank: pixel variance {variance:.2f}"
    assert nonbg_px > 1000, (
        f"{view} view has only {nonbg_px} non-background pixels -- "
        "looks empty or nearly empty")


def test_top_view_shows_span_larger_than_length(rendered_pngs, design):
    """Sanity-check the axis mapping, not just 'something is drawn'. The
    wing span (9.26 m) is more than double the fuselage length (3.4 m), so
    whichever screen axis carries the span in the top view must have a
    noticeably larger bounding-box extent than the one carrying length."""
    from argus7.design.geometry import derive_wing
    arr = np.asarray(Image.open(rendered_pngs["top"]).convert("RGB")).astype(int)
    bg = arr[0, 0]
    mask = np.abs(arr - bg).sum(axis=2) > 10
    ys, xs = np.where(mask)
    long_extent = max(xs.max() - xs.min(), ys.max() - ys.min())
    short_extent = min(xs.max() - xs.min(), ys.max() - ys.min())
    g = derive_wing(design.wing)
    assert long_extent / short_extent == pytest.approx(
        g.span_m / design.fuselage.length_m, rel=0.35)


def test_front_and_side_views_are_distinct_projections(rendered_pngs):
    """FRONT (nose-on) should be wide and short (spanwise, ~9.26 m, against
    a small height); SIDE (profile) should also be wide (length + tail arm,
    a few metres) but the two must not be pixel-identical renders -- that
    would mean the camera rotation collapsed to the same view twice, which
    is exactly the front/side mislabeling this repo's camera tuple had to
    be corrected for empirically (see argus7.cad.render.VIEWS docstring)."""
    front = np.asarray(Image.open(rendered_pngs["front"]).convert("RGB"))
    side = np.asarray(Image.open(rendered_pngs["side"]).convert("RGB"))
    assert front.shape == side.shape
    assert not np.array_equal(front, side)


def test_views_dict_has_four_distinct_camera_angles():
    assert len(VIEWS) == 4
    assert len(set(VIEWS.values())) == 4, "two views share a camera angle"
