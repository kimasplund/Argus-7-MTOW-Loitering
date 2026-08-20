# ARGUS-7 — EMPENNAGE CONFIGURATION TRADE STUDY

**Date:** 2026-08-20 · **Scope:** the tail and its supporting structure for the 250 kg MTOW / 9.26 m span / AR 22 configuration of `docs/argus7_design_report.md` · **Companion to:** `research/boom_construction_pack.md`, `research/materials_pack.md`

**The question this pack was written to answer:** would deleting the twin booms and hanging the tail off the fuselage ahead of the pusher buy endurance, and is there a tail arrangement that beats the inverted-V on the sponsor's stated criterion of *longevity* — 70 Hz blade-passage exposure, 28.4 million cycles per mission, and control redundancy over five to seven unattended days?

---

## 0. How to read this

Provenance tags are the same as `materials_pack.md` §0:

| Tag | Meaning |
|---|---|
| **[DS]** | Manufacturer datasheet, quoted verbatim |
| **[M]** | Measured / published experimental data |
| **[CALC]** | Computed here from the committed geometry and load cases; equations given inline, reproducible from the appendix |
| **[EST]** | Engineering estimate — a judgement, not a measurement |
| **[DR]** | Derived from a secondary source that itself cites a primary one |
| **[UNV]** | Unverified — needs test or vendor confirmation |

**Two rules applied throughout.** Where this pack disagrees with a source in the repository it says so and shows the arithmetic (§8 lists every such disagreement). Where a number is an assumption dressed as a result, it is tagged and its sensitivity is given.

**Calibration check on the endurance model.** Every Δh in this pack comes from a re-implementation of the report's §4 loiter model (ISA 4,000 m, ρ = 0.81935 kg/m³, S = 3.9 m², AR 22, e = 0.85, C_L = 1.6/1.15² = 1.2098, η_prop = 0.84, 500 W payload through a 0.75 alternator path, BSFC 270 g/kWh, step-integrated 250 → 148.5 kg over 20,000 steps). It returns **112.99 h** against the report's 112.8 h [1]; fed C_D0 = 0.016 it returns **+8.59 h** against the report's stated +0.36 d = +8.64 h [1]; fed C_D0 = 0.022 it returns **−3.85 h** against `materials_pack.md` §6.8's −3.8 h [2]. It is a faithful reproduction and is used only for *relative* deltas, scaled onto the report's headline 112.8 h. [CALC]

**The two exchange rates used everywhere below** [CALC, this pack]:

| Rate | Value | Cross-check |
|---|---|---|
| Parasite drag | **1.97 h per 0.001 of C_D0** near the baseline (2.03 at 0.019, 1.96 at 0.021) | `materials_pack.md` §6.8 uses 1.9; report §4 implies 2.16 on the improving side |
| Structure mass, MTOW fixed, fuel displaced | **1.51 h per kg** | `materials_pack.md` §6.8 states 1.5 h/kg |

**Where this pack got its candidate configurations.** Six layouts were analysed independently and each was then put through an adversarial verification pass. **All six analyses were refuted on at least one load-bearing number.** Where a verifier corrected an analysis, *this pack uses the verifier's number and says so at the point of use.* The single exception is the boomless case, which I recomputed from the committed geometry myself; my figure (+8.2 h) sits inside the verifier's band and both are quoted.

---

## 1. Answer first

**Three findings, in descending order of how much money they are worth.**

**Finding 1 — the premise the whole trade was commissioned on is geometrically false, and it does not discriminate between any of the six configurations.** The booms are not in the propeller slipstream. Prop tip radius is 0.4065 m, boom inner surface is at 0.5756 m, and the slipstream *contracts* aft to 0.367–0.393 m, so the clearance is 169 mm to the tip path and 183–209 mm to the wake at every power setting [3 §6.1][CALC]. The excitation is near-field acoustic at **9–28 Pa**, not wake impingement at 281–562 Pa — a 20–40× difference — and the resulting vibratory strain is **0.011% against a matrix fatigue limit of 0.6%, a 55× margin** [3 §6.5][18][M]. **28.4 M cycles per mission, or 126 M by TBO, at a strain that causes no damage per cycle, is still no damage.** No configuration on this table can be scored on boom-laminate fatigue, because there is none to score.

**Finding 2 — deleting the booms is worth about +8 hours, it is the only positive number in the trade, and it is not worth taking yet.** At the geometrically self-consistent design point (§3) the boomless fuselage tail returns **+7 to +8 h (+0.3 d, +7%)**, band **+2 to +13 h**. It buys that by giving up 37% of pitch and yaw damping, by requiring a mandatory geometric CG rebalance, by planting the tail root in the same 0.5 m of tailcone as the belt reduction, exhaust, radiator and removable cowl, and by putting two tail wakes through the propeller disc at 2/rev — which converts the propeller from a commodity into a life-limited qualification article. It is the best configuration on the table and it is held open, not adopted.

**Finding 3 — the highest-value actions on this aircraft's tail are not configuration changes at all, and three of them are free.** They are already in the repository and none of the six configurations is needed to get them:

| Action | Cost | What it buys |
|---|---|---|
| **Ø50 × 150 mm spigot instead of two M6 screws** at the panel root | **0 kg, 0 drag** | Bearing MS **0.54 → 94**, a factor of **174** [3 §7.3] |
| **Boom diameter 90 → 110 mm** at the project's own stiffness requirement | −0.79 h drag, +5.41 h mass | **+4.62 h**, and it pays a stiffness debt the published baseline never paid [3 §9] |
| **Reduce the tail panel's polar inertia** | **0 kg, 0 drag** | f_t1 **× 1.41**, which is most of the fix for the one genuine resonance risk on the aircraft [3 §6.6] |
| **Close the structural loop at the wing**, not at the tail | 0.4 kg, 0 drag (−0.6 h) | Deletes the 1,626 N·m lateral peel path at the let-in joint [3 §8.3] |
| **Segment the ruddervators** (2 panels → 4 independently actuated segments) | +1.1 kg (−1.6 h) | Single-actuator-failure survival: **~60× reduction** in per-mission loss-of-control [CALC] |

**Together those five are worth roughly +2.4 h net and they retire both real longevity risks — the negative-margin tail joint and the 22.7 Hz torsional coincidence — for a fifth of the engineering risk of any configuration change on this table.** That is the recommendation. See §5.

---

## 2. The comparison table

All Δ are against the report's published baseline (112.8 h, C_D0 = 0.020, twin booms as drawn at 90 × 2.5 mm). **Δh figures are the adversarially-corrected values, not the original analyses' claims** — every original was refuted, and §2.2 lists what changed.

| # | Configuration | Tail arm | Tail area (S_h,eff / true panel) | ΔC_D0 | Δ mass | **Δ endurance** | Killer problems |
|---|---|---|---|---|---|---|---|
| **1** | **Twin-boom inverted-V** (baseline, as drawn) | 3.200 m | 0.310 / 0.561 m² | 0 | 0 | **0 (datum)** | Boom sized to 62.3 kN·m² gives 1.94° tail rotation against the project's own adopted 1.5° criterion — the published 112.8 h contains ~3.4 h of **unpaid stiffness debt** [3 §2.5]. Tail joint is two M6 screws at **MS 0.54 — fails at ultimate before fatigue** [3 §7.3]. f_t1 = 22.7 Hz against a possible ~23 Hz prop 1P at loiter, **1% separation for 122 continuous hours** [3 §6.4]. Report's stated V_h = 0.68 is arithmetically wrong (0.5765). Tail-area convention understates the drag build-up by 34% (§8.1). |
| **2** | **A-frame / portal tail on booms** (flat stabiliser + two fins between boom ends) | 3.200 m | 0.310 / 0.550 m² | +0.00079 | +2.44 kg | **−5.3 h** | The fatigue benefit it is sold on is **already bought more cheaply**: closing the loop is ×3.3–7.2 on joint life [3 §8.1], the spigot is ×174 for free. At boom level ~58% of the stabiliser span sits **inside r = 0.45 m aft of the disc** — the repo's own prohibition [3 §6.6] — so it must be raised to z = +0.50 m, where it clears by 50 mm and **creates a new 65–90 Hz resonator in the tail load path**. Directional stiffness *falls* 11–26% on its own corrected lift-curve slopes. CG +7.1% MAC, outside the 38–46% window. |
| **3** | **Boomless, tail on the aft fuselage** (inverted-V ahead of the disc) | **2.005 m** (fixed point) | 0.495 / 0.896 m² | **−0.00104** | **−5.24 kg** | **+7.3 h** (verifier) / **+8.2 h** (this pack) | The 2.0–2.2 m arm assumed in the tasking **does not geometrically exist** without eating the prop standoff: the arm–area–chord loop runs the wrong way (§3.1). Pitch and yaw damping fall **37%** (S_h·l² → 0.63 of baseline). CG moves ~34 mm **forward**, out of the window; must be fixed by geometry, not ballast (ballast costs more than the whole gain). Tail root shares 0.5 m of a 265→163 mm tailcone with the belt drive, exhaust, radiator and a removable cowl — the **+2.8 kg aft-structure allowance is the single largest downside risk in the ledger** and +5 kg is plausible. Two tail wakes into the disc at 2/rev makes the **propeller a life-limited article**. Tail tips drop to 636 mm below keel on a **35% narrower** lateral base. |
| **4** | **Tractor-conventional** (nose engine, 4.4 m fuselage, no booms) | 2.909 m | 0.341 / 0.341 + 0.251 m² fin | +0.0017 | −1.55 kg | **−1.0 h** | **Prop strike on every recovery.** No landing gear, parachute + belly airbag, 50–100 cycles; the blade tip sits 167 mm below the belly line 1.31 m ahead of the CG, so **7.3° of nose-down at touchdown** puts the blade in first against ±5–15° of canopy pendulum. The whole belly-recovered class (ScanEagle, Aerosonde, Penguin B, Bramor) is uniformly pusher for this reason. Puts the **entire 4.4 m fuselage and the inboard 60% of the empennage inside r = 0.45 m** for all 112.8 h — moving the airframe from a 55× strain margin to 1.4–2.7× [3 §6.5]. Exhaust plume across the EO/IR aperture for 113 h. |
| **5** | **X-tail on booms** (4 panels at ±45°) | 3.200 m | 0.335 / 0.669 m² | +0.0001 | +1.43 kg | **−2.4 h** | **Does nothing about the 70 Hz axis it was proposed for** — same booms, same station, same excitation — and *doubles* the joint count in the excited region (2 boom-root joints → 4). Joints, not laminate, are where fatigue lives here. Its one real benefit (4→3 control allocation) is **fully reproduced by segmenting the inverted-V's ruddervators for +1.1 kg / −1.6 h** with no area growth, no lift-curve-slope loss, no CG excursion and no boom re-spec. The residual it charges ~0.8 h for is tolerance to loss of a whole panel, a ~10⁻⁵/mission event. Redundancy is worth **zero** without FDIR that neither ArduPlane nor PX4 ships. |
| **6** | **Pylon pusher** (engine aft, propshaft raised 0.54 m, single cranked tailcone) | 3.200 m | 0.310 / 0.561 m² | −0.00064 | −0.42 kg | **−2.2 h** | **Cannot meet prop-tip clearance and modal separation simultaneously.** At the drawn 0.54 m hub height the tailcone sits at r = 0.463 m from the thrust axis — 0.070 D, against the ≥0.2 D floor the whole 20 Pa near-field argument rests on [3 §6.1][16][DR]. Raising the hub to the compliant 0.651 m drops the pylon lateral mode from 93 to **71 Hz — dead on 2-blade BPF**, on the member carrying all the thrust. The pylon (5.2–6.0 kg) **eats the entire boom saving**: net −0.42 kg. 233 N·m of nose-down thrust moment at climb power, zero at idle. Whirl flutter becomes a live analysis item. |

### 2.1 The same table as a ledger

| # | Configuration | Δ drag h | Δ mass h | Δ other h | **Net Δh** | Band | Confidence |
|---|---|---|---|---|---|---|---|
| 1 | Twin-boom inverted-V | 0 | 0 | 0 | **0** | datum | — |
| 3 | Boomless fuselage tail | **+2.04** | **+7.91** | −1.7 (installed η) | **+8.2** | +2 … +13 | medium-low |
| 4 | Tractor-conventional | −3.35 | +2.34 | 0 | **−1.0** | −7.9 … +5.7 | low |
| 6 | Pylon pusher | +1.37 | −0.57 | −2.26 η, −0.92 trim | **−2.2** | −6 … +2 | low |
| 5 | X-tail on booms | −0.22 | −2.15 | 0 | **−2.4** | −1.6 … −4.2 | medium |
| 2 | A-frame on booms | −1.56 | −3.68 | 0 | **−5.3** | −4.3 … −6.5 | medium |

**The spread from best to worst is 13.5 h — 12% of the mission, and less than the 16.6–23.3 h that `materials_pack.md` §11 puts on the wing skin decision alone.** The empennage configuration is not where this aircraft's endurance lives. It is where its *durability* lives, and §4 scores that separately.

### 2.2 What the adversarial pass changed, and why the corrected numbers are used

Every one of the six analyses was refuted. The corrections that moved a headline number:

| Config | Claimed | Corrected | The error |
|---|---|---|---|
| **A-frame** | −3.7 h | **−5.3 h** | Directional stiffness computed with a = 3.5/rad at AR_eff 2.1; the DATCOM relation the same analysis used elsewhere gives **2.69/rad**. Corrected, the A-frame *loses* 11–26% of yaw stiffness and the fins must grow to 0.29 m². Frequency-tuning mass under-budgeted ~2× (0.5 kg allowed for a 2.7× EI increase that needs ~1.8 kg of caps). |
| **Boomless** | +8.5 h | **+7.3 h** | Mass ledger did not sum: −9.77 −3.0 +5.05 +2.8 = **−4.92 kg, not −5.62 kg**, and a +0.4 kg metal heat-shielded root fitting the analysis itself declared mandatory was never booked. ΔC_D0 internally inconsistent between its two cases (0.000802 vs 0.000647 per m²). |
| **Tractor** | +0.6 h | **−1.0 h** | Its "decisive number" — that 110 mm booms move f_b2 from 76 to 93 Hz, "34% clear" — used the **110 mm answer as the 90 mm baseline**. `boom_construction_pack.md` §6.3 FE gives 61.5 Hz at 90 mm and 75.8 Hz at 110 mm: the bigger boom carries the mode *through* 70 Hz, not clear of it. Drag ledger omitted the un-scrubbed 0.00270 residual, the tripped fuselage nose and an unphysical Meredith credit at 35.6 m/s. |
| **X-tail** | −5.5 h | **−2.4 h** | 47% of its mass delta was a +1.50 kg boom wall step charged against a 90 × 2.5 mm tube the repo says "has never been sized"; on the recommended 110 mm boom the step is unnecessary (85 mm tip deflection at +19% load, inside the 93 mm already accepted). Its a_t deficit was over-stated 3–5× — the X's upper pair is joined AR 6.011 against the V's 6.00. |
| **Pylon** | −2.1 h | **−2.2 h** | Headline barely moved but the supporting case collapsed: the claimed r = 0.570 m tailcone clearance is actually **r = 0.463 m** (the 5.5° crank buys 4.8 mm across a 50 mm gap, not 111 mm), so the compliance check inverts and the "0.4% clear of the keep-out band" pylon mode is unobtainable at a compliant hub height. |
| **Baseline** | 0 | **0** | Correct as stated. Its proposed −1.5 h "honest baseline" correction (§8.1) is **real but is a datum shift shared by every equal-effectiveness tail**, so it cancels out of every pairwise comparison and is not a delta for any configuration. |

---

## 3. The sponsor's actual question: delete the booms, put the tail on the fuselage

**Short answer: it works, it is the best number in this trade, and it is worth +7 to +8 hours — about 7% of the mission, a third of a day. It is not free, the four things it costs are not yet priced, and one of them (the propeller) is a new life-limited part.**

### 3.1 The 2.0–2.2 m arm the tasking assumes does not exist

The tasking's first-order estimate holds V_h at a 2.1 m arm. Running that through the committed geometry generator (`argus7/design/geometry.py::derive_tail_panel`, which sizes each panel at S_h/(2cos²Γ), span = √(A·AR_p), unswept, quarter-MAC on the tail station) shows why it cannot be built:

| Arm | S_h,eff | Panel total | Root chord | Root TE to prop disc |
|---|---|---|---|---|
| 3.200 m (baseline, on booms) | 0.310 m² | 0.561 m² | 0.395 m | tail is **0.950 m aft** of the disc |
| 2.400 m | 0.413 m² | 0.748 m² | 0.456 m | **−199 mm — root TE is inside the disc** |
| **2.100 m (the tasking's assumption)** | 0.472 m² | 0.855 m² | 0.487 m | **+76 mm = 0.094 D** |
| **2.005 m** | 0.495 m² | 0.896 m² | 0.499 m | **+163 mm = 0.200 D** |
| 1.794 m | 0.553 m² | 1.001 m² | 0.527 m | +350 mm = 0.431 D |
| 1.623 m | 0.611 m² | 1.107 m² | 0.554 m | +500 mm = 0.615 D |

[CALC] **The loop runs the wrong way.** Shortening the arm grows the area, which grows the chord, which eats the standoff again, which forces the arm shorter still. At the tasking's 2.10 m the tail root trailing edge stands **76 mm — 0.094 propeller diameters — ahead of the blades.** That is not a design; it is a wake generator bolted to the disc.

**The design point adopted here is arm = 2.005 m, S_h,eff = 0.495 m², total panel 0.896 m², root chord 0.499 m, standoff 163 mm = 0.200 D** — the same 0.2 D floor that `boom_construction_pack.md` §6.1 cites for radial prop clearance [16][DR], applied axially. It is the *minimum* defensible standoff, not a comfortable one: pusher-pylon practice wants 0.5–1.0 D ahead of the disc for a wake generator, which here would force the arm to 1.62 m and S_h to 0.611 m² (1.97× baseline). **Sensitivity: every 0.1 D of extra standoff demanded costs roughly 0.6 h of the answer below.** [CALC][EST]

**This is precisely the loop the twin booms exist to break.** They put the tail 0.950 m *aft* of the disc in clean air, at any arm the designer wants, for 9.4% of C_D0 and ~9.4 kg.

### 3.2 The ledger, item by item

**Drag.** Component build-up from `materials_pack.md` §6.7, with the effective flat-plate areas back-solved to per-m² skin-friction coefficients so the substitution is honest rather than area-for-area:

| Item | S_wet | f = C_D0·S | C_f,eff = f/S_wet |
|---|---|---|---|
| Twin booms, 2 × 3.6456 × Ø0.090 | 2.0615 m² | 0.007332 m² | **0.003557** |
| Inverted-V tail, as billed in §6.7 (0.4172 m² panel) | 0.8553 m² | 0.004836 m² | **0.005654** |

[CALC] **The tail section runs at 1.59× the boom's drag per unit wetted area** — a thick, low-Re, low-fineness NACA 0010 at a much lower local Reynolds number against a smooth slender cylinder. So the tasking's first-order "net saving 1.450 m² of 15.081 m², ΔC_D0 ≈ −0.00125, ≈ +2.7 h" is optimistic on two counts: the tail has to grow 1.60×, not 1.52×, and each square metre it grows costs 59% more than the boom area it replaces.

| | Value |
|---|---|
| Delete boom wetted area | −2.0615 m² |
| Tail wetted area, 0.561 → 0.896 m² panel at k_wet = 2.05 | +0.6863 m² |
| Net wetted | **−1.375 m² of ~15.2 m² (−9.0%)** |
| Δf | −0.007332 + 0.003881 = **−0.003451 m²** |
| ΔC_D0 raw | −0.000885 |
| ΔC_D0 after the build-up's own interference + cooling scale-up (×1.1713) | **−0.001037** |
| **Endurance** | **+2.04 h** |

[CALC] Against the tasking's +2.7 h. If the booms are first re-sized to the recommended 110 × 2.0 mm (which the project's own boom pack advocates on its own merits), the boom drag to be deleted rises to 0.00230 and the credit grows to **−0.00153 → +3.01 h**.

**Mass.** The number that carries the answer, and the one that needs the most care. The baseline boom system is *not* 7.78 kg: that is the bare tube of a 90 × 2.5 mm boom which **fails the project's own adopted 1.5° tail-rotation criterion at 1.94°** [3 §2.5]. Installed, with the local reinforcement `boom_construction_pack.md` §14 itemises (2 collars 0.30 + let-in over-wrap 0.24 + 6 bulkheads 0.18 + 2 tail sockets 0.50 + 2 splice sleeves 0.44):

| Boom build | Tube | Reinforcement | Installed |
|---|---|---|---|
| As drawn, 90 × 2.5 (non-compliant, 1.94°) | 7.78 kg | 1.66 kg | **9.44 kg** |
| 90 mm sized to the 1.5° requirement | 10.06 kg | 1.66 kg | 11.72 kg |
| **Recommended COTS 110 × 2.0** | 7.54 kg | 1.66 kg | **9.20 kg** |

[3 §14][2 §4.2]

| Boomless mass ledger | kg |
|---|---|
| Delete boom system (as-drawn installed) | **−9.44** |
| Tail structure growth, 0.561 → 0.896 m² panel at ~3.0 kg/m² true area, plus scaled root fittings | +1.30 [EST] |
| Metal heat-shielded root fitting (the bondline sits ≤0.3 m from the exhaust of an engine running 112.8 h continuously; EA 9394 loses 28% of lap shear at 82 °C [2 §8.3][6][DS]) | +0.40 |
| Aft-fuselage frames, tail-root cantilever rings and cutout reinforcement | **+2.80** [EST], band +1.5 … +5.0 |
| Delete control and power runs down two booms | −0.30 [EST] |
| **Net** | **−5.24 kg → +7.91 h** |

**Installed propulsive efficiency.** Two tail panel wakes now convect into the disc. Each blade crosses each wake once per revolution: at 2 blades and 35 rev/s that is 70 Hz, **28.4 M cycles per mission and 126 M by the 500 h TBO — the identical cycle count the tasking was worried about, transferred from the booms onto the propeller.** At 0.2 D standoff the wake deficit at the disc is of order 12–18% of local axial velocity [EST]; converted to blade incidence at 0.7 R and attenuated by the Sears function at a reduced frequency k ≈ 3–4, the residual is roughly ±15–20% of cyclic blade load on a mean C_l ≈ 0.5. Installed efficiency penalty **−1 to −2%**; at η ∝ endurance that is **−1.1 to −2.3 h**, taken at **−1.7 h**. [EST][CALC] This term is not settleable on paper (§6).

**Net: +2.04 + 7.91 − 1.7 = +8.2 h.** The adversarial verifier, working the same problem at a more conservative 0.431 D standoff and a heavier tail estimate, returns **+7.3 h**. Both are inside a band of **+2 to +13 h**, dominated by the aft-structure allowance.

**Take the answer as +7 to +8 hours: +0.3 days, +7% of the mission.**

### 3.3 What the +8 hours costs, and none of it is in the ledger above

**(a) 37% of the pitch and yaw damping.** Holding V_h constant while the arm goes 3.200 → 2.005 m preserves the *static* margin contribution exactly and destroys the *dynamic* one: C_mq and C_nr scale with l², and S_h·l² falls to **0.626 of baseline**. On an AR-22 airframe whose V_v is only 0.0223 [CALC], which simultaneously loses 0.59 m² of boom side area aft of the CG, that is a real and un-costed degradation of short-period and Dutch-roll damping over a 112.8 h autopilot-flown loiter — and it feeds directly into 70 Hz EO/IR line-of-sight jitter through a shorter, stiffer path to the payload bay.

**(b) A mandatory CG rebalance that cannot be done with ballast.** Removing 9.44 kg centred at x ≈ 2.42 m and adding 4.2 kg centred at x ≈ 2.8 m moves the CG **~34 mm forward, to ≈ 34% MAC, outside the report's own 38–46% window.** Left uncorrected the trimmed tail download costs ΔC_D ≈ +0.0013 — **more than the entire parasite saving** — and the configuration is net draggier than the baseline. It must be fixed geometrically (wing forward ~33 mm, or the 20 kg chin gimbal aft ~0.4 m). Aft ballast to fix it costs ~4.2 kg = −6.4 h and erases most of the gain. [CALC]

**(c) The tail root lands in the worst bay on the aircraft.** The root spans roughly x = 2.7 → 3.2 m, sharing 0.5 m of a 265 → 163 mm tailcone with the belt reduction, prop-shaft bearing housing, exhaust, radiator and cooling ducts — a shell that must also open as a removable cowl for a 500 h TBO. No spar carry-through is possible; each panel cantilevers off its own machined frame ring, and every system in that bay is a cutout that has to react the root moment. **The +2.8 kg allowance is the single largest downside risk in this pack.** At +5 kg the answer falls to ≈ +4.9 h; at +7 kg it falls to ≈ +1.9 h and the trade is a wash.

**(d) The propeller becomes a life-limited qualification article.** Two wake sheets at 2/rev, 126 M cycles to TBO, ±15–20% cyclic blade load. Survivable for a composite blade on a metal hub *with a stated life*; disqualifying for the wooden props normal at 32 inches; and it adds +5 to +10 dB on the blade-passage tone, which matters for ground crew and for launch-site community noise in a disaster zone. **The 70 Hz problem is not removed. It is relocated from a member with a 55× strain margin onto the one rotating part that has to survive 500 h.**

**(e) Ground contact gets narrower and deeper.** This point is usually argued wrongly, so it is worth stating precisely. The **booms are not a ground-contact base** — they sit on the fuselage centreline at z = 0, 240 mm *above* the keel. What contacts is the tail. On booms the V tips sit at **y = ±1.303 m, 374 mm below the keel**; boomless they sit at **y = ±0.862 m, 636 mm below the keel** [CALC]. So the boomless arrangement has a base **34% narrower and 70% deeper** — worse for roll-over onto a 9.26 m AR-22 wingtip at 6 m/s with drift, on an aircraft with no landing gear recovered 50–100 times. (The README's 385 mm figure for the boom-mounted case is 11 mm optimistic against the committed geometry's 374 mm.) The sponsor has already ruled tail grounding acceptable by making the panel a serviceable item; **the sponsor has not ruled on the lateral base, and this is a new point.**

### 3.4 Verdict on the boomless question

**Yes, it gains, and the number is +7 to +8 hours.** That is the largest single figure in this trade and it is the only positive one. It is also 7% of the mission, against a 5–7 day target that needs 20–40%.

It is not adopted, for one reason that can be settled and one that cannot yet: the **+2.8 kg aft-structure allowance is unverified in a bay that already contains the engine**, and the **installed-efficiency and blade-load consequences of two wake sheets through the disc cannot be settled on paper**. Both are Phase-2 items (§6). If the aft structure closes at ≤ +1.5 kg and the wake ingestion costs ≤1% of η, boomless wins outright at ≈ +11 h and should be adopted. If the aft structure comes in at ≥ +5 kg, or the propeller has to become a custom life-limited part, it does not.

---

## 4. Longevity: does anything beat the inverted-V?

The sponsor asked for the tail to be scored on longevity — the 70 Hz propwash exposure, 28.4 M cycles per mission, and control redundancy over five to seven unattended days. **Answered in three parts, because the three parts have very different answers.**

### 4.1 The 70 Hz fatigue exposure: not a discriminator, for any configuration

`boom_construction_pack.md` §6.1 and §6.5 settle this and the arithmetic reproduces [CALC]:

| | Value |
|---|---|
| Prop tip radius | 0.4065 m |
| Boom inner surface | 0.5756 m → **169 mm clearance = 0.208 D** |
| Contracted slipstream radius, loiter (a = 0.078) / full power (a = 0.298) | 0.393 / 0.367 m → boom clear by **183 / 209 mm** |
| Tail panel minimum radius from thrust axis (committed outboard-and-down geometry) | **0.621 m** |
| Unsteady pressure, inside the wake | 281–562 Pa |
| Unsteady pressure, **at 0.21 D outside**, differential across a 0.11 m cylinder at a 4.9 m acoustic wavelength | **9–28 Pa** |
| Peak vibratory strain at Q = 25 | **0.011%** |
| Matrix fatigue-limit strain ε_mf [18][M] | 0.6% → **55× margin** |

**28.4 M cycles per mission and 126 M by TBO at 0.011% strain is not a fatigue case.** It is 55× below the strain at which carbon/epoxy accumulates matrix damage at all. The README's own "Verified non-issues" section still carries the superseded claim that the booms "sit in its slipstream"; that sentence contradicts the same file's "Known gaps" entry and should be deleted (§8.4).

**What follows for the trade.** The 70 Hz axis does not rank the six configurations, because none of them has a boom-laminate fatigue problem to fix. What the 70 Hz axis *does* do is generate a **prohibition** — *nothing structural inside r = 0.45 m of the thrust axis aft of the prop plane* [3 §6.6] — and that prohibition kills two candidates outright:

- **The A-frame / H-tail at boom level fails it.** A stabiliser spanning boom-tip to boom-tip runs from y = −0.62 to +0.62 through the wake at 281–562 Pa, reaching 0.44% strain at Q = 50 — a 1.4× margin, not acceptable. It survives only by being raised to z = +0.50 m, where it clears by 50 mm and buys a new 65–90 Hz resonator in the tail load path.
- **The tractor fails it comprehensively**, putting the entire 4.4 m fuselage (r = 0.24 m) and the inboard ~60% of the empennage inside the wash for all 112.8 h.

And it constrains a third: the **pylon pusher** cannot simultaneously hold ≥0.2 D of tip clearance (which needs a 0.651 m hub) and keep its pylon lateral mode out of the 59.5–92.6 Hz keep-out band (at 0.651 m the mode falls from 93 to **71 Hz**, on the member carrying all the thrust).

**One caveat that could reverse all of it.** The excitation frequency is not established. `boom_construction_pack.md` §6.2 shows the propulsion set does not close: **C_P = 0.911 is required for 17 kW at 2,100 rpm on a 0.813 m propeller against a physical ceiling near 0.25** — a 4× inconsistency. Blade-passage frequency is therefore uncertain **from ~47 Hz to ~107 Hz**. Every keep-out-band statement in this pack, and every one in the six analyses, inherits ±50% uncertainty. **This is the highest-value open question in the programme and it is a propulsion question, not a structures one.**

### 4.2 What the real longevity items are, and they are the same for every configuration

| Rank | Item | Why it is the real one | Cost to fix |
|---|---|---|---|
| **1** | **The panel-root joint.** Two clearance-fit M6 screws at 60 mm centres carrying 330 N·m gives **306 MPa of bearing against a 165 ± 28 MPa design allowable — MS 0.54, a negative margin at ultimate before fatigue is considered** [3 §7.3][19][DR]. Composite bolted joints fail by four-stage hole elongation and fretting; preload is lost as the hole wears, which accelerates the wear. There is no mechanism by which this joint survives 28 M cycles. | It is the only *negative margin* anywhere in the empennage | **Ø50 × 150 mm spigot: 1.76 MPa, MS 94. Zero mass, zero drag, ×174.** Standard removable-tailplane practice on gliders |
| **2** | **f_t1 = 22.7 Hz against a possible ~23 Hz prop 1P at loiter rpm.** A **1% separation held for 122 continuous hours** — `boom_construction_pack.md` §6.4 calls it "the one genuine resonance risk in the mode map" | It is the only mode in the map that is both close and continuously excited | Reduce panel polar inertia (**free, ×1.41**); close the loop at the wing (0.4 kg, ×1.30–1.55); add ±45 (4 kg, ×1.7). Do the first two |
| **3** | **The wing let-in joint under lateral load.** The 1,626 N·m lateral ultimate moment prises the boom out of a 111° open saddle, putting a component **normal to the bondline** — EA 9394's T-peel is 22 N/25 mm, 800× below its shear [6][DS] | It is the joint whose failure loses the aircraft | Full-circumference collars + a 360° ±45 over-wrap, **≈0.20 kg per boom** [3 §7.2] |
| 4 | f_b2 at 61.5 Hz (90 mm) / 75.8 Hz (110 mm), both inside the 59.5–92.6 Hz band | Real, but it does not matter: the amplitude at that mode is 20 Pa, not 400 | **Nothing. There is no escape by diameter (needs 137–176 mm) and none is needed** |

**Every one of these is configuration-independent, and three of the four fixes cost nothing.** No tail re-architecture on this table addresses item 1 or item 3 at all, and only the A-frame addresses item 2 — at −5.3 h, against ×1.41 for free.

### 4.3 The X-tail on control redundancy: right question, wrong answer

The redundancy argument is the one genuinely valuable thing in the X-tail proposal, and it deserves to be scored properly rather than dismissed.

**The two-surface inverted-V is single-fault critical.** Lose one ruddervator and the surviving one can still trim pitch by cancelling the vertical component, but the yaw components no longer cancel and must be held on a permanent sideslip; a runaway to hard-over is unrecoverable. At an assumed electromechanical actuator MTBF of 20,000 h [EST][UNV — COTS UAV servos run 2,000–10,000 h; this assumption swings the answer 5× and must be stated loudly]:

| Configuration | P(loss of control), 112.8 h mission | Over 500 h TBO |
|---|---|---|
| 2 surfaces (any single failure is critical) | **1.12%** | 4.88% |
| 4 surfaces (needs 2 failures) | **0.019%** | 0.354% |
| **Ratio** | **59×** | 13.8× |

[CALC] At 10,000 h MTBF the mission ratio is 30×; at 50,000 h it is 148×. **The sponsor is right to refuse to dismiss this: on a five-day unattended flight over a populated disaster zone, a factor of 30–150 on loss-of-control probability is worth real money.**

**But it is an argument for redundant actuation, not for an X-tail.** Split each inverted-V panel into independently actuated inboard and outboard segments:

| | X-tail | **Segmented ruddervators** |
|---|---|---|
| Independent control surfaces | 4 | **4** |
| Control allocation | 3 × 4 | **3 × 4, identical topology** |
| Single-jam tolerance | Yes — the diagonal surface nulls it | **Yes — the co-panel partner cancels it exactly, producing a parallel control vector** |
| Tail area growth | +19% true area | **0** |
| Lift-curve-slope penalty | 2–4% (free-tipped pairs) | **0** |
| CG shift | +4.2% MAC | **≈0** |
| Boom re-spec | none needed on 110 mm booms | **none** |
| Extra joints in the excited region | **2 boom-root joints → 4** | **0** |
| **Cost** | **−2.4 h** | **+1.1 kg = −1.6 h** |

[CALC][EST for the segmentation mass]

**The X-tail's exclusive residual over segmentation is tolerance to structural loss of an entire panel — a ~10⁻⁵-per-mission event — and it charges roughly 0.8 h for it while adding two more bolted joints at the highest-cycle station on the airframe.** On the sponsor's own longevity criterion, doubling the joint count in the excited region is a *loss*, because §4.2 establishes that joints, not laminate, are where this aircraft's fatigue lives.

**And the redundancy of either arrangement is worth exactly zero without FDIR.** The 3 × 4 allocation matrix is trivial arithmetic. Knowing *which* of four surfaces has failed, on an unattended aircraft 400 km from an operator, and re-mixing around it, is not — and without it the allocator keeps commanding a dead surface while the aircraft flies with a growing trim error until it departs. Neither ArduPlane nor PX4 ships a four-surface fault-reconfiguring mixer. That is custom flight-control software on a 250 kg SAIL III–IV airframe, landing squarely on the report's own premortem failure mode #2 (one pair of hands, three sequential full-time workstreams) and widening the Design Verification Report scope of mode #4.

### 4.4 Longevity verdict

**No arrangement on this table beats the inverted-V on longevity, and the inverted-V is not being defended on merit — it is being defended because the alternatives fix nothing it has wrong.**

The honest statement of the inverted-V's position: it is **never justified anywhere in the report or the design pack**, its one distinctive property (proverse roll-yaw coupling) is worth close to nothing on an aircraft specified for gentle turning only, and the same dihedral-effect trim could be had free by reducing the 3° wing dihedral. But the two most-cited arguments *against* it are both wrong:

- **"It costs 81% more wetted area than an equal-effectiveness flat surface"** — false. cos²Γ + sin²Γ = 1 makes a V-tail's total panel area exactly equal to S_h,eff + S_v,eff: **0.310 + 0.251 = 0.561 m², which is the V's panel area to four figures.** An H-tail providing the same horizontal *and* vertical function has the same planform and essentially the same wetted area. The claimed +0.51 m² / −1.7 h penalty is approximately zero.
- **"Its ventral hang-down makes it ground first, forcing a demountable joint at the highest-cycle station"** — the sponsor has already ruled tail grounding acceptable, and the joint at that station has to be a spigot regardless of tail topology.

**The inverted-V survives this trade by default.** Fix its joint, re-size its booms, lighten its panels, and segment its ruddervators if the redundancy is wanted.

---

## 5. Ranked recommendation

### The ranking

| Rank | Option | Δh | Decisive reason |
|---|---|---|---|
| **1** | **Twin booms + inverted-V, re-specified** — 110 × 2.0 mm booms, Ø50 × 150 spigot tail joint, wing-station loop closure, lightened panels, segmented ruddervators | **+2.4 h** net (+4.62 boom, −0.6 loop, −1.6 segmentation) | **It is the only option that fixes the two things actually wrong with this empennage** — a tail joint at MS 0.54 and a 1% frequency separation held for 122 h — and it does so for a fifth of the engineering risk of any configuration change. Three of the five actions cost nothing. |
| **2** | **Boomless fuselage tail** | **+7 to +8 h** | **The largest number in the trade, and the only positive configuration delta.** Ranked second, not first, because +8 h buys 37% of the pitch and yaw damping, a mandatory geometric CG rebalance, the tail root planted in the engine/exhaust/belt/cowl bay on a **+2.8 kg estimate that could be +5 kg**, and a propeller converted into a life-limited article. **Held open, not rejected.** |
| 3 | Tractor-conventional | −1.0 h | Endurance-neutral inside its own error bars, so it must be judged on the fatigue argument alone — where it moves the whole airframe from a 55× strain margin to 1.4–2.7× and violates the repo's own r = 0.45 m prohibition comprehensively. Plus a prop strike on every one of 50–100 recoveries. |
| 4 | Pylon pusher | −2.2 h | Cannot meet 0.2 D prop clearance and modal separation at the same time, at any t/c. The pylon eats the entire boom saving (net −0.42 kg). |
| 5 | X-tail on booms | −2.4 h | Dominated on every axis by segmented ruddervators, which reproduce its only real benefit for 29% of the cost with no area growth, no CG excursion and **no extra joints**. |
| 6 | A-frame on booms | −5.3 h | Pays 5.3 h for ×3.3–7.2 on joint life that a **free** spigot delivers at ×174; at boom level it violates the r = 0.45 m prohibition, and raised above it, it creates a new 65–90 Hz resonator in the tail load path. |

### The trade between #1 and #2 is genuinely close, and here is the tiebreaker

**#2 beats #1 by roughly 5 hours out of 112.8 — 4% of the mission.** That is inside the uncertainty of the aft-fuselage mass estimate on its own. It is not a clear win and it should not be presented as one.

**The tiebreaker is a single number nobody has computed: the mass of the aft-fuselage structure required to cantilever a 0.90 m² tail off a 265 → 163 mm tailcone that also contains the belt reduction, prop-shaft bearing, exhaust, radiator and a removable cowl.**

| Aft-structure mass | Boomless Δh | Beats #1 by |
|---|---|---|
| +1.5 kg | +10.2 h | 7.8 h — **adopt boomless** |
| **+2.8 kg (assumed)** | **+8.2 h** | **5.8 h — close** |
| +5.0 kg | +4.9 h | 2.5 h — **not worth the risk** |
| +7.0 kg | +1.9 h | −0.5 h — **keep the booms** |

[CALC] One shell-FE model of that bay settles the ranking. It is the highest-value single piece of Phase-2 work in this pack (§6).

### What would change the ranking

**Boomless wins outright if:**
- Aft-fuselage reinforcement closes at ≤ +1.5 kg, **and**
- Installed propulsive efficiency loss from two-wake ingestion is ≤1% (RANS/BEMT, §6), **and**
- A commercially available composite prop can be qualified for ±15–20% cyclic blade load at 126 M cycles without becoming a custom part.

**Booms win outright if:**
- Aft structure comes in at ≥ +5 kg, **or**
- The wing fuel-volume escalation (~50 L usable against 120 L required, README "Known gaps") forces fuselage tanks that compete with the tail root for the same aft bay, **or**
- The propeller has to become a life-limited item with a stated replacement interval — which converts an endurance gain into a recurring cost and an availability hit on a 500 h TBO.

**The whole trade re-opens if:**
- The propulsion set closes at a blade-passage frequency near 47 Hz or 107 Hz *and* the 9–28 Pa near-field pressure estimate turns out to be 200 Pa. That would take the boom strain margin from 55× to 2.7× and make frequency placement a real constraint for the first time. **Both inputs are currently [EST]** and both are cheap to measure (§6).
- V_D is fixed at a value materially different from the 200 km/h EAS carried over from `materials_pack.md`. Every tail load in this pack scales with q_D.

**What would *not* change it:** anything about the inverted-V versus a flat-plus-fins tail on wetted area (§4.4 — the areas are identical), anything about ground clearance (already ruled non-driving), or anything about boom laminate fatigue (55× margin).

---

## 6. What Phase 2 must simulate, and at what fidelity

Ordered by value per euro. The first item is not a simulation and it gates four of the others.

| # | Item | Method and fidelity | Effort | What it settles |
|---|---|---|---|---|
| **1** | **Close the propulsion set.** C_P = 0.911 required against a ~0.25 ceiling | **Analytic first** (reconcile power, rpm, diameter, reduction ratio), then **BEMT** with a real blade geometry — no CFD needed | **1 day** | Blade-passage frequency, currently uncertain 47–107 Hz. **Gates every keep-out-band statement in this pack and in `boom_construction_pack.md` §6.** Highest value in the programme |
| **2** | **Aft-fuselage tail-root structure, boomless case** | **Linear shell FE** (Nastran/CalculiX class, ~50–100 k DOF), real cutouts for exhaust, radiator, belt drive, cowl split lines; two load cases (879 N × 1.60 ultimate tail load; 5–11 g parachute-recovery inertia) | 3–5 days | **The tiebreaker between rank 1 and rank 2** (§5). +1.5 kg vs +5 kg is the whole difference |
| **3** | **Installed propulsive efficiency and blade cyclic load with two tail wakes** | Two-stage: (a) **steady RANS** of the airframe without the prop, k-ω SST, ~15–25 M cells, to extract the circumferential inflow deficit at the disc plane; (b) feed that as a prescribed non-uniform inflow into **BEMT or a lifting-line blade model** for the 2/rev load. Full sliding-mesh URANS (~40 M cells, 2° azimuth step, 20 revolutions) only if (b) shows >±20% cyclic load | 1 week for (a)+(b); 3–4 weeks if URANS is needed | The −1.7 h installed-η term and whether the propeller becomes life-limited. **Do not start with URANS** |
| **4** | **Dynamic stability at the short arm** | **Linear 6-DOF** from a vortex-lattice model (AVL/VSPAero class) — no CFD. Short-period and Dutch-roll damping at arm 3.200 vs 2.005 m, with and without 0.59 m² of boom side area | 2 days | The 37% damping loss in §3.3(a) — currently asserted from S_h·l², not modelled |
| **5** | **Empennage mode map with the real tail panel** | Extend the existing Euler–Bernoulli beam FE (`boom_construction_pack.md` §6.3, appendix group 5) with a **plate/shell model of the panel** and a parametric sweep of f_t1 against loiter rpm across the 47–107 Hz BPF band from item 1 | 2 days | f_t1 vs prop 1P — the one genuine resonance risk. Also prices the polar-inertia fix |
| **6** | **Recovery kinematics and roll-over** | **Rigid-body multibody** (6-DOF, contact), 6 m/s descent + 0–5 m/s drift, ±5–15° canopy pendulum, Monte Carlo ~1,000 cases; contact set = keel, tail tips, prop | 3 days | Whether the boomless tail's 34% narrower / 70% deeper base actually rolls the aircraft onto a wingtip, and whether the tractor's prop-strike case is as bad as §2 says |
| **7** | **Wing let-in joint under lateral load** | **Shell FE** of the 111° saddle, or a static test to 1.5× limit lateral load on a boom stub — the test is cheaper and better | 2 days FE / 1 day test | `boom_construction_pack.md` open question 10: the joint whose failure loses the aircraft, currently analysed only by hand couple |

**Two measurements worth more than any of the above, and both cost an afternoon** [3 §6.6, §12.2]:

- **A surface-mounted pressure sensor on the boom during a ground run.** Replaces the 9–28 Pa near-field estimate — the input that decides the entire fatigue argument — with a number.
- **A tap test on the finished boom with the tail fitted.** Measures f_b1, f_b2, f_t1 *and* the structural damping ratio (currently assumed 1–5%) directly from the decay envelope.

**Fidelity discipline.** Nothing in this trade needs LES, DES, or a coupled aeroelastic solver. The two places where high fidelity is genuinely justified are the prop-wake ingestion (item 3, and only if the cheap two-stage method flags it) and nothing else. The programme's top-ranked failure mode is the budget; a 40 M-cell URANS run started before item 1 closes would be spent computing the response to a frequency nobody has established.

---

## 7. Open questions

**These block conclusions in this pack**

1. **The propulsion set does not close.** C_P = 0.911 required for 17 kW at 2,100 rpm on an 0.813 m propeller against a ~0.25 ceiling; blade-passage frequency uncertain 47–107 Hz [3 §6.2]. Inherited from `boom_construction_pack.md` open question 2 and unchanged. **Every frequency statement in §4 carries ±50%.**
2. **V_D is not stated in the design report.** 200 km/h EAS is carried over from `materials_pack.md` §4.2 and is [EST]. Every tail load in every configuration scales with q_D [3 open question 1].
3. **The aft-fuselage structural mass for the boomless case is an [EST] with a ±3.5 kg band that exceeds the configuration's own net mass saving.** It is the tiebreaker between rank 1 and rank 2 (§5) and it is unpriced.
4. **The installed propulsive efficiency penalty for two-wake ingestion (−1 to −2%) is [EST], unmeasured, and the sign of the wake-momentum-recovery term is not established.** A pusher ingesting an upstream wake partially recovers its momentum deficit; the loss mechanism is inflow non-uniformity, not the deficit itself.
5. **The near-field blade-passage pressure at 0.21 D (9–28 Pa) is [EST].** It is the single input on which the 55× strain margin — and therefore the whole "no fatigue case" finding — rests [3 open question 8].
6. **Actuator MTBF is assumed at 20,000 h [EST][UNV].** COTS UAV servos are quoted at 2,000–10,000 h. The assumption swings the redundancy answer in §4.3 by 5×, and it is the only quantitative basis for spending 1.6 h on segmentation.

**Configuration**

7. **Which way do the tail panels point?** `argus7/design/geometry.py` computes `y_tip_offset = span·cos Γ` (positive, i.e. **outboard**-and-down) and `tail.dihedral_deg` is tagged `assumption` in the yaml. This pack assumes outboard throughout. If the panels are in fact inboard-and-down to a centreline apex, then the structural loop is already closed for free and boom torsion is rigidly restrained (f_t1 rises far above 22.7 Hz) — **but the panels then sweep to 0.4153 m from the thrust axis, inside the 0.45 m prohibition**, and §4.1 reverses [3 §8.4, open question 3]. **The apex route is therefore closed in both directions and cannot be used to fix f_t1.**
8. **The CG does not close at the CAD's wing station.** With `wing.x_le_frac: 0.22` (tagged `assumption`, sourced to nothing) the wing root LE sits at x = 0.748 m, and a plausible mass build-up puts the CG far aft of the 42% MAC target: 25 kg of pusher powertrain at x ≈ 3.05 m plus the empennage generate ~75–87 kg·m about the target CG, against ~42 kg·m recoverable with all 63 kg of payload, avionics and recovery jammed at x = 0.30 m. Balance needs the wing root LE near **x = 1.24–1.55 m**. **Configuration-independent — it invalidates every static-margin figure in the report until fixed — but boom length is invariant under that translation** (it is derived as tail_qc − wing_le + 2 × clearance), so every boom number in this pack survives it.
9. **The wing cannot hold its fuel** (~50 L usable against 120 L required, README "Known gaps"). The 1.51 h/kg exchange rate that carries ~95% of the boomless gain assumes MTOW fixed and structure displacing fuel. Relocating 101.5 kg to the fuselage reopens the CG-travel problem *and* competes with the boomless tail root for the same aft bay.
10. **The `booms.diameter_m: 0.09` value has never been sized** and is tagged `assumption`. 110 mm is worth +4.62 h and needs `wing.z_offset_m` changed with it (burial goes 19.5 → 39.5 mm on a 75.2 mm-thick section), with `test_wing_boom_interference_volume_is_plausible` re-derived [3 §9, open question 5].

**Structural and control**

11. **Segmented-ruddervator mass (+1.1 kg) is [EST]** — two extra servos, two extra hinge lines, two extra control runs. It has not been laid out.
12. **No FDIR exists.** Four-surface redundancy is worth zero without fault detection, isolation and reconfiguration, and neither ArduPlane nor PX4 ships a four-surface fault-reconfiguring mixer. Scope this before crediting any redundancy argument.
13. **Flutter is unassessed for every configuration.** `materials_pack.md` already calls the tail "a flutter article"; the boom bending/torsion frequency ratio is 2.4–3.0 (clear of the ~1.5 coalescence zone) but no configuration has been checked for coupled antisymmetric-boom-bending / tail-pitch modes.
14. **Tail-joint inspection intervals** (25 h then 50 h, replace at 2% hole elongation) are engineering judgement, not measured, and only matter if a bolted joint is adopted against the spigot recommendation [3 open question 6].

---

## 8. Disagreements with the repository, stated with the arithmetic

### 8.1 The tail-area convention understates the baseline drag build-up by 34%

`argus7/design/geometry.py::derive_tail_panel` computes `panel_area = area_h_m2 / (2 cos² Γ)`, i.e. **0.31 m² is the effective horizontal area** and each panel's true area is 0.2807 m², 0.5613 m² total. `boom_construction_pack.md` §2.1 independently confirms it (`2 × 0.2808 × cos² 42° = 0.3102 ✓`). But `materials_pack.md` §6.7 bills the tail at **"0.42 m² panel"** — the cos-projection reading, 0.31/cos 42° = 0.4172 — which is **1.345× too small**.

Propagating: 0.00124 × (0.5613/0.4172 − 1) = **+0.000428 raw**, ×1.1713 for the build-up's own interference and cooling scale-up = **+0.000502**, so the honest baseline is **C_D0 = 0.02050, not 0.020**, worth **−0.99 h**, plus ~0.4 kg of unbilled tail mass = −0.6 h. **Honest baseline endurance ≈ 111.2 h, not 112.8 h.** [CALC]

**This is a datum shift, not a delta, and it is why it appears here rather than in the table.** Every configuration carrying an equal-effectiveness tail — inverted-V, flat-plus-fins, H-tail, X-tail — inherits the same correction, because cos²Γ + sin²Γ = 1 makes their total areas identical. **It cancels out of every pairwise comparison in §2 and must not be scored against any configuration.**

### 8.2 The report's stated V_h = 0.68 is wrong; 0.5765 is correct

V_h = S_h·l_h/(S·MAC) = 0.31 × 3.2 / (3.9 × 0.44123) = **0.57648**. The report's 0.68 would need S_h = 0.3657 m². Already tracked as an xfail in `tests/test_geometry_closure.py::test_report_stated_tail_volume` and in the README's "Known gaps". **Every tail-sizing calculation in this pack uses 0.5765.** [CALC]

### 8.3 The published 112.8 h contains ~3.4 h of unpaid stiffness debt

`materials_pack.md` §4.2 recommends 90 × 2.5 mm (EI 62.3 kN·m², 7.78 kg) as "the practical minimum", implicitly adopting a 2° tail-rotation criterion. `boom_construction_pack.md` §2.5 tightens that to **1.5°** and shows the 90 × 2.5 tube sits at **1.94° — it fails.** Sizing the 90 mm boom to the requirement costs +2.28 kg of tube (**−3.4 h**); going to 110 × 2.0 mm meets it for **−0.24 kg** at +0.00042 of drag.

**Consequence for this trade:** the boom mass a boomless configuration deletes is **9.20–11.72 kg installed**, not the 7.78 kg of bare tube that `materials_pack.md` quotes. Using 7.78 kg understates the boomless mass credit by 2–6 h. This pack uses 9.44 kg (as-drawn tube + the itemised local reinforcement) and gives the band.

### 8.4 The README contradicts itself on the slipstream

README "Known gaps" carries the correct statement (169 mm clearance, wake contracts to ~287 mm, 0.011% strain, 55× margin, r = 0.45 m prohibition). README **"Verified non-issues" still says "the booms do extend aft of the prop disc and therefore sit in its slipstream — a drag and blade-passage-tone consideration for the 122-hour fatigue case."** That sentence is superseded and should be deleted; it is the sentence that generated this trade's original premise.

### 8.5 Two smaller items

- **`materials_pack.md` §12 calls 80.5 Hz "engine firing".** For a single-cylinder 4-stroke at 4,830 rpm, firing is **40.25 Hz** and 80.5 Hz is 1× shaft. The pack's own text says "a single- or **twin**-cylinder 250 cc", and 80.5 Hz is correct for a 360° twin — so this is ambiguous rather than flatly wrong, but the engine architecture must be fixed before the keep-out comb is.
- **The README's 385 mm tail-below-keel figure is 11 mm optimistic.** The committed geometry gives panel tips at z = −0.6140 m against a keel at z = −0.240 m: **374 mm**. Immaterial to any conclusion (clearance is not a design driver) but the two numbers should agree.

---

## 9. Sources

| # | Source | Type |
|---|---|---|
| [1] | `docs/argus7_design_report.md` v1.0 — §2 geometry and tail row, §3 mass budget, §4 aero/performance and sensitivities, §5 structures, §6 powertrain, §7 recovery, Annex A premortem | project document |
| [2] | `research/materials_pack.md` — §4.2 boom sizing, §6.7 parasite-drag component build-up, §6.8 endurance ledger and the 1.5 h/kg exchange rate, §7 adhesives and joints, §8 fatigue and environment, §11 verdict | project document |
| [3] | `research/boom_construction_pack.md` — §2 loads and the 1.81× area-convention correction, §2.5 the 1.5° rotation criterion, §6 frequencies and the slipstream correction, §7 joints, §8 closing the loop, §9 the diameter sweep, §14 consolidated ledger, §15 open questions | project document |
| [4] | `design/argus7_v1.yaml` — geometry, masses, aero, and the field-level provenance block (`booms.diameter_m`, `tail.dihedral_deg`, `wing.x_le_frac`, `wing.z_offset_m` all tagged `assumption`) | project document |
| [5] | `argus7/design/geometry.py` — `derive_tail_panel` (panel_area = S_h/(2 cos² Γ)), `derive_booms`, `tail_volume_h`, `wing_ac_x`, `tail_qc_x` | project source |
| [6] | Henkel Aerospace, "Hysol EA 9394 Epoxy Paste Adhesive" TDS — 28.9 MPa lap shear at 25 °C, T-peel 22 N/25 mm, Tg 78 °C dry | [DS] |
| [16] | FAA AC 20-66B, "Propeller Vibration and Fatigue" — propeller-induced vibratory excitation, resonance avoidance, ≥0.2 D structure clearance practice | [DS]/[DR] |
| [17] | Resonance separation practice — ±20% band around natural frequencies; blade-passage = shaft rate × blade count (ABS "Insights into Ship Vibration Analysis") | [DR] |
| [18] | "Very High Cycle Fatigue (VHCF) Characteristics of CFRP under Ultrasonic Loading", *Materials* 13(4):908 — matrix fatigue-limit strain ε_mf = 0.6%, below which no damage progression occurs; no traditional fatigue limit in CFRP; matrix micro-cracking is the principal driver | [M] |
| [19] | "Bearing Fatigue and Hole Elongation in Composite Bolted Joints" (Vertical Flight Society) — four-stage bearing damage accumulation, progressive hole elongation and preload loss; design bearing allowable 165 ± 28 MPa | [M]/[DR] |

Source numbering follows `boom_construction_pack.md` where the same reference is used, so [6], [16]–[19] are the same documents in both packs.

---

## Appendix — reproducibility

Every `[CALC]` figure derives from the equations stated inline plus the committed geometry in `design/argus7_v1.yaml` and `argus7/design/geometry.py`. Five calculation groups:

1. **Endurance.** Step integration of dt = dm/(BSFC · P_shaft) from 250 → 148.5 kg, with V = √(2mg/ρSC_L), C_D = C_D0 + C_L²/(πARe), P_shaft = DV/η_p + P_payload/0.75, at ρ = 0.81935, S = 3.9, AR = 22, e = 0.85, C_L = 1.2098, η_p = 0.84, BSFC = 270 g/kWh, P_payload = 500 W, 20,000 steps. Returns 112.99 h at C_D0 = 0.020; all Δh are scaled onto the report's 112.8 h.

2. **Tail sizing and the boomless fixed point.** S_h(l) = V_h·S·MAC/l with V_h = 0.5765; panel_area = S_h/(2 cos² Γ); panel_span = √(panel_area · AR_p) with AR_p = 3; c_root = 2·panel_area/(span(1+λ)) with λ = 0.55; MAC_t = (2/3)c_root(1+λ+λ²)/(1+λ); x_le = wing_ac + l − 0.25·MAC_t; standoff = x_disc − (x_le + c_root) with x_disc = 3.46, wing_ac = 0.8936. Solved by Brent's method for standoff = 0.2 D = 0.1626 m → l = 2.0045 m.

3. **Drag.** Component equivalent flat-plate areas f = C_D0 · S from `materials_pack.md` §6.7; per-component C_f,eff = f/S_wet with S_wet,boom = πDL × 2 and S_wet,tail = 2.05 × panel area; Δf = −f_boom + ΔS_wet,tail · C_f,eff,tail; ΔC_D0 = Δf/S × 1.1713, where 1.1713 = 0.01730/0.01477 is the build-up's own interference-plus-cooling scale-up.

4. **Geometry.** b = √(S·AR) = 9.2628; c_root = 2S/(b(1+λ)) = 0.58074; MAC = 0.44123; panel tip at y = y_boom + span·cos Γ, z = −span·sin Γ; keel at z = −max_diameter/2 = −0.240.

5. **Actuator reliability.** Exponential failures, λ = 1/MTBF. Two surfaces, single-fault critical: P = 1 − e^(−2λT). Four surfaces, dual-fault critical: P = 1 − e^(−4λT) − 4(1 − e^(−λT))e^(−3λT). T = 112.8 h and 500 h.

Anyone re-deriving these should get the same answers; where they do not, the discrepancy is more interesting than the number.
