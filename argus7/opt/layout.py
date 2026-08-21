"""Batched, differentiable balance — so the optimiser owns the LAYOUT, not just the wing.

The first optimiser had eight variables: wing area, aspect ratio, taper, thickness,
MTOW, altitude, BSFC and engine power. Not one of them was a layout variable. It
therefore optimised the *wing* and left the *aeroplane* unbalanced — and the
resulting v2.0 turned out to be statically unstable at every fuel state, against a
static-margin gate this programme had pre-registered and then never evaluated,
because nothing in the codebase could evaluate it.

Hand-moving the wing aft afterwards is the wrong instinct when a GPU evaluates 40
million configurations in under five seconds. The fix is to give the optimiser the
layout and make stability a hard constraint:

    x_le_frac        wing longitudinal station, as a fraction of fuselage length
    tail_volume      horizontal tail volume coefficient V_h
    tail_arm_frac    tail arm, as a fraction of fuselage length

and then require 5% <= static margin <= 15% MAC **at every fuel state**, not just
at one.

This module mirrors ``argus7.analysis.balance`` in torch. That module is the
authority — scalar, tested, AVL-cross-checked. This one exists only because the
optimiser needs the same physics batched and differentiable. The constants below
are imported from it rather than re-typed, so the two cannot drift apart.
"""
from __future__ import annotations

import torch

from argus7.analysis.balance import (
    AVIONICS_X_FRAC_L,
    ETA_TAIL,
    MISC_FRACTION_OF_NON_WING,
    PAYLOAD_X_GIMBAL_OFFSET_M,
    PAYLOAD_X_GIMBAL_R_COEFF,
    POWERTRAIN_X_FRAC_L,
    RECOVERY_X_FRAC_L,
    TAIL_GROUP_CG_FRAC_MAC,
    TANK_CHORD_CENTROID_FRAC,
    TANK_SPAN_FRAC,
    WING_GROUP_CG_FRAC_MAC,
    X_AC_WING_FRAC_MAC,
)

FUSELAGE_LENGTH_M = 3.4
FUSELAGE_DIAMETER_M = 0.48


def wing_geometry(S, AR, taper):
    """span, c_root, MAC, and the spanwise station of the MAC."""
    span = torch.sqrt(AR * S)
    c_root = S / ((span / 2.0) * (1.0 + taper))
    mac = (2.0 / 3.0) * c_root * (1 + taper + taper**2) / (1 + taper)
    y_mac = (span / 6.0) * (1 + 2 * taper) / (1 + taper)
    return span, c_root, mac, y_mac


def lift_curve_slope(AR, sweep_le_rad=0.0, taper=0.45):
    """Helmbold/DATCOM slope. Sweep is ~0 here, so this is effectively Helmbold."""
    tan_half = torch.as_tensor(sweep_le_rad) - (2.0 / AR) * (1 - taper) / (1 + taper)
    beta2 = 1.0  # incompressible
    root = torch.sqrt(AR**2 * beta2 * (1 + tan_half**2 / beta2) + 4.0)
    return 2.0 * torch.pi * AR / (2.0 + root)


def balance(S, AR, taper, tc, mtow, x_le_frac, tail_volume, tail_arm_frac,
            *, fuel_kg, wing_mass_kg, airframe_kg, powertrain_kg, avionics_kg,
            recovery_kg, payload_kg, fuel_fraction=1.0,
            L=FUSELAGE_LENGTH_M, R=FUSELAGE_DIAMETER_M / 2):
    """CG, neutral point and static margin for a batch of layouts.

    Returns (x_cg, x_np, static_margin_fraction_of_mac). All tensors.
    """
    span, c_root, mac, y_mac = wing_geometry(S, AR, taper)

    x_wing_le = x_le_frac * L
    x_mac_le = x_wing_le  # sweep ~0, so the MAC leading edge is at the root LE
    x_ac_wing = x_mac_le + X_AC_WING_FRAC_MAC * mac
    x_tail_qc = x_ac_wing + tail_arm_frac * L

    # --- mass build-up -----------------------------------------------------
    m_non_wing = torch.clamp(airframe_kg - wing_mass_kg, min=0.1)
    m_misc = MISC_FRACTION_OF_NON_WING * m_non_wing
    m_struct = m_non_wing - m_misc

    # Split the structural remainder by a wetted-area proxy: the fuselage
    # dominates, booms and tail share the rest in proportion to the tail arm.
    s_fus = torch.pi * (2 * R) * L * 0.75 * torch.ones_like(S)
    s_boom = 2.0 * torch.pi * 0.09 * (tail_arm_frac * L + 0.3)
    s_tail = 2.1 * tail_volume * S * mac / torch.clamp(tail_arm_frac * L, min=0.1)
    s_tot = s_fus + s_boom + s_tail

    x_wing_cg = x_mac_le + WING_GROUP_CG_FRAC_MAC * mac
    x_fus_cg = 0.45 * L * torch.ones_like(S)
    x_boom_cg = 0.5 * (x_wing_le - 0.15 + x_tail_qc + 0.15)
    x_tail_cg = x_tail_qc + (TAIL_GROUP_CG_FRAC_MAC - 0.25) * 0.4 * mac

    m_fuel = fuel_kg * fuel_fraction
    # Tanks sit between the spars, inboard: chordwise at 40% of local chord,
    # spanwise centroid of the inner 80% of a tapered wing.
    x_fuel_cg = x_mac_le + TANK_CHORD_CENTROID_FRAC * mac * TANK_SPAN_FRAC

    masses = [
        (wing_mass_kg, x_wing_cg),
        (m_struct * s_fus / s_tot + m_misc, x_fus_cg),
        (m_struct * s_boom / s_tot, x_boom_cg),
        (m_struct * s_tail / s_tot, x_tail_cg),
        (powertrain_kg * torch.ones_like(S), POWERTRAIN_X_FRAC_L * L * torch.ones_like(S)),
        (avionics_kg * torch.ones_like(S), AVIONICS_X_FRAC_L * L * torch.ones_like(S)),
        (recovery_kg * torch.ones_like(S), RECOVERY_X_FRAC_L * L * torch.ones_like(S)),
        (payload_kg * torch.ones_like(S),
         (PAYLOAD_X_GIMBAL_R_COEFF * R + PAYLOAD_X_GIMBAL_OFFSET_M) * torch.ones_like(S)),
        (m_fuel, x_fuel_cg),
    ]
    m_tot = sum(m for m, _ in masses)
    moment = sum(m * x for m, x in masses)
    x_cg = moment / m_tot

    # --- neutral point -----------------------------------------------------
    a_w = lift_curve_slope(AR, 0.0, taper)
    ar_tail = 3.0 * torch.ones_like(AR)
    a_t = lift_curve_slope(ar_tail, 0.0, 0.55 * torch.ones_like(taper))
    de_da = 2.0 * a_w / (torch.pi * AR)
    x_np = x_ac_wing + tail_volume * ETA_TAIL * (a_t / a_w) * (1.0 - de_da) * mac

    sm = (x_np - x_cg) / mac
    return x_cg, x_np, sm


def static_margin_envelope(*args, **kwargs):
    """Static margin at full fuel AND dry — both must satisfy the constraint.

    Evaluating stability at one fuel state is how the previous design shipped
    unstable: it carries 41% of gross mass as fuel, so the CG moves a long way
    as that burns off.
    """
    kwargs.pop("fuel_fraction", None)
    _, _, sm_full = balance(*args, fuel_fraction=1.0, **kwargs)
    _, _, sm_dry = balance(*args, fuel_fraction=0.0, **kwargs)
    return sm_full, sm_dry
