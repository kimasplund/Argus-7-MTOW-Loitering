# ARGUS-7 — RIBLET, DENTICLE & SURFACE-TEXTURE DATA PACK

**Date:** 2026-08-20 · **Scope:** shark-denticle and riblet surface texturing evaluated against the 250 kg MTOW / 9.26 m span / AR 22 / **FX 63-137** configuration of `docs/argus7_design_report.md` · **Companion to:** `research/materials_pack.md` (§6 surface quality, §6.8 endurance ledger)

**The question this pack was written to answer, as the sponsor posed it:** riblets demonstrably cut *turbulent* skin friction by 5–8% in the best aircraft trials. The ARGUS-7 wing is a natural-laminar-flow section chosen for its low-drag bucket. Does texturing it help, or does it destroy the laminar run and cost more than it saves?

**The short answer, stated before the evidence:** the aerodynamics work, the arithmetic does not. Riblets on this aircraft are worth **at most +1.25 h of endurance (+1.1%)** and only if they are formed at zero mass cost. Applied as film at the only areal density anybody has actually measured in service, they are worth **−0.96 to −2.6 h**. Shark denticles as the Harvard group built them are worth **−5.9 h** and are a transition trip by construction. Neither is a serious endurance lever for this airframe, and both compete for build hours against levers worth 8–27 h.

---

## 0. How to read this

Same provenance discipline as `research/materials_pack.md` [2]. Every numeric claim carries a bracketed source `[n]` and a tag:

| Tag | Meaning |
|---|---|
| **[DS]** | Manufacturer/operator datasheet or published product figure, quoted verbatim (unit-converted only) |
| **[M]** | Measured / published experimental data (wind tunnel, flight test, mechanical test) |
| **[CALC]** | Computed here from the report's own geometry, or from XFOIL runs made for this pack; equations given inline |
| **[EST]** | Engineering estimate by the author of this pack — a judgement, not a measurement |
| **[DR]** | Derived from a secondary source that itself cites a primary one |
| **[UNV]** | Unverified — flagged as needing test or vendor confirmation |

**Two new tools were used here that were not available to `materials_pack.md`.**

1. **XFOIL 6.99 was actually run** on the repository's own pinned `data/airfoils/fx63137.dat` (sha256 `8c3a70fa…`, t/c 0.13712), converted Lednicer→Selig, 300 panels, Ncrit = 9, viscous, fixed-C_L mode at the report's loiter C_L = 1.21, at ten spanwise stations. `materials_pack.md` §13 open question 2 asked "where does transition actually occur on this section at C_L = 1.21?" and answered "assumed 45–55% chord [EST]". **That question is now closed with a computation, not an assumption** — see §3. The assumption was right.
2. **The endurance model of `materials_pack.md` was re-implemented independently** and re-validated: fed C_D0 = 0.016 it returns **+8.589 h** against the report's own stated **+0.36 d = +8.64 h** sensitivity [1], and it reproduces the pack's isolated sensitivities to the last quoted digit (0.022 → −3.854 h vs −3.8; 0.024 → −7.453 vs −7.4; 0.027 → −12.427 vs −12.4; C_Lmax 1.4 → −5.370 vs −5.4; +1 kg → −1.517 h/kg vs −1.5) [2][CALC]. **All endurance deltas in this pack are therefore directly comparable with those in `materials_pack.md` §6.8.**

**Two honesty rules, carried over:**

1. Where a published headline number is an artefact of its baseline, that is stated rather than repeated. §7.3 does this to the "323%" figure in the sponsor's article.
2. Where this pack disagrees with `materials_pack.md`, it says so and shows the arithmetic. One such disagreement is in §3.4 (the fully-tripped C_D0 is worse than the pack's flat-plate floor, and this pack now has the number).

**Two useful constants, used throughout** [CALC]:

- **dEndurance/dC_D0 = −1,995 h per unit C_D0**, i.e. **−2.00 h per 0.001 of C_D0**, linear to better than 1% over 0.019 ≤ C_D0 ≤ 0.022.
- **dEndurance/dm = −1.517 h per kg** of structure at fixed 250 kg MTOW (fuel displaced) — this is `materials_pack.md`'s "1.5 h per kilogram", reproduced.

---

## 1. Answer first

| Question | Verdict | The number |
|---|---|---|
| Is any of the ARGUS-7 wing turbulent at loiter? | **Yes, about 40% of it** | XFOIL, C_L = 1.21, span-integrated: transition at **50.2% chord upper / 61.4% lower at the root**, moving aft to **60.5% / 68.2% at the tip**. **3.26 m² of the wing's 8.03 m² wetted area (40.5%) is turbulent**, carrying **53.3% of the wing's skin friction** [CALC] |
| Is that enough area to matter? | **Marginally** | Turbulent, riblet-coverable friction over the whole aircraft = **C_D0 0.00784 of 0.020**, which is **17.5% of total loiter drag** (induced drag is 55.5%) [CALC] |
| Would riblets of the right size trip the laminar run? | **No — and this is the surprise** | A 200 µm riblet at loiter has Re_k = 351 on freestream velocity and **150 on the local velocity at its own height** — against Braslow's critical **600**. The riblets themselves are sub-critical. The risk is the *film edge* and the *placement*, not the grooves [CALC from 16] |
| Is the optimum riblet size manufacturable? | **Yes, and this is the second surprise** | ARGUS-7 flies slowly at 4,000 m where ν = 2.028×10⁻⁵. Optimum spacing is **s ≈ 210 µm** — against **≈ 87 µm** for a 777 in cruise and **62 µm** for the UIUC wind-tunnel optimum at the same chord Reynolds number at sea level [CALC from 5][8] |
| Do riblets work at this Reynolds number on this kind of airfoil? | **Yes, measured** | UIUC/3M on the DU 96-W-180 (18% thick, **chord 0.457 m** ≈ our MAC 0.441 m) at **Re = 1.0×10⁶**: riblets placed *only in the turbulent region* gave **2–4% reduction in total section drag**; at Re 1.5×10⁶ **4–5%**. Non-optimal sizes **increased** drag by up to **10–12%** [5][M] |
| So does riblet film pay on ARGUS-7? | **No. It loses.** | AeroSHARK's measured areal mass is **150 kg over 950 m² = 0.158 kg/m²** [13][DS]. Covering all 9.23 m² of eligible area costs **1.46 kg = −2.21 h**. The best aerodynamic return at 8% friction reduction is **+1.25 h**. **Net −0.96 h**, and −2.56 h if the film is scaled up to carry 210 µm riblets [CALC] |
| Could riblets pay if formed at zero mass? | **Yes, but only just** | Moulded into the surface-filler layer of a female-moulded skin: **+0.94 h at 6% / +1.25 h at 8% / +2.03 h at the 13% adverse-pressure-gradient best case**. That is **+0.04 to +0.08 d out of 4.70 d** [CALC from 10] |
| What does getting it wrong cost? | **3–12× the upside** | Moving upper-surface transition forward by just **5 points of chord** (0.505 → 0.45) costs **Δc_d = +0.00057 → −1.13 h**, which erases the entire aircraft-wide best case. A fully tripped wing costs **Δc_d = +0.00684 → −13.6 h** [CALC] |
| Do the Harvard shark denticles apply? | **No, and they are not riblets** | NACA 0012, **chord 68 mm**, **Re_c ≈ 4×10⁴**, water tunnel, single row of **0.70 mm** denticles at 26% chord. The paper's own conclusion: "the shark-inspired profiles **trip the boundary layer**". At ARGUS-7's loiter condition a 0.70 mm element has **Re_k = 1,592 on local velocity, 2.7× Braslow's critical 600**, and occupies **65% of the local laminar boundary-layer thickness**. Geometrically scaled to our chords they are **2.7–6.0 mm tall — 2.5 to 5.6× the entire boundary layer** [4][M][CALC] |
| What would denticles cost? | **−5.9 h** | Trip at 26–30% chord (Δc_d +0.00235) plus the device drag of the array (+0.00053 [EST]) plus 0.3 kg of printed features = **−5.90 h**, against a lift benefit worth **+1.97 h only if C_Lmax rose from 1.60 to 1.70** — and break-even needs **C_Lmax ≥ 1.92**, a gain of +0.32 [CALC] |
| Leading-edge tubercles? | **No** | A near-stall and post-stall device with a documented pre-stall penalty, most effective at **AR ≈ 1**. ARGUS-7 loiters at AR 22 with a **15% stall margin deliberately built in** [12][M][1] |
| Where, if anywhere, is it worth pursuing? | **Fuselage pod and booms, and only as a moulded/embossed surface, and only after the wing surface is already good** | Fuselage + booms + tail carry **C_D0 0.00478 of fully-turbulent friction over 5.97 m²** with **no laminar run to lose**. Best case there is **+0.57 to +0.76 h** at zero mass, and the technical risk is near zero [CALC] |

### The endurance answer, stated precisely

Against the report's 112.8 h / 4.70 d baseline [1]:

| Configuration | ΔC_D0 | Mass | Δ Endurance |
|---|---|---|---|
| Riblet **film**, all eligible surfaces, 6% friction reduction | −0.000470 | +1.46 kg | **−1.27 h** |
| Riblet **film**, all eligible surfaces, 8% | −0.000627 | +1.46 kg | **−0.96 h** |
| Riblet **film** at 210 µm scale (0.25 kg/m²), 8% | −0.000627 | +2.31 kg | **−2.25 h** |
| **Moulded-in** riblets, wing only, 6% | −0.000184 | 0 | **+0.37 h** |
| **Moulded-in** riblets, all surfaces, 6% | −0.000470 | 0 | **+0.94 h** |
| **Moulded-in** riblets, all surfaces, 8% | −0.000627 | 0 | **+1.25 h** |
| **Moulded-in**, all surfaces, 13% (APG best case) | −0.001019 | 0 | **+2.03 h** |
| Harvard **denticles** at 26% chord, C_Lmax unchanged | +0.00288 | +0.3 kg [EST] | **−5.90 h** |
| Harvard **denticles**, with an optimistic +0.10 C_Lmax | +0.00288 | +0.3 kg | **−3.66 h** |
| **Risk case:** riblet zone trips upper transition 5% chord early | +0.00057 | — | **−1.13 h** |
| **Risk case:** riblet zone trips the wing at 20% chord | +0.00386 | — | **−7.7 h** |

**For scale, from `materials_pack.md` [2]:** choosing a moulded CFRP skin over a moldless wet layup is worth **+12 to +16 h**. Choosing pultruded caps over a tube spar is worth **+13 to +20 h**. Dyno-mapping the engine to 250 g/kWh is worth **+12 h** [1]. **Every one of those is 10–20× the entire riblet best case, and none of them has a downside branch that costs more than the upside.**

---

## 2. Three different technologies the literature conflates

The sponsor's tasking was right to insist on this separation. The press coverage of the Harvard work, including the article supplied [3], mixes all three. They have different mechanisms, different operating regimes, and different verdicts for this aircraft.

### 2.1 (a) Classical riblets — streamwise micro-grooves, turbulent skin friction

**Mechanism.** Streamwise grooves of spacing s and height h, both O(10–20) viscous wall units, impede the *spanwise* excursion of the near-wall quasi-streamwise vortices more than they impede the streamwise flow. The result is an offset between the virtual origin seen by the streamwise flow and that seen by the cross-flow — the **protrusion height** Δh — which shifts the log-law intercept and reduces wall shear [8][M]. Lufthansa Technik's own engineering statement of it: "Riblets reduce lateral momentum transfer **in fully turbulent flow**" [6][DS].

**The mechanism requires turbulence.** In laminar flow there are no near-wall streaks to interfere with, and grooves are pure added wetted area. This is not a subtlety; it is the whole basis of the technique.

**Operating window.** Drag reduction is roughly linear in size at small size, peaks, then reverses:

| Quantity | Value | Source |
|---|---|---|
| Optimum spacing, conventional geometries | **s⁺ = 10–20**, geometry-dependent; the common rule of thumb s⁺ ≈ 15 | [8][M] |
| Better-collapsing parameter: √(groove cross-section) | **ℓ_g⁺,opt = 10.7 ± 1.0** for *all* geometries reviewed (±10% scatter vs ±40% for s⁺ or h⁺) | [8][M] |
| Maximum drag reduction, closed form | **DR_max = 0.83·m_ℓ·ℓ_g⁺,opt ≈ 8.9·m_ℓ**, where m_ℓ is the viscous slope; experimental m₀ clusters at 0.66 and 0.785 | [8][M] |
| Best laboratory result, blade riblets h/s = 0.5 | **≈ 10%** | [7][M] |
| Trapezoidal-groove riblets (the practical shape) | **≈ 6%** | [7][M] |
| Sinusoidal / rounded-tip riblets | **2%** — against 8% for sharp triangular | [19][M] |
| Drag *increase* threshold | **s⁺ > ≈ 28** | [6][DS] |
| Practical ceiling quoted by the only operator flying it | "Drag reduction of **maximum 8%** (viscous drag)" | [6][DS] |

**For a symmetric V-groove with h = s** — the geometry of the 3M films that have actually been tested on airfoils [5] — the groove cross-section is A_g = s²/2, so ℓ_g = s/√2 and **s⁺_opt = 10.7·√2 = 15.1** [CALC from 8]. That is the sizing rule used in §5.

### 2.2 (b) Shark denticles as vortex generators — what the Harvard work actually is

The Harvard press release the sponsor supplied is subtitled, in its own words, **"Bioinspired vortex generators increase airfoil lift, decrease drag"** [3]. That subtitle is accurate and the rest of the coverage is not. The primary paper [4] is explicit:

> "…we demonstrate that the denticles can simultaneously enhance lift and reduce drag… we find that shark denticles generate both a **recirculation zone (in the form of a short separation bubble in the wake of the denticle)** that alters the pressure distribution of the aerofoil to enhance suction, as well as **streamwise vortices**…" [4][M]

and, in the conclusions:

> "The remarkable results shown here were achieved by using two mechanisms. First, **the shark-inspired profiles trip the boundary layer** and generate a short (reattaching) separation bubble that provides extra suction along the chord and thereby enhances lift." [4][M]

**This is a vortex-generator and separation-control result. It is not a skin-friction-reduction result, and the mechanism explicitly includes tripping the boundary layer.** Full numbers and the transfer calculation are in §7.

### 2.3 (c) Leading-edge tubercles — a third mechanism again

Sinusoidal leading-edge protuberances derived from the humpback whale flipper. Miklosovic et al. measured on a scale flipper model a **≈ 40% delay in stall angle** with increased maximum lift and reduced drag **in the 12°–17.5° incidence band** [12][M]. The mechanism is spanwise compartmentalisation of the stall and vortex generation at the tubercle troughs — again a high-incidence device.

Two facts kill it here. First, the benefit is at and beyond stall; pre-stall, tubercled sections show lift penalties [12][DR]. Second, the effect is strongly aspect-ratio dependent and is clearest at **AR ≈ 1**; it weakens on high-aspect-ratio foils [12][DR]. ARGUS-7 is AR 22 and loiters at **V ≥ 1.15 V_s** with C_L = 1.21 against C_Lmax 1.60 [1] — it never approaches the region where tubercles do anything except add wave-form drag to the leading edge, which is precisely the region where NLF surface accuracy matters most.

### 2.4 Which applies to a high-AR laminar loiter wing below stall?

| Technology | Requires | ARGUS-7 loiter has | Verdict |
|---|---|---|---|
| (a) Riblets | Turbulent boundary layer; s⁺ 10–20; alignment ≤15° yaw | 40.5% of wing wetted area turbulent; s⁺ achievable; yaw negligible on an unswept wing | **Applicable, on the aft 40% only** |
| (b) Denticles / low-profile VGs | Flow near separation, or a benefit from tripping | Attached flow with a 47–60% laminar run and 15% stall margin | **Counter-indicated** |
| (c) LE tubercles | Operation near/beyond stall; low AR | AR 22, α = 2.6° at loiter, C_L/C_Lmax = 0.76 | **Not applicable** |

---

## 3. Where the boundary layer on this wing is actually turbulent

This is the crux of the sponsor's question and it is answerable by computation, so it is computed rather than assumed.

### 3.1 Method

XFOIL 6.99 [26], `data/airfoils/fx63137.dat` (the repository's pinned coordinate file, checksum-enforced by `tests/test_airfoil_coords.py`), converted from its Lednicer 49/49 format to Selig order, re-panelled to 300 points, viscous, **Ncrit = 9** (standard free-air e^N), fixed-C_L mode at **C_L = 1.21** — the report's stall-constrained loiter lift coefficient, C_Lmax/1.15² = 1.60/1.3225 = 1.2098 [1]. Atmosphere from `materials_pack.md` §6.1: 4,000 m ISA, ρ = 0.8194 kg/m³, **ν = 2.028×10⁻⁵ m²/s** [2].

Chord Reynolds number varies along the span as Re(y) = V·c(y)/ν = 1.7564×10⁶ · c(y) at the heavy-loiter speed of 35.62 m/s, with c(y) = 0.581 → 0.261 m (taper 0.45) [1].

### 3.2 Transition location — the result

Ten spanwise stations, mid-panel, heavy loiter (250 kg, 128 km/h, 4,000 m). `x_tr` here is the point at which the shape factor H falls below 2.0, i.e. **fully turbulent**; XFOIL's e^N transition *onset* lies 3–8 points of chord ahead of it. The onset location is itself panel-density sensitive — at the MAC it moves from 0.473 at 160 panels to 0.505 at 300 — which is one reason the H < 2.0 point is used here as the primary measure: it is the more stable number and it is also the physically correct boundary for riblet eligibility, since riblets need a developed turbulent boundary layer, not a transitional one.

| y (m) | c (m) | Re_c | x_tr upper | x_tr lower | c_df (section) | of which turbulent | turbulent share | turbulent arc share |
|---|---|---|---|---|---|---|---|---|
| 0.232 | 0.565 | 992,000 | **0.502** | 0.614 | 0.00563 | 0.00328 | 58.3% | 43.6% |
| 0.695 | 0.533 | 936,000 | 0.511 | 0.614 | 0.00566 | 0.00324 | 57.3% | 43.2% |
| 1.158 | 0.501 | 880,000 | 0.521 | 0.624 | 0.00566 | 0.00317 | 56.1% | 42.3% |
| 1.621 | 0.469 | 824,000 | 0.530 | 0.633 | 0.00568 | 0.00312 | 54.9% | 41.3% |
| 2.084 | 0.437 | 768,000 | 0.540 | 0.643 | 0.00570 | 0.00305 | 53.6% | 40.4% |
| 2.547 | 0.405 | 711,000 | 0.549 | 0.643 | 0.00575 | 0.00302 | 52.5% | 40.0% |
| 3.010 | 0.373 | 655,000 | 0.558 | 0.653 | 0.00579 | 0.00296 | 51.0% | 39.0% |
| 3.474 | 0.341 | 599,000 | 0.577 | 0.662 | 0.00585 | 0.00286 | 48.8% | 37.7% |
| 3.937 | 0.309 | 543,000 | 0.586 | 0.672 | 0.00591 | 0.00279 | 47.2% | 36.7% |
| 4.400 | 0.277 | 487,000 | **0.605** | 0.682 | 0.00597 | 0.00268 | 44.9% | 35.3% |

[CALC]

**Span-integrated result** (both semi-spans, chord-weighted, wetted area from the section's own perimeter/chord ratio of 2.0603 measured off the pinned coordinates):

- Wing wetted area **8.03 m²** — closes on `materials_pack.md`'s ~8.0 m² [2]
- **Turbulent (riblet-eligible) area 3.26 m² = 40.5% of wing wetted area**
- Wing friction drag C_D(ref S = 3.9 m²) = **0.00574**
- Of which turbulent = **0.00306 = 53.3%**

**This closes `materials_pack.md` §13 open question 2.** The pack assumed x_tr = 45–55% chord [EST]; the computation gives 50–61% upper and 61–68% lower, i.e. **the assumption was correct and slightly conservative**. The C_D0 = 0.020 build-up in `materials_pack.md` §6.7, which used x_tr = 0.50, stands.

**Two consequences that matter for the riblet question:**

1. **The laminar region is not "free".** Only 40.5% of the wing's wetted area is even eligible, but that 40.5% carries **53.3% of the wing's skin friction** — because the aft, thicker turbulent boundary layer sits under the FX 63-137's aggressive pressure recovery. The eligible fraction is better than the area fraction suggests.
2. **The transition line is not a line.** It moves **10.3 points of chord from root to tip** on the upper surface, and a further ~4 points between heavy and light loiter (at the tip at 99 km/h, Re falls to 3.5×10⁵ and transition moves aft again). A single straight film boundary cannot follow it. §3.5 quantifies what that costs.

### 3.3 Transition at the other mission points

Same method, XFOIL e^N onset (not the H < 2.0 point), 160-panel runs, C_L = 1.21:

| Condition | Station | Re_c | Top_Xtr | Bot_Xtr | c_d |
|---|---|---|---|---|---|
| Heavy loiter, 128 km/h | root | 1.02×10⁶ | 0.418 | 0.569 | 0.00924 |
| Heavy loiter | MAC | 7.75×10⁵ | 0.473 | 0.593 | 0.00943 |
| Heavy loiter | tip | 4.58×10⁵ | 0.546 | 0.640 | 0.01051 |
| Light loiter, 99 km/h | root | 7.87×10⁵ | 0.471 | 0.592 | 0.00941 |
| Light loiter | MAC | 5.97×10⁵ | 0.514 | 0.618 | 0.00984 |
| Light loiter | tip | 3.53×10⁵ | 0.576 | 0.665 | 0.01141 |

[CALC]

Transit is different and worth noting: at 175 km/h and 250 kg, C_L = 2W/(ρV²S) = **0.65**, and at Re_MAC = 1.06×10⁶ XFOIL puts upper transition at **0.669** but **lower-surface transition at 0.037** — the lower surface trips essentially at the nose at low C_L. For the local-ops mission (the headline 4.70 d) transit is zero; for deploy-2,000 km it is 11.5 h of 107.1 h [1]. Riblets sized for loiter therefore also happen to sit on a lower surface that is *fully* turbulent in transit, which is a small bonus, not a design driver.

### 3.4 What tripping the wing costs — measured against the section, not a flat plate

XFOIL, MAC, Re 7.75×10⁵, C_L held at 1.21, forced transition:

| x_tr upper (lower) | α | c_d | Δc_d vs natural | ΔC_D0 | Δ Endurance |
|---|---|---|---|---|---|
| 0.505 / 0.599 **(natural)** | 2.612° | **0.00914** | — | — | — |
| 0.48 / 0.599 | 2.649° | 0.00939 | +0.00025 | +0.00025 | −0.50 h |
| 0.45 / 0.599 | 2.690° | 0.00971 | **+0.00057** | +0.00057 | **−1.13 h** |
| 0.40 / 0.599 | 2.764° | 0.01032 | +0.00118 | +0.00118 | −2.35 h |
| 0.30 / 0.55 | 2.897° | 0.01149 | **+0.00235** | +0.00235 | **−4.69 h** |
| 0.20 / 0.45 | 3.076° | 0.01300 | +0.00386 | +0.00386 | −7.70 h |
| 0.10 / 0.30 | 3.304° | 0.01475 | +0.00561 | +0.00561 | −11.19 h |
| 0.05 / 0.05 | 3.494° | 0.01598 | **+0.00684** | +0.00684 | **−13.65 h** |

[CALC]

**This pack disagrees with `materials_pack.md` §6.7 in the conservative direction, and now has the number.** That pack's mixed laminar/turbulent flat-plate model gave Δc_d = +0.00422 for a wing tripped at 5% chord and flagged the result as "a lower bound… it does not count the growth in pressure drag when a boundary layer that is turbulent from 5% chord enters the FX 63-137's aggressive aft recovery much thicker" [2]. **A viscous-inviscid calculation that does count it gives +0.00684, 62% higher.** The pack's estimated band for a fully-tripped wing was C_D0 = 0.024–0.027 [EST]; the computed value is **0.0268**, at the top of its own band. The pack's judgement was right and its floor was too low.

**Note also the incidence penalty.** Holding C_L at 1.21 while tripping the wing costs 0.88° of extra angle of attack (2.61° → 3.49°), which eats 0.88° of the stall margin the loiter constraint was built on. That is a second-order effect not modelled here and it makes the tripped case worse, not better.

### 3.5 The asymmetry that decides this section

| | Value |
|---|---|
| Best case gain from riblets on the **whole aircraft**, at zero mass, 8% friction reduction | **+1.25 h** |
| Cost of moving upper transition forward by **5 points of chord** | **−1.13 h** |
| Cost of moving it forward by **10 points** | **−2.35 h** |

The riblet zone's leading edge must be placed aft of the aftmost natural transition point across the whole span and the whole mission. From §3.2/3.3 that is **x/c ≈ 0.61 upper, 0.68 lower** — not the 0.50/0.60 of the design point. The UIUC group hit exactly this problem and solved it by restricting their own performance assessment: "Since at C_l values outside this range riblets would no longer start inside the separation bubble, **any measured change in drag may not be due to the action of riblets but instead due to early flow transition**. Therefore, the assessment of riblet performance will be made based on the drag at C_l values ranging from 0.75 to 1.0" [5][M]. **ARGUS-7 loiters at C_l = 1.21, outside the band in which the only directly comparable experiment was willing to make a claim.**

Cost of the safe placement, span-integrated [CALC]:

| Film start (upper / lower) | Covered area | Covered friction, C_D ref S | % of wing friction | Δ Endurance at 6% |
|---|---|---|---|---|
| Ideal, following x_tr(y) exactly | 3.26 m² | 0.00306 | 53.3% | +0.37 h |
| 0.55 / 0.62 (heavy-loiter-safe) | 3.17 m² | 0.00295 | 51.4% | +0.35 h |
| **0.62 / 0.70 (all-mission-safe)** | **2.66 m²** | **0.00237** | **41.3%** | **+0.28 h** |
| 0.70 / 0.75 (conservative) | 2.18 m² | 0.00177 | 30.9% | +0.21 h |

Retreating to a genuinely safe boundary costs **23% of the wing benefit** and leaves the highest-shear strip — the 5–10 points of chord immediately behind transition, where local C_f peaks at 0.0072 against 0.0013 at the trailing edge [CALC] — uncovered. This is not a large loss in absolute terms because the absolute terms are small.

---

## 4. Admissible roughness: what the surface criteria say about denticles and riblets

`materials_pack.md` §6.1 established the *waviness* criterion (Carmichael, h/λ = √(59,000·c·cos²Λ/Re_c^1.5), allowable h/λ 0.036–0.044 single-wave, ÷3 for multiple close-spaced waves) [2][17]. The relevant criterion for a discrete protuberance is different: **Braslow's critical roughness Reynolds number**.

**Braslow & Knox:** transition is precipitated at the roughness element when Re_k = u_k·k/ν exceeds **≈ 600**, where u_k is the undisturbed boundary-layer velocity at the height of the element. Schlichting's more conservative "admissible roughness" criterion uses Re_k ≈ 100 on freestream velocity [16][M].

At the ARGUS-7 loiter condition (V = 35.62 m/s, ν = 2.028×10⁻⁵) [2]:

| Criterion | Admissible height |
|---|---|
| Schlichting, Re_k = 100 on U∞ | **0.057 mm** |
| **Braslow & Knox, Re_k = 600 on U∞** | **0.342 mm** |
| X-21 forward-facing step, Re_h = 900 | 0.512 mm |

Now the actual candidate heights, evaluated two ways: on freestream velocity (as `materials_pack.md` did, the conservative form) and on the **local velocity at the element's own height** (the form Braslow actually defined), using XFOIL's computed edge velocity u_e/U∞ = 1.539 and laminar boundary-layer thickness δ ≈ 1.07 mm at x/c = 0.26 on the MAC, with a Pohlhausen velocity profile:

| Element | h (µm) | h/δ at 26% c | Re_k (U∞) | Re_k (local) | vs Braslow 600 |
|---|---|---|---|---|---|
| **Harvard denticle, as tested (h₁ = 0.70 mm)** | 700 | **0.65** | 1,229 | **1,592** | **2.7× over** |
| Denticle geometrically scaled to tip chord 0.261 m | 2,688 | 2.51 | 4,722 | 7,267 | **12× over** |
| Denticle geometrically scaled to MAC 0.441 m | 4,542 | 4.25 | 7,978 | 12,278 | **20× over** |
| Denticle geometrically scaled to root chord 0.581 m | 5,984 | 5.59 | 10,511 | 16,176 | **27× over** |
| **Riblet, s = h = 200 µm (this pack's sizing)** | 200 | 0.19 | 351 | **150** | **sub-critical** |
| 3M 62 µm riblet (UIUC measured optimum) | 62 | 0.06 | 109 | 15 | sub-critical |

[CALC from 4][5][16]

**Three plain statements follow.**

1. **The Harvard denticles are taller than the critical roughness height, at the size they were actually tested at, by a factor of 2.7 on the criterion that governs.** Scaled to ARGUS-7's chords they are 12–27× critical and **taller than the entire local boundary layer**. They cannot be applied to this wing forward of transition without destroying the laminar run. The paper does not dispute this; it says so.
2. **Riblets at the correct size for this flight condition are comfortably sub-critical**, at 150 on the local-velocity criterion against a threshold of 600. This is a genuinely favourable and slightly counterintuitive result: it exists because ARGUS-7 flies slowly in thin air, where ν/V is 1.4× larger than in a sea-level tunnel and 5× larger than for a jet in cruise. The riblet *grooves* are not the tripping risk.
3. **Braslow's criterion is not the right criterion for riblets anyway, and the literature that is says the risk is real but different.** Grek, Kozlov & Titarenko measured that riblets slightly *destabilise* two-dimensional linear Tollmien–Schlichting waves — TS waves are excited at a slightly *lower* Reynolds number over grooved surfaces than smooth ones, with wall-normal disturbance amplitude ~15% higher — while simultaneously *delaying* the nonlinear Λ-vortex-to-turbulent-spot transformation [11][M]. The net effect on transition location is small and sign-ambiguous, which is exactly why the operational rule is placement, not tolerance: **"Riblets cannot be applied everywhere: avoid areas with laminar flow and complex curvature"** — Lufthansa Technik's own engineering guidance [6][DS].

**The remaining geometric risk is the film edge, and it is smaller than expected.** A riblet film with backing and adhesive at 250–350 µm total thickness creates a forward-facing step at its leading edge. The X-21 forward-facing step criterion at loiter gives **0.512 mm** [2][17], so **even a misplaced film edge landing in laminar flow would be below the step-tripping threshold**. What it would do instead is documented by Ananth, Vaid et al.: "a separated shear layer forms over the riblet leading edge as the flow encounters an abrupt surface transition from the smooth surface onto the riblets", with an associated spurt in turbulent kinetic energy that a **leading-edge ramp** substantially mitigates [18][M]. A feathered or ramped film edge is therefore mandatory, not optional.

---

## 5. Riblet sizing at the ARGUS-7 flight condition

### 5.1 Viscous length scale along the chord

From the XFOIL dumps: u_τ(x) = V∞·√(C_f(x)/2) with C_f normalised on freestream dynamic pressure (verified against Ludwieg–Tillmann at x/c = 0.74 to within 4%), viscous length ℓ_v = ν/u_τ.

Turbulent region only, heavy loiter [CALC]:

| Station | Re_c | ℓ_v range (µm) | s at s⁺ = 17 (µm) | shear-weighted s at s⁺ = 17 |
|---|---|---|---|---|
| Root, upper | 1.02×10⁶ | 9.1–35.7 | 154–607 | **203** |
| Root, lower | 1.02×10⁶ | 11.1–20.5 | 188–348 | **268** |
| MAC, upper | 7.75×10⁵ | 9.5–34.6 | 161–589 | **206** |
| MAC, lower | 7.75×10⁵ | 10.7–23.9 | 182–407 | **261** |
| Tip, upper | 4.58×10⁵ | 10.0–30.9 | 169–526 | **210** |
| Tip, lower | 4.58×10⁵ | 10.1–22.0 | 171–374 | **244** |
| MAC, upper, **light loiter** | 5.97×10⁵ | 12.5–43.1 | 212–732 | **269** |

Shear-weighting is the correct averaging, and is the same method the UIUC group used: "The h value at each location on the airfoil was weighted using the local skin friction drag at that location normalized by the total drag" [5][M]. Span-integrated over the whole covered area, s(s⁺ = 17) = **218 µm** [CALC].

### 5.2 The recommended size, and why it is good news

Using the better-collapsing parameter from García-Mayoral & Jiménez — ℓ_g⁺,opt = 10.7 ± 1.0, which for a symmetric V-groove with h = s gives **s⁺_opt = 15.1** [8][CALC] — and sizing at the *mid-loiter* mass (≈200 kg, V = 31.9 m/s) rather than the heavy end:

> **Recommended riblet geometry: symmetric V-groove, s = h ≈ 210 µm.**

Robustness across the flight envelope, for a fixed s = 210 µm [CALC]:

| Condition | V (m/s) | s⁺ | ℓ_g⁺ | Status |
|---|---|---|---|---|
| Light loiter, 99 km/h, 148.5 kg | 27.45 | **13.2** | 9.3 | Below optimum, ~90% of DR_max |
| Mid loiter, ~200 kg | 31.9 | **15.1** | 10.7 | **At optimum** |
| Heavy loiter, 128 km/h, 250 kg | 35.62 | **16.7** | 11.8 | Just past optimum, ≈99% of DR_max |
| Transit, 175 km/h | 48.61 | **22.2** | 15.7 | Past optimum, ~60–70% of DR_max, still beneficial |
| Drag-*increase* threshold | — | ≈28 | ≈20 | Never reached [6][DS] |

**This is one of only two things in this pack that goes ARGUS-7's way, and it goes its way strongly.** A single fixed riblet geometry stays inside the drag-reducing band across the entire 250→148.5 kg loiter and the transit case. Lufthansa Technik has to *zone* the AeroSHARK layout — "Riblet Layout is a simplification of the wall shear distribution… optimized for cruise conditions (FL340 / Mach 0.84)" [6][DS] — because a transport's shear varies far more across its wetted area than ARGUS-7's does. ARGUS-7 needs one size.

**And 210 µm is manufacturable in a way that 62 µm and 87 µm are not.** For comparison [CALC]:

| Application | ν (m²/s) | V (m/s) | τ_w (Pa) | u_τ (m/s) | s at s⁺ = 17 |
|---|---|---|---|---|---|
| **ARGUS-7, wing at x/c = 0.70, loiter** | 2.028×10⁻⁵ | 35.62 | 3.05 | 1.93 | **179 µm** |
| UIUC/3M tunnel test, DU 96-W-180, Re 1.5×10⁶ | 1.46×10⁻⁵ | 47.9 | — | — | ≈62–100 µm measured optimum [5][M] |
| B777, cruise FL340 M0.84 | 3.825×10⁻⁵ | 249.8 | 21.3 | 7.49 | **87 µm** |

The low-speed, high-altitude operating point that makes ARGUS-7 a poor riblet candidate on every other axis makes the riblets themselves **2.4× larger and correspondingly easier to form** than on the aircraft the technology was developed for. §9.4 shows why that is not the gift it looks like.

### 5.3 Alignment

Riblet drag reduction degrades with misalignment to the local flow, but **"yaw effects are negligible up to 15° misalignment"**, and trapezoidal grooves with a 45° tip angle are the least yaw-sensitive geometry [24][M]. On an unswept AR-22 wing at C_L 1.21, upper-surface streamline deviation from the freestream direction is a few degrees at most. **Alignment is a non-issue on the wing.** It is a live issue on the fuselage pod, which sits in the propwash of a nose-mounted 0.813 m propeller (the `design/argus7_v1.yaml` fuselage OML has a 0.072 m nose diameter consistent with a spinner) — swirl there is light at 3.4 kW of loiter shaft power but is unquantified [UNV].

---

## 6. Measured riblet performance — the evidence base, ranked by transferability

### 6.1 The one dataset that is nearly a direct read-across

**Sareen, Deters, Henry & Selig, ASME J. Solar Energy Engineering 136(2):021007 (2014), DOI 10.1115/1.4024982**, commissioned by the 3M Renewable Energy Division; also as AIAA 2011-558 [5][M].

Why it transfers: **DU 96-W-180, 18% thick, chord 0.457 m** (ARGUS-7 MAC is 0.441 m), **Re = 1.0, 1.5 and 1.85 ×10⁶** (ARGUS-7 root at heavy loiter is 1.02×10⁶), natural transition near **40% chord upper / 75% lower**, laminar separation bubble present on both surfaces, and — uniquely in the riblet literature — **riblets applied only downstream of natural transition, with the film's leading edge inside the separation bubble and never ahead of the laminar separation point**. The authors are explicit that this was the point: "Riblets have never been tested with the film applied downstream of the natural transition point" [5][M].

Films: 3M V-groove, **peak-to-valley height = peak-to-peak spacing**, h = 44, 62, 100 and 150 µm. Calculated optimum for the test conditions: **80 µm**. Measured by wake rake, ±0.1% uncertainty, three repeats per configuration [5][M].

**Results, as percent change in total section drag against the clean baseline, upper + lower turbulent regions covered:**

| Riblet h | Re = 1.0×10⁶ | Re = 1.5×10⁶ | Re = 1.85×10⁶ |
|---|---|---|---|
| 44 µm | marginal decrease | −1 to −2% | ≈0 |
| **62 µm** | **−2 to −4%** | **−4 to −5%** | −1 to −2% |
| 100 µm | **−2 to −4%** | −2 to −4% | "highly detrimental" |
| 150 µm | **increase** | **up to +6%** | "highly detrimental" |

"Optimally sized riblets, when applied in the turbulent region, produced a drag reduction of 4–5%. **Non-optimal riblet sizes, on the other hand, increased drag up to 10–12% in some cases.**" [5][M]

**Three findings from this paper are load-bearing for ARGUS-7:**

1. **At the Reynolds number closest to ours (1.0×10⁶), the achievable benefit is 2–4% of total section drag, not 4–5%.** The higher figure belongs to Re 1.5×10⁶.
2. **The window is narrow and the downside is steep.** Getting the size wrong by a factor of 2.4 (62 → 150 µm) turns −4% into +6%. That is a 10-point swing for a manufacturing error smaller than the tolerance of most low-cost microtexturing routes.
3. **Tripping the flow ahead of the bubble buys nothing.** "No benefit, however, was seen from forcing transition ahead of the bubble and in some cases trips even proved to be detrimental to the airfoil performance." [5][M] This is a direct experimental refutation, on a comparable section at a comparable Reynolds number, of the idea that a surface texture might pay for itself by killing the laminar separation bubble.

**Cross-check against this pack's own model.** ARGUS-7's turbulent friction is 53.6% of the wing's friction at the MAC and, in XFOIL's own accounting there (c_d = 0.00914, C_Df = 0.00568), **33.3% of total section drag** [CALC]. A 6% reduction of turbulent friction therefore returns **2.00% of section drag**; 8% returns **2.66%**; the adverse-pressure-gradient case of 13% (§6.4) returns **4.33%**. **The UIUC measured band of 2–4% at Re 1×10⁶ falls squarely inside that range.** Two independent routes — a wake-rake measurement and an XFOIL-derived friction decomposition — agree. This is the strongest single piece of validation in the pack.

### 6.2 Canonical laboratory

**Bechert, Bruse, Hage, van der Hoeven & Hoppe, J. Fluid Mech. 338:59–87 (1997)** [7][M], the reference dataset, obtained on an adjustable-geometry oil channel:

- Blade riblets, h/s = 0.5: **≈10% maximum drag reduction** — the highest figure ever obtained for a passive riblet surface
- Trapezoidal-groove riblets, the practical shape: **≈6%**
- Optimum in the range s⁺ 10–20 depending on geometry

**García-Mayoral & Jiménez, Phil. Trans. R. Soc. A 369:1412–1427 (2011)** [8][M] reduced Bechert's and Walsh's data to a single collapsed curve and gave the closed-form model used in §5 and recommended in §11.

### 6.3 Flight and in-service

| Programme | Coverage | Result | Source |
|---|---|---|---|
| **NASA, Walsh, Sellers & McGinley**, Learjet 28/29 fuselage, Re 1.0–2.75×10⁶/ft, M 0.3–0.7 | Fuselage panels | **≈6% drag reduction at s⁺ = 12**, by boundary-layer rake and direct drag balance. Perforated riblets (0.010 in holes at 0.25 in centres) gave the same reduction as unperforated | [9][M] |
| **Airbus A320 / 3M riblet film, 1989** | Flight-test coverage | **2% proven saving according to Airbus** | [6][DR] |
| **Cathay Pacific A340-300 / 3M, 1990s** | In-service degradation monitoring | **2% predicted**; skin-friction reduction quoted at 5–8% locally; **film replacement needed every 2–3 years** | [6][29][DR] |
| **AeroSHARK, B747-400 lower fuselage, 2019** | ~500 m², first STC Nov 2019 | Certified; slow market uptake | [6][13][DS] |
| **AeroSHARK, B777-300ER** | **950 m²** fuselage + nacelles | **≈1.1% fuel saving**; **adds 150 kg** | [13][DS] |
| **AeroSHARK, B777-200ER** | ~830 m² fuselage + nacelles | ≈1% fuel per flight | [13][DS] |
| **AeroSHARK, LHT measured, 1st aircraft** | fuselage + nacelles | **0.9% cruise drag reduction measured**, → 670–750 kg on a 93 t ZRH–SFO sector (0.7–0.8% fuel), → **1.0–1.1% total** once the initial fuel load is reduced | [6][M] |
| **AeroSHARK, Austrian Airlines, 4× B777, 12 months in service to 2026** | fuselage + nacelles | **0.7% drag reduction**, 930 t fuel, 3,000 t CO₂ | [14][M] |
| **AeroSHARK fleet, Aug 2025** | — | >232,000 flight hours, >13,000 t fuel, >42,000 t CO₂ | [13][DS] |
| **LHT + Airbus, A330ceo, May 2026** | Extends STC to **wings, horizontal stabiliser, vertical tailplane** | **>2% target** for a fully modified aircraft | [15][DS] |

**Three observations.**

1. **In-service delivery is consistently below the marketing figure.** Austrian's measured 0.7% against a claimed 1.1%; LHT's own measured 0.9% cruise drag reduction against a 2.2–3.6% "if applied everywhere" potential [6][M]. Apply the same discount to any ARGUS-7 estimate.
2. **The 777 application deliberately excluded the wing.** "Target: Apply film on fuselage and nacelles. **Application on wing shifted due to certification issues.**" [6][DS] The wing came seven years later, on a different type, as a joint programme with the OEM [15].
3. **When riblets did go on a wing, it was a transonic supercritical wing with turbulent flow from close to the leading edge, not a natural-laminar-flow section.** The A330ceo wing is not an NLF wing. This is not an argument that riblets belong on NLF wings; it is the opposite.

### 6.4 Adverse pressure gradient — the one effect that favours ARGUS-7

The FX 63-137's entire turbulent region sits under its pressure recovery: XFOIL gives u_e/U∞ falling from 1.378 at x/c = 0.55 to 0.986 at the trailing edge, with H rising from 1.47 to 2.37 [CALC]. That is a strong adverse gradient, and riblets do *better* there:

> **Debisschop & Nieuwstadt:** riblets in an adverse pressure gradient gave **13% skin-friction reduction against 6% in the same rig at zero pressure gradient** [10][M].

The mechanism is attributed to Kelvin–Helmholtz roller vortices near the riblet crest being augmented in size, strength and frequency by the adverse gradient [10][DR]. This is why the "best case" column in §1 and §9 uses 13% rather than 8%. It should be treated as an upper bound, not a design value: it is a single-rig result in a canonical geometry, and the AeroSHARK flight data does not show anything like a doubling.

### 6.5 Riblets applied to laminar airfoils — what actually exists

The sponsor asked for "any evidence at all on riblets applied to laminar aerofoils rather than turbulent ones." The honest answer is that there is **one good dataset and one system study**, and both say the same thing: keep the riblets behind transition.

1. **Sareen et al. 2014 [5][M]** — the DU 96-W-180 is a laminar-bucket wind-turbine section with natural transition at 40%/75% chord, and the entire experimental design is built around applying riblets only aft of it. This is the closest thing to a direct answer that exists, and it is summarised in §6.1.
2. **Catalano, de Rosa, Mele, Tognaccini & Moens, J. Aircraft 57(1):29–40 (2020)** [23][M] — a regional-aircraft system study applying **both** natural laminar flow and riblets. Each technology alone gives a maximum of about **12% drag reduction, decreasing with angle of attack**; together they exceed **20% at cruise**. The two are complementary *at aircraft level* — NLF on the wing, riblets on the turbulent remainder — not superimposed on the same surface.
3. **Ananth, Vaid et al., AIAA J. (2023), DOI 10.2514/1.J062418** [18][M] — scale-resolving simulations of riblets straddling the transitional and turbulent regimes, which is the regime a real riblet patch boundary sits in. The finding that matters for construction: an abrupt smooth-to-riblet surface transition produces a separated shear layer and a turbulent-kinetic-energy spurt, and **a leading-edge ramp effectively minimises it**.
4. **Grek, Kozlov & Titarenko, J. Fluid Mech. (1996)** [11][M] — riblets in the laminar region marginally destabilise linear TS waves while delaying the nonlinear breakdown; "transition control by means of riblets requires special attention to the choice of their location, taking into account the stage of transition" [11][DR].

**What does not exist:** any published measurement of riblets applied *forward of transition* on a laminar-bucket section that shows a net benefit. If the sponsor has seen one, it should be produced, because this pack could not find it.

---

## 7. The Harvard denticle aerofoil result, read carefully

### 7.1 What was actually tested

**Domel, Saadat, Weaver, Haj-Hariri, Bertoldi & Lauder, J. R. Soc. Interface 15(139):20170828 (2018)** [4][M] — the primary paper behind the article the sponsor supplied [3].

| Parameter | Value |
|---|---|
| Aerofoil | **NACA 0012 — symmetric, not a laminar-flow section** |
| Chord | **L = 68 mm** |
| Aspect ratio | W/L = 2.8 (a finite low-AR panel) |
| Medium | **Water flow tank**, ν = 1×10⁻⁶ m²/s |
| Speed | **U = 0.58 m/s** |
| **Chord Reynolds number** | **Re_c ≈ 4×10⁴** |
| Denticles | Micro-CT models of *Isurus oxyrinchus*, ~2 mm × 2 mm footprint, **middle-ridge height h₁ = 0.70 mm**, spanwise separation 1 mm, **single row at 26% chord** |
| Fabrication | Objet Connex500 PolyJet, RGD81 photopolymer |
| Incidence | α = 0° to 24° in 2° steps |
| Configurations | 20 denticle aerofoils, plus a 2-D bump control and a "continuous shark-inspired profile" |

**Re_c ≈ 4×10⁴ is 15–27× below ARGUS-7's chord Reynolds number** (4.87×10⁵ at the tip to 1.02×10⁶ at the root). At Re 4×10⁴ a NACA 0012 is deep in the low-Reynolds regime where a large laminar separation bubble or full leading-edge separation dominates the polar, and tripping is a well-known net win. At Re 10⁶ on a cambered NLF section at design C_L the flow is attached with half its chord laminar. **These are different flow regimes, not different points on the same curve.** The paper's own methods section concedes the Re was set by the printer, not the physics: "the dimensional limitations of the 3D printer used to fabricate our test models… necessitated the use of a water tank" [4][M].

### 7.2 What was measured

Ratios of denticle foil to smooth control, best-performing configuration (single row, 26% chord) [4][M]:

| α | 0° | 2° | 4° | 6° | 8° | 10° | 12° | 14° | 16° |
|---|---|---|---|---|---|---|---|---|---|
| **C_L ratio** | ∞ (control = 0) | — | 1.24 | 1.13 | 1.24 | 1.06 | 1.04 | 0.96 | 1.03 |
| **C_D ratio** | — | 0.84 | 0.81 | 0.78 | 0.72 | 0.83 | 0.87 | — | — |
| **L/D ratio** | — | (see §7.3) | **1.53** | **1.46** | **1.72** | **1.28** | **1.19** | — | — |

The "continuous shark-inspired profile" — a smoothed, sinusoidal-spanwise version, and the paper's own best design — reached L/D ratios of **1.39, 1.52, 1.86, 1.83, 1.83** at α = 4°–12°, with drag ratios down to **0.53 at α = 10°**.

Note carefully what the drag reduction is: at α = 4°, **19%**. That is far above anything riblets have ever achieved and far above what skin-friction reduction can produce. It is separation-bubble suppression on a stalling low-Re section, not skin friction.

### 7.3 The "323%"

The headline in the sponsor's article — "lift-to-drag ratio improvements of up to 323 percent" [3] — is real but is an artefact of the baseline. The paper's own tabulated L/D ratios for α = 4°–12° are 1.19–1.86, i.e. **19–86% improvements**. The 323% figure sits at the lowest incidence tested [4][DR — the α = 2° value is rendered as an image in the full text and could not be read; its position is inferred from the six-value/six-angle sequence]. At α = 0° a **symmetric** NACA 0012 produces exactly zero lift, so L/D = 0 and *any* lift is an infinite improvement; at α = 2° at Re 4×10⁴ the control's lift is still very small. **The denominator, not the numerator, produces the 323%.**

For an aircraft that flies at C_L = 1.21 on a section with 5.97% camber, this number carries no information. The transferable numbers from the paper are the 19–86% band at moderate incidence — and those are separation-control numbers on a stalling section.

### 7.4 What denticles would do to ARGUS-7

| Effect | Value | Source |
|---|---|---|
| Denticle height at the size tested | 0.70 mm | [4] |
| Local boundary-layer thickness at 26% chord, MAC, loiter | **1.07 mm** | [CALC] |
| h/δ | **0.65** | [CALC] |
| Re_k on local velocity | **1,592** vs Braslow critical 600 | [CALC from 16] |
| **Consequence** | **Wing tripped at 26% chord** | |
| Δc_d for transition forced at 0.30 upper / 0.55 lower | **+0.00235** | [CALC, §3.4] |
| Endurance cost of that alone | **−4.69 h** | [CALC] |
| Device drag of the array: 3,087 denticles per row per wing at 3 mm pitch, frontal area 0.7 mm² each, C_D ≈ 0.4 on local q (u_e/U∞ = 1.539 → q ratio 2.37) | ΔC_D0 ≈ **+0.00053** | [EST] |
| Endurance cost of the device drag | **−1.05 h** | [CALC] |
| Mass of the printed denticle features, 9.26 m × 1 row | ≈0.3 kg | [EST] |
| Endurance cost of the mass | **−0.45 h** | [CALC] |
| **Total, computed as one combined case** (C_D0 = 0.02288, +0.3 kg) | | **−5.90 h (−0.246 d)** |

The combined figure is slightly smaller in magnitude than the sum of the separately-computed increments (4.69 + 1.05 + 0.45 = 6.19 h) because dEndurance/dC_D0 falls from −1,927 h/unit over 0.020→0.022 to −1,800 h/unit over 0.022→0.024. Increments computed at the baseline over-count when stacked; the combined run is the one to quote.

**The steelman, computed honestly.** The one route by which a vortex generator could pay on this aircraft is C_Lmax. The loiter speed is set by the stall constraint V ≥ 1.15·V_s, so raising C_Lmax lets the aircraft loiter slower and burn less. From the endurance model [CALC]:

| C_Lmax | Endurance | Δ |
|---|---|---|
| 1.60 (baseline) | 112.99 h | — |
| 1.65 | 114.03 h | **+1.04 h** |
| 1.70 | 114.96 h | **+1.97 h** |
| 1.80 | 116.54 h | **+3.56 h** |
| 1.90 | 117.79 h | +4.80 h |
| 2.00 | 118.75 h | +5.76 h |

Combined with the drag penalty of the trip and the device:

| Case | Endurance | Δ |
|---|---|---|
| Denticles, C_Lmax unchanged at 1.60 | 107.09 h | **−5.90 h** |
| Denticles, C_Lmax → 1.70 (+0.10) | 109.33 h | **−3.66 h** |
| Denticles, C_Lmax → 1.80 (+0.20) | 111.19 h | **−1.80 h** |

**Break-even requires C_Lmax ≥ 1.92, a gain of +0.32** (1.89 if the denticle mass is waived). Micro-vortex generators on high-lift aerofoils typically deliver +0.1 to +0.2 [27][DR], and that is on sections that are already separating. The FX 63-137 at Re 10⁶ is not. **The steelman does not close, and it misses by a margin larger than the whole benefit.**

There is also a second-order penalty the model does not capture: Selig & McGranahan measured **ΔC_l,max = −0.2** on the FX 63-137 from leading-edge roughness [25][M], which is the opposite sign. Whether a denticle array at 26% chord behaves like a trip (losing C_Lmax) or like a VG (gaining it) is genuinely unknown for this section and would have to be measured. A design whose sign is unknown, whose upside is +2 h and whose downside is −5 h, is not a design.

---

## 8. Manufacturing on a solo-built composite wing

### 8.1 The four routes, and what each costs

| Route | How | Areal mass | Feasible solo? | Tip quality |
|---|---|---|---|---|
| **Adhesive riblet film** | Buy pre-formed film, apply | **0.158 kg/m² measured** [13][DS]; **0.25 kg/m² [EST]** if scaled to 210 µm riblets | Application yes; **procurement no** — see §8.3 | Factory-sharp |
| **Moulded-in** | Riblet *negative* cut into the female mould; riblets form in the surface filler/gelcoat layer during cure | **≈0** — the riblets occupy a filler layer already in the mass budget (gelcoat is typically ~0.5 kg/m² [DR]) | **Only with option A/B skins** from `materials_pack.md` §6.7 [2]; requires a specialist to make the tool negative | Mould-limited, can be excellent |
| **Embossed lacquer** (Fraunhofer IFAM route) | Liquid dual-cure lacquer + UV-transparent silicone stamp bearing the negative, UV cure in contact, demould | ≈0 **if** it replaces the topcoat already required — but a 210 µm riblet needs a ≥250 µm coating layer, ≈0.29 kg/m², against ~0.10–0.15 kg/m² for a normal PU topcoat → **net +0.15 kg/m² [EST]** | Application yes; **the stamp is the specialist item** | Demonstrated in service, "dirt-repellent, UV-stable, abrasion- and erosion-resistant"; 2-year in-service demonstration, free-flight wear tests on an A300-600ST Beluga [21][M] |
| **3D printing** | Print the riblets, or print the skin with riblets | Prohibitive | **No** | MJF PA12 has Ra ≈ 11 µm and ±0.3% dimensional tolerance = ±1.14 mm over 380 mm [2][28] — it cannot hold a 210 µm feature at all. PolyJet (as Harvard used) resolves 42 µm XY / 16 µm Z, so a 210 µm riblet is 5 pixels wide with a 40–80 µm tip radius — **blunt by the standard that matters** |

### 8.2 Why tip sharpness decides the whole thing

The riblet tip is the functional element. Blunting it does not degrade performance gracefully:

- **Sinusoidal riblets with rounded peaks produce only 2% drag reduction against 8% for triangular riblets with very sharp tips** [19][M]
- **Tip rounding can reduce drag performance by up to 40%** [19][M]
- Non-ideally manufactured riblets remain net-beneficial but at reduced effectiveness [20][M]

A 40% loss takes the ARGUS-7 wing-plus-fuselage best case from +1.25 h to +0.75 h, and takes the film case from −0.96 h to −1.5 h. **There is no version of this that survives a blunt tip.**

### 8.3 Procurement — the practical blocker

There is no commercial riblet film available to a one-person programme in 9 m² quantities. The two suppliers are **Lufthansa Technik/BASF Coatings** (AeroSHARK, sold as a certified aircraft modification, not as material) and **MicroTau** (MAKO Flightfilm, in trials with Delta on a 767 and with Boom on the XB-1) [13][15][28][DS]. The 3M films used in the UIUC work were **"off-the-shelf experimental samples, manufactured solely for the purpose of the research and are not commercially available"** [5][DS]. **No public per-square-metre price for riblet film exists** [UNV] — the only public figures are a market size of USD 443M (2024) [28][DR], which says nothing about unit cost.

The moulded-in route needs a riblet negative over ~8–15 m² of tool surface. CNC-milling it is out: 210 µm pitch over 8 m² is ~38 km of toolpath per square metre, ~300 km total, which at 5 m/min is >1,000 machine-hours. **Direct Laser Interference Patterning** is the process that is actually used for this — it can pattern metallic moulds for hot embossing at rates approaching 1 m²/min, and patterned mould surfaces transfer into GFRP/CFRP during cure [22][DR]. That is a specialist subcontract, not a garage operation, and it must be costed before this option is taken seriously [UNV].

### 8.4 Durability over a 122-hour mission and repeated parachute landings

| Threat | Assessment |
|---|---|
| **Mission-duration erosion** | 122 h at 35.6 m/s is 15.6 million metres of relative air travel. Rain and particulate erosion at 4,000 m loiter is mild; the exposure is in climb and descent. The Fraunhofer riblet lacquer survived a two-year in-service application [21][M]; 3M film in airline service needed replacement every 2–3 years [6][DR]. **A single 5-day mission is not the problem.** |
| **Parachute landing** | The report recovers by parachute onto an **under-fuselage airbag + crush keel with 0.2–0.3 m stroke**, 4.5 kJ at touchdown, onto unprepared ground [1]. **Any riblet texture on the lower fuselage is consumed at every landing.** That eliminates the single largest riblet-eligible area (the pod, 3.85 m² fully turbulent) unless the belly is excluded, which costs roughly half the pod benefit. |
| **Field handling** | This is a disaster-response asset handled by non-specialists: tie-downs, transport cradles, de-icing, cleaning. A 210 µm sharp-tipped texture will not survive routine handling on the surfaces people touch. |
| **Contamination** | "Particles deposit more on sharp riblet tips than in the grooves" [19][DR]; the tips that do the work are the tips that foul. Riblets need cleaning discipline, and cleaning is abrasive. |
| **Icing** | Loiter band −5 to −15 °C [1]. Whether 210 µm grooves trap supercooled water and nucleate ice earlier than a smooth surface is **unknown** [UNV] and is a flight-safety question, not a performance question. |

### 8.5 Compatibility with the skin decision already on the table

The moulded-in route — the only route with a positive net answer — is compatible with exactly two of the seven skin options in `materials_pack.md` §6.7 [2]:

| Skin option | Riblets moulded in? |
|---|---|
| **A** Moulded CFRP/Rohacell sandwich, vacuum-bagged | **Yes** — the mould already exists and the negative goes in it |
| **B** Pultruded caps + moulded skin | **Yes** |
| E Moldless foam core + wet layup (Rutan) | **No** — no female tool exists; would need the embossed-lacquer route |
| C/C2/C3 Heat-shrink film aft of 32%/55% c | **No** — and the film sits precisely where the riblets would go |
| D Printed MJF skin panels | **No** — tolerance is 5× the riblet height |

**So the riblet question is downstream of, and strictly smaller than, the skin question.** Options A and B already carry `materials_pack.md`'s best endurance outcome (−2.0 to +2.0 h against baseline, versus −12 to −30 h for the alternatives). Choosing A or B is worth **12–28 h**; adding riblets to A or B is worth **at most 1.25 h**.

---

## 9. The endurance ledger

### 9.1 The drag build-up, and the share riblets can reach

Reproducing `materials_pack.md` §6.7's component build-up [2] from first principles as a check, using C_F = 0.074·Re^(−0.2) and standard body form factors [CALC]:

| Component | Wetted area | Re_L | C_F | FF | D/q | C_D0 (ref S = 3.9) | Pack's figure [2] |
|---|---|---|---|---|---|---|---|
| Fuselage pod 3.4 × 0.48 m | 3.845 m² | 5.97×10⁶ | 0.00327 | 1.1865 | 149.0 cm² | **0.00382** | 0.00382 ✓ |
| Twin booms 2 × 3.65 × 0.09 m | 2.064 m² | 6.41×10⁶ | 0.00322 | 1.1023 | 73.3 cm² | **0.00188** | 0.00188 ✓ |
| Inverted-V tail | 1.714 m² | ~5.3×10⁵ | 0.00234 (mixed) | 1.206 | 48.4 cm² | 0.00124 | 0.00124 ✓ |
| Wing (XFOIL span-integrated friction) | 8.03 m² | 4.9–9.9×10⁵ | — | — | 223.7 cm² | 0.00574 friction; 0.00782 with form [2] | 0.00782 |

The build-up closes on the pack's own numbers exactly for the fuselage and booms, confirming that the pack treated both as **fully turbulent** — which they are, the pod sitting in propwash and the booms in the wing's wake.

**Drag composition at loiter** [CALC]:

| | C_D | Share of total |
|---|---|---|
| Induced, C_L²/(π·AR·e) at C_L = 1.2098, AR 22, e 0.85 | 0.02491 | **55.5%** |
| Parasite, C_D0 | 0.02000 | 44.5% |
| — of which total skin friction | 0.01169 | 26.0% |
| — of which **turbulent and riblet-coverable** | **0.00784** | **17.5%** |
| **Total C_D at loiter** | **0.04491** | 100% |

**Only 17.5% of ARGUS-7's loiter drag is reachable by riblets at all.** A 6% reduction on that is 1.05% of total drag; 8% is 1.40%.

### 9.2 Zone-by-zone

| Zone | Coverable turbulent friction, C_D0 | Coverable area | ΔC_D0 at 6% | ΔC_D0 at 8% |
|---|---|---|---|---|
| Wing, turbulent region (§3.2) | 0.00306 | 3.26 m² | −0.000184 | −0.000245 |
| Fuselage pod, 85% coverable | 0.00274 | 3.27 m² | −0.000164 | −0.000219 |
| Booms, 90% coverable | 0.00153 | 1.86 m² | −0.000092 | −0.000123 |
| Tail, turbulent region, 90% | 0.00051 | 0.85 m² | −0.000031 | −0.000041 |
| **Total** | **0.00784** | **9.23 m²** | **−0.000470** | **−0.000627** |

[CALC]

### 9.3 The ledger

Endurance deltas against the report's 112.8 h / 4.70 d, using −2.00 h per 0.001 C_D0 and −1.517 h/kg [CALC]:

| Build | Coverage | DR | ΔC_D0 | Aero Δ | Mass | Mass Δ | **NET** |
|---|---|---|---|---|---|---|---|
| **Film at 0.158 kg/m²** (AeroSHARK measured) | wing only | 6% | −0.000184 | +0.37 h | 0.52 kg | −0.78 h | **−0.42 h** |
| Film at 0.158 kg/m² | wing only | 8% | −0.000245 | +0.49 h | 0.52 kg | −0.78 h | **−0.29 h** |
| Film at 0.158 kg/m² | all surfaces | 5% | −0.000392 | +0.78 h | 1.46 kg | −2.21 h | **−1.43 h** |
| Film at 0.158 kg/m² | all surfaces | 6% | −0.000470 | +0.94 h | 1.46 kg | −2.21 h | **−1.27 h** |
| Film at 0.158 kg/m² | all surfaces | 8% | −0.000627 | +1.25 h | 1.46 kg | −2.21 h | **−0.96 h** |
| Film at 0.158 kg/m² | all surfaces | 13% (APG) | −0.001019 | +2.03 h | 1.46 kg | −2.21 h | **−0.18 h** |
| **Film at 0.25 kg/m²** (scaled to 210 µm) | all surfaces | 8% | −0.000627 | +1.25 h | 2.31 kg | −3.50 h | **−2.25 h** |
| **Moulded-in, mass-neutral** | wing only | 6% | −0.000184 | +0.37 h | 0 | 0 | **+0.37 h** |
| Moulded-in | wing only | 8% | −0.000245 | +0.49 h | 0 | 0 | **+0.49 h** |
| Moulded-in | fuselage+booms+tail | 6% | −0.000287 | +0.57 h | 0 | 0 | **+0.57 h** |
| **Moulded-in** | **all surfaces** | **6%** | **−0.000470** | **+0.94 h** | 0 | 0 | **+0.94 h** |
| Moulded-in | all surfaces | 8% | −0.000627 | +1.25 h | 0 | 0 | **+1.25 h** |
| Moulded-in | all surfaces | 13% (APG) | −0.001019 | +2.03 h | 0 | 0 | **+2.03 h** |
| **Embossed lacquer at +0.15 kg/m² net** | all surfaces | 8% | −0.000627 | +1.25 h | 1.38 kg | −2.10 h | **−0.85 h** |
| **Harvard denticles** at 26% c | wing | — | +0.00288 | −5.47 h | 0.3 kg | −0.43 h | **−5.90 h** |
| Denticles, with +0.10 C_Lmax | wing | — | +0.00288 | −3.24 h (net of C_Lmax) | 0.3 kg | −0.42 h | **−3.66 h** |
| **Risk: riblet zone trips upper x_tr 5 points early** | wing | — | +0.00057 | −1.13 h | — | — | **−1.13 h** |
| Risk: non-optimal riblet size (+6% drag, per [5]) | all surfaces | −6% | +0.000470 | −0.94 h | 1.46 kg | −2.21 h | **−3.15 h** |
| Risk: wing tripped at 20% chord | wing | — | +0.00386 | −7.70 h | — | — | **−7.70 h** |

### 9.4 Break-even, and why this works on a 777 and not here

**Break-even conditions for riblet film on ARGUS-7, all eligible surfaces** [CALC]:

- At 6% friction reduction, the film would have to weigh **less than 67 g/m²**. AeroSHARK measures **158 g/m²**.
- At 158 g/m², the film would have to deliver **14.2% turbulent-friction reduction**. The best *laboratory* result ever obtained on any passive riblet is **≈10%** [7][M]; the best flight result is **≈6%** [9][M].
- At 250 g/m² (210 µm riblets), it would have to deliver **22.4%**.

**None of these is achievable. The film case is closed.**

**The scaling that explains it.** For a riblet of optimal size, spacing s = 15.1·ν/u_τ, so the material mass per unit area is ρ_mat·φ·s ∝ ν/u_τ, while the drag saved per unit area is DR·τ_w = DR·ρ_air·u_τ². The figure of merit — **newtons of drag saved per kilogram of riblet material** — is therefore

> **F ∝ ρ_air · u_τ³ / ν**

| | ρ_air | V | τ_w | u_τ | ν | s at s⁺ = 17 | **F** |
|---|---|---|---|---|---|---|---|
| ARGUS-7, wing x/c 0.70, loiter | 0.819 | 35.6 | 3.05 Pa | 1.93 m/s | 2.028×10⁻⁵ | 179 µm | 2.90×10⁵ |
| B777, cruise FL340 M0.84 | 0.380 | 249.8 | 21.3 Pa | 7.49 m/s | 3.825×10⁻⁵ | 87 µm | 4.18×10⁶ |

**Riblets return 14.4× less drag reduction per kilogram of riblet material on ARGUS-7 than on a 777 in cruise** [CALC]. The reason is exactly the operating point that makes them manufacturable: low speed and high altitude give a large viscous length, which makes the riblets big, which makes them heavy, without making them proportionally more effective.

**And then the mass matters 14× more.** The 150 kg of AeroSHARK on a 777-300ER is **0.043% of MTOW**. The 1.46 kg on ARGUS-7 is **0.59%** — and because ARGUS-7 is 40.6% fuel by mass with a fixed MTOW, that mass comes straight out of the tank at **1.34% of endurance per kilogram**.

| | B777-300ER + AeroSHARK | ARGUS-7 + riblet film |
|---|---|---|
| Friction share of cruise/loiter drag | 42.8% [6][M] | **26.0%** [CALC] |
| Induced share | ~35–40% [DR] | **55.5%** [CALC] |
| Measured / estimated drag reduction | **0.9% cruise, measured** [6][M] | 1.05% at 6% [CALC][EST] |
| Film area | 950 m² | 9.23 m² |
| Film mass | 150 kg | 1.46 kg |
| Film mass / MTOW | **0.043%** | **0.59%** |
| Mass cost as a fraction of the aero benefit | ≈9% [EST] | **235%** [CALC] |

**The aerodynamics transfer almost exactly — 0.9% versus 1.05% of total drag. The mass accounting does not, by a factor of 25.** That is the entire answer to the sponsor's question, and it is not about laminar flow at all; laminar flow only makes it worse.

---

## 10. Verdict

### Is this worth pursuing for THIS aircraft?

**No, not as a build item, and not now.**

The honest summary in one paragraph: riblets are real, they work, and they would work on this aircraft — the wing has 3.26 m² of genuinely turbulent surface carrying 53% of its friction, the optimal riblet size is a manufacturable 210 µm, a single geometry covers the whole flight envelope at s⁺ 13–22, the adverse pressure gradient of the FX 63-137's recovery is if anything favourable to them, and there is a wind-tunnel dataset at almost exactly our chord and Reynolds number showing 2–4% section drag reduction from a film applied only behind natural transition. And after all of that, the very best case is **+1.25 h out of 112.8 h**, achievable only if the riblets cost zero mass, and it is bought against a downside branch where a 5-point-of-chord placement error costs **−1.13 h** and a mis-sized riblet costs **−3.15 h**. Applied the way it is actually available — as film — it is **net negative in every configuration examined**.

### Where is it most likely to pay?

Ranked:

1. **Fuselage pod and booms, moulded or embossed.** 5.13 m² of fully turbulent flow with **no laminar run to lose**, therefore no downside branch. Worth **+0.51 h (6%) to +0.68 h (8%)** at zero mass with the full pod covered, falling to **+0.41 to +0.55 h** once the belly is excluded — and the belly must be excluded, because the crush keel destroys it on every landing [CALC]. This is the only place where the risk-adjusted answer is positive.
2. **Wing, aft of 62%/70% chord, moulded into the female tool, only if skin option A or B is selected anyway.** Worth **+0.28 to +0.38 h**. Requires the mould negative as a specialist subcontract [UNV cost].
3. **Tail.** +0.06 h. Not worth the drawing.
4. **Nowhere, as film.** −0.29 to −2.56 h.
5. **Nowhere, as denticles.** −3.7 to −6.2 h.

### What to tell the sponsor

The article is about a real and interesting piece of biology, and the Harvard group's work is good work. But it is a **vortex-generator and separation-control** result, obtained on a symmetric section at a Reynolds number 20× below ours, using surface features that are **2.7× taller than the critical roughness height at our flight condition** and that the authors themselves describe as tripping the boundary layer. It does not transfer.

The riblet technology it is conflated with in the press *does* transfer aerodynamically — the percentage drag reduction on ARGUS-7 comes out almost identical to what Lufthansa Technik measures on a 777. What does not transfer is the mass bookkeeping: an airliner carries 150 kg of film on 350 t and pays about 9% of the benefit for it; ARGUS-7 would carry 1.46 kg on 250 t and pay 235% of the benefit for it, because on an endurance aircraft with a fixed MTOW every kilogram of structure is a kilogram of fuel.

**There is one thing in this pack the sponsor should act on, and it is not riblets.** It is the transition survey in §3. `materials_pack.md` §13 asked where transition sits and this pack has answered it — **50–61% chord upper, 61–68% lower, 40.5% of the wing turbulent**. That answer confirms the C_D0 = 0.020 baseline, and it says that the *laminar* 59.5% of the wing is where the drag leverage is. Protecting it is worth **13.6 h**. Texturing the other 40.5% is worth **0.4 h**. Spend the attention accordingly.

---

## 11. Recommended simulation plan

**Fidelity ladder, with the honest statement of what each tool can and cannot do.**

### Tier 0 — already done in this pack, at zero cost

XFOIL cannot model riblets. It **can** answer the two questions that actually decide the case, and it has:

- **Transition location** across the span and the mission (§3.2, §3.3) — this bounds the eligible area at 40.5% of the wing.
- **The cost of getting the placement wrong** (§3.4) — this bounds the downside at −1.13 h per 5 points of chord.

Both are reproducible from `data/airfoils/fx63137.dat` with the commands in the Appendix. **No further work is needed to reject the film option**; the mass arithmetic in §9.4 does that without any aerodynamic model at all.

### Tier 1 — the right fidelity for the remaining question (recommended)

**An empirical riblet drag model applied to XFOIL's own C_f(x) distribution.** This is cheap, defensible, and is exactly the level of fidelity the decision warrants.

Method:

1. Run XFOIL viscous at each span station and each mission point; `DUMP` gives x, U_e/U∞, δ*, θ, C_f, H.
2. At each x in the turbulent region, compute u_τ(x) = U∞·√(C_f(x)/2), ℓ_v(x) = ν/u_τ(x), and for a candidate riblet geometry the groove parameter ℓ_g⁺(x) = √(A_g)/ℓ_v(x). For a symmetric V-groove with h = s, √(A_g) = s/√2.
3. Apply the García-Mayoral & Jiménez collapsed drag curve [8][M]: linear viscous regime **DR ≈ m_ℓ·ℓ_g⁺** with m_ℓ from the protrusion height (experimental values cluster at m₀ = 0.66–0.785), peaking at **ℓ_g⁺,opt = 10.7 ± 1.0** with **DR_max = 0.83·m_ℓ·ℓ_g⁺,opt ≈ 8.9·m_ℓ**, and falling to zero and reversing beyond. Anchor the peak to the flight-demonstrated 5–6% rather than the laboratory 10%.
4. Integrate ΔC_f·dx over the covered region, span-integrate, and feed ΔC_D0 into the endurance model.
5. Repeat for the adverse-pressure-gradient enhancement of [10] as an upper bound, and for a 40% tip-rounding knockdown [19] as a lower bound.

Effort: **under a day**, no new tools, entirely inside the repository's existing Python + XFOIL stack. It would refine the +0.94 h number and would not change its sign.

**Validation target:** the model must reproduce Sareen et al.'s measured −2 to −4% of section drag on the DU 96-W-180 at Re 1×10⁶ with 62 µm and 100 µm riblets, and the **+6% at 150 µm** [5][M]. If it cannot reproduce the sign reversal at 150 µm, it is not calibrated and its ARGUS-7 output is worthless.

### Tier 2 — RANS with a riblet-modified wall function (only if Tier 1 says pursue)

This is what Lufthansa Technik actually did, and their description of it is the best available scoping estimate [6][DS]:

> "Riblets are too small to resolve them geometrically. To resolve the effect of Riblets numerically, an **adaption of the turbulence model** is required. Development of modified and calibrated CFD Solver in cooperation with Ansys Germany GmbH. Validation of the modified solver with wind tunnel tests in cooperation with DLR Berlin and DNW… **Calibration of SST Turbulence Model using oil channel model**."

and the cost:

> "More than **100 calculations per aircraft type**. Temporary use of **six High Performance Clusters in parallel**. Generation of **14 TB** of simulation data over **6 months**."

**This is out of reach for a €60k solo programme, and it is out of proportion to a 1.25 h prize.** More importantly, the modified wall function has to be *calibrated* against an oil-channel measurement of the specific riblet geometry — which the programme does not have and cannot cheaply obtain. Running an uncalibrated riblet wall function would produce a number with no error bar.

A second finding from the same source is worth flagging: **riblets change the loads.** "Riblets create secondary effects due to reduction of boundary layer thickness → change of aerodynamic and structural loads, impact on handling characteristics, possible influence on Autoflight systems" [6][DS]. On a wing already at 14.2% semi-span tip deflection at limit load [2], a spanwise-varying change in section drag and boundary-layer displacement is not automatically benign.

### Tier 3 — riblet-resolved LES/DNS

Correct physics, wrong programme. Resolving 210 µm riblets over even a 100 mm × 100 mm patch at Re_θ ~2,000 is a 10⁷–10⁸-cell problem per case. **Not even the AeroSHARK programme did this** — it used calibrated RANS. Reject.

### Tier 4 — the experiment that would actually settle it, and why it is the right thing to build anyway

**Measure the transition location on the first wing.** Infrared thermography in flight, or a surface oil-flow / tuft survey on the ground rig, at the loiter C_L and at three span stations.

This is the highest-value experiment in the programme for reasons that have nothing to do with riblets:

- If x_tr lands where XFOIL says (50–61% upper), the C_D0 = 0.020 baseline is confirmed, the eligible riblet area is 40.5%, and the riblet ceiling is +1.25 h. **Drop riblets.**
- If x_tr is much further forward — because the as-built surface is worse than the VariEze/Long-EZ standard `materials_pack.md` §6.2 relies on [2] — then the wing is losing **up to 13.6 h** to a surface-quality problem, riblets become *more* attractive because more area is eligible, **and fixing the surface is worth ten times more than adding riblets.**

**In either branch, the measurement tells you to work on the surface, not on the texture.** That is the correct conclusion and it costs an IR camera and an afternoon.

---

## 12. Open questions

**Aerodynamic**

1. **Ncrit is assumed, not known.** All transition locations in §3 use Ncrit = 9. A UAV loitering in a quiet atmosphere at 4,000 m may see Ncrit 11–13, which moves transition aft and *reduces* the riblet-eligible area further; a propeller-wash-immersed or turbulent-air condition gives Ncrit 5–7 and moves it forward. **The whole §3 table should be re-run at Ncrit 7 and 12 as a sensitivity band before any number in it is quoted as settled.** [UNV]
2. **The FX 63-137's tabulated polars at Re 0.5–1.5×10⁶ have still not been obtained.** `materials_pack.md` §13 open question 1 remains open [2]. XFOIL agrees with itself; it has not been checked against the Stuttgart Profilkatalog or UIUC measurements at these Reynolds numbers. The FX 63-137 has a known "high-drag knee" and non-monotonic Re behaviour below 5×10⁵ [25][M], which is exactly where the tip sits at light loiter.
3. **Is the fuselage pod really fully turbulent from the nose?** The build-up in §9.1 assumes so, and the `argus7_v1.yaml` OML implies a tractor propeller, which would settle it. If the prop is a pusher and the nose is clean, the pod carries a laminar run and the riblet-eligible area drops. [UNV — the report does not state the propeller position]
4. **Propwash swirl angle on the pod** — riblets tolerate ≤15° yaw [24][M] and the swirl behind a lightly-loaded 0.813 m propeller at 3.4 kW should be well inside that, but it has not been computed. [UNV]
5. **Does the adverse-pressure-gradient enhancement (13% vs 6%, [10]) survive on a real airfoil recovery, or is it a canonical-rig artefact?** The whole "best case" column depends on it, and the AeroSHARK flight data shows no such doubling. [UNV]

**Manufacturing and materials**

6. **What does a DLIP riblet negative over 8–15 m² of female mould actually cost, and who does it?** This is the single number that decides whether the moulded-in route exists at all for this programme. [UNV]
7. **Areal mass of a 210 µm riblet layer, measured rather than estimated.** The 0.25 kg/m² figure is scaled from AeroSHARK's measured 0.158 kg/m² at ~50 µm riblets and is [EST]. A single moulded test panel weighed against a smooth control settles it and could move the film verdict by ±0.8 h.
8. **Achievable tip radius by each route.** 40% of the benefit rides on it [19][M]. Measure with a profilometer on a moulded coupon, a PolyJet coupon and a lacquer-embossed coupon.
9. **Riblet film procurement:** does any supplier sell 10 m² of riblet film to a non-airline customer, and at what price? No public per-m² price exists. [UNV]
10. **Does a 210 µm groove texture change the icing behaviour** at the −5 to −15 °C loiter band? This is a safety question, not a performance one, and it is unanswered. [UNV]

**Programme**

11. **What is the as-built transition location?** See §11 Tier 4. This is the cheapest decisive experiment in the aerodynamics programme, exactly as the moulded-plug test segment is in the materials programme [2]. **Do it on the first wing, before the riblet question is reopened.**
12. **Does the sponsor have a source showing riblets net-beneficial forward of transition on a laminar-bucket section?** This pack could not find one. If it exists, it inverts §3.5 and should be produced.

---

## 13. Sources

| # | Source | Type |
|---|---|---|
| [1] | `docs/argus7_design_report.md` v1.0, 2026-08-20 — §2 configuration, §4 aerodynamics and mission table, §5 structures, §7 recovery, Annex A premortem | project document |
| [2] | `research/materials_pack.md`, 2026-08-20 — §6.1 surface criteria, §6.7 skin comparison and transition-location model, §6.8 endurance ledger, §13 open questions | project document |
| [3] | Harvard SEAS, L. Burrows, "Using shark scales to design better drones, planes, and wind turbines" — subtitled *"Bioinspired vortex generators increase airfoil lift, decrease drag"*, 7 Feb 2018 — https://seas.harvard.edu/news/using-shark-scales-design-better-drones-planes-and-wind-turbines | press release (the sponsor's starting point) |
| [4] | A. G. Domel, M. Saadat, J. C. Weaver, H. Haj-Hariri, K. Bertoldi & G. V. Lauder, "Shark skin-inspired designs that improve aerodynamic performance", *J. R. Soc. Interface* **15**(139):20170828, 1 Feb 2018, DOI 10.1098/rsif.2017.0828 — https://pmc.ncbi.nlm.nih.gov/articles/PMC5832729/ | [M] |
| [5] | A. Sareen, R. W. Deters, S. P. Henry & M. S. Selig, "Drag Reduction Using Riblet Film Applied to Airfoils for Wind Turbines", *ASME J. Solar Energy Engineering* **136**(2):021007 (May 2014), DOI 10.1115/1.4024982; earlier as AIAA 2011-558 — https://m-selig.ae.illinois.edu/pubs/SareenDetersHenrySelig_2014_ASME-JSEE-AirfoilDragReduction-with-Riblets.pdf | [M] — **the closest read-across to ARGUS-7 in the whole literature** |
| [6] | S. Kuntzagk (Lufthansa Technik), "Aeroshark — Drag Reduction Using Riblet Film on Commercial Aircraft", Hamburg Aerospace Lecture Series, RAeS Hamburg / DGLR / VDI / ZAL / HAW Hamburg, 18 Apr 2024, DOI 10.5281/zenodo.11214243 — https://www.fzt.haw-hamburg.de/pers/Scholz/dglr/hh/text_2024_04_18_Aeroshark.pdf | [M][DS] — operator engineering deck with measured delta-drag and the CFD scoping |
| [7] | D. W. Bechert, M. Bruse, W. Hage, J. G. T. van der Hoeven & G. Hoppe, "Experiments on drag-reducing surfaces and their optimization with an adjustable geometry", *J. Fluid Mech.* **338**:59–87 (1997) | [M] |
| [8] | R. García-Mayoral & J. Jiménez, "Drag reduction by riblets", *Phil. Trans. R. Soc. A* **369**:1412–1427 (2011) — ℓ_g⁺,opt = 10.7 ± 1.0, DR_max = 0.83·m_ℓ·ℓ_g⁺,opt — https://torroja.dmt.upm.es/pubs/2011/rgm_jj_philtrans11.pdf | [M] |
| [9] | M. J. Walsh, W. L. Sellers & C. B. McGinley, "Riblet drag reduction at flight conditions", AIAA-88-2554; *J. Aircraft* (1989) — Learjet 28/29 fuselage, ≈6% at s⁺ = 12 — https://ntrs.nasa.gov/citations/19880053537 | [M] |
| [10] | R. Debisschop & F. T. M. Nieuwstadt, "Turbulent boundary layer in an adverse pressure gradient: effectiveness of riblets", *AIAA J.* **34** (1996), DOI 10.2514/3.13170 — 13% APG vs 6% ZPG | [M] |
| [11] | G. R. Grek, V. V. Kozlov & S. V. Titarenko, "An experimental study of the influence of riblets on transition", *J. Fluid Mech.* (1996); and V. V. Kozlov & G. R. Grek, "Effect of Riblets on Flow Structures" — https://dwc.knaw.nl/DL/publications/PU00011240.pdf | [M] |
| [12] | D. S. Miklosovic, M. M. Murray, L. E. Howle & F. E. Fish, "Leading-edge tubercles delay stall on humpback whale (*Megaptera novaeangliae*) flippers", *Physics of Fluids* **16**(5):L39 (2004) | [M] |
| [13] | Lufthansa Technik / Lufthansa Group AeroSHARK product and press pages — **950 m² adds 150 kg**, ≈1.1% fuel on 777-300ER; 830 m² ≈1% on 777-200ER; 747-400 STC Nov 2019 at up to 500 m²; >232,000 fleet flight hours by Aug 2025 — https://www.lufthansagroup.com/en/themes/aeroshark.html | [DS] |
| [14] | Austrian Airlines / FlightGlobal, "Austrian details fuel-burn saving from aerodynamic film on 777s", Mar 2026 — **0.7% measured drag reduction**, 930 t fuel, 3,000 t CO₂ over 12 months on four 777s | [M] |
| [15] | Lufthansa Technik & Airbus, "collaborate on AeroSHARK wing & tailplane development", 19 May 2026 — extends the STC to A330ceo wings, horizontal stabiliser and vertical tailplane; **>2% target** for a fully modified aircraft — https://www.lufthansa-technik.com/en/lufthansa-technik-and-airbus-collaborate-on-aeroshark-wing-tailplane-development-07b37b5ed773fde8 | [DS] |
| [16] | A. L. Braslow & E. C. Knox, critical roughness Reynolds number Re_k ≈ 600; Schlichting admissible-roughness Re_k ≈ 100 on freestream — NASA roughness-effects literature — https://ntrs.nasa.gov/api/citations/19660023725/downloads/19660023725.pdf (as `materials_pack.md` [22]) | [M] |
| [17] | B. J. Holmes, C. J. Obara, G. L. Martin & C. S. Domack, "Manufacturing Requirements", NASA Langley / PRC Kentron, N88-23744 — Carmichael waviness, X-21 step and gap tolerances — https://ntrs.nasa.gov/api/citations/19880014361/downloads/19880014361.pdf (as `materials_pack.md` [23]) | [M] |
| [18] | M. Ananth, A. Vaid et al., "Riblet Performance Beneath Transitional and Turbulent Boundary Layers at Low Reynolds Numbers", *AIAA J.* (2023), DOI 10.2514/1.J062418 — the riblet leading-edge shear layer and the mitigating ramp | [M] |
| [19] | "On the tip sharpness of riblets for turbulent drag reduction", *Acta Mechanica Sinica* (2022), DOI 10.1007/s10409-022-09019-x — rounded-peak sinusoidal riblets 2% vs 8% for sharp triangular; tip rounding costs up to 40% of performance; particles deposit preferentially on sharp tips | [M] |
| [20] | J. Tiainen, A. Grönman, A. Jaatinen-Värri & L. Pyy, "Effect of non-ideally manufactured riblets on airfoil and wind turbine performance", *Renewable Energy* **155**:79–89 (2020) | [M] |
| [21] | Fraunhofer IFAM riblet lacquer: dual-cure UV acrylate + polyurethane embossed against a UV-transparent stamp, continuous rolling process; "dirt-repellent, UV-stable and abrasion- and erosion-resistant"; two-year in-service application and free-flight wear tests on an Airbus A300-600ST Beluga — http://publica.fraunhofer.de/documents/N-255045.html | [M][DR] |
| [22] | Riblet manufacture by Direct Laser Interference Patterning, incl. patterning of metallic moulds for transfer into GFRP/CFRP during cure, ~1 m²/min — DE102017206968A1; US 12,115,599 | [DR] |
| [23] | P. Catalano, D. de Rosa, B. Mele, R. Tognaccini & F. Moens, "Performance Improvements of a Regional Aircraft by Riblets and Natural Laminar Flow", *J. Aircraft* **57**(1):29–40 (2020), DOI 10.2514/1.C035445 — NLF and riblets each ≈12% max, combined >20% at cruise | [M] |
| [24] | W. Hage, D. W. Bechert et al., "Yaw Angle Effects on Optimized Riblets", in *Aerodynamic Drag Reduction Technologies*, Springer, DOI 10.1007/978-3-540-45359-8_29 — yaw effects negligible to 15°; 45° trapezoidal grooves least sensitive | [M] |
| [25] | M. S. Selig & B. D. McGranahan, "Wind Tunnel Aerodynamic Tests of Six Airfoils for Use on Small Wind Turbines", AIAA 2004-1188 — FX 63-137 clean and tripped, ΔC_l,max = −0.2 from LE roughness (as `materials_pack.md` [6]) — https://m-selig.ae.illinois.edu/pubs/SeligMcGranahan-2004-AIAA-2004-1188.pdf | [M] |
| [26] | M. Drela, "XFOIL: An Analysis and Design System for Low Reynolds Number Airfoils", *Low Reynolds Number Aerodynamics*, Lecture Notes in Engineering **54**, Springer (1989); XFOIL 6.99 as installed at `/usr/bin/xfoil` | tool |
| [27] | J. C. Lin, "Review of research on low-profile vortex generators to control boundary-layer separation", *Prog. Aerospace Sci.* **38** (2002); J. C. Lin, S. K. Robinson, R. J. McGhee & W. O. Valarezo, "Separation control on high-lift airfoils via micro-vortex generators", *J. Aircraft* **31**:1317–1323 (1994) | [M][DR] |
| [28] | MicroTau "MAKO Flightfilm" product pages; Delta Air Lines / Boeing 767 and Boom XB-1 riblet trials; riblet-film market sizing — https://www.microtau.com.au/product | [DS][DR] |
| [29] | Airbus A320 / 3M riblet flight test (1989, "2% proven saving according to Airbus") and Cathay Pacific A340-300 in-service degradation trial, incl. the 2–3 year film replacement interval — reported in [6] and in the riblet review literature | [DR] |
| [30] | HP Multi Jet Fusion PA12 surface roughness and dimensional tolerance (Ra ≈ 11 µm; ±0.3% over 380 mm) — as `materials_pack.md` [5][28] | [DS][M] |

---

## Appendix — reproducibility

Every `[CALC]` figure in this pack derives from four groups, all reproducible from files already in the repository.

**1. XFOIL transition and boundary-layer survey.** Input: `data/airfoils/fx63137.dat` (Lednicer 49/49, sha256 `8c3a70fa1639885a72bb1394ff6666db637efc4971d3594f1a3882c1b9f18c5d`), converted to Selig order by reversing the upper-surface block and concatenating the lower, de-duplicating the shared leading-edge point (97 points). Then:

```
LOAD <selig file>
PPAR / N 300 / T 1.0
OPER / VPAR / N 9
VISC <Re> / ITER 300
CL 1.21
DUMP <file>          ! s, x, y, Ue/Vinf, Dstar, Theta, Cf, H
```

Re values, heavy loiter: Re(y) = 35.62·c(y)/2.028×10⁻⁵ with c(y) = 0.581 + (0.261−0.581)·(y/4.6314), evaluated at ten mid-panel stations y = (i+0.5)·0.46314, i = 0…9 → Re = 992,372 down to 486,526. XFOIL's dumped C_f is normalised on **freestream** dynamic pressure — verified by comparing x/c = 0.7435 (C_f = 0.004963, H = 1.498, Re_θ = 1,416) against Ludwieg–Tillmann (c_f = 0.003395 on edge velocity; ratio 1.462 vs (U_e/U∞)² = 1.525, 4% agreement).

For the forced-transition sweep, `VPAR / XTR` with the two values on **separate lines** (XFOIL silently ignores them on the same line, and reports natural transition instead — this bites).

**2. Turbulent-fraction and coverage integration.** Split each surface at the point where H first falls below 2.0 (fully turbulent). Friction integral D/q = 2·Σ_stations [Σ C_f·|Δx|]·c(y)·Δy; wetted area with section perimeter/chord = 2.0603 measured off the pinned coordinates (XFOIL arc length at the trailing edge). Covered area and covered friction use the same sums restricted to x ≥ x_film.

**3. Wall units and riblet sizing.** u_τ(x) = U∞·√(C_f(x)/2); ℓ_v = ν/u_τ; s(s⁺) = s⁺·ℓ_v; shear-weighted mean uses weights C_f(x)·|Δx|·c(y)·Δy, matching [5]'s stated method. For a symmetric V-groove with h = s, ℓ_g = s/√2, so s⁺_opt = √2·ℓ_g⁺,opt = √2·10.7 = 15.1 [8].

**4. Endurance.** Identical to `materials_pack.md` Appendix group 3: ρ = 0.81935, S = 3.9, AR = 22, e = 0.85, C_L = C_Lmax/1.15², η_p = 0.84, P_el = 500 W through η_alt = 0.75, BSFC = 270 g/kWh, V = √(2W/(ρSC_L)), P_shaft = ½ρV³S·C_D/η_p + P_el/η_alt, ṁ = BSFC·P_shaft, integrated 250 kg → (148.5 + Δm) kg over 200,000 steps. **Validation: C_D0 = 0.016 returns +8.589 h against the report's stated +8.64 h (0.6% agreement), and reproduces every isolated sensitivity in `materials_pack.md` §6.8 to the last quoted digit.** Deltas are then applied to the report's headline 112.8 h.

Anyone re-deriving these should get the same answers; where they do not, the discrepancy is more interesting than the number.

---

(see above)