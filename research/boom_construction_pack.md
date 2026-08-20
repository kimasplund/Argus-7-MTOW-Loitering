# ARGUS-7 — TAIL BOOM CONSTRUCTION DATA PACK

**Date:** 2026-08-20 · **Scope:** the two tail booms of the 250 kg MTOW / 9.26 m span configuration — construction method, layup, diameter, joints and fatigue life · **Companion to:** `research/materials_pack.md` (§4 boom sizing, §7 adhesives, §6.8 endurance ledger), `docs/argus7_design_report.md` §3/§5, `design/argus7_v1.yaml`

**The question this pack was written to answer:** the sponsor proposes a thin aluminium tube wrapped in carbon and vacuum-bagged. Does the aluminium earn its mass, how thick does the carbon actually need to be for *this* load case, and does hand-laying beat buying?

---

## 0. How to read this

Provenance tags are the same as `materials_pack.md`:

| Tag | Meaning |
|---|---|
| **[DS]** | Manufacturer datasheet, quoted verbatim (unit-converted only) |
| **[M]** | Measured / published experimental data |
| **[CALC]** | Computed here from the report's own geometry and load cases; equations given inline |
| **[EST]** | Engineering estimate — a judgement, not a measurement |
| **[DR]** | Derived from a secondary source that itself cites a primary one |
| **[UNV]** | Unverified — flagged as needing test or vendor confirmation |

**Two exchange rates are used throughout, both taken from `materials_pack.md` §6.8 and not re-derived:**

- **Mass → endurance: 1.5 h per kilogram** (at fixed 250 kg MTOW, added structure displaces fuel) [2][CALC]
- **Drag → endurance: 1.9 h per 0.001 of C_D0** (from the pack's own 0.020 → 0.022 = −3.8 h sensitivity) [2][CALC]

**Where this pack corrects `materials_pack.md`, it says so and shows the arithmetic.** There are three such corrections, in §2.2, §2.3 and §6.1.

**One geometry interpretation is load-bearing and is stated up front.** The task defines each boom as carrying one inverted-V panel, span 0.918 m, dihedral −42°, and the sponsor's item I contrasts the present arrangement (each boom "reacting the panel load in boom torsion individually") with one that "closes a structural loop between the booms". Those two statements are only consistent if **the panels run outboard-and-down from the boom aft ends, with nothing structural between the booms**: root at y = ±0.6206, tip at y = ±1.3028, z = −0.614 m. That is the geometry used here. §8.4 gives the numbers for the alternative (panels inboard-and-down, meeting on the centreline), which changes several conclusions and is flagged as an open question. [EST — inferred, not stated in `argus7_v1.yaml`, whose `tail.dihedral_deg` is itself tagged `assumption`.]

---

## 1. Answer first

**The sponsor is right about the resin, right about galvanic corrosion, right about UD-for-bending, and right that a tube needs woven plies as well. The sponsor is wrong about the aluminium, wrong about the wrap counts, wrong about which orientation the woven plies go in, and wrong about the tail attachment.**

| Sponsor's point | Verdict | The number |
|---|---|---|
| Low-viscosity laminating epoxy, not polyurethane | **Right, and for the stated reasons** | But West 105/205 specifically is a 975 cP marine coating system with a 2.81 GPa modulus [14][DS] against 3.0–3.9 GPa for a structural laminating/infusion epoxy [15][DS]. And **205 is the *fast* hardener** — wrong for a 3.6 m tube. Use a slow structural laminating system |
| Carbon-on-aluminium is a severe galvanic cell; interpose glass | **Right, and it is a real failure mode** | Aerospace practice is exactly this: "carbon fibres must be isolated from aluminium or steel using a barrier (liquid shim, glass ply)" [11][DS]. But **one 80–120 gsm ply is the documented minimum, not a comfortable margin** — the cited flight-hardware practice used *two to three* plies [DR]. See §11.2 |
| 200 gsm ply ≈ 0.25–0.30 mm cured under vacuum | **Right for a mediocre bag, pessimistic for a good one** | 0.25–0.30 mm corresponds to **Vf 0.37–0.44**. A properly bagged wet layup reaches Vf 0.50 → **0.222 mm**, and 0.55 → 0.202 mm [CALC][12][M] |
| UD at 0° between woven outer layers for bending | **Right, decisively** | 6 UD plies + 2 woven give E_x = 91.2 GPa against 59.0 GPa for the same thickness in all-woven — **+55% bending stiffness for the same mass** [CALC] |
| Woven "gives shear resistance" | **Wrong as usually built** | A woven wrapped warp-along-the-tube is a 0/90 laminate with **G_xy = 3.08 GPa**. Bias-wrapped at ±45 the *same cloth* gives **28.6 GPa — 9.3×** [CALC]. The torsional half of the sponsor's argument only exists if the weave is laid at 45° |
| Wrap count 3–4 / 6–8 / 10+ layers | **Wrong — the whole ladder undershoots** | Even **12 layers** on a 90 × 1.5 mm aluminium liner reaches only **90% of the required EI**, at **17.4 kg** for two booms [CALC]. See §4.1 |
| Aluminium tube stays in as a core | **Wrong, and it is the single most expensive decision in the proposal** | The liner alone is **5.5–16.1 kg = 8.3–24.2 hours of endurance**. At equal mass and equal radius, 1.5 mm of aluminium delivers **28.1 kN·m²** of EI where carbon delivers **69.5 kN·m² — 2.47×** [CALC]. See §3 |
| Vacuum bag at 25–29 inHg | **Right, and shrink tape is a genuine alternative for a tube** | Shrink tape is not merely a convenience: it delivers **0.4–1.2 MPa** of consolidation against the **0.1 MPa** ceiling of any vacuum process [13][M][9][DR]. For a 3.6 m tube it is the *better* method, not the fallback |
| Tail attached by two screws and a connector (revised scope) | **Wrong** | Two M6 at 60 mm centres carrying the 330 N·m panel root moment gives **306 MPa of bearing** against a **165 ± 28 MPa design bearing allowable** [19][DR] — a negative margin *before* fatigue. A 50 mm spigot in a 150 mm socket gives **1.76 MPa** [CALC]. See §7 |

**And the propwash premise is geometrically wrong, which is good news.** The propeller tip radius is 0.4065 m; the boom inner surface is at y = 0.5756 m. **The booms clear the prop tip by 169 mm (0.208 D) and clear the contracted slipstream by 183–209 mm at every power setting** [CALC]. The booms are not in the wash. They sit in its acoustic near field, where the differential pressure across a 110 mm cylinder at 70 Hz is ~0.14 × the local SPL — of order 10–30 Pa, not the ~300–560 Pa that a body inside the wake would see [CALC]. That 20–40× difference in excitation is the whole fatigue argument, and it is the strongest reason to keep both the booms *and* the tail panels outboard of the disc (§8.4).

**The headline numbers.**

| | 2-boom mass | Endurance vs the recommendation |
|---|---|---|
| Sponsor's build, sized to actually meet the stiffness requirement (Al 90 × 1.5 + 2.56 mm carbon) | **15.42 kg** (16.02 with fittings) | **−9.4 h (−0.39 d)** |
| Sponsor's build at the sponsor's own "10+ layer heavy duty" wrap count | 18.45 kg on a real 2 mm stock liner, **and 10% short of the required EI** | −14.0 h *and it still does not meet the requirement* |
| Current 90 mm spec, re-sized to the requirement | 10.06 kg (11.72 with fittings) | −3.0 h |
| **Recommended: COTS roll-wrapped 110 mm × 2.0 mm, no liner** | **7.54 kg** (9.20 with fittings) | **datum** |
| Same, hand-laid one-piece over a removable mandrel at Vf 0.50 | 6.61 kg (7.83 with fittings, no splice) | +2.1 h, at ~83 h of extra builder time |
| Same, hand-laid at a realistic bad-day Vf 0.40 | 7.94 kg (9.16 with fittings) | +0.1 h |

[CALC] **The aluminium liner and the inherited 90 mm diameter, together, are worth 9–14 hours — between a third and six-tenths of a day — of endurance.**

---

## 2. What the boom actually has to do

### 2.1 Geometry, restated from the source files

| | Value | Source |
|---|---|---|
| Boom length | 3.6456 m, x = 0.598 → 4.2436 | task / `derive_booms` |
| Boom station | y = ±0.6206 m | `argus7_v1.yaml` (13.4% semi-span) |
| Boom diameter | 90 mm, tagged **`assumption`** | `argus7_v1.yaml` provenance block [3] |
| Wing chord at the boom station | 537.9 mm (LE x = 0.7588, TE x = 1.2968) | [CALC] |
| Let-in | 19.5 mm burial = 21.7% of diameter; **111° wrapped arc**, 87.2 mm of arc length | [CALC] |
| Tail quarter chord | x = 4.0936 | task |
| Panel | S = 0.2808 m² each, span 0.918 m, taper 0.55, AR 3.0 | task |
| Panel mean/root/tip chord | 305.9 / 394.7 / 217.1 mm | [CALC] |
| Panel spanwise centre of pressure | **ȳ = 0.4146 m** from the boom axis | [CALC], trapezoid centroid (b/3)(1+2λ)/(1+λ) |
| Panel lift-curve slope | a_t = 3.563 /rad (a₀ = 5.73, AR 3) | [CALC] |
| S_h,eff check | 2 × 0.2808 × cos²42° = **0.3102 m²** ✓ matches the stated 0.31 | [CALC] |

**The effective cantilever length is 3.05 m, not 3.4 m.** Modelling the boom as a beam on two supports (wing front spar at 25% chord, rear spar at 70% chord, base a = 0.242 m) with a 2.958 m overhang to the tail quarter chord:

- δ_tip = P·L³/(3EI) + P·L²·a/(3EI) → **L_eff = 3.037 m** for deflection
- θ_tip = P·L²/(2EI) + P·L·a/(3EI) → **L_eff = 3.038 m** for slope
- Joint rotation contributes only **7.6%** of tip deflection and **5.2%** of tip slope

[CALC] **L_eff = 3.05 m** is used throughout. `materials_pack.md` used 3.4 m, which is conservative by 40% on moment. The short 0.242 m support base turns out *not* to dominate — a useful negative result, because it means lengthening the let-in buys very little stiffness (§7.2 shows it matters for a different reason).

### 2.2 Correction 1 — `materials_pack.md` understates the tail load by 1.81×

`materials_pack.md` §4.2 computes the tail load as "S_h = 0.31 m², C_N = 1.0 at q_D = 1,890 Pa → limit tail load 586 N, 440 N per boom ultimate" [2].

**0.31 m² is the *effective horizontal* area — the projected area already de-rated by cos²Γ. The aerodynamic load acts on the actual panel area, 0.2808 m² per panel, 0.5616 m² total.** The two conventions differ by exactly 1/cos²42° = **1.812**.

| Case | Per panel, limit | Total, limit |
|---|---|---|
| C_N = 1.0 at V_D = 200 km/h EAS (q_D = 1,890 Pa) | **530.8 N** | 1,062 N |
| C_N = 1.0 at V_A = 177.7 km/h EAS (q_A = 1,493 Pa) | 419.2 N | 838 N |
| Sharp-edged gust at V_C = 150 km/h EAS, U_de = 15.24 m/s, K_g = 0.75, (1−dε/dα) = 0.855 | 249.7 N | 499 N |
| **`materials_pack.md`'s figure** | 293.0 N | 586 N |

[CALC]. V_S = 25.33 m/s EAS at MTOW with C_Lmax 1.6; V_A = V_S√3.8 = 49.37 m/s; V_D = 55.56 m/s EAS is carried over from `materials_pack.md` and is **[EST]** — the report does not state a V_D (§15, open question 1).

**Design case adopted: C_N = 1.0 at V_D → 530.8 N per panel limit, 796 N ultimate.** This is deliberately the conservative envelope. It costs nothing, because §2.4 shows the boom is stiffness-critical by a factor of 3–4 in strength, so load conservatism does not buy mass.

Resolved at the boom (panel normal **n** = (0, sin Γ, cos Γ), force applied at ȳ = 0.4146 m):

| Component, ultimate, per boom | Value |
|---|---|
| Vertical (N cos 42°) | **592 N** |
| Lateral, outboard (N sin 42°) | **533 N** |
| Torque about the boom axis (N · ȳ) | **330 N·m** |
| Tail mass inertia at n_ult = 5.7 (1.6 kg) | 89 N |
| **Total vertical at the tail** | **681 N** |

[CALC] The torque is **2.2× the 150 N·m in `materials_pack.md` §4.2**, for the same reason — the area convention, plus a 0.4146 m arm rather than the 0.33 m assumed there.

### 2.3 Correction 2 — the torque does not cancel, and neither does the side load

For a V-tail on a single fuselage the two panels' torques about the fuselage axis cancel in the symmetric case. **On twin booms they do not.** Each boom individually reacts N·ȳ = 330 N·m ultimate, and the two booms twist in opposite senses. Likewise the two panels' lateral components both point outboard; there is nothing between the boom aft ends to react them, so **each boom carries 533 N of outboard shear at 3.05 m of arm = 1,626 N·m of lateral bending** all the way forward into the wing let-in joint.

Root moments, ultimate, per boom (including 5.7 g boom self-weight):

- Vertical: 681 × 3.05 + w·L²/2 = **2,334 N·m**
- Lateral: **1,626 N·m**
- Resultant: **2,845 N·m** — the lateral component adds **22%** to the root bending

[CALC] `materials_pack.md` §4.2 tabulates only "per-boom ultimate root bending 1,494 N·m". The corrected figure is **1.9× that**. It still does not make the boom strength-critical (§2.4) — but it makes the *wing let-in joint* a much more interesting problem (§7.2).

### 2.4 The boom is stiffness-critical — confirmed, with the corrected loads

At the corrected 2,845 N·m resultant, on a 110 mm × 2.0 mm roll-wrapped tube (I = 9.90×10⁻⁷ m⁴):

σ = M·r/I = 2,845 × 0.055 / 9.90×10⁻⁷ = **158 MPa** against a 620 MPa tensile allowable [4][DS] → **margin 3.9×**

[CALC] Across every candidate in §4 the margin runs **2.7× to 4.3×**. `materials_pack.md`'s finding stands, and it stands against loads 1.9× larger than the ones it used. **E/ρ, not σ/ρ, is the figure of merit. Nothing in this pack is decided by strength.**

What *is* decided by: stiffness (§4), torsional frequency (§5, §6), and joint durability (§7).

### 2.5 The stiffness criterion, stated and justified

Deflection is the wrong criterion. **Rotation is the right one**, because a cantilever's tip *slope* is what changes tail incidence, and the feedback is positive: tail load up → boom bends up → tail leading edge up → more tail load.

Four candidate criteria, evaluated:

| Criterion | Required EI | Binding? |
|---|---|---|
| Divergence margin V_div ≥ 2.0 V_D | 19.4 kN·m² | No |
| Aeroelastic tail-load amplification at V_D ≤ 10% | 53.6 kN·m² | No |
| Ultimate strength, MS ≥ 0 on 620 MPa | ~25 kN·m² | No |
| **Tail rotation ≤ 1.5° at limit load** | **80.7 kN·m²** | **Yes** |

**Why 1.5°.** At limit load the panel operates at C_N = 0.667, i.e. an incidence of 0.667/3.563 = **10.7°**. A NACA 0010 panel at AR 3 and Re ≈ 0.5–0.9 M stalls at roughly 14–16° three-dimensionally [EST]. The reserve is therefore 3.3–5.3°. A boom rotation of 1.5° consumes **28–45% of the tail's remaining incidence reserve** at the moment the tail is working hardest; 2.9° (which is what a 90 × 1.6 mm tube gives) consumes 55–88% and is not defensible. Tail stall at limit load is loss of pitch control.

At EI = 80.7 kN·m² the same criterion delivers, free: **V_div/V_D = 4.08**, and a tail-load amplification at V_D of **1.064**.

| Rotation limit | Required EI |
|---|---|
| 1.0° | 121.0 kN·m² |
| **1.5° (adopted)** | **80.7 kN·m²** |
| 2.0° | 60.5 kN·m² |
| 3.0° | 40.3 kN·m² |

[CALC] For reference, `materials_pack.md`'s recommended 90 × 2.5 mm tube (EI = 62.3 kN·m²) sits at **1.94°** — i.e. the pack implicitly adopted a 2° criterion. This pack tightens it to 1.5° and shows in §9 that the tightening is free if the diameter is opened up.

---

## 3. Question A — does the aluminium tube stay in?

### 3.1 The mass, and what it costs

A 90 mm OD aluminium tube, two booms, 3.6456 m each:

| Wall | Mass, 2 booms | Endurance |
|---|---|---|
| 1.0 mm | 5.50 kg | **−8.3 h** |
| 1.2 mm | 6.59 kg | **−9.9 h** |
| 1.5 mm | 8.21 kg | **−12.3 h** |
| **2.0 mm (the common stock wall)** | **10.88 kg** | **−16.3 h (−0.68 d)** |
| 3.0 mm | 16.14 kg | −24.2 h |

[CALC] at ρ = 2,700 kg/m³ and 1.5 h/kg [2].

Note the supply reality: **90 mm OD aluminium round tube is a stock item at 2 mm, 3 mm and 5 mm wall; 1.0–1.5 mm is not a standard extrusion in that diameter** [21][DS][UNV for the thin walls]. The sponsor's "thin 4 m aluminium tube" is realistically a 90 × 2 mm, i.e. **10.88 kg and 16.3 hours** before a single gram of carbon goes on.

### 3.2 The efficiency argument, at equal mass

For a thin-walled tube, both EI and mass are proportional to wall thickness at the same radius. So the figure of merit is **E/ρ, evaluated at the same radius** — exactly `materials_pack.md`'s finding, applied to the wall itself:

| Material at 90 mm mean diameter | E (GPa) | ρ (g/cm³) | E/ρ |
|---|---|---|---|
| 6061-T6 aluminium | 68.9 | 2.70 | **25.5** |
| Woven 0/90 carbon, wet layup Vf 0.50 | 59.0 | 1.50 | 39.4 |
| Roll-wrapped COTS tube wall | 94.7 | 1.523 | **62.2** |
| 6 UD + 2 woven ±45, wet layup Vf 0.50 | 91.2 | 1.50 | **60.8** |

Stated as the builder will experience it: **1.5 mm of aluminium (1.126 kg/m) buys 28.1 kN·m² of EI. The identical 1.126 kg/m spent on 2.66 mm of wet-layup carbon at the same radius buys 69.5 kN·m² — 2.47×.** At 2.0 mm the comparison is 36.9 vs 89.6 kN·m², the same ratio. [CALC]

There is no configuration in which the aluminium is the efficient way to carry bending in this tube.

### 3.3 The three options, sized to the same requirement

All sized to EI = 80.7 kN·m² (§2.5), 30% ±45 content, wet layup at Vf 0.50:

| Option | Carbon wall | Plies | 2-boom mass | Δ endurance |
|---|---|---|---|---|
| **(i)** Al 90 × 1.5 stays as structural liner | 2.56 mm | 11.5 | **15.42 kg** | **−12.5 h** |
| **(i)** Al 90 × 1.0 stays | 2.96 mm | 13.3 | 13.98 kg | −10.3 h |
| **(ii)** Al used as a *removable mandrel*, hollow CFRP 90 | 3.76 mm | 16.9 | 11.15 kg | −6.1 h |
| **(ii)** Al used as a removable mandrel, hollow CFRP **110** | 1.91 mm | 8.6 | **7.11 kg** | **datum** |
| **(iii)** Sacrificial / collapsible mandrel, hollow CFRP 110 | 1.91 mm | 8.6 | 7.11 kg | datum (−0.79 h drag) |

[CALC] Options (ii) and (iii) are identical structurally; they differ only in how the mandrel comes out.

### 3.4 What the liner genuinely buys, and what that is worth

Three real benefits, honestly valued:

1. **Crush and dent resistance.** A 90 × 1.5 mm aluminium liner will survive being clamped in a workbench vice; a 1.7 mm carbon tube will not. **But this is a local problem with a local fix**: bonded internal bulkheads and an external ±45 over-wrap at the three places that matter (the two let-in ends and the tail joint). Estimated **0.20 kg per boom** [EST], against 8.21 kg for the liner. **The liner is a 40× over-solution to a local problem.**
2. **It simplifies the wing let-in joint.** True, but only marginally: the let-in reacts 2,334 N·m over 538 mm as a 4,338 N couple, which even in a bonded 111° saddle is **0.185 MPa** of bond shear [CALC] — trivial against EA 9394's 28.9 MPa [6][DS]. What the joint actually needs is hoop restraint against the *lateral* couple (§7.2), which a metal liner does not provide either. **The liner does not solve the joint's real problem.**
3. **It is a free, straight, round, 4 m mandrel that you do not have to make.** This is the strongest argument in the proposal and it is a good one — but it is an argument for using the aluminium as a **mandrel**, not for leaving it in.

**Galvanic corrosion is a fourth, negative consideration that the sponsor identified correctly but under-weighted.** A permanent carbon/aluminium couple sealed inside a closed tube for a 2,000-hour airframe life is an inspection-impossible, repair-impossible interface. If a single glass ply is locally bridged by a stray carbon tow — which is exactly what happens at a wrap seam — the resulting cell is buried where nobody can see it. **Removing the aluminium removes the failure mode entirely.** That is worth more than the small probability-weighted mass it saves.

### 3.5 How to get a 3.65 m mandrel out

The extraction problem is real but solved industrially, and the mechanism is favourable:

- **Differential thermal contraction.** Aluminium's CTE is 23.6 µm/m·K; a UD-dominated carbon tube's hoop CTE is ~10–15 µm/m·K [EST]. Cooling from a 60 °C post-cure to 20 °C opens a diametral clearance of (23.6 − 12) × 10⁻⁶ × 40 × 90 mm ≈ **0.042 mm**. Small, but in the right direction.
- **Industrial practice runs it the other way and it works better:** roll-wrap production extracts the mandrel "while the tube is still slightly warm — typically 40–50 °C — when the differential thermal contraction between mandrel and composite provides the maximum extraction force reduction" [10][DR]. Chilling the mandrel (dry ice down the bore) while the tube is warm is the solo-builder version.
- **Taper.** Production mandrels are tapered ~0.1–0.2 mm/m. A parallel aluminium tube is not. **Mitigation: 2 layers of 25 µm PTFE film or FEP release film wrapped over the mandrel, spiral-wound with a 50% overlap and left with a tail to pull.** The film both releases and, when pulled, breaks the seal along the whole length.
- **Fallback that always works: cut the mandrel out.** Sacrifice the aluminium tube; slit it lengthwise from the ends with a long-reach cutter, or simply accept a €60–120 mandrel as consumable per boom. At €120/boom this is cheaper than one hour of a contractor's time.

### 3.6 Recommendation on question A

**Use the aluminium tube as a mandrel with release film, and remove it. Do not leave it in.**

- **Cost of leaving it in:** 8.21 kg (at 1.5 mm) to 10.88 kg (at the real 2 mm stock wall) = **12.3 to 16.3 hours of endurance**, plus a permanently buried galvanic interface, plus more carbon on top than the hollow tube needs because the aluminium is stiffness-inefficient.
- **Cost of taking it out:** roughly 2–4 hours of extraction work per boom, a €60–120 mandrel that may be consumed, and 0.4 kg of local internal reinforcement across both booms.
- **And if it will not come out:** you have lost the mandrel, not the boom. Slit it and pull it in pieces.

**The exchange rate is 30 hours of endurance per hour of extraction work.** [CALC]

---

## 4. Question B — wall thickness from the load case

### 4.1 What the sponsor's wrap counts actually deliver

On a 90 × 1.5 mm aluminium liner, using the sponsor's own 0.275 mm cured ply thickness and woven cloth wrapped 0/90 (the conventional way):

| Sponsor's band | Carbon wall | EI (kN·m²) | % of the 80.7 required | GJ | 2 booms | Tail rotation at limit |
|---|---|---|---|---|---|---|
| bare liner, no carbon | — | 28.1 | 35% | 21.2 | 8.21 kg | 4.30° |
| **3 layers** "light duty" | 0.82 mm | 40.2 | **50%** | 21.4 | 10.58 kg | 3.01° |
| 4 layers | 1.10 mm | 44.0 | 55% | 21.5 | 11.37 kg | 2.75° |
| **6 layers** "general structural" | 1.65 mm | 51.5 | **64%** | 21.6 | 12.91 kg | 2.35° |
| 8 layers | 2.20 mm | 58.7 | 73% | 21.8 | 14.44 kg | 2.06° |
| **10 layers** "heavy duty" | 2.75 mm | 65.6 | **81%** | 21.9 | 15.94 kg | 1.85° |
| 12 layers | 3.30 mm | 72.2 | 90% | 22.0 | 17.43 kg | 1.68° |

[CALC]

**Three things fall out of this table and all three are decisive:**

1. **The ladder never arrives.** Twelve layers — 50% more than the top of the sponsor's "heavy duty" band — still reaches only 90% of the required EI, at **17.4 kg for two booms**. The recommended hollow 110 mm tube reaches 100% at **7.5 kg**. The proposal is not slightly heavy; it is **2.3× the mass and still short**.
2. **The sponsor's intuition about "still noticeably flexible over 4 m" is correct and well-calibrated.** 3 layers gives 3.0° of tail rotation. The intuition is right; only the conclusion drawn from it ("use more layers") is wrong. The right conclusion is "use a bigger tube".
3. **GJ barely moves — 21.2 → 22.0 kN·m² across the whole ladder.** Because the woven is at 0/90 (G = 3.08 GPa), *all* of the torsional stiffness is coming from the aluminium liner. Adding twelve plies of carbon adds **4%** to torsional stiffness. This is the single clearest demonstration that the weave orientation, not the weave count, is what matters (§5).

### 4.2 The layup that does meet the requirement

Classical lamination theory, ply properties from micromechanics at the stated Vf (E_f1 = 230 GPa, E_m = 3.2 GPa, Halpin-Tsai transverse and shear, 5% crimp knockdown on woven warp/weft):

| Stack (200 gsm plies) | t at Vf 0.50 | E_x (GPa) | G_xy (GPa) | E/ρ | %0° |
|---|---|---|---|---|---|
| 6 woven, 0/90 | 1.33 mm | 59.0 | **3.08** | 39.4 | 50 |
| 6 woven, ±45 | 1.33 mm | 11.2 | **28.60** | 7.5 | 0 |
| 2 woven±45 + 4 UD0 + 2 woven±45 *(sponsor's stack, charitable reading)* | 1.78 mm | 64.7 | 15.84 | 43.2 | 50 |
| 2 woven0/90 + 4 UD0 + 2 woven0/90 *(literal reading)* | 1.78 mm | 88.0 | **3.08** | — | — |
| **1 woven±45 + 6 UD0 + 1 woven±45** | **1.78 mm** | **91.2** | 9.46 | **60.8** | 75 |
| 2 woven±45 + 6 UD0 + 2 woven±45 | 2.22 mm | 75.4 | 13.29 | 50.2 | 60 |
| COTS roll-wrapped reference [4][DS] | — | 94.7 | 11.68 | 62.2 | ~60 |

[CALC] from [4][7]

**The recommended hand layup, if hand-laying:**

```
110 mm mandrel, inside → outside:
  1 × 200 gsm 3k twill, BIAS-WRAPPED at ±45        0.22 mm   torsion, inner surface
  6 × 200 gsm UD carbon at 0° (staggered seams)    1.33 mm   bending
  1 × 200 gsm 3k twill, BIAS-WRAPPED at ±45        0.22 mm   torsion, abrasion, outer surface
                                                   ────────
                                        8 plies    1.78 mm at Vf 0.50
```

- **EI = 80.7 kN·m²** ✓ (meets §2.5 exactly at Vf 0.50)
- GJ = 16.7 kN·m²
- σ_ult = 183 MPa on a 620 MPa allowable → **MS 3.4** ✓
- Shell buckling: σ_cr ≈ 0.3·√(E_x E_y)·t/R = **520 MPa** → MS 2.8 ✓
- **0.908 kg/m → 3.31 kg per boom, 6.62 kg for two**

**A result worth stating on its own, because it inverts the usual worry about wet layup:**

| Vf achieved | Cured wall | E_x | EI (= E·I) | 2-boom mass |
|---|---|---|---|---|
| 0.55 | 1.62 mm | 100.1 GPa | 81 kN·m² | 6.12 kg |
| **0.50** | 1.78 mm | 91.2 GPa | 81 kN·m² | 6.61 kg |
| 0.45 | 1.98 mm | 82.3 GPa | 81 kN·m² | 7.20 kg |
| 0.40 | 2.22 mm | 73.5 GPa | 81 kN·m² | 7.94 kg |

[CALC] **For a fixed ply count, EI is essentially independent of fibre volume fraction** — E falls and t rises in near-exact compensation (E·t = 162 ± 1 kN/m across the whole range). **A resin-rich layup does not cost you stiffness. It costs you mass, at 1.5 h/kg.** A bad bag that lands at Vf 0.40 instead of 0.50 costs **1.33 kg = 2.0 hours** and nothing else. That is a much more forgiving failure mode than the folklore suggests, and it means the layup schedule should be written in **plies, not millimetres**.

### 4.3 Strength check, as the secondary criterion it is

At the recommended 110 × 1.78 mm hand layup, ultimate resultant root moment 2,845 N·m:

| Check | Value | Allowable | MS |
|---|---|---|---|
| Axial bending stress | 183 MPa | 620 MPa (tension) [4][DS] | **3.4** |
| Torsional shear, T = 330 N·m | 4.9 MPa | ~70 MPa (±45 laminate) [EST] | **14** |
| Local shell buckling in bending | 183 MPa | 520 MPa | 2.8 |
| Brazier ovalisation | — | not critical at t/R = 0.032 | — |

[CALC] **Nothing is close.** This is the boom's defining characteristic and every decision in this pack respects it.

---

## 5. Question C — torsion, ±45 content, and where "only half the fibres run lengthwise" gets decided

### 5.1 The sponsor's point 4 is half right, and the wrong half is the important one

> "woven twill/plain gives hoop strength and shear resistance but only half the fibres run lengthwise"

**Hoop strength: right.** A 0/90 woven contributes E_y ≈ 59 GPa in hoop, which is what resists crushing at clamps and local ovalisation.

**Shear resistance: wrong as built.** A woven cloth wrapped with its warp along the tube axis produces a **0/90 laminate**, whose in-plane shear modulus is just the ply's G₁₂ = **3.08 GPa**. That is *lower than epoxy-dominated*; it is 8× worse than aluminium (25.9 GPa) and 3.8× worse than the COTS roll-wrapped tube (11.68 GPa) [4][DS]. **The same cloth bias-wrapped at ±45 gives 28.6 GPa — a factor of 9.3, for zero mass change.**

**This is the single cheapest correction in the pack.** Cut the woven on the bias (or spiral-wrap it at 45°). Nothing else changes.

### 5.2 How much ±45 the boom actually needs

The torsional requirement is not strength (§4.3 shows a margin of 14×). It is **frequency**. The boom's first torsional mode is:

f_t1 = (1/2π)·√( (GJ/L) / (J_tail + J_boom·L/3) )

with **J_tail = m_panel·b²/3 = 0.365 kg·m²** about the boom axis — a big polar inertia, because a 1.3 kg panel hangs 0.918 m off the axis. At D = 110 mm with the wall always re-sized to hold EI = 80.7 kN·m²:

| Stack | %±45 | wall | E_x | G_xy | GJ (kN·m²) | **f_t1** | 2 booms |
|---|---|---|---|---|---|---|---|
| 6 UD 0° only | 0% | 1.37 mm | 116.6 | 3.08 | 4.3 | **9.8 Hz** | 5.13 kg |
| **1w±45 + 6UD + 1w±45** | **25%** | 1.78 mm | 91.2 | 9.46 | 16.7 | **19.4 Hz** | 6.61 kg |
| 2w±45 + 6UD + 2w±45 | 40% | 2.17 mm | 75.4 | 13.29 | 23.5 | 23.0 Hz | 8.05 kg |
| 4w±45 + 6UD + 4w±45 | 57% | 2.93 mm | 57.1 | 17.66 | 49.9 | 33.3 Hz | 10.77 kg |
| 6w±45 + 6UD + 6w±45 | 67% | 3.63 mm | 46.9 | 20.09 | 69.1 | 39.2 Hz | 13.28 kg |
| **COTS roll-wrapped** | ~30% | 1.71 mm | 94.7 | 11.68 | 19.9 | **21.1 Hz** | **6.45 kg** |

[CALC]

**The trade is brutally non-linear and this is the number that decides it:** going from 25% to 57% ±45 raises the torsional frequency by 1.7× and costs **4.16 kg = 6.2 hours of endurance**. Buying torsional frequency with ±45 plies is the most expensive lever on the boom, because every ±45 ply displaces a 0° ply and forces the wall thicker to hold EI.

**Two cheaper levers exist and both should be used before adding a single ±45 ply:**

- **Halve the tail panel's polar inertia** → f_t1 × 1.41, free. The panel's inertia is m·b²/3; moving mass inboard (root-mounted servo instead of mid-span, lighter tip, no tip weight) attacks b² directly. A 0.65 kg panel instead of 1.3 kg gives the same 1.41× as adding 4 kg of ±45.
- **Close the tail loop** → f_t1 × 1.30 to 2.41 for 0.34–0.55 kg (§8).

**Recommendation: 25–30% ±45, i.e. one bias-wrapped woven ply inside and one outside a 6-ply UD core.** That is what the COTS roll-wrapped tube already is, and it is not a coincidence — it is where the trade lands.

### 5.3 Divergence and classical flutter

**Divergence** at the recommended stiffness: q_div = 1/(S_h,eff,boom · a_t · K_θ) with K_θ = L²/(2EI) = 5.66×10⁻⁵ rad/N →

q_div = 31,500 Pa → **V_div = 4.08 V_D = 816 km/h EAS**. [CALC] Not a constraint.

**Boom torsion does not feed pitch.** A rotation φ about the boom's longitudinal axis leaves the panel's chord line parallel to the flow; the panel's angle of attack is unchanged (Ω·**s** = 0, since the panel span vector has no x-component). Boom torsion changes the panel's *dihedral*, which is a lateral-directional effect, not a pitch one. **So the classic wing bending–torsion flutter mechanism is not the one to worry about here.** The two mechanisms that are:

1. **Symmetric boom bending + tail pitch.** The elastic axis is the boom axis. If the boom axis passes through the panel's quarter-chord line, the aerodynamic pitching moment about the elastic axis is ~zero and the only coupling is inertial. **Design rule: put the boom axis at or slightly ahead of the panel's 25% chord line, and mass-balance the panel so its CG is at or ahead of the boom axis.** With those two conditions the binary system is flutter-free to first order, at zero mass cost if done at the design stage. [DR — standard practice; the mass-balance rule is the same one that governs control surfaces]
2. **Ruddervator rotation mode.** For a UAV this is the realistic flutter risk, because the "hinge stiffness" is a servo gearbox with backlash. **Mass-balance the ruddervator about its hinge line, use a zero-backlash linkage, and keep the surface-rotation frequency above the boom's first torsion mode (19–21 Hz).** [DR]

Neither of these is a boom-layup question. They belong on the tail drawing, and §7 argues they are now *more* important because the tail has become a removable item.

---

## 6. Question G — boom frequencies versus blade-passage excitation

### 6.1 Correction 3 — the booms are not in the slipstream

| | Value |
|---|---|
| Propeller diameter, from `argus7_v1.yaml` | 0.813 m → tip radius **0.4065 m** |
| Boom axis | y = 0.6206 m |
| Boom inner surface (90 mm) | y = 0.5756 m |
| **Radial clearance, boom surface to prop tip** | **169 mm = 0.208 D** |
| Slipstream radius aft of the disc, loiter (T = 91 N, a = 0.078) | 0.393 m → boom clear by **183 mm** |
| Slipstream radius aft of the disc, full power SL (T = 442 N, a = 0.298) | 0.367 m → boom clear by **209 mm** |
| Tail panels (outboard-and-down): minimum radius from the thrust axis | **0.621 m** — entirely outside the disc |

[CALC] Slipstream contraction from R_w/R = √((1+a)/(1+2a)).

**The booms and the tail are outside the propeller slipstream at every power setting, and the slipstream contracts *away* from them as power increases.** The premise "the booms extend aft of the prop and sit in its slipstream, excited continuously" is geometrically incorrect. The excitation is real but it is **near-field acoustic, not wake impingement**, and the difference in amplitude is 20–40×:

| Location | Unsteady pressure at BPF |
|---|---|
| **Inside the slipstream**, blade-wake velocity defect ±10–20% at q_slip = 1,404 Pa | **281–562 Pa** [CALC] |
| **Outside at 0.21 D tip clearance**, near-field SPL 130–140 dB | 63–200 Pa SPL, but the acoustic wavelength at 70 Hz is 4.9 m against a 0.11 m cylinder, so the *differential* across the boom is (kD)·p = 0.14 p ≈ **9–28 Pa** [CALC][EST] |

0.208 D of tip clearance is also right at the conventional design floor — propeller-to-structure clearance guidance sits at **≥ 0.2 D** for exactly this reason [16][DR]. ARGUS-7 passes, with nothing to spare. **Any change that moves a boom, a tail panel or a cross-member inboard of r = 0.45 m converts a 20 Pa problem into a 400 Pa problem, and every conclusion in this section reverses.** That is the strongest single argument in this pack for keeping the tail panels outboard (§8.4).

### 6.2 The excitation comb is not a single frequency, and it is not currently determinable

| Source | At prop 2,100 rpm (the yaml value) | At the loiter rpm a fixed-pitch prop would actually turn |
|---|---|---|
| Prop 1P (shaft order) | 35.0 Hz | ~23 Hz |
| 2-blade BPF | **70.0 Hz** | ~47 Hz |
| 3-blade BPF | **105.0 Hz** | ~70 Hz |
| Engine firing (single-cyl 4-stroke, 4,830 rpm) | 40.25 Hz | ~27 Hz |
| Engine 1st order | 80.5 Hz | ~54 Hz |
| 2× BPF (2-blade) | 140 Hz | ~93 Hz |

**And the propulsion numbers do not close, which makes this worse.** A 0.813 m propeller at 2,100 rpm absorbing 17 kW at sea level requires a power coefficient of

C_P = P/(ρ n³ D⁵) = 17,000/(1.225 × 35³ × 0.813⁵) = **0.911**

[CALC] Realistic maximum C_P for a two-blade propeller at these advance ratios is 0.15–0.25; even a heavily loaded four-blade tops out near 0.4. **The report's prop diameter, reduction ratio, rpm and power are mutually inconsistent by roughly 4× in C_P.** Either the reduction ratio is nearer 1.5:1 (giving ~3,200 prop rpm and a 107 Hz two-blade BPF), or the propeller is larger, or 17 kW is never delivered at 2,100 rpm. Until that is resolved, **the blade-passage frequency is uncertain by roughly ±50%, from about 47 Hz to about 107 Hz.** Logged as open question 2.

### 6.3 The mode map

Euler–Bernoulli beam FE of the actual boom (x = 0.598 → 4.2436, pinned at the wing front and rear spar stations, 1.6 kg tail mass and 0.174 kg·m² pitch inertia at x = 4.0936), plus a torsional rod model fixed at the mid-let-in station with the 0.365 kg·m² panel inertia at the tail:

| Build | f_b1 | f_b2 | f_b3 | f_t1 |
|---|---|---|---|---|
| Al 90 × 1.5 liner + 8 plies carbon | 6.8 | **48.0** | 124.0 | 27.5 |
| Al 90 × 2.0 liner + 8 plies carbon | 7.0 | **47.9** | 125.3 | 29.7 |
| COTS 90 × 1.6 | 7.1 | **57.4** | 139.9 | 15.1 |
| COTS 90 × 2.5 (`materials_pack.md`'s pick) | 8.1 | **61.5** | 153.2 | 18.6 |
| COTS 100 × 2.0 | 8.8 | **67.6** | 167.3 | 19.7 |
| **COTS 110 × 2.0 (recommended)** | **10.0** | **75.8** | **188.5** | **22.7** |
| COTS 120 × 1.6 | 10.5 | **81.2** | 200.5 | 23.3 |
| Hand-laid 110 × 1.78 (8 ply) | 9.5 | 74.0 | 182.4 | 19.4 |

[CALC] Higher modes: f_b4 ≈ 300 Hz, f_b5 ≈ 540 Hz; the lowest shell ovalling mode of a 110 × 2 mm carbon tube is **>400 Hz** [CALC], so no shell mode is in play.

**Two scaling laws govern the design space and both matter:**

- **f_bending ∝ D at constant EI.** For a thin tube, EI ∝ D³t and mass ∝ Dt, so at fixed EI the frequency scales linearly with diameter and is independent of wall thickness. Across D = 80 → 140 mm, f_b2 moves only **56 → 86 Hz**.
- **f_torsion is completely insensitive to diameter at constant EI**, because GJ tracks EI for a given laminate and the tail inertia is fixed: 18.5 Hz at every diameter in the sweep. Only the ±45 fraction and the tail's polar inertia move it.

### 6.4 The separation margin, the criterion, and the honest verdict

**Criterion adopted: ±20%.** This is the standard resonance-avoidance separation — "many major vibration problems can be avoided by making sure the excitation frequency does not fall within a 20 percent range around the natural frequencies" [17][DR], and it is the margin implicit in FAA AC 20-66B's treatment of propeller-induced vibration and the associated fatigue evaluation [16][DR].

Applying it to the 2,100 rpm comb gives keep-out bands of 29.8–46.3 Hz (prop 1P + engine firing), **59.5–92.6 Hz** (2-blade BPF + engine 1st order), 89.3–120.8 Hz (3-blade BPF) and 119–185 Hz (2×BPF + engine 2nd order). The clear windows below 200 Hz are **< 29.8 Hz**, **46.3–59.5 Hz** and, with a two-blade propeller only, **92.6–119 Hz**.

| Mode, recommended 110 × 2.0 build | Frequency | Verdict |
|---|---|---|
| **f_b1** | 10.0 Hz | **PASS** — 3.5× below the lowest comb line, and 5× above a realistic 2 Hz autopilot pitch bandwidth |
| **f_t1** | 22.7 Hz | **PASS at 2,100 rpm** (35% clear of 35 Hz and 44% clear of 40.25 Hz) — **FAILS at the loiter rpm**, where prop 1P is ~23 Hz. See below |
| **f_b2** | 75.8 Hz | **FAILS** — 8% above 70 Hz, 6% below 80.5 Hz. There is no escape by diameter: to reach the 92.6–119 Hz window needs D ≈ 137–176 mm |
| **f_b3** | 188.5 Hz | PASS — 17% above 161 Hz, marginal |

**So the frequencies cannot all be separated at any sensible diameter, and it is more honest to say so than to pretend a layup change fixes it.** What remains is to compute the consequence.

### 6.5 The consequence, computed

Forced-response of the FE model to a harmonic differential pressure applied over the 1.2 m of boom nearest the propeller plane, with a CFRP structural damping ratio ζ = 0.01–0.05 (Q = 10–50):

| Excitation | Static root stress | At resonance, Q = 10 | Q = 25 | Q = 50 |
|---|---|---|---|---|
| **20 Pa** (near field, computed §6.1) | 0.42 MPa | 4.2 MPa / 0.004% | 10.4 MPa / 0.011% | 20.9 MPa / 0.022% |
| 50 Pa | 1.04 MPa | 10.4 MPa / 0.011% | 26.1 MPa / 0.028% | 52.2 MPa / 0.055% |
| 200 Pa | 4.18 MPa | 41.8 MPa / 0.044% | 104 MPa / 0.110% | 209 MPa / **0.221%** |
| **400 Pa** (*if it were inside the slipstream*) | 8.35 MPa | 83.5 MPa / 0.088% | 209 MPa / **0.221%** | 418 MPa / **0.441%** |

[CALC] strain quoted as σ/E_x on the 94.7 GPa laminate.

**The allowable to compare against is the matrix fatigue-limit strain: ε_mf = 0.6% for epoxy resins, below which no damage progression occurs — this is the mechanism that gives CFRP its very-high-cycle behaviour, since matrix micro-cracking is the principal driver of CFRP fatigue failure** [18][M].

| | Peak vibratory strain | Margin to ε_mf = 0.6% |
|---|---|---|
| **As designed (booms outside the slipstream, Q = 25)** | **0.011%** | **55×** |
| Pessimistic (200 Pa, Q = 50) | 0.221% | 2.7× |
| **If a member is placed inside the slipstream at Q = 50** | **0.441%** | **1.4× — not acceptable** |

**Verdict on item G.** The boom's second bending mode will sit inside the blade-passage keep-out band and there is no affordable way to move it. **That is acceptable, and the reason it is acceptable is entirely geometric: the boom is not in the wash.** The vibratory strain is 0.011%, which is 55× below the threshold at which CFRP accumulates matrix damage at all, and 28.4 M or 504 M cycles at a strain that causes no damage per cycle is still no damage.

**The design action that follows is not a layup change. It is three prohibitions:**

1. **Nothing structural inside r = 0.45 m of the thrust axis aft of the prop plane.** This is now a configuration constraint, and it is the reason §8 recommends against a naïve cross-tie at z = 0.
2. **f_b1 must stay below 25 Hz and f_t1 must be resolved against the true loiter rpm once the propulsion set closes** (§6.2). f_t1 = 22.7 Hz against a possible ~23 Hz prop 1P at loiter is a **1% separation for 122 continuous hours** and it is the one genuine resonance risk in the mode map. The fixes, in cost order: reduce the panel's polar inertia (free, ×1.41), close the tail loop (0.4 kg, ×1.30–1.55), add ±45 (4 kg, ×1.7). **Do the first two.**
3. **Measure it.** A single tap test on the finished boom with the tail fitted, and a ground run with an accelerometer at the tail, settles the whole section in an afternoon. Everything above is a model.

---

## 7. Question H — fatigue of the layup and, more importantly, of the joints

### 7.1 The laminate is not the fatigue article; say so and move on

Three load spectra act on the boom:

| Spectrum | Cycles per 112.8 h mission | Peak strain |
|---|---|---|
| Blade-passage vibration (§6.5) | **28.4 M** (2-blade) / 42.6 M (3-blade) | 0.011% |
| Atmospheric turbulence / gust, 0.1–2 Hz | ~10⁵–10⁶ | ~0.03–0.08% [EST] |
| Manoeuvre and recovery | 10²–10³ | up to 0.19% at limit |

[CALC] Against ε_mf = 0.6% [18][M] and a 1-g steady strain of 0.019%, **the laminate has 3× margin at limit load and 55× at the vibratory level.** Carbon/epoxy at these strains is, for practical purposes, fatigue-immune — the same conclusion `materials_pack.md` §8.1 reached for the spar cap, reached here independently for the boom.

**The honest caveat: published CFRP S-N data essentially stops at 10⁷ cycles.** The 504 M-cycle 2,000-hour figure is an extrapolation, and the VHCF literature warns that CFRP shows "no traditional fatigue limit" and a step in the S-N curve in the HCF→VHCF transition [18][M]. The defence is not the extrapolation; it is the 55× strain margin.

### 7.2 The boom-to-wing joint — the one whose failure loses the aircraft

**Geometry.** A 19.5 mm burial of a 90 mm boom gives a contact half-angle of 55.5°, a **111° wrapped arc**, 87.2 mm of arc length and a 74.2 mm chord width, over the 538 mm wing chord at that station. [CALC]

**Vertical loads are trivial.** The 2,334 N·m ultimate vertical moment reacted over the 538 mm let-in is a 4,338 N couple; smeared over the bonded arc it is **0.185 MPa** of adhesive shear against EA 9394's 28.9 MPa [6][DS]. A margin of 156×.

**The lateral load is the problem, and it is the one `materials_pack.md` did not see because it did not have the side-force term (§2.3).** The 1,626 N·m lateral ultimate moment produces a **3,022 N** couple acting to prise the boom sideways out of a 111° open saddle. Over most of that arc the load has a component **normal to the bondline**. EA 9394's T-peel strength is **22 N per 25 mm** [6][DS] — 800× lower than its shear strength. `materials_pack.md` §7.1 states the governing rule for the whole aircraft: *design every bonded joint to work in shear or compression; never let a bondline see peel.* **A 111° saddle carrying a lateral couple violates that rule.**

**The fix, and it is cheap:**

- Two **full-circumference clamped collars**, one at each end of the let-in, each 60–80 mm long: a split aluminium or CFRP ring, bonded *and* through-bolted, that converts the lateral couple into hoop compression and shear rather than bond peel. ~0.15 kg per boom.
- **A ±45 over-wrap** of 3 plies of 200 gsm carbon (or aramid, which is tougher in this role) over the full 538 mm of let-in, taken around 360°. This is `materials_pack.md` §7.2's own prescription for tube-to-fitting joints — "over-wrap tube-to-fitting joints circumferentially to convert peel into hoop tension" [2] — applied to the joint that most needs it. ~0.12 kg per boom.
- **Internal bulkheads** at both ends of the let-in to stop the tube ovalising under the collar. 2 × 30 g of Rohacell-and-carbon disc per boom.
- **A glass ply** between the carbon boom and any aluminium collar (§11.2).

Total local reinforcement at the wing joint: **≈ 0.20 kg per boom**, 0.60 h of endurance for both booms — against a boom-loss failure mode.

**Fatigue verdict on the wing joint.** Bonded, in shear, at 0.185 MPa ultimate = 0.6% of static: adhesive fatigue thresholds sit near 20–30% of static shear [EST][DR], so the margin is ~40×. **The bonded path is fine. The bolted path through the collars must be preloaded and close-fit, not clearance-fit** (§7.3).

### 7.3 The boom-to-tail quick-release — two screws will not do

The sponsor's revised scope makes the tail a serviceable item: "two screws and a quick connector". The panel root reactions the joint must carry are **796 N of shear and 330 N·m of bending, ultimate** (220 N·m limit).

| Arrangement | Bolt shear | Bearing on the laminate | vs static ~600 MPa | vs **design allowable 165 ± 28 MPa** [19][DR] |
|---|---|---|---|---|
| **2 × M6 at 60 mm centres** | 5,500 N | **306 MPa** | MS 1.96 | **MS 0.54 — FAILS** |
| 2 × M6 at 120 mm centres | 2,750 N | 153 MPa | MS 3.93 | MS 1.08 — marginal |
| 4 × M6 in a 120 × 60 pattern | 1,375 N | 76 MPa | MS 7.85 | MS 2.17 |
| 2 × M8 at 150 mm centres, 4 mm laminate | 2,200 N | 69 MPa | MS 8.73 | MS 2.39 |
| **Spigot Ø40 × 120 mm engagement** | — | **3.44 MPa** | MS 175 | MS 48 |
| **Spigot Ø50 × 150 mm engagement** | — | **1.76 MPa** | MS 341 | MS 94 |
| Full 110 mm socket × 150 mm engagement | — | 0.80 MPa | MS 750 | MS 206 |

[CALC], peak spigot bearing from p = 6M/(d·ℓ²) for a linear bearing distribution.

**Two clearance-fit M6 screws at 60 mm centres are not a viable tail attachment**, before fatigue is considered. With fatigue considered they are worse: composite bolted joints fail by progressive **hole elongation and fretting**, a four-stage compressive damage accumulation (onset, growth, local fracture, structural fracture) in which preload is lost as the hole wears, which accelerates the wear [19][M]. There is no mechanism by which a clearance-fit shear bolt in a composite laminate survives 28 M cycles at 60–100 MPa of bearing without measurable elongation.

**Recommendation, in preference order:**

1. **Spigot-and-socket, with the screws taking only retention.** A Ø50 × 150 mm spigot bonded into the panel root, entering a socket bonded into the boom. The moment is reacted as **1.76 MPa** of distributed bearing over a large area; the two screws see only axial pull-out and a small torque, not the 5.5 kN couple. **This is standard removable-tailplane practice on gliders and it costs nothing extra to build.** Fit a single spring-plunger or a captive clamp bolt, plus one 3-pin connector for the ruddervator servo.
2. If the sponsor insists on a purely bolted joint: **4 × M8, close-fit (H8/h7) with bonded-in aluminium or titanium bushes**, spread over ≥ 150 × 80 mm, with a glass isolation ply under every bush (§11.2), at a controlled preload. This works but is heavier, fiddlier and slower to service than the spigot.
3. **Never** two screws.

**Relocating the quick-release, as the coordinator suggests.** The right answer is (i): **the release should be outboard of the fatigue-critical structure, but the fatigue-critical structure at this joint is the *panel root*, not the boom.** Placing the release at the panel root is correct — provided it is a spigot, not a bearing joint. Placing it further outboard (part-span) would put a joint in the middle of a lifting surface for no gain.

**If a bolted joint is used anyway, here is the life-limit regime**, and it should be written on the drawing:

- Inspect at **25 flight hours** after first fit, then every **50 flight hours**.
- Measure hole elongation with a pin gauge. **Replace the panel root fitting at 2% elongation** — 0.12 mm on a 6 mm hole, 0.16 mm on an 8 mm hole — which is the conventional bearing-failure criterion [19][DR].
- Re-torque at every inspection; a falling torque reading is the leading indicator and it precedes measurable elongation.
- **Log it as a life-limited item.** [EST for the intervals — they are engineering judgement anchored on the four-stage damage model in [19], not measured on this joint. Open question 6.]

### 7.4 The framing the sponsor should hear

**Making the tail sacrificial is a sound decision, and it does reduce risk — but it moves risk, it does not delete it.** A tail panel that departs in flight is a recoverable event only if the *boom* and the *joint* are undamaged. A quick-release joint that wears is a joint that transmits its wear into the boom's end fitting, and a boom failure is not recoverable. The correct expression of "sacrificial tail" is therefore:

> The **panel** is sacrificial. The **spigot, the socket, the boom end fitting and the boom** are permanent, and the joint must be designed so that all the wear happens in the removable half.

Practically: put the bushes, the threads and the wear surfaces **in the panel-root fitting**, which is replaced with the panel. The boom's socket should be a plain bonded CFRP or hard-anodised aluminium bore with nothing in it that can wear out.

---

## 8. Question I — does closing the tail loop help?

### 8.1 What "closing the loop" does, mechanically

With the panels outboard-and-down (§0), the boom aft ends are free. Adding a spanwise member between them (ℓ = 1.2412 m) does three distinct things, of very different value:

**(a) It reacts the lateral tail load panel-to-panel.** The two panels each push outboard with 533 N ultimate; a tie takes that in tension and deletes the 1,626 N·m of lateral bending from both booms and from the wing let-in joint (§7.2).

Root moment: **2,845 N·m open → 2,334 N·m closed = 17.9% lower.** [CALC]

Converted to life through S = S₀N^(−1/m):

| S-N exponent m | Applicable to | Life multiplier |
|---|---|---|
| 6 | bonded and bolted joints, matrix-dominated | **×3.3** |
| 8 | composite bolted joints | ×4.9 |
| 10 | mixed | ×7.2 |
| 14–20 | UD carbon in tension | ×16 – ×52 |

[CALC][EST for the exponents — CFRP S-N is conventionally fitted linear-log rather than as a power law, so these are indicative]

**(b) It adds a rotational restraint against boom torsion at the aft end**, in parallel with the boom's own GJ/L = 6,983 N·m/rad. For symmetric loading the two boom-end rotations are equal and opposite, so the tie contributes k = 2EI_tie/ℓ:

| Tie | k_tie | Boom's share of the torque | **f_t1** | Mass | Faired drag |
|---|---|---|---|---|---|
| 40 × 1.5 mm carbon tube | 4,882 N·m/rad | 59% | 21.1 → **27.5 Hz** (×1.30) | 0.34 kg (−0.5 h) | −1.9 h |
| **50 × 1.5 mm** | 9,755 | **42%** | → **32.7 Hz** (×1.55) | 0.43 kg (−0.6 h) | **−2.4 h** |
| 60 × 1.5 mm | 17,113 | 29% | → 39.2 Hz (×1.86) | 0.51 kg (−0.8 h) | −2.9 h |
| 80 × 1.2 mm | 33,447 | 17% | → 50.8 Hz (×2.41) | 0.55 kg (−0.8 h) | −3.9 h |

[CALC] Faired drag assumes a 3:1 streamline fairing at C_D = 0.08 on frontal area.

**(c) It raises the antisymmetric boom modes and stiffens the whole empennage in yaw** — qualitatively valuable, not quantified here.

### 8.2 What it costs, and the cost that kills the naïve version

- **Mass:** 0.34–0.55 kg for the member, plus two end joints at ~0.10 kg each = **0.54–0.75 kg → 0.8–1.1 h**.
- **Drag, faired:** **1.9–3.9 h**. This dominates.
- **Drag, unfaired round tube:** at C_D = 1.0 on frontal area, a bare 40 mm tube across 1.24 m is ΔC_D0 = 0.0127 → **−24.2 hours**. **A bare cross-tube is a mission-ending drag item. If a tie is fitted it must be faired, full stop.** [CALC]
- **Two more joints**, in a load path that is now primary, and both of them in the region where §6 wants nothing.
- **And the fatal one: a member at z = 0 spanning y = −0.62 to +0.62 passes straight through the propeller slipstream** (radius 0.37–0.39 m). §6.5 shows that puts it at 281–562 Pa of blade-passage excitation instead of ~20 Pa, and at Q = 50 that reaches 0.44% strain — within 1.4× of the matrix fatigue limit. **The cross-tie would become the fatigue article of the aircraft.**

### 8.3 Recommendation on question I

**Do not fit a bare cross-member at the tail. The physics says the loop is worth closing; the geometry says this is the wrong place to close it.**

The ledger for a 50 mm faired tie: **+3.3× to +7.2× joint life and f_t1 × 1.55 (which fixes the one genuine resonance risk in §6.4), against −3.0 to −3.5 hours of endurance and a new member sitting in the propwash.**

**Three better ways to get the same benefits:**

1. **Close the loop at the wing, not at the tail.** A stiff spanwise carry-through between the two boom collars, inside the wing at y = ±0.62 — where there is already structure, no drag and no propwash — takes the lateral couple out of the wing skin and into a designed member. It does not reduce boom bending (nothing can; the load has to travel forward), but it removes the peel path identified in §7.2 and costs ~0.4 kg and zero drag. **Do this regardless.**
2. **Buy the torsional frequency by reducing the panel's polar inertia instead** (§5.2): ×1.41 for free, versus ×1.55 for 3.0–3.5 hours.
3. **If the loop must be closed at the tail, close it with tail area, not with a strut.** A centre section between the boom ends at the tail station could carry the whole S_h,eff = 0.31 m² on a 1.2412 m span at a 0.25 m chord, turning the inverted-V into an H- or U-tail; the panels then become outboard fins. The tie then costs no *net* drag because it replaces area that had to exist anyway. **But it puts the horizontal surface directly in the slipstream** — good for elevator authority, and squarely into the 400 Pa excitation regime, so it would have to be sized as a fatigue article. That is a tail redesign, not a boom decision, and it is logged as open question 4.

**Bottom line: the sponsor's instinct that closing the loop helps fatigue is correct in principle and the effect is real but modest (×3–7 on joint life, ×1.55 on the torsional frequency). Given that the boom's own laminate has a 55× strain margin and the joint problem is far better solved by replacing two screws with a spigot (§7.3, which buys MS 0.54 → 94, a factor of 174), closing the loop at the tail is not the best available €/hour. Close it at the wing, fix the tail joint properly, and lighten the panel.**

### 8.4 The geometry caveat that could invert this

If the panels in fact point **inboard-and-down**, meeting at an apex on the centreline at z = −0.559 m, then:

- The loop is **already closed** for free, in panel-to-panel compression; item I is moot; the lateral bending never reaches the booms; boom torsion is restrained at the apex by the mirror-symmetry condition (θ_x = 0), which is a *rigid* restraint and pushes f_t1 far above 22.7 Hz.
- **But the panels then sweep to a minimum radius of 0.4153 m from the thrust axis** — 8.7 mm outside the propeller tip radius of 0.4065 m at the disc plane, and about 50–70 mm outside the contracted slipstream at the tail station [CALC]. That is *far* tighter than the booms' 169 mm, well inside the 0.2 D clearance guideline [16][DR], and it puts the inboard part of each panel in the blade tip-vortex path.

**Which geometry is actually intended must be settled before this pack's §6 and §8 conclusions can be relied on.** Open question 3. The recommendation if it is a free choice: **keep the panels outboard and close the loop at the wing.** The propwash exposure is the deciding factor, and it is the one thing that cannot be fixed later by adding material.

---

## 9. Question F — the 90 mm diameter is a parameter

`design/argus7_v1.yaml` tags `booms.diameter_m: 0.09` as `assumption`, carried over from "the defective artifact this phase replaces" [3]. It has never been sized.

**The scaling.** For a thin-walled tube, EI ∝ D³t and mass ∝ Dt. At constant EI, **mass ∝ 1/D²**. Boom parasite drag is proportional to wetted area, so **drag ∝ D**. The optimum is where the two exchange rates cross.

Sweep at EI = 80.7 kN·m² (§2.5) with roll-wrapped laminate properties:

| D (mm) | wall | kg/m | 2 booms | σ_ult | MS | shell-buckling MS | Δh mass | Δh drag | **Δh net** | f_b2 |
|---|---|---|---|---|---|---|---|---|---|---|
| 80 | 5.15 | 1.843 | 13.44 | 144 | 4.30 | 14.9 | −5.08 | +0.40 | **−4.68** | 57.3 |
| **90 (inherited)** | 3.33 | 1.379 | **10.06** | 156 | 3.97 | 7.9 | — | — | **datum** | 63.6 |
| 100 | 2.33 | 1.087 | 7.93 | 170 | 3.66 | 4.6 | +3.20 | −0.40 | **+2.80** | 69.1 |
| **110** | **1.71** | 0.885 | **6.45** | 183 | 3.38 | 2.8 | +5.41 | −0.79 | **+4.62** | 74.0 |
| **120** | 1.30 | 0.736 | **5.37** | 198 | 3.14 | **1.8** | +7.03 | −1.19 | **+5.84** | 78.4 |
| 130 | 1.01 | 0.624 | 4.55 | 212 | 2.92 | **1.2** | +8.26 | −1.59 | +6.68 | 82.4 |
| 140 | 0.80 | 0.536 | 3.91 | 227 | 2.73 | **0.85 — buckles** | +9.23 | −1.98 | +7.24 | 86.1 |

[CALC] Shell buckling from σ_cr ≈ 0.3·√(E_x E_y)·t/R, the 0.3 being the conventional knockdown for a real (imperfect) cylinder [EST][DR]. Drag from ΔC_D0 = 0.00188 × (D/0.090 − 1) [2] at 1.9 h per 0.001.

**Findings:**

1. **The endurance benefit of a larger diameter is monotonic and does not turn over within the feasible range.** The drag penalty (0.40 h per 10 mm) is 5–13× smaller than the mass benefit (2.0–3.2 h per 10 mm). There is no diameter at which drag wins.
2. **The binding constraint is not drag; it is minimum wall.** Below about 1.2 mm, the shell-buckling margin collapses (1.8 at 120 mm, 1.2 at 130 mm, negative at 140 mm), the tube becomes dentable in handling, and there is not enough wall for a bolted or bonded fitting.
3. **Choose 110–120 mm.** 110 mm gives a comfortable 2.8× shell-buckling margin at a stock 1.71–2.0 mm wall and is the safe answer. 120 mm gives another 1.2 h but at a 1.30 mm wall and a 1.8 margin, and needs local reinforcement everywhere anything is attached.

**Cost of going to 110 mm:**

| | Value |
|---|---|
| Boom wetted area | 2.062 → 2.520 m² (+22%) |
| Boom C_D0 share | 0.00188 → 0.00230 (9.4% → 11.5% of a 0.020 total) |
| Endurance | **−0.79 h** |
| Mass at equal EI | 10.06 → 6.45 kg → **+5.41 h** |
| **Net** | **+4.62 h (+0.19 d)** |
| Wing let-in burial, if `wing.z_offset_m` is unchanged | 19.5 mm on a 90 mm boom (21.7%) → **39.5 mm on a 110 mm boom (35.9%)** |

**The let-in is the real consequence and it needs stating carefully.** `argus7_v1.yaml` records that the wing section is only **75.2 mm thick at the boom station against a 90 mm boom**, that a through-boom is therefore geometrically impossible, and that `wing.z_offset_m = 0.008` was chosen inside a narrow [0, 0.0175] window with documented ill-conditioning of the CAD boolean at neighbouring values [3]. A 110 mm boom at the same z-offset buries 39.5 mm — **more than half the wing's local thickness** — and would foul the wing's own spar. **The diameter change must be made together with a z-offset change, and the `test_wing_boom_interference_volume_is_plausible` guard re-derived**, not by editing one number.

Recommended: **D = 110 mm with `z_offset_m` raised so the burial returns to ~20 mm (i.e. z_offset ≈ 0.018 m)**, keeping the joint architecture the sponsor already has and staying inside the documented upper bound of the usable window. That is a CAD task with a test to re-derive, not a boom task, and it is logged as open question 5. **If the geometry will not take 110 mm, 100 mm still returns +2.80 h and needs only a 2.33 mm wall.**

---

## 10. Question D — hand layup versus buying a tube

### 10.1 The fibre volume fraction argument is weaker than folklore

| Process | Consolidation pressure | Achievable Vf | Source |
|---|---|---|---|
| Hand wet layup, no bag | none | **0.35–0.42** ("generally resin rich… in excess of 100% fabric weight by resin") | [12][DR] |
| **Wet layup + vacuum bag** | **0.1 MPa max, ever** | **0.45–0.58** (0.58 with a controlled viscosity dwell, <2% voids) | [12][M][13][M] |
| Wet layup + **shrink tape** | **0.4–1.2 MPa** | 0.50–0.60 | [13][M][9][DR] |
| **Roll-wrapped prepreg + shrink tape (COTS)** | 0.4–1.2 MPa | **0.55–0.65** | [10][DR] |
| Prepreg + autoclave | 0.6–0.7 MPa | 0.58–0.62 | [DR] |

Back-calculating from the COTS tube's own datasheet density of 1.523 g/cm³ gives **Vf ≈ 0.54–0.57** [4][DS][CALC] — consistent with [10].

**The like-for-like comparison, at equal EI, D = 110 mm:**

| Route | Vf | E_x | wall | **2-boom mass** | Δ vs COTS |
|---|---|---|---|---|---|
| COTS roll-wrapped | ~0.54 | 94.7 GPa | 1.71 mm | **6.45 kg** | — |
| Hand layup, good bag | 0.55 | 100.1 | 1.61 mm | 6.12 kg | **−0.33 kg (+0.5 h)** |
| **Hand layup, realistic** | **0.50** | 91.2 | 1.78 mm | **6.61 kg** | +0.16 kg (−0.2 h) |
| Hand layup, poor bag | 0.45 | 82.3 | 1.98 mm | 7.20 kg | +0.75 kg (−1.1 h) |
| Hand layup, bad day | 0.40 | 73.5 | 2.22 mm | 7.94 kg | **+1.49 kg (−2.2 h)** |
| COTS filament-wound | ~0.54 | 72.6 | 2.26 mm | 8.50 kg | +2.05 kg (−3.1 h) |

[CALC]

**So the honest answer to "quantify the difference": it is 0.2 to 2.2 hours of endurance, not the order-of-magnitude the fibre-volume argument implies.** The reason is the one in §4.2 — for a fixed ply count, poor consolidation costs mass but not stiffness. A hand-laid boom at a *good* Vf is marginally **lighter** than the COTS tube, because it can be laid at exactly the required wall while COTS comes in 0.5 mm steps.

Note also that filament-wound tube, which the materials pack correctly identifies as torsionally superior, is **2.05 kg (3.1 h) heavier** at equal bending stiffness. For a boom whose torsional requirement is a frequency (§5.2) and whose bending requirement is the sizing case, **roll-wrapped is the right architecture and filament-wound is not.**

### 10.2 Where buying actually wins

The case for COTS is not mass. It is:

| | COTS roll-wrapped | Hand layup |
|---|---|---|
| **Builder hours, 2 booms** | **10–20 h** (cut, splice, bond fittings) | **80–130 h** (incl. one test article and the learning curve) [EST] |
| **Straightness** | 0.5–1 mm/m, controlled | whatever the mandrel is; a 4 m aluminium tube sags visibly under its own weight and must be supported at ≥5 points during cure [EST] |
| **Roundness / wall uniformity** | machine-wound, ±0.1 mm | seam ridges at every ply overlap; wall variation ±0.2–0.3 mm unless the shrink tape is applied with real discipline |
| **Repeatability boom-to-boom** | identical | two booms with different EI produce a permanently rigged-out aircraft; a 5% EI mismatch is a 5% tail-load asymmetry |
| **Defect visibility** | supplier's process control | dry spots and voids inside a closed tube are **invisible and unrepairable** |
| **Length** | **stock tops out at 2 m (EU) / 1.83–2.44 m (US)** [2][20][DS] → needs a splice or a custom mandrel order | **one-piece 3.65 m, which is the real advantage and the sponsor should be given it** |
| **Property provenance** | datasheet E_x, E_y, G_xy [4][DS] | must be coupon-tested; `materials_pack.md` §13 open question 7 already requires this even for COTS |
| **Cash, 2 booms** | €1,100–2,300 at €150–300/kg for 7.5 kg [EST][UNV]; up to €2,000–5,000 aerospace-sourced [2] | €1,200–1,700 in materials (§13) |

**The splice is the answer to the length problem and it is structurally trivial.** Put a bonded internal sleeve at 2.0 m aft of the wing rear spar, where M = 0.34 × M_root = 803 N·m:

- axial wall stress at the splice: σ = 803 × 0.055/9.90×10⁻⁷ = **44.6 MPa**
- running load into the bond: σ·t = 89.2 kN/m
- over a 110 mm (1 D) overlap each side: **0.81 MPa** of adhesive shear against 28.9 MPa [6][DS] → **MS 35**, and 2.8% of static, which is well below any adhesive fatigue threshold
- with `materials_pack.md`'s own rule (overlap ≥ 2 D, scarfed ends, 0.15–0.25 mm bondline, circumferential over-wrap) [2] the margin is larger still

[CALC] **Two 2 m stock tubes per boom, spliced at 2.0 m, is a legitimate and cheap answer** and it removes most of the length argument for hand-laying.

### 10.3 Recommendation on question D

**Buy the tube. Specify it. Coupon-test one offcut.**

For a solo builder with €60k and 18 months, whose premortem names "one pair of hands" as the second-highest failure mode [1], **70–110 hours saved for €0–600 of price difference is the trade, and it is obviously worth taking.** The mass difference (0.2–2.2 h of endurance) is real but second-order; the *variance* is the argument — a hand-laid boom can come out anywhere between 6.1 and 7.9 kg with defects you cannot see, and you will build exactly two of them with no chance to learn.

**Specify, in the purchase order:**

- **110 mm OD (or 100 mm), 2.0 mm nominal wall, roll-wrapped**
- **Layup declared: ≥ 55% of thickness at 0°/low-angle, 25–30% at ±45, remainder hoop.** Do not accept "3K twill" without a layup statement — a generic twill tube is ±45-dominated and bending-soft [2].
- **Declared E_x, E_y, G_xy and areal density**
- **Straightness ≤ 1 mm/m, roundness ≤ ±0.15 mm**
- **Length: 2 × 2,000 mm per boom, or one-piece ≥ 3,700 mm if the supplier holds a 4 m mandrel** (Carbon-Composite's 81–120 mm precision-tube range and Easy Composites' roll-wrapped range are the two European starting points [20][8][DS])
- **A 300 mm offcut from the same production run**, for the four-point bend and torsion coupon tests `materials_pack.md` §13 already requires

---

## 11. Question E — verifying the sponsor's technical claims

### 11.1 Resin — right conclusion, wrong product

**Polyurethane is correctly rejected**, and for the reasons given. Nothing here disputes it.

**But West System 105/205 is the wrong choice within the right family, on three counts:**

| | West 105/205 | Structural laminating / infusion epoxy |
|---|---|---|
| Mixed viscosity at 22 °C | **975 cP** [14][DS] | 200–600 cP (infusion), 400–900 (hand lam) [15][DS] |
| Tensile modulus | **2.81 GPa** [14][DS] | **3.0–3.9 GPa** [15][DS] |
| Tensile elongation | 3.4% [14][DS] | 1.9–5.3% [15][DS] |
| Hardener | **205 is the *fast* hardener** — 9–12 min pot life | slow/extra-slow hardeners give 40–90 min |

The sponsor's own stated requirement — "low-viscosity … does wet out dense carbon tows" — is not met by a 975 cP marine coating resin. And a 3.65 m tube with 8 plies is a **60–90 minute continuous layup**; a 9–12 minute pot life makes that physically impossible without mixing in six separate batches, which is how dry spots happen.

**Recommendation: a slow-hardener structural laminating epoxy** (PRO-SET LAM-125/226, Sicomin SR 8100 series, Resoltech 1080T, or Easy Composites' EL2/IN2 class), mixed by weight on a scale, with **a 40–90 minute pot life**. It costs the same per kilogram and it removes the most likely cause of a bad boom. The 8% modulus difference is negligible in a fibre-dominated laminate; the **viscosity and the pot life are what matter**.

**And: post-cure is mandatory.** `materials_pack.md` §5.3 already establishes this — room-temperature-cure epoxy reaches Tg 50–70 °C as cured and 80–90 °C after 12–24 h of elevated post-cure, and a dark composite surface parked in the sun exceeds 100 °C [2][19][DR]. **Post-cure the booms at 55–60 °C for ≥ 12 h before any fitting is bonded.**

### 11.2 Galvanic barrier — right, but one ply is the floor, not the answer

**The mechanism is correctly identified and it is a genuine, documented failure mode.** Carbon is cathodic to aluminium by roughly 1 V; the couple in the presence of moisture corrodes the aluminium preferentially, and the carbon's large cathodic area makes it worse.

**Aerospace practice confirms the sponsor's prescription:** "carbon fibres must be isolated from aluminium or steel using a barrier (liquid shim, glass ply, etc.)"; "any direct contact isolated with a single ply of glass on the graphite at the contact area" [11][DS][DR].

**But the sponsor's "one layer of 80–120 gsm fibreglass" is the documented *minimum*, and flight hardware routinely uses more.** A directly relevant data point: in an aerospace harness isolation application, "preliminary tests illustrated that **two plies** of glass could provide sufficient isolation … though **three plies** of glass were used as the base isolation … to ensure adequate insulation" [DR]. The reason is not electrochemical, it is manufacturing: **a single 80 gsm ply is ~0.07 mm thick and a single stray carbon tow, or a resin-starved patch, bridges it.**

Separately, the epoxy layer thickness itself matters, measurably: a 0.1 mm epoxy film on carbon reduced the galvanic corrosion rate in seawater **7-fold**, and 0.25 mm — "typical of that used in wet layup" — reduced it **21-fold** [23][M].

**The rule this produces, if any aluminium is retained anywhere near carbon:**

> **Two plies of 80–120 gsm E-glass, not one, with staggered seams, plus a resin-rich (not resin-starved) bondline of ≥ 0.2 mm. Where the interface is inspectable, one ply plus a sealant is acceptable. Where it is buried inside a closed tube for the life of the airframe, use two, and preferably do not create the interface at all.**

Which is §3.6's conclusion arrived at from a second direction: **the cheapest galvanic barrier is not having the aluminium.**

Note that this rule still applies to the recommended build — every aluminium collar, bush, spigot or fitting touching the carbon boom gets a glass ply, as `materials_pack.md` §7.4 already requires [2][22][DS].

### 11.3 Cured ply thickness — right for a mediocre bag

| Vf | Cured thickness, 200 gsm | Laminate density | UD E₁ |
|---|---|---|---|
| 0.40 | **0.278 mm** | 1,440 kg/m³ | 93.9 GPa |
| 0.45 | 0.247 mm | 1,470 | 105.3 |
| **0.50** | **0.222 mm** | 1,500 | 116.6 |
| 0.55 | 0.202 mm | 1,530 | 127.9 |
| 0.60 | 0.185 mm | 1,560 | 139.3 |

[CALC] from CPT = areal weight/(ρ_fibre × Vf), ρ_fibre = 1,800 kg/m³ [7][DS]

**The sponsor's 0.25–0.30 mm corresponds to Vf 0.37–0.44 — i.e. a bagged layup that is not much better than a hand layup.** A well-executed vacuum bag reaches 0.45–0.58 [12][M], i.e. **0.202–0.247 mm**. The sponsor's number is a safe planning figure and not a wrong one; it just means the layup schedule should be written in plies (§4.2), because the mass will vary by 20% and the stiffness will not vary at all.

### 11.4 Shrink tape versus vacuum bagging — the sponsor's "alternative" is actually the better method

| | Vacuum bag | Shrink tape |
|---|---|---|
| Consolidation pressure | **0.1 MPa, and no more, ever** — atmospheric is the hard ceiling [13][M] | **0.4–1.2 MPa** [13][M] |
| Void content | up to 7.5% in WLVB/VARTM [13][M] | lower; "parts feature a better fiber-to-resin ratio and improved physical properties" [9][DR] |
| Suitability for a 3.65 m tube | needs a 4 m bag, a 4 m sealed perimeter and a 4 m breather run; one leak anywhere loses the whole part | applied progressively; a local defect is a local defect |
| Radial uniformity on a cylinder | good in principle, but bridging at any local diameter change is a classic failure | uniform hoop compaction by construction |
| Industrial usage | general | **this is how roll-wrapped tube is actually made** [10][8][DR] |

[13][9][10]

**The sponsor lists shrink tape as an "alternative for tubes". It should be the primary method.** For a cylinder specifically, shrink tape delivers 4–12× the consolidation pressure of a vacuum bag, produces the higher Vf that shortens the wall (§10.1), and removes the single-point-of-failure that a 4 m vacuum bag represents for a solo builder.

**Practical warnings the sources make explicit:**

- **Overlap matters enormously.** "Each wrap of the tape advances only a few millimetres down the tube. Although time-consuming to do by hand, having lots of overlap in this way will provide much more consolidation pressure" — 50–75% overlap is the target [8][10][DR]. At 75% overlap on a 50 mm tape over a 110 mm tube, that is **~105 m of tape per boom**. Budget for it (§13) and budget the hours.
- **The tape leaves a helical witness ridge.** It must be sanded off, which removes some outer-ply fibre. Put a **sacrificial peel ply under the shrink tape**; strip it after cure and the surface comes off clean.
- The two are not exclusive: "for complex geometries, segmented tape application **or the use of a vacuum bag over the tape wrapping** provides more uniform consolidation pressure" [13][DR].

### 11.5 Vacuum level — right, and note what it means

25–29 inHg = 0.85–0.98 bar of the theoretical 1.013 bar. That is correct practice. It is worth stating explicitly what the number implies: **it is 0.085–0.098 MPa, i.e. one twelfth of what shrink tape delivers** [13][M]. The 25–29 inHg specification is not a target you can beat by pulling harder.

---

## 12. The recommended build — step by step

**Configuration: two hollow CFRP booms, 110 mm OD × 2.0 mm wall, no aluminium liner, COTS roll-wrapped tube, spliced at 2.0 m if bought in 2 m lengths.**

### 12.1 Materials

| Item | Spec | Qty |
|---|---|---|
| Boom tube | 110 mm OD × 2.0 mm roll-wrapped CFRP, layup declared (≥55% 0°, 25–30% ±45), E_x, G_xy declared | 4 × 2,000 mm (or 2 × 3,700 mm one-piece) |
| Splice sleeves | 106 mm OD × 2.0 mm CFRP, 260 mm long (2 D overlap + tolerance) | 2 |
| Adhesive | Loctite EA 9394 or equivalent RT-cure epoxy paste, 0.15–0.25 mm controlled bondline | ~600 g |
| Over-wrap cloth | 200 gsm 3k twill, **bias-cut at ±45** | 3 m² |
| Barrier cloth | 105 gsm E-glass plain weave | 1 m² |
| Laminating epoxy | slow-hardener structural laminating system, 40–90 min pot life | 1.5 kg |
| Bulkheads | 20 mm Rohacell 51 IG-F discs, 2 CFRP faces each | 6 |
| Wing collars | split CFRP or 7075 rings, 70 mm long, bonded + 4 × M5 through-bolts | 4 |
| Tail sockets | 50 mm ID CFRP socket, 150 mm engagement, bonded into the boom aft end | 2 |
| Tail spigots | 50 mm OD CFRP, 150 mm, bonded into the panel root fitting | 2 |
| Retention | 1 × M6 captive clamp bolt per side + 1 × 3-pin servo connector per side | 2 |

### 12.2 Procedure

**Stage 1 — Receive and verify (2 h)**
1. Measure each tube: OD at 5 stations, wall at both ends, straightness on a flat surface (accept ≤ 1 mm/m), mass per metre. **Record.** Compare the measured kg/m against the declared density; a discrepancy is your first evidence of the true Vf.
2. Cut a 300 mm coupon from the offcut. Four-point bend to measure E_x; torsion to measure G_xy. **Do not commit the tail to a tube whose properties you have not measured** — `materials_pack.md` §13 open question 7 requires this, and this pack's entire frequency analysis depends on E_x and G_xy [2].

**Stage 2 — Splice (4 h per boom, if two-piece)**
3. Mark the splice at **2,000 mm aft of the wing rear-spar station**, where M = 0.34 M_root.
4. Abrade the sleeve OD and both tube bores with 220 grit; degrease with IPA, not acetone [2].
5. Scarf/chamfer both tube ends internally over 10 mm to spread the shear peak.
6. Bond with EA 9394, 0.20 mm bondline set with three 0.2 mm nylon shim wires. Rotate the assembly through 90° every 10 minutes for the first hour so the adhesive does not sag to one side.
7. Cure 24 h at 20 °C, then **post-cure 12 h at 55 °C**.
8. Over-wrap 3 plies of bias-cut ±45 cloth, 300 mm wide, centred on the splice; peel ply over; shrink tape at 50% overlap; cure and post-cure.

**Stage 3 — Local reinforcement (5 h per boom)**
9. Bond internal bulkheads at: the forward end of the let-in, the aft end of the let-in, and 40 mm forward of the tail socket. These stop the tube ovalising under clamp load.
10. Bond the tail socket into the aft end: 150 mm engagement, EA 9394, controlled bondline, then a 3-ply ±45 external over-wrap over the whole socket length. **This is the joint that converts peel into hoop tension** [2].
11. Over-wrap the full 538 mm let-in region with 3 plies of bias-cut ±45, 360° around.
12. **Glass ply everywhere a metal fitting will touch carbon** — two plies of 105 gsm E-glass, staggered seams (§11.2).

**Stage 4 — Wing joint (6 h per boom)**
13. Fit the two split collars, one at each end of the let-in. Bond *and* bolt: the bond carries the working load, the bolts carry the peel and give you a mechanical backup.
14. Trial-fit into the wing let-in. The saddle must bear over the full 111° arc — shim with EA 9394 as a liquid shim, not with a dry gap.
15. Bond the boom into the let-in. **Rig both booms in a jig against the wing datum**, not to each other, so the two tails end up at the same incidence.

**Stage 5 — Verification before flight (3 h)**
16. **Tap test** each finished boom with the tail panel fitted. Record f_b1, f_b2 and f_t1 with a phone accelerometer or a cheap USB accelerometer and an FFT. Compare with §6.3.
17. **Static deflection check.** Hang 454 N (the limit vertical tail load) at the tail quarter chord with the wing rigidly supported. **Expect 45.8 mm of deflection and 1.29° of rotation.** More than 60 mm means the tube is not what the datasheet says.
18. **Ground run with the engine at cruise power**, accelerometer at the tail. Sweep the rpm. Look for any peak within 20% of a comb line (§6.4). This is the single test that closes out §6.
19. Weigh the finished booms. Both. If they differ by more than 100 g, find out why.

### 12.3 If the sponsor insists on hand-laying

Then do it this way and it will work:

- **Mandrel:** 110 mm OD aluminium tube, 4.2 m, supported at 5 points; 2 wraps of 25 µm FEP release film, spiral-wound at 50% overlap, with pull tails at both ends.
- **Layup:** 1 × 200 gsm twill **bias-wrapped ±45** / 6 × 200 gsm UD at 0°, seams staggered 60° between plies / 1 × 200 gsm twill bias-wrapped ±45. **Eight plies. Write the schedule in plies, not millimetres** (§4.2).
- **Consolidation: shrink tape, 50 mm wide, 75% overlap, over a peel ply.** ~105 m of tape per boom. Not a vacuum bag.
- **Resin:** slow-hardener structural laminating epoxy, weighed, applied by squeegee and consolidated ply by ply.
- **Cure** 24 h at 20 °C; **post-cure 12 h at 55 °C**; extract the mandrel **while the tube is at 40–50 °C** and the mandrel is chilled [10][DR].
- **Build a third boom first, as a test article, and destroy it.** Four-point bend it to failure. That is the only way you will know what your own layup achieves.
- Expected result: **1.78 mm wall at Vf 0.50, 3.31 kg per boom, EI 80.7 kN·m²** — or 2.22 mm and 3.97 kg at Vf 0.40, which is a 1.3 kg / 2.0 h penalty and nothing worse.

---

## 13. Bill of materials, cost and build hours

### 13.1 Recommended (COTS) route

| Item | Qty | Unit | Total |
|---|---|---|---|
| 110 × 2.0 mm roll-wrapped CFRP tube | 7.5 kg | €150–300/kg [EST][UNV] | **€1,125–2,250** |
| Splice sleeve stock (106 × 2 mm) | 0.6 m | — | €90–160 |
| EA 9394 or equivalent paste adhesive | 1 kg kit | €90–140 | €90–140 |
| 200 gsm 3k twill, bias-cut | 3 m² | €25–35/m² | €75–105 |
| 105 gsm E-glass | 1 m² | €12–18/m² | €15 |
| Slow laminating epoxy | 1.5 kg | €25–35/kg | €40–55 |
| Rohacell 51 IG-F offcut | — | — | €25 |
| Collars, bushes, fasteners, spigots/sockets | — | — | €150–300 |
| Consumables (peel ply, release film, shrink tape, gloves, mixing) | — | — | €120–200 |
| Coupon testing (or a friendly workshop) | — | — | €0–400 |
| **Total, two booms** | | | **€1,730–3,650** |

### 13.2 Hand-laid route

| Item | Qty | Total |
|---|---|---|
| 200 gsm UD carbon (6 plies × 2 booms + 30% waste) | 20 m² | €600–800 |
| 200 gsm 3k twill (2 plies × 2 booms + over-wraps, bias-cut → +40% waste) | 9 m² | €250–360 |
| Structural laminating epoxy, slow hardener | 6 kg | €160–220 |
| **Shrink tape, 50 mm** (~210 m at 75% overlap + test article) | 6 rolls | **€250–420** |
| Peel ply, FEP release film | 35 m² | €120–180 |
| Aluminium mandrel, 110 × 2 mm × 4.2 m (may be consumed) | 2 | €140–260 |
| E-glass, adhesives, fittings, consumables | — | €300–500 |
| Post-cure oven (insulated box + thermostat + heater) | 1 | €150–350 |
| Test article (3rd boom, destroyed) | — | €300–400 |
| **Total, two booms + one test article** | | **€2,270–3,490** |

**The cash difference is close to zero.** The difference is entirely in hours and in variance.

### 13.3 Build hours, solo builder

| Task | COTS | Hand-laid |
|---|---|---|
| Sourcing, specification, vendor liaison | 6–12 | 4–8 |
| Incoming inspection + coupon test | 3–6 | 3–6 |
| Mandrel preparation and support rig | 0 | 8–14 |
| Ply cutting (incl. bias cutting) | 0 | 8–12 |
| Layup | 0 | 12–20 |
| Shrink-tape wrapping | 0 | 8–14 |
| Cure, post-cure, demould, clean-up | 0 | 10–18 |
| Test article: build, test, learn, redo | 0 | **25–40** |
| Splicing (if two-piece) | 6–10 | 0 |
| Local reinforcement, bulkheads, over-wraps | 8–14 | 8–14 |
| Sockets/spigots, collars, fittings | 10–16 | 10–16 |
| Jig, rig, bond into the wing | 10–16 | 10–16 |
| Verification (tap test, deflection, ground run) | 4–6 | 4–6 |
| **Total, both booms** | **47–80 h** | **110–184 h** |
| **Midpoint** | **≈ 64 h** | **≈ 147 h** |

[EST], calibrated against the task-level structure of `materials_pack.md` §12.

**≈ 83 hours of difference.** On a programme whose premortem lists "one pair of hands, 18 months, three full-time workstreams" as failure mode #2 [1], and where the booms are perhaps 3% of the airframe by hours, this is not where the builder's time should go.

---

## 14. Consolidated endurance ledger

All figures for **two booms, 3.6456 m each**, sized to EI = 80.7 kN·m² except where noted. Baseline 112.8 h [1].

| Build | Boom tube | Local reinf. | **Total** | Δ mass h | Δ drag h | **Net Δh** |
|---|---|---|---|---|---|---|
| **Sponsor as proposed** — Al 90 × 2.0 liner + 10 "heavy duty" woven layers | 18.45 | 0.60 | **19.05 kg** | −14.8 | +0.79 | **−14.0, and 10% short of the stiffness requirement** |
| Same on a 1.5 mm liner (if a 1.5 mm wall can be sourced) | 15.94 | 0.60 | 16.54 kg | −11.0 | +0.79 | −10.2, **and 19% short** |
| Sponsor's architecture, **sized to actually meet the requirement** — Al 90 × 1.5 + 2.56 mm carbon | 15.42 | 0.60 | **16.02 kg** | −10.2 | +0.79 | **−9.4** |
| Same with a 1.0 mm liner | 13.98 | 0.60 | 14.58 kg | −8.1 | +0.79 | −7.3 |
| Hollow CFRP at the inherited 90 mm, sized to requirement | 10.06 | 1.66 | 11.72 kg | −3.8 | +0.79 | **−3.0** |
| Hollow CFRP 100 mm, sized to requirement | 7.93 | 1.66 | 9.59 kg | −0.6 | +0.40 | −0.2 |
| **Recommended — COTS roll-wrapped 110 × 2.0, two-piece spliced** | **7.54** | **1.66** | **9.20 kg** | **datum** | **datum** | **datum** |
| Same, 110 mm sized exactly to requirement (1.71 mm wall) | 6.45 | 1.66 | 8.11 kg | +1.6 | 0 | +1.6 |
| Hand-laid 110 mm, **one-piece**, Vf 0.50 | 6.61 | 1.22 | 7.83 kg | +2.1 | 0 | **+2.1** |
| Hand-laid 110 mm, one-piece, Vf 0.40 | 7.94 | 1.22 | 9.16 kg | +0.1 | 0 | +0.1 |
| COTS 120 × 1.6 (stock wall, 22% stiffness surplus) | 6.61 | 1.90 | 8.51 kg | +1.0 | −0.40 | +0.6 |
| 120 mm sized exactly to requirement (1.30 mm wall, buckling MS 1.8) | 5.37 | 1.90 | 7.27 kg | +2.9 | −0.40 | **+2.5** |
| **Optional: + faired 50 mm tail cross-tie (§8)** | | +0.75 | +0.75 kg | −1.1 | −2.4 | **−3.5** |

[CALC] Δh = −1.5·(m − 9.20) − 1900·(C_D0,boom − 0.002298), with C_D0,boom = 0.00188 × D/0.090 [2].

Local reinforcement, both booms: 2 collars 0.30 + let-in over-wrap 0.24 + 6 bulkheads 0.18 + 2 tail sockets 0.50 = **1.22 kg**, plus **0.44 kg** for two splice sleeves and their over-wraps if the tube is bought in 2 m lengths, and **+0.24 kg** at 120 mm where the thinner wall needs more local build-up. The aluminium-lined builds are credited with needing only 0.60 kg because the liner genuinely does provide the crush resistance the bulkheads and collars otherwise buy. [EST]

**Read four ways:**

- **Against the sponsor's proposal as written: +14.0 hours (0.58 days)** — and the proposal is still 10% short of the stiffness requirement, so it would have to grow further before it is airworthy.
- **Against the sponsor's architecture properly sized: +9.4 hours (0.39 days).**
- **Against the current 90 mm baseline in `argus7_v1.yaml`, properly sized: +3.0 hours**, entirely from the diameter change (+3.8 h of mass, −0.8 h of drag).
- **And a one-piece hand-laid 110 mm boom at Vf 0.50 is the lightest option on the table (+2.1 h)** — because it avoids the splice and can be laid at exactly the required wall. That is the real, honest argument for hand-laying, and §10.3 still recommends against it on hours and variance, not on mass.

For scale, `materials_pack.md` §11 puts the *entire* cost of following the sponsor's build preference across the whole wing at 16.6–23.3 h [2]. **The boom decision alone is 10–15 h of that, and it is decided by two numbers: whether the aluminium stays and what the diameter is.**

---

## 15. Open questions

**Configuration — these block conclusions in this pack**

1. **V_D is not stated in the design report.** Every tail load in §2.2 scales with q_D. 200 km/h EAS is carried over from `materials_pack.md` and is [EST]. Fix V_D and the load case is closed.
2. **The propulsion set does not close: C_P = 0.911 is required for 17 kW at 2,100 rpm on a 0.813 m propeller** (§6.2), against a physical ceiling near 0.25. Until the reduction ratio, prop diameter and rpm are reconciled, the blade-passage frequency is uncertain from ~47 to ~107 Hz and §6.4 cannot be closed. **This is the highest-value open question in the pack** and it is a propulsion question, not a structures one.
3. **Which way do the tail panels point?** Outboard-and-down (assumed here) or inboard-and-down to a centreline apex. It decides whether the structural loop is already closed (§8.4), whether the panels sit 169 mm or 9 mm from the prop tip radius, and whether §8's recommendation stands. `tail.dihedral_deg` is tagged `assumption` in the yaml [3].
4. **Should the tail be re-architected as an H/U-tail with a centre section?** It closes the loop for free, removes the cos²Γ effectiveness loss, and gives propwash over the elevator — at the price of putting the horizontal surface inside the slipstream and making it a fatigue article (§8.3). Out of this pack's scope; worth an hour of someone's time.
5. **A 110 mm boom needs `wing.z_offset_m` changed with it**, and the yaml documents that this value sits in a narrow window with an ill-conditioned CAD boolean at neighbouring values [3]. Diameter and z-offset must be changed together and `test_wing_boom_interference_volume_is_plausible` re-derived.

**Structural**

6. **The tail-joint inspection intervals in §7.3 (25 h then 50 h, replace at 2% hole elongation) are engineering judgement, not measured.** If a bolted joint is adopted, one bearing-fatigue coupon at the design bearing stress would replace judgement with data.
7. **CFRP S-N data above 10⁷ cycles is thin** and the VHCF literature reports no true fatigue limit and a step in the S-N curve at the HCF/VHCF transition [18][M]. The 55× strain margin in §6.5 is the defence, not the extrapolation — but the margin depends on the near-field pressure estimate, which is [EST].
8. **The near-field blade-passage pressure at 0.21 D tip clearance is estimated, not measured** (§6.1). A single microphone or surface-mounted pressure sensor on the boom during a ground run would replace a 20–200 Pa estimate with a number, and it is the input that decides §6.5.
9. **Structural damping ratio of the finished boom is assumed at 1–5%.** The tap test in §12.2 step 16 measures it directly from the decay envelope and costs nothing.
10. **The 111° let-in arc under lateral load has not been analysed beyond a hand couple calculation** (§7.2). It is the joint whose failure loses the aircraft. A simple FE shell model, or a static test to 1.5× limit lateral load on a boom stub, would close it.

**Supply and process**

11. **No verified vendor price for 110 mm roll-wrapped tube at ≥ 2 m.** §13's €150–300/kg is [EST][UNV]. Two quotes settle it, and the answer changes the COTS-vs-hand-lay calculus in §10.3 more than any technical argument does.
12. **Will any supplier declare E_x, E_y and G_xy and the layup?** `materials_pack.md` §4.5 already makes this the acceptance condition [2]. If nobody will, the tube must be coupon-tested and the schedule must allow for it.
13. **Shrink tape consumption is 105 m per boom at 75% overlap** (§11.4) — verify against a real trial on a 500 mm test piece before ordering, because the number is derived from the overlap geometry, not from experience.

---

## 16. Sources

| # | Source | Type |
|---|---|---|
| [1] | `docs/argus7_design_report.md` v1.0, 2026-08-20 — §2 geometry, §3 mass budget, §4 aero/performance, §5 structures, §6 powertrain, Annex A premortem | project document |
| [2] | `research/materials_pack.md`, 2026-08-20 — §4 boom sizing and tube properties, §6.8 endurance ledger and the 1.5 h/kg exchange rate, §7 adhesives and joints, §8 fatigue and environment, §13 open questions | project document |
| [3] | `design/argus7_v1.yaml` — `booms.diameter_m: 0.09` tagged `assumption`; `wing.z_offset_m` window and CAD-boolean conditioning notes; `tail.dihedral_deg` tagged `assumption` | project document |
| [4] | Rock West Composites, P/N 45285, roll-wrapped 2×2 twill + multidirectional uni tube, engineering property table (E_x 94.7 GPa, E_y 32.9, G_xy 11.68, σ_t 620 MPa, ρ 1.523 g/cm³) — https://www.rockwestcomposites.com/45285.html | [DS] |
| [5] | Rock West Composites, P/N 35165-U, filament-wound tube (E_x 72.6 GPa, G_xy 22.53 GPa), available to 15 ft — https://www.rockwestcomposites.com/35165-u.html | [DS] |
| [6] | Henkel Aerospace, "Hysol EA 9394 Epoxy Paste Adhesive" TDS — 28.9 MPa lap shear at 25 °C, **T-peel 5 lb/in = 22 N/25 mm**, Tg 78 °C dry — https://exdron.co.il/Exdron-Pdf/Loctite_Hysol_EA9394.pdf | [DS] |
| [7] | Easy Composites, "210g (6.2 oz) 2×2 Twill 3k Carbon Fibre Cloth" product data (areal weight, fibre density basis for CPT) — https://www.easycomposites.us/200g-22-twill-3k-carbon-fiber-cloth | [DS] |
| [8] | Easy Composites, "How to Choose the Best Carbon Fibre Tube for an Application" and "How to Make a Roll Wrapped Carbon Fibre Tube" (roll-wrapped = highest bending stiffness; shrink-tape overlap practice) — https://www.easycomposites.eu/learning/carbon-fibre-tubes-explained · https://www.easycomposites.co.uk/learning/how-to-make-a-roll-wrapped-carbon-fibre-tube | [DS]/[DR] |
| [9] | Dunstone Innovation, "Shrink Tape vs. Vacuum Bagging vs. Autoclave" — shrink tape pressurises by heat, shrinks up to 20%, "better fiber-to-resin ratio and improved physical properties"; used for tubing where bagging is impractical — https://www.shrinktape.com/resources/news/shrink-tape-vs-vacuum-bagging-vs-autoclave/ | [DR] |
| [10] | "Roll Wrapping Carbon Fiber Tubes: Process, Materials, and Technical Specifications" — Vf 55–65% with shrink-tape consolidation; PTFE/nylon shrink tape helically at 50–75% overlap; **mandrel extraction while the tube is still at 40–50 °C** — https://incomepultrusion.com/roll-wrapping-carbon-fiber-tubes-an-in-depth-guide/ | [DR] |
| [11] | Abbott Aerospace, AA-SB-001 §4.1.8 "General Laminate Design Guidelines" — "Carbon fibers must be isolated from aluminum or steel using a barrier (liquid shim, glass ply, etc)" — https://www.abbottaerospace.com/aa-sb-001/4-materials/4-1-composite-materials/4-1-8-general-laminate-design-guidelines/ | [DS] |
| [12] | "Optimization of the wet lay-up/vacuum bag process for the fabrication of carbon fibre epoxy composites with high fibre fraction and low void content", *Composites* (1989) — up to **58% fibre by volume and <2% voids** within a 7,500–16,500 mPa·s viscosity dwell window — https://www.sciencedirect.com/science/article/abs/pii/0010436189902139 | [M] |
| [13] | "Magnet Assisted Composite Manufacturing: A Flexible New Technique for Achieving High Consolidation Pressure in Vacuum Bag/Lay-Up Processes", *Materials* — **VARTM and WLVB consolidation pressure limited to atmospheric 0.1 MPa, void content up to 7.5%, versus 0.4–1.2 MPa processes** — https://pmc.ncbi.nlm.nih.gov/articles/PMC6101221/ | [M] |
| [14] | Gougeon Brothers / WEST SYSTEM, "Technical Data Sheet 105 System 105/205" — mixed viscosity **975 cP at 72 °F**, tensile modulus **2.81 GPa**, elongation 3.4%, 205 = fast hardener — https://www.westsystem.com/app/uploads/2022/09/105_205-207-Combined.pdf | [DS] |
| [15] | PRO-SET LAM-125/LAM-226 and LAM-1002/LAM-237 laminating & infusion epoxy TDS (tensile modulus 3.0–3.9 GPa, elongation 1.9–5.3%) — https://eu.prosetepoxy.com/wp-content/uploads/2025/04/PRO-SET-LAM-125-with-LAM-226-Medium-Cure-Laminating-Epoxy-Rev-3.pdf | [DS] |
| [16] | FAA Advisory Circular **AC 20-66B, "Propeller Vibration and Fatigue"** (3/24/11) — propeller-induced vibratory excitation, resonance avoidance and fatigue evaluation practice — https://www.faa.gov/documentLibrary/media/Advisory_Circular/AC_20-66B.pdf | [DS] |
| [17] | Resonance separation practice: "many major vibration problems can be avoided by making sure the excitation frequency does not fall within a **20 percent range** around the natural frequencies of the vibration modes of the system"; blade-passage excitation = shaft rate × blade count — ABS "Insights into Ship Vibration Analysis" and ScienceDirect "Blade Passing Frequency" overview — https://cloudstage.eagle.org/content/dam/eagle/advisories-and-debriefs/Insights%20into%20Ship%20Vibration%20Analysis.pdf | [DR] |
| [18] | "Very High Cycle Fatigue (VHCF) Characteristics of Carbon Fiber Reinforced Plastics (CFRP) under Ultrasonic Loading", *Materials* 13(4):908 — **matrix fatigue-limit strain ε_mf = 0.6% for epoxy resins, below which no damage progression occurs**; CFRP shows no traditional fatigue limit and a step in the S-N curve at the HCF/VHCF transition; matrix micro-cracking is the principal failure driver — https://doi.org/10.3390/ma13040908 | [M] |
| [19] | Composite bolted-joint bearing fatigue: "Bearing Fatigue and Hole Elongation in Composite Bolted Joints" (Vertical Flight Society); bearing failure as four-stage compressive damage accumulation with progressive hole elongation and preload loss; **typical composite design bearing allowable 24,000 ± 4,000 psi (165 ± 28 MPa)** — https://vtol.org/store/product/bearing-fatigue-and-hole-elongation-in-composite-bolted-joints-631.cfm | [M]/[DR] |
| [20] | Carbon-Composite GmbH, carbon precision tubes, outside diameter 81–120 mm, ex-stock — https://www.carbon-composite.com/en/Products/Carbon-tubes-round/Sorted-by-outside-diameter/Precision-tubes-81-120mm/ | [DS] |
| [21] | Aluminium Online / Aluminium Warehouse, 90 mm × 2 mm 6060 round tube; standard alloys 6060/6063/6082-T6, 6 m stock lengths, cut to size — https://www.aluminium-online.co.uk/product/aluminium-round-tube-90mm-x-2mm/ | [DS] |
| [22] | Clearwater Composites, "Carbon Fiber Tube FAQ — Galvanic Corrosion" (insulate carbon from metal with fibreglass) — https://www.clearwatercomposites.com/resources/faq/carbon-fiber-tubing/ | [DS] |
| [23] | Galvanic corrosion rate vs epoxy coating thickness on carbon fibre: 0.1 mm coating reduces the rate **7-fold** in seawater and 5-fold in deicing salt; 0.25 mm ("typical of that used in wet layup") reduces it **21-fold** and 23-fold — galvanic-corrosion literature on CFRP/metal couples | [M]/[DR] |

---

## Appendix — reproducibility

Every `[CALC]` figure derives from the equations stated inline plus the source files' own geometry. The seven calculation groups are:

1. **Loads.** N = q·S_panel·C_N; components N cos Γ / N sin Γ; boom torque N·ȳ with ȳ = (b/3)(1+2λ)/(1+λ); M_root = F_z·L_eff + w·L²/2.
2. **Effective cantilever.** Two-support overhang: δ = P(L³/3 + L²a/3)/EI, θ = P(L²/2 + La/3)/EI; L_eff from matching a pure cantilever.
3. **Laminates.** Classical lamination theory: micromechanics (rule of mixtures axial, Halpin–Tsai transverse with ξ = 2 and shear with ξ = 1, E_f1 = 230 GPa, E_f2 = 15 GPa, G_f = 15 GPa, E_m = 3.2 GPa, G_m = 1.25 GPa), Q̄ transformation, A-matrix, E_x = 1/(a₁₁h), G_xy = 1/(a₆₆h); woven modelled as paired half-thickness cross-plies with a 0.95 crimp knockdown. Cured ply thickness = areal weight/(1,800·Vf).
4. **Sections.** EI = Σ E_i·π/4(r_o⁴−r_i⁴), GJ = Σ G_i·π/2(r_o⁴−r_i⁴), summed layer by layer from the inside out so a hybrid Al/CFRP wall is handled exactly rather than smeared.
5. **Modes.** Euler–Bernoulli beam FE, 100+ elements over x = 0.598 → 4.2436, consistent mass, pinned at x = 0.8933 and 1.1354, tip mass 1.6 kg and pitch inertia 0.174 kg·m² at x = 4.0936; torsional rod FE fixed at the mid-let-in with 0.365 kg·m² at the tail. Generalised eigenproblem via `scipy.linalg.eigh`.
6. **Aeroelasticity.** K_θ = L²/(2EI); q_div = 1/(S_h,eff,boom·a_t·K_θ); amplification = 1/(1 − q/q_div). Forced response by modal superposition with H = 1/√((1−r²)² + (2ζr)²).
7. **Slipstream.** T = ηP/V; a from T = 2ρA V²a(1+a); R_wake/R = √((1+a)/(1+2a)).

Anyone re-deriving these should get the same answers; where they do not, the discrepancy is more interesting than the number.
