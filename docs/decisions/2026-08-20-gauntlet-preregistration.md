# Gauntlet pre-registration: adoption gates for ARGUS-7 v2.0

**Written 2026-08-20, BEFORE the optimiser's challenger design was inspected.**
The Stage-1 Sobol result was known (8 M designs, 13.145% feasible); the refined
challenger was not. Pre-registration is the whole point: gates chosen after
seeing the result are not gates, they are rationalisations.

`skill-gauntlet` is built to A/B test skill and prompt revisions, and `plan.md`
correctly flagged it N/A for engineering. Its *method* transfers, and this is
that method applied to a design.

## Champion and challenger

- **Champion:** ARGUS-7 v1.0 as published in `docs/argus7_design_report.md`,
  including its own stated caveats, without retroactive correction.
  Design point: S 3.9 m², AR 22, taper 0.45, t/c 0.1371, MTOW 250 kg,
  loiter 4000 m, C_D0 0.020, e 0.85, BSFC 0.270 → **112.8 h published**,
  **112.98 h** under this project's own validated simulator.
- **Challenger:** the optimiser's best *feasible* design point — feasible
  meaning the fuel physically fits the wing and span ≤ 12 m.

## The conjunctive adoption gates

The challenger is adopted only if **every** gate passes. Conjunctive, not
weighted: a design that wins on endurance while failing a feasibility gate is
not a better design, it is the same error this programme has spent a week
correcting.

| # | Gate | Threshold | Why |
|---|---|---|---|
| **G1** | Endurance improvement | **≥ +5%** over the champion, evaluated by the *same* simulator on *both* | Below 5% is inside the model's own uncertainty; adopting on noise is worse than not adopting |
| **G2** | Wing fuel volume | Fuel required ≤ wing tank capacity, **no exception** | The champion violates this by 62 kg. A challenger that also violates it has not solved anything |
| **G3** | Span | ≤ 12.0 m | Packaging and transport limit, already in the spec |
| **G4** | Mass closure | Empty + payload + fuel = MTOW exactly | Non-negotiable |
| **G5** | Structural scaling honoured | Wing mass from the AR^1.5 physics model, not a fixed constant | An optimiser with a fixed empty mass will run AR to its bound; this gate confirms it did not |
| **G6** | Regulatory band declared | Result tagged with its MTOW band, not silently crossing | Assumption A1: soft constraint, but must be visible |
| **G7** | Buildability | AR ≤ 25, span ≤ 12 m, engine matched to a real unit from report §6's shortlist | From the spec's buildability proxy. A solo builder with ~€60k cannot jig an AR 30 wing |
| **G8** | No regression on stall margin | Loiter C_L ≤ C_Lmax / 1.15² | The champion's 1.21 comes from this constraint binding; the challenger must respect it too |

## Judging protocol

- **Blind panel.** Judges score both design points with identity stripped and
  order randomised (labelled A/B). They are not told which is published.
- **Planted-flaw key.** A third design is scored alongside, carrying deliberate
  seeded errors. Judges catching **< 80%** of planted flaws are declared
  uncalibrated and the panel is re-run. Verifying the judges before trusting
  their verdict is the part most often skipped.
- **Cross-check auditor.** Independent re-derivation of the challenger's
  headline numbers from the design variables, not from the optimiser's output.

## Declared model limitations, registered in advance

These are known weaknesses of the evaluation, stated now so they cannot be
discovered conveniently later:

1. **C_D0 and Oswald e are optimiser *variables*, not outputs of geometry.** The
   optimiser can therefore "buy" a better C_D0 within its bounds without paying
   for it in mass or manufacturability. Any challenger sitting at the low C_D0
   bound is exploiting this and must be discounted. Phase 2's build-up and AVL
   coupling is what closes it.
2. **The Oswald factor is unvalidated** — 0.77 vs 0.85 vs 0.98 depending on which
   quantity is meant (see `2026-08-20-span-efficiency-finding.md`). A ±0.08 swing
   is ±5.6 h, which is comparable to the G1 threshold itself.
3. **Non-wing airframe mass is fixed** at 28 kg. A challenger with a much larger
   fuselage is undercharged.
4. **The propulsion set does not close** at the champion's design point (C_P
   0.911 vs a ~0.25 ceiling), and the optimiser does not model propeller
   absorption at all. Neither design is currently flyable as specified.
5. **Cruise-climb and transit are not modelled** — pure loiter only.

## Decision rule

- All gates pass → adopt as v2.0, write `design/argus7_v2.yaml`, regenerate CAD.
- G1 fails, others pass → the design point is already near-optimal; report that
  as a positive finding rather than forcing a change.
- Any of G2–G8 fails → do not adopt; report the best design that *does* pass,
  even if its endurance is lower than the champion's published figure.

**If the honest answer is that the published design cannot be beaten while
holding its own fuel, that is the finding, and it gets reported as such.**
