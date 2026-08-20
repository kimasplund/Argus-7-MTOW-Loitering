"""ISA standard atmosphere, differentiable and batched (PyTorch).

Model
-----
ICAO Standard Atmosphere (ICAO Doc 7488/3), identical to the US Standard
Atmosphere 1976 over the range covered here: a linearly-lapsing troposphere from
sea level to 11 km geopotential and an isothermal lower stratosphere from 11 km
to 20 km.  Transport properties come from Sutherland's law.

Altitude convention
-------------------
``isa()`` takes GEOPOTENTIAL altitude by default, because that is what the ISA is
defined on and what the published tables are indexed by.  Pass ``geometric=True``
to supply true geometric altitude instead; it is converted with the standard
Earth radius before use.  The difference is small but not nil: 4000 m geometric
is 3997.48 m geopotential (-0.016 K, +0.03% density), and at 11 km it is 19 m.

Differentiability
-----------------
Everything is expressed as elementwise torch ops on the input tensor, so grads
flow to altitude on CPU or CUDA, in float32 or float64, for any input shape.

The layers are joined by ``min(H, 11000)`` rather than a branch, which keeps a
single formula valid in both layers:

    T   = T0 + L * Hc                                        with Hc = min(H, 11 km)
    p   = p0 * (T/T0)**(-g0/(L*R)) * exp(-g0*(H - Hc)/(R*T))

Below the break the exponential factor is exactly 1 and the power law is the
tropospheric solution; above it the power law is frozen at its 11 km value and
the exponential is the isothermal solution.  Both branches are finite for every
H in range, so there is no NaN-gradient hazard of the kind ``torch.where`` has
when one branch is undefined.

p is C1 across the tropopause (d ln p/dH = -g0/(R*T) and T is continuous), so
second-order optimisers are safe on pressure.  T and rho have a kink there: the
lapse rate steps from -6.5 K/km to 0.  At exactly 11 km autograd returns the
tropospheric one-sided derivative -- finite, never NaN.  If a smooth second
derivative is needed (trajectory optimisation that crosses the tropopause),
pass ``blend_m`` to replace the hard min with a softmin of that width; the
result is C-infinity and matches the exact ISA to <1e-6 relative more than a few
blend widths away from 11 km.  ARGUS-7 loiters at 4 km, so the default is the
exact, unblended ISA.

Range
-----
0 to 20 km is the validated envelope (``ISA_MAX_ALTITUDE_M``); the model is
extended down to -5 km for completeness.  Outside that, the isothermal formula
would silently keep extrapolating (the real atmosphere starts warming again at
20 km, L = +1.0 K/km), so ``isa()`` raises by default.  Pass ``strict=False`` to
skip the check -- it costs a device-to-host sync, which matters inside a hot
optimiser loop or under torch.compile.
"""
from __future__ import annotations

from typing import NamedTuple

import numpy as np
import torch
import torch.nn.functional as F

# --- ISA defining constants (ICAO Doc 7488/3) ------------------------------
T0_K = 288.15                 # sea-level temperature
P0_PA = 101325.0              # sea-level pressure
LAPSE_RATE_KM = -0.0065       # troposphere temperature gradient [K/m]
TROPOPAUSE_M = 11000.0        # geopotential altitude of the 11 km break
T_TROPOPAUSE_K = T0_K + LAPSE_RATE_KM * TROPOPAUSE_M   # 216.65 K
GRAVITY_MS2 = 9.80665         # standard gravity, constant with geopotential H
R_AIR_JKGK = 287.05287        # R* / M = 8314.32 / 28.9644, ICAO value
GAMMA_AIR = 1.4               # ratio of specific heats, calorically perfect air
EARTH_RADIUS_M = 6356766.0    # ISA nominal Earth radius for the H <-> h map

# --- Sutherland's law for air (White, "Viscous Fluid Flow", 3rd ed. Eq 1-36;
#     the same coefficients ICAO uses).  mu = beta*T^1.5/(T+S).
SUTHERLAND_BETA = 1.458e-6    # [kg/(m s sqrt(K))]
SUTHERLAND_S_K = 110.4        # [K]

# Validated altitude envelope [m geopotential].
ISA_MIN_ALTITUDE_M = -5000.0
ISA_MAX_ALTITUDE_M = 20000.0

# sea-level density, derived (1.225 kg/m3) -- exported for convenience.
RHO0_KGM3 = P0_PA / (R_AIR_JKGK * T0_K)

_PRESSURE_EXPONENT = -GRAVITY_MS2 / (LAPSE_RATE_KM * R_AIR_JKGK)  # +5.25588

__all__ = [
    "Atmosphere",
    "isa",
    "isa_numpy",
    "geopotential_altitude",
    "geometric_altitude",
    "T0_K", "P0_PA", "RHO0_KGM3", "GRAVITY_MS2", "R_AIR_JKGK", "GAMMA_AIR",
    "LAPSE_RATE_KM", "TROPOPAUSE_M", "T_TROPOPAUSE_K",
    "ISA_MIN_ALTITUDE_M", "ISA_MAX_ALTITUDE_M",
]


class Atmosphere(NamedTuple):
    """Atmospheric state.  Fields are tensors (or numpy values from
    :func:`isa_numpy`) with the same shape/dtype/device as the altitude input."""

    temperature_K: torch.Tensor
    pressure_Pa: torch.Tensor
    density_kgm3: torch.Tensor
    speed_of_sound_ms: torch.Tensor
    dynamic_viscosity_Pas: torch.Tensor

    @property
    def dynamic_viscosity(self):
        """Alias for :attr:`dynamic_viscosity_Pas` [Pa s]."""
        return self.dynamic_viscosity_Pas

    @property
    def kinematic_viscosity_m2s(self):
        """nu = mu / rho [m^2/s] -- the quantity Reynolds numbers need."""
        return self.dynamic_viscosity_Pas / self.density_kgm3


def _as_float_tensor(x) -> torch.Tensor:
    """Accept a tensor / array / list / scalar; return a floating tensor.

    Integer and python-scalar inputs are promoted to float64 rather than to the
    global default dtype: an int tensor cannot be raised to a fractional power,
    and float32 would quietly cost 7 digits on a quantity nobody expects to be
    approximate.  A floating tensor is passed through untouched, so dtype and
    device are the caller's choice.
    """
    if not isinstance(x, torch.Tensor):
        x = torch.as_tensor(x)
    if not x.dtype.is_floating_point:
        x = x.to(torch.float64)
    return x


def geopotential_altitude(geometric_m) -> torch.Tensor:
    """Geometric altitude h [m] -> geopotential altitude H = r*h/(r+h) [m]."""
    h = _as_float_tensor(geometric_m)
    return EARTH_RADIUS_M * h / (EARTH_RADIUS_M + h)


def geometric_altitude(geopotential_m) -> torch.Tensor:
    """Geopotential altitude H [m] -> geometric altitude h = r*H/(r-H) [m]."""
    H = _as_float_tensor(geopotential_m)
    return EARTH_RADIUS_M * H / (EARTH_RADIUS_M - H)


def _check_range(H: torch.Tensor) -> None:
    Hd = H.detach()
    if not bool(torch.isfinite(Hd).all()):
        raise ValueError("altitude contains non-finite values (NaN or inf)")
    lo, hi = float(Hd.min()), float(Hd.max())
    if lo < ISA_MIN_ALTITUDE_M or hi > ISA_MAX_ALTITUDE_M:
        raise ValueError(
            f"geopotential altitude [{lo:.1f}, {hi:.1f}] m is outside the validated "
            f"ISA range [{ISA_MIN_ALTITUDE_M:.0f}, {ISA_MAX_ALTITUDE_M:.0f}] m; the "
            "two-layer model would extrapolate silently. Pass strict=False to allow it."
        )


def isa(
    altitude_m,
    *,
    geometric: bool = False,
    blend_m: float = 0.0,
    strict: bool = True,
) -> Atmosphere:
    """ISA state at ``altitude_m``.

    Parameters
    ----------
    altitude_m
        Geopotential altitude [m] (or geometric, with ``geometric=True``).  Any
        shape; tensors keep their dtype and device.
    geometric
        Treat the input as true geometric altitude and convert it first.
    blend_m
        Width [m] of a smooth softmin at the 11 km layer break.  0 (default)
        gives the exact ISA with a lapse-rate kink; >0 gives a C-infinity model.
    strict
        Validate the altitude range (one host sync).  Disable in hot loops.

    Returns
    -------
    Atmosphere
        ``(temperature_K, pressure_Pa, density_kgm3, speed_of_sound_ms,
        dynamic_viscosity_Pas)``.
    """
    H = _as_float_tensor(altitude_m)
    if geometric:
        H = EARTH_RADIUS_M * H / (EARTH_RADIUS_M + H)
    if strict:
        _check_range(H)

    # Altitude clipped at the tropopause: the argument of the lapse-rate law.
    if blend_m > 0.0:
        # min(H, Ht) == Ht - softplus(Ht - H), smoothed with width blend_m.
        Hc = TROPOPAUSE_M - F.softplus(
            TROPOPAUSE_M - H, beta=1.0 / blend_m, threshold=40.0
        )
    else:
        Hc = torch.clamp(H, max=TROPOPAUSE_M)

    T = T0_K + LAPSE_RATE_KM * Hc
    # Tropospheric power law, frozen above the break, times the isothermal
    # factor for whatever altitude remains above it (zero below the break).
    p = P0_PA * (T / T0_K) ** _PRESSURE_EXPONENT * torch.exp(
        -GRAVITY_MS2 * (H - Hc) / (R_AIR_JKGK * T)
    )
    rho = p / (R_AIR_JKGK * T)
    a = torch.sqrt(GAMMA_AIR * R_AIR_JKGK * T)
    mu = SUTHERLAND_BETA * T ** 1.5 / (T + SUTHERLAND_S_K)
    return Atmosphere(T, p, rho, a, mu)


def isa_numpy(altitude_m, **kwargs) -> Atmosphere:
    """numpy convenience wrapper around :func:`isa`.

    A scalar in gives python floats out; an array in gives float64 ndarrays of
    the same shape.  Keyword arguments are forwarded to :func:`isa`.
    """
    arr = np.asarray(altitude_m, dtype=np.float64)
    out = isa(torch.from_numpy(np.atleast_1d(arr).copy()), **kwargs)
    if arr.ndim == 0:
        return Atmosphere(*(float(v.item()) for v in out))
    return Atmosphere(*(v.numpy().reshape(arr.shape) for v in out))
