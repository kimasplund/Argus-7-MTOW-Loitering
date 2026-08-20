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
