# ARGUS-7 — CONFIGURATION HYPOTHESIS STUDY

**Date:** 2026-08-21 · **Scope:** whole-aircraft configuration for the 250 kg MTOW / 9.26 m span / AR 22 point of `docs/argus7_design_report.md` · **Companion to:** `research/empennage_trade.md`, `research/materials_pack.md`, `research/design_pack.md`

**The question this pack was written to answer:** at loiter C_L 1.21 induced drag is **55.5%** of total drag and parasite drag only 44.5%, yet every optimisation the programme has run — riblets, boom deletion, surface finish — attacks the smaller half. What configuration change attacks the larger half, and can the booms be deleted entirely?

**The short answer is that the premise is right and the payoff is not there.** The induced-drag half of the budget is real, but it is nearly all *already spent well*: the committed AVL run on this exact planform returns an inviscid span efficiency of **0.9786** against a theoretical ceiling of 1.0000, so the whole remaining spanload lever is worth **+0.93 h**, not the +7.1 h the report's own e-sensitivity table appears to promise. The recoverable part of the (1 − e) deficit is **viscous**, not spanload, and it is a section-and-surface question. Meanwhile the aircraft as specified cannot carry its fuel and cannot be balanced, and those two defects between them are worth **−60 h**.

---

## 0. How to read this

Provenance tags are the same as `materials_pack.md` §0 and `empennage_trade.md` §0:

| Tag | Meaning |
|---|---|
| **[DS]** | Manufacturer datasheet, quoted verbatim |
| **[M]** | Measured / published experimental data |
| **[CALC]** | Computed here from the committed geometry and the committed simulator; equations inline, reproducible from the appendix |
| **[EST]** | Engineering estimate — a judgement, not a measurement |
| **[DR]** | Derived from a secondary source that itself cites a primary one |
| **[UNV]** | Unverified — needs test, tool run, or vendor confirmation |
| **[AN]** | **From one of the six deep analyses or its refutation.** Those runs used the vendored AVL 3.36, XFOIL on the repository's own `data/airfoils/fx63137.dat`, and independent lifting-line and Trefftz-plane solvers. **They were not re-run in this pack.** What *was* re-run here is every endurance integration (on the committed `argus7.mission.sim`) and every geometry number (on the committed `argus7.design.geometry`) — so a `[CALC]` tag in this pack means exactly that and nothing more |

**Three rules applied throughout.**

1. **Six hypotheses were analysed in depth and every one of them was adversarially refuted on at least one load-bearing number. Where a refuter corrected a number, this pack uses the refuter's number and says so at the point of use.** §2.3 lists every such correction.
2. **Where this pack disagrees with a repository source it says so and shows the arithmetic.** Five such disagreements are flagged inline: **§1** (the report's fuel density does not exist), **§3.5** (the propeller's absorbed-power ceiling is a sea-level number), **§4.2** (the report's own e-sensitivity ladder is unreachable above e = 0.866), **§5** (every published endurance number is against a baseline that cannot be built), and **§7 / P2-3** (`materials_pack` §2.3's limit-load tip deflection does not reproduce). Two of the five are corrections to the *tasking's* own established list, not to a published pack.
3. **Where a number is an assumption dressed as a result it is tagged, and its sensitivity is given.** The single largest such number in this study is `aero.oswald_e = 0.85`, which `design/argus7_v1.yaml` tags `report-§4` and which §4 of the report states with no derivation.

**Calibration check on the endurance model.** Unlike the earlier packs, this one does not re-implement the report's §4 loiter model — it calls **the committed simulator**, `argus7.mission.sim.simulate_loiter`, at the report's own operating point (ISA 4,000 m, ρ = 0.81913 kg/m³, S = 3.9 m², AR 22, e = 0.85, C_L = 1.6/1.15² = 1.20983, η_prop = 0.84, 500 W payload through a 0.75 alternator path, BSFC 270 g/kWh, 20,000 equal-fuel-mass steps from 250 → 148.5 kg, float64):

| Quantity | This pack (committed sim) | Repository source | Δ |
|---|---|---|---|
| Baseline endurance | **112.977 h** | report §4: 112.8 h [1] | +0.16% |
| C_D0 = 0.016 | **+8.588 h** | report §4: +0.36 d = +8.64 h [1] | −0.6% |
| C_D0 = 0.022 | **−3.854 h** | `materials_pack` §6.8: −3.8 h [2] | −1.4% |
| C_D0 = 0.024 | **−7.453 h** | `materials_pack` §1: −7.4 h [2] | −0.7% |
| C_Lmax 1.6 → 1.4 | **−5.370 h** | `materials_pack` §1: −5.4 h [2] | −0.6% |
| Mass exchange, MTOW fixed | **1.516 h/kg** | tasking / both packs: 1.5 h/kg | +1.1% |
| Parasite exchange | **1.996 h per 0.001 C_D0** | `empennage_trade` §0: 1.97 | +1.3% |
| L/D at loiter | **26.94** | report §2: 27.1 [1] | −0.6% |
| Induced share of C_D at loiter | **55.47%** | tasking: 55.5% | ✓ |

[CALC] The simulator is a faithful reproduction of the report's model and is used only for **relative** deltas, scaled onto the report's headline 112.8 h.

**One correction to the tasking's own arithmetic, applied everywhere below.** The tasking's e-ladder (+1.8 / +3.0 / +4.1 / +5.7 / +7.1 h at e = 0.88 / 0.90 / 0.92 / 0.95 / 0.98) reproduces on the committed simulator as **+1.72 / +2.83 / +3.91 / +5.49 / +7.00 h** — within 0.21 h everywhere, so the ladder itself is sound. What is **not** sound is the implicit assumption that any point on that ladder is reachable. §4.2 shows the ceiling is e = 0.866.

---

## 1. Answer first

**Four findings, in descending order of how much endurance they are worth.**

### Finding 1 — the two unresolved defects are worth −60 h, and every configuration hypothesis in this study is noise beside them

The wing holds **~50 L usable against 120 L required**, and at the report's own mass budget the aircraft **does not balance** — the dry CG lands 0.47–0.67 m aft of the 42% MAC target, which is 107–153% MAC against a 35.3 mm window [AN, from two independent mass build-ups, and independently again in `empennage_trade` §8 finding 8; the 35.3 mm window is [CALC] from the committed geometry]. On the committed simulator, an aircraft carrying only what the wing can actually hold flies:

| Aircraft | Fuel | MTOW | Endurance |
|---|---|---|---|
| **A — paper, as written** (120 L at the report's implied 0.8458 kg/L) | 101.5 kg | 250.0 kg | **112.98 h** |
| **B — buildable today**, wing tanks only, Jet-A at 0.804 kg/L | 40.2 kg | 188.7 kg | **53.35 h** |
| **B′ — same on mogas** at 0.745 kg/L | 37.2 kg | 185.8 kg | **49.91 h** |

[CALC] **The gap is −59.6 h.** Deleting both booms is worth +7.3 h [3, verifier-corrected]. The best riblet case is +1.25 h [4]. The entire spanload lever is +0.93 h (§4.2). **The volume-and-balance gap is eight times the whole drag-and-structure optimisation programme combined, and it is the only number in this study that decides whether the mission is a record or a re-statement of what ScanEagle-class platforms already do.**

A second, smaller instance of the same error class: **the report's fuel density does not exist.** 101.5 kg in 120 L implies 0.8458 kg/L. Mogas E10 is 0.745, Jet-A1 typically 0.804, Jet-A1 *maximum spec* 0.840. The requirement is therefore **126.2 L (Jet-A1) to 136.2 L (mogas)**, not 120 L. Every volume-closure claim in this repository is stated against a target that is 5–14% too small.

### Finding 2 — the sponsor's driving insight is correct and its payoff is already banked

Induced drag *is* 55.5% of the total, and the programme *has* been optimising the smaller half. But the induced half is not sitting there waiting. `docs/decisions/2026-08-20-span-efficiency-finding.md` contains a committed AVL run on this exact planform at the as-designed −3° twist returning **inviscid span efficiency e_inv = 0.9786** [5]. Decomposing the lumped Oswald factor as 1/e = 1/e_inv + k gives a viscous lift-dependent term **k = 0.15460**, and then:

- **Perfect elliptic loading** (e_inv → 1.0000) gives lumped **e = 0.8661**, i.e. **Δe = +0.0161, worth +0.93 h gross**. That is the *absolute ceiling* on every spanload, twist, taper and planar tip-shape change available on this aircraft, taken together, with no mass and no wetted area. [CALC]
- **e = 0.90** would require the viscous lift-dependent term to fall **28%** even at perfect elliptic loading; **e = 0.95** requires a **66%** cut; **e = 0.98** requires **87%**. Those are not spanload numbers. They are section-drag and surface-finish numbers.
- The AVL twist sweep in the same record [5] puts the optimum near the as-designed value: e_inv 0.9804 at 0°, **0.9786 at −3°**, 0.9673 at −5°, 0.8932 at −11°. `wing.twist_tip_deg = −3.0` is tagged `assumption` in the design file and it is, by accident, within **0.2% of optimal**.

**So: compute the spanload, yes — but to close the question, not to harvest it.** The recoverable induced-drag deficit is viscous, and the open band on the lumped e (0.77 to 0.85, worth **−5.6 h**, per the same decision record) is six times larger than the entire spanload lever. **No tip-device or spanload decision is resolvable before that band is closed.**

### Finding 3 — the tailless is a NO, and the number that kills it is the CG station, not the drag

Full arithmetic in §3. In one line: at 25° of quarter-chord sweep the wing-alone neutral point is **8.6% MAC** [AVL, refuter-verified], the 3.4 × 0.48 m pod drags it forward **7–9% MAC**, so the aircraft neutral point lands **on the MAC leading edge** and the CG must sit at **−5% to −10% MAC — 22 to 44 mm ahead of the leading edge of the mean aerodynamic chord**, against a swept integral-tank centroid at **49.1% MAC** and 19.9% MAC of fuel-burn CG travel into a 5–8% MAC window. **Corrected net endurance: −9 h, band −19 to +2 h.**

### Finding 4 — one thing in this study is unambiguously worth doing, it costs €0, and it expires

**Specify a 125 mm/side raked wing tip before the wing plug is cut.** +2.1 h for +0.54 kg, ΔC_D0 −0.00016, CG-neutral, structurally free inside the wing's existing 17.9% root-bending margin. If it is specified **after** tooling it needs its own mould pair and a structural bonded joint: **€800–1,500 and 30–50 h instead of €0 and ~0 h**, a factor of roughly 1,000 on the cost of the single best item in this study. It belongs on the same month-3-to-5 tooling gate as the premortem's tripwire #1. And it should be honestly labelled: **88% of the credit is aspect ratio and area, not tip treatment** — it is the first 125 mm of a span extension, and it pays for exactly that reason.

---

## 2. The comparison table

All Δ are against the report's published baseline (**112.98 h** on the committed simulator, 112.8 h as published), C_D0 = 0.020, e = 0.85, C_Lmax = 1.6, twin booms and inverted-V as drawn.

**Δh figures are the adversarially-corrected values, not the original analyses' claims.** Every one of the six deep analyses was refuted; §2.3 lists what changed and by how much.

### 2.1 Ranked

| # | Hypothesis | ΔC_D0 | Δe | Δ mass | **Net Δ endurance** | Killer problems |
|---|---|---|---|---|---|---|
| **1** | **Raked wing tip, 125 mm/side** (b 9.2628 → 9.5128, S 3.900 → 3.965, AR 22.0 → 22.82) | **−0.00016** | 0 (span enters via AR) | **+0.54 kg** | **+2.1 h** (band +1.5 … +2.3) | It is not a tip device: **+1.81 h is aspect ratio and +0.75 h is area**, only the remainder is tip treatment — so the obvious follow-up (why stop at 125 mm?) is unasked. The −0.00016 is *reference-area bookkeeping*, not drag reduction: total non-wing drag in newtons is unchanged. The claimed +1.3 L of wing volume is **0 L usable** — it lies outside the 80%-of-span tankage. Δe is held at 0; a constant-chord extension on a taper-0.45 wing makes the spanload *less* elliptic, and at Δe = −0.005 the number falls to +1.78 h. **Expires at the tooling gate.** |
| **2** | **Inverted-V dihedral 42° → 32.5°**, holding S_h,eff = 0.310 m² (falls out of hypothesis 3's own argument) | −0.00044 | 0 | **−0.49 kg** | **+1.6 h** | The endurance is real; **the stability case for it is not made.** S_v,eff halves (0.2513 → 0.1258 m²), so on the analysis's own build-up Cn_β = **+0.029/rad, not the claimed +0.040** — a 38% error in the number that decides whether it is safe. ω_n 1.65 rad/s, period 3.8 s. No Cl_β was computed: with 3° dihedral on AR 22, \|Cl_β/Cn_β\| goes from ~1.4 to ~3, the Dutch-roll-deficient quadrant. Retained yaw control is 117 N·m, not the stated 155. |
| **3** | **Hoerner / shaped tip cap** (tip shape only, no span change) | 0 | **+0.0025 … +0.0075** | +0.10 kg | **+0.15 h** (band −0.05 … +0.5) | **The credit has no datum.** Nothing in the repository defines a tip geometry — `argus7/design/geometry.py` lofts root and tip chords with no tip treatment and `argus7/aero/buildup.py` integrates the section arc length with no tip term. A Hoerner credit is by construction a credit *relative to a square-cut tip*; if e = 0.85 was picked as generic sailplane practice, sailplane practice already has shaped tips and the credit is **exactly 0**. The 0.10 kg charge (−0.15 h) is **half the benefit**, and nobody has weighed it. |
| **4** | **Winglet, 0.6 m/side** | +0.00069 | +0.072 (e 0.85 → 0.922 at 80% realisation of Raymer's 1.9h/b) | +1.3 … +2.5 kg | **+0.5 h at 1.3 kg → −1.3 h at 2.5 kg** (the refuter's own model gives −1.64 h at 2.5 kg; both are decisively negative) | **The sign is decided by an unweighed mass estimate.** 0.143 m² of cantilevered load-carrying fin at the report's own 8.33 kg/m² with nothing booked for tip rib, hardpoint, skin doubler or bond; sign flips at ~1.6 kg. Mean chord 0.119 m gives **Re = 1.85 × 10⁵**, where a plain symmetric section runs a laminar separation bubble across the whole C_y range a winglet must carry. Needs its own mould pair, tip hardpoint, alignment jig and a PSU 90-125WL-class section the programme has not budgeted: **€1,500–3,000 and 60–100 h**. On a belly-recovered airframe it is a 0.6 m lever arm into a 0.26 m-chord outboard box, ~100–200 times. |
| **5** | **Wingtip drag rudders replacing the fin's stability function** | +0.00095 | −0.006 | **+2.8 kg** | **−6.4 h** | **The hardware deletes nothing** — the ailerons stay, the ruddervator actuation stays, and the fin's vertical share is only 0.70 kg against a +1.7 kg install. **The flat stabiliser "between the boom ends" violates the repository's own r = 0.45 m prohibition**: booms at ±0.6206 m means 0.90 m of a 1.24 m span sits inside it, which `empennage_trade` line 214 already ruled out at 0.44% strain. Cn_β goes to **−0.005/rad** — an *aperiodic directional divergence*, time to double 1.7–1.9 s, needing a ~1 Hz inner loop held for 122 unbroken hours. A 5° bias on both sides is 14.6 N = **16% of the aircraft's entire 90.7 N of drag**. |
| **6** | **Tailless / flying wing** (25° sweep, tip fins, elevons only) | −0.0015 | −0.042 (e → 0.808) | +2.55 kg | **−9 h** (band −19 … +2) | **CG must sit ahead of the wing's own leading edge** (§3). C_Lmax 1.616 → **1.35** (band 1.23–1.46), and C_Lmax is what buys slow flight. **6.0% MAC per g of regenerative aeroelastic pitch-up** on a wing already deflecting 174 mm at 1 g — the report's own 12 m/s gust case (n = 2.10) eats the entire design margin, and no tool in the repository can close it. Fuel-burn CG travel 19.9% MAC into a 5–8% MAC window. **It breaks the only flight phase that currently closes** (§3.4). |
| **7** | **Move the wing aft ~0.9 m and put the fuel in the fuselage** (balance + volume as one fix) | +0.0009 | 0 | **+10.5 kg** | **−17.9 h vs A** / **+42 h vs B** | Not an optimisation — a **feasibility fix**, and it should never be quoted against baseline A alone. The required station is **x_le_frac 0.40–0.53** and is *unknowable* until an equipment layout exists: ±100 mm of dry-CG uncertainty moves it 144 mm = 33% MAC. Fuel closure is asserted, not demonstrated (125 L usable claimed against 120.8 L required, on a fuel density that does not exist and a 94% bay packing fraction that is not achievable). Bladder mass contradicts `materials_pack` §10's own 5.0–6.5 kg line. |
| **8** | **Prandtl / Bowers bell spanload** | +0.0030 | **−0.158** (lumped e → 0.692) | −0.95 kg | **−18.6 h** | e_span is **0.750 exactly** by construction (A₃/A₁ = −1/3), i.e. **+33.3% induced drag at fixed span**. Local c_l peak rises to 1.301 × C_L, so **C_Lmax 1.60 → 1.31**. The root then runs c_l 1.49–1.57 (above the FX 63-137's 0.5–1.2 low-drag bucket) while everything outboard of η = 0.72 runs below c_l 0.5. It needs **−17.6° of nonlinear tip washout**, not the −8 to −10° assumed, which means a CNC-machined plug or fully twisted female moulds. **And the requirement does not exist:** `research/design_pack.md` never calls for a bell spanload; the call is in `docs/report_outline.md`, an outline of the report, for an aircraft the design file's own provenance block says is a different one. |
| **9** | **Fuselage saddle tank + parasol wing** | +0.0002 (saddle) … +0.0011 (parasol) | 0 | +6.0 … +10.5 kg | **−37.9 h vs A** / **+25 h vs B′** | Same problem as #7, solved worse. **The parasol is unnecessary**: the spar carry-through box plus rear shear web is 5.7 L of a 119.2 L bay — **4.8%** — so a mid-wing saddle around it delivers 85.1 L against the parasol's 87 L, for +0.0002 instead of +0.00112 C_D0 and no pylon. The recommended 65 L saddle is **asserted against the study's own volume budget**, which derives 154.6 L of bay against 147 L of non-fuel demand — a **7.6 L residual**. Fuel density (Jet-A 0.804) and BSFC (270 g/kWh, a mogas spark-ignition number) are taken from **different engines**. |

### 2.2 The same table as a ledger

Each row decomposes the net into single-effect terms at the local exchange rates (1.996 h per 0.001 C_D0, 1.516 h/kg). **The "net" column is the committed simulator's answer for the full input vector, not the sum of the terms** — the terms are linearised and the residual column carries the interaction. Where the residual is large, the linearised ledger is misleading and only the simulator result should be quoted.

| # | Hypothesis | Δ drag h | Δ mass h | Δ e h | Δ C_Lmax h | Δ other h | Residual | **Net Δh (sim)** | Band |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Raked tip 125 mm/side | +0.32 | −0.82 | +2.56 (AR + area) | 0 | 0 | 0.00 | **+2.06** | +1.5 … +2.3 |
| 2 | Tail dihedral 42° → 32.5° | +0.89 | +0.74 | 0 | 0 | 0 | 0.00 | **+1.63** | +1.2 … +1.9 |
| 3 | Hoerner tip cap | 0 | −0.15 | +0.30 | 0 | 0 | 0.00 | **+0.15** | −0.05 … +0.5 |
| 4 | Winglet 0.6 m (at 1.3 kg) | −1.38 | −1.97 | +3.95 | 0 | 0 | −0.06 | **+0.54** | +0.7 … −1.6 |
| 5 | Drag rudders replacing the fin | −1.90 | −4.24 | −0.35 | 0 | 0 | +0.14 | **−6.35** | −2.1 … −11 |
| 6 | Tailless | +3.00 | −3.87 | −2.53 | **−7.06** | 0 | +1.06 | **−9.40** | −19 … +2 |
| 7 | Wing aft + fuselage fuel | −1.80 | −15.92 | 0 | 0 | −1.07 (prop wake) | +0.93 | **−17.86** | −11.6 … −25.8 |
| 8 | Bell spanload | −5.99 | +1.44 | −10.28 | **−8.55** | 0 | +4.8 | **−18.6** | −17 … −22 |
| 9 | Saddle tank as specified | — | — | — | — | — | — | **−37.9** | −17.5 … −58.6 |

**Two rows need their footnotes read.**

- **Row 8.** The linearised ledger sums to −23.4 h and the drop-in simulator call with those same four inputs returns **−21.1 h**; the **−18.6 h** quoted is the refuter's *self-consistent rebuild* of the polar (component C_D0 plus spanwise-integrated section drag plus C_L²/πARe_span, rather than a lumped-e shortcut applied on top of a section-drag adder that partly double-counts it). The 4.8 h residual is that double count. **The sign and the order of magnitude are not in dispute at any point in that range.**
- **Row 9.** Not a delta on baseline A at all: the saddle-tank configuration changes the fuel *state* (85 L of mogas, 63.3 kg, MTOW 217.8 kg), so no drag/mass decomposition against a 101.5 kg-fuel baseline is meaningful. Quoted as an absolute: **75.1 h**. Against baseline B′ (§5, same mogas fuel) it is **+25 h**.

**The spread from best to worst is 40 h, and 38 h of it is one item — fuel.** As in `empennage_trade` §2.1, the configuration is not where this aircraft's endurance lives. Unlike the empennage question, though, the configuration question does contain a genuine kill: hypotheses 7 and 9 are the *same* problem, and until it is solved every other number on this table is being computed for an aircraft that cannot fly.

### 2.3 What the adversarial pass changed

| Hypothesis | Claimed | Analysed | **Refuter-corrected** | The error that moved it |
|---|---|---|---|---|
| **Tip devices** | +1.5 h (Hoerner) | +0.84 h | **+0.15 h** | The measured 1–3% tip-shape band comes from AR 6–10 wings with c_tip/b = 0.067–0.125. Here **c_tip/b = 0.02821**, 2.4–4.4× smaller. Since δb_eff/b = 2k·c_tip/b, the same physical k gives **0.34–1.01%**, not 1–3%. ~3× optimistic. The analysis also decomposed e with an invented e_inv ≈ 0.95 when the repository already holds a committed AVL measurement of **0.9786**; its claimed e = 0.867 back-solves to e_inv = 1.0012, i.e. better than elliptic on a planar wing. |
| **Winglets** | −0.3 h (net negative) | **+1.81 h** (net positive) | **+0.5 h at 1.3 kg, negative above ~1.6 kg** | The analysis flipped the sign using an unvalidated Trefftz e-ratio of 1.1614 (3.4% above Raymer, 2.8% above Kroo) **and** a 1.30 kg pair with zero booked for tip rib, hardpoint, doubler and bond. Two optimistic inputs pushing the same way. The original hypothesis's negative sign was probably right — but it got there by taking the aero credit at a hypothetical 12 m span and the penalties at 9.26 m. |
| **Tailless** | −5.0 h | −2.4 h | **−9 h** | The −2.4 h **does not reproduce from its own declared deltas**: feeding ΔC_D0 −0.0019, Δe −0.05, Δm −3.5 kg into the committed simulator returns **+6.11 h**. The sign came entirely from an *undeclared fourth delta*, C_Lmax 1.616 → 1.278, worth −8.8 h — and that C_Lmax is not reproducible by the stated AVL strip method (which returns 1.544). Separately the mass ledger books −3.45 kg while declaring an unclosable 6% MAC/g pitch-up whose fix is +4 to +11 kg of **spar cap**, not the +2.5 kg of torsion box the ledger charges. |
| **Drag rudders** | +2.2 h | −2.2 h | **−6.4 h** | The only positive term — a flat 0.310 m² stabiliser between the boom ends, credited +3.16 h — **violates the repository's own propwash prohibition**, which `empennage_trade` line 214 had already ruled on for that exact geometry. Surviving in raised form it costs pylons, mass and a new 65–90 Hz resonator: the tail term is **−2.2 h, not +3.16 h**. A 5.4 h swing. |
| **Wing station** | +51 h (vs a strawman baseline) | −8.8 h | **−17.9 h** | Understated ~2× on inputs: bladder mass contradicts `materials_pack` §10's own 5.0–6.5 kg figure while taking the 3.0 kg credit from the same line; joint and bay structure understated 1.5–3.5 kg at an **+87% rise** in the mass reacted through the wing joint; the prop-wake charge asserted at −0.5 pt and converted at 1.07 h/pt while the report's own register says 2.4 h/pt. Its Monte Carlo "P(x_le_frac ≤ 0.40) = 0.00%" is a probability over the analyst's own station priors, and `empennage_trade` finding 8 — cited by the analysis *as corroboration* — computes 0.365–0.456, which excludes the analysis's own median. |
| **Saddle tank** | +46.8 h (vs buildable) | −11.8 h | **−37.9 h** | The 65 L saddle is asserted against the study's own derived **7.6 L residual**; fuel density and BSFC are taken from different engines (Jet-A 0.804 with a mogas 270 g/kWh); the headline is the best corner of a 2 × 2 grid. Self-consistent: mogas 0.745 + 270 g/kWh = 95.46 h; Jet-A 0.804 + 330 g/kWh = 82.78 h. |
| **Bell spanload** | −17.7 h | −16.1 h | **−18.6 h** | The −16.1 h **does not reproduce from its own inputs**: fed e 0.6924, C_D0 0.023, C_Lmax 1.3068, −0.95 kg the simulator returns **−21.0 h**. The gap is the C_Lmax term, assigned −2.3 h where the correct value is −7.2 h — three times wrong, and flatly inconsistent with `materials_pack`'s own −0.20 → −5.4 h sensitivity that the analysis claimed to reproduce. |

**Two patterns are worth naming, because they will recur.**

1. **Four of the six headline numbers did not reproduce from the deltas their own authors reported.** In three cases the discrepancy was a *hidden* term (an undeclared C_Lmax change, a mis-scaled C_Lmax conversion, an unpriced structural fix). This pack's ranked table therefore quotes only numbers this pack has re-run end-to-end on the committed simulator, not summed from linearised deltas.
2. **Every one of the six chose the flattering baseline at least once.** Hypotheses 7 and 9 quoted +51 h and +46.8 h against a wing-tanks-only aircraft; hypotheses 1 and 4 quoted tip-device credits against an undefined datum tip. §5 states both baselines explicitly, every time.

---

## 3. The sponsor's question, part (a): can the booms come off and the aircraft fly as a tailless?

### **No.**

Not because of drag — the drag ledger is close to neutral — but because **there is no CG station that works**, and the number that says so is this:

> **At 25° of quarter-chord sweep the aircraft's neutral point lands on the MAC leading edge, so the centre of gravity must sit at −5% to −10% MAC — 22 to 44 mm AHEAD of the leading edge of the mean aerodynamic chord — while the swept wing's integral-tank centroid is at +49.1% MAC and the 40.6% fuel fraction moves the CG 19.9% MAC across the burn, into a usable window of 5–8% MAC.**

That is a factor of **2.5 to 4** on the binding tolerance, on an aircraft where the failure mode is not a diversion but a hull loss at hour 60 of an unattended 113-hour flight.

### 3.1 What the tailless actually buys, stated fairly

The credit is large and should not be dismissed. Deleting the boom system (installed 9.44 kg per `boom_construction_pack` §14) plus the inverted-V panels, two ruddervator actuators, tail root fittings and boom control runs — **−12.52 kg and −0.00337 C_D0** — is worth **+28.3 h** on the committed simulator (the analysis and its refuter both quote +29.0 h from their own re-implementations; the 0.7 h difference is inside the model-reproduction noise and does not matter here) [CALC]. That is by far the largest positive number anywhere in this study.

It is then spent, and over-spent:

| Term | Δh |
|---|---|
| Delete booms + inverted-V (−12.52 kg, −0.00337 C_D0) | **+28.3** |
| Tip fins, 0.49 m² at l_v 1.41 m (and they are undersized: V_v = 0.019 against the baseline's 0.0223) | −8.9 |
| Sweep structure: spar span ×1/cos25, kinked-spar centre fitting, torsion box | −6.9 |
| Tip-mass flutter / mass-balance allowance | −2.0 |
| Segmented elevons (now primary pitch **and** roll for 122 unattended hours) | −1.8 |
| Bending-stiffness fix for the aeroelastic pitch-up (§3.3), **low end only** | −6.1 |
| Fuel relocation to the pod (+2.0 kg), which the analysis computed and then excluded | −3.0 |
| Span-efficiency loss, e 0.85 → 0.808 | −2.5 |
| **C_Lmax 1.616 → 1.35** | **−7.2** |
| Interaction residual (the terms above are linearised; the net is the simulator's answer for the full input vector: C_D0 0.0185, e 0.808, C_Lmax 1.35, +2.55 kg) | +0.7 |
| **Net** | **−9.4** |

[CALC] Band **−19 h** (central +6 kg of stiffening, C_Lmax 1.30) to **+2 h** (C_Lmax 1.46, e 0.84, the analysis's own mass ledger at face value). **The honest reading is a 20-hour-wide coin flip whose centre is negative and whose downside is not bounded by anything the repository can compute.**

### 3.2 Trim drag: it cannot fund this, and the number is small in both directions

On the **baseline**, the wing-body pitching moment about the CG at 42% MAC is Cm = Cm_ac + C_L(0.42 − 0.227) = −0.20 + 0.2335 = **+0.0335**, so the tail carries **+9.4 N of upload on a 2,452 N aircraft — 0.38% of weight, worth about +0.2 h** [AN — AVL plus XFOIL on `data/airfoils/fx63137.dat` at Re 0.6 M; the 2,452 N is 250 × 9.80665 and checks here]. The original hypothesis's +18 N is the right order and the conclusion is identical either way: **there is no trim-drag saving to be had by deleting the tail, because the tail is already almost unloaded.**

Going the other way, the tailless must trim on **something**, and this is where the section choice dies:

- **An unswept wing generates Cm0 = 0 from twist at every twist angle** [AN]. So an unswept tailless must trim on reflex or on elevon deflection alone.
- **Elevon-only trim** needs Cm = SM·C_L + \|Cm_ac\|. XFOIL on the repository's own FX 63-137 coordinates at Re 0.6 M gives **Cm_ac = −0.20** (worse than the −0.17 assumed). At SM 10% that is **+0.261**, and with Cm_δ = −0.0109/deg swept or −0.0040/deg unswept, that is **24° or 65° of up-elevon**. Both are separated. Dead.
- **Therefore the wing must be swept and must trim on washout.** AVL Cm0-versus-twist, solved at the trim condition: 25° sweep at SM 10% needs **−10.5° of washout**; SM 5% needs −8.6°; 30° needs −8.1°; 35° needs −6.3°.

### 3.3 The four numbers that decide it

**(a) Static margin and the neutral point.** AVL wing-alone NP, measured from the MAC leading edge, **using the refuter's values** [AN] — the refuter's AVL setup reproduced the analysis's unswept baseline exactly, which is what makes the two comparable, and its swept values then sit 1.0–1.7% MAC aft of the analysis's; the more conservative reading is used here:

| Quarter-chord sweep | 0° | 20° | 25° | 30° | 35° |
|---|---|---|---|---|---|
| Wing-alone NP (% MAC) | 22.6 | 11.7 | **8.6** | 4.7 | −1.0 |

The 3.4 × 0.48 m pod contributes a **forward** shift of **7.3% MAC by Multhopp and 8.2% by Munk** on the lofted 0.4105 m³ volume — 7–9%, **not** the 10–15% the hypothesis assumed. The chin gimbal is about −1.5% and the pusher-prop normal force about +1.5%, which cancel. **Net aircraft NP at 25° sweep ≈ 0% MAC**, i.e. on the leading edge of the mean aerodynamic chord. At SM 5–10% the CG must be at **−5% to −10% MAC**. The MAC is 0.4412 m, so that is **22–44 mm ahead of the MAC LE at x = 0.7833 m**, on an aircraft whose engine is at x ≈ 3.0 m.

**(b) The CG window and the fuel.** The usable window between an aft limit at SM 5% and a forward limit set by elevon trim authority is **5–8% MAC**, against the baseline's 8%. The swept wing's integral tank centroid (η 0.15–0.80, volume-weighted at 45% chord) computes to **38.7% MAC → 217 mm → 49.1% MAC aft of the required CG**. At a 40.6% fuel fraction, all-fuel-in-the-wing gives **19.9% MAC of CG travel**. Holding travel to 3% MAC demands the fuel centroid stay within **32.6 mm** of the empty CG for the entire burn — sequenced transfer under a CG computer, where a transfer fault at hour 60 of an unattended flight is a loss of aircraft. **The baseline's equivalent tolerance is 87 mm and its unswept tank centroid is 3.2% MAC from the CG.** The tailless makes the repository's one unresolved constraint **2.7× tighter** — and it does not solve it either: 70–85 L still has to go in the pod, in the same volume as the payload bay and the spar carry-through.

**(c) C_Lmax, and the asymmetry that makes it decisive.** Keeping the FX 63-137 unchanged (section c_lmax 1.70), AVL strip loading gives wing C_Lmax **1.616 unswept** — which reproduces the report's stated 1.6 from measured section data and validates the method — and, at 25° sweep with the −10.5° trim washout, **1.544 by the same method**, **1.23 with a cos²Λ normal-flow correction, ~1.46 with cosΛ**. Centre **1.35**. Worth **−7.2 h**.

This is the lever the tailless walks down the wrong side of. Endurance at fixed C_D0 is bought with *slow* flight, and C_Lmax is what buys slow flight. The lever is sharply asymmetric: **raising C_Lmax is worth about +1 h before the FX 63-137's viscous drag rise takes it back; lowering it by 0.29 costs −7.2 h.** Note the perversity — **L/D at the tailless loiter point is 27.7 against the baseline's 26.9.** The aircraft is marginally *more* efficient and still loses.

The reflex-section branch is worse, not better: a reflexed section (c_lmax 1.10–1.30, Cm_ac ≈ −0.02) needs less washout but scales C_Lmax to 0.98–1.16. **There is no section choice that escapes.**

**(d) Aeroelastic trim — the one that cannot be closed at all.** `materials_pack` §2.3 gives 174 mm of tip deflection and 4.9° of tip slope at 1 g. On a swept wing the streamwise incidence change from bending is dα = −(dw/dy)·sin Λ = **−2.07°/g** at 25°. With AVL's dCm0/dtwist = +0.0281/deg at that sweep, each additional g adds **Cm0 = +0.058, equivalent to moving the CG 6.0% MAC aft** — against a design margin of 5–10%, in a **regenerative** direction (up-bend → nose-up → more α → more bend). **The report's own gust case (12 m/s sharp-edged, Δn = 1.10, n = 2.10) consumes the entire margin.** This mechanism does not exist on the unswept baseline, and AVL is rigid — nothing in this repository can close it. Fixing it means bending stiffness, not torsional: **+4 to +11 kg of spar cap on a 32.5 kg wing**, i.e. **−6 to −17 h** that no version of this ledger has ever carried.

And a build-tolerance corollary: at +0.0281 Cm0/deg, **±1° of as-built twist error = ±2.6% MAC of static margin**, against a 5–8% window. A −10.5° nonlinear washout distribution would have to be held to about **±0.4° over 4.63 m of bonded semi-span** through layup, cure and springback. On a tailed aircraft you check the tail with a tape and shim its incidence between flights; here the first flight *is* the stability test and the only adjustment is a new mould.

### 3.4 The thing that ends the argument

**The tailless breaks the only flight phase that currently closes.**

The programme's established propulsion correction is that the 0.813 m prop at 2,100 rpm can absorb only about **4.66 kW**; climb and takeoff do not close, loiter is fine. Loiter shaft power at MTOW, on the committed simulator's own operating point:

| Configuration | Loiter C_L | V (m/s) | Shaft power (kW) |
|---|---|---|---|
| Baseline | 1.210 | 35.62 | **4.53** |
| Tailless, C_Lmax 1.35 | 1.021 | 38.78 | **4.79** |
| Tailless, C_Lmax 1.278 | 0.966 | 39.85 | **4.87** |

[CALC] The baseline clears the established ceiling by ~3%. **Every tailless variant is over it at the heavy end.** The configuration does not merely fail to buy endurance; it converts the one phase that closes into one that does not.

> **§3.5 — Disagreement 1, and it is against the tasking's own established correction.** The ~4.66 kW ceiling is a **sea-level** number. At the loiter density ρ = 0.81913 kg/m³ the same C_P = 0.25 ceiling at 2,100 rpm and D = 0.813 m gives **P = 0.25 · ρ · n³ · D⁵ = 3.12 kW** — *below* the baseline's own 4.53 kW loiter demand. Either the C_P ceiling is not advance-ratio-independent (it is not; at J = 1.25 a properly pitched blade absorbs considerably more than a static C_P limit suggests), or **loiter does not close either**. This is flagged rather than asserted, and it **must not be used to discriminate between configurations** — it applies identically to all of them, including the baseline. But the table above compares power at a *fixed* density, so the *relative* finding stands: the tailless needs 6–8% more shaft power at loiter than the baseline, at the same altitude, forever.

### 3.5 What to do instead

The empennage credit the tailless is chasing is genuinely available, and `empennage_trade` §3 already holds it open: **the boomless-fuselage-tail (configuration 3) returns +7.3 h (verifier-corrected; +8.2 h by that pack's own recompute)**, captures essentially the same drag and mass credit, and **touches neither C_Lmax nor the CG window nor pitch damping nor the aeroelastic trim path**. It has its own four unpriced costs — a 2.005 m arm that is the minimum defensible prop standoff, 37% less pitch and yaw damping, a tail root sharing 0.5 m of tailcone with the belt drive and exhaust, and a propeller that becomes a life-limited article — but they are ordinary engineering costs, not unclosable ones.

**Tailless is roughly 16 hours worse than the best conventional option on the table, and it buys that deficit with three new risks nobody in this programme can retire.**

**One correction to the framing, in the sponsor's favour and against the hypothesis:** the tailless does **not** attack induced drag. It makes lumped e *worse* (0.85 → 0.808) and cuts the induced *fraction* from 55.5% to 47.9% only by flying faster and paying more total power. The e lever the sponsor is right to chase is real, but it is a wing-and-section question, not an empennage question.

---

## 4. The sponsor's question, part (b): wingtips and spanload — what is actually available

### 4.1 The honest headline

**Real winglets buy a few percent of induced drag, not tens of percent. Tip *shaping* on this aircraft buys well under one percent. And the entire spanload lever — every tip device, every twist distribution, every taper change, taken together and perfectly executed — is capped at +0.93 h, which is 0.8% of the mission.**

### 4.2 Why: the ceiling, computed

> **Disagreement 2 — with the report's own e-sensitivity table.** The report's ladder (e → 0.90, → 0.95, → 0.98) is arithmetically correct and **aerodynamically unreachable**, and this pack says so.

The lumped Oswald factor decomposes as **1/e = 1/e_inv + k**, where e_inv is inviscid span efficiency (a spanload property) and k is the viscous lift-dependent term (a section and surface property). The repository holds a committed AVL measurement of e_inv for this exact planform at the as-designed twist [5]:

- e_inv = **0.9786** → k = 1/0.85 − 1/0.9786 = **0.15460**

| Target lumped e | Required k at e_inv 0.9786 | Cut in viscous term | Required k at **perfect elliptic** | Cut at perfect elliptic |
|---|---|---|---|---|
| 0.8661 (**ceiling from spanload alone**) | 0.15460 | **0%** | 0.15460 | 0% |
| 0.88 | 0.11450 | 26% | 0.13636 | 12% |
| 0.90 | 0.08924 | 42% | 0.11111 | **28%** |
| 0.92 | 0.06509 | 58% | 0.08696 | 44% |
| 0.95 | 0.03076 | 80% | 0.05263 | **66%** |
| 0.98 | −0.00146 | **impossible** | 0.02041 | 87% |

[CALC] **Read the "perfect elliptic" column.** Even if the spanload were made exactly elliptic at zero cost — no mass, no wetted area, no twist penalty — e reaches **0.8661** and stops. Every point on the report's ladder above that requires cutting the *viscous* lift-dependent drag: 28% for e = 0.90, 66% for e = 0.95. Those are surface-finish, transition-location and section-selection numbers. They are not spanload numbers, and no tip device touches them.

**+0.93 h gross, +0.78 h after a 0.1 kg tip cap.** That is the whole prize.

Three corollaries the sponsor should have in front of them:

1. **The twist is already right.** AVL's own sweep [5]: e_inv 0.9804 at 0°, **0.9786 at −3°** (as designed), 0.9673 at −5°, 0.9236 at −9°, 0.8932 at −11°. `wing.twist_tip_deg = −3.0` is tagged `assumption` and lands within **0.2% of optimal**. Compute it to close the question and to set stall progression and build tolerance — not to harvest endurance. Zero twist takes e_inv 0.9786 → 0.9804, i.e. lumped e 0.8500 → 0.8514, worth **+0.12 h** — and costs stall behaviour. [CALC]
2. **`design_pack`'s bell spanload is a category error, and it is not `design_pack`'s.** The bell minimises induced drag at **fixed root bending moment** — a structural-mass optimisation that permits a longer span. At **fixed span** the elliptical spanload maximises e, by definition. With the span frozen at 9.2628 m the correct target is elliptical, and the bell is **+33.3% induced drag** (e_span = 0.750 exactly, since sin³θ = (3 sin θ − sin 3θ)/4 gives A₃/A₁ = −1/3 and e = 1/(1 + 3·(1/3)²) = 0.75). Separately: **the requirement does not appear in `research/design_pack.md` at all.** The call for a bell spanload is in `docs/report_outline.md` and in a decision record, for the 200 kg AR-20 predecessor that the design file's own provenance block says "is a different aircraft, and none of v1.0's numbers come from it".
3. **Bell, priced properly: −18.6 h.** Lumped e falls to 0.692 (using the repository's own e_inv, 0.672 and −22 h), local c_l peak rises to 1.301 × C_L so **C_Lmax 1.60 → 1.31**, the root runs above and the outer 28% of span below the FX 63-137's low-drag bucket (+0.0030 C_D0), and it needs **−17.6° of *nonlinear* tip washout** (+0.6° wash-**in** at η 0.2, −4.7° at 0.6, −11.1° at 0.8, −17.6° at the tip). Linear washout cannot produce it at all. It returns **−0.95 kg of spar cap (+1.4 h)** at fixed span and a genuinely more benign outboard stall — and neither comes close.

### 4.3 What tip devices are actually worth here

Everything below is against the verified 9.2628 m span, on the committed simulator.

| Device | Mechanism, honestly stated | Δe | Δ mass | **Δh** |
|---|---|---|---|---|
| **Hoerner / shaped tip cap** | Effective-span credit of k·c_tip per side. **c_tip/b = 0.02821 here**, against 0.067–0.125 on the AR 6–10 wings the measured 1–3% credits come from; correctly transferred, the same physics gives **0.34–1.01%** of induced drag | +0.0025 … +0.0075 | +0.10 kg | **+0.15** (−0.05 … +0.5) |
| **Winglet, 0.6 m/side** | Raymer AR_eff = AR(1 + 1.9h/b) at h/b = 0.06477 gives ×1.1231; at 80% realisation, e_inv → 1.075 and lumped **e → 0.922**. **7.2 points of e = a 7.8% cut in induced drag = 4.3% of total drag.** That is at the *optimistic* edge of the 3–8% band real winglet retrofits deliver, and it is the number **before** mass, which is what decides the sign | +0.072 | +1.3 … +2.5 kg | **+0.5 → −1.3** |
| **Raked tip, 125 mm/side** | Not a tip device. b → 9.5128, S → 3.9653, AR → 22.82; ΔC_D0 = −0.00016 is reference-area dilution, not drag reduction | 0 | +0.54 kg | **+2.1** (+1.5 … +2.3) |

**The ranking is unambiguous and it is the one useful output of this whole line of enquiry: on this aircraft, planar span and area beat every non-planar device.** Against tip *shaping* the margin is ~14× (2.1 h against 0.15 h); against a 0.6 m *winglet* it is ~4× at the winglet's own best case and unbounded once the winglet's mass is realistic.

Three supporting facts, one of which contradicts the usual argument for span and should be stated because a reviewer who checks it may otherwise discard the correct conclusion with it:

- **At *equal root bending moment* the winglet beats the span extension** — Trefftz-plane solution gives −8.65% induced drag for an h = 0.30 m winglet against −7.77% for the bending-moment-matched +191 mm/side extension, a ratio of 1.11 rising to 1.18 at h = 1.0 m. That is the classical Kroo/Jones result and it holds here. **Planar span wins on this aircraft for three different reasons:** the extension *adds area* (which lowers loiter speed — worth +0.75 h of the +2.56 h on its own), the added area runs laminar to ~55% chord at Re 5.4 × 10⁵ and dilutes S_ref, and the winglet carries a fixed joint/hardpoint mass overhead that does not scale down.
- **The bending moment is free anyway.** The spar was sized to **16.18 kN·m** (uniform lift) while the realistic elliptic ultimate is **13.73 kN·m** — a **17.9% margin already banked** [both reproduce `materials_pack` §2.1 exactly]. A 0.6 m winglet raises root BM 6.6% and a 300 mm/side extension 6.5%; **both are inside it**. The original hypothesis's −2.9 h charge for "outboard torsional reinforcement" does not exist as a flight-load cost. Planar span stays free to about **b ≈ 10.9 m** at fixed area, or ΔL ≈ 0.9 m/side as an extension. *Caveat:* that is a gap between two **load models**, not a certified reserve, and it moves the moment a real spanload is run.
- **Tip devices are CG-neutral and volume-neutral**, which is the cleanest property in this trade space. The wing tip quarter-chord sits at x = 0.8942 m, **74 mm forward of the CG at 42% MAC** — so every tip mass is essentially at the CG station. A 0.10 kg Hoerner pair moves the CG **−0.0068% MAC**; a 1.30 kg winglet pair −0.022% MAC; a raked tip +0.013% MAC. All below the resolution of the mass budget. A winglet at x = 0.894 m is also **74 mm ahead of the CG and therefore very slightly *destabilising* in yaw** — the "free fin area" argument for winglets does not exist on a pusher with the tail 3.2 m aft.

### 4.4 What specifically should be done

**Do this:**

1. **Specify a 125 mm/side raked tip, before the wing plug is cut.** +2.1 h, +0.54 kg, €0 of incremental tooling if it is on the drawing at the tooling gate; **€800–1,500 and 30–50 h** if it is not. Make the tip a **thickened, radiused, sacrificial bonded cap**, for the reason in §4.5.
2. **Ask the follow-up the raked tip implies.** 88% of its credit is AR and area. The not-shortlisted hypothesis "take the span to the 12 m packaging limit and grow area with it" claims **+8.6 h** and is a strictly larger version of the same lever. It is unpriced here and should be run in Phase 2 (§7) — but note the trap in §4.5.
3. **Close `docs/decisions/2026-08-20-span-efficiency-finding.md` before spending anything else on tip devices.** Its open band on the lumped e (0.77–0.85) is worth **−5.6 h**. **A +0.15 h decision cannot be made inside a 5.6 h uncertainty.**

**Do not do this:**

4. **Do not build winglets.** Best case +0.5 h; sign flips at ~1.6 kg of pair mass; needs its own mould pair, tip hardpoint, alignment jig and a section designed for Re 1.85 × 10⁵ that nobody has budgeted; and at h/b = 0.065 on an AR-22 wing the span is already too long for the device to earn its wetted area.
5. **Do not book the Hoerner shape credit.** +0.15 h is inside the noise, its datum does not exist anywhere in the repository, and verifying it would need a flight-test drag polar resolved to ~1% in induced drag, which a €60k solo programme cannot buy. **You would be purchasing an unfalsifiable hour.** Shape the tip anyway — the closeout is a part the builder makes regardless — but do not put a number on it.
6. **Do not adopt the bell spanload.** −18.6 h, and the requirement is not real.

### 4.5 Two things every tip decision must carry

**The ground-strike case, corrected.** At 3° dihedral the tip chord plane sits at z = +0.2507 m over a 4.6314 m arm. Against the **fuselage keel** at z = −0.240 m, any recovery with more than **6.05°** of roll puts the wing tip down first. But the keel is not the lowest point: README states the inverted-V hangs 385 mm below it and "grounds first", and the sponsor has already ruled that acceptable by making the tail a serviceable item. **Against the true lowest point at z = −0.625 m the roll-to-tip-first angle is 10.71°, not 6.05°** — the analysis's headline number was **1.8× pessimistic** and in the alarming direction. The finding survives qualitatively: 10.7° is inside the ±5–15° canopy pendulum band that `empennage_trade` cites, and a parachute descent at 6 m/s with no attitude control will exceed it. **The wing tip is a repeated-impact article and this appears nowhere in the report, in `materials_pack` §8 fatigue, or in the recovery sizing.** A sharp-edged Hoerner corner is close to the worst shape you could put there; a 0.6 m winglet is a ×17 moment amplification against a 36 mm local section depth. **A raked/blended tip with a thickened, radiused lower corner is the only one of the three that survives that load path.**

**Span growth makes the fuel problem worse.** Wing internal volume scales as S²/b at fixed area, so going to 12 m takes gross volume **143 → 110 L** and usable ~50 → ~39 L against 120 L required: the shortfall grows from 70 L to **81 L**, i.e. from 59 kg to 68 kg of fuel that must be relocated to a fuselage bay already bisected by the mid-wing spar carry-through (`design/argus7_v1.yaml`, `wing.z_offset_m` note). **The "12 m span" that hypothesis 1 measures everything against is not a free baseline.** Tip devices are exactly volume-neutral; a raked extension adds **+1.42 L gross and 0 L usable**, because it lies outside the 80%-of-span tankage.

---

## 5. The baseline problem: which aircraft is being optimised

> **Disagreement 3 — with every endurance number published by this programme, including this pack's own table.**

Two baselines exist and they differ by **59.6 h**. Every hypothesis in §2 quoted whichever one flattered it. Both are stated here, and both are computed on the committed simulator.

| | Fuel | MTOW | Endurance |
|---|---|---|---|
| **A — paper, as written.** 120 L in the wing at 0.8458 kg/L | 101.5 kg | 250.0 | **112.98 h** |
| **B — buildable today.** Wing tanks only (~50 L usable), Jet-A1 0.804 | 40.2 kg | 188.7 | **53.35 h** |
| B′ — same, mogas 0.745 | 37.2 kg | 185.8 | **49.91 h** |

**Baseline A is not an aircraft. It is a spreadsheet with 70 L of fuel that has nowhere to live and a dry CG 0.47–0.67 m aft of where it needs to be.**

What the fix is worth, honestly, with the fuel in the fuselage and the wing moved aft to balance (+10.5 kg of tankage, bay structure, joint reinforcement and fuel system; +0.0009 C_D0 for junction, vents, fairing and access; −1.0 point of prop efficiency for halving the wing-TE-to-disc spacing from 4.7 to 2.1 root chords):

| Usable fuel volume | Jet-A1 (0.804) | mogas (0.745) |
|---|---|---|
| 50 L (wing only, no fix) | 53.35 h | 49.91 h |
| 85 L | 75.96 h | 71.39 h |
| 110 L | 93.07 h | 87.74 h |
| 125 L+ (MTOW-capped at 250 kg, 91 kg usable) | **95.12 h** | **95.12 h** |

[CALC] **Read the last row.** Once the fix is paid for, the aircraft is **mass-limited, not volume-limited**: at 250 kg MTOW and 159 kg of dry mass, only 91 kg of fuel fits regardless of how many litres the bay holds. **The ceiling on this configuration is 95 h, not 113 h**, and it does not move until dry mass comes down.

**Two consequences the sponsor should act on immediately.**

1. **Re-baseline every endurance claim in the programme.** Not onto B — B is a 250 kg-sized spar, parachute and airframe flown at 189 kg, which nobody would build; it is a *diagnostic of the gap*, not a design point. Re-baseline onto **the mass-and-volume-closed aircraft at 95 h**, and re-state the mission as **~4 days, not 4.7**, unless dry mass falls.
2. **Do not spend another euro on a tank or a mould until an equipment layout exists.** Hypotheses 7 and 9 are the same problem. Both fail on the same missing input: **nobody has stationed and volumed the 148.5 kg of dry mass**, so `wing.x_le_frac` cannot be solved for. Its correct entry today is not 0.22 and not 0.40 but **a flagged unknown in the range 0.365–0.53**, and *every static-margin figure in the report should carry the same flag.* A saddle tank is bay-specific hardware and the bay moves 0.6–0.9 m when the wing does.

---

## 6. Hypotheses generated but not shortlisted

Twenty-one hypotheses were generated; six were analysed in depth (§2) and every one of the six was adversarially refuted. **All twenty-one are listed here** — the six shortlisted ones marked as such, in their original wording — so nothing is silently dropped and the selection is auditable. **Claimed Δh is the generator's own first-order estimate and has NOT been through analysis or refutation** — on the evidence of §2.3, where every one of six headline claims moved and four did not reproduce from their own deltas, these should be read as *hypotheses ranked by claim*, not as results.

| Claimed Δh | Hypothesis | Disposition |
|---|---|---|
| **+51** | The wing is ~0.6 m too far forward: longitudinal balance and the 70 L fuel shortfall are one problem with one joint fix | **Shortlisted (§2 #7).** Refuted: −17.9 h against baseline A. Mechanism correct and the most important finding in the repository |
| **+46.8** | Fuel volume, not drag, is the binding configuration constraint: ~90 L fuselage saddle tank straddling the CG, wing raised to clear it | **Shortlisted (§2 #9).** Refuted: −37.9 h against A. Same problem as the above; parasol unnecessary |
| **+12.5** | Delete both booms: single stretched fuselage, aft pusher, V-tail (MQ-1/MQ-9 layout) | Not analysed here. **Overlaps `empennage_trade` config 3 (+7.3 h, verifier-corrected)** and is the strongest surviving empennage option. Should be run against that pack's arm–area–standoff loop before being believed |
| **+12** | The engine runs at 14–27% load for 113 h, where the assumed 270 g/kWh BSFC does not exist — buy the load fraction back with a variable-pitch prop | **Not a configuration item, and probably the largest un-analysed number in the programme.** The committed simulator's docstring flags exactly this ("a constant BSFC materially overstates endurance"). Propulsion workstream; escalate |
| **+10.7** | 20% of the fuel is burned to make electricity: fix the alternator path before touching aerodynamics | Not a configuration item. 500 W through a 0.75 alternator is 667 W of shaft power against a 4.53 kW loiter demand — **14.7% of shaft power**. Real, cheap, and orthogonal to everything in this pack. Escalate |
| **+10** | Delete both booms and the inverted-V: single dorsal fin-pylon carrying a T-tail over the pusher disc | Not analysed. Superseded by `empennage_trade` config 6 (pylon pusher, **−2.2 h**), which failed on simultaneous prop-tip clearance and modal separation |
| **+8.6** | Take the span to the 12 m packaging limit and grow area with it: S 3.9 → 4.6 m², b 9.263 → 12.0 m, AR 22 → 31, on high-modulus pultruded spar caps | **The largest credible aerodynamic item not analysed, and the natural extension of §2 #1.** Warnings: fixed-area span growth *deepens* the fuel shortfall (§4.5), the cap mass grows as k³ (strength) or k⁶ (deflection) once spar depth shrinks, and `materials_pack` §2.3 says the wing is already at the flexible end of anything flown. **Run it in Phase 2** |
| **+6.9** | The fuel-volume-compatible variant: S 5.2 m², b 12.0 m, AR 27.7 — trade 3.6 points of aspect ratio for 37% more wing tank volume | **Not analysed and it should have been.** It is the only hypothesis in the whole set that attacks the binding constraint *with* the aerodynamics rather than against it. Run it in Phase 2 alongside the above |
| **+3.5** | The loiter C_L is 36% below the endurance optimum, and the binding constraint is the FX 63-137's drag bucket, not the stall margin | Partially answered in §3.3: with XFOIL section data integrated spanwise the true viscous optimum is C_Lmax ~1.7–1.8 (loiter C_L 1.29–1.36), worth **only about +1.2 h**, and beyond C_Lmax 1.9 endurance *falls*. The +3.5 h is a constant-e parabolic-polar artefact |
| **+3.4** | e = 0.85 is an unmeasured assumption and `twist_tip_deg = −3.0` is tagged `assumption`: compute the spanload before optimising anything else | **Correct as a process instruction, wrong as an endurance claim.** §4.2: the ceiling from spanload alone is +0.93 h and the twist is already within 0.2% of optimal. Do it to close the question, not to harvest it |
| **+2.9** | Size the recovery system to recovery mass, not MTOW, and buy the abort case with a fuel dump valve | Not analysed. Genuinely orthogonal, plausible, and cheap. The 85 m² canopy and its ≥5×MTOW (12.3 kN) attach path are sized at 250 kg for a landing that happens at ~150 kg. Escalate to the recovery workstream |
| **+2.8** | Descend as you burn: at fixed C_L the power law is W^1.5/√ρ, so the whole loiter should sit at the bottom of the 3,000–4,500 m band | Not analysed. **Operations, not configuration, and free.** `mission.loiter_altitude_m` is tagged `report-§4` and §1 locks only the *band* — so this is a change of one number in a mission profile, not of the aircraft. Verify against the payload's own line-of-sight and coverage requirement before adopting |
| **+2.8** | Redraw the propeller operating map: 0.813 m at 2,100 rpm on a 2.3:1 belt is three mutually inconsistent numbers | Not analysed. **Confirmed as a real inconsistency by the established correction, and §3.5 above shows the ceiling is also density-dependent.** Propulsion workstream |
| **+2.2** | Wingtip drag rudders replace the fin's control function but cannot replace its stability function; nose-mounted verticals are wrong-signed | **Shortlisted (§2 #5).** Refuted: **−6.4 h** |
| **+1.6** | Spend recovered structural mass on span (the correct use of the bell spanload) rather than on fuel | Partially answered in §4.2: the bell's structural credit is **−0.95 kg at fixed span**, and under constant-stress cap sizing curvature is κ = 2σ/(E·h), *independent of spanload entirely* — so on a stiffness-critical wing the bell buys **zero** stiffness. The premise of this hypothesis is largely void |
| **+1.5** | Winglets lose to planar span everywhere in this trade space; a Hoerner/raked tip is the only tip device that pays | **Shortlisted (§2 #1, #3, #4).** Refuted: the ranking holds, the Hoerner credit is **+0.15 h** not +1.5 h, the winglet verdict was wrong-signed, and the item that actually pays is the **raked tip at +2.1 h** |
| **+0.4** | Stop trying to move e with twist and taper — they are already within 0.5% of optimal; the recoverable deficit is viscous, and e = 0.85 has never actually been computed | **Not shortlisted, and in hindsight that was the selection error of this study.** It is the *correct* answer to the sponsor's driving question and §4.2 is a longer version of it. It was passed over because +0.4 h reads like nothing — which is precisely the point it was making. **Its claimed +0.4 h is also right for the right reason** (the ceiling from spanload alone is +0.93 h gross, +0.78 h net) where three of the six shortlisted hypotheses spent thousands of words reaching worse answers |
| **−3.8** | The chin EO/IR gimbal is in the crush-keel load path and will be destroyed on landings, not by drag | Not analysed. **Not an endurance item and should not be scored as one** — it is a recovery-survivability item, and `materials_pack` §9 already routes 20 kg × (5–11 g) = 1,000–2,160 N of transient into an aluminium load frame. Real; belongs in the recovery pack |
| **−5.0** | TAILLESS / flying wing: the aerodynamics are survivable, the C_Lmax collapse and the CG window are not | **Shortlisted (§2 #6, §3).** Refuted: **−9 h**, band −19 … +2. Conclusion upheld, magnitude nearly doubled |
| **−14.6** | Canard or forward-mounted horizontal surface with no booms: dead on induced drag and dead on CG | Not analysed in depth; **the §3.3(a) arithmetic disposes of it a fortiori.** Any surface ahead of the CG drives the neutral point forward, and the pod already drags it forward 7–9% MAC. A canard on this pod at this fuselage fineness has no CG solution at all |
| **−17.7** | Reject the Prandtl/Bowers bell spanload the design pack calls for: its span efficiency is 0.750 and its structural credit does not survive this wing's stiffness criterion | **Shortlisted (§2 #8).** Refuted on magnitude and on three of four supporting claims: **−18.6 h**. Conclusion upheld. Note the title is wrong — `design_pack` does not call for a bell spanload (§4.2) |

---

## 7. What Phase 2 must simulate, at what fidelity, with what is already installed

The tool chain is present and verified on this machine: **XFOIL** (`/usr/bin/xfoil`), **AVL 3.36** (`vendor/bin/avl`), **NeuralFoil 0.3.3**, **AeroSandbox 4.2.10**, **SU2** (`vendor/bin/SU2_CFD`), **CalculiX 2.x** (`/usr/bin/ccx`), and **torch 2.11.0+cu128 with CUDA on an RTX 3500 Ada**. Nothing below needs a purchase.

Ordered by **hours of uncertainty retired per hour of work**, not by intellectual interest.

### P2-1 — Close the lumped Oswald factor. **Worth −5.6 h of open band. Blocks everything else in this pack.**

*Fidelity: AVL (inviscid spanload) + NeuralFoil or XFOIL (section polars) integrated spanwise, cross-checked against AeroSandbox `AeroBuildup`. No CFD.*

- AVL on the committed planform at matched C_L = 1.21, 12 sections, 24 spanwise panels with tip-bunched spacing (the NaN limit of 40 is already established), extracting the spanload Γ(y) and e_inv. **First fix the open defect in `docs/decisions/2026-08-20-span-efficiency-finding.md`: AVL's α = 11.71° at C_L 1.21 implies it is not ingesting the FX 63-137 camber from the AFILE.** Span efficiency is planform- and twist-driven so the *trend* stands, but no absolute angle from that run is trustworthy until camber ingestion is verified.
- NeuralFoil (or XFOIL with `ncrit` swept 7/9/11) on `data/airfoils/fx63137.dat` at **Re 0.30–1.10 M** across the local c_l range the spanload actually produces, integrated strip by strip to give the viscous lift-dependent term k directly rather than by subtraction.
- **Deliverable:** a lumped e with a stated band, replacing `aero.oswald_e: 0.85`, and a C_D0 built up per component rather than assumed. **Gate:** the buildup must reproduce the report's 0.020 to within the report's own ±15% C_D0 validation gate, or the disagreement must be explained.
- Torch on the GPU is the right vehicle for the sweep: the committed simulator is already batched and differentiable, so a population of (e_inv, k, C_D0, C_Lmax) draws integrates in one pass and the uncertainty propagates to endurance directly.

### P2-2 — Settle the equipment layout and solve for `wing.x_le_frac`. **Worth −60 h. Not a simulation task, and it must not be deferred behind one.**

Station and volume every item of the 148.5 kg dry mass; decide where the 85 m² canopy fires from; resolve the powerplant bay. **Then** solve for the wing station, and only then re-run everything else. Tooling: the committed CAD (`argus7.cad`, `scripts/build_model.py`) already lofts the fuselage from `design/argus7_v1.yaml`, so bay volumes come out of the existing frustum integration for free. **Until this exists, `wing.x_le_frac` is a flagged unknown in 0.365–0.53 and every static-margin figure in the report inherits the flag.**

### P2-3 — Price the span-and-area extension properly (the not-shortlisted +8.6 h and +6.9 h items). **Worth up to +9 h, and it is the only remaining positive lever of any size.**

*Fidelity: AVL for e_inv(b, S, taper, twist); the existing constant-stress cap-sizing and double-integration deflection model for mass and tip deflection; CalculiX only if the deflection model's linearity is in doubt (it is — **and this is disagreement five**: `materials_pack` §2.3 puts limit-load tip deflection at 14.2% of semi-span, and one of the analyses could not reproduce that figure: an independent reconstruction of the same sizing basis gives **27.3%** [AN], a factor of 1.92 in I, consistent with an I = A·h² rather than A·h²/2 slip. **That discrepancy must be resolved before any span decision**, because it doubles the flexibility of the wing being extended).*

Sweep b from 9.26 to 12.0 m at fixed and growing area, carrying **all four** couplings the hypotheses kept dropping: cap mass (k³ strength / k⁶ deflection once depth shrinks), wing internal volume (S²/b at fixed area — it *falls*), transport and assembly (the design pack already flags 8.72 m), and V_h (which falls as MAC grows).

### P2-4 — Aeroelastic tip-twist under load. **The only Phase-2 item that requires a tool the programme has not yet used.**

*Fidelity: CalculiX beam or shell model of the spar-plus-skin box, statically coupled to AVL's spanload, iterated to convergence. Two runs: 1 g and the report's own 12 m/s gust case (n = 2.10).*

This is the item that kills the tailless (§3.3d) and it is also unanswered for the **baseline**: at 4.9° of tip slope at 1 g on an unswept wing the streamwise incidence change is nominally zero, but the spanload the caps were sized for assumes a rigid wing, and `materials_pack` open question 5 has been asking for exactly this since the materials pack was written. Add flaperon reversal and divergence speed while the model exists.

### P2-5 — FX 63-137 at the true operating Reynolds numbers, and where transition actually is.

*Fidelity: XFOIL/NeuralFoil first; **SU2 RANS with a transition model only if the XFOIL bubble behaviour proves decisive**, and only on 2-D sections — a 3-D RANS of an AR-22 wing on a laptop GPU is not a Phase-2 activity.*

`materials_pack` open questions 1 and 2 are still open and they carry more endurance than this entire pack: the wing-skin decision alone is **16.6–23.3 h**. The tip runs at Re 3.5 × 10⁵ at light-weight loiter, inside the documented high-drag knee. **This is partly a data-purchase problem, not a research problem** — obtain the Stuttgart Profilkatalog or UIUC tabulated polars, smooth and tripped, before treating any C_D0 band as settled.

### P2-6 — Only if P2-1 through P2-5 close: the two tip decisions.

The raked tip (§4.4) does **not** wait for any of this — it is a €0 drawing change that expires at the tooling gate, and at +1.5 to +2.3 h across every assumption band examined it does not need a simulation to justify. **What waits is the Hoerner shape credit**, which needs a nonplanar VLM or panel run of a *defined datum tip* against a *defined Hoerner tip* on this exact planform, and which is worth +0.15 h — i.e. it should probably never be run at all.

**One methodological requirement, and it is the lesson of §2.3.** Every Phase-2 result must be reported as a **complete input vector fed to the committed simulator**, not as a sum of linearised deltas. Four of six analyses in this study produced headline numbers that did not reproduce from their own reported inputs, and in three of those the discrepancy was a *hidden* term. The simulator is batched, differentiable and free to run; there is no excuse for a hand-summed ledger.

---

## 8. Open questions

**Aerodynamic**

1. **Is the lumped Oswald factor 0.77 or 0.85?** `docs/decisions/2026-08-20-span-efficiency-finding.md`, status *open, blocks the optimiser*. ΔC_D = 0.00259, **worth −5.6 h** — larger than every positive item in this pack combined. **Nothing else in this study is decidable inside that band.**
2. **What is the datum tip?** Nothing in the repository defines one: `argus7/design/geometry.py` lofts root and tip chords with no tip treatment, `argus7/aero/buildup.py` has no tip term. Every Hoerner-class credit is by construction relative to a square-cut tip. If e = 0.85 was picked as generic sailplane practice, the credit is already banked and is **exactly zero**.
3. **Does AVL ingest the FX 63-137 camber from the AFILE?** α = 11.71° at C_L 1.21 says probably not [5]. The e trend survives; no absolute angle from that run does.
4. **What does the FX 63-137 actually do at Re 0.30–1.10 M, smooth and tripped?** Inherited unresolved from `materials_pack` open questions 1 and 2. It sets the viscous lift-dependent term k, which §4.2 shows is the *only* remaining route to e > 0.866.
5. **Where is transition at C_L 1.21?** Assumed 45–55% chord [EST]. The raked-tip ΔC_D0 of −0.00016 and the whole laminar-run argument for span extension both rest on it.

**Configuration and balance**

6. **What is `wing.x_le_frac`?** Tagged `assumption`, sourced to nothing, and the single most load-bearing literal in the codebase. The committed value 0.22 does not balance by 0.47–0.67 m (107–153% MAC). `empennage_trade` finding 8 computes 0.365–0.456 from one mass build-up; a second gives 0.446–0.527. **The spread is itself 33% MAC.** Not resolvable by analysis — it needs an equipment layout.
7. **Where does 70–86 L of fuel live, and what does it weigh?** `materials_pack` §10 says bladders are 5.0–6.5 kg; the saddle-tank analysis booked 3.5 kg while taking the 3.0 kg integral-tank credit from the same line. And at the mass-limited ceiling (§5) the answer may be that **volume stops mattering at 91 kg of fuel**, which changes the question.
8. **What is the actual fuel?** 0.8458 kg/L exists in no fuel. Mogas 0.745 and Jet-A 0.804 differ by **7.9% in mass at fixed volume and by 3.4 h of endurance at 85 L**, and the report's 270 g/kWh BSFC belongs to the mogas engine while the only heavy-fuel candidates in report §6 run 330 g/kWh and cannot make the 12.2 kW climb requirement. **The fuel, the BSFC and the engine must be chosen together or not at all.**
9. **Does the wing tip strike the ground before the fuselage on recovery?** Yes at more than **10.7°** of roll, inside the ±5–15° canopy pendulum band, 50–100 times. Absent from the report, from `materials_pack` §8 fatigue, and from the recovery sizing.

**Structural**

10. **Is limit-load tip deflection 14.2% of semi-span or 27.3%?** `materials_pack` §2.3 says 659 mm; an independent reconstruction of its own stated sizing basis gives 1,264 mm — **a factor of 1.92 in I**, consistent with an I = A·h² rather than A·h²/2 slip. Either answer makes the wing flexible; they differ by whether it is *unusually* flexible. **This blocks any span decision.**
11. **Is the 17.9% root-bending margin (16.18 kN·m sized against 13.73 kN·m elliptic) real?** It is a gap between two **load models**, not a certified reserve, and it moves the moment a real spanload is run against a twist that is tagged `assumption`. Every "structurally free" claim in §4.3 depends on it.
12. **What does a concentrated tip moment do?** The winglet's torsion path is not covered by the uniform-versus-elliptic *bending* comparison that was used to delete the hypothesis's reinforcement charge. Plausible, not established.

**Propulsion (out of this pack's remit, escalated)**

13. **What is the propeller's absorbed-power ceiling at loiter density?** §3.5: the established ~4.66 kW is a sea-level figure; the same C_P = 0.25 at ρ = 0.81913 gives **3.12 kW against a 4.53 kW baseline demand**. Either C_P is strongly advance-ratio-dependent here (likely) or **loiter does not close either** — and that would be the single largest unresolved item in the programme, larger than fuel volume.
14. **What is the BSFC at 14–27% load for 113 hours?** The committed simulator's own docstring flags that a constant BSFC materially overstates endurance. One un-analysed hypothesis puts a variable-pitch fix at +12 h.

---

## 9. Sources

| # | Source | Type |
|---|---|---|
| [1] | `docs/argus7_design_report.md` v1.0, 2026-08-20 (§2 geometry, §3 mass budget, §4 aero/performance, §5 structures, §6 propulsion, Annex A premortem, Appendix C assumptions register) | project document |
| [2] | `research/materials_pack.md`, 2026-08-20 (§2.1 load cases, §2.2 cap mass, §2.3 stiffness criticality, §2.5 wing fuel volume, §6.8 exchange rates, §10 mass closure, §11 verdict, §13 open questions) | project document |
| [3] | `research/empennage_trade.md`, 2026-08-20 (§1 findings, §2 configuration table, §2.2 adversarial corrections, §3 boomless case, §8.1 tail-area convention, finding 8 balance) | project document |
| [4] | `research/riblets_pack.md`, 2026-08-20 | project document |
| [5] | `docs/decisions/2026-08-20-span-efficiency-finding.md`, 2026-08-20 — AVL 3.36 twist sweep, e_inv 0.9786 at −3°, the three-quantity conflation, status *open, blocks the optimiser* | project document [M] |
| [6] | `research/boom_construction_pack.md`, 2026-08-20 (§6.1 slipstream geometry, §6.5 vibratory strain, §14 boom mass) | project document |
| [7] | `research/design_pack.md`, 2026-08-20 — **the 200 kg AR-20 predecessor**; per `design/argus7_v1.yaml`'s provenance block, "a different aircraft, and none of v1.0's numbers come from it" | project document |
| [8] | `design/argus7_v1.yaml` and `argus7/design/geometry.py` — the committed parametric model and its field-level provenance | source |
| [9] | `argus7/mission/sim.py` — the committed batched differentiable loiter integrator used for every Δh in this pack | source |
| [10] | D. Raymer, *Aircraft Design: A Conceptual Approach* — winglet effective-aspect-ratio relation AR_eff = AR(1 + 1.9h/b) | [DR] |
| [11] | I. Kroo, "Drag Due to Lift: Concepts for Prediction and Reduction", *Annu. Rev. Fluid Mech.* 33 (2001); R. T. Jones, minimum induced drag at fixed root bending moment | [DR] |
| [12] | L. Prandtl, "Über tragflügel kleinsten induzierten widerstandes" (1933) — the bell spanload at constant integrated bending moment, ×√1.5 span for −11.1% induced drag | [DR] |
| [13] | A. H. Bowers *et al.*, "On Wings of the Minimum Induced Drag: Spanload Implications for Aircraft and Birds", NASA/TP-2016-219072 | [DR] |
| [14] | M. S. Selig & B. D. McGranahan, AIAA 2004-1188 — FX 63-137 clean and tripped, Re 1–5 × 10⁵, the documented high-drag knee | [M] |
| [15] | S. F. Hoerner, *Fluid-Dynamic Drag* — tip-shape effective-span credits and endplate relations | [DR] |
| [16] | Z. Lyu & J. R. R. A. Martins, trim-drag sensitivity to static margin (~0.36% of drag per 1% MAC), as cited in `research/design_pack.md` | [DR] |
| [17] | Multhopp and Munk slender-body neutral-point shift methods, applied to the lofted 0.4105 m³ pod volume | [CALC from DR] |

---

## Appendix — reproducibility

Every `[CALC]` figure in this pack derives from the committed model and the committed simulator, not from a re-implementation. To reproduce:

```bash
PYTHONPATH=. .venv/bin/python - <<'PY'
import torch
from argus7.mission.sim import simulate_loiter
from argus7.design.schema import load_design
from argus7.design import geometry as G

T = lambda x: torch.tensor(float(x), dtype=torch.float64)

def endurance(mtow=250.0, fuel=101.5, S=3.9, AR=22.0,
              cd0=0.020, e=0.85, clmax=1.6, eta=0.84):
    return simulate_loiter(
        mass_total_kg=T(mtow), mass_fuel_kg=T(fuel), wing_area_m2=T(S),
        aspect_ratio=T(AR), cd0=T(cd0), oswald_e=T(e), cl_max=T(clmax),
        altitude_m=T(4000.0), bsfc_kg_per_kwh=T(0.270),
        payload_power_w=T(500.0), prop_efficiency=T(eta),
        n_steps=20000).endurance_h.item()

print(endurance())                                            # 112.977  (baseline A)
print(endurance(cd0=0.016) - endurance())                     # +8.588
print(endurance(mtow=188.7, fuel=40.2))                       #  53.35   (baseline B)
print(endurance(S=3.9653, AR=22.82, cd0=0.019840, fuel=100.96))  # 115.04 (raked tip, +2.06)
print(endurance(cd0=0.0185, e=0.808, clmax=1.35, fuel=98.95))    # 103.57 (tailless, -9.40)

d = load_design('design/argus7_v1.yaml')
w = G.derive_wing(d.wing)
mac_le = G.wing_ac_x(d) - 0.25 * w.mac_m
print(w.span_m, w.mac_m, mac_le, G.wing_ac_x(d), G.tail_qc_x(d), G.tail_volume_h(d))
# 9.26283  0.441230  0.783310  0.893618  4.093618  0.576477
PY
```

The five calculation groups behind the non-simulator numbers are:

1. **Span-efficiency decomposition** — 1/e = 1/e_inv + k, with e_inv from [5] and k = 1/0.85 − 1/0.9786 = 0.154603. Every ceiling in §4.2 follows from inverting it.
2. **Tip-device effective span** — δb_eff/b = 2k·c_tip/b with c_tip/b = 0.2613/9.2628 = 0.028209; winglets via AR_eff = AR(1 + 1.9h/b) at 80% realisation applied to the *inviscid* part of e only.
3. **Bending and cap sizing** — as `materials_pack` appendix: M(y) = w(s−y)²/2, ultimate 16.18 kN·m uniform / 13.73 kN·m elliptic, both reproduced exactly.
4. **Neutral point and CG** — MAC LE at x = 0.78331 m, MAC 0.44123 m, 8% MAC window = 35.3 mm; CG travel over a fuel burn = m_fuel·(x_cg − x_fuel)/(MTOW − m_fuel), i.e. **divided by the empty mass, not the MTOW** — the fuel-at-the-AC case is 11.62% MAC, not 6.90%.
5. **Propeller absorbed power** — P = C_P·ρ·n³·D⁵ at n = 35 rev/s, D = 0.813 m; ρ = 1.225 gives 4.66 kW at C_P 0.25, ρ = 0.81913 gives 3.12 kW (§3.5).

Anyone re-deriving these should get the same answers; where they do not, **the discrepancy is more interesting than the number** — and on the evidence of §2.3, it is usually a hidden term.
