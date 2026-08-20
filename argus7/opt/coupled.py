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


def cd0_from_geometry(wing_area_m2, thickness_ratio, cleanliness=1.0):
    """C_D0 as a consequence of geometry, not a free variable.

    ``cleanliness`` in [0.85, 1.35] spans the report's own range from an
    exceptionally clean build to a dirty one with external antennas, and is the
    only remaining discretionary factor.
    """
    swet = wetted_area_m2(wing_area_m2, thickness_ratio)
    return CFE * swet / wing_area_m2 * cleanliness


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
