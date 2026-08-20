"""Geometry-coupled evaluation: C_D0 and Oswald e become OUTPUTS, not free inputs.

The first optimiser run exposed a real defect in its own formulation. Given C_D0,
Oswald e and BSFC as free variables, it drove every one of them to its favourable
bound and returned 208 h. That is not a design; it is the corner of the box. The
pre-registered limitation list called this exact failure, and here it is.

The fix is to make the aerodynamic coefficients follow from the geometry:

- **C_D0** from a wetted-area build-up. Buying wing area now costs parasite drag,
  so area is no longer free. Calibrated against `argus7.aero.buildup`, which gave
  C_D0 = 0.01529 for the baseline with the verified XFOIL transition.
- **Oswald e** from a surface MEASURED with AVL across 45 planforms (AR 14-30,
  taper 0.30-0.60, twist 0 to -6 deg) at matched C_L, plus an explicit viscous
  lift-dependent term. A first attempt used Raymer's straight-wing correlation,
  which is fitted to conventional aircraft at AR 5-10 and returns e = 0.485 at
  AR 22 against 0.979 measured; it drove that run to AR 15.25 for a fictitious
  reason. Span efficiency is in fact nearly flat in aspect ratio here, so the
  only legitimate pushback on AR is structural mass.
- **BSFC** stays a variable but bounded by engine technology, because it is
  genuinely a procurement choice rather than a consequence of the airframe.

Everything remains differentiable, so gradients still flow to the design vector.

The remaining honest caveat: this is a *correlation-level* coupling, not the full
AVL-plus-build-up loop. It removes the free lunch; it does not replace Phase 2's
proper aerodynamic closure.
"""
from __future__ import annotations

import torch

from argus7.opt.design_space import (
    empty_mass_kg,
    fuel_available_kg,
    wing_fuel_capacity_kg,
)

# --- calibration anchors, from this project's own measurements ---
CD0_BASELINE = 0.01529  # argus7.aero.buildup at the v1 point, verified transition
SWET_BASELINE = 14.72  # m^2, sum of the build-up's component wetted areas
SREF_BASELINE = 3.9

# Equivalent skin-friction coefficient implied by the build-up. Holding this fixed
# and letting wetted area follow geometry is the standard C_D0 = Cfe * Swet/Sref
# method (Raymer §12.5); it is coarse but it is *physical*, which is the point.
CFE = CD0_BASELINE * SREF_BASELINE / SWET_BASELINE

# Non-wing wetted area (fuselage + booms + tail) held fixed at this fidelity.
SWET_NONWING = 4.029 + 2.062 + 1.139


def wetted_area_m2(wing_area_m2, thickness_ratio):
    """Wing wetted area grows with area and thickness; the rest is fixed."""
    wing_wet = wing_area_m2 * 2.0 * (1.0 + 1.2 * thickness_ratio)
    return wing_wet + SWET_NONWING


# Wing profile-drag penalty for thickening the section, MEASURED with NeuralFoil
# on the actual FX 63-137 coordinates scaled about their camber line, Re 1.0e6:
#   t/c   0.137  0.150  0.170  0.190  0.200
#   C_D   1.000  1.028  1.080  1.132  1.158  (relative)
# i.e. multiplier ~ 1 + 2.5*(t/c - 0.137), linear to within 0.5% across the range.
#
# A pure wetted-area model captures only +6.5% of the +15.8% real penalty at
# t/c 0.20, so without this the optimiser buys thickness -- and with it fuel
# volume and spar depth -- at roughly 40% of its true drag cost. This is the same
# class of unpriced lunch that C_D0-as-a-free-variable and Raymer's e were.
TC_REF = 0.137
TC_DRAG_SLOPE = 2.5
WING_FRACTION_OF_CD0 = 0.484  # from the build-up at the baseline


def thickness_drag_multiplier(thickness_ratio):
    """Applied to the WING share of C_D0 only; the rest does not care about t/c."""
    wing_mult = 1.0 + TC_DRAG_SLOPE * (thickness_ratio - TC_REF)
    return 1.0 + WING_FRACTION_OF_CD0 * (wing_mult - 1.0)


def cd0_from_geometry(wing_area_m2, thickness_ratio, cleanliness=1.0):
    """C_D0 as a consequence of geometry, not a free variable.

    ``cleanliness`` in [0.85, 1.35] spans the report's own range from an
    exceptionally clean build to a dirty one with external antennas, and is the
    only remaining discretionary factor.
    """
    swet = wetted_area_m2(wing_area_m2, thickness_ratio)
    base = CFE * swet / wing_area_m2 * cleanliness
    return base * thickness_drag_multiplier(thickness_ratio)


# --- span efficiency, MEASURED with AVL across the planform family ---------
# Fitted to 45 AVL runs at matched C_L 1.21 spanning AR 14-30, taper 0.30-0.60,
# twist 0 to -6 deg. Max abs error 0.024, rms 0.009.
#
# This replaces Raymer's straight-wing correlation, which was fitted to
# conventional aircraft at AR 5-10 and gives e = 0.485 at AR 22 and 0.331 at
# AR 30 -- against 0.979 and 0.969 actually measured. Extrapolating it that far
# drove an earlier run to AR 15.25 for an entirely fictitious reason.
E_FIT = (1.015357, -0.001543, 0.077956, -0.428148, -0.001823, -0.000923)

# Viscous lift-dependent drag, the term a lumped Oswald factor hides. Anchored so
# the baseline reproduces the report's own total C_D at C_L 1.21.
K_VISC = 0.002237


def span_efficiency_inviscid(aspect_ratio, taper_ratio, twist_tip_deg=-3.0):
    """Inviscid span efficiency from the AVL surface. Nearly flat in AR."""
    a, b, c, d, f, g = E_FIT
    dt = taper_ratio - 0.45
    tw = twist_tip_deg
    return torch.clamp(a + b * aspect_ratio + c * dt + d * dt**2 + f * tw + g * tw**2,
                       min=0.80, max=1.0)


def oswald_from_planform(aspect_ratio, taper_ratio, twist_tip_deg=-3.0):
    """Effective Oswald factor: inviscid span efficiency plus the viscous term.

    Folding the viscous lift-dependent drag into an effective e keeps the mission
    simulator's polar form unchanged:

        1/e_eff = 1/e_inviscid + K_VISC * pi * AR

    At the baseline this returns 0.8500 -- exactly the value the design file
    assumes, now derived from an AVL measurement plus the report's own total
    rather than asserted.
    """
    e_inv = span_efficiency_inviscid(aspect_ratio, taper_ratio, twist_tip_deg)
    return 1.0 / (1.0 / e_inv + K_VISC * torch.pi * aspect_ratio)


def evaluate_coupled(x, k_cal, *, payload_kg=50.0, payload_w=500.0, n_steps=120,
                     span_limit_m=12.0):
    """Evaluate designs where the aero coefficients follow from geometry.

    ``x`` is (N, 7): wing_area, aspect_ratio, taper, thickness_ratio, mtow,
    altitude, bsfc. C_D0 and e are no longer inputs.
    """
    from argus7.mission.sim import simulate_loiter

    S, AR, lam, tc, mtow, alt, bsfc = (x[..., i] for i in range(7))

    cd0 = cd0_from_geometry(S, tc)
    e = oswald_from_planform(AR, lam)

    empty = empty_mass_kg(S, AR, lam, mtow, tc, k_cal)
    fuel = fuel_available_kg(mtow, empty, payload_kg=payload_kg)
    tank = wing_fuel_capacity_kg(S, AR, lam, tc)
    span = torch.sqrt(AR * S)

    r = simulate_loiter(
        mass_total_kg=mtow, mass_fuel_kg=torch.clamp(fuel, min=1e-3),
        wing_area_m2=S, aspect_ratio=AR, cd0=cd0, oswald_e=e,
        cl_max=torch.full_like(S, 1.6), altitude_m=alt, bsfc_kg_per_kwh=bsfc,
        payload_power_w=torch.full_like(S, payload_w), n_steps=n_steps,
    )

    v_span = torch.clamp(span - span_limit_m, min=0.0) / span_limit_m
    v_tank = torch.clamp(fuel - tank, min=0.0) / 50.0
    v_fuel = torch.clamp(-fuel, min=0.0) / 50.0
    violation = v_span + v_tank + v_fuel

    return {
        "endurance_h": r.endurance_h, "cd0": cd0, "oswald_e": e, "fuel_kg": fuel,
        "tank_kg": tank, "empty_kg": empty, "span_m": span,
        "violation": violation, "feasible": violation <= 1e-6,
    }


def refine_augmented_lagrangian(x0, k_cal, lo, hi, *, outer=12, inner=150, lr=0.03):
    """Refinement that actually holds feasibility.

    The first attempt used a fixed quadratic penalty (mu=50) and drifted 26 kg
    infeasible: the endurance gradient simply outran the penalty. Here mu ramps
    across outer iterations and a Lagrange multiplier accumulates, so the
    constraint is satisfied *at convergence* rather than merely discouraged.
    """
    device = x0.device
    z = torch.logit(torch.clamp((x0 - lo) / (hi - lo), 1e-4, 1 - 1e-4)).clone().requires_grad_(True)
    mu = torch.tensor(10.0, device=device)
    lam = torch.zeros((), device=device)

    for _ in range(outer):
        opt = torch.optim.Adam([z], lr=lr)
        for _ in range(inner):
            opt.zero_grad()
            x = lo + torch.sigmoid(z) * (hi - lo)
            ev = evaluate_coupled(x.unsqueeze(0), k_cal)
            g = ev["violation"].squeeze()
            loss = -ev["endurance_h"].squeeze() + lam * g + 0.5 * mu * g**2
            loss.backward()
            opt.step()
        with torch.no_grad():
            x = lo + torch.sigmoid(z) * (hi - lo)
            g = evaluate_coupled(x.unsqueeze(0), k_cal)["violation"].squeeze()
            lam = lam + mu * g
            mu = mu * 2.5

    with torch.no_grad():
        x = lo + torch.sigmoid(z) * (hi - lo)
    return x.detach(), evaluate_coupled(x.unsqueeze(0), k_cal)


# =============================================================================
# Part-load BSFC and engine right-sizing (added 2026-08-21, gauntlet audit)
# =============================================================================
# The audit's second finding: the optimiser was handed BSFC as a free variable
# bounded at 0.25 kg/kWh, and duly took it. But BSFC is not free -- it is a
# strong function of LOAD FRACTION, and this aircraft loiters at ~3.4 kW from a
# 17 kW engine, i.e. **20% load**, where the engine module's own curve gives
# 411 g/kWh, not 270 and certainly not 250.
#
# Fitted to argus7.prop.engine's curve, max error 0.8 g/kWh over 12-100% load:
#
#     BSFC(load) = bsfc_full * (0.8471 + 0.1529 / load)
#
# Consequence for the published design: 112.8 h at an assumed 270 becomes 74.0 h
# (3.08 d) at the real part-load value. That is the single largest correction
# anywhere in this programme.
#
# The fix is not to accept the penalty but to let the optimiser CHOOSE the engine.
# A smaller engine runs at higher load fraction and better BSFC, but must still
# meet a climb requirement -- which is the real tension, because climb wants
# ~12-17 kW and loiter wants ~3.4 kW.
BSFC_A = 0.8471
BSFC_B = 0.1529
CLIMB_RATE_MS = 2.0  # minimum sea-level climb rate at MTOW
PROP_ETA = 0.84


def bsfc_at_load(bsfc_full_kg_per_kwh, load_fraction):
    """Part-load BSFC. `load_fraction` is shaft power over rated power."""
    lf = torch.clamp(load_fraction, min=0.05, max=1.0)
    return bsfc_full_kg_per_kwh * (BSFC_A + BSFC_B / lf)


def climb_power_required_w(mtow_kg, wing_area_m2, aspect_ratio, cd0, e, cl_max):
    """Sea-level shaft power for CLIMB_RATE_MS at MTOW, at best-climb speed."""
    from argus7.mission.atmosphere import isa

    rho = isa(torch.zeros_like(mtow_kg)).density_kgm3
    w = mtow_kg * 9.80665
    cl = torch.sqrt(torch.clamp(cd0 * torch.pi * aspect_ratio * e, min=1e-9)) * 1.2
    cl = torch.minimum(cl, cl_max / 1.3)
    v = torch.sqrt(2.0 * w / (rho * wing_area_m2 * cl))
    cd = cd0 + cl**2 / (torch.pi * aspect_ratio * e)
    drag = 0.5 * rho * v**2 * wing_area_m2 * cd
    return (drag * v + w * CLIMB_RATE_MS) / PROP_ETA


def evaluate_full(x, k_cal, *, payload_kg=50.0, payload_w=500.0, n_steps=120,
                  span_limit_m=12.0):
    """The honest model: 8 variables, part-load BSFC, engine sized by the optimiser.

    ``x`` is (N, 8): wing_area, AR, taper, t/c, MTOW, altitude, bsfc_full,
    engine_rated_kw.
    """
    from argus7.mission.sim import loiter_cl, drag_polar, simulate_loiter
    from argus7.mission.atmosphere import isa

    S, AR, lam, tc, mtow, alt, bsfc_full, p_rated_kw = (x[..., i] for i in range(8))

    cd0 = cd0_from_geometry(S, tc)
    e = oswald_from_planform(AR, lam)
    cl_max = torch.full_like(S, 1.6)

    empty = empty_mass_kg(S, AR, lam, mtow, tc, k_cal)
    # Engine mass scales with rated power; 17 kW ~ 25 kg powertrain in the baseline.
    empty = empty + (p_rated_kw - 17.0) * (25.0 / 17.0) * 0.6
    fuel = fuel_available_kg(mtow, empty, payload_kg=payload_kg)
    tank = wing_fuel_capacity_kg(S, AR, lam, tc)
    span = torch.sqrt(AR * S)

    # Shaft power at the loiter mid-point, to set the load fraction.
    rho = isa(alt).density_kgm3
    cl = loiter_cl(cd0, AR, e, cl_max)
    cd = drag_polar(cl, cd0, AR, e)
    w_mid = (mtow - 0.5 * torch.clamp(fuel, min=0.0)) * 9.80665
    v_mid = torch.sqrt(2.0 * w_mid / (rho * S * cl))
    shaft_mid = w_mid / (cl / cd) * v_mid / PROP_ETA + payload_w / 0.75
    load = shaft_mid / (p_rated_kw * 1000.0)
    bsfc_eff = bsfc_at_load(bsfc_full, load)

    r = simulate_loiter(
        mass_total_kg=mtow, mass_fuel_kg=torch.clamp(fuel, min=1e-3),
        wing_area_m2=S, aspect_ratio=AR, cd0=cd0, oswald_e=e, cl_max=cl_max,
        altitude_m=alt, bsfc_kg_per_kwh=bsfc_eff,
        payload_power_w=torch.full_like(S, payload_w), n_steps=n_steps,
    )

    p_climb = climb_power_required_w(mtow, S, AR, cd0, e, cl_max)
    v_span = torch.clamp(span - span_limit_m, min=0.0) / span_limit_m
    v_tank = torch.clamp(fuel - tank, min=0.0) / 50.0
    v_fuel = torch.clamp(-fuel, min=0.0) / 50.0
    v_climb = torch.clamp(p_climb - p_rated_kw * 1000.0, min=0.0) / 5000.0
    v_load = torch.clamp(load - 1.0, min=0.0)
    violation = v_span + v_tank + v_fuel + v_climb + v_load

    return {"endurance_h": r.endurance_h, "cd0": cd0, "oswald_e": e, "fuel_kg": fuel,
            "tank_kg": tank, "empty_kg": empty, "span_m": span, "load_fraction": load,
            "bsfc_eff": bsfc_eff, "climb_kw_req": p_climb / 1000.0,
            "violation": violation, "feasible": violation <= 1e-6}
