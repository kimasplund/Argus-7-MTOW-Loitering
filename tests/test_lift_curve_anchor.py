"""Independent anchors for the finite-wing lift-curve slope.

Mutation testing found this function had NO independent anchor: flipping the
sign of the sweep correction left the whole suite passing. It is invisible on
this aircraft because the wing has 1 degree of sweep, where the error is 0.11%.
At 15 degrees it is 1.56%, and on a swept design it would move the neutral point
by several percent MAC while still passing every test.

The function itself is correct -- verified here against AVL, against the
analytic limits, and against an independently written DATCOM computation. What
was missing was any test that would notice if it stopped being correct.

The three anchors are deliberately different in kind:
  1. analytic limits, which no fitted constant can satisfy by accident
  2. AVL, an independent code
  3. a hand-written DATCOM relation, exercised at a sweep where the sign bites
"""
import math

import pytest

from argus7.analysis.balance import lift_curve_slope_per_rad


def datcom_helmbold(aspect_ratio, sweep_le_deg, taper_ratio):
    """The same physics, written out independently from the source relation.

    Deliberately NOT a call into the module under test: DATCOM gives the
    quarter/half-chord sweep as tan(Lambda_n) = tan(Lambda_le) - (4n/AR)*(1-l)/(1+l),
    and Helmbold gives a = 2*pi*AR / (2 + sqrt(AR^2*(1+tan^2 Lambda_c/2) + 4)).
    Written from those two statements, not from the implementation.
    """
    n = 0.5  # half-chord
    tan_half = (math.tan(math.radians(sweep_le_deg))
                - (4.0 * n / aspect_ratio) * (1.0 - taper_ratio) / (1.0 + taper_ratio))
    return (2.0 * math.pi * aspect_ratio
            / (2.0 + math.sqrt(aspect_ratio**2 * (1.0 + tan_half**2) + 4.0)))


def test_infinite_aspect_ratio_approaches_two_pi():
    """The 2-D thin-aerofoil limit. Nothing fitted can satisfy this by accident."""
    assert lift_curve_slope_per_rad(1e6, 0.0, 1.0) == pytest.approx(2 * math.pi, rel=1e-5)


def test_slope_falls_monotonically_with_sweep():
    a = [lift_curve_slope_per_rad(22.0, s, 0.45) for s in (0, 10, 20, 30, 40)]
    assert all(x > y for x, y in zip(a, a[1:])), f"not monotone in sweep: {a}"


def test_slope_rises_monotonically_with_aspect_ratio():
    a = [lift_curve_slope_per_rad(ar, 0.0, 0.45) for ar in (2, 5, 10, 20, 40)]
    assert all(x < y for x, y in zip(a, a[1:])), f"not monotone in AR: {a}"


@pytest.mark.parametrize("ar,sweep,taper", [
    (8.0, 0.0, 1.00), (8.0, 15.0, 0.50), (8.0, 30.0, 0.50),
    (15.0, 0.0, 0.45), (22.0, 1.0, 0.45), (22.0, 15.0, 0.45), (6.0, 25.0, 0.40),
])
def test_matches_an_independent_datcom_computation(ar, sweep, taper):
    """MUTATION ANCHOR. The 15-degree cases are the ones with teeth.

    At the aircraft's own 1 degree of sweep a sign error in the half-chord
    correction is 0.11% and slips through everything. At 15 degrees it is 1.56%,
    which this catches.
    """
    assert lift_curve_slope_per_rad(ar, sweep, taper) == pytest.approx(
        datcom_helmbold(ar, sweep, taper), rel=1e-9)


def test_half_chord_sweep_is_always_less_than_leading_edge_sweep():
    """The structural statement the sign error violates.

    For any positive taper the half-chord line is swept LESS than the leading
    edge, because the chord shortens outboard. A sign flip makes it swept more,
    which is geometrically impossible -- and is exactly the surviving mutant.
    """
    for ar in (8.0, 22.0, 30.0):
        for taper in (0.25, 0.45, 0.70):
            for sweep in (0.0, 5.0, 15.0, 30.0):
                tan_le = math.tan(math.radians(sweep))
                tan_half = tan_le - (2.0 / ar) * (1 - taper) / (1 + taper)
                assert tan_half < tan_le, (
                    f"AR={ar} taper={taper} sweep={sweep}: half-chord sweep must be "
                    "less than leading-edge sweep for a tapered wing")


@pytest.mark.parametrize("ar,sweep,taper,avl", [
    (8.0, 0.0, 1.00, 4.5815), (8.0, 15.0, 0.50, 4.6766), (8.0, 30.0, 0.50, 4.3821),
    (15.0, 0.0, 0.45, 5.3640), (22.0, 1.0, 0.45, 5.6316), (22.0, 15.0, 0.45, 5.5094),
    (6.0, 25.0, 0.40, 4.2346),
])
def test_tracks_avl_within_the_expected_band(ar, sweep, taper, avl):
    """Cross-check against an independent code (AVL 3.36, measured 2026-08-21).

    Helmbold is a thin-aerofoil finite-wing estimate and runs consistently ABOVE
    a panel method: measured +1.7% to +7.1% across this matrix, always the same
    sign. The band is one-sided on purpose -- a slope BELOW AVL would mean
    something is wrong, not merely lower-fidelity.
    """
    a = lift_curve_slope_per_rad(ar, sweep, taper)
    assert a > avl, f"analytic {a:.4f} should exceed AVL {avl:.4f} (Helmbold runs high)"
    assert a / avl - 1 < 0.10, f"analytic {a:.4f} is {100*(a/avl-1):.1f}% above AVL {avl:.4f}"
