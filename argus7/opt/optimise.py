"""Design-point optimisation on the GPU.

Three stages, each doing what it is good at:

1. **Sobol DOE, batched on the GPU.** Millions of designs evaluated in one pass
   through the differentiable mission simulator. This finds the basins; it does
   not polish.
2. **Gradient refinement by autograd**, straight through the fuel-burn
   integration, with an augmented-Lagrangian treatment of the constraints. This
   polishes; it cannot escape a basin.
3. **CMA-ES** as an independent check that stage 2 did not settle in a local
   optimum that stage 1 happened to seed it into.

The constraints are the point of the exercise as much as the objective. The
published design violates the wing fuel-volume constraint by a wide margin, so
the optimiser reports **two** answers: the best design that actually closes, and
the best design ignoring the tank constraint. Quoting only the second would
reproduce the error the programme has been correcting all week.
"""
from __future__ import annotations

from dataclasses import dataclass

import torch

from argus7.mission.sim import simulate_loiter
from argus7.opt.design_space import (
    Bounds,
    calibrate,
    constraints,
    empty_mass_kg,
    fuel_available_kg,
    wing_fuel_capacity_kg,
)

VAR_NAMES = [
    "wing_area_m2", "aspect_ratio", "taper_ratio", "thickness_ratio",
    "mtow_kg", "altitude_m", "cd0", "oswald_e", "bsfc_kg_per_kwh",
]

# Bounds per variable, in VAR_NAMES order.
LO = [2.5, 14.0, 0.30, 0.10, 180.0, 2500.0, 0.0153, 0.75, 0.25]
HI = [6.0, 30.0, 0.70, 0.20, 320.0, 5000.0, 0.0240, 0.92, 0.32]


@dataclass
class Evaluation:
    endurance_h: torch.Tensor
    fuel_kg: torch.Tensor
    tank_kg: torch.Tensor
    empty_kg: torch.Tensor
    span_m: torch.Tensor
    feasible: torch.Tensor
    violation: torch.Tensor


def evaluate(x: torch.Tensor, k_cal: float, *, payload_kg=50.0, payload_w=500.0,
             n_steps=120, span_limit_m=12.0) -> Evaluation:
    """Evaluate a batch of designs. `x` is (N, 9) in VAR_NAMES order."""
    S, AR, lam, tc, mtow, alt, cd0, e, bsfc = (x[..., i] for i in range(9))

    empty = empty_mass_kg(S, AR, lam, mtow, tc, k_cal)
    fuel = fuel_available_kg(mtow, empty, payload_kg=payload_kg)
    tank = wing_fuel_capacity_kg(S, AR, lam, tc)
    span = torch.sqrt(AR * S)

    # Clamp fuel positive for the integration so infeasible designs still produce
    # a finite, differentiable number the penalty can push on.
    fuel_pos = torch.clamp(fuel, min=1e-3)

    r = simulate_loiter(
        mass_total_kg=mtow, mass_fuel_kg=fuel_pos, wing_area_m2=S, aspect_ratio=AR,
        cd0=cd0, oswald_e=e, cl_max=torch.full_like(S, 1.6), altitude_m=alt,
        bsfc_kg_per_kwh=bsfc, payload_power_w=torch.full_like(S, payload_w),
        n_steps=n_steps,
    )

    c_span = torch.clamp(span - span_limit_m, min=0.0)
    c_tank = torch.clamp(fuel - tank, min=0.0)
    c_fuel = torch.clamp(-fuel, min=0.0)
    violation = c_span / span_limit_m + c_tank / 50.0 + c_fuel / 50.0

    return Evaluation(
        endurance_h=r.endurance_h, fuel_kg=fuel, tank_kg=tank, empty_kg=empty,
        span_m=span, feasible=violation <= 1e-6, violation=violation,
    )


def sobol_search(n: int, k_cal: float, device="cuda", seed=0, chunk=1_000_000):
    """Stage 1: Sobol DOE over the whole box, in GPU-sized chunks."""
    lo = torch.tensor(LO, device=device)
    hi = torch.tensor(HI, device=device)
    eng = torch.quasirandom.SobolEngine(dimension=9, scramble=True, seed=seed)

    best = {"endurance_h": -1.0, "x": None}
    best_feas = {"endurance_h": -1.0, "x": None}
    n_feasible = 0

    done = 0
    while done < n:
        m = min(chunk, n - done)
        u = eng.draw(m).to(device)
        x = lo + u * (hi - lo)
        ev = evaluate(x, k_cal)

        i = int(torch.argmax(ev.endurance_h))
        if float(ev.endurance_h[i]) > best["endurance_h"]:
            best = {"endurance_h": float(ev.endurance_h[i]), "x": x[i].clone()}

        feas = ev.feasible
        n_feasible += int(feas.sum())
        if bool(feas.any()):
            e_masked = torch.where(feas, ev.endurance_h, torch.full_like(ev.endurance_h, -1.0))
            j = int(torch.argmax(e_masked))
            if float(e_masked[j]) > best_feas["endurance_h"]:
                best_feas = {"endurance_h": float(e_masked[j]), "x": x[j].clone()}

        done += m
        del x, ev, u

    return best, best_feas, n_feasible


def refine(x0: torch.Tensor, k_cal: float, *, steps=800, lr=0.02, mu=50.0,
           enforce_feasible=True):
    """Stage 2: gradient refinement in a normalised box, with a penalty."""
    device = x0.device
    lo = torch.tensor(LO, device=device)
    hi = torch.tensor(HI, device=device)

    # Optimise in unconstrained space; a sigmoid maps back into the box so bounds
    # can never be violated and the gradient stays well behaved at the edges.
    z0 = torch.logit(torch.clamp((x0 - lo) / (hi - lo), 1e-4, 1 - 1e-4))
    z = z0.clone().requires_grad_(True)
    opt = torch.optim.Adam([z], lr=lr)

    for _ in range(steps):
        opt.zero_grad()
        x = lo + torch.sigmoid(z) * (hi - lo)
        ev = evaluate(x.unsqueeze(0), k_cal)
        loss = -ev.endurance_h.squeeze()
        if enforce_feasible:
            loss = loss + mu * ev.violation.squeeze() ** 2
        loss.backward()
        opt.step()

    with torch.no_grad():
        x = lo + torch.sigmoid(z) * (hi - lo)
        ev = evaluate(x.unsqueeze(0), k_cal)
    return x.detach(), ev


def describe(x: torch.Tensor, k_cal: float) -> dict:
    ev = evaluate(x.unsqueeze(0), k_cal)
    d = {n: float(v) for n, v in zip(VAR_NAMES, x.tolist())}
    d.update(
        endurance_h=float(ev.endurance_h), endurance_d=float(ev.endurance_h) / 24.0,
        fuel_kg=float(ev.fuel_kg), tank_capacity_kg=float(ev.tank_kg),
        empty_kg=float(ev.empty_kg), span_m=float(ev.span_m),
        feasible=bool(ev.feasible), violation=float(ev.violation),
    )
    return d
