# Finding: the Oswald efficiency in the design file is unvalidated, and three different quantities are being conflated

**Date:** 2026-08-20 · **Status:** open, blocks the optimiser · **Tools:** AVL 3.36 (verified), AeroSandbox 4.2.10, NeuralFoil (latest)

## Why this matters

At loiter C_L = 1.21, induced drag is **55.5%** of total drag (C_Di = 0.02492 against
C_D0 = 0.020). Every optimisation the programme has examined so far — riblets, boom
deletion, surface finish — attacks the smaller 44.5%. The Oswald factor is the single
largest lever in the drag model and it has never been validated.

## What was measured

AVL, run on the actual wing planform at **matched C_L = 1.21**, 12 sections, 24 spanwise
panels with tip-bunched spacing (inside the NaN limit of 40 established earlier):

| twist_tip | alpha | C_Dind | e (AVL) |
|---|---|---|---|
| 0° | 10.41° | 0.02157 | 0.9804 |
| **−3° (as designed)** | 11.71° | 0.02160 | **0.9786** |
| −5° | 12.57° | 0.02184 | 0.9673 |
| −7° | 13.43° | 0.02225 | 0.9486 |
| −9° | 14.30° | 0.02283 | 0.9236 |
| −11° | 15.16° | 0.02358 | 0.8932 |

## The conflation

**These are three different quantities and must not be compared directly:**

1. **AVL's e = 0.9786** is *inviscid span efficiency* — how close the lift distribution is
   to elliptic. It says the planform is excellent, which is expected for AR 22 with 0.45
   taper and mild washout.
2. **The design file's e = 0.85** is a *lumped Oswald factor* in `C_D = C_D0 + C_L²/(πARe)`,
   which conventionally also absorbs viscous lift-dependent drag. This is why real aircraft
   quote 0.7–0.85 while inviscid span efficiency exceeds 0.95.
3. **AeroSandbox's viscous buildup** implies a lumped value nearer **0.77** (crude
   subtraction, not authoritative).

Treating AVL's 0.9786 as if it were the design file's 0.85 would appear to hand the
programme **+7.1 h** that does not exist. That error would have propagated straight into
the optimiser's objective.

## The real open question

Is the *lumped* Oswald factor nearer 0.77 or 0.85? The spread is **dC_D = +0.00259**, worth
**−5.6 h** — larger than the riblet question and the boom-deletion question combined.

## What settles it

A proper drag polar: AVL spanload for the induced term, NeuralFoil section data integrated
spanwise for the viscous lift-dependent term, cross-checked against AeroSandbox's
AeroBuildup as an independent implementation. That is exactly what the Phase 2 buildup
module is for. **Until then, e = 0.85 is an assumption, and the optimiser must treat it as
a variable with a stated uncertainty band, not a constant.**

## Secondary observations

- Washout beyond −5° measurably degrades span efficiency (0.9786 → 0.8932 at −11°). The
  design pack calls for a Prandtl bell spanload, which deliberately trades induced
  efficiency for structural and adverse-yaw benefit — that trade has never been quantified
  here and `twist_tip_deg` is tagged `assumption` in the design file.
- AVL's alpha at C_L 1.21 (11.71°) implies it is not picking up the section camber from the
  AFILE — a cambered FX 63-137 should reach C_L 1.21 far earlier. Span efficiency is driven
  by planform and twist so the e trend stands, but **the AVL driver must verify camber
  ingestion before absolute angles from it are trusted.**
