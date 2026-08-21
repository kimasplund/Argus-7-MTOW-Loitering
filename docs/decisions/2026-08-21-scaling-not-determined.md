# MTOW scaling: what is established, and what is not

**2026-08-21.** Requested as "document the scaling law thoroughly". The thorough
answer is that **there is no reliable scaling law in this data**, and the useful
document is the one that says so with the evidence.

## Why no law

Three power-law fits, from three datasets, all of the same quantity:

| Dataset | E[h] = a·MTOW^b | R² | Max residual |
|---|---|---|---|
| First sweep, unrefined, 196–595 kg | b = **0.869** | 0.956 | 12.3% |
| Refined, 178–350 kg | b = **1.452** | 0.975 | 10.1% |
| Combined, 178–595 kg | b = **0.998** | 0.897 | 23.4% |

Each looks respectable alone. An exponent that moves from 0.87 to 1.45 depending
on the subset is a curve fit, not a law.

## The reason, which is itself the finding

Only one design quantity scales cleanly:

| Quantity | Exponent | Scatter |
|---|---|---|
| **Engine power** | MTOW^0.82 | **6.1%** |
| Span | MTOW^0.90 | 20.0% |
| Wing area | MTOW^1.19 | 24.6% |
| Aspect ratio | MTOW^0.62 | **30.5%** |

Engine power is tight because the **climb constraint pins it** — it is the one
variable with an active constraint at every design point. Everything else is
scattered because **the objective is genuinely flat in those directions**: the
optimiser returned AR 17.0 at 178 kg and AR 29.7 at 200 kg, with sensible
endurance both times. It is not failing to converge; there is a broad ridge and
it lands wherever the sampler looked.

The marginal exchange rate shows the same thing and is **not monotone**:
1.29 → 0.36 → 0.68 → 0.81 → 0.47 h/kg across consecutive refined points. An
earlier report of "a four-fold decline in marginal returns" was reading a trend
into noise, and is withdrawn.

## What IS established

- **Endurance increases monotonically with MTOW**, from roughly **2.8 days at
  180 kg to 9.9 days at 600 kg**. The direction and rough magnitude are solid
  across every dataset.
- **Every point balances.** Static margin inside 5–15% MAC at both full fuel and
  dry, with the fuel fitting the wing. Verified for two points against the
  authoritative `argus7.analysis.balance`, which is AVL-cross-checked.
- **Engine power scales as MTOW^0.82**, tightly, because climb pins it.
- **Aspect ratio is not a strong lever.** This is robust, comes from an
  independent AVL measurement (span efficiency is nearly flat in AR: 0.989 at
  AR 14 to 0.969 at AR 30), and contradicts the design's founding premise that
  high aspect ratio was the route to endurance.
- **Stability is nearly free once the layout is in the search.** Moving the wing
  station from `x_le_frac` 0.22 to about 0.40 balances the aircraft *and* puts
  the tanks at the CG, giving CG travel of −0.08% to −0.29% MAC — better than the
  "<0.5% MAC" the design pack claimed but never achieved.

## What is NOT established

- The exponent.
- The marginal exchange rate between weight and endurance.
- The optimal planform at any given weight.

## What settling it would take

Either a denser sweep with proper convergence at every MTOW point — the flat
ridge means single-shot optima are unreliable, so each point needs multi-start
refinement — or, better, a **Pareto front** rather than a single optimum per
weight, which would show the ridge directly instead of sampling one arbitrary
point on it.

## Model limits that bound any future law

- Fuselage fixed at 3.4 m and non-wing airframe mass fixed at 28 kg, regardless
  of a wing that grows from 3.9 to 12 m². A 600 kg aircraft is undercharged.
- Pure loiter only: no transit, climb or reserve.
- Mass model calibrated on a single point (the published 32.5 kg wing).
- The batched balance model used in the search agrees with the authoritative
  scalar module to ~5% MAC, not exactly; search with it, verify with the other.
