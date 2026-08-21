# ARGUS-7 — Persistent Disaster-Zone Communications & Survey UAV
## Engineering Design Report (v2.0 of the report; design point v5.0)

**Date:** 2026-08-21 · **Design point:** `design/argus7_v5.yaml` (variant tag `v5.0`)
**Status:** Paper design. Nothing here has been built, flown, wind-tunnel tested, or meshed for CFD.
There is now a first pass of structural analysis (§6) — analytic, cross-validated, and
carrying one finding that makes the mass model optimistic. The finite-element model
built alongside it **does not reproduce the cross-validated answer and its numbers are
not used anywhere in this report.**

---

> ### This report supersedes `docs/argus7_design_report.md` (v1.0).
>
> That document remains in the repository as the historical record and must not be
> edited. It should not be used as a design reference. It publishes an aircraft that
> is **statically unstable at every fuel state** (−44.0% MAC full, −82.2% MAC dry),
> whose **wing cannot hold its own fuel** (101.5 kg required into 66.1 kg of tank),
> whose **propeller cannot absorb its engine** (C_P 0.911 demanded against a ~0.25
> practical ceiling), whose **§2 tail row does not close** (V_h 0.5765, not the stated
> 0.68), and **two of whose three published sensitivity anchors are wrong**. Its
> headline 4.70-day endurance is 3.16 days once the engine is modelled at the load it
> actually runs at instead of assumed. Every one of those statements is measured, and
> §10 gives the arithmetic and the file for each.

> ### An earlier revision of *this* report published v3.0. That design point is superseded twice over.
>
> v3.0 balanced, but at **+5.79% MAC** — below the programme's own pre-registered 8%
> static-margin floor, because the optimiser had been run with a 5–15% window instead
> of the spec's 8–20%. v4.0 fixed the stability gate and then landed at **12.0015 m of
> span against a 12.0 m limit** — 1.5 mm over, which is zero buildable margin and a
> failed gate G3. **v5.0 is the current design point.** Every number in this report is
> v5.0's unless it is explicitly labelled otherwise. §9 gives the lineage.

---

## 0. Executive summary

ARGUS-7 v5.0 is a 320 kg MTOW, single-engine, high-aspect-ratio, twin-boom pusher UAV
sized to loiter over a disaster zone carrying a 50 kg / 500 W multi-role
communications and survey bay, recovered by parachute. It is the output of an
11-variable optimiser that owns the **layout** as well as the wing, and that treats
longitudinal static margin, wing fuel volume, climb power and span as hard
constraints rather than as things checked afterwards.

| Headline | Value | Where it comes from | The caveat, stated next to it |
|---|---|---|---|
| **Loiter endurance** | **6.97 d (167.3 h)** | `opt_runs/layout_final.json` (`refined`), reproduced here to 167.325 h from the recorded design variables | **Pure loiter only** — no transit, climb, reserve or wind. The recorded figure is computed at **η_prop 0.858**, hardcoded in the run script; at the propeller efficiency **the design file itself records (0.8529)** it is **166.56 h (6.94 d)**, and with BSFC evaluated pointwise across the burn rather than frozen, **159.98 h (6.67 d)**. See §7.3 |
| Loiter altitude | 4,000 m | optimiser variable, at the lower bound of the run that produced this point | Inside the sponsor-locked 3,000–4,500 m band. Coverage 10.81 km radius / 367 km², on v1.0 §8's own unvalidated elevation model — the same as v1.0's design point, and 16% less area than v3.0's 4,359 m |
| MTOW | 320.00 kg | `design/argus7_v5.yaml`, and it is **at the optimiser's upper bound** | **+28% on v1.0's 250 kg.** This crosses the mass band v1.0 §9's entire regulatory case was built at. Declared here, see §12.4 |
| Wing | 5.7201 m², AR 24.573, span 11.8558 m, taper 0.25, t/c 0.220 | design file; closure verified by `argus7.design.geometry` to 1e−9 | Span is inside the 12 m transport gate with **144 mm** of margin. **Taper 0.25 and t/c 0.22 are both outside the ranges the aero surrogates were fitted over** — §3.4, §3.5 |
| Static margin | **+12.72% MAC full, +13.68% dry**, travel **+0.95% MAC** | `argus7.analysis.balance` on the design file | **Inside the spec's 8–20% MAC window on all four readings available** (+8.23% to +17.96%, §5.4) at both fuel states. This is the first design point in the programme of which that is true |
| Fuel | 172.42 kg into a 190.44 kg wing tank | `argus7.opt.design_space.wing_fuel_capacity_kg` | **+18.02 kg (10.4%) margin**, against v3.0's 4.4%. Survives mogas density (+5.5%) where v3.0 did not — §12.2. The capacity model is three fractions, two of them measured, not a lofted cavity |
| Mass closure | **0.00 kg** residual on 320.00 kg | `argus7.analysis.balance.mass_budget_residual_kg` | Exact to the design file's own precision |
| Engine | 10.849 kW rated, 30.0% loiter load, **effective BSFC 339.3 g/kWh** | optimiser; cross-checked against `argus7.prop.engine`, which gives 350.1 g/kWh at the same shaft power (3.2% apart) | The 339 rests on a **full-load BSFC of 250 g/kWh, which is the report's aspirational dyno target, not a measured unit.** Both shortlist engines with *verified* BSFC are 330 g/kWh, at which this aircraft flies **5.26 d**, §4.4 |
| Propeller | 1.04 m, 2 blades, 2,050 rpm, p/D 0.95, η 0.8529, 3.659:1 reduction | design file; re-solved at **this** design point, not inherited | **A found-and-fixed defect** — v3.0 carried v2.0's propeller and was 26% short of level-flight thrust (§4.5). v5.0's disc meets loiter thrust and absorbs 101% of the rating at climb. **But it cannot turn fast enough for the ferry mission** — §8.4 |
| C_D0 | 0.01690 | `argus7.opt.coupled.cd0_from_geometry` | Contains **no** payload turret, cooling drag, or base drag. A modest +0.0035 allowance costs **−0.43 d** — §3.2 |
| **Tip deflection at limit** | **855 mm = 14.4% of semi-span** | `scripts/structural_analysis.py`, cross-validated to 0.2 points against `research/materials_pack.md`'s independent estimate | Sailplane territory, not light-aircraft territory. Not disqualifying; it interacts with spanload, control effectiveness and flutter, none of which is modelled coupled — §6.2 |
| **Compression-cap buckling** | **critical at 80 MPa against 600 MPa applied — margin −87%** | `fea_runs/structural.json`, corroborated independently by the cap's width-to-thickness ratio | **The mass model is optimistic.** A buckling-sized cap is heavier than a strength-sized one and wing mass feeds straight into endurance — §6.3 |
| Best range | **17,659 km at 134 km/h TAS**, 131.8 h aloft | `opt_runs/range.json`, `scripts/range_analysis.py` | Still air, no reserve, burned to dry tanks — and **the recorded fixed-pitch propeller and 3.659:1 gearing cannot reach that speed** at the engine's assumed rpm rating, §8.4 |

### The honest bottom line

**v5.0 is the first design point in this programme that passes every closure the
repository can evaluate simultaneously**: it balances, inside the pre-registered
window rather than merely positively; it holds its fuel with real margin; its mass
budget closes exactly; its span is inside the transport gate with buildable margin;
and its propeller was solved at its own operating point instead of inherited from a
retired aircraft. Each of those was false of at least one of v1.0, v2.0, v3.0 and v4.0.

**Two things are still open, and neither is aerodynamic.**

**First, the engine.** 6.97 days is the *optimistic* end of a defensible band, and the
report says so here rather than in a footnote. Stacking the corrections this
repository can already justify:

| Applied cumulatively to the recorded design point | Endurance |
|---|---|
| As recorded (`opt_runs/layout_final.json`, η_prop 0.858) | **167.32 h — 6.97 d** |
| + the propeller efficiency the design file itself records (0.8529) | 166.56 h — 6.94 d |
| + the load fraction recomputed at that efficiency (29.62%, 340.8 g/kWh) | 165.80 h — 6.91 d |
| + BSFC evaluated pointwise along the burn instead of frozen at mid-load | 159.98 h — 6.67 d |
| + a +0.0035 C_D0 allowance for turret, cooling and base drag | 153.69 h — **6.40 d** |
| + a **verified** engine's 330 g/kWh full-load BSFC instead of the 250 target | 116.43 h — **4.85 d** |

**The programme's 5–7 day ambition is met with room to spare on the modelled engine,
and missed — narrowly, at 4.85 days — on the only engines whose fuel consumption
anybody has measured.** That is a materially better position than v3.0, which fell to
4.46 d under the same stack, but it is the same finding: the design lives or dies on a
dyno, not on aerodynamics.

**Second, the structure.** The first structural analysis in the programme's history
(§6) returns a wing that deflects **14.4% of semi-span at limit load** and whose
compression caps buckle at **an eighth of the stress the material allowable assumes**.
The deflection is large but survivable. The buckling is not a caveat, it is a
correction: **the wing mass model is optimistic, and wing mass converts to endurance
at 1.51 h/kg** (§6.5). Nothing in this report has been re-run with a buckling-sized
cap, because sizing one properly is a design task, not an analysis task.

### The pre-registered gates

Unlike every previous revision of this report, this section is short.

Running the eight gauntlet gates (`docs/decisions/2026-08-20-gauntlet-preregistration.md`)
plus the spec's separate stability window against v5.0:

| Gate | v5.0 | Verdict |
|---|---|---|
| G1 endurance ≥ +5% on the champion | 167.3 h vs 75.9 h honest / 112.98 h published | ✅ +48% |
| G2 fuel ≤ wing tank capacity | 172.42 ≤ 190.44 kg (+10.4%) | ✅ |
| G3 span ≤ 12 m | 11.8558 m (144 mm margin) | ✅ |
| G4 mass closure | 0.00 kg residual | ✅ |
| G5 AR^1.5 wing-mass scaling honoured | yes | ✅ |
| G6 regulatory band declared | 320 kg, declared in §12.4 | ✅ |
| G7 buildability: AR ≤ 25, span ≤ 12 m, **engine matched to a real §6 unit** | AR 24.57 ✅, span ✅, **engine is a 250 g/kWh target** | ❌ **FAIL** |
| G8 stall margin | loiter C_L 1.2098 = C_Lmax/1.15² exactly | ✅ (binding) |
| Spec line 109: 8% ≤ SM ≤ 20% MAC | **+12.72% full / +13.68% dry**, and 8.23–17.96% across every reading | ✅ |
| Annex A tripwire #3: loiter BSFC ≤ 300 g/kWh | **339.3 g/kWh modelled** | ❌ **trips** |

**Eight of the nine gates pass. G7 does not, for exactly the reason it did not pass on
v3.0 and on the challenger before it: the design rests on a full-load BSFC of
250 g/kWh that report §6 itself describes as a target, and the gauntlet audit already
ruled that a target is not a unit** (`docs/decisions/2026-08-20-gauntlet-audit.md` §G7).
Nothing about the engine has changed between v3.0 and v5.0; the airframe changed
around it.

**`README.md` currently states that v5.0 passes 9/9. On the repository's own record it
passes 8/9,** and the ninth is the one gate that no amount of optimisation can close.
The honest statement is narrower than "v5.0 is the design": **v5.0 is the best design
point this programme has produced and verified, it clears every airframe gate, and the
one gate it fails is about an engine nobody has put on a dyno.**

---

## 1. Mission and requirements

Unchanged from v1.0 §1. Restated so this document is self-contained.

- **Payload:** 50 kg multi-role bay — LTE/5G relay (eNB plus sector antennas), EO/IR
  gimbal (TrakkaCam TC-300 class), mesh MANET feeder, LEO/Iridium backhaul, mission
  computer and power conditioning. **50 kg / 500 W continuous, ~620 W peak**, all
  COTS-derived. Tagged `report-§1` and `report-§3` in the design file's provenance
  block.
- **Modes:** (A) *Local* — launch near the zone, pure loiter. (B) *Deploy* — transit
  to the zone, loiter, recover locally. **Only mode A is modelled as a mission.**
  Every endurance figure in this report is mode A. §8 adds a straight-line **ferry**
  calculation, which is a third thing and is not mode B either — it has no loiter
  segment at all.
- **Recovery:** parachute plus airbag, reusable airframe, no single-use elements.
- **Environment:** loiter band **3,000–4,500 m AGL**, −5 to −15 °C at altitude.

The loiter band is a locked requirement, and it is treated as one here. The retired
v2.0 optimiser went 500 m *below* the floor to buy 8 hours, giving up 61% of the
coverage area, because nothing in its objective knew coverage existed. The run that
produced v5.0 was bounded at [4,000 m, 4,500 m] and returned **4,000 m** — the floor of
its own search, because at fixed lift coefficient a denser atmosphere means a slower
loiter and less power. **The bound is what stops it going lower, not the physics**, and
that is worth saying plainly: altitude is a coverage requirement fighting an endurance
gradient, and the requirement is winning only because it was written down.

**Coverage at the v5.0 loiter altitude,** on v1.0 §8's own suburban elevation-angle
model (θ* = 20.3°): service radius **10.81 km**, area **367 km²**. That is identical to
v1.0's 4,000 m design point and **16% less area than v3.0's 4,359 m** — a real
regression against the superseded design point, bought for +0.28 d of endurance
(§7.4). The elevation model itself is unchanged and unvalidated; v1.0 §8 already flags
that no published measurement exists in this altitude band.

---

## 2. The v5.0 configuration

### 2.1 Geometry

Every row below is either read directly from `design/argus7_v5.yaml` or derived from
it by `argus7.design.geometry`, which enforces closure to 1e−9. Nothing is typed in.

| Parameter | v3.0 (superseded) | **v5.0** | Provenance |
|---|---|---|---|
| MTOW | 312.93 kg | **320.00 kg** | derived (optimiser); **at its upper bound** |
| Wing area S | 5.9191 m² | **5.7201 m²** | derived |
| Aspect ratio AR | 21.442 | **24.573** | derived |
| Span b | 11.266 m | **11.8558 m** | closure identity √(AR·S) |
| Taper ratio λ | 0.697 | **0.250** | derived — **at the search's lower bound** |
| Root / tip chord | 0.6192 / 0.4316 m | **0.7720 / 0.1930 m** | closure |
| MAC | 0.5310 m | **0.5404 m** | closure |
| MAC leading edge | x = 1.2485 m | **x = 1.4269 m** | derived |
| Wing loading | 52.87 kg/m² | **55.94 kg/m²** | derived |
| Airfoil | FX 63-137 at t/c 0.1909 | **FX 63-137, scaled to t/c 0.2200** | section `report-§2`; thickness derived, **at its upper bound** |
| Twist (tip) / dihedral / LE sweep / incidence | −3° / +3° / 1° / 2° | unchanged | **all four tagged `assumption`** — no source in report or research packs |
| **Wing station `x_le_frac`** | 0.3536 | **0.4075** (root LE at x = 1.3855 m) | **derived — this is the single change that makes the aircraft balance** |
| Wing vertical offset | +8 mm | unchanged | assumption; makes this a mid-wing aircraft |
| Fuselage | 3.4 m × 0.48 m, 6-station loft, 0.4022 m³ | unchanged | **assumption, unchanged from v1.0 and fixed for every design point** |
| Booms | Ø90 mm, y = ±0.7548 m, length 4.064 m | **Ø90 mm, y = ±0.7943 m, length 6.2497 m** | diameter and station `assumption`; length derived |
| Tail | inverted V, −42° dihedral, panel AR 3.0, taper 0.55, NACA 0010 | unchanged | type `report-§2`; angles `assumption` |
| Tail effective horizontal area S_h | 0.3698 m² | **0.3222 m²** | derived |
| Tail arm | 3.5847 m = 1.0543 × L | **5.7732 m = 1.6980 × L** | derived |
| **Tail volume coefficient V_h** | 0.4218 | **0.6018** | derived, and it **closes** — see §10 |
| Engine | 10.845 kW | **10.849 kW**, 250 cc nominal displacement | power derived; displacement inherited `report-§2` |
| Reduction | 3.947 : 1 | **3.659 : 1** | derived |
| Propeller | 1.04 m, 2 blades, 1,900 rpm, p/D 0.95 | **1.04 m, 2 blades, 2,050 rpm, p/D 0.95** | derived (BEMT), **at this design point** |
| Loiter altitude | 4,358.8 m | **4,000.0 m** | derived |

**A note on the tail arm, because it has nearly doubled.** At 1.698 × fuselage length
the tail quarter-chord sits at x = **7.335 m — 3.94 m aft of the 3.4 m fuselage
tailcone**, against v3.0's 1.57 m, carried on booms **6.25 m** long
— 54% longer than v3.0's and 71% longer than the 3.646 m boom on which
`research/boom_construction_pack.md` sized the whole boom structure. That long arm is
what buys V_h 0.6018 and the +29.5% MAC tail contribution the neutral point needs, and
it is what allows a *smaller* tail (0.3222 m² against v3.0's 0.3698) to do more work.
**Every boom number in the research pack is now wrong by more than it was for v3.0.**
The one boom quantity that has been re-derived for v5.0 is torsional frequency, and it
moved: **14.5 Hz against the pack's 22.7 Hz** (§6.6).

**Three of the eleven design variables sit hard against a bound**: MTOW at 320 kg,
t/c at 0.22, taper at 0.25. A fourth, `bsfc_full`, sits at its 0.250 floor. The
premortem's "hidden assumption" finding applies unchanged and with one more variable:
**the answer is partly a description of where the box was drawn.** Taper 0.25 and
t/c 0.22 are additionally *outside the calibration ranges of the aerodynamic
surrogates that price them* (§3.4, §3.5), which is the specific failure class this
report exists to stop repeating.

### 2.2 Mass table

Produced by `argus7.analysis.balance.mass_table` on the design file. The `x` column is
the fuselage station of each group's centre of gravity; `%MAC` is measured from the
MAC leading edge, which is the convention used throughout this report.

| Item | Mass (kg) | x (m) | % MAC | Moment (kg·m) |
|---|---|---|---|---|
| Wing | 40.63 | 1.6430 | 40.0 | 66.75 |
| Fuselage (incl. misc) | 15.06 | 1.6264 | 36.9 | 24.49 |
| Booms | 9.70 | 4.3603 | 542.9 | 42.29 |
| Tail | 3.25 | 7.3833 | 1102.3 | 23.99 |
| Powertrain | 15.95 | 3.0500 | 300.4 | 48.65 |
| Avionics | 6.00 | 1.4500 | 4.3 | 8.70 |
| Recovery | 7.00 | 0.9500 | −88.3 | 6.65 |
| Payload | 50.00 | 0.4320 | −184.1 | 21.60 |
| **Fuel** | **172.42** | **1.6568** | **42.6** | **285.67** |
| **TOTAL** | **320.00** | **1.6524** | **41.7** | **528.78** |

Design-file MTOW 320.00 kg; **unallocated residual 0.00 kg.**

Design-file grouping, for comparison with v1.0 §3:

| Group | v1.0 | v3.0 | **v5.0** |
|---|---|---|---|
| Airframe structure | 60.5 | 73.39 | **68.63** (wing 40.63 + non-wing 28.00) |
| Powertrain | 25.0 | 15.95 | **15.95** (a 10.8 kW engine, not a 17 kW one) |
| Avionics | 6.0 | 6.00 | 6.00 |
| Recovery | 7.0 | 7.00 | 7.00 |
| Payload | 50.0 | 50.00 | 50.00 |
| **Empty (no payload, no fuel)** | **98.5** | 102.34 | **97.58** |
| Fuel | 101.5 (40.6% of MTOW) | 160.60 (51.3%) | **172.42 (53.9% of MTOW)** |
| MTOW | 250.0 | 312.93 | **320.00** |

**v5.0's wing is 4.76 kg lighter than v3.0's on a 3.4% smaller area and a 5.2% larger
span.** That is not an error; it is what a 22% section buys. The spar is 170 mm deep at
the root against v3.0's 118 mm, and depth buys cap area faster than span and weight
consume it (§6.1). It is also, as §6.3 establishes, exactly where the buckling problem
comes from.

**Two assumptions in that table carry the whole thing, and both are declared:**

1. **Non-wing airframe mass is fixed at 28.00 kg** regardless of how large the wing,
   tail or booms become. It was 28 kg on a 3.9 m² wing with a 3.65 m boom and it is
   28 kg on a 5.72 m² wing with a **6.25 m** boom. The mass table above splits that
   28 kg across fuselage/booms/tail for CG purposes only; the total is a constant.
   Charging it honestly — fuselage ∝ MTOW, booms ∝ length, tail ∝ wetted area,
   recovery ∝ MTOW — puts it at roughly **32.9 kg plus an 8.96 kg recovery system**,
   i.e. **about +6.6 kg the model never charges**, and the boom-length term has grown
   since that estimate was made. At the measured exchange rate of **1.51 h/kg** that is
   **−9.8 h, 166.6 → 156.8 h**. This is the same defect the gauntlet audit found on the
   original challenger. It is not fixed here, and v5.0's 6.25 m booms make it worse
   than it was on v3.0.
2. **The wing mass model is calibrated on one point.** `argus7.opt.design_space`
   derives spar-cap mass from root bending moment with a single fitted coefficient
   `k_cal = 4.2257`, set so the model returns v1.0's published 32.5 kg wing. The
   gauntlet audit verified the AR^1.5 exponent analytically and cross-checked the
   *ratio* between two design points against Raymer's independent GA regression to
   1.0% — but it also established that **76% of the spar-cap term at the baseline is
   the fitted constant**. The scaling survives, because `k_cal` is a pure multiplier
   and cancels from every ratio; the absolute level is calibrated, not derived. **And
   §6.3 establishes that the sizing criterion it implements is the wrong one.**

---

## 3. Aerodynamics

### 3.1 The drag polar and the loiter point

The mission model uses the standard lumped polar

    C_D = C_D0 + C_L² / (π · AR · e)

with C_D0 = 0.016904 and e = 0.81012, both **outputs of geometry** in the optimiser's
coupled model rather than free variables. At the loiter point:

| Quantity | v3.0 | **v5.0** |
|---|---|---|
| Loiter C_L | 1.2098 | **1.2098** = C_Lmax / 1.15², stall-constrained |
| C_D | 0.04150 | **0.04030** |
| **L/D at loiter** | 29.15 | **30.02** |
| **L/D max** | — | **30.42 at C_L 1.0281** |
| Induced share of C_D | 61.7% | **58.1%** |
| ρ at loiter altitude | 0.78856 (4,359 m) | **0.81913 (4,000 m)** |
| TAS, MTOW → dry | 118.7 → 82.8 km/h | **119.8 → 81.4 km/h**, mean 101.8 km/h |
| Drag, MTOW → dry | 105.3 → 51.2 N | **104.6 → 48.2 N** |
| Shaft power, MTOW → dry | 4.71 → 2.04 kW | **4.75 → 1.94 kW**, mean 3.26 kW |
| Re at MAC, MTOW → dry | 8.37e5 → 5.84e5 | **8.87e5 → 6.02e5** |
| Re at tip, MTOW → dry | 6.80e5 → 4.75e5 | **3.17e5 → 2.15e5** |

The **stall constraint binds**, as it did on v1.0 and v3.0: unconstrained minimum-power
C_L for this polar is 1.7806, above C_Lmax/1.15², so the aircraft loiters at 1.2098
exactly. This matters, because loiter speed — and therefore power — is set by C_Lmax,
and C_Lmax is held at a flat 1.60 for every design point.

**The tip Reynolds number is the new exposure, and it is a big move.** Taper 0.25 on an
AR 24.57 wing gives a **193 mm tip chord**, and Re at the tip falls to **2.15 × 10⁵ by
the end of the mission** — against v3.0's 4.75 × 10⁵. Low-Reynolds airfoil behaviour
degrades sharply below about 3 × 10⁵, and a flat C_Lmax of 1.60 applied to a wing whose
tip lives there is a stronger assumption than it was.

**Measured, and it survives — in two dimensions.** NeuralFoil (xxlarge) on the pinned
`data/airfoils/fx63137.dat` coordinates scaled to 22% thickness gives 2D C_Lmax:

| Re | 13.7% section | **22% section** |
|---|---|---|
| 2.2 × 10⁵ (tip, dry) | 1.747 | **2.103** ⚠ |
| 3.2 × 10⁵ (tip, MTOW) | 1.770 | **2.118** ⚠ |
| 8.9 × 10⁵ (MAC, MTOW) | 1.871 | **2.154** |
| 1.0 × 10⁶ | 1.869 | **2.163** |

So the flat 1.60 is **conservative by 31% even at the tip's worst Reynolds number** —
thickness buys more C_Lmax than low Reynolds number takes away. ⚠ marks the two rows
where **NeuralFoil flags itself as extrapolating outside its training distribution**
(analysis confidence 0.825 against its own 0.9 threshold); the two higher-Re rows carry
no such flag. Those two rows should be checked against XFOIL before being leaned on.

**What is not answered by any of this** is three-dimensional: a taper-0.25 wing loads
its tip harder than a taper-0.7 one, tip stall on a highly tapered high-AR wing is a
departure question, and nothing in this stack models tip-stall progression, spanwise
boundary-layer drift, or the washout needed to control either. The −3° tip twist in the
design file is tagged `assumption` and was not chosen for this planform.

**81.4 km/h at end of mission is slow.** At 22.6 m/s, station-keeping margin against
wind over a disaster zone is thin, and it is slower than v3.0's already-thin 82.8 km/h.
Nothing in the objective function knows about wind. This is a mission-suitability
caveat on the last third of the endurance, not a modelling error.

### 3.2 C_D0 build-up

`argus7.aero.buildup` computes a component parasite build-up from the *actual*
geometry — real FX 63-137 arc length, real fuselage station loft, derived boom length,
true (not projected) tail panel area — with a **measured** transition location rather
than an assumed one. Run on the v5.0 geometry:

| Component | S_wet (m²) | Re | x_tr | C_f | FF | Q | C_D0 | share |
|---|---|---|---|---|---|---|---|---|
| Wing | 11.066 | 8.87e5 | 0.546 | 0.00289 | 1.302 | 1.00 | 0.00729 | 53.3% |
| Fuselage | 4.029 | 5.58e6 | 0.100 | 0.00298 | 1.187 | 1.00 | 0.00249 | 18.2% |
| Booms | 3.534 | 1.03e7 | 0.150 | 0.00253 | 1.003 | 1.30 | 0.00204 | 14.9% |
| Tail | 1.184 | 5.26e5 | 0.300 | 0.00412 | 1.212 | 1.05 | 0.00108 | 7.9% |
| Miscellaneous (6%) | — | — | — | — | — | — | 0.00077 | 5.7% |
| **Total** | **19.813** | | | | | | **0.01368** | |

**The booms are now the third-largest drag item, at 14.9% of C_D0 against v3.0's
10.7%.** That is the 6.25 m tail arm arriving in the drag budget. It is charged, and it
is charged at Q = 1.30 for interference — but the booms have not been re-sized, and
§6.6 is a stiffness argument for making them *larger* in diameter, which would charge
more.

**Three things must be said about that number, and none of them is comfortable.**

**(a) It is not the number the design file carries.** The design file's 0.016904 comes
from `argus7.opt.coupled.cd0_from_geometry`, an equivalent-skin-friction model —
C_D0 = C_fe · S_wet/S_ref — calibrated at the v1.0 point and multiplied by a
NeuralFoil-measured thickness penalty. The two disagree by **23.5%** on v5.0, wider
than v3.0's 22%. They disagree because the build-up reads t/c from the *airfoil
coordinates* (13.71%) while the design flies a section scaled to **22.00%**; the
build-up therefore under-charges the wing's wetted area and form factor, and the gap
grows with thickness. The optimiser's number is the one used, and it is the higher
(more conservative) of the two.

**(b) Neither number contains the payload.** `argus7.aero.buildup`'s own docstring
lists what it omits: the 50 kg payload installation (a ~0.3 m gimballed EO/IR ball at
C_D 0.4 on frontal area is **alone worth ~0.007 in C_D0**), engine cooling drag (5–10%
of total on a piston installation), fuselage base drag (the aft station closes to
r/R = 0.34), and recovery/launch hardware. A modest **+0.0035** allowance for those
costs **−0.43 d** on this design point. The fix is to add the hardware to the design
file, not to raise a factor.

**(c) The correlation is being used outside its calibration.** Raymer's form factor
(eq. 12.30) is a function of t/c and (x/c)_m only — a **minimum-drag** pressure
correlation with no C_L dependence — while the transition location fed to it was
measured **at C_L 1.21**. The module has it both ways, and says so. Cross-checked
strip-by-strip against NeuralFoil on the same coordinates, the C_f·FF build-up was
**11.2% low** on wing drag area at the loiter lift coefficient on v3.0's planform. The
sign of the disagreement with the design file is solid; its size is not.

### 3.3 The XFOIL transition result

The wing transition location is **measured, not assumed** — the one input in this
build-up that is. XFOIL 6.99 on the repository's pinned, checksum-enforced
`data/airfoils/fx63137.dat`, converted Lednicer→Selig, 300 panels, Ncrit 9, viscous,
fixed-C_L mode at C_L = 1.21, ten spanwise stations (`research/riblets_pack.md` §3):

- **Upper surface transition 50.2% chord at the root, moving aft to 60.5% at the tip.**
- Lower surface 61.4% → 68.2%.
- **40.5% of the wing's wetted area is turbulent, carrying 53.3% of its skin friction.**
- Independently corroborated by NeuralFoil (xxlarge), which puts upper transition at
  0.547 (root) to 0.599 (tip).

Two consequences the report must carry:

1. **The laminar run is the leverage, and it is fragile.** Moving upper-surface
   transition forward by five points of chord costs Δc_d ≈ +0.00057 → about **−1.2 h**.
   A fully tripped wing costs on the order of **−14 h**. That is why
   `research/materials_pack.md` §6 is a structures-and-surface question with an
   endurance answer.
2. **Ncrit = 9 is assumed.** A UAV in quiet air at 4,000 m may see Ncrit 11–13, which
   moves transition aft; in turbulent air or propeller wash, Ncrit 5–7 moves it
   forward. The riblets pack flags explicitly that the whole transition table should be
   re-run at Ncrit 7 and 12 before any number in it is treated as settled. It has not
   been.

**And the measurement no longer describes this wing.** These numbers were taken **on
the 13.7% section at v1.0's chords and speeds**. v5.0 flies a **22.0%** section at a
tip Reynolds number less than half v1.0's. Transition on a 22% section is not the same
problem — the pressure recovery is steeper and the separation bubble behaves
differently — and it has not been re-measured. This was a caveat on v3.0; on v5.0 it is
a larger one.

### 3.4 The Oswald factor — three different quantities, and why that mattered

This is the finding that most changed how the programme models drag, and it is
recorded in `docs/decisions/2026-08-20-span-efficiency-finding.md`.

At the loiter lift coefficient, **induced drag is the majority of total drag** (58.1%
on v5.0; 61.7% on v3.0; 55.5% on v1.0). Every optimisation the programme had examined
— riblets, boom deletion, surface finish — was attacking the smaller half. And the
Oswald factor, the single largest lever in the drag model, had never been validated.

AVL 3.36, run on the actual planform at matched C_L 1.21 (12 sections, 24 spanwise
panels, tip-bunched, inside the single-precision NaN limit of 40), returned
**e = 0.9786** at the as-designed −3° twist on v1.0's planform. The design file said
0.85. A crude AeroSandbox viscous subtraction implied 0.77.

**These are three different quantities and must not be compared:**

| Symbol | What it is | v1.0 value |
|---|---|---|
| AVL's e | **Inviscid span efficiency** — how close the lift distribution is to elliptic | 0.9786 |
| The design file's e | **Lumped Oswald factor** in C_D = C_D0 + C_L²/(πARe), which conventionally also absorbs viscous lift-dependent drag | 0.85 |
| AeroSandbox's implied value | A viscous build-up's lumped equivalent, crude subtraction | ~0.77 |

Treating AVL's 0.9786 as if it were the design file's 0.85 would have handed the
programme **+7 h that does not exist**, straight into the optimiser's objective.

**How it was closed.** `argus7.opt.coupled` fits a surface to **45 AVL runs** spanning
AR 14–30, **taper 0.30–0.60**, twist 0 to −6°, and adds an explicit viscous
lift-dependent term:

    1/e_eff = 1/e_inviscid + K_visc · π · AR,   K_visc = 0.002237

calibrated once so the baseline reproduces the report's own total C_D at C_L 1.21. On
v5.0's planform this returns **e_inviscid = 0.9419** and **e_eff = 0.8101**.

**What the AVL sweep established, and it contradicts the design's founding premise:**
span efficiency is **nearly flat in aspect ratio** — 0.989 at AR 14 to 0.969 at AR 30.
The previous optimiser had used Raymer's straight-wing correlation, fitted to
conventional aircraft at AR 5–10, which returns e = 0.485 at AR 22 against 0.979
measured, and it drove a run to AR 15.25 for an entirely fictitious reason. **High
aspect ratio was never the route to endurance it was assumed to be**; the only
legitimate pushback on AR is structural mass, and the only legitimate reward is span.

**Four caveats on the surface, and one of them is new to v5.0:**

- The stored table **reproduces to four decimals** when the decks are rebuilt from
  scratch — the 45-run sweep is real, not asserted.
- **It is not panel-converged.** On a test planform e falls monotonically with
  refinement, 0.9611 (12×24) → 0.9564 (12×36), i.e. −0.5% and still moving. The whole
  surface is built on the coarsest of those, and its coefficients are quoted to six
  figures they have not earned.
- **`K_visc` is design-independent and double-books.** It is calibrated once on a
  13.7% section at Re 7.75e5 and applied unchanged to a 22.0% section at less than half
  that tip Reynolds number. It also overlaps the thickness drag multiplier: the wing's
  profile drag at lift is represented twice, in two terms neither of which knows about
  the other.
- **NEW, and it is an extrapolation the previous revision of this report did not have
  to declare: v5.0's taper ratio is 0.25, below the 0.30 floor of the 45 runs the
  surface was fitted to.** The fit is a quadratic in (λ − 0.45); at λ = 0.25 the
  quadratic term is being read 0.05 outside its data on the steep side. It is also
  below `argus7.opt.design_space.Bounds`'s own taper floor of 0.30 — the layout run
  script carries a wider box than the specification's. The direction of the error is
  not knowable from inside the fit.

**The open band on the lumped Oswald factor — 0.77 to 0.85 — is worth about −3.8 h on
v5.0** (e = 0.77 gives 162.8 h against the baseline 166.6 h). Narrower than it was on
v3.0, because v5.0's higher AR reduces the induced share. It has been narrowed by
measurement, not closed.

### 3.5 The thickness penalty is also being read outside its data

`argus7.opt.coupled.thickness_drag_multiplier` prices wing thickness from a NeuralFoil
measurement on the actual coordinates at **t/c 0.137, 0.150, 0.170, 0.190 and 0.200**,
fitted as `1 + 2.5·(t/c − 0.137)`, linear to within 0.5% across that range.

**v5.0 flies t/c 0.220.** That is 10% beyond the last measured point, on a linear
extrapolation of a quantity (profile drag versus thickness) that is not linear
indefinitely — it steepens as the section approaches separation-limited pressure
recovery. The multiplier is therefore **likely to be optimistic**, and the model has no
way to know by how much. Re-measuring at t/c 0.22 and 0.24 is a NeuralFoil run of a few
seconds and has not been done.

This is the same class of error as Raymer's Oswald correlation at AR 22 (§3.4) and as
the propeller carried from v2.0 (§4.5): **a constant used at a point it was not
evaluated for.** It is listed here rather than in §12 because it prices a variable that
sits hard against its bound.

---

## 4. Propulsion

### 4.1 Why v1.0's propulsion set could not close

v1.0 specified a **0.813 m propeller at 2,100 rpm against a 17 kW engine**. The power
coefficient that demands is

    C_P = P / (ρ n³ D⁵) = **0.911**

against a practical ceiling near 0.25 for a two- or three-blade disc of that
proportion. Swept across every pitch a real propeller could be built with and across
advance ratio, the best C_P that disc reaches is far below what the rated power
demands: **it can absorb about 4.7 kW of 17.** Asserted, not merely claimed, by
`tests/test_bemt.py::test_required_cp_for_the_report_baseline_is_0_911` and
`::test_report_propulsion_set_cannot_absorb_rated_power`.

**The propeller was never the real defect.** It was being asked to absorb an engine
sized for *climb* while flying a *loiter* mission. That tension — climb wants 11–17 kW,
loiter wants 3.3 kW, one fixed-pitch propeller on one fixed engine must serve both —
is the central configuration problem of this aircraft. §8.4 shows it is still not
solved: the same fixed set that serves loiter cannot serve the ferry mission either.

### 4.2 Engine right-sizing

The single largest lever in the whole programme is the **engine rating**, not the
airframe.

| | v1.0 published | v1.0, honest model | v3.0 | **v5.0** |
|---|---|---|---|---|
| Engine rating | 17 kW | 17 kW | 10.845 kW | **10.849 kW** |
| Loiter shaft power (mean) | ~3.4 kW | 3.25 kW | 3.30 kW | **3.26 kW** |
| **Load fraction (mid-burn)** | — | **19.0%** | 30.6% | **30.0%** |
| BSFC assumed / effective | 270 assumed flat | **425 g/kWh** | 339 g/kWh | **339 g/kWh** |
| Endurance | 4.70 d (claimed) | **3.16 d** | 6.33 d | **6.97 d** |

Source: `opt_runs/final.json` (`baseline_v1`, 75.90 h = 3.163 d) and
`opt_runs/layout_final.json`.

Right-sizing works because BSFC is a strong function of load. A 17 kW engine loitering
at 3.3 kW is at 19% load, deep in the hyperbolic part of the fuel-flow curve. An
11 kW engine at the same shaft power is at 30%, where the curve has flattened.

The climb constraint is what stops the engine shrinking further, and on v5.0 it is
**very nearly exactly active**: `argus7.opt.coupled.climb_power_required_w` returns
**10.839 kW** for 2 m/s sea-level climb at MTOW against the **10.849 kW** installed.
That is **+0.09% margin** — tighter than v3.0's 1.5%, and another way of saying the
engine size is *determined* by the climb requirement and not by the loiter mission at
all. It also means the engine rating has no headroom whatsoever for the +6.6 kg of
uncharged airframe mass in §2.2, for a buckling-sized spar (§6.3), or for a real
propeller's installation losses.

**A consistency item that is not resolved.** The design file still carries
`engine_displacement_cc: 250`, tagged `report-§2`, alongside a 10.849 kW rating. At
`argus7.prop.engine`'s assumed 7,500 rpm power peak that is a BMEP of **6.94 bar**,
against v1.0's 10.88 bar for the same displacement at 17 kW. Either this is a 250 cc
engine run well below its rating, or the displacement should have moved with the power
and did not. **The displacement field was inherited, not re-derived** — the same
inheritance defect §4.5 documents on the propeller, still standing.

### 4.3 The part-load BSFC curve

`argus7/prop/engine.py` implements a **Willans line** — fuel power affine in brake
power, because fuel buys *indicated* work and a nearly load-independent loss is
subtracted from it:

    BSFC(P) = k · (1 + P_loss(n) / P)

with loss power scaling as n·(F₀ + (1−F₀)·n/n_rated), near-quadratic in speed as
measured FMEP data are. The asymptote k is calibrated so that BSFC at 75% load and
rated speed equals the report's 270 g/kWh, giving **217.7 g/kWh** — 38% indicated
thermal efficiency, plausible for a modern SI engine and the check that the
calibration has not been pushed into fantasy.

At v5.0's mid-burn shaft power (3.214 kW) this returns **350.1 g/kWh**.

The optimiser uses a simpler fit to the same curve,
BSFC(load) = BSFC_full · (0.8471 + 0.1529/load), which at the recorded 29.98% load and
a 250.0 g/kWh full-load basis returns **339.3 g/kWh** (`opt_runs/layout_final.json`,
`bsfc_eff`). **The two independent implementations agree to 3.2%.** The gauntlet
audit's third, independently coded Willans line agreed with the module to 2.4% on a
different design point. This is one of the better-corroborated numbers in the report.

The same deck, run across the burn, gives 307.3 g/kWh at full fuel (43.7% load) and
**436.5 g/kWh dry (17.9% load)** — which is why freezing BSFC at the mid-burn value is
worth −6.6 h (§7.3).

**Five things about it that are assumptions or inconsistencies, and the report will
not hide them:**

1. **The load fraction at which 270 g/kWh is taken to hold is 0.75, and it is the most
   load-bearing unsourced number in the engine deck.** The report never says at what
   load its 270 holds. `engine.py`'s own comment sweeps it: 0.50 → 292.9 g/kWh (the
   report's >300 walk-away does **not** fire), 0.60 → 306.5 (fires), 0.75 → 321.3
   (fires, as coded), 0.90 → 332.0. **0.50 is not an absurd alternative reading.**
2. **The module contradicts itself on the friction fraction and refuses to resolve it.**
   `FRICTION_POWER_FRACTION_AT_RATED = 0.18` and the Gagg-Farrar altitude lapse's
   1/7.55 = 0.1325 are the *same physical quantity* and disagree by 36%. The file says
   so in terms and leaves both standing, because choosing between them is a modelling
   decision with a headline consequence. It is still unresolved.
3. **Throttling losses are folded in at a load-independent level.** A throttled SI
   engine's pumping loss grows as load falls, so the true deep-part-load penalty is
   **worse** than modelled. This model is the optimistic bound.
4. **BSFC was frozen at the mid-burn load in the mission integration.** See §7.3 — this
   is worth −6.6 h on v5.0.
5. **The load fraction the BSFC is read at was computed with a different propeller
   efficiency from the one the mission was flown with, and this is still an
   inconsistency in the recorded design point.** `scripts/run_optimisation_layout.py`
   sets the mid-burn shaft power with `argus7.opt.coupled.PROP_ETA = 0.84` and then
   integrates the mission at `prop_efficiency = 0.858`, while the design file records
   the propeller's own loiter efficiency as **0.8529**. Made self-consistent at 0.8529
   the mid-burn load is **29.62%**, not 29.98%, the effective BSFC is **340.8 g/kWh**,
   not 339.3, and the endurance is **165.80 h**, not 167.32 — **−1.53 h**. Small in
   magnitude; it is a constant used at a point it was not evaluated for, which is the
   exact failure class this report exists to stop repeating, and **it is the same
   finding this report made against v3.0 and it has not been fixed.** It needs an
   optimiser re-run, not an edit.

### 4.4 The BSFC that the answer actually rests on

The optimiser treated full-load BSFC as a variable bounded [0.250, 0.320] kg/kWh and
took **0.250 — the floor**. That is the report's own §6 language: *"BSFC is not
published — must be dyno-mapped; design assumes 270 g/kWh, target ≤250."*

**250 g/kWh is the target, not a unit.** The only two engines on v1.0 §6's shortlist
carrying a BSFC figure at all — the RCV DF70LC (*"verified 330 g/kWh"*) and the Orbital
HFDI-150 (*"~330 g/kWh"*) — are both **330 g/kWh**; the primary candidate, the Honda
250-class conversion the design actually assumes, has no published figure of any kind.
Endurance is exactly inversely proportional to BSFC in this model (BSFC enters mass
flow linearly and nothing else), so:

| Full-load BSFC | Effective at 30.0% load | Endurance |
|---|---|---|
| **250 g/kWh (as optimised — the §6 target)** | **339.3** | **166.56 h — 6.94 d** |
| 270 g/kWh (the §6 assumption) | 366.4 | 154.22 h — 6.43 d |
| 300 g/kWh (the §6 walk-away) | 407.1 | 138.80 h — 5.78 d |
| **330 g/kWh (the verified units)** | **447.8** | **126.18 h — 5.26 d** |

**This single row is the largest uncertainty in the report.** It is not an aerodynamic
question and it cannot be closed by analysis. It is closed by putting an engine on a
dyno.

Note also that the variable sits **on its bound**. An optimiser that takes the floor of
a procurement variable is telling you the answer is limited by procurement, not by
design — and v5.0's takes the floor exactly, where v3.0's took 0.2519, marginally
inside.

### 4.5 The propeller — a defect found, and fixed

**v3.0 and v4.0 were both first written with v2.0's propeller.** The cause is
structural and still present in the repository: `scripts/prop_design_sweep.py` and
`scripts/prop_refine.py` both **load `design/argus7_v2.yaml`** and both **hardcode
v1.0's boom station** (`BOOM = 0.6206 − 0.045`). Neither takes a design path. Anyone
re-running them gets a propeller for a 248 kg aircraft with an 8.15 kW engine at
4,191 m, regardless of which aircraft they meant.

The consequence, measured with `argus7.prop.bemt` at each aircraft's own mid-burn
loiter condition:

| Design point | Level-flight thrust required, mid-burn | The inherited v2.0 disc at 1,900 rpm delivers | Shortfall |
|---|---|---|---|
| **v3.0** as committed | 78.2 N | **58.1 N** | **−25.8%** |
| v4.0, before its propeller was re-solved | 76.0 N | 61.4 N | **−19.1%** |
| v5.0, had it inherited | 76.4 N | 60.1 N | −21.3% |

**v3.0 as published in the previous revision of this report could not hold level
flight at its own loiter point.** That is the defect, stated plainly rather than
absorbed. v4.0's design file records the fix in its own header comment; v5.0 carries it
forward.

**The v5.0 propeller, solved at v5.0's operating point:**

| | v3.0 (inherited) | **v5.0 (solved here)** |
|---|---|---|
| Diameter / blades / p/D | 1.04 m / 2 / 0.95 | **1.04 m / 2 / 0.95** |
| Loiter rpm | 1,900 (wrong for the aircraft) | **2,050** |
| Reduction ratio | 3.947 : 1 | **3.659 : 1** for a 7,500 rpm engine |
| Loiter efficiency at that rpm | 0.8581 (v2.0's) | **0.8530** |
| Climb power absorbed | 101.3% at 2,675 rpm | **101.2% of 10.849 kW at 2,675 prop rpm** |
| Tip Mach at loiter | 0.306 | **0.329** (against a 0.75 limit) |
| **Boom clearance** | 190 mm | **229 mm** |

At 2,050 rpm the disc makes **84.1 N against the 76.4 N** required at mid-burn — a 10%
margin — and the crank sits at **2,050 × 3.659 = 7,501 rpm**, on the assumed rating
rather than 7% above it as v3.0's gearing implied. The propulsion set closes at the
loiter design point.

**Variable pitch is not needed for the loiter mission — a genuine save.** The
loiter-optimal pitch is the same p/D the fixed-pitch optimum already uses, so a
constant-speed unit buys **+0.00%** at loiter. It would add mass, cost and a failure
mode to a 167-hour unattended flight for no endurance. **This conclusion does not
survive §8.4**, where the ferry mission wants a propeller this one cannot be.

**Three things about the propeller record that are still open:**

**(a) No committed script produces the v5.0 propeller.** `prop_design_sweep.py` and
`prop_refine.py` still load v2.0 and still hardcode v1.0's boom station. The v5.0
entries in the design file were solved interactively and reproduced here from
`argus7.prop.bemt` directly. **The propeller is verified but not regression-guarded**,
which is the same status as everything else in §11.5.

**(b) The rpm the design file records is the mid-burn rpm, not a fixed property.** A
fixed-pitch propeller on a throttled engine changes rpm with load. Across the burn the
disc needs **2,340 rpm at full fuel, 2,005 at mid, 1,600 dry**. At full fuel that is a
crank speed of **8,562 rpm — 114% of the assumed 7,500 rpm rating**, just inside the
engine module's own 1.15× overspeed limit and outside the speed at which its power
peak, and therefore its BSFC map, was defined. **The BSFC used for the first third of
the mission is read at a crank speed the engine deck does not cover.** Not quantified;
it is the next thing the engine deck should be asked.

**(c) `docs/decisions/2026-08-21-propeller-selection.md` describes a different
propeller on a different aircraft.** It selects 1.00 m at p/D 1.05 and 1,900 rpm,
preferring it over the 1.04 m disc because the larger one *"leaves only 56 mm to the
booms."* That 56 mm is computed from **v1.0's** boom station. On v5.0 the booms sit at
y = ±0.7943 m and the true clearance for a 1.04 m disc is **229 mm** — four times the
figure that drove the recommendation. **The record is superseded by the design file
and by this section**, and it should be marked as such.

---

## 5. Stability and control

This is where v1.0 fails hardest, and it is where v5.0 makes the change that v3.0 could
not.

### 5.1 Why v1.0 was divergent

Until `argus7/analysis/balance.py` was written, **nothing in the repository could
compute a CG, a neutral point, or a static margin** — while the report published
"+14.7% MAC at CG 42%" and `research/design_pack.md` published "neutral point 55% MAC,
static margin 10%". Two research packs
(`research/configuration_hypotheses.md` §3, `research/empennage_trade.md` open question
8) had already recorded from hand build-ups that the aircraft *"does not balance"*, and
it was never followed up in code. The retired v2.0 then grew the wing 40% with nothing
checking.

Measured on `design/argus7_v1.yaml` at its committed wing station (`x_le_frac` 0.22,
root LE at x = 0.748 m):

| | v1.0 |
|---|---|
| Neutral point, analytic (wing + tail) | 52.95% MAC |
| Neutral point, **AVL, independently** | **58.30% MAC** |
| CG, full fuel | **97.0% MAC** |
| CG, dry | **135.1% MAC** |
| **Static margin, full → dry** | **−44.0% → −82.2% MAC** |
| Static-margin excursion over the burn | **−38.15% MAC** |

The CG sits **194 mm aft of the neutral point at full fuel and 363 mm aft of it dry.**
This is not a marginal aeroplane; it is a divergent one, for the whole flight.

**Crucially, this is not a modelling artefact.** The **neutral-point half of the
published stability line reproduces**: 52.95% analytic and 58.30% from the vendored
AVL bracket the published ~55% MAC. It is the **CG half** that does not exist. The
report's 42% MAC CG is an assumed target that no mass build-up on the committed
geometry supports. It cannot be recovered by tuning the equipment layout either:
moving **all 63 kg** of payload, avionics and recovery to the nose at x = 0 still
leaves v1.0's CG at 72% MAC. It is the **wing station**, and `x_le_frac = 0.22` was
tagged `assumption` and sourced to nothing.

`research/design_pack.md`'s claim that fuel tanks at the AC hold CG travel under 0.5%
MAC fails by **76×** on v1.0. The *mechanism* is sound — fuel at the CG moves the CG
not at all — but it is conditional on the CG being where the report assumes. The fuel
centroid is at 41.2% MAC, close to the claimed 45%; the CG is at 97.0%.

All of the above is asserted by strict `xfail` tests in `tests/test_balance.py` that
carry the measured numbers in their reason text and will **error** the moment anyone
makes them pass without rewriting the reason.

### 5.2 The v5.0 neutral point

    Xnp/MAC = Xac_wing/MAC + V_h · (a_t/a_w) · (1 − dε/dα) · η_t

| Term | v3.0 | **v5.0** |
|---|---|---|
| Wing AC | 25% MAC (thin-airfoil; see the bias note below) | 25% MAC |
| V_h | 0.4218 | **0.6018** |
| a_w (Helmbold/DATCOM) | 5.724 /rad (AR 21.44) | **5.790 /rad** (AR 24.57) |
| a_t (panel AR 3.0) | 3.335 /rad | 3.335 /rad |
| dε/dα = 2a_w/(πAR) | 0.1700 | **0.1500** |
| η_t (tail dynamic-pressure ratio) | 1.00 | 1.00 — the inverted V sits on booms outboard of the fuselage wake and ahead of the pusher disc |
| **Tail contribution** | +20.40% MAC | **+29.46% MAC** |
| **Neutral point, analytic** | 45.40% MAC | **54.46% MAC** (x = 1.7212 m) |
| **Neutral point, AVL (wing + inverted-V tail, real dihedral)** | 50.98% MAC | **59.70% MAC** (x = 1.7495 m) |
| Munk fuselage apparent-mass term | −4.47% MAC | **−4.49% MAC** |

The tail contribution has grown by half, and it is bought with **arm**, not area: S_h
fell 13% while the arm grew 61%. That is the efficient direction — arm costs boom mass
and boom drag, area costs both plus tail mass — but it is also what put a 6.25 m
cantilever on the aircraft (§6.6).

### 5.3 CG, static margin and fuel burn

| Fuel state | Mass (kg) | x_cg (m) | CG (% MAC) | SM (% MAC) | SM with Munk pod (% MAC) |
|---|---|---|---|---|---|
| Full | 320.00 | 1.6524 | 41.74 | **+12.72** | +8.23 |
| Half | 233.79 | 1.6508 | 41.44 | +13.02 | +8.53 |
| Dry | 147.58 | 1.6473 | 40.79 | **+13.68** | +9.18 |

**Static-margin excursion full → empty: +0.95% MAC**, and it moves in the *safe*
direction — the aircraft gets more stable as it burns fuel, not less.

This is the finding that justifies putting the layout in the optimiser. **The design
pack's "<0.5% MAC CG travel" claim, which failed by 76× on v1.0, is very nearly
achieved here** — 0.95% against a claimed 0.5%, and achieved *for the reason the pack
gave*, not by accident. The fuel centroid sits at **42.55% MAC**, 95 mm aft of the wing
AC and within **0.8% MAC of the CG itself**, so 172.4 kg — 54% of gross mass — burns
off while moving the balance by less than 1% of chord.

Note that v3.0 did better on this one metric (−0.08% MAC), and v5.0 is not worse for
it: v3.0 bought its near-zero travel at a static margin that failed the gate. **A
+0.95% travel inside an 8–20% window is a better aeroplane than a −0.08% travel below
the floor.**

Moving the wing station from 0.22 to 0.4075 is what does it. It moves the neutral
point aft nearly 1:1 while moving only the wing group and the wing fuel with it, so
static margin rises monotonically with `x_le_frac` — and it simultaneously puts the
tanks where the CG lands.

### 5.4 The honest band, and the two biases that partly cancel

**The static margin depends on which neutral point you believe, and the spread is
wide.** On v3.0 that spread straddled the gate. On v5.0 it does not.

| Reading | Neutral point | SM, full fuel | SM, dry | 8–20% MAC gate |
|---|---|---|---|---|
| Analytic, wing + tail (the convention the spec and the published 55% figure are written in) | 54.46% MAC | **+12.72%** | **+13.68%** | ✅ |
| Analytic + Munk fuselage term | 49.97% MAC | **+8.23%** | +9.18% | ✅ (by 0.23 points) |
| **AVL, wing + tail** | **59.70% MAC** | **+17.96%** | +18.91% | ✅ |
| AVL + Munk fuselage term | 55.20% MAC | **+13.46%** | +14.41% | ✅ |
| The batched model the optimiser searched with | — | +19.92% | +16.91% | (search only) |

**All four readings clear the floor at both fuel states, and all four sit under the
ceiling.** That sentence could not be written about any previous design point in this
programme. The tightest reading — analytic plus the Munk pod term — clears 8% by
0.23 points at full fuel, which is thin; the widest — AVL without the pod — reaches
18.91% dry, 1.1 points under the ceiling. **The design is inside the window on the
pessimistic reading and inside it on the optimistic one**, and the gate is met without
having to argue about which convention is right.

**Two known method biases run in opposite directions and are declared, not netted:**

1. **The 25% wing AC is conservative.** Running the AVL deck with the tail surface
   deleted puts the isolated wing's AC at **30.2–30.5% MAC** on a planform with sweep,
   taper and twist — 5.2 to 5.5% MAC aft of the quarter-chord. Every static margin
   computed with 0.25 is therefore **understated by about 5% MAC**. That difference,
   not any tail effect, is most of the gap between the analytic and AVL neutral points.
2. **The Munk pod term is not in the headline number and it is worth −4.49% MAC.** It
   is excluded because the specification's relation and the published 55% MAC figure
   are both wing-plus-tail only, and because AVL — the independent check — carries no
   fuselage. It is Munk's apparent-mass estimate, which
   `research/configuration_hypotheses.md` §3.3(a) computes for this pod as 8.2% on
   v1.0 against 7.3% by the more elaborate Multhopp strip method: **this term is the
   pessimistic end of the published band.**

Applied together (AVL wing AC + Munk pod) the answer is **+13.46% MAC** — almost
exactly the middle of the spec window.

**One thing that is not in this analysis at all:** dynamic stability, control power,
trim authority, spiral and Dutch-roll modes, aeroelastic trim, and departure
behaviour. This is a longitudinal static balance and nothing more. On a wing that
deflects 14.4% of semi-span at limit load (§6.2) and carries a 6.25 m boom-mounted
tail, the aeroelastic trim question in particular is not academic.

### 5.5 The gate v3.0 did not pass, and how it was closed

Recorded here because the mechanism matters more than the outcome.

The programme's pre-registered static-margin gate is
**8% ≤ SM ≤ 20% MAC** — `docs/superpowers/specs/2026-08-20-argus7-cad-sim-optimisation-design.md`
line 109, and line 178 makes *"no regression on static margin validity"* a conjunctive
adoption gate.

**The optimiser that produced v3.0 searched a 5–15% window instead.** The v3.0 design
file's own header records it. Nothing in `docs/decisions/` records a ruling that moved
8–20% to 5–15%. v3.0 landed at **+5.79%** and duly failed the real gate — which is
exactly what `docs/decisions/2026-08-20-gauntlet-preregistration.md` exists to prevent,
and which §11.3 of this report condemns in the abstract.

**How it was closed, and the closure carries its own caveat.**
`scripts/run_optimisation_layout.py` now carries `SM_LO, SM_HI = 0.08 + 0.047,
0.20 + 0.047`. The `+0.047` is a deliberate offset, and the script says why in a
comment: **the batched balance model used inside the search reads about 4.7% MAC high
against the authoritative `argus7.analysis.balance`** — it returned 10.5% where the
scalar module measured 5.79% on v3.0. Biasing the search window compensates for a known
model disagreement so the search lands where the authoritative module will confirm it.

That is a defensible engineering move and it worked: v5.0's search value is 19.92% and
its verified value is 12.72%, a 7.2-point gap in the expected direction, landing
comfortably inside the real window. **But it is a magic number tuned on one comparison,
it is 53% larger than the discrepancy it was fitted to, and the honest description is
"search with the biased model, verify with the authoritative one" — which is what was
done.** The verification is what this report publishes; the search value appears
nowhere in §5.3.

---

## 6. Structures

**This section is new.** The previous revision of this report opened §6 with *"The
structural work in this repository is research-grade, not design-grade: no FEA, no test
coupons, no article."* CalculiX and gmsh had been installed since day one and never
pointed at the airframe; `docs/argus7_v3_premortem.md` mode #7 — *"the wing that was
never analysed"* — scored the highest impact on the page and the worst detection
profile, precisely because nothing existed to detect anything with.

`scripts/structural_analysis.py` and `docs/decisions/2026-08-21-structural-analysis.md`
are the first structural analysis in the programme. **It does not clear mode #7. It
confirms the concern and adds a specific, quantified defect to the mass model.**

### 6.0 What is trustworthy here, and what is not — read this first

| Result | Method | Status |
|---|---|---|
| Tip deflection 14.4% of semi-span at limit | analytic M/EI double integration over the tapered spar | **Cross-validated** — `research/materials_pack.md` independently gives 14.2% |
| Root cap stress 600 MPa at ultimate | closed form on the mass model's own sizing | **Trustworthy, and circular** — this is how the mass model sizes, so a zero margin is a tautology, not a result |
| Cap buckling critical at 80 MPa | plate/column buckling between ribs | **Sign trustworthy, magnitude uncertain** — corroborated independently by the cap's b/t ratio, §6.3 |
| Divergence ~1,030 km/h, flutter ~493 km/h | first-order torsional divergence and a binary flutter approximation | **Directionally trustworthy** — a 2.4× margin is robust to a crude method |
| Boom first torsion 14.5 Hz | Bredt closed-cell torsion on the derived boom length | Trustworthy at the level of a hand calculation; **supersedes** the research pack's 22.7 Hz |
| **CalculiX beam FEA — deflections and mode shapes** | B31 Timoshenko beams, section converted to an equivalent rectangle | **NOT TRUSTWORTHY. Its numbers are not used anywhere in this report and should not be quoted.** |

**On the FEA, plainly.** The beam model does not reproduce the cross-validated
deflection. The fault is in the section definition: section properties are converted to
an equivalent rectangle, and CalculiX's local-axis convention means the bending
direction and the section's strong axis are not reliably aligned. One bug in that
conversion (b and h transposed, worth a factor of 10⁴ in second moment of area) was
found and fixed; the conversion has since been revised again, and **the model's tip
deflection has moved by more than an order of magnitude across those revisions within a
single working day, without ever landing on the cross-validated 14.4%.** A model whose
answer moves that far when the person editing it changes their mind about an
orientation vector is not measuring the wing.

The modal frequencies come from the same model and inherit the same doubt. **They are
deliberately not reproduced in this report.** The one modal number quoted anywhere here
— the boom's 14.5 Hz first torsion — is an analytic Bredt calculation, not a CalculiX
output.

**What would settle it:** define the section explicitly with
`*BEAM SECTION, SECTION=GENERAL`, giving A, I11, I12, I22 and J directly rather than via
an equivalent rectangle, and validate against a uniform cantilever with a closed-form
solution *before* trusting any tapered result. Until that is done the FEA contributes
nothing and the analytic routes carry the section.

### 6.1 The load case and the spar

`argus7.opt.design_space` sizes the spar cap from root bending moment:

    M_root = n_ult · W · (b/2) · k_lift · fuel_relief
    A_cap  = M_root / (h_spar · σ_cap),  h_spar = (t/c) · c_root
    m_cap  ∝ ρ · A_cap · (b/2) · k_taper

with n_ult = 5.7, k_lift = 0.40, fuel relief 0.78, σ_cap = 600 MPa (compression
allowable, nominally carrying a buckling/damage knockdown), ρ = 1600 kg/m³.
Substituting gives **m_cap ∝ W · AR^1.5 · √S / (t/c)** — the exponent verified
analytically by the gauntlet audit, and the wing-mass *ratio* between two design points
agreed with Raymer's independent GA regression to 1.0%.

| | v1.0 | v3.0 | **v5.0** |
|---|---|---|---|
| Root chord | 0.5807 m | 0.6192 m | **0.7720 m** |
| **Spar depth at root** | 79.6 mm | 118.2 mm | **169.8 mm** |
| Ultimate root bending moment | 20.19 kN·m | 30.74 kN·m | **33.08 kN·m** |
| **Required cap area** | 423 mm² | 433 mm² | **325 mm²** |
| Cap mass | 14.56 kg | 18.16 kg | **14.31 kg** |
| Skin / rib / systems (4.6 kg/m²) | 17.94 kg | 27.23 kg | **26.31 kg** |
| **Wing total** | **32.51 kg (8.33 kg/m²)** | **45.39 kg (7.67 kg/m²)** | **40.63 kg (7.10 kg/m²)** |

**The interesting row is the cap area: 325 mm² against v1.0's 423 mm², despite +28%
MTOW and +28% span.** Thickening the section from 13.7% to 22.0% makes the spar 113%
deeper, and depth buys cap area back faster than weight and span consume it. That is
the mechanism by which a much larger wing costs only +8.1 kg over v1.0's and is
*lighter* than v3.0's.

**Areal density cross-check, and it has crossed to the wrong side.** 40.63 kg on
5.7201 m² is **7.10 kg/m²**. The materials pack's costed build options, computed from
first principles: Option A (moulded CFRP sandwich, female moulds) 6.85 kg/m²,
Option B (pultruded strip caps + moulded sandwich skin, the recommendation)
**7.40 kg/m²**, Option C3 8.65 kg/m². **v3.0's wing sat 3.6% above the recommended
build. v5.0's sits 4.0% below it.** That is not evidence of a lighter wing; it is the
mass model returning a number the recommended build does not reach, and it is the same
direction as §6.3's finding.

### 6.2 The wing is very flexible, and that is cross-validated

Two independent routes agree:

| Route | Tip deflection at limit (+3.8 g) |
|---|---|
| M/EI double integration over the tapered spar (`scripts/structural_analysis.py`) | **14.43% of semi-span** |
| `research/materials_pack.md`, independently derived | **14.2%** |

**Agreement to 0.2 points across separately-derived methods. 855 mm of tip rise at
limit load on a 5.93 m semi-span**, and **1,283 mm — 21.6% — at ultimate**, far enough
into geometric non-linearity that a linear beam calculation stops being trustworthy at
the ultimate case. Modern 15 m sailplanes run 8–10%. **This is a sailplane wing, not a
light-aircraft wing.**

It is not obviously disqualifying, and it should not be presented as if it were. It is
also not free:

- **It inverts the material argument.** The figure of merit for a stiffness-critical
  wing is E/ρ, not σ/ρ. Pultruded rod's 1,682 MPa compressive strength buys nothing
  here; high-modulus pultrusion (+71% EI at equal mass) is the right lever, and it is a
  procurement decision, not a layup one.
- **It interacts with the span efficiency the endurance rests on.** The AVL sweep
  measured e on an undeflected planform. An 855 mm tip rise changes the spanload, the
  dihedral effect and the effective aspect ratio. Nothing in this stack couples them.
- **It interacts with control effectiveness and with flutter.** §6.4 says the flutter
  margin is large; that estimate is made on an undeflected wing.

For comparison, v3.0's wing was **15.3%** at limit on the same method — marginally
worse. This is one of the few structural quantities where v5.0's deeper section helps.

### 6.3 Buckling governs the sizing, and the margin is negative

The cap reaches its 600 MPa material allowable exactly at ultimate — zero margin **by
construction**, because that is how the mass model sizes it. That row is a tautology.

The row that is not a tautology is local buckling of the compression cap between ribs:

| | Value |
|---|---|
| Cap section, as assumed by the analysis | 36.0 × 9.01 mm |
| Rib pitch | 350 mm (assumed) |
| **Critical stress** | **80.2 MPa** |
| Applied stress at ultimate | 600 MPa |
| **Margin** | **−86.6%** |

**The cap would buckle at roughly an eighth of the load the material could carry.**

**An independent corroboration, from a completely different route.** The gauntlet audit
condemned the original challenger's cap laminate on a width-to-thickness argument:
1.10 mm thick at b/t ≈ 200 is *"not entitled to a 600 MPa allowable already carrying a
buckling knockdown."* Applying the same test at a 0.25c cap width:

| | v1.0 (the calibration point) | v3.0 | **v5.0** |
|---|---|---|---|
| Cap width × thickness | 145 × 2.91 mm | 155 × 2.80 mm | **193 × 1.68 mm** |
| **b/t** | **50** | **55** | **115** |

**v3.0 sat essentially where the calibration point does. v5.0 sits at more than twice
that slenderness**, because a 170 mm-deep spar needs only 325 mm² of cap and spreading
325 mm² over a 193 mm width leaves a 1.68 mm laminate. The previous revision of this
report was able to write *"the buckling concern raised by the audit does not bite
here."* **On v5.0 it bites.** Two independent methods — an explicit buckling
calculation and the audit's b/t heuristic — say the same thing, and they were not
calibrated against each other.

**What this changes, and it is not a caveat:**

- **The mass model is optimistic.** A buckling-sized cap is heavier than a
  strength-sized one. The mass model uses the latter, so wing mass is understated by an
  amount nobody has computed.
- **Wing mass converts to endurance at 1.51 h/kg** (§6.5). This is therefore an
  endurance correction of unknown size and known sign.
- **The fix is not more carbon.** It is rib pitch, cap width-to-thickness ratio and
  skin support — a design task. A narrower, thicker cap at the same area buckles at a
  higher stress for no mass; closer ribs cost a little mass and buy a lot of critical
  stress. Both are available. Neither has been done.
- **σ_cap = 600 MPa is applied without a minimum-gauge or panel-buckling floor**, which
  was already a declared model limit. v5.0 is the first design point that stands on it.

**The honest caveat, from the analysis's own record:** the cap cross-section aspect
ratio in the buckling calculation is assumed, not designed, and the rib pitch is
assumed. **The magnitude of the shortfall is uncertain; its sign is not**, and the b/t
cross-check makes the sign independent of the assumption.

### 6.4 Aeroelastic — the good news, and it retires a real worry

| | Value |
|---|---|
| Root GJ | 202 kN·m² |
| **Divergence speed** | **~1,030 km/h TAS** |
| Wing first torsion | ~34 Hz |
| **Flutter estimate** | **~493 km/h TAS** |
| Power-limited maximum level speed (§8.3) | **207 km/h** |

**Both aeroelastic speeds are far above the power limit, so the aircraft is
power-limited rather than aeroelastically limited.** That retires the concern raised
when the speed envelope was first computed: a high-aspect wing on slender booms might
have capped V_max below its power limit. It does not — the flutter margin is 2.4×.

**These are first-order estimates** — torsional divergence and a binary flutter
approximation, not a coupled aeroelastic solution — and the flutter estimate uses an
assumed wing torsional mass (half of 60% of the airframe mass, 20.6 kg, against an
actual wing mass of 40.63 kg) and an assumed radius of gyration of 0.25 MAC. The margin
is large enough that the *conclusion* survives the method being crude; the *number*
should not be quoted to three figures, and this report does not.

For scale: v3.0's same calculation gave divergence at 721 km/h and flutter at 352 km/h
— still above its power limit, but v5.0's deeper, stiffer section roughly doubles GJ
and buys a 40% higher flutter speed for free.

### 6.5 The mass-to-endurance exchange rate

**Measured on this design point: 1.51 h/kg** (removing 1 kg of fuel at constant MTOW
costs 1.511 h). The materials pack independently derived 1.5 h/kg on v1.0; the previous
revision measured 1.41 h/kg on v3.0. Every structural decision can be priced with it,
and every one of §6's open items is a mass item.

### 6.6 The booms, and why the research pack no longer describes them

`research/boom_construction_pack.md` sizes the booms to a **stiffness** criterion
(1.5° of tail rotation), not a strength one, and corrects the tail load upward by
1.81× from the materials pack's figure. **Every number in it was computed for a 3.646 m
boom carrying a 0.31 m² tail behind a 0.813 m propeller at 2,100 rpm. v5.0 has a
6.25 m boom carrying a 0.32 m² tail behind a 1.04 m propeller at 2,050 rpm.** The boom
is **71% longer** than the one the pack sized, and boom bending stiffness requirements
scale with the cube of length.

What survives, what has moved, and what has not been re-run:

- **Re-run for v5.0, and it moved: first torsional frequency is 14.5 Hz**, against the
  pack's 22.7 Hz for the 3.65 m boom. Propeller 1P is at 34.2 Hz and blade passage at
  68.3 Hz, so the nearest separation is **19.7 Hz** and the mode is clear. This is the
  one boom number that has been re-derived at this design point, and it is *better*
  separated than the pack's was, because the longer boom moved the mode down and away
  from 1P rather than into it. `docs/decisions/2026-08-21-structural-analysis.md`
  records this as superseding the pack.
- **Not re-run, and the pack's recommendation is now certainly wrong:** the stiffness
  sizing. The pack recommends COTS roll-wrapped **110 mm × 2.0 mm, 7.54 kg for the
  pair** (9.20 kg with fittings) for a 3.646 m boom. The design file still specifies
  **Ø90 mm**, which met the pack's requirement only at 10.06 kg on the short boom. **On
  a 6.25 m boom neither figure applies**, and the tail rotation criterion has not been
  evaluated. The 28 kg fixed non-wing airframe mass (§2.2) is carrying this.
- **The propwash premise is geometrically false, and that is the good news.** The booms
  clear the propeller tip path by **229 mm** on v5.0 (§4.5) and sit in the acoustic near
  field at ~10–30 Pa, not in the wake at 300–560 Pa — a 20–40× difference in
  excitation. Forced-response on v1.0's geometry gave a peak vibratory strain of
  **0.011% against a 0.6% matrix fatigue limit: a 55× margin.** The clearance argument
  strengthens with every design point because `booms.y_station_frac` is a fraction of
  semi-span; the forced-response number has not been re-run.
- **Three configuration prohibitions follow and are unchanged:** nothing structural
  inside r = 0.45 m of the thrust axis aft of the prop plane; the first torsional mode
  must be resolved against the true loiter rpm (now done, 14.5 Hz vs 34.2 Hz); and
  **measure it** — one tap test with the tail fitted settles the section in an
  afternoon.
- **The tail attachment as proposed has a negative margin before fatigue**: two M6 at
  60 mm centres carrying the panel root moment gives 306 MPa of bearing against a
  165 ± 28 MPa allowable. A Ø50 × 150 mm spigot gives 1.76 MPa. **Zero mass, zero drag,
  a factor of 174 on the margin.** This is the cheapest fix in the programme and it is
  still not in the design.

### 6.7 What the materials research establishes

The sponsor's premise — *"carbon fibre rods and tubes and 3D printed parts as much as
possible"* — was evaluated and is **right about spar caps and booms, wrong about the
wing spar and the skins, roughly break-even on ribs.**

| Claim | Verdict | The number |
|---|---|---|
| Pultruded UD carbon as spar-cap material | **Right, strongly** | 1,682 MPa compressive / 133.8 GPa measured, two independent vendors agreeing. E/ρ **87.9 vs 77.8** for hand wet layup — it matches prepreg on specific stiffness with no autoclave, no freezer, and no layup skill |
| COTS carbon tube for the twin booms | **Right** | 90 × 2.5 mm roll-wrapped runs at 102 MPa against a 620 MPa allowable — **4× strength margin**, stiffness-critical. **Computed for a 3.646 m boom; v5.0's is 6.25 m and this has not been re-run** |
| COTS carbon tube as the **wing** spar | **Wrong, by a clean geometric factor** | A round tube inside a 12%-thick wing needs **2.07×** the material of a cap-and-web spar for the same moment. The ratio is 2h/D — pure geometry, not a materials argument |
| 3D-printed ribs, fairings, trays, ducts | **Acceptable at a 3.8–4.4× mass penalty** | Rib stress **0.06 MPa, 170× below the creep-test floor**. This is where the preference is simply free — **but see §6.3: rib pitch is now a structural variable, not a free one, and printed ribs in a wet-wing tank bay also have to seal** |
| Printed skin panels | **Wrong, decisively** | ±1.14 mm MJF tolerance against a 0.512 mm step budget; **+18.7 kg**, 46% of v5.0's entire wing budget |
| Heat-shrink film skin | **Wrong, but not for the usual reason** | Streamwise waviness actually passes. It fails because film cannot form the leading edge, and its scalloping is a **spanwise** disturbance for which NASA states no criteria exist |
| Printed tooling, plugs, jigs | **Right, and under-used** | The highest-leverage use of printing on the programme — it attacks the €9–14k wing-tooling quote that is the premortem's highest-probability failure mode |

**And the surface-quality bar is about 6× looser than the programme assumed.**
Carmichael's allowable single-wave h/λ at Re 0.6–1.1 M is 0.031–0.044, because
allowable waviness scales as Re^−0.75. NASA TP-2256 **measured** moldless homebuilt
VariEze/Long-EZ wings at h/λ 0.0030–0.0046 — passing with 2.6–4.9× margin. **A garage
build can hold laminar flow.** Measured, not asserted. Note that v5.0's tip Reynolds
number is *lower* than the range that criterion was tabulated over, which makes the
allowable *looser* still, not tighter.

### 6.8 Recovery

Unchanged from v1.0 in mass (7.0 kg) and unchanged in the design file, but **the
aircraft got 28% heavier and the recovery system did not**.

| | v1.0 | v3.0 | **v5.0** |
|---|---|---|---|
| Recovery mass allowance | 7.0 kg | 7.0 kg | **7.0 kg (unchanged)** |
| Descent rate on v1.0's 85 m² canopy, at MTOW | 5.43 m/s | 6.07 m/s | **6.14 m/s** |
| Canopy area for 6 m/s at MTOW | 69.5 m² | 87.0 m² | **89.0 m²** |
| Touchdown energy at 6 m/s, dry recovery mass | 2.67 kJ | 2.74 kJ | **2.66 kJ** |
| Touchdown energy at 6 m/s, MTOW | 4.50 kJ | 5.63 kJ | **5.76 kJ** |

Recovery normally happens near dry mass, where v5.0 is essentially identical to v1.0
(2.66 vs 2.67 kJ) — the airbag/crush-keel case does not move, and v5.0's *dry* mass is
actually 1 kg lighter than v1.0's because it burns proportionally more fuel. **The MTOW
case does move**, and the ground-risk argument in v1.0 §9 was built on the 3–4.5 kJ
figure. The gauntlet audit's recommendation that recovery mass scale with MTOW
(7.0 → 8.96 kg at 320 kg) is not implemented.

---

## 7. Mission performance — endurance

### 7.1 How the 6.97 days is computed

`argus7.mission.sim.simulate_loiter` integrates a pure loiter until the fuel is gone,
in 120 equal-fuel-mass steps by the midpoint rule. Per step, at weight W:

    C_L      = min( √(3·C_D0·π·AR·e),  C_Lmax / 1.15² )     [stall-limited here]
    C_D      = C_D0 + C_L² / (π·AR·e)
    V        = √( 2W / (ρ·S·C_L) )
    D        = W / (L/D)
    P_shaft  = D·V / η_prop  +  P_elec / η_alt
    ṁ        = BSFC · P_shaft
    E        = Σ Δm / ṁ

with η_alt = 0.75, P_elec = 500 W, ρ from the ISA at 4,000 m, and BSFC = 339.3 g/kWh
(the part-load value at the mid-burn load fraction, §4.3).

Result at **η_prop = 0.858**, the value hardcoded in
`scripts/run_optimisation_layout.py`: **167.325 h = 6.9719 days**, reproducing
`opt_runs/layout_final.json` to 0.008%.

**Result at η_prop = 0.8529, the value `design/argus7_v5.yaml` records for its own
propeller: 166.562 h = 6.9401 days.** The report's headline is the first number
because that is what the optimiser recorded; **the second is the one the design file
supports**, and the gap is §4.3 item 5.

| | Full | Mid | Dry |
|---|---|---|---|
| Mass (kg) | 320.00 | 233.79 | 147.58 |
| TAS (km/h) | 119.8 | 102.4 | 81.4 |
| Drag (N) | 104.6 | 76.4 | 48.2 |
| Shaft power (kW) | 4.75 | 3.21 | 1.94 |
| Engine load fraction | 43.7% | 29.6% | 17.9% |
| Engine-deck BSFC at that power (g/kWh) | 307.3 | 350.1 | 436.5 |

### 7.2 The validation gates it passed

**Gate 1 — the step integration must reproduce the closed-form Breguet solution.**
Called with `payload_power_w = 0` and a constant BSFC — the conditions under which the
analytic solution exists — the 120-step integrator matches the Breguet form to better
than 0.001% on this design point's polar, and moving to 20,000 steps changes the answer
by a further 0.0007%, so the discretisation contributes nothing. The committed test,
`tests/test_mission_sim.py::test_gate1_step_integration_matches_closed_form_breguet`,
runs the same gate on **v1.0's** polar at 400 steps — 142.7478 h against 142.7478 h — at
a <0.1% threshold.

**Gate 2 — the same simulator must reproduce the published v1.0 endurance.** Run on
v1.0's published polar (S 3.9, AR 22, C_D0 0.020, e 0.85, MTOW 250, fuel 101.5,
4,000 m, BSFC 270, η_prop 0.84, 500 W payload), it returns **112.977 h against the
published 112.8 h: +0.16%.** Asserted by
`::test_gate2_reproduces_the_published_endurance`. The gauntlet audit's fully
independent re-implementation — its own ISA from the ICAO defining constants, its own
adaptive-quadrature Breguet integration — got **112.977 h** as well, and agreed with
the repository to **six significant figures** on the coupled model's own aero.

**This is worth stating precisely, because it is the trap this programme keeps
falling into: six figures of agreement means the arithmetic has been checked and
passed. It says nothing about the model.** The v1.0 number that reproduces to 0.16% is
a number for an aircraft that cannot balance, cannot hold its fuel, and cannot turn
its propeller.

### 7.3 Where the headline is optimistic, quantified

**BSFC was frozen at the mid-burn load and this costs 6.6 hours.** The optimiser
evaluates the part-load BSFC once, at the mid-point shaft power, and holds it constant
for the whole integration. But engine load falls from 43.7% to 17.9% across the burn,
and BSFC(load) goes as 1/load. By convexity the average of the true BSFC exceeds the
BSFC at the average load. Re-running the integration with BSFC evaluated **pointwise**
at each step's shaft power:

| | Endurance |
|---|---|
| BSFC frozen at mid-burn load, η 0.8529 | 166.56 h — 6.940 d |
| **BSFC evaluated pointwise across the burn** | **159.98 h — 6.666 d** |

**−6.58 h (−0.27 d).** This is a real, unreported optimism in the headline number, and
it is a property of the *evaluation*, not of the aircraft. It is 18% larger in absolute
terms than the same correction on v3.0, because v5.0 burns a larger fuel fraction and
therefore traverses more of the BSFC curve.

### 7.4 Sensitivity

#### v1.0's published anchors: two of the three are wrong

v1.0 §4 states: *"BSFC 250 g/kWh → +0.5 d; C_D0 0.016 → +0.36 d; loiter at 3,000 m
instead of 4,000 m → +0.23 d."* All three were re-derived by the gauntlet auditor from
first principles with independent code, and all three re-derived again with the
repository's own simulator on the published polar. Both derivations agree.

| Anchor | v1.0 published | **Measured** | Verdict |
|---|---|---|---|
| C_D0 0.020 → 0.016 | +0.36 d | **+0.358 d** (+8.588 h) | ✅ correct to 0.6% |
| BSFC 270 → 250 g/kWh | +0.5 d | **+0.377 d** (+9.038 h) | ❌ **the report is high by 33%** |
| 4,000 m → 3,000 m | +0.23 d | **+0.198 d** (+4.742 h) | ❌ **the report is high by 16%** |

**Two of the three published sensitivity anchors are wrong, and both errors are in the
optimistic direction.** Endurance is *exactly* inversely proportional to BSFC in this
model, so +0.5 d would require 244 g/kWh, not 250. The C_D0 anchor reproduces, which
corroborates `research/riblets_pack.md`'s appendix; the other two do not. Both are
levers the programme leans on.

#### v5.0's own sensitivities

Computed on the v5.0 design point at the design file's own η_prop 0.8529 and
bsfc_full 0.250 — **baseline 166.56 h (6.940 d)** — one lever at a time, everything else
held:

| Lever | Endurance | Δ |
|---|---|---|
| **Baseline** | **166.56 h — 6.940 d** | — |
| C_D0 −0.004 (an exceptionally clean build) | 180.29 h | **+0.572 d** |
| C_D0 +0.0035 (turret + cooling + base drag allowance) | 156.17 h | **−0.433 d** |
| Loiter at 3,000 m (band floor) | 173.31 h | **+0.281 d** — but coverage falls from 367 to 207 km², −44% |
| Loiter at 4,500 m (band ceiling) | 163.20 h | −0.140 d — coverage rises to 464 km², +27% |
| Payload duty-cycled to 350 W average | 179.16 h | **+0.525 d** |
| Oswald e 0.77 instead of 0.8101 (the open band, §3.4) | 162.79 h | −0.157 d |
| Full-load BSFC 270 instead of 250 | 154.22 h | −0.514 d |
| Full-load BSFC 330 (the verified units) | 126.18 h | **−1.682 d** |
| Non-wing mass charged honestly (−6.6 kg of fuel) | 156.77 h | **−0.408 d** |
| BSFC evaluated pointwise across the burn | 159.98 h | **−0.274 d** |

**The altitude row deserves its own sentence.** Going to the band ceiling costs
0.14 days and buys 27% more coverage area; going to the band floor buys 0.28 days and
gives up 44% of it. **Nothing in the objective function knows that coverage exists**,
which is why the optimiser sat on the floor of its altitude bound. On a
communications-relay aircraft that is an objective-function defect, not a design
choice, and it is the same defect that let the retired v2.0 fly below the band
entirely.

### 7.5 What is not modelled

Every endurance figure in this section is **pure loiter**. There is no transit segment,
no climb to altitude, no reserve, no descent, no hold, no diversion, and no wind. v1.0
published a deploy-mode table (2,000 km transit → 3.98 d on station); **nothing in
this repository can reproduce or replace that table**, and it should not be quoted.
§8 computes a straight-line ferry, which is a different mission, not a replacement.

The comms coverage figures in §1 are the v1.0 elevation-angle model rescaled to the
new altitude. No link budget, no antenna pattern, no measured data in this altitude
band.

---

## 8. Range and the speed envelope

**This section is new.** No previous revision of this report contained a range figure,
a cruise speed, a stall speed, or a maximum level speed. It is computed by
`scripts/range_analysis.py` from `design/argus7_v5.yaml` and the repository's own
models, and recorded in `opt_runs/range.json`.

### 8.1 Endurance and range are different missions at different speeds

This is the framing the section exists to establish, because conflating the two is how
a long-endurance aircraft acquires a range claim it cannot fly.

**Endurance maximises time aloft, so it flies at minimum *power*** — high lift
coefficient, slow. **Range maximises distance, so it flies at minimum *drag*** — the
best-L/D lift coefficient, faster. They are different flight conditions on the same
polar, and **you do not get both from one flight**.

| | Loiter mission | Ferry mission |
|---|---|---|
| **Time aloft** | **167.3 h (6.97 d)** | 131.8 h (5.49 d) |
| **Still-air distance** | not a useful quantity | **17,659 km** |
| Speed | ~102 km/h TAS (mean over the burn) | **134 km/h TAS** |
| Lift coefficient | 1.2098 (stall-limited) | ~1.03 (best L/D) |
| Governing quantity | C_L^1.5/C_D | L/D |

**L/D max is 30.42 at C_L 1.0281**; the loiter point sits at C_L 1.2098 where L/D is
30.02, so the loiter condition gives up only 1.3% of L/D — the polar is flat here, and
that is why the two missions are closer together than they would be on a conventional
aircraft.

### 8.2 The range result

| | Value |
|---|---|
| **Best still-air range** | **17,659 km at 134 km/h TAS** |
| Time aloft at that speed | 131.8 h = 5.49 d |
| Within 1% of best | **124–146 km/h** — a broad, flat optimum |
| Range at 120 km/h | 17,365 km (−1.7%) |
| Range at 200 km/h | 14,291 km (−19.1%), 71.5 h |
| Payload–range | 23,578 km at zero payload, 13,980 km at 82.5 kg, trading payload for fuel kg-for-kg at constant MTOW |

**The range optimum sits *faster* than textbook best-L/D would put it**, and the reason
is the engine, not the aerodynamics: BSFC depends on load fraction, so cruising harder
works the engine into a better part of its curve. That effect is worth several km/h of
optimum speed and it is a genuine coupling the simple Breguet range formula misses.

**A sanity check against a real aircraft.** The Vanilla VA001's 8-day record at 191 kg
is roughly 19,300 km of air distance if flown straight. v5.0 is a heavier aircraft with
a much larger payload and lands in the same order of magnitude. This is *not* the
discredited 16,000 km claim from the originating session revived — that was 200 kg on
BSFC 230 g/kWh with no stall margin; this is 320 kg on ~310 g/kWh part-load with the
stall margin active.

**A 10,000 km trip**, marched step by step at 200 km/h: **50.0 hours, 122.3 kg of fuel
burned, 50.1 kg remaining** — which is a meaningful reserve, and the only place in this
repository where a reserve appears at all.

### 8.3 The speed envelope

At the 4,000 m loiter altitude, from the drag polar and the rated shaft power:

| | MTOW 320 kg | mid-burn 234 kg | dry 148 kg |
|---|---|---|---|
| **Stall, clean, C_Lmax 1.60** | **104.2 km/h** | 89.0 km/h | 70.7 km/h |
| Loiter TAS (C_L 1.2098) | 119.8 km/h | 102.4 km/h | 81.4 km/h |
| **Maximum level speed, zero power margin** | **206.9 km/h** | 211.9 km/h | **215.1 km/h** |
| Maximum level speed at sea level | 183.2 km/h | 186.4 km/h | 188.5 km/h |
| Shaft power at 200 km/h, MTOW | 10.05 kW = **92.6% of rated** | | |

**200 km/h is the practical maximum**, at 93% of rated power. 206.9 km/h is the speed at
which the power margin reaches exactly zero, which is not a speed anyone flies.

**The stall speed is the operationally interesting number, and it is why the loiter
speed is not available at the start of the mission.** Stall at MTOW is 104.2 km/h and
the *mean* loiter speed across the burn is 101.8 km/h — **below the clean stall speed
at full fuel.** The aircraft cannot fly its own mean loiter condition until it has
burned off fuel; at MTOW it must fly 119.8 km/h, and it settles onto the slower
condition progressively. The endurance integration models this correctly (it computes
speed from instantaneous weight at every step), but the mission-planning consequence
should be stated: **the first hours of the mission are flown faster, higher-powered and
closer to the stall boundary than the headline loiter figure suggests.**

The margin against stall at MTOW, at the loiter condition, is exactly the 1.15 factor
the stall constraint imposes — 15% on speed, and it is *binding*, not chosen.

### 8.4 The range figure is not flyable with the recorded propulsion set

**This is the largest single caveat in this section, and it is not in
`scripts/range_analysis.py`.**

The range calculation holds propeller efficiency at **0.8529** — the *loiter* value —
at every cruise speed, and guards only against exceeding rated *engine power*. It never
asks whether the propeller can turn fast enough to deliver that power as thrust.

Running `argus7.prop.bemt` on the recorded 1.04 m, p/D 0.95, two-blade disc at each
cruise condition:

| Cruise speed | Thrust required at MTOW | Prop rpm to make it | η there | **Crank rpm through 3.659:1** |
|---|---|---|---|---|
| 102 km/h (loiter, MTOW) | 115.5 N | 2,240 | 0.828 | 8,196 |
| **134 km/h (best range)** | 103.4 N | **2,500** | **0.875** | **9,148 — 122% of rating** |
| 170 km/h | 118.4 N | 2,990 | 0.887 | 10,940 — 146% |
| 200 km/h | 144.0 N | >3,400 | — | >12,400 — 165% |

The propeller efficiency at those speeds is **better** than 0.8529, not worse — 0.875
to 0.889 — so the range figure is conservative in that one respect. **But the crank
speeds required are 22% to 65% above the 7,500 rpm rating the engine deck assumes**,
and `argus7/prop/engine.py`'s own overspeed ceiling is 1.15× (8,625 rpm).

Holding the crank to that 8,625 rpm ceiling, the fixed-pitch disc turns 2,357 rpm, and
the maximum level speed it can actually deliver is:

| | Maximum level speed, gearing-limited |
|---|---|
| MTOW 320 kg | **122.0 km/h** (shaft power used: 4.09 kW of 10.85) |
| mid-burn 234 kg | **130.5 km/h** (3.29 kW of 10.85) |

**The aircraft is not power-limited at 207 km/h. It is gearing-limited at about
122 km/h at MTOW, with two-thirds of its installed power unusable**, because a
fixed-pitch propeller on a fixed reduction ratio can only convert power to thrust
within a narrow band of advance ratio. **The 134 km/h best-range speed sits just
outside that band at MTOW and just inside it once fuel has burned off.**

**This is the same defect family as v1.0's C_P 0.911, seen from the other side.** v1.0's
propeller could not *absorb* its engine; v5.0's cannot *deliver* its engine at any
speed but the one it was optimised for. It does not affect the loiter mission at all —
the design mission — because loiter is where the propeller was solved. It invalidates
the ferry mission as currently specified.

**What settles it, and none of it is a redesign:** re-solve the reduction ratio jointly
with diameter and pitch against *both* missions; or accept two propellers (a loiter
blade and a ferry blade, a bolt-change on the ground); or reconsider variable pitch,
whose §4.5 dismissal was argued **on the loiter mission alone** and does not survive
this section. The 7,500 rpm rating is itself an assumption in `argus7/prop/engine.py`,
not a datasheet, so a real engine's speed range may reopen part of the gap on its own.

**Until one of those is done, this report claims the 17,659 km as a property of the
airframe and its fuel load, not as a flight the aircraft can perform.**

### 8.5 What else the range figure does not contain

- **Still air.** A 30 km/h headwind costs about 22% of range. There is no wind model
  anywhere in this repository.
- **No reserve, no climb, no descent, no diversion, no hold.** Fuel is burned to dry
  tanks. The 10,000 km case in §8.2 is the only calculation here with anything
  resembling a reserve, and that reserve is an outcome, not a requirement.
- **The full-load BSFC in `scripts/range_analysis.py` is hardcoded at 0.2506 kg/kWh**,
  the stage-1 optimiser's value, where the v5.0 design point uses 0.250. The effect is
  under 0.25% on range and in the conservative direction, but it is a number typed into
  a script rather than read from the design file, which is exactly what the provenance
  discipline exists to prevent.
- **Every BSFC caveat in §4.4 applies unchanged.** At a verified 330 g/kWh the range
  falls in roughly the same proportion as the endurance — about 24%, to some 13,400 km.
- **The aeroelastic clearance in §6.4 was checked against the 207 km/h power limit**,
  which §8.4 now shows is not the real limit. The margin only grows.

---

## 9. The lineage, and what each superseded point got wrong

### 9.1 Five design points, four corrections

| File | Endurance | Span | SM full / dry | Status |
|---|---|---|---|---|
| `argus7_v1.yaml` | 4.70 d published, **3.16 d** measured | 9.26 m | **−44.0% / −82.2%** | **Published, defective.** Statically unstable at every fuel state; wing cannot hold its fuel (101.5 kg into 66.1); propeller cannot absorb its engine (C_P 0.911) |
| `argus7_v2.yaml` | 4.88 d | 11.54 m | **−8.66% / −23.52%** | **RETIRED.** Still unstable; mass budget 13.02 kg short, traced to an engine-mass credit applied twice. (README's lineage table gives 5.02 d for this row; that figure is from `opt_runs/scaling3.log`, a later 250 kg scaling point with a 12.31 m span, not from `argus7_v2.yaml`.) |
| `argus7_v3.yaml` | 6.33 d | 11.27 m | **+5.79% / +5.71%** | **Superseded.** Balances, but **below the spec's own 8% floor** — the optimiser searched a 5–15% window, a pre-registered threshold moved without a ruling. Also carried **v2.0's propeller**, 26% short of level-flight thrust at its own loiter point |
| `argus7_v4.yaml` | 6.99 d | **12.0015 m** | +12.78% / +13.72% | **Superseded.** Stability gate met; **span 1.5 mm over the 12.0 m limit, failing gate G3** with zero buildable margin. Propeller re-solved at its own point |
| `argus7_v5.yaml` | **6.97 d** | **11.8558 m** | **+12.72% / +13.68%** | **Current.** 8 of 9 gates pass; the ninth (G7) is the engine and is unchanged since v1.0 |

**These are not variants of one aircraft; they are successive corrections**, and each
one was made because a check that had never been run was run.

**What v4.0 → v5.0 cost.** Almost nothing: 0.02 days of endurance to buy 144 mm of span
margin instead of −1.5 mm. The two design points are otherwise near-identical
(t/c 0.22, taper 0.25, x_le_frac ≈ 0.4076, tail volume 0.602, the same propeller and
gearing). **That the 12 m gate is nearly free at this MTOW is itself information**: the
optimiser's unconstrained-span answer at the same stability window sits at **14.47 m
and 7.16 d** (`opt_runs/layout_sm8.json`), so the transport limit costs about
**4.5 hours**, not days.

### 9.2 The propeller defect, and why it is a process finding

v3.0 was published in the previous revision of this report with a propeller that could
not hold it in level flight. The mechanism was not carelessness at the design point; it
was that **`scripts/prop_design_sweep.py` and `scripts/prop_refine.py` hardcode the
design file they load and the boom station they check against.** Two scripts that take
no arguments quietly returned answers for a retired aircraft, three design points in a
row, and each time the answer was copied into a design file and quoted in a report.

The fix applied at v4.0 and carried to v5.0 was to solve the propeller at the actual
design point. **The fix not applied is to parameterise the scripts**, which is why §4.5
still records that no committed script reproduces v5.0's propeller.

---

## 10. What changed from v1.0, claim by claim

| v1.0 claim | Status | v3.0 | **v5.0 / measured** | Where |
|---|---|---|---|---|
| Loiter endurance **4.70 d (112.8 h)** | **Reproduces arithmetically, wrong physically** | 6.33 d | **6.97 d as recorded, 6.94 d at the design file's own η_prop.** v1.0 is 112.977 h on its own polar (+0.16%); **3.16 d** once the engine is modelled at its 19% load | `opt_runs/final.json`; §4.2, §7.1 |
| **Static margin +14.7% MAC at CG 42%** | **DOES NOT REPRODUCE** | +5.79% (fails the 8% floor) | **+12.72% full / +13.68% dry — inside the 8–20% gate on all four readings.** v1.0 measures **−44.0% / −82.2%** | `argus7.analysis.balance`; §5.1, §5.4 |
| CG window 38–46% MAC | **Missed on v1.0, met on v5.0** | 39.6% | **41.7% full → 40.8% dry — inside the published window at every fuel state** | §5.3 |
| Fuel **101.5 kg in wing tanks at the AC** | **v1.0's WING CANNOT HOLD IT** | 160.6 into 168.0 (+4.4%) | **172.4 into 190.4 (+10.4%), and it survives mogas density (+5.5%)**. v1.0's capacity is **66.1 kg** on measured geometry | `wing_fuel_capacity_kg`; §12.2 |
| **CG travel <0.5% MAC** (design pack) | **Fails by 76× on v1.0** | −0.08% (achieved) | **+0.95% MAC — close, in the safe direction, and inside a passing stability window rather than below it** | §5.3 |
| **V_h = 0.68** (§2 tail row) | **DOES NOT CLOSE** | 0.4218, closes | **0.6018, closes.** v1.0's S_h 0.31 m² with a 3.2 m arm gives **V_h 0.5765** (17.9% off) | xfail in `tests/test_geometry_closure.py`; §2.1 |
| **0.813 m prop at 2,100 rpm on 17 kW** | **CANNOT ABSORB ITS ENGINE** | inherited from v2.0, **26% short of thrust** | **1.04 m at 2,050 rpm on 10.849 kW, absorbing 101% at climb and making 110% of loiter thrust — solved at this design point** | `tests/test_bemt.py`; §4.1, §4.5 |
| Reduction **2.3:1** | **Impossible** | 3.947:1 (v2.0's, wrong for v3.0) | **3.659:1 — and 2,050 × 3.659 = 7,501 rpm, on the assumed rating** | §4.5 |
| Prop η **0.84 assumed** | Slightly pessimistic | 0.858 claimed, 0.853 real | **0.8529 at the design point.** Note the mission was integrated at 0.858 | §4.5, §7.1 |
| BSFC **270 g/kWh flat** | **Wrong regime** | 339 g/kWh | **339.3 g/kWh** at 30.0% load. v1.0's installation gives **425** | §4.3 |
| **BSFC 250 → +0.5 d** | ❌ **WRONG** | — | **+0.377 d.** +0.5 d would need 244 g/kWh | §7.4 |
| **C_D0 0.016 → +0.36 d** | ✅ correct | — | **+0.358 d** | §7.4 |
| **3,000 m → +0.23 d** | ❌ **WRONG** | — | **+0.198 d** | §7.4 |
| C_D0 = 0.020 "realistic" | Ambiguous, and the ambiguity matters | 0.01588 | **0.01690.** The build-up returns 0.01368 with the measured laminar run; on v1.0 it returned 0.0200 with the wing assumed fully turbulent | xfail in `tests/test_buildup.py`; §3.2 |
| L/D_max 27.1 at C_D0 0.020 | Consistent | 29.15 at loiter | **30.42 max, 30.02 at loiter** | §3.1, §8.1 |
| e = 0.85 | Now derived, not asserted | 0.8482 | **0.8101 from 45 AVL runs plus an explicit viscous term — but read at taper 0.25, outside the sweep's 0.30–0.60 range** | §3.4 |
| MTOW 250 kg | **Superseded, and the band is crossed** | 312.93 (+25%) | **320.00 kg (+28%), at the optimiser's bound.** v1.0 §9's whole regulatory case is built at 250 kg | §12.4 |
| High AR is the route to endurance | **Contradicted** | — | AVL measures span efficiency nearly flat in AR (0.989 at AR 14 → 0.969 at AR 30). AR is not a strong lever; span and MTOW are | §3.4 |
| Wing 32.5 kg | Superseded | 45.39 kg | **40.63 kg** on a 47% larger wing — 7.10 kg/m² against 8.33, and **4.0% below the recommended build's areal density**, which is a warning not a win | §6.1 |
| *(no v1.0 claim)* Range | **New** | — | **17,659 km at 134 km/h**, and **not flyable with the recorded gearing** | §8 |
| *(no v1.0 claim)* Speed envelope | **New** | — | **Stall 104.2 km/h at MTOW; V_max 206.9 km/h on power, ~122 km/h on gearing** | §8.3, §8.4 |
| *(no v1.0 claim)* Structure | **New, and it is a correction** | — | **Tip deflection 14.4% of semi-span at limit (cross-validated); compression caps buckle at 80 MPa against 600 applied.** The mass model is optimistic | §6 |
| *(no v1.0 claim)* MTOW scaling law | **Not determined, and the earlier claim is withdrawn** | — | Three fits of the same quantity give exponents **0.869, 0.998 and 1.452**. Only engine power scales cleanly (MTOW^0.82, 6.1% scatter) because climb pins it | §12.5 |
| Premortem (Annex A) | **Still valid, unchanged** | — | The failure modes, tripwires and decision rule in v1.0 Annex A are about the *programme*, not the design point. The engine-numbers mode (#3) has grown in weight | v1.0 Annex A |

**A correction to the programme's own quotation of the fuel-volume defect.** The
repository has been quoting v1.0 as short by ~62 kg of tank. On honestly-measured
geometry it is short by **35.4 kg** (101.5 required, 66.1 available). Still a hard
fail, but the number the programme was quoting overstated it by 78%. The cause was
two conflated fractions in the capacity model — *fraction of chord* with *fraction of
section area*, and *fraction of span* with *fraction of volume*. A 15–65% chord box
holds **71.6%** of an FX 63-137's section area, not 50%; the inner 80% of a tapered
span holds **90.7–94.0%** of volume, not 80%. Both were wrong in the conservative
direction, which still invalidates an optimum: a binding constraint in the wrong place
distorts every variable that touches it.

---

## 11. Verification

### 11.1 The test suite

**463 passed, 12 xfailed** (`PYTHONPATH=. .venv/bin/pytest tests/`, ~87 s), across 17
test modules covering airfoil coordinates, ISA, geometry closure, CAD
wing/airframe/export/render, drag build-up, NeuralFoil, XFOIL driver, BEMT, engine
deck, mission simulation, optimiser design space, balance, lift-curve anchors, and a
regression-defect file.

Every one of the 12 `xfail`s is **strict** and carries its measured numbers in its
reason text, so it fails loudly if the reason is read and **errors** if someone makes
it pass without rewriting the reason. They are not skipped work; they are the
programme's findings, held in executable form:

| xfail | What it pins |
|---|---|
| `test_v1_reproduces_the_published_static_margin` | +14.7% MAC does not reproduce; −44.0% measured |
| `test_v1_neutral_point_is_aft_of_the_cg` | v1.0 is divergent, full and dry |
| `test_v2_neutral_point_is_aft_of_the_cg` | the retired v2.0 was too, at −8.7% → −23.5% |
| `test_v1_cg_lies_in_the_published_window` | 38–46% MAC window missed by 189/383 mm |
| `test_both_designs_meet_the_programmes_own_static_margin_gate` | the pre-registered 8–20% MAC gate was never evaluated on v1.0 or v2.0 — **v5.0, evaluated against it in §5.4, passes it on every reading** |
| `test_report_claim_of_half_percent_cg_travel` | 76× and 30× over on v1.0/v2.0 |
| `test_v2_mass_budget_closes` | 13.02 kg unallocated in the retired v2.0, traced to an engine-mass credit applied twice |
| `test_v2_static_margin_stays_inside_the_window_across_the_whole_burn` | outside at every fuel fraction |
| `test_report_stated_tail_volume` | V_h 0.5765, not 0.68 |
| `test_total_cd0_against_report_baseline` | build-up 0.0153 vs stated 0.020, −23.6%, outside the ±15% gate |

### 11.2 Mutation testing — does the suite have teeth?

A passing suite proves nothing about a suite. `scripts/mutation_test.py` injects 13
plausible defects — sign flips, dropped terms, loosened tolerances, an exponent
changed, a constant raised — into a scratch copy of the repository and runs the full
suite against each.

**Result (`opt_runs/mutation.json`): 12 of 13 killed.**

Killed, among others: MAC formula 2/3 → 2/4; the twist-rotation sign flip (**the bug
that has appeared twice in this project**); stall margin squared → linear; drag 5% low;
Oswald factor dropped from the polar; ISA lapse rate 1.5% wrong; **spar allowable
raised 33%, which would make every wing lighter for free**; **the NACA-4 shape factor
this project already caught once**; the chord² spanwise weighting dropped from the fuel
centroid; **the downwash term (1 − dε/dα) dropped from the neutral-point tail term**;
the closure tolerance loosened 10⁸×.

**One survivor, and it is a real hole:** a sign flip in the leading-edge → half-chord
sweep conversion inside `lift_curve_slope_per_rad`. Nothing in the suite catches it.
It affects both a_w and a_t, and therefore the neutral point, so it is exactly the
class of defect the balance module exists to prevent. **It should be closed.**

`opt_runs/mutation.log` records an **earlier, superseded** run at 4/8. It is stale and
should not be read as the current score; `opt_runs/mutation.json` is authoritative.

### 11.3 The gauntlet: pre-registered gates and an adversarial audit

Before any challenger design was inspected, eight conjunctive adoption gates were
written down (`docs/decisions/2026-08-20-gauntlet-preregistration.md`), together with
five model limitations declared in advance so they could not be discovered
conveniently later. Gates chosen after seeing the result are not gates.

An independent cross-check auditor then re-derived every headline number from the
design variables with its own code — its own ISA, its own adaptive-quadrature Breguet
integration, its own AVL decks, its own NeuralFoil runs, its own shoelace integration
of the pinned airfoil coordinates — without calling `argus7.mission.sim` at all.

**Verdict on the then-challenger: DO NOT ADOPT.** G2 (fuel ≤ tank) failed, G6
(regulatory band declared) failed, G7 (buildability / a real engine) failed. The gates
are conjunctive.

What the audit found, and could not break, is as informative as what it broke:

| Attacked | Outcome |
|---|---|
| Endurance arithmetic | **Survived** — reproduced to six significant figures |
| Wing-mass AR^1.5 scaling | **Survived** — exponent verified analytically, ratio agreed with Raymer's independent regression to 1.0% |
| `k_area = 0.6062` airfoil shape factor | **Survived** — measured 0.60620 by independent shoelace integration |
| The 45-run AVL Oswald surface | **Survived** — decks rebuilt from scratch reproduced the table to four decimals |
| Stall margin | **Survived** — and NeuralFoil showed the flat C_Lmax 1.60 is *conservative* for a thick section, not generous, at every Reynolds number this aircraft sees |
| Wing fuel-volume constraint | **Broken** — mis-specified by ~1.6×, so the design was pressed against a wall in the wrong place |
| Fixed 28 kg non-wing airframe mass | **Broken** — +8.08 kg undercharged on that design, and v5.0's 6.25 m booms make it worse |
| `CD0_BASELINE` comment | **Broken** — claimed 0.01529 "at the v1 point"; the function returns 0.016947 there |
| Flat BSFC at 20% load | **Broken** — the repository's own engine module already refuted it |
| **Cap laminate b/t ≥ 200 not entitled to a 600 MPa allowable** | **Broken then, and it applies again now** — v5.0's cap is at b/t 115 against the calibration point's 50, and §6.3 confirms it independently |

That audit is the direct ancestor of §4, §5 and now §6 of this report. It is also why
this report states model limits beside numbers rather than in a footnote.

**The v5.0 gate results are in §0 and §12.4a.** Eight of nine pass. G7 fails on the
engine, as it has for every design point this programme has produced, and Annex A's
BSFC tripwire trips on the modelled value. *"Gates chosen after seeing the result are
not gates"* cuts both ways, and v3.0's 5–15% stability window was that same failure
wearing the other face; v5.0's search window carries a **+4.7% MAC bias** whose
justification is documented in code (§5.5) and whose result is verified against the
authoritative module rather than asserted.

### 11.4 Independent cross-checks that agree

| Quantity | Method A | Method B | Agreement |
|---|---|---|---|
| v5.0 loiter BSFC | optimiser part-load fit, 339.3 g/kWh | `argus7.prop.engine` Willans deck, 350.1 g/kWh | 3.2% |
| Step integration | 120-step midpoint | closed-form Breguet | <0.001% |
| v1.0 endurance | this repository, 112.977 h | independent auditor, 112.977 h | 6 sig figs |
| Neutral point (tail term) | analytic relation | AVL with real inverted-V dihedral | 0.8% MAC (on v1.0/v2.0) |
| Wing mass ratio between design points | this AR^1.5 model | Raymer GA regression | 1.0% |
| Wing transition location | XFOIL 6.99, Ncrit 9 | NeuralFoil xxlarge | 4–5 points of chord |
| **Wing tip deflection at limit** | **M/EI double integration, 14.43%** | **`research/materials_pack.md`, 14.2%** | **0.2 points** |
| **Cap buckling adequacy** | **explicit σ_cr, −86.6% margin** | **gauntlet audit's b/t heuristic, 115 vs a 50 calibration point** | **same sign, independently** |
| Mass-to-endurance exchange rate | measured here, 1.51 h/kg | materials pack, 1.5 h/kg | 1% |
| Fuselage loft volume | `balance.fuselage_volume_m3`, 0.4022 m³ | configuration pack, 0.4105 m³ | same pod, 2% |
| Recorded optimiser endurance | `opt_runs/layout_final.json`, 167.3126 h | re-evaluated here from the recorded design vector, 167.3253 h | 0.008% |

### 11.5 What the verification does NOT cover — and it is still a real gap

**No test in this repository references `design/argus7_v3.yaml`, `argus7_v4.yaml` or
`argus7_v5.yaml`.** Every test parameterisation covers v1.0 and v2.0 only: 40 references
to v1, 4 to v2, **zero to v3, v4 or v5**. **The design point this report publishes has
zero regression coverage.** Every v5.0 number in this document was computed
interactively against the committed modules, which is reproducible but is not guarded.
This gap has been open across three design points and has grown, not shrunk.

**Closed since the previous revision, and worth recording:**

- **v5.0 CAD exists.** `model_final/argus7_v5.scad`, `model_final/argus7.step`,
  `model_final/argus7.stl` and the four renders in `figures/final/` depict this design
  point. The previous revision recorded "no three-view in this repository depicts the
  aircraft described here"; that is no longer true.
- **The producing run is recoverable.** `opt_runs/layout_final.json` contains the v5.0
  design vector, and `scripts/run_optimisation_layout.py` as committed carries the
  bounds that produced it (span target 11.85 m, MTOW ≤ 320 kg, SM window 8–20% + 4.7%
  bias). The v3.0 equivalent was not recoverable.

**Still open, and specific:**

- **`opt_runs/layout_final.json` records `feasible: false` for the v5.0 point**, with
  `violation = 4.87e−4`. The entire violation is span: **11.8558 m against the script's
  own internal target of 11.85 m, 5.8 mm over.** The pre-registered gate is 12.0 m,
  which v5.0 clears by 144 mm. **The design point is feasible against the gate and
  infeasible against a tighter number the script chose for itself**, and anyone reading
  that JSON without this paragraph will draw the wrong conclusion.
- **`scripts/build_model.py` defaults to `design/argus7_v1.yaml`.** The v5.0 CAD was
  generated by passing a path; README's "Reproducing" block as written reproduces
  v1.0's model.
- **`figures/current/drag_budget.png` is built from v1.0**, not v5.0, while sitting in
  a directory README describes as current.
- **No committed script produces v5.0's propeller** (§4.5a).
- **The CalculiX beam model is not validated** and its outputs appear nowhere in this
  report (§6.0).

---

## 12. Open questions, and what would settle them

Ordered by how much they could move a headline number.

### 12.1 What is the engine's actual BSFC? — worth ±1.7 days, and it is the gate that fails

The single largest uncertainty in the report, and it is not an analysis question.
Everything rests on a **250 g/kWh full-load** figure that is the report's aspirational
dyno target, taken by the optimiser at exactly its lower bound. The two shortlist
engines with published, verified BSFC are both **330 g/kWh**, at which this aircraft
flies **5.26 d instead of 6.97**. The engine deck's own reference-load assumption
(0.75) can move the modelled loiter BSFC from 293 to 332 g/kWh on its own, and the
module carries an unreconciled 36% disagreement between two values of the same
friction fraction.

**This is also the gate that fails.** G7 requires an engine matched to a real unit from
report §6's shortlist; a target is not a unit, and the gauntlet audit already ruled so.

**What settles it:** a mapped dyno run at the 2–5 kW band with altitude simulation,
plus a 100 h continuous oil-system test. This is exactly v1.0 Annex A's Phase 0, and it
is exactly its tripwire #3 (*walk away if >300 g/kWh at the loiter point*). Note that
the modelled value, 339.3 g/kWh, already exceeds that tripwire. **Second, and cheap:**
resolve φ = 0.1325 vs φ = 0.18 in `argus7/prop/engine.py`, which the file itself
declines to do; settle the reference load fraction; and extend the deck to the
8,562 rpm crank speed the first third of the mission actually runs at (§4.5b).

### 12.2 Does the wing actually hold 190 kg? — probably, and this is the item that improved most

The tank capacity is `k_area · (t/c) · S · MAC · chord_frac · span_frac · net_frac`
with `k_area = 0.6062` **measured** by shoelace integration of the pinned coordinates,
`chord_frac = 0.716` **measured** as the section-area fraction of a 15–65% chord box,
and `span_frac = 0.940` **measured** as the volume fraction inboard of 80% semi-span.
Two of the three guessed fractions in the original model have been replaced by
measurements. `net_frac = 0.88` has not.

**The margin is +18.02 kg on 190.44 kg, i.e. 10.4%** — against v3.0's 4.4%, which was
thinner than the model's own uncertainty. And **the fuel-density problem that
threatened v3.0 has gone away**:

| Fuel | Density | Volume required | Volume available | Margin |
|---|---|---|---|---|
| Model default | 0.780 kg/L | 221.1 L | 244.2 L | **+10.4%** |
| Jet-A1 typical | 0.804 kg/L | 214.5 L | 244.2 L | +13.8% |
| **Mogas E10** | **0.745 kg/L** | **231.4 L** | 244.2 L | **+5.5%** |

`research/configuration_hypotheses.md` found that v1.0's implied fuel density
(101.5 kg in 120 L = 0.8458 kg/L) **does not exist** — no available fuel is that dense.
On v3.0, mogas made the margin vanish. **On v5.0 the tank closes on every candidate
fuel**, which removes one of the two halves of the premortem's named fatal flaw. The
fuel still has not been chosen, and the choice now affects BSFC and the engine
shortlist rather than the tank.

**What still settles the capacity question:** *measure the tank, do not model it.* The
repository already builds this geometry — `argus7/cad/model.py`, `to_openscad.py`,
OpenSCAD installed, and `model_final/argus7_v5.scad` already exists. Loft the wing,
place real front and rear spar webs at their chord stations, subtract skin laminate,
spar-cap volume, rib flanges and the flaperon cutout, and integrate the remaining
cavity. **One measured number replaces three fractions.** Note that §6.3's fix for the
buckling problem — closer ribs — takes volume out of the tank, so these two items are
coupled.

### 12.3 How much heavier is a wing that does not buckle? — sign known, magnitude not

**New, and it is the most important open item that is not the engine.** §6.3 establishes
that the compression cap buckles at 80 MPa against 600 MPa applied, and that v5.0's cap
laminate is at b/t 115 against the calibration point's 50. **The mass model sizes for
material strength and the structure fails by buckling**, so wing mass is understated by
an amount nobody has computed.

At **1.51 h/kg**, this is directly an endurance correction. For scale: if a
buckling-resistant cap and the rib pitch to support it cost 5 kg, that is **−7.6 h**;
if they cost 10 kg, **−15.1 h**. Both are plausible and neither is computed. Nothing in
this report has been adjusted for it, because guessing the magnitude would be worse
than declaring it.

**What settles it:** size the cap properly — choose a width-to-thickness ratio and a
rib pitch that give a positive buckling margin at ultimate, compute the resulting mass,
and feed it back through the optimiser rather than adjusting the answer afterwards.
This is a design task of perhaps a day, and it is the only item on this list that could
change the design point rather than just its error bars.

### 12.4 The regulatory band has been crossed, and this is the declaration

v1.0 §9's entire regulatory case — EASA Specific category, SORA 2.5, likely SAIL
III–IV, Design Verification Report scope, MoC Light-UAS 2511/2512, ground risk from a
3–4.5 kJ touchdown — is built at **250 kg**. **v5.0 is 320.00 kg, +28%, and it sits at
the optimiser's own upper bound.** Touchdown energy at MTOW rises from 4.50 to
5.76 kJ, and the canopy that gives 6 m/s grows from 69.5 to 89.0 m².

Gate G6 of the pre-registration says results must be *tagged with their MTOW band, not
silently crossing*. The retired v2.0 crossed it silently at 278 kg. **This report is
the declaration.** Nothing in this repository evaluates what the new band costs in
SORA terms.

**What settles it:** a SORA pre-application, which v1.0 Annex A's rebuilt plan already
puts in Phase 0 month 1 precisely because early bad news is cheap.

### 12.4a Does v5.0 pass its own pre-registered gates? — eight of nine

The gate table is in §0 and is not repeated. The summary:

**G1–G6 and G8 pass, and the spec's 8–20% MAC stability window passes on all four
readings at both fuel states — the first design point in this programme of which that
is true. G7 fails, on the engine, exactly as it failed for v3.0 and for the original
challenger. Annex A's BSFC tripwire trips on the modelled value, 339.3 g/kWh against a
300 g/kWh walk-away.**

The pre-registration's decision rule is conjunctive — *"any of G2–G8 fails → do not
adopt"*. **On its own rule, v5.0 is not adoptable, and the reason is an engine
procurement fact rather than anything about the aircraft.** `README.md`'s statement
that v5.0 passes 9/9 is not supported by any record in `docs/decisions/`, and this
report does not repeat it.

**What settles it:** put an engine on a dyno. There is nothing else. The airframe gates
are all met.

### 12.5 The MTOW scaling law is not determined, and the earlier claim is withdrawn

Requested as *"document the scaling law thoroughly"*; the thorough answer is that
**there is no reliable scaling law in this data.**
(`docs/decisions/2026-08-21-scaling-not-determined.md`.)

Three power-law fits, from three datasets, of the same quantity:

| Dataset | E[h] = a·MTOW^b | R² | Max residual |
|---|---|---|---|
| First sweep, unrefined, 196–595 kg | b = **0.869** | 0.956 | 12.3% |
| Refined, 178–350 kg | b = **1.452** | 0.975 | 10.1% |
| Combined, 178–595 kg | b = **0.998** | 0.897 | 23.4% |

Each looks respectable alone. **An exponent that moves from 0.87 to 1.45 depending on
the subset is a curve fit, not a law**, and this report does not publish one.

**The reason is itself the finding.** Only one design quantity scales cleanly:

| Quantity | Exponent | Scatter |
|---|---|---|
| **Engine power** | MTOW^0.82 | **6.1%** |
| Span | MTOW^0.90 | 20.0% |
| Wing area | MTOW^1.19 | 24.6% |
| Aspect ratio | MTOW^0.62 | **30.5%** |

Engine power is tight because **the climb constraint pins it** — it is the one variable
with an active constraint at every design point (+0.09% margin on v5.0, §4.2).
Everything else scatters because **the objective is genuinely flat in those
directions**: the optimiser returned AR 17.0 at 178 kg and AR 29.7 at 200 kg with
sensible endurance both times. It is not failing to converge; there is a broad ridge
and it lands wherever the sampler looked. The marginal exchange rate shows the same
thing and is not monotone: 1.29 → 0.36 → 0.68 → 0.81 → 0.47 h/kg across consecutive
refined points. **An earlier report of "a four-fold decline in marginal returns" was
reading a trend into noise, and is withdrawn.**

**What IS established:** endurance increases monotonically with MTOW, roughly 2.8 days
at 180 kg to 9.9 days at 600 kg; engine power scales as MTOW^0.82; aspect ratio is not
a strong lever; and stability is nearly free once the layout is in the search.

**What settling it would take:** a **Pareto front** rather than a single optimum per
weight, which would show the ridge directly instead of sampling one arbitrary point on
it.

### 12.6 Is the propulsion set right for the *ferry* mission? — it is not

§8.4. The recorded fixed-pitch 1.04 m disc on a fixed 3.659:1 reduction is
gearing-limited to about **122 km/h at MTOW**, against a power-limited 207 km/h and a
best-range speed of 134 km/h. **The loiter mission is unaffected. The range figure is
not achievable as specified.**

**What settles it:** sweep the reduction ratio jointly with diameter and pitch against
*both* operating points; or accept a two-propeller fit; or re-price variable pitch,
whose dismissal in §4.5 was argued on the loiter mission alone. **And parameterise
`scripts/prop_design_sweep.py` and `scripts/prop_refine.py`**, which still load
`design/argus7_v2.yaml` and hardcode v1.0's boom station, and which are the root cause
of §9.2.

### 12.7 The model limits that bound every number in this report

Stated once, in one place, because they bound everything above.

1. **Pure loiter only** for endurance; **straight-line still air** for range. No
   transit, no climb, no reserve, no wind, no diversion in either.
2. **The fuselage is fixed** at 3.4 m × 0.48 m for every design point, and
3. **non-wing airframe mass is fixed at 28 kg** regardless of wing size, tail size or
   **boom length** — worth about **−9.8 h** on this design point when charged honestly,
   and v5.0's 6.25 m booms make the estimate itself stale in the pessimistic direction.
4. **The wing mass model is calibrated on a single point**, 76% of its spar-cap term at
   that point is the fitted constant, **and it sizes for a failure mode that is not the
   governing one** (§6.3).
5. **The MTOW scaling exponent is not determined** (§12.5).
6. **The optimiser searched with a batched balance model that reads ~4.7% MAC high**
   against the authoritative scalar module, and the search window was biased by exactly
   that amount to compensate. Search with one, verify with the other — which is what
   was done (§5.5).
7. **C_Lmax is a flat 1.60 for every design.** NeuralFoil measures the 22% section at
   2.10–2.16 across every Reynolds number this wing sees, so 1.60 is conservative in
   2D — but **3D C_Lmax, tip-stall progression on a taper-0.25 wing, and departure
   behaviour are not modelled anywhere in this stack.**
8. **The AVL Oswald surface is not panel-converged**, its viscous term is
   design-independent and partly double-books against the thickness penalty, **and
   v5.0's taper 0.25 is outside the 0.30–0.60 range it was fitted over.**
9. **The thickness drag penalty is a linear extrapolation** from data ending at
   t/c 0.200, read at **t/c 0.220** (§3.5).
10. **XFOIL transition was measured on the 13.7% section at v1.0's conditions**, at an
    assumed Ncrit of 9, and has not been re-measured for the 22% section v5.0 flies at
    less than half v1.0's tip Reynolds number.
11. **Structures are analytic and first-order.** Deflection is cross-validated;
    buckling has a known sign and an uncertain magnitude; divergence and flutter are
    first-order estimates with an assumed torsional mass. **The finite-element model is
    not validated and no number in this report comes from it.**
12. **Nothing has been flight-tested. There is no CFD, no wind tunnel, no structural
    test article, no dynamic stability analysis, no control-power or trim-authority
    check, and no coupled aeroelastic analysis.**

### 12.8 The cheap items that should be done anyway

Each of these is free or near-free, and each is already established by work in this
repository:

- **Correct README's 9/9 gate claim to 8/9**, or record the ruling that changes G7.
  A public repository stating that a design passes a gate the repository's own audit
  says it fails is the one defect on this list that costs nothing to fix and is
  visible from outside.
- **Close the surviving mutant** — the LE→half-chord sweep sign flip in
  `lift_curve_slope_per_rad` has no test.
- **Add v5.0 to the test parameterisations.** The design point this report publishes is
  unguarded, and so were the two before it.
- **Parameterise `prop_design_sweep.py` and `prop_refine.py`** to take a design path
  and read the boom station from `derive_booms`. This is the root cause of the defect
  in §9.2 and it is a ten-line change.
- **Validate the CalculiX beam model against a uniform cantilever** before trusting any
  tapered result, and define the section with `SECTION=GENERAL` (§6.0).
- **Re-measure the thickness drag penalty at t/c 0.22** — a NeuralFoil run of seconds
  that removes an extrapolation from a variable sitting on its bound.
- **Ø50 × 150 mm spigot instead of two M6 screws** at the tail panel root: 0 kg, 0
  drag, bearing margin ×174.
- **Re-run the boom stiffness case for the 6.25 m boom.** Every number in
  `research/boom_construction_pack.md` was computed for a 3.646 m one, and boom
  stiffness requirements scale with the cube of length.
- **Reduce the tail panel's polar inertia**: 0 kg, 0 drag, ×1.41 on the first torsional
  frequency.
- **Put coverage in the objective function**, or at minimum report it alongside
  endurance in every optimiser output. The altitude variable sat on its lower bound
  because nothing in the objective knew that 44% of the coverage area was being traded
  for 0.28 days (§7.4).

---

## Appendix A — Provenance of every headline number

| Number | File | How to reproduce |
|---|---|---|
| Geometry, masses, aero coefficients | `design/argus7_v5.yaml` | `argus7.design.schema.load_design`; every field carries a `derived` / `assumption` / `report-§N` provenance tag, and a test asserts none is untagged |
| Span, chords, MAC, V_h, boom and tail stations | `argus7/design/geometry.py` | closure enforced to 1e−9 |
| 167.313 h endurance | `opt_runs/layout_final.json` (`refined`) | `argus7.mission.simulate_loiter` on the recorded variables, η_prop **0.858**, 120 steps. At the design file's own η 0.8529 it is **166.562 h** |
| C_D0 0.016904, e 0.81012 | `argus7/opt/coupled.py` | `cd0_from_geometry(S, t/c)`, `oswald_from_planform(AR, λ)` |
| Component C_D0 build-up, 0.01368 | `argus7/aero/buildup.py` | `parasite_buildup(design).table()` |
| AVL Oswald surface (45 runs) | `opt_runs/avl_oswald.json`, `e_fit_coef.npy` | `scripts/avl_oswald_sweep.py`, `vendor/bin/avl` |
| XFOIL transition 0.5023 / 0.6051 | `research/riblets_pack.md` §3 | XFOIL 6.99, Ncrit 9, 300 panels, fixed-C_L 1.21 — **on the 13.7% section** |
| C_Lmax 2.10–2.16 for the 22% section | `argus7/aero/neural.py` | `polar(coords_scaled_to_22pct, alpha, Re)`; the two lowest-Re rows carry NeuralFoil's own low-confidence flag |
| CG, NP, static margin, CG travel | `argus7/analysis/balance.py` | `mass_table`, `cg_travel_table`, `avl_neutral_point` |
| Tank capacity 190.44 kg | `argus7/opt/design_space.py` | `wing_fuel_capacity_kg(S, AR, λ, t/c)` |
| Wing mass 40.63 kg, k_cal 4.2257 | `argus7/opt/design_space.py` | `calibrate()`, `wing_mass_kg(...)` |
| Part-load BSFC 339.3 / 350.1 g/kWh | `argus7/opt/coupled.py`, `argus7/prop/engine.py` | `bsfc_at_load`, `Engine.from_design(d).bsfc_g_per_kwh(...)` |
| Propeller 1.04 m / 2 / 2050 / 0.95 / η 0.8529 | `design/argus7_v5.yaml` | `argus7.prop.bemt.run_bemt(constant_pitch_blade(1.04, 0.988, blades=2), rpm, V, rho)` at each fuel state. **No committed script produces it** — §4.5a |
| Climb power 10.839 kW | `argus7/opt/coupled.py` | `climb_power_required_w(...)` |
| **Range 17,659 km at 134 km/h; payload–range** | `opt_runs/range.json` | `scripts/range_analysis.py` — note its hardcoded `BSFC_FULL = 0.2506` and its fixed η_prop, §8.5 |
| **Speed envelope: stall 104.2 km/h, V_max 206.9 km/h on power** | this report | drag polar plus rated shaft power at 4,000 m; the gearing-limited V_max of ~122 km/h from `argus7.prop.bemt`, §8.4 |
| **Tip deflection 14.43% at limit; buckling σ_cr 80.2 MPa** | `fea_runs/structural.json`, `scripts/structural_analysis.py` | M/EI double integration over `argus7.struct.wing_beam.stations`. **The CalculiX outputs in the same file are not used** — §6.0 |
| **Divergence 1,030 km/h, flutter 493 km/h, boom torsion 14.5 Hz** | `fea_runs/structural.json` | analytic, first-order; `docs/decisions/2026-08-21-structural-analysis.md` |
| Sensitivity anchors +0.358 / +0.377 / +0.198 d | `docs/decisions/2026-08-20-gauntlet-audit.md` §1 | re-derived on the v1.0 published polar at 120 steps; both derivations agree |
| Static-margin gate 8–20% MAC | `docs/superpowers/specs/2026-08-20-argus7-cad-sim-optimisation-design.md` line 109 | read directly; line 178 makes it conjunctive |
| Mutation score 12/13 | `opt_runs/mutation.json` | `scripts/mutation_test.py` (**not** `mutation.log`, which is stale) |
| MTOW scaling non-result | `opt_runs/mtow_scaling2.json`, `opt_runs/scaling_law.json` | `scripts/mtow_scaling2.py`; `docs/decisions/2026-08-21-scaling-not-determined.md` |
| Materials, boom, empennage and configuration findings | `research/*.md` | each carries its own source tags and reproducibility appendix — **all computed for the v1.0 configuration** |

## Appendix B — Documents this report supersedes, and documents it does not

**Superseded:**

- `docs/argus7_design_report.md` §§0–8 and §10 — the design point, its performance,
  its stability line, its mass budget, its propulsion set and its sensitivity table.
- **Every v3.0 number in the previous revision of this report.** v3.0 fails the
  programme's own stability gate and, as published, carried a propeller that could not
  hold it in level flight.
- `docs/decisions/2026-08-21-propeller-selection.md` — selects a 1.00 m propeller for a
  retired aircraft on a boom-clearance figure computed from v1.0's span (§4.5c).
- **`research/boom_construction_pack.md`'s 22.7 Hz first-torsion figure**, superseded
  by 14.5 Hz for v5.0's 6.25 m boom (`docs/decisions/2026-08-21-structural-analysis.md`).

**Not superseded, and still current:**

- `docs/argus7_design_report.md` **Annex A (premortem)** — a programme risk analysis,
  not a design point. Its failure modes, tripwires, decision rule and adversary
  analysis apply unchanged, and mode #3 ("the engine never delivered the numbers the
  design assumes") has grown in weight, not shrunk.
- `docs/argus7_v3_premortem.md` — written against v3.0, but its seven failure modes are
  about the *programme*. Two have moved: **mode #7 ("the wing that was never
  analysed") is no longer undetected** — §6 detects it, and confirms rather than clears
  it — and the **fuel-density half of its named fatal flaw has been resolved** by
  v5.0's larger tank (§12.2). The engine half has not. Its tripwires stand, and the
  spar-static-test tripwire is now the one with a number attached to it.
- `docs/argus7_design_report.md` §9 (regulatory) — **directionally** current, but built
  at 250 kg; see §12.4.
- All nine records in `docs/decisions/`, with the exception noted above.
- All five research packs in `research/`, **with the caveat that every structural,
  boom and empennage number in them was computed for the v1.0 configuration, and that
  v5.0's boom is 71% longer than the one they were sized for.**
