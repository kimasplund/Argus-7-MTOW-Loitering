# ARGUS-7 — Persistent Disaster-Zone Communications & Survey UAV
## Engineering Design Report (v2.0)

**Date:** 2026-08-21 · **Design point:** `design/argus7_v3.yaml` (variant tag `v3.0-layout`)
**Status:** Paper design. Nothing here has been built, flown, wind-tunnel tested, meshed for CFD, or checked by FEA.

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
> §8 gives the arithmetic and the file for each.

---

## 0. Executive summary

ARGUS-7 v3.0 is a 313 kg MTOW, single-engine, high-aspect-ratio, twin-boom pusher UAV
sized to loiter over a disaster zone carrying a 50 kg / 500 W multi-role
communications and survey bay, recovered by parachute. It is the output of an
11-variable optimiser that owns the **layout** as well as the wing, and that treats
longitudinal static margin, wing fuel volume, climb power and span as hard
constraints rather than as things checked afterwards.

| Headline | Value | Where it comes from | The caveat, stated next to it |
|---|---|---|---|
| **Loiter endurance** | **6.33 d (151.95 h)** | `opt_runs/layout.log`; reproduced here from the recorded design variables to 151.9510 h | **Pure loiter only** — no transit, climb, or reserve. BSFC frozen at the mid-burn load; evaluating it pointwise across the burn gives **146.36 h (6.10 d)**, see §7.3 |
| Loiter altitude | 4,359 m | optimiser variable, bounded [4000, 4500] in the run that produced this point | Inside the sponsor-locked 3,000–4,500 m band, unlike the retired v2.0 which sat at 2,500 m |
| MTOW | 312.93 kg | `design/argus7_v3.yaml` | **+25% on v1.0's 250 kg.** This crosses the mass band v1.0 §9's entire regulatory case was built at. Declared here, see §10.4 |
| Wing | 5.9191 m², AR 21.44, span 11.27 m, t/c 0.191 | design file; closure verified by `argus7.design.geometry` | Span is inside the 12 m transport gate with 6.1% margin |
| Static margin | **+5.79% MAC full, +5.71% dry**, travel −0.08% MAC | `argus7.analysis.balance` on the design file | This is the **authoritative scalar module's** number. The batched model the optimiser searched with reported +10.5%/+7.5%; the two agree to ~5% MAC, not exactly. The design sits at the **bottom edge** of its own 5–15% gate, not mid-band. Reading band across methods: **+1.3% to +11.4% MAC**, §5.4 |
| Fuel | 160.60 kg into a 168.01 kg wing tank | `argus7.opt.design_space.wing_fuel_capacity_kg` | **+7.41 kg (4.4%) margin.** The capacity model is three measured fractions, not a lofted cavity — §10.2 |
| Mass closure | −0.01 kg residual on 312.93 kg | `argus7.analysis.balance.mass_budget_residual_kg` | Exact to the design file's own precision |
| Engine | 10.845 kW rated, 30.6% loiter load, **effective BSFC 339 g/kWh** | optimiser; cross-checked against `argus7.prop.engine`, which gives 347 g/kWh at the same point (2% apart) | The 339 rests on a **full-load BSFC of 252 g/kWh, which is the report's aspirational dyno target, not a measured unit.** Both shortlist engines with *verified* BSFC are 330 g/kWh, at which this aircraft flies **4.83 d**, §4.4 |
| Propeller | 1.04 m, 2 blades, 1,900 rpm, p/D 0.95, η 0.858, 3.947:1 reduction | `opt_runs/prop_final.json` | **Selected against the retired v2.0 design point, not this one.** Re-run here against v3.0's thrust it needs ~2,040 rpm mid-burn, not 1,900, at η 0.853 — §4.5. This is an open item |
| C_D0 | 0.01588 | `argus7.opt.coupled.cd0_from_geometry` | Contains **no** payload turret, cooling drag, or base drag. A modest +0.0035 allowance costs **−0.39 d** — §3.2 |

### The honest bottom line

The v3.0 design point is the first in this programme that **balances, holds its fuel,
and closes its mass budget simultaneously**. That is the substance of the change; the
endurance number is downstream of it.

But 6.33 days is the *optimistic* end of a defensible band, and the report says so
here rather than in a footnote. Stacking the corrections this repository can already
justify:

| Applied cumulatively to the recorded design point | Endurance |
|---|---|
| As recorded (`opt_runs/layout.log`) | **151.95 h — 6.33 d** |
| + BSFC evaluated pointwise along the burn instead of frozen at mid-load | 146.35 h — 6.10 d |
| + propeller efficiency at the rpm v3.0 actually needs (0.853, not 0.858) | 145.98 h — 6.08 d |
| + a +0.0035 C_D0 allowance for turret, cooling and base drag | 140.31 h — **5.85 d** |
| + a **verified** engine's 330 g/kWh full-load BSFC instead of the 252 target | 107.12 h — **4.46 d** |

**The programme's 5–7 day ambition is met on the modelled engine and missed on the
only engines whose fuel consumption anybody has measured.** That, not aerodynamics,
is where this design lives or dies, and it is the same finding the gauntlet audit
reached about the previous challenger.

---

## 1. Mission and requirements

Unchanged from v1.0 §1. Restated so this document is self-contained.

- **Payload:** 50 kg multi-role bay — LTE/5G relay (eNB plus sector antennas), EO/IR
  gimbal (TrakkaCam TC-300 class), mesh MANET feeder, LEO/Iridium backhaul, mission
  computer and power conditioning. **50 kg / 500 W continuous, ~620 W peak**, all
  COTS-derived. Tagged `report-§1` and `report-§3` in the design file's provenance
  block.
- **Modes:** (A) *Local* — launch near the zone, pure loiter. (B) *Deploy* — transit
  to the zone, loiter, recover locally. **Only mode A is modelled anywhere in this
  repository.** Every endurance figure in this report is mode A.
- **Recovery:** parachute plus airbag, reusable airframe, no single-use elements.
- **Environment:** loiter band **3,000–4,500 m AGL**, −5 to −15 °C at altitude.

The loiter band is a locked requirement, and it is treated as one here. The retired
v2.0 optimiser went 500 m *below* the floor to buy 8 hours, giving up 61% of the
coverage area, because nothing in its objective knew coverage existed. The run that
produced v3.0 was bounded at [4,000 m, 4,500 m] and returned 4,359 m — inside the
band by construction rather than by luck.

**Coverage at the v3.0 loiter altitude,** on v1.0 §8's own suburban elevation-angle
model (θ* = 20.3°): service radius **11.78 km**, area **436 km²** — 19% more area
than v1.0's 4,000 m design point (10.81 km / 367 km²). The elevation model itself is
unchanged and unvalidated; v1.0 §8 already flags that no published measurement exists
in this altitude band.

---

## 2. The v3.0 configuration

### 2.1 Geometry

Every row below is either read directly from `design/argus7_v3.yaml` or derived from
it by `argus7.design.geometry`, which enforces closure to 1e−9. Nothing is typed in.

| Parameter | Value | Provenance |
|---|---|---|
| MTOW | 312.93 kg | derived (optimiser) |
| Wing area S | 5.9191 m² | derived |
| Aspect ratio AR | 21.442 | derived |
| Span b | 11.266 m | closure identity √(AR·S) |
| Taper ratio λ | 0.697 | derived |
| Root / tip chord | 0.6192 / 0.4316 m | closure |
| MAC | 0.5310 m | closure |
| MAC leading edge | x = 1.2485 m | derived |
| Wing loading | 52.87 kg/m² | derived |
| Airfoil | FX 63-137, scaled to **t/c 0.1909** | section `report-§2`; thickness derived |
| Twist (tip) / dihedral / LE sweep / incidence | −3° / +3° / 1° / 2° | **all four tagged `assumption`** — no source in report or research packs |
| **Wing station `x_le_frac`** | **0.3536** (root LE at x = 1.2022 m) | **derived — this is the single change that makes the aircraft balance** |
| Wing vertical offset | +8 mm | assumption; makes this a mid-wing aircraft |
| Fuselage | 3.4 m × 0.48 m, 6-station loft, volume 0.4022 m³ | **assumption, unchanged from v1.0 and fixed for every design point** |
| Booms | Ø90 mm, y = ±0.7548 m, derived length 4.064 m | diameter and station `assumption`; length derived |
| Tail | inverted V, −42° dihedral, panel AR 3.0, taper 0.55, NACA 0010 | type `report-§2`; angles `assumption` |
| Tail effective horizontal area S_h | 0.3698 m² | derived |
| Tail arm | 3.5847 m = **1.0543 × fuselage length** | derived |
| **Tail volume coefficient V_h** | **0.4218** | derived, and it **closes** — see §8 |
| Engine | 10.845 kW rated, 250 cc nominal displacement | power derived; displacement inherited `report-§2` |
| Reduction | 3.947 : 1 | derived |
| Propeller | 1.04 m, 2 blades, 1,900 rpm, p/D 0.95 | derived (BEMT sweep) |
| Loiter altitude | 4,358.8 m | derived |

**A note on the tail arm.** At 1.054 × fuselage length the tail sits 0.68 m aft of the
fuselage tailcone, carried on booms 4.064 m long. That is a longer arm than v1.0's
(0.941 L) and it is what lets V_h fall to 0.4218 while still delivering the tail
contribution the neutral point needs — 20.4% MAC of it (§5.2). It is also a longer
cantilever for the boom stiffness case in `research/boom_construction_pack.md`, which
was sized on v1.0's 3.646 m boom. **The booms have not been re-sized for v3.0.**

### 2.2 Mass table

Produced by `argus7.analysis.balance.mass_table` on the design file. The `x` column is
the fuselage station of each group's centre of gravity; `%MAC` is measured from the
MAC leading edge, which is the convention used throughout this report.

| Item | Mass (kg) | x (m) | % MAC | Moment (kg·m) |
|---|---|---|---|---|
| Wing | 45.39 | 1.4609 | 40.0 | 66.30 |
| Fuselage (incl. misc) | 16.58 | 1.6264 | 71.2 | 26.97 |
| Booms | 7.18 | 3.0841 | 345.7 | 22.13 |
| Tail | 4.24 | 5.0174 | 709.8 | 21.29 |
| Powertrain | 15.95 | 3.0500 | 339.3 | 48.65 |
| Avionics | 6.00 | 1.4500 | 38.0 | 8.70 |
| Recovery | 7.00 | 0.9500 | −56.2 | 6.65 |
| Payload | 50.00 | 0.4320 | −153.8 | 21.60 |
| **Fuel** | **160.60** | **1.4584** | **39.5** | **234.22** |
| **TOTAL** | **312.94** | **1.4588** | **39.6** | **456.51** |

Design-file MTOW 312.93 kg; **unallocated residual −0.01 kg.**

Design-file grouping, for comparison with v1.0 §3:

| Group | v1.0 | v3.0 |
|---|---|---|
| Airframe structure | 60.5 | **73.39** (wing 45.39 + non-wing 28.00) |
| Powertrain | 25.0 | **15.95** (a 10.8 kW engine, not a 17 kW one) |
| Avionics | 6.0 | 6.00 |
| Recovery | 7.0 | 7.00 |
| Payload | 50.0 | 50.00 |
| **Empty (no payload, no fuel)** | **98.5** | **102.34** |
| Fuel | 101.5 (40.6% of MTOW) | **160.60 (51.3% of MTOW)** |
| MTOW | 250.0 | **312.93** |

**Two assumptions in that table carry the whole thing, and both are declared:**

1. **Non-wing airframe mass is fixed at 28.00 kg** regardless of how large the wing,
   tail or booms become. It was 28 kg on a 3.9 m² wing and it is 28 kg on a 5.92 m²
   wing. Charging it honestly — fuselage ∝ MTOW, booms ∝ length, tail ∝ wetted area,
   recovery ∝ MTOW — puts it at roughly **32.9 kg plus a 8.76 kg recovery system**,
   i.e. **+6.6 kg the model never charges**. At the measured exchange rate of
   **1.41 h/kg** (computed by removing that mass from fuel at constant MTOW) that is
   **−9.35 h, 151.95 → 142.60 h**. This is the same defect the gauntlet audit found on
   the previous challenger, at about 80% of its severity. It is not fixed here.
2. **The wing mass model is calibrated on one point.** `argus7.opt.design_space`
   derives spar-cap mass from root bending moment with a single fitted coefficient
   `k_cal = 4.2257`, set so the model returns v1.0's published 32.5 kg wing. The
   gauntlet audit verified the AR^1.5 exponent analytically and cross-checked the
   *ratio* between two design points against Raymer's independent GA regression to
   1.0% — but it also established that **76% of the spar-cap term at the baseline is
   the fitted constant**, most of it probably a missing factor of two. The scaling
   survives, because `k_cal` is a pure multiplier and cancels from every ratio; the
   absolute level is calibrated, not derived.

---

## 3. Aerodynamics

### 3.1 The drag polar and the loiter point

The mission model uses the standard lumped polar

    C_D = C_D0 + C_L² / (π · AR · e)

with C_D0 = 0.01588 and e = 0.8482, both **outputs of geometry** in the optimiser's
coupled model rather than free variables. At the loiter point:

| Quantity | Value |
|---|---|
| Loiter C_L | **1.2098** = C_Lmax / 1.15², stall-constrained |
| C_D | 0.04150 |
| **L/D** | **29.15** |
| Induced share of C_D | 61.7% |
| ρ at 4,359 m | 0.78856 kg/m³ |
| TAS, MTOW → dry | **118.7 → 82.8 km/h** (32.97 → 23.00 m/s), mean 101.8 km/h |
| Drag, MTOW → dry | 105.3 → 51.2 N |
| Shaft power, MTOW → dry | 4.71 → 2.04 kW, mean 3.30 kW |
| Re at MAC, MTOW → dry | 8.37e5 → 5.84e5 |
| Re at tip, MTOW → dry | 6.80e5 → **4.75e5** |

The **stall constraint binds**, as it did on v1.0: unconstrained minimum-power C_L for
this polar is above C_Lmax/1.15², so the aircraft loiters at 1.2098 exactly. This
matters, because it means loiter speed — and therefore power — is set by C_Lmax, and
C_Lmax is held at a flat 1.60 for every design point. NeuralFoil on the actual
coordinates puts the 2D C_Lmax of a 20%-thick FX 63-137 at **1.972** against the
13.7% section's 1.877, so 1.60 is **conservative** for a thickened section. The
residual risk is three-dimensional and is not modelled anywhere in this stack.

**82.8 km/h at end of mission is slow.** At 23 m/s, station-keeping margin against
wind over a disaster zone is thin. Nothing in the objective function knows about wind.
This is a mission-suitability caveat on the last third of the endurance, not a
modelling error.

### 3.2 C_D0 build-up

`argus7.aero.buildup` computes a component parasite build-up from the *actual*
geometry — real FX 63-137 arc length, real fuselage station loft, derived boom length,
true (not projected) tail panel area — with a **measured** transition location rather
than an assumed one. Run on the v3.0 geometry:

| Component | S_wet (m²) | Re | x_tr | C_f | FF | Q | C_D0 | share |
|---|---|---|---|---|---|---|---|---|
| Wing | 11.621 | 8.37e5 | 0.553 | 0.00285 | 1.302 | 1.00 | 0.00728 | 55.9% |
| Fuselage | 4.029 | 5.36e6 | 0.100 | 0.00300 | 1.187 | 1.00 | 0.00243 | 18.6% |
| Booms | 2.298 | 6.41e6 | 0.150 | 0.00276 | 1.005 | 1.30 | 0.00140 | 10.7% |
| Tail | 1.359 | 5.41e5 | 0.300 | 0.00409 | 1.212 | 1.05 | 0.00119 | 9.2% |
| Miscellaneous (6%) | — | — | — | — | — | — | 0.00074 | 5.7% |
| **Total** | **19.307** | | | | | | **0.01304** | |

**Three things must be said about that number, and none of them is comfortable.**

**(a) It is not the number the design file carries.** The design file's 0.01588 comes
from `argus7.opt.coupled.cd0_from_geometry`, which is an equivalent-skin-friction
model — C_D0 = C_fe · S_wet/S_ref — calibrated at the v1.0 point and multiplied by a
NeuralFoil-measured thickness penalty. The two disagree by 22% on v3.0. They disagree
because the build-up reads t/c from the *airfoil coordinates* (13.71%) while the design
flies a section scaled to **19.09%**; the build-up therefore under-charges the wing's
wetted area and form factor. The optimiser's number is the one used, and it is the
higher (more conservative) of the two.

**(b) Neither number contains the payload.** `argus7.aero.buildup`'s own docstring
lists what it omits: the 50 kg payload installation (a ~0.3 m gimballed EO/IR ball at
C_D 0.4 on frontal area is **alone worth ~0.007 in C_D0**), engine cooling drag (5–10%
of total on a piston installation), fuselage base drag (the aft station closes to
r/R = 0.34), and recovery/launch hardware. A modest **+0.0035** allowance for those
costs **−0.39 d** on this design point. The fix is to add the hardware to the design
file, not to raise a factor.

**(c) The correlation is being used outside its calibration.** Raymer's form factor
(eq. 12.30) is a function of t/c and (x/c)_m only — a **minimum-drag** pressure
correlation with no C_L dependence — while the transition location fed to it was
measured **at C_L 1.21**. The module has it both ways, and says so. Cross-checked
strip-by-strip against NeuralFoil on the same coordinates, the C_f·FF build-up is
**11.2% low** on wing drag area at the loiter lift coefficient (+0.00088 in C_D0). The
sign of the disagreement with the design file is solid; its size is not.

### 3.3 The XFOIL transition result

The wing transition location is **measured, not assumed** — the one input in this
build-up that is. XFOIL 6.99 on the repository's pinned, checksum-enforced
`data/airfoils/fx63137.dat`, converted Lednicer→Selig, 300 panels, Ncrit 9, viscous,
fixed-C_L mode at C_L = 1.21, ten spanwise stations
(`research/riblets_pack.md` §3):

- **Upper surface transition 50.2% chord at the root, moving aft to 60.5% at the tip.**
- Lower surface 61.4% → 68.2%.
- **40.5% of the wing's wetted area is turbulent, carrying 53.3% of its skin friction.**
- Independently corroborated by NeuralFoil (xxlarge), which puts upper transition at
  0.547 (root) to 0.599 (tip).

Two consequences the report must carry:

1. **The laminar run is the leverage, and it is fragile.** Moving upper-surface
   transition forward by five points of chord costs Δc_d = +0.00057 → **−1.13 h**. A
   fully tripped wing costs **−13.6 h**. That is why `research/materials_pack.md` §6
   is a structures-and-surface question with an endurance answer.
2. **Ncrit = 9 is assumed.** A UAV in quiet air at 4,400 m may see Ncrit 11–13, which
   moves transition aft; in turbulent air or propeller wash, Ncrit 5–7 moves it
   forward. The riblets pack flags explicitly that the whole transition table should be
   re-run at Ncrit 7 and 12 before any number in it is treated as settled. It has not
   been.

Also note: these numbers were measured **on the 13.7% section at v1.0's chords and
speeds.** v3.0 flies a 19.1% section at different Reynolds numbers, and the transition
locations have not been re-measured for it.

### 3.4 The Oswald factor — three different quantities, and why that mattered

This is the finding that most changed how the programme models drag, and it is
recorded in `docs/decisions/2026-08-20-span-efficiency-finding.md`.

At the loiter lift coefficient, **induced drag is the majority of total drag** (61.7%
on v3.0; 55.5% on v1.0). Every optimisation the programme had examined — riblets,
boom deletion, surface finish — was attacking the smaller half. And the Oswald factor,
the single largest lever in the drag model, had never been validated.

AVL 3.36, run on the actual planform at matched C_L 1.21 (12 sections, 24 spanwise
panels, tip-bunched, inside the single-precision NaN limit of 40), returned **e = 0.9786**
at the as-designed −3° twist. The design file said 0.85. A crude AeroSandbox viscous
subtraction implied 0.77.

**These are three different quantities and must not be compared:**

| Symbol | What it is | v1.0 value |
|---|---|---|
| AVL's e | **Inviscid span efficiency** — how close the lift distribution is to elliptic | 0.9786 |
| The design file's e | **Lumped Oswald factor** in C_D = C_D0 + C_L²/(πARe), which conventionally also absorbs viscous lift-dependent drag | 0.85 |
| AeroSandbox's implied value | A viscous build-up's lumped equivalent, crude subtraction | ~0.77 |

Treating AVL's 0.9786 as if it were the design file's 0.85 would have handed the
programme **+7.1 h that does not exist**, straight into the optimiser's objective.

**How it was closed.** `argus7.opt.coupled` fits a surface to **45 AVL runs** spanning
AR 14–30, taper 0.30–0.60, twist 0 to −6°, and adds an explicit viscous lift-dependent
term:

    1/e_eff = 1/e_inviscid + K_visc · π · AR,   K_visc = 0.002237

calibrated once so the baseline reproduces the report's own total C_D at C_L 1.21. On
v3.0's planform this returns **e_eff = 0.8482**.

**What the AVL sweep established, and it contradicts the design's founding premise:**
span efficiency is **nearly flat in aspect ratio** — 0.989 at AR 14 to 0.969 at AR 30.
The previous optimiser had used Raymer's straight-wing correlation, fitted to
conventional aircraft at AR 5–10, which returns e = 0.485 at AR 22 against 0.979
measured, and it drove a run to AR 15.25 for an entirely fictitious reason. **High
aspect ratio was never the route to endurance it was assumed to be**; the only
legitimate pushback on AR is structural mass, and the only legitimate reward is span.

**Three caveats on the surface, all from the gauntlet audit's independent re-run:**

- The stored table **reproduces to four decimals** when the decks are rebuilt from
  scratch — the 45-run sweep is real, not asserted.
- **It is not panel-converged.** On a test planform e falls monotonically with
  refinement, 0.9611 (12×24) → 0.9564 (12×36), i.e. −0.5% and still moving. The whole
  surface is built on the coarsest of those, and its coefficients are quoted to six
  figures they have not earned.
- **`K_visc` is design-independent and double-books.** It is calibrated once on a
  13.7% section at Re 7.75e5 and applied unchanged to a 19.1% section at a different
  Reynolds number. It also overlaps the thickness drag multiplier: the wing's
  profile drag at lift is represented twice, in two terms neither of which knows about
  the other.

**The open band on the lumped Oswald factor — 0.77 to 0.85 — is worth about −5.6 h**,
larger than the riblet question and the boom-deletion question combined. It has been
narrowed by measurement, not closed.

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
sized for *climb* while flying a *loiter* mission. That tension — climb wants 12–17 kW,
loiter wants 3.3 kW, one fixed-pitch propeller on one fixed engine must serve both —
is the central configuration problem of this aircraft, and no amount of aerodynamic
work substitutes for solving it.

### 4.2 Engine right-sizing

The single largest lever in the whole programme is the **engine rating**, not the
airframe.

| | v1.0 published | v1.0, honest model | **v3.0** |
|---|---|---|---|
| Engine rating | 17 kW | 17 kW | **10.845 kW** |
| Loiter shaft power | ~3.4 kW | 3.33 kW | 3.30 kW |
| **Load fraction** | — | **19.0%** | **30.6%** |
| BSFC assumed / effective | 270 assumed flat | **425 g/kWh** | **339 g/kWh** |
| Endurance | 4.70 d (claimed) | **3.16 d** | **6.33 d** |

Source: `opt_runs/final.json` (`baseline_v1`, 75.90 h = 3.163 d) and
`opt_runs/layout.log`.

Right-sizing works because BSFC is a strong function of load. A 17 kW engine loitering
at 3.3 kW is at 19% load, deep in the hyperbolic part of the fuel-flow curve. An
11 kW engine at the same shaft power is at 31%, where the curve has flattened.

The climb constraint is what stops the engine shrinking further, and on v3.0 it is
**exactly active**: `argus7.opt.coupled.climb_power_required_w` returns **10.68 kW**
for 2 m/s sea-level climb at MTOW against the **10.845 kW** installed. That is 1.5%
margin, which is another way of saying the engine size is *determined* by the climb
requirement and not by the loiter mission at all.

**A consistency item that is not resolved.** The design file still carries
`engine_displacement_cc: 250`, tagged `report-§2`, alongside a 10.845 kW rating. At
`argus7.prop.engine`'s assumed 7,500 rpm power peak that is a BMEP of **6.94 bar**,
against v1.0's 10.88 bar for the same displacement at 17 kW. Either this is a 250 cc
engine run well below its rating, or the displacement should have moved with the power
and did not. **The displacement field was inherited, not re-derived.**

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

At v3.0's loiter point (3.30 kW at a 7,499 rpm crank) this returns **346.6 g/kWh**.

The optimiser uses a simpler fit to the same curve,
BSFC(load) = BSFC_full · (0.8471 + 0.1529/load), which at v3.0's 30.6% load and a
252 g/kWh full-load basis returns **340.1 g/kWh**. **The two independent
implementations agree to 1.9%.** The gauntlet audit's third, independently coded
Willans line agreed with the module to 2.4% on a different design point. This is one
of the better-corroborated numbers in the report.

**Four things about it that are assumptions, and the report will not hide them:**

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
   is worth −5.6 h.

### 4.4 The BSFC that the answer actually rests on

The optimiser treated full-load BSFC as a variable bounded [0.250, 0.320] kg/kWh and
took **0.2519**. That is the report's own §6 language: *"BSFC is not published — must
be dyno-mapped; design assumes 270 g/kWh, target ≤250."*

**252 g/kWh is the target, not a unit.** The only two engines on v1.0 §6's shortlist
with *verified, published* BSFC — the RCV DF70LC and the Orbital HFDI-150 — are both
**330 g/kWh**. Endurance is exactly inversely proportional to BSFC in this model
(BSFC enters mass flow linearly and nothing else), so:

| Full-load BSFC | Effective at 30.6% load | Endurance |
|---|---|---|
| 250 g/kWh (the §6 target) | 336.8 | 153.14 h — 6.38 d |
| **252 g/kWh (as optimised)** | **339.5** | **151.95 h — 6.33 d** |
| 270 g/kWh (the §6 assumption) | 363.8 | 141.79 h — 5.91 d |
| 300 g/kWh (the §6 walk-away) | 404.2 | 127.61 h — 5.32 d |
| **330 g/kWh (the verified units)** | **444.6** | **116.01 h — 4.83 d** |

**This single row is the largest uncertainty in the report.** It is not an aerodynamic
question and it cannot be closed by analysis. It is closed by putting an engine on a
dyno.

### 4.5 Propeller selection — and an open discrepancy

A BEMT sweep over ~400 configurations, requiring **both** operating points
simultaneously — loiter thrust *and* climb power absorption — produced the selection.
Of 100 configurations in the first sweep, **34 satisfied both**. For the published
v1.0 design the count was **zero**.

Selected and carried in the design file (`opt_runs/prop_final.json`):

| | Value |
|---|---|
| Diameter / blades / rpm / p/D | **1.04 m / 2 / 1,900 / 0.95** |
| Loiter efficiency | **0.8581** |
| Climb power absorbed | 101.2% of the 8.15 kW rating it was sized against |
| Tip Mach | 0.309 (against a 0.75 limit) |
| Reduction ratio | **3.947 : 1** for a 7,500 rpm engine |

**Variable pitch is not needed — a genuine save.** The loiter-optimal pitch is the
same p/D the fixed-pitch optimum already uses, so a constant-speed unit buys
**+0.00%** at loiter. It would add mass, cost and a failure mode to a 150-hour
unattended flight for no endurance. This holds *because* the fixed-pitch design was
selected under a simultaneous climb-absorption constraint, so it already sits where a
variable unit would put it. Caveat: this evaluates loiter efficiency and climb
absorption, not climb-*rate* optimisation.

**Loiter is a gentle condition** — 78 N of thrust and 2.2 kW of useful power at
102 km/h mid-burn — which is why a large slow disc wins and why tip Mach never becomes
a constraint.

#### Three discrepancies in the propeller record, stated plainly

**(a) The propeller was sized against the retired v2.0 design point, not v3.0.**
`scripts/prop_refine.py` loads `design/argus7_v2.yaml` — 248.4 kg MTOW, 5.456 m²,
4,191 m, 8.15 kW. v3.0 is 313 kg on 5.919 m² at 4,359 m with 10.845 kW. Re-running the
BEMT here against **v3.0's** operating point:

| Condition | Thrust required | 1.04 m / p/D 0.95 at 1,900 rpm delivers | rpm needed | η there |
|---|---|---|---|---|
| Full fuel | 105.3 N | — | 2,360 | 0.856 |
| Mid burn | 78.3 N | **58.1 N** | **2,040** | **0.853** |
| Dry | 51.2 N | — | 1,660 | 0.849 |

The propeller **can** meet v3.0's thrust and its climb absorption (99.3% of the
10.845 kW rating at 2,660 rpm), so the propulsion set still closes — but **not at the
1,900 rpm the design file records.** At the rpm v3.0 actually needs, loiter efficiency
is 0.853, not 0.858, worth **−0.4 h**. Worse, 2,040 prop rpm through the recorded
3.947:1 reduction puts the crank at **~8,050 rpm, above the 7,500 rpm rating** the
engine deck assumes. **The gearing needs re-deriving for v3.0. It has not been.**

**(b) The decision record and the design file disagree on the diameter.**
`docs/decisions/2026-08-21-propeller-selection.md` selects **1.00 m at p/D 1.05**
(η 0.852), preferring it over the sweep's top-scoring 1.04 m because the larger disc
*"leaves only 56 mm to the booms"*. The design file carries **1.04 m at p/D 0.95**,
which is what `opt_runs/prop_final.json` records and what the sweep actually returned.

**(c) The 56 mm clearance figure is wrong, and in the design's favour.**
`scripts/prop_refine.py` hardcodes the boom inner surface at **0.6206 − 0.045 m**,
which is the **v1.0** boom station (0.134 × a 4.63 m semi-span). On v3.0 the semi-span
is 5.633 m, so the boom station is 0.7548 m and the inner surface is at 0.7098 m. The
true clearance for a 1.04 m disc is therefore **190 mm, not 56 mm.** The trade that
drove the decision record's recommendation does not apply to this aircraft, and the
1.04 m disc in the design file is the better of the two on both counts. The record and
the file should be reconciled; the file is right.

---

## 5. Stability and control

This is where v1.0 fails hardest and where v3.0 makes its real contribution.

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

### 5.2 The v3.0 neutral point

    Xnp/MAC = Xac_wing/MAC + V_h · (a_t/a_w) · (1 − dε/dα) · η_t

| Term | v3.0 |
|---|---|
| Wing AC | 25% MAC (thin-airfoil; see the bias note below) |
| V_h | 0.4218 |
| a_w (Helmbold/DATCOM, AR 21.44) | 5.724 /rad |
| a_t (panel AR 3.0) | 3.335 /rad |
| dε/dα = 2a_w/(πAR) | 0.1700 |
| η_t (tail dynamic-pressure ratio) | 1.00 — the inverted V sits on booms outboard of the fuselage wake and ahead of the pusher disc |
| **Tail contribution** | **+20.40% MAC** |
| **Neutral point, analytic** | **45.40% MAC** (x = 1.4895 m) |
| **Neutral point, AVL (wing + inverted-V tail, real dihedral)** | **50.98% MAC** (x = 1.5192 m) |
| Munk fuselage apparent-mass term | **−4.47% MAC** |

### 5.3 CG, static margin and fuel burn

| Fuel state | Mass (kg) | x_cg (m) | CG (% MAC) | SM (% MAC) | SM with pod (% MAC) |
|---|---|---|---|---|---|
| Full | 312.94 | 1.4588 | 39.61 | **+5.79** | +1.32 |
| Half | 232.64 | 1.4589 | 39.61 | +5.75 | +1.28 |
| Dry | 152.34 | 1.4592 | 39.69 | **+5.71** | +1.24 |

**Static-margin excursion full → empty: −0.08% MAC.**

This is the finding that justifies putting the layout in the optimiser. **The design
pack's "<0.5% MAC CG travel" claim, which failed by 76× on v1.0, is achieved here** —
and achieved *for the reason the pack gave*, not by accident. The fuel centroid sits at
**39.53% MAC**, 77 mm aft of the wing AC and within **0.08% MAC of the CG itself**, so
160.6 kg — 51% of gross mass — burns off without moving the balance. Nobody chose that;
it fell out of a search in which `x_le_frac` was free and static margin was a hard
constraint at **both** fuel states.

Moving the wing station from 0.22 to 0.354 is what does it. It moves the neutral point
aft nearly 1:1 while moving only the wing group and the wing fuel with it, so static
margin rises monotonically with `x_le_frac` — and it simultaneously puts the tanks
where the CG lands.

### 5.4 The honest band, and the two biases that partly cancel

**The static margin depends on which neutral point you believe, and the spread is
wide.** Every reading is stable; none is +5.79% exactly.

| Reading | Neutral point | Static margin, full fuel |
|---|---|---|
| Analytic, wing + tail (the convention the spec and the published 55% figure are written in) | 45.40% MAC | **+5.79%** |
| Analytic + Munk fuselage term | 40.93% MAC | **+1.32%** |
| **AVL, wing + tail** | **50.98% MAC** | **+11.37%** |
| AVL + Munk fuselage term | 46.51% MAC | **+6.90%** |
| The batched model the optimiser searched with | — | +10.51% (dry +7.46%) |

**Two known method biases run in opposite directions and are declared, not netted:**

1. **The 25% wing AC is conservative.** Running the AVL deck with the tail surface
   deleted puts the isolated wing's AC at **30.2–30.5% MAC** on a planform with sweep,
   taper and twist — 5.2 to 5.5% MAC aft of the quarter-chord. Every static margin
   computed with 0.25 is therefore **understated by about 5% MAC**. That difference,
   not any tail effect, is the whole of the gap between the analytic and AVL neutral
   points; the analytic **tail** term matches AVL to within 0.8% MAC on both designs.
2. **The Munk pod term is not in the headline number and it is worth −4.47% MAC.** It
   is excluded because the specification's relation and the published 55% MAC figure
   are both wing-plus-tail only, and because AVL — the independent check — carries no
   fuselage. It is Munk's apparent-mass estimate, which
   `research/configuration_hypotheses.md` §3.3(a) computes for this pod as 8.2% on
   v1.0 against 7.3% by the more elaborate Multhopp strip method: **this term is the
   pessimistic end of the published band.**

Applied together (AVL wing AC + Munk pod) the answer is **+6.90% MAC**, comfortably
inside the 5–15% gate. Applied one at a time it is +1.32% or +11.37%. **The design is
stable on every reading available, and the width of that band is a statement about the
method, not about the aeroplane.**

**One thing that is not in this analysis at all:** dynamic stability, control power,
trim authority, spiral and Dutch-roll modes, aeroelastic trim, and departure
behaviour. This is a longitudinal static balance and nothing more.

---

## 6. Structures and materials

The structural work in this repository is research-grade, not design-grade: no FEA,
no test coupons, no article. What follows is what
`research/materials_pack.md` (31 sources) and `research/boom_construction_pack.md`
establish, and what the mass model actually implements.

### 6.1 The load case and the spar

`argus7.opt.design_space` sizes the spar cap from root bending moment:

    M_root = n_ult · W · (b/2) · k_lift · fuel_relief
    A_cap  = M_root / (h_spar · σ_cap),  h_spar = (t/c) · c_root
    m_cap  ∝ ρ · A_cap · (b/2) · k_taper

with n_ult = 5.7, k_lift = 0.40, fuel relief 0.78, σ_cap = 600 MPa (compression
allowable, carrying a buckling/damage knockdown), ρ = 1600 kg/m³. Substituting gives
**m_cap ∝ W · AR^1.5 · √S / (t/c)** — the exponent verified analytically by the
gauntlet audit, and the wing-mass *ratio* between two design points agreed with
Raymer's independent GA regression to 1.0%.

| | v1.0 | **v3.0** |
|---|---|---|
| Root chord | 0.5807 m | 0.6192 m |
| **Spar depth at root** | 79.6 mm | **118.2 mm** |
| Ultimate root bending moment | 20.19 kN·m | **30.74 kN·m** |
| **Required cap area** | 423 mm² | **433 mm²** |
| Cap mass | 14.57 kg | 18.16 kg |
| Skin / rib / systems (4.6 kg/m²) | 17.94 kg | 27.23 kg |
| **Wing total** | **32.51 kg (8.34 kg/m²)** | **45.39 kg (7.67 kg/m²)** |

**The interesting row is the cap area: 433 mm² against v1.0's 423 mm², despite +25%
MTOW and +22% span.** Thickening the section from 13.7% to 19.1% makes the spar 48%
deeper, and depth buys cap area back almost exactly as fast as weight and span
consume it. That is the mechanism by which a much larger wing costs only +12.9 kg.

**And the buckling concern raised by the audit does not bite here.** The audit found
the retired challenger's cap laminate at 1.10 mm and b/t ≈ 200 — a width-to-thickness
ratio that is not entitled to a 600 MPa allowable already carrying a buckling
knockdown. At a 0.25c cap width v3.0's laminate is **2.80 mm at b/t ≈ 55**, against
v1.0's 2.91 mm at b/t ≈ 50. v3.0 does not exploit the free pass; it sits essentially
where the calibration point does. **σ_cap = 600 MPa is still applied without a
minimum-gauge or panel-buckling floor**, which remains a model limit, but it is not a
limit v3.0 is standing on.

**Areal density cross-check.** 45.39 kg on 5.9191 m² is **7.67 kg/m²**. The materials
pack's costed build options, computed from first principles for the v1.0 planform:
Option A (moulded CFRP sandwich, female moulds) **6.85 kg/m²**, Option B (pultruded
strip caps + moulded sandwich skin, the recommendation) **7.40 kg/m²**, Option C3
(pultruded caps + printed ribs + film aft of 55% chord) 8.65 kg/m². **The mass model's
v3.0 wing sits 3.6% above the recommended build's measured areal density.** That is a
plausible place to sit; it is not evidence that the wing can be built.

### 6.2 What the materials research establishes

The sponsor's premise — *"carbon fibre rods and tubes and 3D printed parts as much as
possible"* — was evaluated and is **right about spar caps and booms, wrong about the
wing spar and the skins, roughly break-even on ribs.**

| Claim | Verdict | The number |
|---|---|---|
| Pultruded UD carbon as spar-cap material | **Right, strongly** | 1,682 MPa compressive / 133.8 GPa measured, two independent vendors agreeing. E/ρ **87.9 vs 77.8** for hand wet layup — it matches prepreg on specific stiffness with no autoclave, no freezer, and no layup skill |
| COTS carbon tube for the twin booms | **Right** | 90 × 2.5 mm roll-wrapped runs at 102 MPa against a 620 MPa allowable — **4× strength margin**, stiffness-critical |
| COTS carbon tube as the **wing** spar | **Wrong, by a clean geometric factor** | A round tube inside a 12%-thick wing needs **2.07×** the material of a cap-and-web spar for the same moment. The ratio is 2h/D — pure geometry, not a materials argument |
| 3D-printed ribs, fairings, trays, ducts | **Acceptable at a 3.8–4.4× mass penalty** | Rib stress **0.06 MPa, 170× below the creep-test floor**. This is where the preference is simply free |
| Printed skin panels | **Wrong, decisively** | ±1.14 mm MJF tolerance against a 0.512 mm step budget; **+18.7 kg**, 58% of the entire wing budget |
| Heat-shrink film skin | **Wrong, but not for the usual reason** | Streamwise waviness actually passes. It fails because film cannot form the leading edge, and its scalloping is a **spanwise** disturbance for which NASA states no criteria exist |
| Printed tooling, plugs, jigs | **Right, and under-used** | The highest-leverage use of printing on the programme — it attacks the €9–14k wing-tooling quote that is the premortem's highest-probability failure mode |

**Two findings from that pack that change how the structure should be read:**

1. **The wing is stiffness-critical, not strength-critical.** Integrating curvature
   along the span gives **14.2% of semi-span tip deflection at limit load** (21.4% at
   ultimate, far enough into geometric non-linearity that a linear beam calculation
   stops being trustworthy). Modern 15 m sailplanes run 8–10%. **That inverts the
   material argument**: the figure of merit is E/ρ, not σ/ρ, so pultruded rod's
   1,682 MPa buys nothing and high-modulus pultrusion (+71% EI at equal mass) is the
   right lever. Computed for v1.0's planform; **not recomputed for v3.0's**, whose
   deeper spar should improve it.
2. **The surface-quality bar is about 6× looser than the programme assumed.**
   Carmichael's allowable single-wave h/λ at Re 0.6–1.1 M is 0.031–0.044, because
   allowable waviness scales as Re^−0.75. NASA TP-2256 **measured** moldless homebuilt
   VariEze/Long-EZ wings at h/λ 0.0030–0.0046 — passing with 2.6–4.9× margin. **A
   garage build can hold laminar flow.** Measured, not asserted.

**The mass-to-endurance exchange rate, measured on this design point: 1.41 h/kg**
(the materials pack independently derived 1.5 h/kg on v1.0). Every structural decision
can be priced with it.

### 6.3 The booms

`research/boom_construction_pack.md` sizes the booms to a **stiffness** criterion
(1.5° of tail rotation), not a strength one, and corrects the tail load upward by
1.81× from the materials pack's figure.

- **Recommended: COTS roll-wrapped 110 mm × 2.0 mm, no liner — 7.54 kg for the pair**
  (9.20 kg with fittings). The design file still specifies **Ø90 mm**, which meets the
  requirement only at **10.06 kg** (11.72 kg installed) — i.e. **the published baseline
  carries about 3.4 h of unpaid stiffness debt**, and going to 110 mm pays it for
  −0.24 kg at +0.00042 of drag.
- **An aluminium liner is the single most expensive idea in the proposal**: 5.5–16.1 kg
  = 8.3–24.2 hours of endurance, for a material that delivers 28.1 kN·m² of EI where
  carbon delivers 69.5 at equal mass and radius.
- **The propwash premise is geometrically false, and that is the good news.** The booms
  clear the propeller tip path by 169 mm and the contracted slipstream by 183–209 mm
  (on v1.0's geometry; **190 mm to the tip path on v3.0's**, §4.5). They sit in the
  acoustic near field at ~10–30 Pa, not in the wake at 300–560 Pa — a 20–40× difference
  in excitation. Forced-response gives a peak vibratory strain of **0.011% against a
  0.6% matrix fatigue limit: a 55× margin.**
- **The frequencies cannot all be separated at any sensible diameter, and it is more
  honest to say so.** The second bending mode sits inside the blade-passage keep-out
  band and there is no affordable escape. It is acceptable *only* because the boom is
  not in the wash. Three prohibitions follow, and they are configuration constraints:
  nothing structural inside r = 0.45 m of the thrust axis aft of the prop plane; the
  first torsional mode must be resolved against the true loiter rpm; and **measure it**
  — one tap test with the tail fitted settles the whole section in an afternoon.
- **The tail attachment as proposed has a negative margin before fatigue**: two M6 at
  60 mm centres carrying the panel root moment gives 306 MPa of bearing against a
  165 ± 28 MPa allowable. A Ø50 × 150 mm spigot gives 1.76 MPa. **Zero mass, zero drag,
  a factor of 174 on the margin.** This is the cheapest fix in the programme.

**Every boom number above was computed for the v1.0 configuration: a 3.646 m boom, a
0.813 m propeller at 2,100 rpm, and a 0.31 m² tail. v3.0 has a 4.064 m boom, a 1.04 m
propeller at 1,900+ rpm, and a 0.37 m² tail. The stiffness case, the mode map and the
excitation comb all need re-running.**

### 6.4 Recovery

Unchanged from v1.0 in mass (7.0 kg) and unchanged in the design file, but **the
aircraft got 25% heavier and the recovery system did not**.

| | v1.0 | v3.0 |
|---|---|---|
| Recovery mass allowance | 7.0 kg | **7.0 kg (unchanged)** |
| Descent rate on v1.0's 85 m² canopy, at MTOW | 5.43 m/s | **6.07 m/s** |
| Canopy area for 6 m/s at MTOW | 69.5 m² | **87.0 m²** |
| Touchdown energy at 6 m/s, dry recovery mass | 2.67 kJ | 2.74 kJ |
| Touchdown energy at 6 m/s, MTOW | 4.50 kJ | **5.63 kJ** |

Recovery normally happens near dry mass, where v3.0 is essentially unchanged from
v1.0 (2.74 vs 2.67 kJ) — the airbag/crush-keel case does not move. **The MTOW case
does**, and the ground-risk argument in v1.0 §9 was built on the 3–4.5 kJ figure. The
gauntlet audit's recommendation that recovery mass scale with MTOW (7.0 → 8.76 kg) is
not implemented.

---

## 7. Mission performance

### 7.1 How the 6.33 days is computed

`argus7.mission.sim.simulate_loiter` integrates a pure loiter until the fuel is gone,
in 120 equal-fuel-mass steps by the midpoint rule. Per step, at weight W:

    C_L      = min( √(3·C_D0·π·AR·e),  C_Lmax / 1.15² )     [stall-limited here]
    C_D      = C_D0 + C_L² / (π·AR·e)
    V        = √( 2W / (ρ·S·C_L) )
    D        = W / (L/D)
    P_shaft  = D·V / η_prop  +  P_elec / η_alt
    ṁ        = BSFC · P_shaft
    E        = Σ Δm / ṁ

with η_prop = 0.858, η_alt = 0.75, P_elec = 500 W, ρ from the ISA at 4,358.8 m, and
BSFC = 339.5 g/kWh (the part-load value at the mid-burn load fraction, §4.3).

Result: **151.9510 h = 6.3313 days**, reproducing `opt_runs/layout.log` exactly.

| | Full | Mid | Dry |
|---|---|---|---|
| Mass (kg) | 312.93 | 232.63 | 152.33 |
| TAS (km/h) | 118.7 | 102.3 | 82.8 |
| Drag (N) | 105.3 | 78.2 | 51.2 |
| Shaft power (kW) | 4.71 | 3.30 | 2.04 |
| Engine load fraction | 43.4% | 30.4% | 18.8% |

### 7.2 The validation gates it passed

**Gate 1 — the step integration must reproduce the closed-form Breguet solution.**
Called with `payload_power_w = 0` and a constant BSFC — the conditions under which
the analytic solution exists — the integrator returns 197.5053 h against the Breguet
form's 197.5066 h: **−0.00067%** at 120 steps. At 20,000 steps the loiter integration
has converged to within 0.0004% of its 120-step value, so the discretisation
contributes nothing. Asserted by
`tests/test_mission_sim.py::test_gate1_step_integration_matches_closed_form_breguet`
at a <0.1% threshold.

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

**BSFC was frozen at the mid-burn load and this costs 5.6 hours.** The optimiser
evaluates the part-load BSFC once, at the mid-point shaft power, and holds it constant
for the whole integration. But engine load falls from 43.4% to 18.8% across the burn,
and BSFC(load) goes as 1/load. By convexity the average of the true BSFC exceeds the
BSFC at the average load. Re-running the integration with BSFC evaluated **pointwise**
at each step's shaft power:

| | Endurance |
|---|---|
| BSFC frozen at mid-burn load (as recorded) | 151.95 h — 6.331 d |
| **BSFC evaluated pointwise across the burn** | **146.35 h — 6.098 d** |

**−5.60 h (−0.23 d).** This is a real, previously unreported optimism in the headline
number, and it is a property of the *evaluation*, not of the aircraft.

### 7.4 Sensitivity, and the corrected v1.0 anchors

#### v1.0's published anchors: two of the three are wrong

v1.0 §4 states: *"BSFC 250 g/kWh → +0.5 d; C_D0 0.016 → +0.36 d; loiter at 3,000 m
instead of 4,000 m → +0.23 d."* All three were re-derived by the gauntlet auditor from
first principles with independent code, and all three are re-derived again here with
the repository's own simulator on the published polar. Both derivations agree.

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

#### v3.0's own sensitivities

Computed here on the v3.0 design point, one lever at a time, everything else held:

| Lever | Endurance | Δ |
|---|---|---|
| **Baseline** | **151.95 h — 6.331 d** | — |
| C_D0 −0.004 (an exceptionally clean build) | 164.19 h | **+0.510 d** |
| C_D0 +0.0035 (turret + cooling + base drag allowance) | 142.65 h | **−0.388 d** |
| Loiter at 3,000 m (band floor) | 160.47 h | **+0.355 d** — but coverage falls from 436 to 207 km², −53% |
| Loiter at 4,000 m | 154.20 h | +0.094 d |
| Payload duty-cycled to 350 W average | 163.10 h | **+0.464 d** |
| Full-load BSFC 270 instead of 252 | 141.79 h | −0.423 d |
| Full-load BSFC 330 (the verified units) | 116.01 h | **−1.497 d** |
| Non-wing mass charged honestly (−6.6 kg of fuel) | 142.60 h | **−0.390 d** |
| BSFC evaluated pointwise across the burn | 146.35 h | **−0.233 d** |

### 7.5 What is not modelled

Every endurance figure in this report is **pure loiter**. There is no transit segment,
no climb to altitude, no reserve, no descent, no hold, no diversion, and no wind. v1.0
published a deploy-mode table (2,000 km transit → 3.98 d on station); **nothing in
this repository can reproduce or replace that table**, and it should not be quoted.

The comms coverage figures in §1 are the v1.0 elevation-angle model rescaled to the
new altitude. No link budget, no antenna pattern, no measured data in this altitude
band.

---

## 8. What changed from v1.0, claim by claim

| v1.0 claim | Status | v3.0 / measured | Where |
|---|---|---|---|
| Loiter endurance **4.70 d (112.8 h)** | **Reproduces arithmetically, wrong physically** | 112.977 h on its own polar (+0.16%); **3.16 d** once the engine is modelled at its 19% load instead of assumed flat | `opt_runs/final.json`; §4.2 |
| **Static margin +14.7% MAC at CG 42%** | **DOES NOT REPRODUCE** | **−44.0% MAC full, −82.2% dry.** The NP half *does* reproduce (52.95% analytic / 58.30% AVL vs published ~55%) — the 42% MAC CG is an assumed target no mass build-up supports | `argus7.analysis.balance`; §5.1 |
| CG window 38–46% MAC | **Missed** | CG at 97.0% MAC full, 135.1% dry. The window is 35.3 mm wide; the CG misses it by 189 mm and 383 mm | §5.1 |
| Fuel **101.5 kg in wing tanks at the AC** | **WING CANNOT HOLD IT** | Capacity **66.1 kg** on measured geometry. 35.4 kg — 14% of MTOW — has nowhere to be | `wing_fuel_capacity_kg`; §8 note below |
| **CG travel <0.5% MAC** (design pack) | **Fails by 76×** | −38.15% MAC on v1.0. **Achieved on v3.0: −0.08% MAC** | §5.3 |
| **V_h = 0.68** (§2 tail row) | **DOES NOT CLOSE** | S_h 0.31 m² with a 3.2 m arm gives **V_h 0.5765** (17.9% off). Either S_h should be 0.3657 m² or V_h is 0.5765. **v3.0's V_h = 0.4218 and closes** | xfail in `tests/test_geometry_closure.py`; §2.1 |
| **0.813 m prop at 2,100 rpm on 17 kW** | **CANNOT ABSORB ITS ENGINE** | Requires **C_P 0.911** against a ~0.25 ceiling; absorbs ~4.7 kW of 17. **v3.0: 1.04 m at 1,900+ rpm on 10.845 kW, absorbing 99–101%** | `tests/test_bemt.py`; §4.1, §4.5 |
| Reduction **2.3:1** | **Impossible** | A small 4-stroke peaking near 7,500 rpm cannot drive a 1,900 rpm prop through 2.3:1. **3.947:1** — and even that needs re-deriving for v3.0's rpm | §4.5 |
| Prop η **0.84 assumed** | Slightly pessimistic | **0.858** achieved by the BEMT sweep (0.853 at v3.0's actual rpm) | `opt_runs/prop_final.json` |
| BSFC **270 g/kWh flat** | **Wrong regime** | 270 applied at 19% load. Modelled: **425 g/kWh** on v1.0's installation, **339** on v3.0's | §4.3 |
| **BSFC 250 → +0.5 d** | ❌ **WRONG** | **+0.377 d.** +0.5 d would need 244 g/kWh | §7.4 |
| **C_D0 0.016 → +0.36 d** | ✅ correct | **+0.358 d** | §7.4 |
| **3,000 m → +0.23 d** | ❌ **WRONG** | **+0.198 d** | §7.4 |
| C_D0 = 0.020 "realistic" | Ambiguous, and the ambiguity matters | The build-up returns 0.0153 with the measured laminar run and **0.0200 with the wing assumed fully turbulent** — the design file's value to three decimals. Either §4's 0.020 is a fully-turbulent build-up containing **no payload allowance at all**, or it is a laminar build-up that does and the agreement is coincidence | xfail in `tests/test_buildup.py` |
| L/D_max 27.1 at C_D0 0.020 | Consistent | v3.0 L/D at loiter is **29.15** | §3.1 |
| e = 0.85 | Now derived, not asserted | 0.85 was a lumped factor conflated with two other quantities. **v3.0's 0.8482 comes from 45 AVL runs plus an explicit viscous term** | §3.4 |
| MTOW 250 kg | **Superseded, and the band is crossed** | **312.93 kg (+25%).** v1.0 §9's whole regulatory case is built at 250 kg | §10.4 |
| High AR is the route to endurance | **Contradicted** | AVL measures span efficiency nearly flat in AR (0.989 at AR 14 → 0.969 at AR 30). AR is not a strong lever; span and MTOW are | §3.4 |
| Wing 32.5 kg | Superseded | **45.39 kg** on a 52% larger wing — 7.67 kg/m² against 8.34 | §6.1 |
| Premortem (Annex A) | **Still valid, unchanged** | The failure modes, tripwires and decision rule in v1.0 Annex A are about the *programme*, not the design point, and are not superseded. The engine-numbers mode (#3) has if anything grown in weight | v1.0 Annex A |

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

## 9. Verification

### 9.1 The test suite

**459 passed, 12 xfailed** (`.venv/bin/pytest tests/`, ~90 s), across 17 test modules
covering airfoil coordinates, ISA, geometry closure, CAD wing/airframe/export/render,
drag build-up, NeuralFoil, XFOIL driver, BEMT, engine deck, mission simulation,
optimiser design space, balance, lift-curve anchors, and a regression-defect file.

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
| `test_both_designs_meet_the_programmes_own_static_margin_gate` | the pre-registered 8–20% MAC gate was never evaluated on either design |
| `test_report_claim_of_half_percent_cg_travel` | 76× and 30× over |
| `test_v2_mass_budget_closes` | 13.02 kg unallocated in the retired v2.0, traced to an engine-mass credit applied twice |
| `test_v2_static_margin_stays_inside_the_window_across_the_whole_burn` | outside at every fuel fraction |
| `test_report_stated_tail_volume` | V_h 0.5765, not 0.68 |
| `test_total_cd0_against_report_baseline` | build-up 0.0153 vs stated 0.020, −23.6%, outside the ±15% gate |

### 9.2 Mutation testing — does the suite have teeth?

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

### 9.3 The gauntlet: pre-registered gates and an adversarial audit

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
| Stall margin | **Survived** — and NeuralFoil showed the flat C_Lmax 1.60 is *conservative* for a thick section, not generous |
| Wing fuel-volume constraint | **Broken** — mis-specified by ~1.6×, so the design was pressed against a wall in the wrong place |
| Fixed 28 kg non-wing airframe mass | **Broken** — +8.08 kg undercharged, worth −15.2 h on that design |
| `CD0_BASELINE` comment | **Broken** — claimed 0.01529 "at the v1 point"; the function returns 0.016947 there |
| Flat BSFC at 20% load | **Broken** — the repository's own engine module already refuted it |

That audit is the direct ancestor of §4 and §5 of this report. It is also why this
report states model limits beside numbers rather than in a footnote.

### 9.4 Independent cross-checks that agree

| Quantity | Method A | Method B | Agreement |
|---|---|---|---|
| v3.0 loiter BSFC | optimiser part-load fit, 340.1 g/kWh | `argus7.prop.engine` Willans deck, 346.6 g/kWh | 1.9% |
| Step integration | 120-step midpoint | closed-form Breguet | 0.0007% |
| v1.0 endurance | this repository, 112.977 h | independent auditor, 112.977 h | 6 sig figs |
| v3.0 neutral point (tail term) | analytic relation | AVL with real inverted-V dihedral | 0.8% MAC (on v1.0/v2.0) |
| Wing mass ratio between design points | this AR^1.5 model | Raymer GA regression | 1.0% |
| Wing transition location | XFOIL 6.99, Ncrit 9 | NeuralFoil xxlarge | 4–5 points of chord |
| Mass-to-endurance exchange rate | measured here, 1.41 h/kg | materials pack, 1.5 h/kg | 6% |
| Fuselage loft volume | `balance.fuselage_volume_m3`, 0.4022 m³ (v3.0) | configuration pack, 0.4105 m³ (v1.0 pod) | same pod, 2% |

### 9.5 What the verification does NOT cover — and it is a real gap

**No test in this repository references `design/argus7_v3.yaml`.** The balance tests
are parameterised over v1.0 and v2.0. The design-space tests are parameterised over
v1.0 and v2.0. The mission, engine, BEMT, build-up, CAD and airfoil tests all load
v1.0. **The design point this report publishes has zero regression coverage.** Every
v3.0 number in this document was computed interactively against the committed modules,
which is reproducible but is not guarded.

Related: **there is no CAD for v3.0.** `model/` is built from v1.0 and `model_v2/`
from the retired v2.0; `figures/cad/` and `figures/cad_v2/` render those. No
three-view in this repository depicts the aircraft described here.

And: **`opt_runs/layout.json` no longer contains the v3.0 design point.** It was
overwritten by a later, deliberately unbounded run (MTOW to 600 kg, span to 20 m,
which returned 10.05 d at 597 kg). The surviving record of the run that produced
v3.0 is `opt_runs/layout.log`, and `scripts/run_optimisation_layout.py` has likewise
been edited to the free-bounds variant. **The exact script and bounds that produced
the published design point are not recoverable from the repository.** The design
variables are, and everything in this report is recomputed from them.

---

## 10. Open questions, and what would settle them

Ordered by how much they could move a headline number.

### 10.1 What is the engine's actual BSFC? — worth ±1.5 days

The single largest uncertainty in the report, and it is not an analysis question.
Everything rests on a **252 g/kWh full-load** figure that is the report's aspirational
dyno target. The two shortlist engines with published, verified BSFC are both
**330 g/kWh**, at which this aircraft flies **4.83 d instead of 6.33**. The engine
deck's own reference-load assumption (0.75) can move the modelled loiter BSFC from
293 to 332 g/kWh on its own, and the module carries an unreconciled 36% disagreement
between two values of the same friction fraction.

**What settles it:** a mapped dyno run at the 2–5 kW band with altitude simulation,
plus a 100 h continuous oil-system test. This is exactly v1.0 Annex A's Phase 0, and
it is exactly its tripwire #3 (*walk away if >300 g/kWh at the loiter point*). Note
that the modelled value already exceeds that tripwire. **Second, and cheap:** resolve
φ = 0.1325 vs φ = 0.18 in `argus7/prop/engine.py`, which the file itself declines to
do, and settle the reference load fraction.

### 10.2 Does the wing actually hold 168 kg? — worth the whole design point

The tank capacity is `k_area · (t/c) · S · MAC · chord_frac · span_frac · net_frac`
with `k_area = 0.6062` **measured** by shoelace integration of the pinned coordinates,
`chord_frac = 0.716` **measured** as the section-area fraction of a 15–65% chord box,
and `span_frac = 0.940` **measured** as the volume fraction inboard of 80% semi-span.
Two of the three guessed fractions in the original model have been replaced by
measurements. `net_frac = 0.88` has not.

The margin is **+7.41 kg on 168.01 kg, i.e. 4.4%**. That is thinner than the model's
own uncertainty. And the tank has to be a **sealed integral wet wing** to be that big,
which rules out unsealed printed ribs in the tank bays and adds a sealing programme
the mass model does not carry.

**What settles it:** *measure the tank, do not model it.* The repository already builds
this geometry — `argus7/cad/model.py`, `to_openscad.py`, OpenSCAD installed. Loft the
v3.0 wing, place real front and rear spar webs at their chord stations, subtract skin
laminate, spar-cap volume, rib flanges and the flaperon cutout, and integrate the
remaining cavity. **One measured number replaces three fractions.**

**A related unclosed item:** `research/configuration_hypotheses.md` found that
v1.0's implied fuel density (101.5 kg in 120 L = 0.8458 kg/L) **does not exist** —
mogas E10 is 0.745, Jet-A1 typically 0.804, Jet-A1 maximum spec 0.840. The capacity
model uses 0.78 kg/L. On mogas at 0.745, 160.6 kg needs 216 L against 215 L available,
and the margin **vanishes**. The fuel has not been chosen.

### 10.3 Is the propulsion set right for *this* aircraft? — worth ~1 hour and a gearbox

The propeller was selected against the retired v2.0 design point (§4.5). Against
v3.0's thrust it needs ~2,040 rpm at mid-burn, not 1,900; at the recorded 3.947:1
reduction that puts the crank above the assumed 7,500 rpm rating. **The endurance cost
is small (−0.4 h); the gearing inconsistency is not, because it invalidates the load
fraction the BSFC map is evaluated at.**

**What settles it:** re-run `scripts/prop_refine.py` against `design/argus7_v3.yaml`
with the boom station read from `derive_booms` rather than hardcoded, sweep the
reduction ratio jointly with diameter and pitch, and reconcile
`docs/decisions/2026-08-21-propeller-selection.md` with the design file.

Also unclosed from the propeller work: blade planform and twist are a constant-pitch
idealisation; boom-wake and pusher-installation effects on inflow are not modelled;
and there is no structural or acoustic check on the blade.

### 10.4 The regulatory band has been crossed, and this is the declaration

v1.0 §9's entire regulatory case — EASA Specific category, SORA 2.5, likely SAIL
III–IV, Design Verification Report scope, MoC Light-UAS 2511/2512, ground risk from a
3–4.5 kJ touchdown — is built at **250 kg**. **v3.0 is 312.93 kg, +25%.** Touchdown
energy at MTOW rises from 4.50 to 5.63 kJ, and the canopy that gives 6 m/s grows from
69.5 to 87.0 m².

Gate G6 of the pre-registration says results must be *tagged with their MTOW band, not
silently crossing*. The retired v2.0 crossed it silently at 278 kg. **This report is
the declaration.** Nothing in this repository evaluates what the new band costs in
SORA terms.

**What settles it:** a SORA pre-application, which v1.0 Annex A's rebuilt plan already
puts in Phase 0 month 1 precisely because early bad news is cheap.

### 10.5 The model limits that bound every number in this report

Stated once, in one place, because they bound everything above.

1. **Pure loiter only.** No transit, no climb, no reserve, no wind, no diversion.
2. **The fuselage is fixed** at 3.4 m × 0.48 m for every design point, and
3. **non-wing airframe mass is fixed at 28 kg** regardless of wing size — worth about
   **−9.4 h** on this design point when charged honestly.
4. **The wing mass model is calibrated on a single point**, and 76% of its spar-cap
   term at that point is the fitted constant.
5. **The MTOW scaling exponent is not determined.** Three power-law fits to the same
   quantity give **b = 0.869, 0.998 and 1.452** depending on the subset. An exponent
   that moves that much is a curve fit, not a law. What *is* established: endurance
   increases monotonically with MTOW (≈2.8 d at 180 kg to ≈9.9 d at 600 kg); engine
   power scales as MTOW^0.82 with only 6.1% scatter, **because the climb constraint
   pins it**; and everything else scatters 20–30% because the objective is genuinely
   flat in those directions — the optimiser returned AR 17.0 at 178 kg and AR 29.7 at
   200 kg with sensible endurance both times. It is not failing to converge; there is
   a broad ridge and it lands wherever the sampler looked. The earlier claim of "a
   four-fold decline in marginal returns" was reading a trend into noise and is
   withdrawn.
6. **The optimiser searched with a batched balance model that agrees with the
   authoritative scalar module to ~5% MAC, not exactly.** Search with one, verify with
   the other — which is what was done, and which is why the headline static margin is
   5.79% and not the search's 10.5%.
7. **C_Lmax is a flat 1.60 for every design**, and 3D C_Lmax, tip-stall progression and
   departure behaviour are not modelled anywhere in this stack.
8. **The AVL Oswald surface is not panel-converged**, and its viscous term is
   design-independent and partly double-books against the thickness penalty.
9. **XFOIL transition was measured on the 13.7% section at v1.0's conditions**, at an
   assumed Ncrit of 9, and has not been re-measured for the 19.1% section v3.0 flies.
10. **Nothing has been flight-tested. There is no CFD, no FEA, no structural
    validation of the v3.0 planform, no dynamic stability analysis, no control-power
    or trim-authority check, and no aeroelastic analysis.**

### 10.6 The cheap items that should be done anyway

Each of these is free or near-free, and each is already established by work in this
repository:

- **Close the surviving mutant** — the LE→half-chord sweep sign flip in
  `lift_curve_slope_per_rad` has no test.
- **Add v3.0 to the test parameterisations.** The design point this report publishes is
  unguarded.
- **Generate v3.0 CAD and three-views.** The pipeline exists and is regression-tested.
- **Ø50 × 150 mm spigot instead of two M6 screws** at the tail panel root: 0 kg, 0
  drag, bearing margin ×174.
- **Boom diameter 90 → 110 mm**: +4.6 h net, and it pays a stiffness debt the published
  baseline never paid.
- **Specify a 125 mm/side raked wing tip before the wing plug is cut**: +2.1 h for
  +0.54 kg, CG-neutral. Specified *after* tooling it needs its own mould pair —
  €800–1,500 and 30–50 h instead of €0. **88% of that credit is aspect ratio and area,
  not tip treatment**, and it should be labelled that way.
- **Reduce the tail panel's polar inertia**: 0 kg, 0 drag, ×1.41 on the first torsional
  frequency, which is most of the fix for the one genuine resonance risk on the
  aircraft.
- **Delete the superseded slipstream sentence** from the README's "Verified
  non-issues" — it contradicts the same file's "Known gaps" and it is the sentence that
  generated an entire configuration trade study on a false premise.

---

## Appendix A — Provenance of every headline number

| Number | File | How to reproduce |
|---|---|---|
| Geometry, masses, aero coefficients | `design/argus7_v3.yaml` | `argus7.design.schema.load_design`; every field carries a `derived` / `assumption` / `report-§N` provenance tag, and a test asserts none is untagged |
| Span, chords, MAC, V_h, boom and tail stations | `argus7/design/geometry.py` | closure enforced to 1e−9 |
| 151.951 h endurance | `opt_runs/layout.log` | `argus7.mission.simulate_loiter` on the recorded variables, η_prop 0.858, 120 steps |
| C_D0 0.01588, e 0.8482 | `argus7/opt/coupled.py` | `cd0_from_geometry(S, t/c)`, `oswald_from_planform(AR, λ)` |
| Component C_D0 build-up | `argus7/aero/buildup.py` | `parasite_buildup(design).table()` |
| AVL Oswald surface (45 runs) | `opt_runs/avl_oswald.json`, `e_fit_coef.npy` | `scripts/avl_oswald_sweep.py`, `vendor/bin/avl` |
| XFOIL transition 0.5023 / 0.6051 | `research/riblets_pack.md` §3 | XFOIL 6.99, Ncrit 9, 300 panels, fixed-C_L 1.21 |
| CG, NP, static margin, CG travel | `argus7/analysis/balance.py` | `mass_table`, `cg_travel_table`, `avl_neutral_point` |
| Tank capacity 168.01 kg | `argus7/opt/design_space.py` | `wing_fuel_capacity_kg(S, AR, λ, t/c)` |
| Wing mass 45.39 kg, k_cal 4.2257 | `argus7/opt/design_space.py` | `calibrate()`, `wing_mass_kg(...)` |
| Part-load BSFC 339.5 / 346.6 g/kWh | `argus7/opt/coupled.py`, `argus7/prop/engine.py` | `bsfc_at_load`, `Engine.from_design(d).bsfc_g_per_kwh(...)` |
| Propeller 1.04 m / 2 / 1900 / 0.95 / η 0.858 | `opt_runs/prop_final.json` | `scripts/prop_refine.py` — **note: run against v2.0** |
| Climb power 10.68 kW | `argus7/opt/coupled.py` | `climb_power_required_w(...)` |
| Sensitivity anchors +0.358 / +0.377 / +0.198 d | `docs/decisions/2026-08-20-gauntlet-audit.md` §1 | re-derived here on the v1.0 published polar; both agree |
| Mutation score 12/13 | `opt_runs/mutation.json` | `scripts/mutation_test.py` (**not** `mutation.log`, which is stale) |
| Materials, boom, empennage and configuration findings | `research/*.md` | each carries its own source tags and reproducibility appendix |

## Appendix B — Documents this report supersedes, and documents it does not

**Superseded:**
- `docs/argus7_design_report.md` §§0–8 and §10 — the design point, its performance,
  its stability line, its mass budget, its propulsion set and its sensitivity table.

**Not superseded, and still current:**
- `docs/argus7_design_report.md` **Annex A (premortem)** — a programme risk analysis,
  not a design point. Its failure modes, tripwires, decision rule and adversary
  analysis apply unchanged, and mode #3 ("the engine never delivered the numbers the
  design assumes") has grown in weight, not shrunk.
- `docs/argus7_design_report.md` §9 (regulatory) — **directionally** current, but built
  at 250 kg; see §10.4.
- All eight records in `docs/decisions/` — except that
  `2026-08-21-propeller-selection.md` disagrees with the design file on diameter and
  its clearance figure is computed against the wrong boom station (§4.5).
- All five research packs in `research/`, with the caveat that every structural, boom
  and empennage number in them was computed for the v1.0 configuration.
