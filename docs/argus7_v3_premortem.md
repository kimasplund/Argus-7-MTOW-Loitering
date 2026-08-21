# Premortem: building ARGUS-7 v3.0 — first flight and a ≥24 h demonstration

**Horizon:** 2028-02-29 (18 months from a 2026-09-01 start) · **Success was defined as:** one ARGUS-7 prototype flying a ≥24 h demonstration by Feb 2028, within €60k, solo builder plus contractors.

**Note on the percentages:** shares of failure — "if this dies, this is what killed it" — not the probability the plan fails overall. They sum to ~100.
**Overall chance this misses its success definition by the horizon:** ~75%.

**Assumptions I'm working from** (correct any and the analysis moves):
- Start 2026-09-01. The €60k and 18 months are the envelope the v1.0 premortem used, carried forward unchanged onto a heavier aeroplane.
- The €60k is the whole programme and excludes the 50 kg payload at real COTS prices — a TrakkaCam-class gimbal alone exceeds the budget — so the demonstration flies instrumented ballast.
- I have no information about the builder's composite experience, workshop size, remote-pilot qualification, or whether the €60k is their own money. All four are load-bearing; none is in the record.
- Fuel type is **not yet chosen**. This matters more than anything else on the page.
- Cost bands are mine, scaled from the v1.0 premortem's figures by the geometry change; labour-hour bands are mine and weakly sourced. Regulatory specifics are flagged where I could not verify them.

---

## The Autopsy

**The strongest case for this plan:** v3.0 is the first version of this aircraft that survives most of its own audit. The mass budget closes to −0.01 kg; the static margin is positive at both fuel states, verified against `argus7.analysis.balance`, which is AVL-cross-checked and mutation-tested; the propeller absorbs 99.3% of the 10.845 kW rating in climb and returns η 0.855 at the loiter point — I re-ran the BEMT for v3.0 to get those two numbers, because the propeller record itself was run against the retired v2.0 at 8.15 kW and its published 99%/0.858 pair belongs to two different propellers on a different aeroplane — where the published v1.0 set could absorb 4.7 kW of 17; the fuel clears the tank by 4.4%; and endurance is computed on a part-load BSFC curve instead of the flat constant that inflated v1.0 by 49%. The programme has also demonstrated it will kill its own results — it retired v2.0 against adoption criteria written before the answer was seen, published a "there is no scaling law" non-result rather than a curve fit, and mutation-tested its own suite. Vanilla VA001's 8-day record at 191 kg says the physics class is real. Every remaining defect looks like a measurement away, not a discovery away.

**The claim held with the most certainty is that v3.0 now balances and holds its fuel, so two v1.0 failure modes are retired.** That is the first thing attacked below, and it does not survive intact. It survives in the model's own units and fails in a builder's: +5.79% MAC is **30.7 mm** of stability on a 0.531 m MAC, and "the fuel fits" is true at the tank model's assumed 0.78 kg/L and false at mogas density. Both are recorded as *retired*. Neither is.

**And the balance claim fails the programme's own written threshold, not merely mine.** The specification's stability requirement is **8% ≤ SM ≤ 20% MAC** (`docs/superpowers/specs/2026-08-20-argus7-cad-sim-optimisation-design.md`, line 109). The search that produced v3.0 ran a 5–15% window — a pre-registered threshold moved without anyone noticing, which is the precise failure the programme's own pre-registration exists to prevent, and which it has now committed on the design point it adopted. `scripts/run_optimisation_layout.py` records this in its own header: *"v3.0 landed at +5.79% and duly FAILED the real gate."* Re-runs at the real threshold exist in `opt_runs/layout_sm8.json` and `opt_runs/layout_sm8_span12.json`, and a `design/argus7_v4.yaml` built from the second of them returns **+12.78% MAC full and +13.72% dry** against the authoritative module with a mass budget that closes to 0.00 kg. This premortem is written against v3.0 because that is the design point the brief names as current; a reader should know that the repository already contains its successor, and that the successor exists because v3.0 failed a stability gate this document's mode #3 otherwise has to discover from first principles.

Seven ways this died, ranked by probability.

### 1. The 313 kg bill of materials broke €60k before the wing came out of the mould
**Probability:** ~30% — the budget was written for a 250 kg aeroplane and never re-scaled for a wing 52% larger in area, a fuel system 58% larger in volume, and a recovery system for 25% more mass.
**Cause of death:** priced against v3.0's actual geometry the programme totals **€54.5–84.5k** with one of everything, no contingency, and the payload valued at zero: wing tooling €14–21k (v1.0's €9–14k scaled by the 1.52× wing area), 45.4 kg of laminate €6–9k, fuselage plus 4.06 m booms and tail €4–6k, engine donor with ECU, generator and auxiliary oil system €5–7k, the dyno programme €8–12k, a canopy resized for 313 kg (≈106 m² for 6 m/s, against 85 m² sized for 250 kg) with drop-test articles €5–8k, takeoff provision €3–5k, avionics and ground station €3–6k, 216 L of integral tankage €1.5–2.5k, insurance, aerodrome access and fuel €5–8k. Midpoint €69k. The ceiling is €60k.
**How it unfolded:**
- Sep–Oct 2026: engine, autopilot and tooling board bought; €11k committed. The wing mould quote arrives at €18k against a €10k mental figure, because it is for a 5.63 m half-mould, not a 4.63 m one.
- Nov–Dec 2026: the dyno house quotes €10k for a mapped part-load survey and bills the 100 h endurance run separately. Committed spend crosses €38k with nothing built.
- Jan–Mar 2027: the builder buys the tooling anyway and defers the dyno "until the airframe is real."
- Sep 2027: the airframe is real, the money is gone, and the number the whole aircraft is designed around has still never been measured.
**The assumption that allowed it:** that scaling the aeroplane 250 → 313 kg was a design decision rather than a procurement decision. The optimiser moved MTOW; nobody re-costed anything.
**First warning sign:** the wing mould quote landing above €15k, visible by end of October 2026.
**Reference class:** the v1.0 premortem put ~30% here on the same class — kit/experimental and small-UAV programmes landing at 2–3× first budget, asserted there without a source and marked weakly sourced here rather than replaced by a firmer number I do not have. **Disanalogy:** the engine is now 10.8 kW instead of 17 and the propulsion set closes on paper, removing one re-buy cycle — that pushes the multiplier down; the 52% larger wing, 58% more fuel volume and 25% more recovery mass push it up harder. Net, the probability holds and the overshoot grows.

### 2. One pair of hands, eight workstreams, and a 24 h flight that needs a crew
**Probability:** ~20% — the v1.0 plan had three sequential full-time workstreams and slipped on that; v3.0 has eight, and the last one is an all-night operation the plan has never staffed.
**Cause of death:** internal layout, wing tooling and layup, fuselage and booms, engine conversion and bench running, avionics and C2, recovery integration and drop test, authorisation paperwork, flight test. My own hour bands for a composite airframe this size total **1,900–3,150 h**. Eighteen months at 20 h/week is 1,560 h; at genuine full time ~3,120 h. The plan fits only at full time, only at the optimistic end of every band, and only with no rework.
**How it unfolded:**
- Oct 2026–Feb 2027: the plug and mould consume every evening; the engine bench never starts, so the BSFC question stays open and every downstream number stays provisional.
- Mar–Aug 2027: wings out of the mould six weeks late; the integral tanks leak at first pressure test and the inboard bay is re-sealed twice.
- Sep–Nov 2027: the engine bench finally runs and eats the autumn. The airframe sits cured and unassembled.
- Dec 2027: first flight slips past the weather window. The 24 h demonstration additionally needs an airspace reservation, a night permission and three people on rotating watch — none of whom have been asked. It moves to spring 2028, past the horizon, and 18 months becomes 26 by arithmetic rather than by failure.
**The assumption that allowed it:** that "build a 24 h aircraft" and "conduct a 24 h flight" are the same project. The second is an operation with a roster, and it has no line in the plan.
**Reference class:** the v1.0 premortem's own mode 2 — solo-builder aircraft programmes slipping 1.5–2× on calendar (asserted there, weakly sourced, carried forward). **Disanalogy:** contractors absorb fabrication peaks, which helps. But this programme's tightest reference class is itself: the design point moved v1.0 → v2.0 (retired) → v3.0 inside 36 hours on 20–21 Aug 2026, every move forced by finding an error rather than by new information. The base rate that v3.0 is the final planform is low, and each further move re-cuts the calendar.

### 3. The 31 mm static margin was spent by the internal layout nobody had drawn
**Probability:** ~15% — the margin is the smallest allowed by a search window that was itself 3 points below the specification's, and three of the numbers that produce it are assumptions the build will overwrite.
**Cause of death:** +5.79% MAC on a 0.531 m MAC is **30.7 mm**. Three things eat it:
- **The powertrain mass is a linear extrapolation.** `run_optimisation_final.py` sets `powertrain = 25.0 × p_kW/17.0`, giving 15.95 kg at 10.845 kW — as if exhaust, starter, belt, prop, mounts, auxiliary sump and generator all shrank with rated power. The research pack's own estimate for a stripped PCX160 donor alone is 15.5 kg **[UNV — must weigh donor]**, before the €3k of EFI/exhaust/starter, the belt and prop, the 2 L auxiliary sump and the 1 kW generator the report requires. A realistic installed powertrain is ~25 kg. It sits at x = 3.05 m, 1.59 m behind the CG. Putting 24.8 kg there and taking the 8.85 kg out of fuel to hold MTOW gives, from the authoritative module, **−2.69% MAC at full fuel and −10.74% dry**: unstable at both, from one component mass.
- **The payload station is an assumption.** All 50 kg is placed at x = 0.432 m, 12.7% of fuselage length from the nose — a nose gimbal's station applied to the whole bay, including the eNB, the mission computer, the power conditioning and the backhaul terminal. **92 mm of aft movement in the payload centroid takes the margin to zero dry; 192 mm takes it to zero at full fuel.** The dry case binds, and it is the one a builder reaches on every landing. Moving half the payload one metre aft moves the centroid **500 mm** — five times the dry allowance.
- **The layout that would settle both has never been done.** `research/configuration_hypotheses.md` records it as the item that "must not be deferred": settle the equipment layout and solve for `wing.x_le_frac`. It is still open.
**How it unfolded:**
- Jan 2027: the internal layout drawing is finally made because the fuselage mould needs it. The bay will not take 50 kg forward of the wing without the gimbal fouling the nose loft.
- Feb 2027: the donor engine is weighed. 24.8 kg installed, not 15.95.
- Mar 2027: restoring +5.79% requires `x_le_frac` 0.354 → 0.393 — the wing station and the tail with it move **135 mm aft**, solved against `argus7.analysis.balance`. The fuselage plug is already cut. Six weeks and €7k to re-cut, or 12.2 kg of nose ballast displacing 12.2 kg more fuel — 21 kg of fuel gone in total, ~13% of the endurance.
- The programme takes the ballast, because it is March and the money is short.
**The assumption that allowed it:** that a stability margin verified in software is a stability margin, when the component masses and stations feeding it were extrapolations rather than weighings.
**First warning sign:** the first weighed component mass that differs from the design file by more than 2 kg — available the day the donor engine is on a scale, if anyone puts it on one.

### 4. There was nowhere to take off from
**Probability:** ~12% — this is the mode the plan never mentions at all: no landing gear mass, no launcher, no aerodrome, no ground roll ever computed.
**Cause of death:** at 313 kg on 10.845 kW driving a 1.04 m disc, ideal-actuator static thrust at a figure of merit of 0.65 is **407 N**, T/W 0.132. Rotating at 1.2 V_stall = 27.6 m/s, the ground roll is **410 m on smooth tarmac and ~790 m on grass** — my own hand calculation at rolling friction 0.02 and 0.08, since the repository contains no takeoff model of any kind to check it against. Nothing in the mass budget is landing gear: the airframe line is wing 45.4 kg plus a non-wing constant of 28 kg the optimiser holds fixed regardless of aircraft size, and recovery is a flat 7.0 kg. A launcher for 313 kg is a €200k-class machine. And once it is off the ground the margin is **1.6%**: the optimiser's climb constraint asks 10.676 kW against 10.845 kW installed — and that constraint is a sea-level rate of **2.0 m/s**, itself a relaxation of the v1.0 report's 3 m/s, which at 313 kg needs **14.33 kW, 32% more than is installed**. So the aeroplane needs 600–800 m of paved runway, and a runway needs an owner who will accept a 313 kg unmanned aircraft carrying **216 L of petrol**, plus an authorisation to fly it BVLOS overnight. Two corrections to the brief here. First, the v1.0 premortem did not assume regulation away: regulation was its mode #4 at ~15% and its **most-dangerous** mode, with a SORA pre-application named as a month-1 action and SAIL III–IV as the walk-away. I have demoted it from a standalone mode to the second half of this one and a walk-away item, on the argument that the binding scarcity is a runway and an operator's signature rather than a rule — and that argument is the weakest joint in this autopsy. Second, on the bands themselves: 250 and 313 kg sit in the same EU Specific-category conversation, the same SORA ground-risk column by dimension (9.26 m and 11.27 m are both over 8 m), and the same sub-500 kg third-party insurance band — I have **not** verified these against current text, and it is one of the walk-away items below. What changed is not which rule applies but who will say yes: the fuel load went from ~136 L to 216 L, and an emergency recovery at MTOW on a canopy sized for 250 kg descends at 6.7 m/s instead of 6.0, giving a **7.0 kJ touchdown against the report's 4.5 kJ** — +57% on the number the ground-risk case is argued with.
**How it unfolded:**
- Apr 2027: the first aerodrome conversation. The operator asks for the ground roll, the touchdown energy, and the insurance certificate. Two of the three do not exist.
- Jun 2027: a second aerodrome offers 700 m of grass, conditional on an authorisation.
- Sep 2027: the authorisation response returns asking for containment and ground-risk evidence built on a touchdown energy the programme has not recomputed since 250 kg.
- Dec 2027: taxi trials on the grass strip reach 19 m/s in 500 m and stop. The aircraft has never left the ground.
**The assumption that allowed it:** that recovery is a solved problem because a parachute is in the mass budget, and that takeoff is not a problem because nobody wrote it down. The simulator models pure loiter — no transit, no climb, no reserve, and no ground.
**First warning sign:** the first aerodrome asking for a ground-roll figure, at any time from April 2027 — or the absence of that conversation by then.

### 5. The demonstration passed and the claim didn't — because no engine burns the fuel the tank needs at the efficiency the design assumes
**Probability:** ~10% — this is the mode where the plan works and that is what kills it.
**Cause of death:** three of v3.0's numbers cannot be satisfied by one engine.
- The 6.33-day figure rests on an **effective 339 g/kWh at 30.6% load**, which under the programme's own Willans fit (`bsfc_full × (0.8471 + 0.1529/load)`) implies a **full-load BSFC of ~252 g/kWh**. That is the optimiser's lower bound of 0.250, and `research/design_pack.md` records the same number as a **verified product gap**: "CI diesel (250 g/kWh, what-if — no production engine exists in 5–15 kW class)".
- The tank holds **215.4 L usable** — a pure geometry result, independent of what goes in it; the model then converts that volume at an assumed 0.78 kg/L to the 168.0 kg capacity the design file records. 160.6 kg of fuel needs 215.6 L at mogas density 0.745 and 223 L on a hot day at 0.72. **The fuel fits only if the fuel is kerosene.** At Jet-A densities (0.775–0.80) the margin is +4.0% to +7.3%; at mogas it is −0.1% to −3.5%.
- Kerosene at ~10.8 kW means the programme's own heavy-fuel shortlist: RCV DF140LC at 8.61 kW / 330 g/kWh (`research/design_pack.md` §4), or Orbital HFDI-150 at 8.8 kW / 330 g/kWh (report §6). Both are **18–19% short of the 10.68 kW the relaxed climb constraint demands**, and both are 32% worse on BSFC than the design assumes.
So the fuel that fits requires an engine that misses the power and the efficiency; the engine that makes the power burns a fuel that does not fit. At a dyno-measured 330 g/kWh full-load the aircraft flies **116 h (4.84 d)**, not 152. A realistic stack of individually modest degradations — a normal rather than exceptional surface finish (cleanliness 1.15), 280 g/kWh full-load, +10 kg of powertrain out of the fuel, prop η 0.83 — gives **119 h (4.96 d), 22% below the design point**; add the low end of the open Oswald range (e 0.77 rather than 0.848) and it is **115.7 h (4.82 d), 24% below**. Every one of these is `simulate_loiter` on v3.0's own geometry, and every one of them is still a pure-loiter number with no transit, climb or reserve in it.
**How it unfolded:**
- Feb 2027: the dyno sheet returns 318 g/kWh full-load on mogas at the best point.
- Mar 2027: the fuel decision is forced. Mogas keeps the power and loses the tank margin; kerosene keeps the tank and loses 2 kW of climb.
- Oct 2027: the 24 h demonstration flies and passes — but only just, and only low. At a 172 kg takeoff weight (55% of MTOW) on 20 kg of fuel, `simulate_loiter` returns **24.5 h at sea level and 22.7 h at the 4,359 m design altitude**: the demonstration clears 24 h by 2% and only by being flown down where the air is thick, and the flight that would have been quoted as proof of the design point is 6% short of its own headline. The compensations are real — the climb margin is 5.4 kW of 10.8, the stall is 61 km/h — and every hard constraint on this page is inactive at that weight.
- Nov 2027: the first serious follow-on conversation asks for the 6-day evidence. What exists is a 24 h flight at 55% of MTOW and a dyno sheet that says 4.8 days, which is inside the band existing platforms already claim.
**The assumption that allowed it:** that the optimiser's variable bounds described the market. `bsfc_full` was a free variable in [0.250, 0.320] and the optimum sat on the favourable end, exactly the failure the pre-registration named in advance for C_D0 and Oswald e — fixed for those two by deriving them from geometry, left open for BSFC.
**First warning sign:** the dyno's best-point BSFC, February 2027. Anything above 280 g/kWh ends the 6-day claim.

### 6. Compound: the mould slipped into winter and the only airframe came down under a canopy at 313 kg
**Probability:** ~8% — modes 1 and 2 are not independent; this narrates their interaction through the one asset the budget cannot replace.
**Cause of death:** the wing mould contractor slipped eight weeks — the solo builder is always the bumpable customer — pushing assembly into Nov–Dec 2027. With the horizon four months out and €9k left, the builder took a marginal January window. The recovery sequence fired above the canopy's design mass, descended at 6.7 m/s onto frozen ground and put 7.0 kJ into the airframe: spar crack at the boom station, gimbal mount torn, autopilot bay crushed. Repair was €12k and four months against €9k and four months, so the programme was shelved "until spring funding," which did not come.
**The assumption that allowed it:** that schedule risk and budget risk could be carried separately, when the thing that couples them is that there is exactly one airframe and the canopy was never resized for 313 kg.

### 7. The wing that was never analysed
**Probability:** ~5% — I cannot put a defensible number on this one, and that is the finding; 5% is a placeholder for a risk whose probability requires the analysis nobody has run.
**Cause of death:** an 11.27 m span, AR 21.4 wing with a 118 mm root spar depth, carrying 160.6 kg of fuel inside it, at an ultimate root bending moment of **30.7 kN·m** — 52% above v1.0's 20.2 kN·m on the same formula. There has been no FEA, no static test, no ground vibration test, no flutter or divergence analysis and no aeroelastic tip-twist calculation; `research/configuration_hypotheses.md` names aeroelastic tip-twist as the one item requiring a tool the programme has never used. Separately, the section is an FX 63-137 **scaled to 19.09% thickness** — an aerofoil with no measured data anywhere, whose drag penalty is known only from a neural surrogate evaluated on scaled coordinates, at Re 7.2×10⁵ at the MAC and 5.9×10⁵ at the tip, where the C_D0 of 0.01588 assumes laminar transition a first hand-built wet wing will not deliver.
**How it unfolded:** the aircraft flew. On the fourth flight, in the first turbulence above 25 m/s, the outer panel did something the builder could not describe afterwards.
**The assumption that allowed it:** that a wing which closes on bending stress is a wing that has been analysed. Bending is the one structural question this programme has asked.
**First warning sign:** there isn't one before first flight, which is exactly why it is here.

**Considered and cut:** nobody buys the demo (folded into #5), builder illness or job change (folded into #2), payload procurement cost (folded into #1), total loss of prototype 1 as a standalone (folded into #6), fuel-price volatility (<2%, recoverable).

**Downgraded — guarded for now:**

| Mode | Guard that holds it down | Signal that re-upgrades it |
|---|---|---|
| The propeller cannot absorb its engine (v1.0's killer: C_P 0.911 vs a ~0.25 ceiling) | Held down only because I re-ran it. The propeller record and its whole BEMT sweep were run on `design/argus7_v2.yaml` — 8.15 kW, 248 kg, 4,191 m — and v2.0 is retired; its 99%-absorption figure is the 1.00 m blade's and its η 0.858 the 1.04 m blade's, so the pair quoted for v3.0 belongs to two propellers on a different aeroplane. Re-run at v3.0's own point, the 1.04 m disc absorbs **99.3% of 10.845 kW** and returns **η 0.855** — but at **~2,030 rpm, not the 1,900 rpm the design file records**; at 1,900 rpm it makes 58.1 N against the 78.3 N v3.0 needs to hold level flight. The file's `prop_rpm` and its 3.947:1 reduction are v2.0's numbers and are wrong for this aircraft, worth ~0.3% of efficiency and a new gearbox ratio. Clearance is fine: 190 mm at v3.0's 11.27 m span, measured from `derive_booms`; the record's 56 mm belongs to **v1.0**'s 9.26 m span, not to v2.0, which clears by 208 mm | The absorption case is already open, not pending — treat any dyno-confirmed rating change, in either direction, as requiring a fresh BEMT sweep at the real operating point; likewise a boom `y_station_frac` inboard of 0.134 |
| Wing fuel volume as a pure geometry problem | 215.4 L usable against 205.9 L required at Jet-A density, with a 0.88 net fraction already applied | Fuel selected as mogas (see #5), or a measured usable fraction below 0.88 once ribs, baffles and sump are real |
| CG travel full→dry (the design pack's "<0.5% MAC" claim that missed by 76× on v1.0) | Tanks on the CG give −0.08% MAC, measured against the authoritative module | Tank bays moved off the 40%-chord centroid during the real internal layout |

---

## The Verdict

| # | Impact (1-5) | Feasibility (1-5) | I×F |
|---|---|---|---|
| 1 budget | 5 | 5 | 25 |
| 2 capacity / calendar | 4 | 5 | 20 |
| 3 static margin / layout | 4 | 4 | 16 |
| 4 nowhere to take off from | 5 | 3 | 15 |
| 5 demo passed, claim didn't | 3 | 4 | 12 |
| 6 compound | 5 | 2 | 10 |
| 7 structure / aeroelastic | 5 | 1 | 5 |

**Most likely:** #1 — highest feasibility among the high scorers, and the only one whose inputs are already visible: the wing mould quote in October 2026 either fits €60k or it does not, and the geometry says it does not.

**Most dangerous:** #7, on silence × irreversibility. It has the worst detection profile on the page — no warning sign exists before first flight — and it is the only mode where the failure is unrecoverable rather than expensive. #3 is the close second and the one I would act on first, because it is silent until the aircraft is weighed and by then the fuselage plug is cut. Neither is the most likely; #1 is, and #1 is survivable.

**The hidden assumption:** by convergence, modes 3, 4, 5 and 7 all die unless one belief holds — **that the optimiser's bounds described what exists**. Two of the eleven variables sit hard against a bound in the run that produced v3.0: MTOW 312.93 of a 320 ceiling, and `bsfc_full` at 0.2519 against a 0.250 floor. Those are precisely the two that carry the fatal flaw. A further three — wing area 5.9191, taper 0.697, t/c 0.1909 — sit within 5% of the *specification's* declared ranges (`argus7.opt.design_space.Bounds`: area ≤ 6.0, taper ≤ 0.70; t/c ≤ 0.20 in the eight-variable run), but `scripts/run_optimisation_layout.py` as it stands today carries area ≤ 12.0, taper ≤ 1.00 and t/c ≤ 0.22, under which all three are interior. I cannot establish from the repository which set was live at 10:07 on 21 Aug when v3.0 was written, so treat those three as unresolved rather than as evidence. The two that are certain are enough: v3.0's mass and its fuel consumption are both sitting on a wall, and each wall was drawn from an assumption rather than from a catalogue, a scale, or a measurement.

**Fatal flaw:** yes, and it is nameable. **v3.0's 6.33 days is bought with a 250 g/kWh engine that the programme's own research pack records as a verified product gap in this power class, burning a fuel dense enough to fit a tank that only closes at kerosene density.** Resolve the fuel and one of the two collapses. Everything else on this page is expensive; this one is close to arithmetic — with one honest caveat that cuts my way and one that cuts against it. The 252 g/kWh full-load figure is not measured on any candidate engine; it is what the design's 339 g/kWh at 30.6% load implies *through the generic Willans coefficients* in `argus7.opt.coupled` (0.8471, 0.1529), which are themselves a correlation nobody has checked against a 160–250 cc four-stroke. A flatter real part-load curve would let a worse full-load engine deliver 339 effective, and `research/design_pack.md` does estimate the budget donor directly at **330–420 g/kWh at 20–40% load [EST]** — which makes v3.0's 339 the optimistic edge of an estimated band rather than a documented impossibility. Cutting the other way: that band's own midpoint is 375, which is 10% worse than the "realistic stack" above already assumes. Either route, the number the aircraft is designed around is an estimate stacked on a correlation, and one dyno afternoon settles both.

---

## The Rebuild

**The revised plan:** decide what aeroplane this is before cutting anything irreversible, and buy the three missing measurements before the tooling.

- **Sep 2026 – Feb 2027, ~€16–22k — measure, don't build.** Choose the fuel first: it decides the engine and the tank simultaneously. Buy the donor engine, **weigh it installed**, and dyno-map part-load BSFC on that fuel across 15–60% load with an altitude-derated point. Draw the real internal equipment layout with weighed or quoted masses and stations, and re-solve `x_le_frac` against `argus7.analysis.balance` at both fuel states. Open the aerodrome and authorisation conversations in month 1, with a ground roll and a recomputed touchdown energy in hand. Nothing is cut or laid up in this window.
- **Mar 2027 – Feb 2028, ~€38–44k — build the aeroplane the measurements support**, at whichever MTOW the decision rule returns. Static-test the spar to ultimate before first flight, and run a flutter estimate at whatever fidelity is affordable, because zero is the current number.
- **Demonstrate twice:** the ≥24 h flight at a light takeoff weight *and* a full-fuel flight to at least 60 h. The first satisfies the success definition; only the second says anything about the design point.

**What changed and why:**

| Change | Failure mode it closes | What it costs | Tier |
|---|---|---|---|
| Choose the fuel before anything else; re-derive tank margin and engine shortlist from it | #5, and the tank half of the retired-claims list | one week; possibly the 6-day headline | **Launch-Blocking — decided by 2026-10-15** |
| Weigh the installed powertrain; rebuild the mass model from scale readings, not from `25.0 × P/17` | #3 | €0 and two days | **Launch-Blocking — by 2026-11-30** |
| Draw the internal layout; re-solve `x_le_frac`; hold the specification's own ≥8% MAC at both fuel states, not the 5% the search was given | #3 | 3 weeks of CAD, and probably no endurance at all: the programme's re-run at the real threshold inside a 12 m span (`opt_runs/layout_sm8_span12.json`) returns 6.50 d against v3.0's 6.33, because the search buys the margin back out of tail arm rather than out of fuel | **Launch-Blocking — by 2027-01-31** |
| Dyno-map part-load BSFC on the chosen fuel before the mould is cut | #1, #5 | €8–12k spent 4 months earlier than planned | **Launch-Blocking — by 2027-02-28** |
| Price and decide the takeoff method; add gear mass to the budget and a runway to the plan | #4 | €3–5k and ~8 kg out of fuel | **Launch-Blocking — by 2027-03-31** |
| Resize the canopy for 313 kg (≈106 m²) or placard a reduced maximum recovery weight | #4, #6 | €2–3k, or an operating limitation | Fast-Follow |
| Spar static test to ultimate + a flutter estimate before first flight | #7 | €3–5k and 3 weeks; one wing consumed if it breaks | Fast-Follow |
| Fly the demonstration twice — light and full | #5 | one extra flight-test campaign | Track |

Every Launch-Blocking change costs less than the mode it closes: the layout re-solve is three weeks against six weeks, €7k and an unstable first flight; the fuel decision is a week against the fatal flaw. The two most dangerous modes are handled differently on purpose. **#3 is prevented** — weigh the masses, draw the layout, and hold the 8% floor the specification already wrote and the adopted design already failed. **#7 is limited, not prevented**: a solo programme cannot buy an aeroelastic clearance, so the response is a static test to ultimate, a hand-calculation flutter estimate, a placarded envelope, and first flights held below 25 m/s indicated.

**Pre-launch checklist:**
1. *Fuel and engine, together.* Name the fuel, then find one engine that delivers ≥10.7 kW at sea level on it. **Walk away from the 313 kg design point if no such engine exists at ≤280 g/kWh full-load in a ≤22 kg installed package** — that is the fatal flaw firing, and the falsifier is concrete: if by 2026-12-15 the shortlist contains no unit meeting all three, the aeroplane is a different aeroplane.
2. *Weighed powertrain.* Put the donor on a scale with its ECU, exhaust, starter, belt, prop, mounts, sump and generator. **Walk away from the current `x_le_frac` if installed mass exceeds 22 kg** — at 22 kg the margin is 0.0% MAC at full fuel and **−5.7% dry**, i.e. already unstable on the state the aircraft lands in, before anything else moves.
3. *Internal layout.* Produce a bay drawing with every payload item at a station. **Walk away from the layout if the payload centroid lands aft of 0.52 m** — 92 mm aft of the assumed 0.432 m is zero static margin *dry*, which is the binding state; the full-fuel limit of 0.62 m is 100 mm of headroom the aircraft only has with the tanks full.
4. *Somewhere to fly.* Get a written aerodrome agreement naming a runway of ≥600 m paved, and an insurance quote. **Walk away from 313 kg if no operator will accept the aircraft with 216 L of fuel aboard by 2027-03-31.**
5. *Regulatory reality.* Verify against current text which EU thresholds actually move between 250 and 313 kg — Specific-category limits, SORA ground-risk column, third-party insurance band, and national fuel-storage rules for >200 L. **Walk away from self-deployment if the answer is a certified-category design requirement.** I could not settle this from the repository and it should not be assumed either way.

**Decision rule:** cut the wing plug for the **313 kg planform IF** (a) a dyno sheet shows ≤280 g/kWh full-load on the chosen fuel **AND** (b) the redrawn layout returns ≥8% MAC at both fuel states with weighed masses **AND** (c) a written aerodrome agreement exists for a 313 kg unmanned aircraft **AND** (d) committed spend is ≤€22k on 2027-02-28. **ELSE cut the plug for the 250 kg planform** and accept 4.88 days instead of 6.33. This is not splitting the difference: the 250 kg point is the aeroplane the €60k and the 18 months were actually estimated against, it flies inside the same 12 m span limit, and 63 kg of MTOW is buying 1.45 days at the cost of every hard constraint on this page. Do not build the 313 kg airframe while waiting for the dyno — that inherits the worst of both.

**If the rule lands on the 250 kg branch — the reverse autopsy:**
- The moulds were cut for a 11.54 m wing and moulds are permanent; the 313 kg growth path was closed for the life of the tooling, and the aircraft could never be re-scaled without re-tooling.
- 4.88 days landed inside the band existing long-endurance platforms already claim, so the demonstration was impressive engineering and not a reason for anyone to change what they buy.
- De-rating did not retire the flaw it was chosen to avoid: the 250 kg point's 328 g/kWh at 33% load implies the same **250 g/kWh full-load** floor. The programme gave away 1.45 days and kept the engine assumption that was the actual problem.

**What tips the balance:** one dyno sheet showing ≤270 g/kWh full-load on a fuel of density ≥0.775 kg/L in a ≤22 kg installed package. That single document makes the 313 kg branch correct, because it retires the fatal flaw and restores the tank margin at the same time. Without it, the caution stands.

**Consciously accepted:** the 50 kg mission payload is not procurable inside €60k, so the demonstration flies instrumented ballast at the real payload station. Cost of accepting: the comms and EO mission is unvalidated at the horizon, and integrating it later is an estimated €15–25k and four months on top of the programme — but the ballast can and must be placed at the drawn payload centroid, so the stability case is still tested.

**How the rebuilt plan dies:** the front-loaded measurement window is itself a plan with an assumption — that six months of bench work and drawings sustains a solo builder's motivation with nothing flying. It probably does not. The rebuild also buys the dyno at the cost of four months of build calendar, which means a first flight in autumn 2027 rather than summer, straight into the weather that mode 6 needs.

**Residual risk:** nothing on this page validates the aerodynamics. C_D0 0.01588 assumes laminar transition on a 19% thick scaled aerofoil never tested at Re 6–7×10⁵, and the lumped Oswald factor is open across 0.77–0.85, worth ±5 h alone. The endurance figure has no wind tunnel, no CFD and no flight data behind it, and the rebuild does not change that.

---

## The Adversary

**Playing:** an established European UAS operator or OEM in the 150–600 kg fixed-wing class that already holds an operator certificate and a design-verification path, with the emergency-comms incumbents (tethered-drone and MNO drone units) as the commercial arm of the same interest. Motivation: disaster response is their reference market and the paperwork is their moat. Resources: certification staff, framework contracts, spectrum relationships, existing authorisations. What they *can't* do: field a multi-day self-deploying 300 kg platform quickly — their alternatives are tethered or stratospheric. Their best alternative costs a marketing budget and a free pilot programme, cheap enough that they will spend it without needing to be sure about you.

**The kill chain:**
- **Probe, Oct–Nov 2027:** your first flight is visible — an aerodrome is a public place and a 11.27 m unmanned aircraft is not discreet. A business-development contact requests a briefing "to explore partnership." The questions are about customers, endurance evidence and authorisations, not about the aeroplane.
- **Position, Dec 2027:** they offer the same civil-protection agencies a funded pilot using already-authorised equipment. Procurement prefers the zero-risk line item over the better aircraft with no operator certificate.
- **Strike, Jan 2028:** an RFI appears whose language mirrors an existing spec sheet — type approval held, operator certificate held, demonstrated authorised BVLOS hours. Your platform is technically superior and procedurally ineligible.
- **Entrench, Feb 2028 onward:** a framework agreement locks the channel for two to four years, and the entry requirement it writes into the market is exactly the thing a solo builder cannot hold.

**Detection opportunities:** a partnership request whose questions are commercial rather than technical (Oct 2027 onward); an agency that previously took meetings suddenly asking for authorisation evidence rather than performance evidence (Dec 2027 onward); RFI text specifying held certificates rather than capability (Jan 2028 onward).

**The move you'd never see coming:** they never engage the aircraft. They fund a national UAS test-range framework whose access condition is an operator certificate — and the runway you spent a year negotiating becomes conditional on paperwork you do not have. The competitive move lands on your airfield access, which is the one dependency in mode #4 you thought was commercial rather than strategic.

**What this means you should change:** get the aerodrome relationship onto paper with a fixed term, not a handshake, before the first flight is visible. And publish the *method* — the dyno map, the balance verification, the fuel-volume integration — rather than the endurance headline. Evidence of rigour is the one asset a solo programme owns that an incumbent cannot buy back.

---

## The Tripwires

| Failure mode | Measurable signal | Threshold | Check on | If tripped |
|---|---|---|---|---|
| 1 budget | wing mould quote, then committed spend | quote >€15k; or >€22k committed with nothing measured | 2026-10-31, 2027-02-28 | re-quote at the 250 kg span; freeze tooling until the dyno is bought |
| 2 capacity | hours logged against the 1,900 h floor; people named for a 24 h watch rota | <300 h by month 4; fewer than 3 people | 2026-12-31, 2027-06-30 | re-baseline to 26 months now, not in Dec 2027; size the demo to the crew that exists |
| 3 static margin | installed powertrain mass, weighed; payload centroid on the layout drawing; tank bays still on the 40%-chord centroid | >22 kg; aft of 0.62 m; bays moved | 2026-11-30, 2027-01-31 | re-solve `x_le_frac` before the fuselage plug is cut — move the wing, not the ballast |
| 3 static margin | measured empty-aircraft CG vs prediction | >15 mm error | 2027-09-30 | no first flight until reconciled |
| 4 takeoff | written aerodrome agreement, runway length | none, or <600 m paved | 2027-03-31 | drop to the 250 kg branch or buy a launch solution |
| 4 regulatory | authorisation response | certified-category design requirement indicated | 2027-04-30 | redesign for local launch only; drop self-deploy |
| 5 engine | dyno best-point BSFC on the chosen fuel; rated power of the selected unit | >280 g/kWh full-load; or >11 kW rated (the propeller absorption case reopens) | 2027-02-28 | withdraw the 6-day claim in writing; re-run the BEMT sweep before ordering a blade |
| 5 fuel volume | usable tank volume, measured after ribs, baffles and sump | <205 L | 2027-06-30 | switch to kerosene or cut the design fuel load |
| 6 compound | contractor slip **and** cash | mould >6 weeks late AND cash <€12k | any month | stop work; protect the engine data, not the airframe |
| 7 structure | spar static test scheduled **and** a flutter estimate on file | either missing | 2027-05-31 | no flight-article wing layup until both exist |
| adversary | briefing requests asking about customers not technology; RFI text naming held certificates rather than capability | first occurrence | any time from 2027-10 | share method, not endurance numbers, until terms are on paper |
| adversary | aerodrome access made conditional on a certificate or a framework | first occurrence | quarterly from 2027-10 | invoke the written-term agreement; stand up a second site |

**Kill condition:** stop — not adjust — if **both** (a) dyno full-load BSFC >300 g/kWh on the fuel that fits the tank, and (b) no aerodrome agreement by 2027-06-30: the aircraft then cannot demonstrate a claim worth making and has nowhere to demonstrate it from. Also stop if the spar static test fails below ultimate **and** cash is under €12k — a second wing is €20k and the programme cannot buy it.

**What this premortem probably missed:** the 24 h flight as an *operation* rather than an event. My frame is a design-and-build frame, built from a repository full of design artefacts, so it reasons well about mass, margin and money and badly about C2 link continuity across a night, crew handover and fatigue, lost-link behaviour at hour 19, weather divert with 100 kg of fuel still aboard, and what the ground segment looks like at 04:00. The repository contains no operational artefact at all, so I had nothing to reason from and under-weighted the whole category rather than one risk inside it.

**Calibration review, 2028-02-29:** score each mode — materialized / didn't / can't tell — and each downgraded mode — stayed down / should have been up. Append the scoring below; never edit the original numbers.

**Committed:** _(one change, with a day attached — not all of them.)_
