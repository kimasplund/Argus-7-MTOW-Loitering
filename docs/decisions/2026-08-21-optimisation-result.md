# ARGUS-7 optimisation result and gauntlet verdict

**2026-08-21.** Gauntlet gates pre-registered 2026-08-20 before any challenger was seen.

## The result, like-for-like at 250 kg MTOW

| | v1.0 published | v1.0, honest model | **v2.0 optimised** |
|---|---|---|---|
| Endurance | 4.70 d (claimed) | **3.16 d** | **4.88 d** |
| Fuel fits the wing | No | **No** (101.5 kg into 66.1) | **Yes** (101.0 into 138.6, +37.6 margin) |
| Wing area | 3.9 m² | 3.9 m² | **5.46 m²** |
| Aspect ratio | 22 | 22 | 24.40 |
| Thickness | 13.7% | 13.7% | 17.6% |
| Span | 9.26 m | 9.26 m | 11.54 m |
| **Engine rating** | **17 kW** | 17 kW | **8.15 kW** |
| Loiter load fraction | — | **19%** | **33%** |
| Effective BSFC | 270 assumed | **425 g/kWh** | **328 g/kWh** |
| MTOW | 250 kg | 250 kg | 248.4 kg |

**The published 4.7-day claim is achievable at 250 kg — but not by the published
aircraft.** It needs a 40% larger, thicker wing and an engine less than half the size.

## The single largest lever is the engine, not the airframe

v1.0 installs 17 kW because *climb* needs it, then loiters at 3.4 kW — **19% load**,
where BSFC is 425 g/kWh rather than the assumed 270. Right-sizing to 8.15 kW lifts
load fraction to 33% and drops effective BSFC to 328. The climb constraint is then
exactly active: 8.11 kW required, 8.15 kW installed.

That tension — climb wants 12–17 kW, loiter wants 3.4 kW, one fixed engine cannot
serve both — is the central unsolved problem of this configuration, and no amount of
aerodynamic work substitutes for it.

## Gauntlet verdict on the earlier challenger: DO NOT ADOPT

G1 PASS · **G2 FAIL** · G3 PASS · G4 PASS · G5 pass-on-the-letter · **G6 FAIL** ·
**G7 FAIL** · G8 PASS. Conjunctive, so not adopted. The audit independently
re-derived endurance to **six significant figures** (171.404 h vs 171.403) — the
arithmetic was clean, the model was not.

## Four modelling errors found and fixed, all mine

1. **C_D0, e and BSFC as free variables** → optimiser returned 208.7 h by sitting in
   the corner of the box. Called in advance by the pre-registration.
2. **Raymer's Oswald correlation extrapolated to AR 22** → gave e = 0.485 against
   0.979 measured by AVL. Fixed with a surface fitted to 45 AVL runs, which showed
   span efficiency is nearly *flat* in aspect ratio.
3. **Wing thickness unpriced** → bought at 40% of its true drag cost. Fixed with a
   NeuralFoil measurement on the actual coordinates (+15.8% profile drag at t/c 0.20,
   and C_Lmax *rises* 1.868 → 1.973).
4. **Tank capacity understated 1.68×** → conflated fraction-of-chord with
   fraction-of-area, and fraction-of-span with fraction-of-volume. A 15–65% chord box
   holds **71.6%** of section area; the inner 80% of a taper-0.30 span holds **94%**
   of volume. Found by the audit, confirmed by integrating the real coordinates.

Every one was a constant used outside the regime it was fitted for, and every one was
caught by checking against an independently measured value rather than by the number
looking plausible. **208.7 h looked like a world record.**

## Also found: two of the report's own sensitivity anchors are wrong

The audit checked all three. C_D0 −0.004 → +0.358 d against the report's +0.36 d ✓.
But BSFC 250 gives **+0.377 d, not +0.5 d**, and 3,000 m gives **+0.198 d, not
+0.23 d**.

## Bounds still pinned, and what that means

The 320 kg unconstrained optimum (6.63 d) pins MTOW, span and thickness. Endurance
against the MTOW cap, engine right-sized throughout:

| MTOW cap | Endurance | Engine | Load | BSFC |
|---|---|---|---|---|
| 200 kg | 3.36 d | 6.70 kW | 38.6% | 313 |
| **250 kg** | **4.88 d** | 8.15 kW | 33.0% | 328 |
| 280 kg | 5.64 d | 9.13 kW | 31.7% | 333 |
| 320 kg | 6.25 d | 10.43 kW | 30.3% | 342 |

Endurance buys almost linearly with MTOW, so "how long can it fly" is really "how
heavy may it be" — a regulatory and operational question, not an aerodynamic one.

## Not yet modelled

- **The propeller cannot absorb its rated power.** C_P = 0.911 against a ~0.25
  ceiling at the v1.0 point. Neither design is flyable as specified until this is
  resolved; a right-sized 8 kW engine helps but does not by itself close it.
- Cruise-climb and transit; pure loiter only.
- Non-wing airframe mass fixed at 28 kg regardless of size.
- The 5–7 day target needs 250 kg+ **and** the propulsion set to close.
