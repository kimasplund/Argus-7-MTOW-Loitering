"""The design space, its constraints, and a mass model that cannot be gamed.

An optimiser handed a fixed empty mass and a free aspect ratio will run the
aspect ratio to its bound, because nothing pushes back. The mass model here is
the pushback: wing structure is sized from the actual root bending moment, so
buying span costs structure, and structure costs fuel at a fixed take-off mass.

Spar-cap scaling, derived rather than fitted:

    b        = sqrt(AR*S)
    c_root   = S / ((b/2)(1+lambda))
    M_root  ~ n_ult * W * (b/2) * k_lift      (k_lift = spanwise centroid of lift)
    h_spar   = (t/c) * c_root
    A_cap    = M_root / (h_spar * sigma)
    m_cap   ~ rho * A_cap * (b/2) * k_taper

Substituting gives m_cap ~ n_ult * W * AR^1.5 * sqrt(S) / ((t/c) * sigma), i.e.
**wing structural mass grows as AR^1.5**. That exponent is what stops the
optimiser running away to AR 30, and it is physics rather than a penalty term
bolted on to make the answer look sensible.

Calibration: one dimensionless coefficient is set so the model returns the
report's published 32.5 kg wing at the baseline design point. Everything else is
derived. The calibration constant is reported alongside results so the reader can
see exactly how much is fitted (one number) and how much is derived (the rest).
"""
from __future__ import annotations

from dataclasses import dataclass

import torch

G = 9.80665

# --- structural constants, sourced from the design report and materials pack ---
SIGMA_CAP_PA = 600e6  # compression allowable, report section 5 (buckling/damage knockdown)
RHO_CFRP = 1600.0  # kg/m^3, UD carbon/epoxy
K_LIFT = 0.40  # spanwise centroid of lift for a near-elliptic loading
K_TAPER = 0.55  # cap area tapers toward the tip; integrated fraction of root area
FUEL_RELIEF = 0.78  # wing-borne fuel offloads the root moment, report section 5
N_ULT = 5.7  # ultimate load factor, report section 5

# Non-spar wing mass (skins, ribs, flaperons, tanks) scales with area, calibrated
# to the materials pack's recommended build rather than the report's assumption.
SKIN_RIB_KG_PER_M2 = 4.6


@dataclass(frozen=True)
class Bounds:
    """Design-variable bounds. Ranges come from the spec's optimisation section."""

    wing_area_m2: tuple[float, float] = (2.5, 6.0)
    aspect_ratio: tuple[float, float] = (14.0, 30.0)
    taper_ratio: tuple[float, float] = (0.30, 0.70)
    mtow_kg: tuple[float, float] = (180.0, 320.0)
    altitude_m: tuple[float, float] = (2500.0, 5000.0)
    cd0: tuple[float, float] = (0.0153, 0.024)
    oswald_e: tuple[float, float] = (0.75, 0.92)
    bsfc_kg_per_kwh: tuple[float, float] = (0.25, 0.32)

    def names(self):
        return [f.name for f in self.__dataclass_fields__.values()]

    def lo_hi(self, device=None, dtype=torch.float32):
        lo = torch.tensor([getattr(self, n)[0] for n in self.names()], device=device, dtype=dtype)
        hi = torch.tensor([getattr(self, n)[1] for n in self.names()], device=device, dtype=dtype)
        return lo, hi


def wing_mass_kg(wing_area_m2, aspect_ratio, taper_ratio, mtow_kg, thickness_ratio, k_cal):
    """Physics-based wing mass. `k_cal` is the single calibrated coefficient."""
    span = torch.sqrt(aspect_ratio * wing_area_m2)
    c_root = wing_area_m2 / ((span / 2.0) * (1.0 + taper_ratio))
    h_spar = thickness_ratio * c_root

    m_root = N_ULT * mtow_kg * G * (span / 2.0) * K_LIFT * FUEL_RELIEF
    cap_area = m_root / (h_spar * SIGMA_CAP_PA)
    m_cap = k_cal * RHO_CFRP * cap_area * (span / 2.0) * K_TAPER * 2.0

    return m_cap + SKIN_RIB_KG_PER_M2 * wing_area_m2


def calibrate(baseline_wing_mass_kg=32.5, *, wing_area_m2=3.9, aspect_ratio=22.0,
              taper_ratio=0.45, mtow_kg=250.0, thickness_ratio=0.1371):
    """Solve for the one coefficient that reproduces the published wing mass."""
    t = lambda v: torch.tensor(float(v), dtype=torch.float64)
    unit = wing_mass_kg(t(wing_area_m2), t(aspect_ratio), t(taper_ratio), t(mtow_kg),
                        t(thickness_ratio), t(1.0)) - SKIN_RIB_KG_PER_M2 * wing_area_m2
    return float((baseline_wing_mass_kg - SKIN_RIB_KG_PER_M2 * wing_area_m2) / unit)


def empty_mass_kg(wing_area_m2, aspect_ratio, taper_ratio, mtow_kg, thickness_ratio, k_cal,
                  *, non_wing_airframe_kg=28.0, powertrain_kg=25.0, avionics_kg=6.0,
                  recovery_kg=7.0):
    """Dry mass excluding payload. Non-wing items are fixed at this fidelity."""
    return (
        wing_mass_kg(wing_area_m2, aspect_ratio, taper_ratio, mtow_kg, thickness_ratio, k_cal)
        + non_wing_airframe_kg + powertrain_kg + avionics_kg + recovery_kg
    )


def fuel_available_kg(mtow_kg, empty_kg, payload_kg=50.0):
    """Whatever mass is left after structure and payload becomes fuel."""
    return mtow_kg - empty_kg - payload_kg


def wing_fuel_capacity_kg(wing_area_m2, aspect_ratio, taper_ratio, thickness_ratio,
                          *, k_area=0.6062, chord_frac=0.50, span_frac=0.80,
                          net_frac=0.88, fuel_density_kgl=0.78):
    """Fuel the wing can physically hold.

    This is the constraint that the published design violates: it needs ~120 L and
    the wing holds ~50 L. `k_area` is the measured FX 63-137 section-area
    coefficient (shoelace integration), not the NACA-4-digit 0.68 that produced a
    12.2% error elsewhere in this project.
    """
    span = torch.sqrt(aspect_ratio * wing_area_m2)
    c_root = wing_area_m2 / ((span / 2.0) * (1.0 + taper_ratio))
    mac = (2.0 / 3.0) * c_root * (1 + taper_ratio + taper_ratio**2) / (1 + taper_ratio)
    gross_m3 = k_area * thickness_ratio * wing_area_m2 * mac
    usable_l = gross_m3 * 1000.0 * chord_frac * span_frac * net_frac
    return usable_l * fuel_density_kgl


def constraints(*, wing_area_m2, aspect_ratio, taper_ratio, mtow_kg, thickness_ratio,
                fuel_kg, span_limit_m=12.0):
    """Return a dict of constraint violations. Zero or negative means satisfied.

    Kept as smooth signed quantities rather than booleans so gradients survive and
    a penalty method has something to descend.
    """
    span = torch.sqrt(aspect_ratio * wing_area_m2)
    tank = wing_fuel_capacity_kg(wing_area_m2, aspect_ratio, taper_ratio, thickness_ratio)
    return {
        "span_over_limit_m": span - span_limit_m,
        "fuel_over_tank_kg": fuel_kg - tank,
        "fuel_nonpositive_kg": -fuel_kg,
    }
