import numpy as np
import pytest
from argus7.cad.airfoil_coords import load_airfoil, naca4, max_thickness, scale_airfoil


# --- Brief's baseline tests -------------------------------------------------

def test_naca0010_thickness_is_10_percent():
    assert max_thickness(naca4("0010")) == pytest.approx(0.10, abs=0.002)

def test_naca0012_thickness_is_12_percent():
    assert max_thickness(naca4("0012")) == pytest.approx(0.12, abs=0.002)

def test_naca0010_is_symmetric():
    c = naca4("0010")
    assert abs(c[:, 1].max() + c[:, 1].min()) < 1e-6

def test_fx63137_thickness_matches_its_name():
    """FX 63-137 is 13.7% thick by designation."""
    assert max_thickness(load_airfoil("fx63137")) == pytest.approx(0.137, abs=0.005)

def test_coordinates_are_normalised():
    c = load_airfoil("fx63137")
    assert c[:, 0].min() == pytest.approx(0.0, abs=1e-6)
    assert c[:, 0].max() == pytest.approx(1.0, abs=1e-6)

def test_scale_airfoil_applies_chord_and_twist():
    c = naca4("0010")
    out = scale_airfoil(c, chord=0.5, twist_rad=0.0, le_pos=(1.0, 2.0, 0.3))
    assert out.shape[1] == 3
    # chord runs aft along +x from the leading edge
    assert out[:, 0].max() - out[:, 0].min() == pytest.approx(0.5, abs=1e-6)
    assert out[:, 1].min() == pytest.approx(2.0, abs=1e-6)  # constant span station

def test_twist_rotates_about_leading_edge():
    c = naca4("0010")
    a = scale_airfoil(c, 1.0, 0.0, (0.0, 0.0, 0.0))
    b = scale_airfoil(c, 1.0, np.deg2rad(-3.0), (0.0, 0.0, 0.0))
    assert b[:, 2].max() != pytest.approx(a[:, 2].max(), abs=1e-6)
    # leading edge is the pivot and must not move
    le_a, le_b = a[np.argmin(a[:, 0])], b[np.argmin(b[:, 0])]
    assert np.allclose(le_a, le_b, atol=1e-6)


# --- RULING P4: twist sign ---------------------------------------------------
# The brief's rotation (xr = xc*ct - zc*st; zr = xc*st + zc*ct) produces washIN
# (TE down) for a negative twist, which is backwards. The corrected rotation
# (xr = xc*ct + zc*st; zr = -xc*st + zc*ct) must give washOUT: TE rises above
# LE for a negative (washout) twist. test_twist_rotates_about_leading_edge
# above only checks that *some* rotation happened, not its direction -- it
# would pass with either sign convention, which is why this is separate.

def test_negative_twist_produces_washout():
    c = naca4("0010")
    out = scale_airfoil(c, chord=1.0, twist_rad=np.deg2rad(-3.0), le_pos=(0.0, 0.0, 0.0))
    le_z = out[np.argmin(out[:, 0]), 2]
    te_z = out[np.argmax(out[:, 0]), 2]
    assert te_z > le_z, "negative twist must raise the trailing edge above the leading edge (washout)"


# --- RULING P11: Lednicer/Selig auto-detection -------------------------------
# The real UIUC fx63137.dat is Lednicer format: title line, then a
# point-count header ("49.0 49.0") that is NOT a coordinate, then two
# LE->TE surface blocks (upper, then lower). load_airfoil must detect this
# and reassemble it into Selig order, rather than ingesting the header as a
# spurious coordinate (which yields a bogus t/c of 1.0000). Fix round 1: the
# header's declared per-surface counts must also validate the split (see
# test_lednicer_header_mismatch_raises below), not just detect the format.

def test_fx63137_load_airfoil_is_lednicer_and_reassembled_correctly():
    """Regression guard: the count-header bug produces t/c == 1.0000. The
    correctly parsed FX 63-137 must measure ~0.1371, matching independently
    verified reference values (98 real points, 49/49 split)."""
    c = load_airfoil("fx63137")
    tc = max_thickness(c)
    assert tc == pytest.approx(0.1371, abs=0.001)
    # LE must be interior (two surfaces present), not an endpoint of the array
    le_idx = int(np.argmin(c[:, 0]))
    assert 0 < le_idx < len(c) - 1

def test_load_airfoil_handles_selig_format_directly(tmp_path, monkeypatch):
    """Synthesise a small genuine Selig-format fixture (first pair <= 1.0,
    already in TE->upper->LE->lower->TE order) so the Selig branch is
    covered by an actual parse, not merely assumed because the real fixture
    happens to be Lednicer."""
    import argus7.cad.airfoil_coords as ac

    selig_text = (
        "TEST SELIG AIRFOIL\n"
        " 1.000000  0.000000\n"
        " 0.500000  0.050000\n"
        " 0.000000  0.000000\n"
        " 0.500000 -0.050000\n"
        " 1.000000  0.000000\n"
    )
    (tmp_path / "selig_test.dat").write_text(selig_text)
    monkeypatch.setattr(ac, "DATA", tmp_path)

    c = ac.load_airfoil("selig_test")
    expected = np.array([
        [1.0, 0.0],
        [0.5, 0.05],
        [0.0, 0.0],
        [0.5, -0.05],
        [1.0, 0.0],
    ])
    assert np.allclose(c, expected)

def test_lednicer_header_mismatch_raises(tmp_path, monkeypatch):
    """Fix round 1 finding: the Lednicer header's declared per-surface point
    counts must be used to *validate* the x-decrease split, not just to
    detect the format. A file whose header disagrees with its actual point
    layout (e.g. from a non-monotonic surface) must fail loudly rather than
    silently mis-splitting -- Phase 2 ingests S1223/E387/SD7037, where a
    silent mis-split would quietly corrupt a drag polar.

    This fixture declares 4 upper / 4 lower points, but the actual data has
    5 points climbing monotonically before x resets toward zero (a split at
    index 5, not the declared 4) -- deliberately chosen so it is the
    split-index check, not merely the total-point-count check, that fires.
    """
    import argus7.cad.airfoil_coords as ac

    bad_text = (
        "BAD LEDNICER AIRFOIL\n"
        "   4.0   4.0\n"
        "\n"
        "  0.000000  0.000000\n"
        "  0.300000  0.050000\n"
        "  0.600000  0.070000\n"
        "  0.900000  0.030000\n"
        "  1.000000  0.000000\n"
        "  0.000000  0.000000\n"
        "  0.500000 -0.040000\n"
        "  1.000000  0.000000\n"
    )
    (tmp_path / "bad_lednicer.dat").write_text(bad_text)
    monkeypatch.setattr(ac, "DATA", tmp_path)

    with pytest.raises(ValueError, match="declares"):
        ac.load_airfoil("bad_lednicer")


# --- RULING: make the `derived` provenance tag true --------------------------
# design/argus7_v1.yaml tags wing.thickness_ratio (0.137) as "derived", but
# nothing derived it until now. This converts that aspirational tag into a
# checked one.

def test_yaml_thickness_ratio_matches_loaded_airfoil():
    from argus7.design.schema import load_design
    design = load_design("design/argus7_v1.yaml")
    measured = max_thickness(load_airfoil(design.wing.airfoil))
    assert measured == pytest.approx(design.wing.thickness_ratio, abs=0.002)


# --- FINAL REVIEW M8: airfoil coordinates are pinned data -------------------
# data/airfoils/fx63137.dat is load-bearing far beyond the loft: its
# shoelace shape factor 0.6062 drives test_wing_planform_area_matches_spec,
# the ~143 L gross wing volume quoted in the README, and two corrections in
# research/materials_pack.md §2.5. It had no checksum test. UIUC ships
# several FX 63-137 variants; swapping in one with the same 13.7% t/c passes
# every other check in this repo while silently moving the shape factor, the
# wing volume, and with it the fuel-volume conclusion that is currently
# escalated to the sponsor. Phase 2 adds S1223, E387 and SD7037 to the same
# directory, so the manifest is the place that has to hold.

import hashlib
import re
from pathlib import Path

AIRFOIL_DIR = Path("data/airfoils")
MANIFEST = AIRFOIL_DIR / "MANIFEST.md"
# | `file.dat` | source | retrieved | format | points | t/c | `sha256` |
_ROW = re.compile(r"^\|\s*`(?P<file>[^`]+\.dat)`\s*\|")


def _manifest_rows() -> dict[str, dict[str, str]]:
    rows = {}
    for line in MANIFEST.read_text().splitlines():
        if not _ROW.match(line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        assert len(cells) == 7, f"malformed manifest row (want 7 cells): {line}"
        rows[cells[0].strip("`")] = {
            "source": cells[1], "retrieved": cells[2], "format": cells[3],
            "points": cells[4], "tc": cells[5], "sha256": cells[6].strip("`"),
        }
    return rows


def test_manifest_lists_exactly_the_committed_dat_files():
    assert MANIFEST.exists(), f"{MANIFEST} is missing"
    committed = {p.name for p in sorted(AIRFOIL_DIR.glob("*.dat"))}
    assert committed, "no airfoil .dat files committed"
    assert set(_manifest_rows()) == committed


def test_airfoil_dat_checksums_match_the_manifest():
    """The actual guard: a swapped coordinate file fails here, loudly, instead
    of quietly moving the wing volume."""
    for name, row in _manifest_rows().items():
        digest = hashlib.sha256((AIRFOIL_DIR / name).read_bytes()).hexdigest()
        assert digest == row["sha256"], (
            f"{name} has changed: sha256 {digest} does not match the manifest's "
            f"{row['sha256']}. If the change is intentional, update "
            f"{MANIFEST} -- and re-check the shape factor, the wing volume in "
            f"README.md, and research/materials_pack.md §2.5.")


def test_manifest_thickness_matches_the_measured_file():
    """The checksum pins the bytes; this pins what the bytes MEAN, so a
    manifest row cannot be updated to bless a substituted section without the
    substitution showing up in the recorded t/c."""
    for name, row in _manifest_rows().items():
        measured = max_thickness(load_airfoil(Path(name).stem))
        assert measured == pytest.approx(float(row["tc"]), abs=5e-5), (
            f"{name}: measured t/c {measured:.5f} does not match the "
            f"manifest's {row['tc']}")


def test_manifest_records_a_retrieval_date_for_every_file():
    for name, row in _manifest_rows().items():
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", row["retrieved"]), (
            f"{name}: retrieval date {row['retrieved']!r} is not ISO yyyy-mm-dd")
        assert row["source"].startswith("http"), (
            f"{name}: source {row['source']!r} is not a URL")


def test_no_committed_dat_is_unreachable_by_the_loader():
    """M8, the other half: data/airfoils/naca0010.dat was committed and NEVER
    read. _section_coords routes ANY name beginning with NACA to the naca4()
    generator, so a naca*.dat file is unreachable by construction, not merely
    unused today -- two sources for one section, one of them dead.

    It was deleted rather than wired in: git 0654436 shows it was itself
    generated by naca4('0010') and rounded to 6 dp (max |diff| against the
    live generator: 5e-7), so it was a cached copy of a pure function. The
    generator is the authoritative definition of a NACA 4-digit section, is
    parameterised for the sections Phase 2 may want, and is already covered by
    the thickness and symmetry tests at the top of this file.

    Non-NACA .dat files are left alone: Phase 2 legitimately lands S1223, E387
    and SD7037 in this directory before any design file selects them."""
    dead = [p.name for p in sorted(AIRFOIL_DIR.glob("*.dat"))
            if p.stem.upper().startswith("NACA")]
    assert not dead, (
        f"{dead} can never be read -- _section_coords sends every NACA* name "
        "to the naca4() generator. Delete the file or change the routing; do "
        "not leave two sources for one section.")


# ============================================================================
# MUTATION SURVIVOR 2: the twist transform can be corrupted undetected.
#
# scripts/mutation_test.py flips the sign in scale_airfoil's xr line:
#     xr = xc*cos(t) + zc*sin(t)   ->   xr = xc*cos(t) - zc*sin(t)
# leaving zr = -xc*sin(t) + zc*cos(t) alone. The result is no longer a
# rotation. Its matrix is [[c, -s], [-s, c]], whose determinant is
# c^2 - s^2 = cos(2t), not 1 -- a SHEAR that squashes the section toward the
# line z = x by a factor cos(2*twist).
#
# Every existing test survived it, including test_negative_twist_produces_washout
# directly above: for the closed-TE NACA sections used there the TE sits at
# zc = 0, so the two conventions agree on the TE point exactly, and washout
# direction is all those tests look at. The damage is to everything BETWEEN the
# LE and the TE -- the section is silently thinned, which is what a spar depth,
# a fuel volume and a loft all read.
#
# The invariant that separates a rotation from a shear is AREA. An orthogonal
# transform preserves enclosed area exactly; a shear multiplies it by |det|.
# Measured here by shoelace integration of the transformed coordinates.
# ============================================================================

def _enclosed_area_xz(pts: np.ndarray) -> float:
    """Shoelace area of a closed section in the (x, z) plane.

    Works on the raw Selig loop (TE -> upper -> LE -> lower -> TE): np.roll
    closes the polygon, and the duplicated TE point contributes a zero-area
    segment. Sign depends on traversal direction, hence abs().
    """
    x, z = pts[:, 0], pts[:, 2]
    return 0.5 * abs(float(np.sum(x * np.roll(z, -1) - np.roll(x, -1) * z)))


_TWISTS_DEG = [0.0, -3.0, -6.0, -10.0]      # -3 is the v1 tip twist; -10 brackets it


@pytest.mark.parametrize("section", ["naca0012", "fx63137"])
@pytest.mark.parametrize("twist_deg", _TWISTS_DEG)
def test_twist_preserves_enclosed_section_area(section, twist_deg):
    """A rotation is area-preserving. The shear mutant is not.

    Shortfalls the mutant produces (|det| = cos(2t) - 1): 0.55% at -3 deg,
    2.19% at -6 deg, 6.03% at -10 deg. The 1e-9 relative tolerance is float
    noise, roughly six orders of magnitude below the smallest of those.
    """
    c = naca4("0012") if section == "naca0012" else load_airfoil("fx63137")
    chord = 0.5807                # arbitrary scale factor, not asserted geometry
    untwisted = _enclosed_area_xz(scale_airfoil(c, chord, 0.0, (0.0, 0.0, 0.0)))
    twisted = _enclosed_area_xz(
        scale_airfoil(c, chord, np.deg2rad(twist_deg), (1.2, 0.62, 0.008)))
    assert twisted == pytest.approx(untwisted, rel=1e-9), (
        f"twist of {twist_deg} deg changed the enclosed area by "
        f"{100 * (twisted / untwisted - 1):+.3f}% -- the transform is not a "
        f"rotation")


@pytest.mark.parametrize("twist_deg", _TWISTS_DEG)
def test_twist_scales_area_with_chord_squared_only(twist_deg):
    """Area must go as chord^2 for any twist. Pins the scaling and the
    rotation together, so a mutant cannot trade one against the other."""
    c = load_airfoil("fx63137")
    a1 = _enclosed_area_xz(scale_airfoil(c, 1.0, np.deg2rad(twist_deg), (0.0, 0.0, 0.0)))
    a2 = _enclosed_area_xz(scale_airfoil(c, 2.0, np.deg2rad(twist_deg), (0.0, 0.0, 0.0)))
    assert a2 == pytest.approx(4.0 * a1, rel=1e-9)


@pytest.mark.parametrize("twist_deg", _TWISTS_DEG)
def test_twist_pivots_exactly_about_the_leading_edge(twist_deg):
    """The LE is the pivot, so it must land exactly on le_pos regardless of
    twist -- not merely 'unchanged between two twists' as the older test
    checks."""
    c = load_airfoil("fx63137")
    le_pos = (1.234, 0.62, 0.008)
    out = scale_airfoil(c, 0.5807, np.deg2rad(twist_deg), le_pos)
    le = out[int(np.argmin(c[:, 0]))]
    assert le == pytest.approx(np.array(le_pos), abs=1e-12)


@pytest.mark.parametrize("twist_deg", _TWISTS_DEG)
def test_twist_preserves_chord_length(twist_deg):
    """LE-to-TE distance is a rigid-body invariant: it must equal the chord
    exactly, for every twist."""
    c = load_airfoil("fx63137")
    chord = 0.5807
    out = scale_airfoil(c, chord, np.deg2rad(twist_deg), (1.2, 0.62, 0.008))
    le = out[int(np.argmin(c[:, 0]))]
    te = out[int(np.argmax(c[:, 0]))]
    length = float(np.hypot(te[0] - le[0], te[2] - le[2]))
    assert length == pytest.approx(chord, rel=1e-12)


def test_twist_preserves_every_pairwise_distance():
    """The strongest statement of the same invariant, and the one that does not
    depend on picking the right two points: an orthogonal transform is an
    isometry, so the full distance matrix of the section is unchanged. A shear
    with |det| = 0.9945 cannot satisfy this."""
    c = load_airfoil("fx63137")
    a = scale_airfoil(c, 0.5807, 0.0, (0.0, 0.0, 0.0))[:, [0, 2]]
    b = scale_airfoil(c, 0.5807, np.deg2rad(-6.0), (0.0, 0.0, 0.0))[:, [0, 2]]
    da = np.linalg.norm(a[:, None, :] - a[None, :, :], axis=-1)
    db = np.linalg.norm(b[:, None, :] - b[None, :, :], axis=-1)
    assert np.max(np.abs(da - db)) < 1e-12


# ============================================================================
# ADVERSARIAL REVIEW: the survivor-2 tests above are ALL RELATIVE INVARIANTS.
#
# Every one of them compares the transform against itself -- twisted area
# against untwisted area, chord 2.0 against chord 1.0, distance matrix against
# distance matrix. That is exactly the right shape of test for distinguishing a
# rotation from a shear, and it does kill the mutant. But it leaves the class of
# defect SURVIVOR 2 was ABOUT -- silent thinning of the section -- wide open in
# its simplest form. Injecting
#
#     xc, zc = coords[:, 0] * chord, coords[:, 1] * chord * 0.98
#
# (a section 2% thinner, which is four times the damage the -3 deg shear does)
# passes all 125 tests in test_airfoil_coords, test_cad_airframe, test_cad_wing,
# test_cad_export, test_geometry_closure and test_opt_design_space. Measured,
# not argued. The reason is that a uniform z-scale commutes with the rotation,
# so it cancels out of every ratio: areas scale together, chord^2 scaling is
# untouched, the LE is still the pivot, the TE still sits at z = 0 so the chord
# length is unchanged, and the whole section is still an isometric copy of the
# (thinned) section at zero twist.
#
# The missing statement is an ABSOLUTE one: what the output IS, not only what
# it preserves. h_spar, the fuel volume and the loft all read the section's
# actual thickness, so that is the statement that has to exist.
# ============================================================================

def _unit_shoelace(coords: np.ndarray) -> float:
    """Enclosed area of the normalised section, in its own (x, y) plane."""
    x, y = coords[:, 0], coords[:, 1]
    return 0.5 * abs(float(np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y)))


@pytest.mark.parametrize("section", ["naca0012", "fx63137"])
def test_untwisted_section_is_exactly_the_scaled_translated_coordinates(section):
    """At zero twist the transform is pure scale-and-translate, so the output
    is fully determined and can be written down: x = x_c*chord + x0,
    y = y0 throughout, z = z_c*chord + z0. Nothing here is a ratio."""
    c = naca4("0012") if section == "naca0012" else load_airfoil("fx63137")
    chord, (x0, y0, z0) = 0.5807, (1.234, 0.62, 0.008)
    out = scale_airfoil(c, chord, 0.0, (x0, y0, z0))
    assert out[:, 0] == pytest.approx(c[:, 0] * chord + x0, abs=1e-12)
    assert out[:, 1] == pytest.approx(np.full(len(c), y0), abs=1e-12)
    assert out[:, 2] == pytest.approx(c[:, 1] * chord + z0, abs=1e-12)


@pytest.mark.parametrize("section", ["naca0012", "fx63137"])
@pytest.mark.parametrize("twist_deg", _TWISTS_DEG)
def test_section_area_equals_chord_squared_times_the_input_coordinate_area(
        section, twist_deg):
    """The absolute form of the area invariant: the placed section's enclosed
    area must equal chord^2 times the enclosed area OF THE INPUT COORDINATES,
    at every twist. Ties the output to the .dat file rather than to another
    call of the same function, so a uniform rescale of z cannot cancel."""
    c = naca4("0012") if section == "naca0012" else load_airfoil("fx63137")
    chord = 0.5807
    expected = _unit_shoelace(c) * chord ** 2
    got = _enclosed_area_xz(
        scale_airfoil(c, chord, np.deg2rad(twist_deg), (1.2, 0.62, 0.008)))
    assert got == pytest.approx(expected, rel=1e-12)


@pytest.mark.parametrize("twist_deg", _TWISTS_DEG)
def test_section_thickness_survives_placement(twist_deg):
    """The quantity the spar and the tank actually read. Measured normal to the
    chord line (i.e. after rotating the placed section back by -twist), it must
    be chord * t/c of the source coordinates, for every twist.

    fx63137 measures 0.1371167 t/c; at the 0.5807 m chord used here that is
    79.62 mm of section depth. A 2% thinning shows up as 78.03 mm."""
    c = load_airfoil("fx63137")
    chord, twist = 0.5807, np.deg2rad(twist_deg)
    out = scale_airfoil(c, chord, twist, (1.2, 0.62, 0.008))
    # undo the placement: translate to the LE, then rotate back by -twist
    xz = out[:, [0, 2]] - out[int(np.argmin(c[:, 0])), [0, 2]]
    ct, st = np.cos(twist), np.sin(twist)
    unrot = np.column_stack([xz[:, 0] * ct - xz[:, 1] * st,
                             xz[:, 0] * st + xz[:, 1] * ct])
    assert max_thickness(unrot / chord) == pytest.approx(
        max_thickness(c), rel=1e-9)
