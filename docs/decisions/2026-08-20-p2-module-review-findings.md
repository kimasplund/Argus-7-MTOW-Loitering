# Phase 2 module review findings — carried, not yet fixed

Each Phase 2 module was adversarially reviewed. The atmosphere review is recorded
in full here because its method is worth repeating: the reviewer found defects by
**falsification** — mutating the source and checking whether the suite noticed —
rather than by reading it.

## Atmosphere module

1. **Real defect: `blend_m > 0` silently breaks hydrostatic balance.** The closed
   form is the hydrostatic solution only because `H - Hc` and `dHc/dH` are never
   simultaneously non-zero under a hard `min`. The softmin makes them overlap,
   leaving a residual of **1.10e-5 per metre of blend width** (analytic and
   measured agree to 0.3%). So the "C-infinity option for trajectory optimisers"
   would hand them a model whose returned density and differentiated pressure
   gradient are different atmospheres.
   **Impact on current results: none.** Everything in this project runs the
   default `blend_m=0`, where the residual is 4.5e-16.
2. **A reference value was wrong and the tolerance was tuned to hide it.** The
   10 km pressure row read 26436.3 Pa; the module's own declared gas constant
   gives 26436.2426. It was the only row needing the slack, and the slack's
   stated justification referred to a comparison the test does not perform.
3. **A mutant survived all 49 tests.** Changing `EARTH_RADIUS_M` from 6356766 to
   6371000 — exactly the "correction" someone would plausibly make — passed
   everything, because the geopotential test used `abs=0.5` against a 0.042 m
   discriminant, 12x too loose.
4. **A gradient check was vacuous, proved by falsification.** Replacing viscosity
   with a constant still passed `test_gradcheck_all_outputs` at all seven
   altitudes: `atol=1e-6` is 3200x larger than the true dmu/dH ~ 3.14e-10, and
   above 11 km that derivative is exactly zero.
5. **Two tautologies:** asserting `p == rho*R*T` and `a^2 == gamma*R*T` when the
   source defines rho and a by those very expressions.

## Why this does not invalidate the optimisation results

- ISA values were independently cross-checked against AeroSandbox 4.2.10, an
  entirely separate implementation, agreeing to **< 2e-6 relative** on pressure
  and density at 0 / 4000 / 11000 / 20000 m.
- The reviewer independently recomputed every published value at 40 decimal
  places with mpmath from the ICAO definitions and found no fudged constant.
- The mission simulator's own gates hold regardless: it reproduces closed-form
  Breguet to 0.0000% and the report's published endurance to +0.2%.
- The atmosphere module also independently corroborated the XFOIL work:
  nu(4 km) = 2.0279e-5 gives Re = 992.5k at root chord 0.5807 m and 34.66 m/s,
  reproducing the recorded Re 992372 to **0.01%**.

## Carried to Phase 3

Fix the blend residual (or delete the blend option), correct the 10 km reference
value and remove its slack, tighten the geopotential test until the Earth-radius
mutant dies, and either tighten or delete the viscosity gradient assertion. None
blocks the current results; all are cheap.
