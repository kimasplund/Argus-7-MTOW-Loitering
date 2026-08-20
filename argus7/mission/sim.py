"""Batched, differentiable mission simulator.

Everything here is torch and shape-preserving, so a whole population of designs
integrates in one pass on the GPU, and gradients flow back to the design vector.
That is the point: the optimiser gets both massive batching and exact gradients
from the same code, rather than finite-differencing a scalar simulator.

Physics, per step, for an aircraft loitering at weight W:

    C_L  = W / (q S)                q = 1/2 rho V^2
    C_D  = C_D0 + C_L^2 / (pi AR e)
    D    = q S C_D
    P_shaft = D V / eta_prop  +  P_elec / eta_alt
    mdot = BSFC * P_shaft

Loiter speed is the minimum-power speed *subject to a stall margin*. Unconstrained,
minimum power occurs at

    C_L,minpower = sqrt(3 C_D0 pi AR e)

which for the ARGUS-7 baseline is 1.877 -- well above the stall-limited ceiling of
C_Lmax / margin^2 = 1.6 / 1.15^2 = 1.21. The stall constraint therefore binds, and
the aircraft loiters at C_L 1.21. This reproduces the design report's stated
operating point exactly, and is the reason its loiter C_L is 1.21 rather than the
min-power value.

Units are SI throughout. Angles are radians.
"""
from __future__ import annotations

from dataclasses import dataclass

import torch

from argus7.mission.atmosphere import isa

G = 9.80665


@dataclass(frozen=True)
class MissionResult:
    """Per-design outcome. Every field is a tensor shaped like the design batch."""

    endurance_s: torch.Tensor
    fuel_burned_kg: torch.Tensor
    mean_cl: torch.Tensor
    mean_speed_ms: torch.Tensor
    mean_shaft_kw: torch.Tensor
    converged: torch.Tensor  # bool: fuel actually exhausted within the step budget

    @property
    def endurance_h(self) -> torch.Tensor:
        return self.endurance_s / 3600.0

    @property
    def endurance_days(self) -> torch.Tensor:
        return self.endurance_s / 86400.0


def loiter_cl(cd0, aspect_ratio, oswald_e, cl_max, stall_margin=1.15):
    """C_L at the minimum-power speed, capped by the stall margin.

    Both branches are differentiable; ``torch.minimum`` passes the gradient to
    whichever branch is active, which is what the optimiser needs when a design
    moves across the constraint boundary.
    """
    cl_minpower = torch.sqrt(3.0 * cd0 * torch.pi * aspect_ratio * oswald_e)
    cl_stall_limited = cl_max / stall_margin**2
    return torch.minimum(cl_minpower, cl_stall_limited)


def drag_polar(cl, cd0, aspect_ratio, oswald_e):
    return cd0 + cl**2 / (torch.pi * aspect_ratio * oswald_e)


def simulate_loiter(
    *,
    mass_total_kg,
    mass_fuel_kg,
    wing_area_m2,
    aspect_ratio,
    cd0,
    oswald_e,
    cl_max,
    altitude_m,
    bsfc_kg_per_kwh,
    payload_power_w,
    prop_efficiency=0.84,
    alternator_efficiency=0.75,
    stall_margin=1.15,
    n_steps: int = 200,
) -> MissionResult:
    """Integrate a pure loiter until the fuel is gone.

    All arguments broadcast against one another, so any of them may be a batch of
    designs. Integration is a fixed number of equal-fuel-mass steps using the
    midpoint rule, which converges quickly because weight is the only state and it
    varies monotonically and smoothly.

    ``bsfc_kg_per_kwh`` may be a constant or a callable ``f(shaft_power_w) -> bsfc``
    so a part-load penalty can be injected once the engine module lands. Deep part
    load is the norm here -- roughly 3.4 kW drawn from a 17 kW engine -- so a
    constant BSFC materially overstates endurance.
    """
    atm = isa(altitude_m)
    rho = atm.density_kgm3

    cl = loiter_cl(cd0, aspect_ratio, oswald_e, cl_max, stall_margin)
    cd = drag_polar(cl, cd0, aspect_ratio, oswald_e)
    ld = cl / cd

    # Equal-fuel-mass steps, accumulated in a loop rather than materialised as an
    # (n_steps, batch) tensor. Memory is then O(batch) instead of O(n_steps*batch),
    # which is the difference between running 1M designs and 10M+ on a 12 GB card.
    # The loop is over steps only, so every design still advances in parallel, and
    # autograd still threads the whole integration.
    dm = mass_fuel_kg / n_steps

    endurance_s = torch.zeros_like(cl * mass_total_kg * wing_area_m2)
    speed_sum = torch.zeros_like(endurance_s)
    shaft_sum = torch.zeros_like(endurance_s)

    for i in range(n_steps):
        frac = (i + 0.5) / n_steps
        weight = (mass_total_kg - frac * mass_fuel_kg) * G

        speed = torch.sqrt(2.0 * weight / (rho * wing_area_m2 * cl))
        drag = weight / ld
        shaft_w = drag * speed / prop_efficiency + payload_power_w / alternator_efficiency

        bsfc = bsfc_kg_per_kwh(shaft_w) if callable(bsfc_kg_per_kwh) else bsfc_kg_per_kwh
        fuel_rate = bsfc * (shaft_w / 1000.0) / 3600.0  # kg/s

        endurance_s = endurance_s + dm / fuel_rate
        speed_sum = speed_sum + speed
        shaft_sum = shaft_sum + shaft_w / 1000.0

    ones = torch.ones_like(endurance_s)
    return MissionResult(
        endurance_s=endurance_s,
        fuel_burned_kg=mass_fuel_kg * ones,
        mean_cl=cl * ones,
        mean_speed_ms=speed_sum / n_steps,
        mean_shaft_kw=shaft_sum / n_steps,
        converged=torch.isfinite(endurance_s),
    )


def breguet_endurance_s(
    *,
    mass_total_kg,
    mass_fuel_kg,
    wing_area_m2,
    aspect_ratio,
    cd0,
    oswald_e,
    cl_max,
    altitude_m,
    bsfc_kg_per_kwh,
    prop_efficiency=0.84,
    stall_margin=1.15,
):
    """Closed-form Breguet endurance, for validating the step integration.

    This is the analytic solution of the same problem with **no electrical load**
    and a constant BSFC, so `simulate_loiter` must reproduce it to within the
    integration error when called with ``payload_power_w=0`` and a constant BSFC.
    Agreement is the gate; a mismatch means the integrator is wrong.

        E = (eta_p / (g * c)) * sqrt(2 rho S) * (C_L^1.5 / C_D) * (W1^-0.5 - W0^-0.5)
    """
    atm = isa(altitude_m)
    rho = atm.density_kgm3

    cl = loiter_cl(cd0, aspect_ratio, oswald_e, cl_max, stall_margin)
    cd = drag_polar(cl, cd0, aspect_ratio, oswald_e)

    c = bsfc_kg_per_kwh / (1000.0 * 3600.0)  # kg per joule of shaft work
    w0 = mass_total_kg * G
    w1 = (mass_total_kg - mass_fuel_kg) * G

    return (
        prop_efficiency
        / (G * c)
        * torch.sqrt(2.0 * rho * wing_area_m2)
        * (cl**1.5 / cd)
        * (w1 ** (-0.5) - w0 ** (-0.5))
    )
