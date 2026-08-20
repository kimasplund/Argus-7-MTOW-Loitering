# ARGUS-7 — MATERIALS & MANUFACTURING DATA PACK

**Date:** 2026-08-20 · **Scope:** airframe materials and build methods for the 250 kg MTOW / 9.26 m span / AR 22 configuration of `docs/argus7_design_report.md` · **Companion to:** `research/design_pack.md`

**The question this pack was written to answer:** can a COTS-carbon-tube + 3D-printed build reach the 32.5 kg wing budget *and* the surface quality the FX 63-137 laminar bucket needs — and if not, what does it cost in endurance?

---

## 0. How to read this

Every numeric claim carries a bracketed source `[n]` and a provenance tag:

| Tag | Meaning |
|---|---|
| **[DS]** | Manufacturer datasheet, quoted verbatim (unit-converted only) |
| **[M]** | Measured / published experimental data (wind tunnel, mechanical test) |
| **[CALC]** | Computed here from the report's own geometry and load cases; the scripts are reproducible from the equations given inline |
| **[EST]** | Engineering estimate by the author of this pack — a judgement, not a measurement |
| **[DR]** | Derived from a secondary source that itself cites a primary one |
| **[UNV]** | Unverified — flagged as needing test or vendor confirmation |

Two honesty rules applied throughout:

1. **Where a datasheet is internally inconsistent, it is called out rather than quoted straight.** Two vendors' pultrusion datasheets in §3 fail a rule-of-mixtures cross-check; that is stated.
2. **Where this pack disagrees with the design report, it says so and shows the arithmetic.** Three such disagreements are in §2.2, §2.3 and §2.5.

**Calibration check on the endurance model.** All endurance deltas in this pack come from a re-implementation of the report's §4 loiter model (ISA 4000 m, ρ = 0.81935 kg/m³, S = 3.9 m², AR = 22, e = 0.85, C_L = C_Lmax/1.15² = 1.210, η_prop = 0.84, 500 W payload through a 0.75 alternator path, BSFC 270 g/kWh, integrating 250 kg → 148.5 kg). Fed C_D0 = 0.016 it returns **+8.6 h** against the C_D0 = 0.020 baseline; the report's own stated sensitivity is **+0.36 d = +8.64 h** [1]. The model is therefore a faithful reproduction of the report's model and is used only for *relative* deltas, scaled onto the report's headline 112.8 h. [CALC]

---

## 1. Answer first

**The sponsor's preference is right about spar caps and booms, wrong about skins, and roughly break-even about ribs.**

| Claim | Verdict | The number |
|---|---|---|
| Pultruded UD carbon rod/strip is a genuine spar-cap material | **Right, strongly** | Measured 1,682 MPa compressive / 133.8 GPa in the Rock West rod [2][DS]; 1,600 MPa / 140 GPa independently from a second pultruder [3][DS]. That is **2.8× the report's 600 MPa compression allowable** and **+15% specific stiffness over hand wet layup** [CALC] |
| COTS carbon tube can be the twin booms | **Right** | A 90 × 2.5 mm roll-wrapped tube runs at 102 MPa against a 620 MPa allowable; it is stiffness-, not strength-critical. 1.07 kg/m, 7.8 kg for two 3.65 m booms [CALC from 4][DS] |
| COTS carbon tube can be the **wing** spar | **Wrong** | A round tube inside a 12%-thick wing needs **2.07× the material** of a cap-and-web spar for the same moment — 9.0 kg vs 4.35 kg at σ = 600 MPa [CALC] |
| 3D-printed parts as primary structure | **Wrong** | At equal section, matching pultruded carbon's stiffness needs **15 kg of PA12-CF per 1 kg of carbon** [CALC from 2][5] |
| 3D-printed ribs, fairings, cradles, ducts | **Acceptable, at a 3.8–4.4× mass penalty vs foam/balsa ribs** | 4.10 kg of printed ribs at 100 mm pitch vs 0.91 kg in Rohacell/glass [CALC] |
| Heat-shrink film skin | **Wrong for this aircraft** | Not because of streamwise waviness (there is margin) but because film cannot form the leading edge, cannot hold the pressure-recovery contour, and its scalloping is a *spanwise* disturbance for which no favourable criterion exists — see §6.3 |
| Printed skin panels | **Wrong, decisively** | 2.63 kg/m² for a printed sandwich panel vs 0.68 kg/m² for CFRP/Rohacell at 1,700× *less* bending stiffness in the solid form [CALC]. +18.7 kg on the wing |

**The endurance answer, stated precisely.** The premise in the tasking — "if the build method forces C_D0 to 0.024+, roughly a day of endurance disappears" — is **half right, and right for a different reason than stated**:

- C_D0 = 0.024 **alone** costs **7.4 h (0.31 d)**, not a day. [CALC]
- The full consequence of a film-covered, non-laminar wing is **16.6–23.3 h (0.69–0.97 d)** — and *most of it is not the C_D0 term*. It decomposes as: aero drag −12.4 h, the measured −0.2 C_Lmax roughness penalty (which raises the stall-constrained loiter speed) −5.4 h, and +4.9 kg of extra structure displacing fuel −7.3 h. [CALC from 6][M]
- So: **yes, about a day — but the report's own "dirty 0.024" number understates the penalty by more than half**, because it counts only parasite drag and ignores both the C_Lmax loss and the mass.

**And a partial acquittal of the sponsor.** A hybrid that keeps pultruded caps and an accurate skin forward of 55% chord, but uses printed ribs and film aft, lands at **33.7 kg wing (+1.2 kg over budget)** and **−4.9 to −12.2 h**. That is a real option, not a strawman. See §11.

---

## 2. What the structure actually has to do

### 2.1 Load cases, re-derived from the report's own geometry

Span b = √(22 × 3.9) = **9.263 m**, semi-span s = 4.631 m; root/tip chord 0.581/0.261 m [1].

At n_ult = +5.7 g and MTOW 250 kg, with the report's *uniform* spanwise lift assumption:

- L_ult = 250 × 9.80665 × 5.7 = **13.97 kN**; per half-wing 6.99 kN; w = 1,508.7 N/m
- M_root = w·s²/2 = **16.18 kN·m** — the report says 16.2 kN·m ✓
- Elliptical alternative: 6.99 kN × (4/3π)·s = **13.73 kN·m** — the report says 13.7 ✓
- Structural depth 70 mm at root = 0.1205 × root chord → cap force = 16,180/0.070 = **231.1 kN** — the report says 232 kN ✓
- Cap areas: 231.1 kN / 800 MPa = **289 mm²** tension, / 600 MPa = **385 mm²** compression — the report says 290 / 387 ✓

[CALC] The report's structural chain is internally consistent and reproduces exactly. Three things follow from it that the report does not draw out.

### 2.2 Disagreement 1 — the report's spar-cap mass carries ~5.9 kg of unstated conservatism

The report quotes "cap mass 8.6–11.5 kg" [1]. Integrating the *sized* cap area A(y) = M(y)/(h(y)·σ) along the span for the real tapered planform, with M(y) = w(s−y)²/2 and h(y) = 0.1205·c(y):

| Cap sizing basis | Both wings, both caps |
|---|---|
| Tapered to the local moment, σ = 800/600 MPa, ρ = 1,550 kg/m³ | **3.81 kg** |
| Same, with a 10% minimum-gauge floor outboard | 3.96 kg |
| Same, at a conservative 600/450 MPa | 5.08 kg |
| **Constant root section carried over the full span** | **9.68 kg** |

[CALC] The report's 8.6–11.5 kg band brackets 9.68 kg, i.e. the report almost certainly costed a **constant-section cap running root to tip**. That is not how anyone builds a spar. **A properly tapered cap at the report's own allowables is 3.8–4.0 kg, leaving ~5.9 kg of unclaimed margin inside the 32.5 kg wing budget.** That margin is the single biggest reason the sponsor's heavier build methods come as close to closing as they do (§10).

### 2.3 Disagreement 2 — the wing is stiffness-critical, not strength-critical

Integrating curvature twice along the span with EI(y) from the strength-sized caps (E = 133.8 GPa pultruded [2][DS]):

| Condition | Tip deflection | % semi-span | Tip slope |
|---|---|---|---|
| 1 g cruise | 174 mm | 3.7% | 4.9° |
| Limit +3.8 g | **659 mm** | **14.2%** | 18.8° |
| Ultimate +5.7 g | 989 mm | 21.4% | 28.2° |

[CALC] Modern 15 m sailplanes deflect on the order of 8–10% of semi-span at limit load. 14.2% is at the flexible end of anything flown, and 21.4% at ultimate is far enough into geometric non-linearity that a linear beam calculation stops being trustworthy.

**Consequence for material selection:** if cap area is set by stiffness rather than strength, the figure of merit is **E/ρ, not σ/ρ**. That inverts the usual argument about pultruded rod. Pultruded rod's headline attraction is its 1,682 MPa compressive strength — but that strength is not what buys anything here. What buys something is that pultrusion delivers **133.8–140 GPa at Vf 60–65%** [2][3][DS] where a solo builder's hand wet layup at Vf ≈ 0.50 delivers ~117 GPa:

| Route | E (GPa) | ρ (g/cm³) | E/ρ | Source |
|---|---|---|---|---|
| Pultruded UD, T700-class | 133.8 | 1.523 | **87.9** | [2][DS] |
| Pultruded UD, second vendor | 140 | ~1.57 | 89.2 | [3][DS] |
| Vacuum-bagged UD prepreg, Vf 0.58 | ~134.8 | 1.548 | 87.1 | [CALC], rule of mixtures |
| Hand wet layup UD, Vf 0.50 | ~116.8 | 1.500 | 77.8 | [CALC], rule of mixtures |
| Roll-wrapped tube wall (bending layup) | 94.7 | 1.523 | 62.2 | [4][DS] |
| Filament-wound tube wall | 72.6 | 1.523 | 47.7 | [7][DS] |

**Pultruded strip matches prepreg on specific stiffness and beats hand wet layup by 13%, with no autoclave, no freezer, and no layup skill.** That is the real case for it, and it is a stronger case than the strength argument.

If the deflection is to be pulled back to a glider-like 9% of semi-span, EI must rise 1.57×. Two ways:
- **+57% standard-modulus cap area:** 3.8 → 5.97 kg (**+2.2 kg**)
- **High-modulus pultrusion (240 GPa, UMS45-class):** 1.71× EI at *unchanged mass*, but compressive strength drops to 1,000 MPa [3][DS] and price roughly 2.5× [8]

[CALC] The HM route is the better lever and it is only available *because* the section is pultruded — you cannot hand-lay HM fibre well.

### 2.4 Torsion is not demanding — which tells you what the skin is actually for

At V_D = 200 km/h EAS (q_D = 1,890 Pa) with C_m = 0.18 for the FX 63-137 class, the root torque is 293 N·m limit / 439 N·m ultimate. Carried in a D-nose torsion cell of enclosed area 85 cm², Bredt gives a shear flow of 25.8 kN/m — **0.26 mm** of ±45 skin at τ = 100 MPa. [CALC]

The shear web is equally undemanding: root shear 6.99 kN over a 70 mm depth needs **1.00 mm** at τ = 100 MPa, or 1.66 mm at a conservative 60 MPa. [CALC]

**So neither the web nor the skin is strength-driven.** Minimum gauge and buckling stability set the web; **aerodynamic shape-holding sets the skin.** This is why the skin question in §6 is a surface-quality question and not a structures question, and why "make the skin thinner to save mass" is the wrong lever — the mass is in whatever it takes to hold contour between supports.

### 2.5 Disagreement 3 — the wing cannot hold the fuel

> **Correction (added post-publication, P1 CAD rebuild):** the 0.68 "typical
> airfoil" shape factor used below is measurably wrong for this design's
> actual section. Loading the real FX 63-137 coordinates
> (`data/airfoils/fx63137.dat`) and computing the enclosed area directly by
> shoelace integration gives a shape factor of **0.6062**, not 0.68 — 0.68
> is **+12.2% biased high** for this aerofoil (`0.68/0.6062 = 1.122`; see
> `tests/test_cad_wing.py::test_wing_planform_area_matches_spec`, which
> found and fixed the same bias in the CAD volume check). Propagating the
> corrected factor through this section's own arithmetic:
> `160 L × 0.6062/0.68 = 142.6 L gross` (≈ **143 L**, not 160 L). The
> "56–72 L usable" figure below scales down by the same ratio to
> **~50–64 L usable**, still well short of the report's 120 L requirement —
> the qualitative finding (the wing cannot hold the fuel) is unchanged and,
> if anything, worse than originally stated. The rest of this section is
> left as originally written rather than silently edited; treat 0.68 and
> everything downstream of it (160 L, 56–72 L) as superseded by the 143 L /
> ~50–64 L figures above. See `README.md`'s "Known gaps" for the
> project-level tracking of this finding.

Wing internal volume, taking the enclosed airfoil area as 0.68·c·t = 0.0932·c² for a 13.7% section:

V = 2 × 0.0932 × ∫₀ˢ c(y)² dy = 2 × 0.0932 × 0.8604 = **0.160 m³ = 160 L gross**

Usable integral tankage is realistically 35–45% of gross wing volume once the spar box, ribs, control runs, dry bays and expansion space are removed → **56–72 L**. The report requires **~120 L** in "wing tanks at the AC" [1]. [CALC]

This is outside this pack's remit but it lands squarely on it: closing the fuel volume forces either (a) sealed integral wet-wing bays, which is a hard requirement for a bonded rod-and-tube build and rules out unsealed printed ribs inside the tank bays, or (b) fuselage-pod tankage, which reopens the CG-travel question the report closed by putting fuel at the AC. Flagged in §13.

---

## 3. Pultruded UD carbon rod, strip and plate

### 3.1 Measured properties — three sources, cross-checked

| Property | Rock West 47312 rod, Ø 0.432″ [2] | Compositesplaza pultrusion [3] | R&G / DPP (Van Dijk) [8] |
|---|---|---|---|
| Fibre | Toray T700S, ">60%" | Torayca T700 or equiv. | HT carbon, T300/T700 or equiv. |
| Fibre volume fraction | not stated | **±63%** | 60–65% (DPP), ~63% (R&G) |
| Axial modulus E_x | **133.8 GPa** (1.94×10⁷ psi) | **140 GPa** | ">200 GPa" — see note |
| Axial tensile strength | **2,372 MPa** (344 ksi) | **2,500 MPa** | ">3 GPa" — see note |
| **Axial compressive strength** | **1,682 MPa** (244 ksi) | **1,600 MPa** | not stated |
| Transverse modulus E_y | 8.69 GPa | — | — |
| Transverse tensile | 63.4 MPa | — | — |
| Shear modulus G_xy | 5.52 GPa | — | — |
| ILSS | — | — | ~100 MPa |
| Density | **1.523 g/cm³** (0.055 lb/in³) | ~1.55–1.60 (back-calc from g/m) | "approx. 1.78" — see note |
| Resin / Tg | bisphenol-A epoxy, **Tg 120 °C** | bisphenol-A epoxy, **Tg 120 °C** | HDT ~120 °C |
| Straightness | — | 2 mm / 1,000 mm | ≤1 mm / m |

[DS] for all. Unit conversions at 1 psi = 6.894757 kPa.

**Two datasheet problems, called out:**

- **R&G's ">200 GPa modulus / >3 GPa tensile" are virgin-fibre values, not laminate values.** At Vf 0.63 with T700 (230 GPa fibre), rule of mixtures gives 0.63 × 230 + 0.37 × 3.5 = **146 GPa** — you cannot get 200 GPa out of HT fibre at 63% Vf. Use 134–146 GPa. [CALC]
- **R&G's stated density of 1.78 g/cm³ is ~13% too high.** Rule of mixtures at Vf 0.63 (fibre 1.80, epoxy 1.20) gives **1.578 g/cm³**; Rock West's independently stated 1.523 and Compositesplaza's back-calculated 1.55–1.60 g/m both agree with the mixture rule. **Design to 1.52–1.60 g/cm³, not 1.78** — using 1.78 would over-predict cap mass by 13%. [CALC]

**The compressive number is the one that matters and it cross-validates.** Two independent pultruders quote 1,600 and 1,682 MPa. This is the strongest single result in this pack: pultrusion's straight, void-free, high-Vf fibre is precisely what compressive strength is sensitive to [9][DR].

### 3.2 How this compares with the report's allowables

| | Report allowable [1] | Measured material [2][3] | Ratio |
|---|---|---|---|
| Tension | 800 MPa | 2,372–2,500 MPa | **3.0–3.1×** |
| Compression | 600 MPa | 1,600–1,682 MPa | **2.7–2.8×** |
| Ultimate strain at the allowable | 0.60% / 0.45% (at E = 133.8 GPa) | 1.77% / 1.26% break strain | — |

[CALC] The report's allowables sit at a knockdown of ~0.34–0.36 on measured material strength. That is *not* excessive for a spar cap: the knockdown has to cover local buckling of the cap between web stabilisation points, fibre waviness, bondline defects, impact damage tolerance, hot/wet, and statistical B-basis. Published sailplane-structures practice puts a "high tensile fibre / tough resin system" cap at ~900 MPa design compression at ultimate with fracture above 1,000 MPa, justified by the spar being protected from impact and free of stress raisers [10][DR].

**Conclusion:** the report's 600 MPa compression allowable is *conservative by roughly 1.5×* against sailplane practice and by 2.8× against the raw material — and, per §2.3, is not the binding constraint anyway. Keeping it is the right call for a first article, but it should be recorded as a deliberate 1.5× reserve, not as the material limit.

### 3.3 Round rod vs rectangular strip vs plate — take the strip

Round rod packed into a cap groove loses to geometry:

- Hexagonal close packing of circles is 90.7% theoretical; a hand-packed bundle in a resin-filled groove realistically achieves **75–85%** [EST]. The remaining volume is neat resin: mass with no stiffness.
- To deliver 385 mm² of carbon you must cut a groove of **450–515 mm²** — into a spar that is only 70 mm deep at the root.
- Rectangular strip stacks at **>95%** with thin, uniform, easily-controlled bondlines, and the flat interfaces let you inspect for voids.

[CALC] **Specify pultruded rectangular strip (or plate), not round rod, for spar caps.** Round rod is the right product for pushrods, control links, rib capstrips, trailing-edge stiffeners and localised reinforcement.

### 3.4 Available sections and the splice problem — this is the real constraint

| Supplier | Sections held | Stock length | Note |
|---|---|---|---|
| Compositesplaza (NL) [3] | Ø 0.5–10 mm rod; 3×0.8, 6×0.8, 8×0.8, **20×1.0 mm** strip; small tubes | **1,000 mm only** | straightness 2 mm/m |
| R&G / DPP (DE/NL) [8] | round, square, half-round, rectangular incl. **50 × 10 mm** and 15 × 3 mm | **1,000–2,000 mm** | DPP = Van Dijk Pultrusion Products, premium grade |
| Rock West (US) [2] | Ø 0.011–0.5″ rod; strips 0.019×0.118″, **0.125 × 0.325″** | up to **96″ (2.44 m)** | 0.125×0.325″ = 26.2 mm² |

**The semi-span is 4.631 m. No supplier holds stock that long.** [DS]

This is the single most important practical finding about pultruded caps and it is not a showstopper — pultrusion is a continuous process and long lengths are a mill-order item (wind-blade spar-cap pultrusions are supplied in coiled tens of metres [9][DR]) — but a solo builder ordering from stock must splice. The correct method is a **glulam-style staggered butt**: build the cap as a stack of 4–8 strips, butt-joint each strip, and stagger adjacent joints by ≥20× the strip thickness, so at any station only 1/n of the cap area is discontinuous and the load ferries around the joint through the adjacent laminae in shear.

Sizing check: with 8 strips of 3 mm × 16 mm (48 mm² each, 384 mm² total ≈ the required root area), one butt joint locally removes 48 mm² = 12.5% of the cap. Transferring 231.1 × 0.125 = **28.9 kN** through the two adjacent bondlines at 30 MPa adhesive shear [11][DS] with a 50% peak-vs-average knockdown needs **2 × 16 mm × 60 mm** of overlap, i.e. a 60 mm stagger minimum; a 20t = 60 mm stagger satisfies it exactly, and 100 mm gives comfortable margin. [CALC]

**Rule: no butt joint inboard of 30% semi-span.** Inboard of that station the moment is high enough that a splice defect is a wing-loss event; buy or order continuous strip for the inner 1.4 m, splice only outboard.

### 3.5 Price

| Product | Price | €/kg or $/kg | Source |
|---|---|---|---|
| Rock West Ø 0.432″ rod × 72″ | $126.99 (clearance $63.49) | **$482/kg** ($241 clearance) | [2][DS] |
| R&G 20 × 2.0 mm × 1,000 mm strip (remainder stock) | from €14.27/pc | **€230/kg** | [8][DS] |
| Raw T700 12k UD fabric + laminating epoxy, hand layup | — | ~€90–150 for 4.2 kg of laminate | [EST] |

[CALC] **4.2 kg of pultruded spar caps costs €1,000–2,000 (add ~25% for waste and splice overlap → €1,250–2,600).** The same caps hand-laid cost €90–150 in materials.

**That €1,100–2,500 premium buys:** (a) 40–80 h of the highest-consequence layup on the aircraft, eliminated; (b) fibre volume fraction and straightness that a solo builder in a garage will not reproduce; (c) removal of the single failure mode most likely to be invisible until the wing breaks — fibre waviness in a compression cap. **On a €60k / one-pair-of-hands programme, this is the best-value line item in the whole build.**

### 3.6 Verdict on pultruded UD

**Adopt for spar caps, in rectangular strip form.** It is where the sponsor's preference is most clearly correct, and the reason is not the one usually given: the win is specific stiffness, quality assurance and eliminated labour, not headline strength.

---

## 4. Carbon tube — booms, and the tube-spar question

### 4.1 Roll-wrapped vs filament-wound: the trade is bending stiffness against torsional stiffness

Two real, in-stock products with published laminate allowables:

| | Roll-wrapped, 3k 2×2 twill outer + multidirectional uni core [4] | Filament-wound, standard modulus [7] | Clearwater reference laminates [12] |
|---|---|---|---|
| Part | RWC 45285, 3.000 × 3.125″ × 72″, wall 0.063″ (1.60 mm) | RWC 35165-U, 2.875 × 3.155″, wall 0.140″ (3.56 mm), to 15 ft | — |
| Fibre / resin | Tenax UTS50 / Eporite EHM32 | Grafil 34-700 | — |
| **E_x (axial)** | **94.7 GPa** | **72.6 GPa** | UD-"bending" 103 GPa; ±45-"torsion" 15.2 GPa |
| E_y (hoop) | 32.9 GPa | 33.2 GPa | — |
| **G_xy** | **11.68 GPa** | **22.53 GPa** | UD-"bending" 4.1 GPa; ±45-"torsion" 31 GPa |
| σ axial tension | 620 MPa | 455 MPa | UD 2,068 MPa |
| σ axial compression | 732 MPa | 510 MPa | — |
| Density | 1.523 g/cm³ | 1.523 g/cm³ | 1.55 |
| Mass | 0.591 kg/m | 1.302 kg/m | — |
| Tg | 107–121 °C (225–249 °F) | — | — |

[DS] all. Note that both vendors quote a *compressive* axial strength above the tensile one; that is characteristic of laminate-solver output rather than coupon test and should be treated as [UNV] — design to the tensile number.

**The trade is exactly as the fibre architecture predicts:** roll-wrapped gives +30% axial modulus (bending), filament-wound gives +93% shear modulus (torsion). **A twin boom carrying an inverted-V tail needs both.** Buying a generic "3K twill carbon tube" — which is largely ±45 fabric — gets you the torsional half and leaves you bending-soft. This is a specification, not a shopping decision.

### 4.2 Boom sizing for the inverted-V tail

Tail S_h = 0.31 m², arm 3.2 m, boom cantilever ≈ 3.4 m [1]. At V_D = 200 km/h EAS (q_D = 1,890 Pa) and C_N = 1.0 on the tail:

- limit tail load 586 N, ultimate 879 N, **440 N per boom**
- per-boom ultimate root bending **1,494 N·m**
- torque about the boom axis from a V-panel force acting at ~0.33 m along the panel: **≈150 N·m ultimate** [CALC]

| Tube | σ (MPa) | EI (kN·m²) | Tip defl. @ ult. | GJ (kN·m²) | Twist @ 150 N·m | kg/m | 2 booms, 3.65 m |
|---|---|---|---|---|---|---|---|
| 90 × 1.6 mm roll-wrapped [4] | 155 | 41.1 | **140 mm** | 10.2 | **2.9°** | 0.689 | 5.03 kg |
| 90 × 2.5 mm roll-wrapped | 102 | 62.3 | 93 mm | 15.4 | 1.9° | 1.065 | **7.78 kg** |
| 90 × 3.5 mm roll-wrapped | 76 | 84.2 | 68 mm | 20.8 | 1.4° | 1.474 | 10.76 kg |
| 80 × 3.56 mm filament-wound [7] | 95 | 45.8 | 126 mm | 28.4 | 1.0° | 1.339 | 9.78 kg |
| 90 × 2.5 mm, 60/40 UD/±45 custom | 102 | 52.6 | 109 mm | 23.7 | 1.3° | 1.065 | 7.78 kg |

[CALC from 4][7][DS]

**Findings:**

1. **The booms are stiffness-critical by a wide margin.** Even the thinnest tube runs at 155 MPa against a 620 MPa allowable — a margin of 4.0×. Nothing about boom *strength* is difficult.
2. **A 140 mm tip deflection is 2.4° of tail incidence change**, which directly erodes tail effectiveness and feeds the aeroelastic case. 90 × 2.5 mm is the practical minimum.
3. **A larger, thinner boom is a better trade than a thicker one.** Going 90 → 110 mm at the same wall raises I by 1.84× for 1.24× the mass — a net 48% gain in stiffness per kilogram. The drag cost is ΔC_D0 = +0.00042 → **−0.83 h of endurance** [CALC]. Trading 0.83 h for 2 kg of boom mass (which itself is worth 3.0 h of endurance, §11) is clearly favourable.
4. The report's current `booms.diameter_m: 0.09` is tagged `assumption` in `design/argus7_v1.yaml`. **It should be re-opened as a design variable at 100–110 mm.**

### 4.3 Can a COTS tube be the *wing* spar? No — and the penalty is a clean 2.07×

For a cap-and-web spar of depth h: required cap area = 2M/(σ·h).
For a round tube of diameter D carrying the same moment: section modulus πR²t = M/σ, and wall area = 2πRt = **4M/(σ·D)**.

Ratio = 2h/D. A tube must fit inside the wing (D ≈ 0.85 × local thickness) while a cap-and-web spar can put material at ≈0.88 × thickness, so:

**ratio = 2 × 0.88 / 0.85 = 2.07×** [CALC]

Integrated over the span at σ = 600 MPa:

| Spar architecture | Mass, both wings |
|---|---|
| Cap-and-web (caps only) | **4.35 kg** |
| Round tube spar | **9.01 kg** |

And it gets worse in practice, because the tube diameter must shrink outboard:

| y/s | chord | wing thickness | max tube OD |
|---|---|---|---|
| 0.00 | 581 mm | 79.6 mm | 67.7 mm |
| 0.25 | 501 mm | 68.6 mm | 58.3 mm |
| 0.50 | 421 mm | 57.7 mm | 49.0 mm |
| 0.75 | 341 mm | 46.7 mm | 39.7 mm |

[CALC] **A single constant-diameter tube cannot run out the span.** The build requires 3–4 telescoped/stepped sections with bonded overlap joints — which adds a further **+20–30%** over the ideal-taper 9.01 kg (call it 10.8–11.7 kg) [EST], plus 6–8 more joints in the primary load path.

**Offsetting credit:** the tube carries shear and torsion itself, so it deletes the shear web (0.8 kg) and reduces the demand on a D-nose torsion cell. Net honest comparison: **tube spar ≈ 9.0–11.7 kg vs cap+web ≈ 5.2 kg. The tube costs 3.8–6.5 kg of wing.** At the report's mass-to-endurance exchange rate (§11) that alone is **5.7–9.7 h of endurance**.

The geometry is unarguable: a circle puts most of its material near its own neutral axis, and a 12%-thick wing does not have the depth to spare.

### 4.4 Supply, sizes and price for the booms

- **Filament-wound is available to 15 ft (4.57 m) continuous** [7][DS] — long enough for a one-piece 3.65 m boom. Roll-wrapped stock at Rock West tops out around 72–96″ (1.83–2.44 m); a 3.65 m roll-wrapped boom is a custom mandrel order.
- 90 mm OD tubes are stocked in Europe (e.g. carbonwebshop's 90 mm range) and widely available from Asian drone-boom suppliers; observed listings for 90 × 86 mm × 1,000 mm run **$80–302** [13][UNV — marketplace listings, not vendor datasheets].
- Rock West's large filament-wound tubes are priced per 12″ increment; the 2.875″ family runs into four figures at 15 ft [7][DS]. **Budget €2,000–5,000 for two aerospace-sourced booms; €400–1,200 from a drone-boom supplier with unverified allowables.**

**Recommendation:** buy the booms from a supplier that will state E_x, G_xy and the layup. If the vendor cannot, treat the tube as [UNV] and coupon-test one before committing the tail.

### 4.5 Verdict on tube

**Adopt COTS tube for the booms (specify a mixed UD/±45 layup, 100–110 mm OD, ~2.5 mm wall). Reject it for the wing spar.**

---

## 5. 3D printing for aerostructures

### 5.1 Measured properties

| Material / process | ρ (g/cm³) | σ_t (MPa) | E (MPa) | Elong. (%) | Thermal | Source |
|---|---|---|---|---|---|---|
| **PA12, HP MJF** | 1.01 | 48 (yield 40) | **1,700** | 20 | — | [5][DS] |
| **PA12-CF, EOS CarbonMide (SLS)** | 1.04 | **72 / 56 / 25** (X/Y/Z) | **6,100 / 3,400 / 2,200** | 4.1 / 6.3 / 1.3 | T_melt 176 °C | [14][DS] |
| **PA6-CF, FDM (Bambu)** | 1.09 | **102 ± 7 (XY) / 48 ± 6 (Z)** | **4,430 ± 310 (XY) / 2,170 ± 230 (Z)** | 5.8 / 3.7 | **Tg 68 °C**, HDT 164 °C @1.8 MPa, 186 °C @0.45 MPa | [15][DS] |
| **PPS-CF10, FDM (Polymaker Fiberon)** | ~1.35 | 32 (as listed) — other vendors 74 | 5,314 dry; flex 4,647 (XY) | — | **HDT 252.5 °C @0.45 MPa** | [16][DS], [17][DR] |
| PA12-CF, FDM | ~1.06 | 60–75 | 3,500–5,500 | 3–6 | — | [17][DR][UNV] |
| PETG-CF, FDM | ~1.30 | 45–55 | 3,500–5,000 | 2–4 | Tg ~80 °C | [17][DR][UNV] |
| — for reference — | | | | | | |
| Pultruded UD carbon | 1.52 | 2,372 | 133,800 | 1.8 | Tg 120 °C | [2][DS] |
| 6061-T6 aluminium | 2.70 | 241 | 68,900 | 12 | — | [12][DS] |

Charpy (CarbonMide, unnotched, 23 °C): 20.5 / 27.5 / **5.5** kJ/m² X/Y/Z; notched 5.3 / 4.4 / **2.1** [14][DS]. MJF PA12 unfilled: 45 kJ/m² [5][DS] — **the unfilled grade is 2× tougher than the carbon-filled one and 8× tougher in Z.**

### 5.2 Anisotropy is the design constraint, not strength

CarbonMide Z-direction is **35% of X strength and 36% of X modulus**, with break strain down from 4.1% to **1.3%** [14][DS]. Bambu PA6-CF Z is **47% of XY strength, 49% of XY modulus** [15][DS].

[CALC] **Every printed part on this aircraft must have its build orientation specified on the drawing, and the drawing must state which direction carries load.** A rib printed flat (load in-plane) is a different part from the same geometry printed upright. This is a documentation obligation, not a material property — and it is the most common way printed aero parts fail.

### 5.3 Temperature — the real ceiling, and it is not HDT

The report's environment is "−5 to −15 °C at altitude" [1]. That is the benign case. The binding case is a **parked aircraft in sun**.

Measured reference: at 38 °C ambient, a *white* fibreglass-coated foam box reached **66 °C** surface; a *black* one exceeded **104 °C** [18][M]. Sailplanes are painted white specifically to keep the laminate below the epoxy Tg of ~88 °C [18][DR].

Against that:

| Material | Relevant temperature | Verdict for a sun-exposed part |
|---|---|---|
| PA6-CF | **Tg 68 °C dry** [15][DS] — and PA6's Tg falls steeply with absorbed water | **Fails.** A dark printed part in sun sits above Tg; creep rate multiplies |
| PA12 (MJF/SLS) | Tg ~40–50 °C; melt 176 °C; HDT 97 °C @1.8 MPa [5][14][DS] | Marginal. Survives, but see §5.4 |
| PPS-CF | HDT 252 °C @0.45 MPa, continuous use ~220 °C [16][17][DS/DR] | Passes comfortably, incl. engine bay |
| PETG-CF | Tg ~80 °C [17][DR] | Marginal for sun; fails in engine bay |
| Room-temperature-cure laminating epoxy | Tg 50–70 °C as cured; 80–90 °C after a 12–24 h elevated post-cure [19][DR] | **Fails without post-cure.** Post-cure is mandatory |
| Hysol EA 9394 paste adhesive | **Tg 78 °C dry / 68 °C wet** [11][DS] | Marginal — and its lap shear at 82 °C is 20.7 MPa vs 28.9 at 25 °C, a **28% loss** |

**Three hard rules follow:**
1. **Paint the aircraft white or very light.** This is a structural requirement, not cosmetic.
2. **Post-cure every room-temperature-cured epoxy joint** at 50–60 °C for ≥12 h before flight.
3. **No PA6-CF anywhere in sun or in the engine bay.** PA12 for exterior printed parts, PPS-CF for anything hot.

### 5.4 Creep — the number that disqualifies printed primary structure

SLS PA12 tensile creep, measured [20][M]:

- At **10 MPa** (25% of the material's 40 MPa UTS), after **100 h**: **1.7% strain at 23 °C, 2.5% at 60 °C, 3.9% at 100 °C**
- Isochronous 1,000 h curve at 23 °C: SLS PA12 reaches 10 MPa at ~2.0–2.5% strain → a **1,000 h isochronous modulus of ~400–500 MPa**, against a short-term modulus of 1,700 MPa [5][DS]
- Creep is approximately linear on log time, so a 1,000 h test extrapolates reliably to 10⁵ h [20][M]
- SLS PA12 is *more* creep-sensitive than most engineering thermoplastics but *less* than injection-moulded PA12 [20][M]

**Interpretation for a 122 h continuous mission:** a printed part under sustained load loses **60–75% of its stiffness over the mission**, at room temperature, and more at 60 °C. Elastic strain at 10 MPa is 0.59%; creep adds 1.7% in 100 h — creep is **~3× the elastic response**.

**But this cuts both ways, and the honest answer for ribs is favourable.** A rib at 100 mm pitch and c = 0.44 m carries its bay's airload: at n = 1, that is 0.044 m² × 629 Pa = 27.7 N, spread over a rib cross-section of ~500 mm² → **~0.06 MPa**. That is **170× below** the lowest stress in the creep test. [CALC] Creep is irrelevant for ribs. It is decisive for anything carrying a meaningful fraction of its own strength.

**The rule:** printed thermoplastic is acceptable where the sustained stress is **below ~2 MPa** (5% of UTS) [EST, derived from the 5 MPa lowest test point which still showed ~1% strain at 1,000 h]. Above that, size for the 1,000 h isochronous modulus, not the datasheet modulus.

### 5.5 Dimensional accuracy and build volume — the quiet showstopper for skins

HP MJF stated tolerance: **±0.30 mm below 100 mm, ±0.3% above 100 mm** [5][DS].

Over a 380 mm part (the machine's maximum dimension) that is **±1.14 mm**. Build envelope: **380 × 284 × 380 mm** [5][DS].

[CALC] A 4.63 m half-wing skin would need ≥13 panels per surface per wing — **52 panels and ~50 spanwise joints**, each carrying ±1.14 mm of contour tolerance and each producing a step. Against the admissible forward-facing step of **0.51 mm** at loiter (§6.1), **the tolerance alone is 2.2× the aerodynamic budget before you have printed anything.**

### 5.6 The mass penalty, quantified — and why it depends on the load type

Two different penalties, and conflating them is the usual error:

**(a) Tension/compression-dominated members (spar caps, tie rods).** Section geometry is fixed by the airframe; the only variable is area. At equal stiffness:

mass ratio = (ρ_print/ρ_carbon) × (E_carbon/E_print) = (1.04/1.523) × (133,800/6,100) = **15.0×**

[CALC] **1 kg of pultruded carbon = 15 kg of the best printed material.** There is no version of this that closes.

**(b) Bending/stiffness-dominated members (ribs, panels, brackets) where you are free to add thickness.** EI ∝ E·t³ and mass ∝ ρ·t, so at equal EI:

mass ratio = (ρ_print/ρ_carbon) × (E_carbon/E_print)^(1/3) = 0.683 × 2.80 = **1.9×**

[CALC] — which is why printed ribs are merely expensive, not impossible.

Measured against the actual parts:

| Part | Printed | Composite/wood equivalent | Penalty |
|---|---|---|---|
| Rib set, 100 mm pitch, 94 ribs | **4.10 kg** PA12 3 mm w/ 40% lightening | 0.91 kg Rohacell 3 mm + 2×80 g glass | **4.5×** |
| Same | 3.58 kg PA6-CF 2.5 mm | 1.05 kg 3 mm balsa | 3.4× |
| Same | 4.10 kg | 2.30 kg 1.5 mm birch ply | 1.8× |
| Skin panel, 100 mm support pitch, solid | 2.63 kg/m² printed sandwich 6 mm | **0.68 kg/m²** CFRP/Rohacell 2 mm | **3.9×** |
| Skin panel, solid 1.35 mm printed | 1.36 kg/m², **EI = 0.51 N·m/m** | 0.68 kg/m², **EI = 48.4 N·m/m** | 2× the mass at **1/95 the stiffness** |

[CALC] The last row is the one that ends the printed-skin discussion. A solid printed panel thin enough to be mass-competitive deflects **2.6 mm** between 100 mm supports under a 1,039 Pa suction load — five times the entire aerodynamic waviness budget (§6.1). Making it stiff enough (printed sandwich) costs 3.9× the mass.

### 5.7 Where printed parts are, and are not, appropriate

| Component | Printed? | Material | Reasoning, with numbers |
|---|---|---|---|
| **Spar caps** | **No** | — | 15× mass penalty [CALC §5.6a]; 231 kN cap force |
| **Shear web** | **No** | — | Shear-carrying primary structure; 6.99 kN root shear |
| **Wing skin (torsion box)** | **No** | — | ±1.14 mm print tolerance vs 0.51 mm step budget; 3.9× mass |
| **Ribs (non-primary, film or sandwich support)** | **Yes** | MJF PA12 (exterior UV/temp) or PA12-CF | Stress ~0.06 MPa, 170× below the creep test floor. Costs +3.2 kg vs foam ribs |
| **Wingtips** | **Yes** | MJF PA12 | Zero primary load; complex geometry; replaceable after a hard landing |
| **Fairings, wing-boom and boom-tail fillets, inspection covers** | **Yes** | MJF PA12 | Aerodynamic, not structural — but see the surface-finish requirement in §6.1 |
| **Cooling ducts, Meredith diffuser/nozzle** | **Yes** | PPS-CF or PA12 | PPS-CF HDT 252 °C covers the radiator core outlet [16][DS]; internal flow surfaces are not laminar-critical |
| **Control horns** | **Marginal** | PA12-CF, printed in-plane | Bearing loads are small, but Z-strength is 25 MPa [14][DS] and a horn failure is a control failure. **Use metal.** Print the *jig* that locates the metal horn |
| **Gimbal cradle** | **Yes, with an aluminium load frame** | PA12-CF shell + Al frame | 20 kg gimbal at 1 g = 0.12 MPa in a printed cradle (fine); at the 5–11 g airbag touchdown [1] it is 1,000–2,160 N transient, which must land on metal |
| **Avionics trays, wire routing, antenna mounts** | **Yes** | MJF PA12 | Ideal application |
| **Engine mount** | **No** | 4130 steel weldment or machined Al + elastomeric isolators | 33.6 N·m torque reaction at 17 kW/4,830 rpm; vibration fatigue; firewall temperature above every printable Tg except PPS/PEKK |
| **Fuel tank fittings** | **Qualified yes for PA12 only** | MJF PA12 | PA12 chemistry is the automotive fuel-line standard, and MJF PA12 is rated "excellent chemical resistance to oil, grease, hydrocarbons" [5][DS]. **But** powder-bed PA12 retains porosity and absorbs 1.5% water at saturation [5][DS] — every fuel-wetted printed part must be epoxy-sealed and pressure-tested. Main feed, drain and any fitting whose failure empties a tank: **metal** |
| **Parachute attach hardware** | **No** | Steel/Al | ≥5 × MTOW = 12.3 kN opening-shock path [1] |
| **Moulds, plugs, layup jigs, rib-location fixtures, drill jigs** | **Yes — this is the highest-value use on the programme** | PETG-CF / ASA / PC | See §5.8 |

### 5.8 The best use of 3D printing here is tooling, not parts

The premortem's mode #1 (30% of failure mass) is the budget, and its named trigger is "**quotes for wing tooling arrive at €9–14k, double the guess**" [1].

Printing attacks that line item directly:

- **Print the plug in segments, not the mould.** Only the outer surface needs accuracy; a segmented printed plug is skimmed with tooling putty, faired and polished, then a GRP female mould is laid up over it. The print's ±0.3% tolerance is absorbed by the skim coat.
- Material: PETG-CF (Tg ~80 °C) or ASA (HDT ~95 °C) is sufficient — the mould only has to hold shape at the 50–60 °C post-cure. PLA (Tg 60 °C) is not.
- **Print the rib-location and spar-alignment jigs.** For a build with 94 ribs to place within a fraction of a millimetre over 4.6 m, the jig is the difference between a wing and a banana. This is where printing earns its place on a solo-builder programme regardless of what the parts are made of.
- Cost anchor: MJF service pricing from **€0.29/cm³** [21][DS]; desktop FDM filament in PA12-CF/PA6-CF at €40–80/kg [17][DR].

Worked example: the 94-rib set is 4.10 kg / 1.04 g/cm³ = 3,942 cm³ → **€1,143 at bureau MJF** [CALC from 21], or **€165–330 in filament plus ~250–400 h of unattended desktop printer time** [EST]. A full printed skin set at 21 kg → 20,200 cm³ → **€5,860 bureau** — which is on its own a budget-ending number for a €60k programme.

---

## 6. Wing skin and surface quality — the crux

### 6.1 What the FX 63-137's laminar bucket actually requires at Re 0.6–1.1 M

Atmosphere at 4,000 m ISA: ρ = 0.8191 kg/m³, μ = 1.661×10⁻⁵ Pa·s, **ν = 2.028×10⁻⁵ m²/s** [CALC].

| Condition | V (m/s) | Re at root chord | Re at MAC | Re at tip |
|---|---|---|---|---|
| Loiter, heavy (128 km/h) | 35.62 | 1.02×10⁶ | 7.75×10⁵ | 4.58×10⁵ |
| Loiter, light (99 km/h) | 27.45 | 7.87×10⁵ | 5.97×10⁵ | 3.53×10⁵ |
| Transit (175 km/h) | 48.61 | 1.39×10⁶ | 1.06×10⁶ | 6.26×10⁵ |

**Admissible surface imperfections.** These scale as ν/V and are therefore *generous* at this speed and altitude — a point the "sailplanes need 0.1 mm" folklore obscures:

| Criterion | Basis | @ loiter (35.6 m/s) | @ transit (48.6 m/s) |
|---|---|---|---|
| Schlichting admissible roughness, Re_k = 100 on U∞ | classical | **0.057 mm** | 0.042 mm |
| Braslow & Knox critical roughness, Re_k = 600 | [22][M] | **0.342 mm** | 0.250 mm |
| **Forward-facing step, X-21 Re_h = 900** | [23][M] | **0.512 mm** | 0.375 mm |
| Aft-facing step, X-21 Re_h = 1,800 | [23][M] | 1.025 mm | 0.751 mm |
| Spanwise gap, X-21 Re_h = 15,000 | [23][M] | 8.54 mm | 6.26 mm |

[CALC from 22][23]

**Streamwise waviness — the Carmichael criterion.** From NASA's own restatement [23]:

> **h/λ = [ 59,000 · c · cos²Λ / Re_c^1.5 ]^0.5** — h = double-amplitude wave height, h, λ and c in inches

This form was verified against the source's own tabulated allowable for the Cessna P-210 (c ≈ 62 in, Re_c ≈ 1.1×10⁷ → h/λ = 0.01001 vs the paper's tabulated 0.0100) [24][M]. For ARGUS-7, unswept:

| Station | c (in) | Re_c @ loiter | **allowable h/λ, single wave** | ÷3 for multiple close-spaced waves [23] | h at λ = 50 mm |
|---|---|---|---|---|---|
| Root | 22.87 | 1.02×10⁶ | **0.0362** | 0.0121 | 1.81 / 0.60 mm |
| MAC | 17.36 | 7.75×10⁵ | **0.0388** | 0.0129 | 1.94 / 0.65 mm |
| Tip | 10.28 | 4.58×10⁵ | **0.0442** | 0.0147 | 2.21 / 0.74 mm |
| MAC @ transit | 17.36 | 1.06×10⁶ | 0.0307 | 0.0102 | 1.53 / 0.51 mm |

[CALC from 23]

**This is the single most useful result in the pack, and it is good news:** at Re 0.6–1.1 M the streamwise waviness budget is **h/λ ≈ 0.010–0.015 even on the conservative multiple-wave criterion**, i.e. **0.5–0.75 mm of wave depth over a 50 mm wavelength**. That is roughly 6× looser than the 0.1 mm (0.004″) rule of thumb quoted in the sailplane refinishing community [25][DR], because sailplanes run at 2–4× our chord Reynolds number and the allowable goes as Re^(−0.75).

### 6.2 What a hand-built composite surface actually achieves — measured

NASA measured surface waviness on the airframes it used for its natural-laminar-flow flight programme, with a 2-inch-base dial indicator, and tabulated it [24][M]:

| Airplane / surface | Construction | measured h/λ | λ (in) | h (mm, double amp.) | Allowable h/λ [24] |
|---|---|---|---|---|---|
| Rutan **VariEze**, right wing | **moldless full-depth foam core, homebuilt** | 0.0035 | 2.0 | 0.178 | 0.0100 |
| Rutan **Long-EZ**, right wing | moldless foam core, homebuilt | 0.0030 | 2.0 | 0.152 | 0.0100 |
| Rutan Long-EZ, canard | moldless foam core, homebuilt | 0.0046 | 1.75 | 0.204 | 0.0135 |
| Rutan VariEze, winglet | moldless foam core, homebuilt | 0.0045–0.0070 | 2.0–3.5 | 0.23–0.36 | 0.0125–0.0215 |
| Cessna P-210, upper surface | production aluminium | 0.0020 | 3.5 | 0.178 | 0.0100 |
| Bellanca Skyrocket, inboard | composite | 0.0015 | 2.0 | 0.076 | 0.0078 |

And the paper's summary conclusion: "**None of the measured heights of surface waviness exceeded the empirically predicted allowable surface waviness**" and "no discernible effects on transition due to surface waviness were observed" [24][M].

**Two things follow, and they matter:**

1. **A competently hand-built, moldless, garage-made composite wing measurably meets the laminar-flow waviness criterion** — at *higher* Reynolds numbers than ARGUS-7 flies. The VariEze/Long-EZ data is direct, measured evidence, on exactly the class of builder this programme has. The surface-quality bar is achievable without a factory.
2. Against ARGUS-7's allowable of h/λ ≈ 0.0121–0.0147 (multiple-wave), the demonstrated homebuilt standard of **0.0030–0.0046 has a 2.6–4.9× margin.**

**The honest caveat on the other side:** NASA also identifies "excessive waviness **between ribs and stringers**" as one of three named reasons the 1950s production aircraft failed to achieve laminar flow [24][M]. Rib-pitch waviness is a known NLF killer. That is the mechanism §6.3 has to confront.

### 6.3 Heat-shrink film over ribs

**Mass and material.** Oratex 6000: 170 µm thick modified polyester, **140–160 g/m²** (150–210 with backside coating), tensile 1,300–1,600 N/50 mm lengthwise, shrinkage 9–13%, melting point 250 °C, airtight, **fuel resistant**, non-flammable after application [26][DS]. Oratex 600: 120 µm, **92–122 g/m²**, tensile 750–1,050 N/50 mm [26][DS]. An independent builder comparison put an Oratex 6000 test panel at **12 g vs 20 g (light-coated Ceconite) vs 30 g (normally coated Ceconite)** for the same panel [26][M].

With adhesive and tapes, budget **~150 g/m²** installed. Against ~8.0 m² of wing wetted area that is **1.2 kg** — genuinely light, and about 1/5 of a moulded sandwich skin.

**So why does it fail here?** Not for the reason usually given. Four separate mechanisms, in order of severity:

**(1) Film cannot form the leading edge — at all.** A membrane spans chords of a circle. Over a surface of radius R with rib pitch s, the maximum deviation from true contour is s²/(8R). Near the nose of a 0.5 m-chord FX 63-137 the upper-surface radius is on the order of 10 mm; at s = 150 mm the deviation would be 281 mm. **Every fabric wing ever built therefore has a rigid D-nose**, and that D-nose covers the *entire* region where surface accuracy actually determines transition. A "film-covered wing" is a wing with a moulded or otherwise accurate nose skin plus a fabric aft section. **The tooling you were trying to avoid is still required.** [CALC]

**(2) Scalloping is a spanwise disturbance, and the favourable criteria do not apply to it.** Membrane bulge between ribs under pressure Δp with tension T per unit width is δ = Δp·s²/(8T):

| Δp | T = 500 N/m | T = 1,000 N/m | T = 2,000 N/m | T = 4,000 N/m |
|---|---|---|---|---|
| 520 Pa (C_p = −1.0), s = 100 mm | 1.30 mm | 0.65 mm | 0.33 mm | 0.16 mm |
| 520 Pa, s = 150 mm | 2.92 mm | 1.46 mm | 0.73 mm | 0.37 mm |
| 1,039 Pa (C_p = −2.0), s = 100 mm | 2.60 mm | 1.30 mm | 0.65 mm | 0.33 mm |
| 1,039 Pa, s = 150 mm | 5.85 mm | 2.92 mm | 1.46 mm | 0.73 mm |

[CALC]. Shrink-fabric working tension is not published by the manufacturers; 500–2,000 N/m is an [EST] bracket taken as 5–15% of Oratex 6000's 1,300 N/50 mm = 26,000 N/m breaking strength.

At the plausible middle of that table — 100 mm rib pitch, T = 1,000 N/m, C_p = −1 — the bulge is **0.65 mm at λ = 100 mm, i.e. h/λ = 0.0065**, which is *inside* the 0.0129 multiple-wave allowable. **On a naive reading of the streamwise criterion, film would pass.**

It does not pass, because **the criterion is the wrong one.** Carmichael's and Fage's criteria describe two-dimensional waves whose crests run *spanwise*, so the flow climbs over them [23][24]. Fabric scalloping produces ridges at each rib and valleys between, with crests running **chordwise** — the flow runs *along* them. That is a spanwise-periodic disturbance producing spanwise pressure gradients and spanwise-varying transition; it is a crossflow/3-D problem for which, as the NASA source states plainly, "**No criteria exist which fully address surface-imperfection-induced transition related to crossflow amplification**" [23][M]. The empirical record is the only guide, and it is one-directional: fabric wings do not achieve laminar flow, and NASA names rib-and-stringer waviness as a cause of the 1950s failures [24][M].

**(3) Surface texture.** Oratex is a woven modified polyester 120–170 µm thick [26][DS]. The admissible roughness at loiter is **0.057 mm = 57 µm** on the Schlichting criterion and 342 µm on the more permissive Braslow criterion [22][M]. The weave texture of a 170 µm woven fabric is of the same order as the tighter of these two limits. [EST — no measured weave roughness height was found; flagged as an open question, §13.]

**(4) Unsteadiness.** Aircraft fabric between ribs oscillates ("drums") in flight. An unsteady wall is a strong transition trigger and is not covered by any static waviness criterion at all. [EST]

**(5) The pressure recovery.** The FX 63-137 is a high-lift Wortmann section with a long, aggressive aft pressure recovery. Contour errors in the recovery region do not merely trip transition — they risk turbulent separation, which costs lift and C_m as well as drag. Film sits precisely there.

**Measured consequence of a rough wing on this section.** UIUC tested the FX 63-137 clean and with zigzag boundary-layer trips at 2% chord (upper) and 5% (lower), simulating leading-edge debris and erosion, at Re = 1–5×10⁵ [6][M]. Result: "**the maximum lift performance of the FX 63-137 suffers from the addition of simulated roughness. Overall the drop in C_l,max is 0.2**" [6][M]. That is the number used throughout §6.8 — and it is a genuinely nasty one, because ARGUS-7's loiter speed is **stall-constrained** at 1.15 V_s [1], so a C_Lmax loss goes straight into a higher loiter speed and a shorter mission.

**Verdict on film:** a legitimate skin for a low-wing-loading, non-laminar aircraft; wrong for a 64 kg/m², laminar-bucket-dependent wing. But see §11 — used *only aft of 55% chord*, over a properly-formed nose, the argument weakens considerably.

### 6.4 Moulded sandwich skin — the reference

Composition and areal mass, glider practice [CALC, component data from 27][DS]:

| Layer | g/m² |
|---|---|
| Outer ply, 93 g/m² carbon twill | 93 |
| Resin, vacuum-bagged at 40% resin content | 62 |
| Rohacell 51 IG-F, 2 mm (52 kg/m³) | 104 |
| Core surface resin uptake (fine-cell IG-F, "minimal") | 60 |
| Inner ply, 93 g/m² carbon + resin | 155 |
| **Sub-total, structural** | **474** |
| Filler + primer + white topcoat | 200–300 |
| **Total installed** | **≈ 720** |

Hand wet layup at 50–60% resin content instead of vacuum bagging adds ~130 g/m² → ~850 g/m².

Rohacell 51 IG-F: **52 ± 12 kg/m³**, compressive strength 0.9 MPa, compressive modulus 43 MPa, tensile 1.9 MPa, shear strength 0.8 MPa, shear modulus 19 MPa [27][DS].

**Why sandwich, when §2.4 showed the skin isn't strength-critical?** Because sandwich is the only cheap way to buy the *bending stiffness* that holds contour between ribs:

| Panel | EI (N·m per m width) | Deflection @ 100 mm span, 1,039 Pa | kg/m² |
|---|---|---|---|
| **CFRP/Rohacell 51, 2 mm core, 0.2 mm faces** | **48.4** | **0.028 mm** | **0.680** |
| CFRP/Rohacell 51, 3 mm core, 0.15 mm faces | 74.4 | 0.018 mm | 0.525 |
| 3 mm balsa + 1 ply 80 g glass | 13.5 | 0.100 mm | 0.740 |
| GRP solid 1.0 mm | 1.67 | 0.812 mm | 1.900 |
| CFRP solid 0.6 mm | 1.26 | 1.074 mm | 0.930 |
| Printed PA6-CF solid 2.0 mm | 2.95 | 0.458 mm | 2.180 |
| Printed PA12 solid 1.35 mm | 0.51 | **2.639 mm** | 1.364 |
| Printed PA12 sandwich 6 mm (1 mm skins, 15% core) | 31.7 | 0.043 mm | 2.626 |

[CALC] A 2 mm Rohacell sandwich is **95× stiffer than a solid carbon skin of similar weight** and **1,700× stiffer than an equal-mass printed panel**. This table is the whole skin argument in one place.

### 6.5 Printed skin panels

Ruled out on three independent grounds, any one of which is sufficient:

1. **Tolerance:** ±0.3% over the 380 mm build envelope = ±1.14 mm [5][DS], versus a 0.512 mm forward-facing-step budget [23][CALC].
2. **Joints:** ~52 panels per wing set, ~50 spanwise joints, each a potential step and each needing fill-and-fair anyway — at which point the print bought you nothing.
3. **Mass:** 2.63 kg/m² for a stiff-enough printed sandwich vs 0.68 kg/m² for CFRP/Rohacell → **+15.6 kg over 8 m² of skin**, on a 32.5 kg budget.

**Cost is a fourth:** 21 kg of MJF ≈ **€5,860** at €0.29/cm³ [21][DS][CALC].

If a printed panel *is* used somewhere (a fairing, a wingtip), it must be filled, primed and sanded like any other surface. The as-printed surface is Ra ≈ 2.5–11 µm for MJF [28][M] — which is within the roughness budget — but the *waviness* from warp and the *steps* at joints are not.

### 6.6 Moldless foam core (Rutan method)

The NASA data in §6.2 is a direct endorsement of this method's surface quality. Its problem here is mass and labour, not accuracy.

> **Correction (added post-publication, P1 CAD rebuild, fix round 2):** the
> "Gross wing volume 0.160 m³" below is the same §2.5 figure built on the
> 0.68 shape factor already corrected there — see the correction note at
> the head of §2.5. The true gross volume is 0.1426 m³ (142.6 L), which
> gives **~5.4 kg of core**, not 6.1 kg (a −0.68 kg change), and a
> corrected **Total wing ≈ 38.9 kg**, not 39.6 kg. This also flows into
> §10's build-option comparison table, Option E ("moldless foam core + wet
> layup + micro"): its quoted Wing total (39.59), kg/m² (10.15) and margin
> (+7.09, fails) all inherit the same stale constant. At ~38.9 kg, Option E
> would rank *below* Option C2 (39.24 kg) rather than above it — a ranking
> change, not just a rounding difference. The table itself is left
> unedited here (recomputing its "Primary (×1.18)" column for Option E
> requires re-deriving from this section's own structural method, which is
> beyond a constant-substitution fix); flagging for a dedicated follow-up
> pass rather than silently patching one cell of a multi-column table.

Gross wing volume 0.160 m³ [CALC]; at 38 kg/m³ blue/urethane foam that is **6.1 kg of core** — carried permanently, doing structural work only as a shear/stabilising medium. Add ~0.95 kg/m² of wet-layup skin and, critically, **0.55 kg/m² of micro/filler**, which is what it takes to fair a hot-wired core to contour. Total wing ≈ **39.6 kg** (§10) — the second-heaviest option, and the one with the highest labour.

At AR 22 with a 0.26 m tip chord, hot-wiring cores to the accuracy the NASA data assumes is also markedly harder than on a Long-EZ's fatter, shorter-span wing. [EST]

### 6.7 Skin option comparison

| Option | Installed mass | Skin area applied | Achievable waviness | C_D0 impact | Tooling needed | Cost |
|---|---|---|---|---|---|---|
| **Moulded CFRP/Rohacell sandwich, vacuum-bagged** | 0.72 kg/m² | full 8.0 m² | h/λ ≤ 0.003 (mould-limited) [EST from 24] | **baseline 0.020** | female moulds, €9–14k or printed plug | ~€1,200 materials |
| **Moldless foam core + wet layup + micro** | 0.95 + 0.55 kg/m² | full | h/λ 0.0030–0.0046 **measured** [24][M] | **0.021–0.023** | none (templates only) | ~€900 materials |
| **Printed MJF panels, filled & sanded** | 2.63 kg/m² | full | as good as you sand it | 0.020–0.022 | none | €5,900 print |
| **Printed MJF panels, as printed** | 2.63 kg/m² | full | ±1.14 mm; steps > budget | 0.024–0.027 | none | €5,900 print |
| **Heat-shrink film aft of 32% c** (D-nose to spar) | 0.15 kg/m² film + 0.74 kg/m² nose | 5.3 m² film + 2.7 m² nose | 3-D scalloping, no valid criterion | **0.023–0.027** | still needs the nose skin | ~€400 |
| **Heat-shrink film aft of 55% c** (extended nose) | 0.15 + 0.74 kg/m² | 3.5 m² film + 4.5 m² nose | nose accurate; film in turbulent flow only | **0.021–0.025** | still needs the nose skin | ~€700 |

C_D0 figures are built from the component parasite drag build-up in §6.8 and the transition-location model below; treat the ranges as [EST] with the lower bound [CALC].

**Transition-location model.** Section drag from a mixed laminar/turbulent flat plate with form factor FF = 1 + 2(t/c) + 60(t/c)⁴ = 1.295 at t/c = 0.137, at Re_MAC = 9×10⁵:

| x_tr | c_d | Δc_d vs 0.50 | resulting C_D0 |
|---|---|---|---|
| 0.55 | 0.00738 | −0.00044 | 0.0196 |
| **0.50 (baseline)** | **0.00782** | 0 | **0.0200** |
| 0.45 | 0.00826 | +0.00044 | 0.0204 |
| 0.40 | 0.00871 | +0.00089 | 0.0209 |
| **0.32 (D-nose to spar)** | 0.00944 | +0.00162 | **0.0216** |
| 0.10 | 0.01154 | +0.00372 | 0.0237 |
| **0.05 (tripped at LE)** | 0.01204 | +0.00422 | **0.0242** |

[CALC] **This is a lower bound.** It counts skin friction only. It does not count (a) the growth in pressure drag when a boundary layer that is turbulent from 5% chord enters the FX 63-137's aggressive aft recovery much thicker, (b) local separation over scallops, or (c) laminar-separation-bubble effects. A realistic band for a fully-tripped wing is therefore **0.024 (flat-plate floor) to 0.027 (with recovery thickening)** [EST].

**Where C_D0 = 0.020 comes from — component build-up, so the wing's share is visible:**

| Component | C_D0 contribution | Equivalent flat plate |
|---|---|---|
| Wing, laminar to 50% c | 0.00782 | 305 cm² |
| Fuselage pod 3.4 × 0.48 m | 0.00382 | 149 cm² |
| Twin booms 2 × 3.65 × 0.09 m | 0.00188 | 74 cm² |
| Inverted-V tail (0.42 m² panel) | 0.00124 | 49 cm² |
| Sub-total | 0.01477 | |
| + 8% interference | 0.01595 | |
| + cooling (3% of total C_D) [1] | 0.01730 | |
| **Residual to reach the report's 0.020** | **0.00270** | 105 cm² of antennas, skids, gaps, leakage |

[CALC] The build-up closes on the report's number with a plausible 105 cm² residual. **The wing is 39% of C_D0** — so wing surface quality moves about two-fifths of the aircraft's parasite drag, and nothing else the builder does to the skin matters as much.

### 6.8 The endurance ledger

Baseline: **112.8 h / 4.70 d** at C_D0 = 0.020, C_Lmax = 1.6 [1].

**Isolated sensitivities** [CALC]:

| Change | Endurance | Δ |
|---|---|---|
| C_D0 0.020 → 0.022 | 109.0 h | **−3.8 h** |
| C_D0 0.020 → 0.024 (report's "dirty") | 105.4 h | **−7.4 h** |
| C_D0 0.020 → 0.027 (fully tripped wing) | 100.4 h | **−12.4 h** |
| C_Lmax 1.6 → 1.5 | 110.4 h | −2.4 h |
| **C_Lmax 1.6 → 1.4** (the measured roughness penalty [6][M]) | 107.4 h | **−5.4 h** |
| +1 kg of structure (MTOW fixed, fuel displaced) | 111.3 h | **−1.5 h** |
| +4.9 kg of structure | 105.5 h | −7.3 h |
| +18.7 kg of structure | 86.2 h | −26.6 h |

**The mass-to-endurance exchange rate is 1.5 h per kilogram.** That is the single most useful design number in this pack: any material decision can be scored directly against it.

**Integrated ledger, mass and aero together** (structure mass overrun from §10 displaces fuel at fixed 250 kg MTOW):

| Build | Δ wing mass vs 32.5 kg | C_D0 | C_Lmax | Endurance | Δ vs 112.8 h |
|---|---|---|---|---|---|
| **A** moulded CFRP sandwich | −5.8 kg (margin) | 0.019–0.021 | 1.60 | 110.8–114.8 h | **−2.0 … +2.0 h** |
| **B** pultruded caps + moulded skin | −3.6 kg (margin) | 0.019–0.021 | 1.60 | 110.8–114.8 h | **−2.0 … +2.0 h** |
| **C3** pultruded caps + printed ribs + film aft of 55% c | +1.2 kg | 0.021–0.025 | 1.55 | 100.6–107.9 h | **−12.2 … −4.9 h** |
| **C2** tube spar + printed ribs + film aft of 55% c | +6.7 kg | 0.021–0.025 | 1.55 | 93.2–100.0 h | **−19.6 … −12.8 h** |
| **C** tube spar + printed ribs + film aft of 32% c | +4.9 kg | 0.023–0.027 | 1.45 | 89.5–96.2 h | **−23.3 … −16.6 h** |
| **E** moldless foam core + wet layup | +7.1 kg | 0.021–0.023 | 1.60 | 97.1–100.5 h | **−15.7 … −12.3 h** |
| **D** printed MJF skin panels | +18.7 kg | 0.020–0.022 | 1.60 | 83.2–86.2 h | **−29.6 … −26.6 h** |

[CALC] Negative mass deltas (margin) are not credited as extra fuel, since MTOW would more likely absorb it elsewhere.

---

## 7. Adhesives and joints

A rod-and-tube-and-print airframe is joint-dominated by construction. This section is therefore load-bearing for options C/C2/C3/D and much less so for A/B.

### 7.1 Adhesive data

**Hysol / Loctite EA 9394** — two-part RT-cure epoxy paste, the aerospace default for composite bonding and liquid shim [11][DS]:

| Property | Value |
|---|---|
| Density mixed | 1.36 g/mL |
| Tensile lap shear (ASTM D1002, 5 d @ 25 °C, PAA-treated 2024-T3) | **28.9 MPa @ 25 °C** |
| — at −55 °C | 22.7 MPa |
| — at 82 °C | 20.7 MPa (**−28%**) |
| — at 121 °C | 15.8 MPa |
| After 7 d in water @ 25 °C | 28.2 MPa (−4.7%) |
| **After 7 d in JP-4 fuel** | **28.9 MPa (no loss)** |
| After 7 d in hydraulic oil | 28.2 MPa |
| T-peel (ASTM D1876) | **5 lb/in = 22.2 N/25 mm** |
| Bell peel (ASTM D3167) | 20 lb/in = 89.0 N/25 mm |
| Bulk tensile / modulus | 46.0 MPa / 4,237 MPa |
| Compressive strength | 68.9 MPa |
| **Tg dry / wet** | **78 °C / 68 °C** |

Two things stand out. **Fuel and oil immunity is excellent** — directly relevant to a wet-wing build and to 122 h missions. **The peel strength is terrible** — 22 N/25 mm in T-peel against 28.9 MPa in shear. This is the governing design rule for the whole build:

> **Design every bonded joint to work in shear or compression. Never let a bondline see peel.**

A 25 mm-wide bond that carries 18 kN in shear carries **22 newtons** in peel. That is a factor of 800.

### 7.2 What fails first, in order

For a well-made composite-to-composite joint the failure sequence is:

1. **Peel at a joint edge** (22 N/25 mm) — where a flexible member meets a stiff one, e.g. a film-tensioned rib cap, a tube exiting a fitting, a skin at a rib flange.
2. **Interlaminar shear of the adherend**, not the adhesive: pultruded UD ILSS ≈ 100 MPa [8][DS] and roll-wrapped tube transverse tensile 181 MPa [4][DS], but a *tube* loaded through a bonded plug fails by circumferential peel of the outer plies long before either number.
3. **Adhesive shear** (28.9 MPa) — rarely the first failure in a competent joint.

**Practical consequence for a tube-based build:** a carbon tube bonded into a socket carries load by shear over the overlap, but the load path forces the outer plies to peel off the tube. The fix is the standard one: **overlap length ≥ 2 tube diameters, a scarfed/tapered adherend end to spread the shear peak, a controlled 0.15–0.25 mm bondline, and a circumferential over-wrap** of 2–3 plies of ±45 carbon or aramid tape at every tube-to-fitting joint. The over-wrap turns the peel case into a hoop-tension case.

### 7.3 Bonding to printed thermoplastics — the 6–10× penalty

This is where a printed-parts build gets structurally expensive, and it is well-documented:

| Substrate / adhesive | Lap shear | Source |
|---|---|---|
| PAA-treated 2024-T3 Al / EA 9394 | **28.9 MPa** | [11][DS] |
| **MJF PA12 / polyurethane adhesive (best performer tested)** | **5.0 ± 0.35 MPa** | [29][M] |
| **PA12 / cyanoacrylate (Loctite 401 + 770 primer), no plasma or flame** | **3.0 MPa** | [29][M] |
| PA12, after atmospheric plasma pre-treatment | "greatly enhanced" — value not stated | [29][M][UNV] |
| PA12, after chemical smoothing | **reduced** — smoothing is counter-productive for bonding | [29][M] |

Root cause is stated in the literature: **PA12 has a surface energy of ~40 dyn/cm and absorbs up to 3% moisture by mass**, producing a weak interfacial layer [29][M]. MJF PA12's datasheet water absorption is 1.5% at saturation [5][DS].

**The rule this produces:** a bond to a printed PA12 part carries **1/6 to 1/10** the load per unit area of a bond to a properly prepared composite or metal. Design printed-part bonds with 6–10× the area you would use elsewhere, and never put a printed part in a path where that area is unavailable.

**Does this actually bite for ribs?** No, and it should be said plainly. A rib at 100 mm pitch carries ~157.7 N at ultimate over ~2,400 mm² of bond land (two feet, front and rear spar) → **0.066 MPa**, which is 45× below even the untreated cyanoacrylate figure. [CALC] Printed ribs are fine. It bites hard for anything that concentrates load: fittings, horns, engine and parachute attachments.

### 7.4 Surface preparation — non-negotiable, and different for each adherend

| Adherend | Preparation |
|---|---|
| **Pultruded carbon** | **Sand with 220 grit and remove all dust.** Pultrusion uses internal mould release which migrates to the surface; the vendor states this explicitly [8][DS]. An unsanded pultruded surface is a release film |
| Roll-wrapped / filament-wound tube | Remove the peel-ply or abrade to a uniform matte; degrease with IPA (not acetone, which can attack partially-cured epoxy) |
| Moulded composite | Peel ply, torn off immediately before bonding — the best available prep |
| **Printed PA12** | Abrade + degrease + **atmospheric plasma or flame treatment** [29][M]. Do **not** chemically smooth a surface that is to be bonded [29][M] |
| Metal fittings | Abrade + degrease; for aluminium, phosphoric-acid anodise if achievable (the EA 9394 datasheet values are quoted on PAA-treated adherends [11][DS], so a hand-abraded bond will not reach 28.9 MPa) |
| **Carbon-to-metal anywhere** | Interpose a glass-fibre ply. Carbon is electrically conductive and galvanic corrosion of the metal is a real failure mode; anodising plus the epoxy layer is *sometimes* enough, glass is always enough [30][DS] |

### 7.5 The joint census — the argument the sponsor's preference has to answer

| Build | Structural joints in the wing |
|---|---|
| A / B moulded | 2 shell closeouts, 2 spar-to-skin bondlines, ~24 rib bonds, 1 root joint |
| C / C2 tube + printed ribs + film | 6–8 telescoped tube-spar joints (in the primary path), **94 rib-to-spar bonds**, ~94 rib-to-nose-skin bonds, film-to-rib and film-to-edge adhesion over ~5 m² of perimeter, 1 root joint |

[EST] The sponsor's build has roughly **8× the joint count**, of which a handful are in the primary bending path. That is where the "+1.2 kg of joints and bonds" in the §10 mass table comes from, and it is also where the *inspection* burden goes: 94 bondlines are 94 chances for a dry joint that no one can see.

---

## 8. Fatigue and environment

### 8.1 Spar fatigue is not a problem — say so and move on

At 1 g cruise the root moment is 16.18/5.7 = 2.84 kN·m → cap force 40.6 kN → **105 MPa** on a 385 mm² cap → **0.079% strain**. The report's gust case (Δn = 1.10 at 4,000 m [1]) cycles that by ±0.087%. [CALC]

Carbon/epoxy UD at 0.08% cyclic strain is, for practical purposes, fatigue-immune. A 122 h mission accumulates perhaps 10⁵–10⁶ gust cycles at strains an order of magnitude below any published knee in a CFRP S-N curve. **The spar cap is not the fatigue article.**

### 8.2 The fatigue articles are the parachute landings and the engine

- **Recovery:** 4.5 kJ touchdown, mean 5–11 g over a 0.2–0.3 m airbag/crush-keel stroke [1]. This is a low-cycle, high-load event repeated once per sortie. Over 50–100 recoveries it is the dominant damage accumulator for **bonded joints, fittings, and printed parts**, none of which have the composite spar's fatigue immunity. Adhesive fatigue is also much less forgiving than composite fatigue.
- **Engine:** a single- or twin-cylinder 250 cc at 4,830 rpm produces a 80.5 Hz firing excitation and 33.6 N·m of torque reaction. Everything within 1 m of the engine — mount, firewall, pod frames, fuel and oil fittings, and any printed part — sees continuous vibration for 122 h. **Printed thermoplastics have far worse fatigue behaviour than composites or metals and the datasheets do not report it** [UNV].

**Design consequences:** (a) instrument or at least inspect the primary bondlines after every hard recovery; (b) put nothing printed in the engine bay; (c) treat the gimbal cradle's *impact* path as metal even if its shell is printed.

### 8.3 Temperature

Covered in §5.3. Restated as requirements:

- White or very light exterior paint — **structural, not cosmetic** (66 °C white vs >104 °C black at 38 °C ambient [18][M]).
- Post-cure all RT-cure epoxy at 50–60 °C for ≥12 h; unpost-cured Tg 50–70 °C sits below the parked-in-sun surface temperature [19][DR].
- EA 9394 loses 28% of its lap shear at 82 °C [11][DS]; size hot bondlines on 20.7 MPa, not 28.9.
- Cruise at −5 to −15 °C is benign for all materials here; EA 9394 retains 22.7 MPa at −55 °C [11][DS]. Thermal cycling between −15 °C and +65 °C twice a day for 122 h is a bondline consideration where CTEs differ — carbon (~0–2 µm/m·K axially), Rohacell 51 IG-F (**4.71×10⁻⁵ /K** [27][DS]), PA12 (~1×10⁻⁴ /K). **The foam and the printed parts move 20–50× more than the carbon does.** Keep printed parts mechanically decoupled from long carbon members: bond at one point, slip-fit or flex-mount the rest.

### 8.4 Moisture

| Material | Saturated water uptake | Consequence |
|---|---|---|
| MJF PA12 | **1.50%** (0.70% hygroscopicity) [5][DS] | Modest property change; bondability degraded (§7.3) |
| PA6-CF (FDM) | **2.35%** at 25 °C/55% RH [15][DS] | "will experience a decrease in strength and stiffness after absorbing water" [15][DS]. General PA6 loses roughly 45% of its modulus between dry and conditioned [17][DR][UNV for the printed grade] |
| EA 9394 | — | Tg drops 78 → 68 °C wet; shear modulus 1,461 → 1,027 MPa wet (**−30%**) [11][DS] |
| SLS PA12 creep | — | Creep specimens conditioned by 24 h immersion at 60 °C were tested as a distinct "moist" case [20][M] |

**PA12 over PA6 for anything exposed.** The PA6-CF stiffness advantage on the datasheet (4,430 MPa) is a *dry* number and this aircraft lives outdoors.

### 8.5 UV

- **Unfilled PA12 and PA6 degrade under UV.** Carbon-filled grades are markedly better because carbon black is an effective UV blocker — a genuine argument for CF-filled prints on exterior parts, though it is not a licence to leave them unpainted. [EST/DR]
- **Epoxy degrades under UV** and must be paint- or gelcoat-protected — which the aircraft needs anyway for the temperature reason (§8.3).
- **Oratex 6000 is a modified polyester with an integral pigmented finish**, which is exactly its selling point: no dope, no UV topcoat, non-flammable after application [26][DS]. If film is used anywhere, this is the correct product.

### 8.6 Fuel and oil

- EA 9394 after 7 days in JP-4: **28.9 MPa, no measurable loss**; hydraulic oil 28.2 MPa [11][DS]. The adhesive is fine.
- MJF PA12: "**excellent chemical resistance to oil, grease, hydrocarbons**" [5][DS]. PA12 is the standard automotive fuel-line polymer, so the *chemistry* is right — but powder-bed parts retain porosity and must be sealed and pressure-tested before any fuel-wetted use [EST].
- Oratex 6000 is stated **fuel resistant** [26][DS].
- **Open risk:** the report specifies "mogas/Jet-A blend class" [1]. Ethanol content (E10) is aggressive to several polymers and to some epoxy fillers, and is not covered by the JP-4 data above. Flagged in §13.

---

## 9. Recommended material and method assignment

| Component | Recommendation | Why, with the number |
|---|---|---|
| **Spar caps** | **Pultruded UD carbon rectangular strip**, stacked and bonded into a machined cap channel; staggered butt splices ≥100 mm apart, none inboard of 30% semi-span; **consider intermediate/high-modulus pultrusion** if the deflection target tightens | E/ρ = 87.9 vs 77.8 for hand wet layup [CALC]; eliminates 40–80 h of the highest-consequence layup; €1,250–2,600 (§3.5) |
| **Shear web** | Rohacell 51 IG-F 3 mm core with ±45 CFRP faces (0.3 mm each), bonded between the caps | 1.00 mm of ±45 at τ = 100 MPa satisfies the 6.99 kN root shear; sandwich adds stability. ~0.8 kg [CALC] |
| **Wing skin** | **Moulded CFRP/Rohacell 51 sandwich, 2 mm core, 0.2 mm faces, vacuum-bagged**, in female moulds taken off a **3D-printed segmented plug** | 0.72 kg/m²; EI = 48.4 N·m/m → 0.028 mm deflection between supports; 95× the stiffness of an equal-mass solid skin [CALC] |
| **Ribs** | **Printed MJF PA12** at ~400 mm pitch (moulded-skin build), specified with build orientation on the drawing | Rib stress 0.06 MPa, 170× below the creep-test floor. 0.24 kg at 400 mm pitch. This is where the sponsor's preference is simply free |
| **Booms** | **COTS carbon tube, 100–110 mm OD × ~2.5 mm wall, mixed UD/±45 layup specified**, one-piece, with circumferentially over-wrapped end fittings | Strength margin 4×; the driver is 93 mm tip deflection and 1.9° twist [CALC]. 7.8–9.5 kg for two. Larger diameter costs only 0.83 h of endurance and buys 48% more stiffness per kg |
| **Tail (inverted-V)** | Moulded CFRP/Rohacell sandwich, foam-core moulded panels; **printed PA12 tip caps and boom-junction fillets** | Panel area 0.42 m²; the tail is far below the wing's Reynolds number and its surface quality matters much less — but it is a flutter article, so build it stiff |
| **Fuselage pod** | Moulded CFRP/Rohacell sandwich shells from printed-plug moulds; **printed PA12 internal trays, ducts, brackets, antenna mounts** | Pod C_D0 share 0.00382 (19%); it is not laminar-critical over most of its length but its nose is. Printed internals are ideal — no load, complex geometry, one-off |
| **Fittings (root joint, spar carry-through, hinge and control brackets)** | **Metal.** 7075-T6 or 4130; glass-ply isolation at every carbon interface | 231 kN cap force through the root joint; galvanic isolation mandatory [30][DS] |
| **Engine mount** | **4130 steel weldment or machined aluminium, elastomeric isolators** | 33.6 N·m torque reaction, 80.5 Hz excitation, bay temperature above every printable Tg except PPS/PEKK |
| **Gimbal mount** | **Aluminium load frame + printed PA12-CF shell/cradle + elastomeric isolation** | 20 kg × (5–11 g) = 1,000–2,160 N transient at recovery [1] must land on metal; the printed shell adds compliance and geometry for free |
| **Fuel system** | Integral sealed bays where volume allows, bladders otherwise; **printed PA12 for vent/return fittings only, sealed and pressure-tested; metal for feed and drain** | PA12 is the right chemistry [5][DS]; powder-bed porosity is the disqualifier for anything whose failure empties a tank |
| **Parachute attachment** | **Metal, no exceptions** | ≥5 × MTOW = 12.3 kN [1] |
| **Tooling: plugs, moulds, jigs, drill fixtures** | **3D-printed PETG-CF / ASA, skimmed and faired** | Attacks premortem failure mode #1 directly: the €9–14k wing-tooling quote [1]. The single highest-leverage use of printing on this programme |
| **Finish** | **White or very light**, filled and sanded, post-cured | 66 °C white vs >104 °C black at 38 °C ambient [18][M]; RT-cure epoxy Tg 50–70 °C [19][DR] |
| **Adhesive** | EA 9394 (or equivalent RT-cure epoxy paste) throughout; controlled 0.15–0.25 mm bondline; scarfed adherends; every joint in shear | 28.9 MPa shear vs **22 N/25 mm peel** [11][DS] |

---

## 10. Revised wing mass — does it close?

Method: primary structure from §2 and §6, multiplied by **1.18** for manufacturing growth (excess resin, adhesive fillets, local doublers, inspection reinforcement, tip weights) [EST — a standard first-article factor], then a common set of items the report's 32.5 kg budget must also cover:

- flaperons **2.80 kg** (≈5.5 m of surface at 0.5 kg/m)
- root/centre joint fittings **4.00 kg** (231 kN through a demountable joint)
- systems: 6–8 servos, linkages, wiring, pitot/AoA **2.00 kg**
- fuel tankage 3.0 kg (integral sealed) / 5.0–6.5 kg (bladders, needed where a bonded/printed interior cannot be sealed)
- paint 0.30 kg/m² of wetted area

| Option | Primary (×1.18) | Wing total | kg/m² | vs 32.5 kg |
|---|---|---|---|---|
| **A** moulded CFRP sandwich, female moulds | 12.50 | **26.70** | 6.85 | **−5.80 (closes)** |
| **B** pultruded strip caps + moulded sandwich skin | 14.68 | **28.88** | 7.40 | **−3.62 (closes)** |
| **C3** pultruded caps + printed ribs + film aft of 55% c | 18.58 | **33.73** | 8.65 | **+1.23 (marginal)** |
| **C** COTS tube spar + printed ribs + film aft of 32% c | 21.32 | **37.41** | 9.59 | **+4.91 (fails)** |
| **C2** COTS tube spar + printed ribs + film aft of 55% c | 22.59 | **39.24** | 10.06 | **+6.74 (fails)** |
| **E** moldless foam core + wet layup + micro | 20.99 | **39.59** | 10.15 | **+7.09 (fails)** |
| **D** printed MJF skin panels + pultruded caps | 37.02 | **51.22** | 13.13 | **+18.72 (fails badly)** |

[CALC] Reference points: the report's budget is 32.5 kg = 8.33 kg/m²; the ASW 27B measured 12.9 kg/m² [1]. Note the ASW 27B comparison flatters us — that wing carries roughly 4.5× ARGUS-7's root bending moment (500 kg at +8 g ultimate over a 15 m span) with water ballast and airbrakes, so 12.9 kg/m² is not a target to aim at, it is an upper bound on plausibility.

**Answers, plainly:**

- **The recommended build (B) closes with 3.6 kg to spare.** With the report's own conservative cap basis restored (§2.2, +5.9 kg) it still closes at 34.8 kg — 2.3 kg over — which is why §2.2 matters: the report's own conservatism is the difference between closing and not.
- **The sponsor's full preference (C) does not close.** It misses by 4.9 kg, and that is before the +20–30% penalty for a stepped rather than ideally-tapered tube spar (§4.3), which would push it to +6.9 to +7.6 kg.
- **The hybrid (C3) is within 1.2 kg** — inside the noise of a first-article mass estimate. It is a live option.
- **Printed skins (D) miss by 18.7 kg**, which is 58% of the entire wing budget. There is no version of this that closes.

**Every one of these numbers deserves a caveat:** the ×1.18 growth factor and the six common line items are [EST]. They are the same for every option, so the *rankings* are robust even if the absolute values move. Weigh the first set of parts.

---

## 11. Verdict on "carbon fibre rods and tubes and 3D printed parts as much as possible"

### Where the preference is right

**1. Pultruded carbon for spar caps — right, and for a better reason than usually given.** The material is real (1,682 MPa compression, 133.8 GPa, Vf 60–65%, two independent vendors agreeing), it matches prepreg on specific stiffness, and it deletes the single most dangerous layup on the aircraft. On a solo-builder programme this is the best €1,250–2,600 in the build. **Use rectangular strip, not round rod** (§3.3), and **do not butt-splice inboard of 30% semi-span** (§3.4).

**2. COTS tube for the booms — right.** The booms are stiffness-, not strength-critical, with a 4× strength margin. Specify the layup (mixed UD/±45); do not buy generic twill.

**3. Printed ribs — right, at a price.** Rib stress is 0.06 MPa, 170× below the creep-test floor. The penalty is mass (4.5× vs foam ribs) and joint count, not integrity.

**4. Printed tooling, jigs and fixtures — right, and under-used.** This is the highest-leverage application of printing on the programme, because it attacks the highest-probability failure mode in the premortem (the €9–14k wing-tooling quote) rather than the airframe.

### Where the preference is wrong

**1. Tube as the wing spar — wrong by a clean geometric factor of 2.07×.** A circle cannot compete with a cap-and-web spar in a 12%-thick wing. Cost: 3.8–6.5 kg, i.e. 5.7–9.7 h of endurance, plus 6–8 telescoping joints in the primary bending path.

**2. Printed skin panels — wrong on four independent grounds**, any one sufficient: ±1.14 mm print tolerance against a 0.512 mm step budget; 52 panels and ~50 joints; 3.9× the mass of the sandwich equivalent (+15.6 kg); €5,860 in print cost.

**3. Film skin over ribs — wrong, but not for the reason usually cited.** The streamwise waviness criteria actually give film a pass at these Reynolds numbers. It fails because (a) film cannot form the leading edge, so the tooling it was meant to avoid is still required; (b) its scalloping is a spanwise 3-D disturbance for which no favourable criterion exists and the empirical record is uniformly negative; (c) its 120–170 µm woven texture is comparable to the 57 µm admissible roughness height; (d) it sits in the FX 63-137's aggressive pressure recovery, where contour errors cost separation, not just transition.

**4. Printed parts anywhere hot, anywhere concentrated, anywhere sustained-loaded.** Engine mount, parachute attachment, control horns, main fuel fittings, and any bond that must carry more than ~1 MPa on a printed adherend.

### The endurance cost if the preference is followed everywhere

**Option C — tube spar, printed ribs, film aft of 32% chord: 89.5–96.2 h against a 112.8 h baseline. That is −16.6 to −23.3 hours, or 0.69 to 0.97 days.**

Decomposed, so you can see where it goes:

| Contribution | Hours |
|---|---|
| Parasite drag, C_D0 0.020 → 0.023–0.027 | −5.7 to −12.4 |
| C_Lmax 1.6 → 1.45, measured roughness penalty [6][M], raising the stall-constrained loiter speed | −3.8 |
| +4.9 kg of structure displacing fuel at 1.5 h/kg | −7.3 |
| **Total** | **−16.6 to −23.3** |

**So: yes, roughly a day — but the report's own "dirty C_D0 = 0.024" number would have predicted only −7.4 h.** The report understates the penalty by more than half, because its sensitivity table treats C_D0 in isolation and the real mechanism is three-way.

**And what it buys.** Roughly **350 hours of builder time (~35%)** and the **€9–14k tooling line item** (§12). On a programme whose highest-probability failure mode is the budget and whose second-highest is builder capacity [1], that is not nothing. It is a legitimate trade, and someone might legitimately take it — the 4.7 d spec becoming a 3.8–4.0 d spec.

But the premortem already says what happens next: "the specification is quietly re-baselined to '4 days', which existing platforms already do — the project's reason to exist evaporates" [1]. **The endurance is the product.** Spending it to save build time is spending the thing you are building.

### The recommendation

**Take options B and C3 seriously; take C, D and E off the table.**

- **B (pultruded caps + moulded sandwich skin + printed ribs + COTS tube booms + printed tooling)** is the recommendation. It closes the mass budget with 3.6 kg to spare, holds C_D0 at 0.020, and adopts the sponsor's preference everywhere it is actually right.
- **C3 (pultruded caps + accurate skin forward of 55% chord + printed ribs + film aft of 55%)** is the honest fallback if the mould programme proves unaffordable. It costs 4.9–12.2 h and lands 1.2 kg over budget. Its virtue is that the accurate skin covers the whole laminar run, so the film only ever sits in flow that is already turbulent. **It should be flight-tested, not argued about** — a tufted or IR-imaged transition survey on the first wing would settle it in one sortie.

---

## 12. Build effort for a solo builder, per approach

All figures are [EST], built from task-level estimates and calibrated against published homebuilt totals (Pro-Composites Personal Cruiser ~800 h, Team Tango Tango 2 ~1,000 h for complete aircraft [31][DR]). They cover **the wing only** — the pod, booms, tail, systems and engine are excluded. Print time is machine time, not builder time, and is listed separately because it is the one resource a solo builder can genuinely parallelise.

| Task | **A/B moulded** | **C/C2 tube + printed ribs + film** | **C3 hybrid** | **E moldless foam** | **D printed skin** |
|---|---|---|---|---|---|
| CAD, lofting, structural layout | 80–150 | 100–200 (94 ribs; 30–60 if scripted parametrically) | 100–200 | 60–120 | 150–300 |
| Plug fabrication (printed segments, skim, fair, polish) | 150–300 | 100–200 (nose only) | 130–260 | 0 | 0 |
| Female moulds from plugs | 120–250 | 80–160 (nose only) | 100–200 | 0 | 0 |
| Skin layup and cure | 80–140 | 30–60 (nose only) | 55–100 | 80–140 | 0 |
| Spar caps + web | 40–80 | 20–40 (bond tube sections) | 40–80 | 40–80 | 40–80 |
| Rib fabrication / post-processing | 10–20 | 30–60 | 30–60 | 0 (hot-wire cores 60–120) | 25–50 |
| Rib installation and bonding | 15–30 | 40–75 (94 bonds) | 40–75 | 0 | 25–45 |
| Skin/panel installation, film covering | — | 30–60 | 25–50 | — | 100–200 |
| Close-out, flaperons, TE, edging | 100–180 | 60–100 | 80–140 | 100–180 | 90–160 |
| Fit-out: tanks, servos, wiring | 80–140 | 100–160 | 90–150 | 80–140 | 80–140 |
| Fill, sand, prime, paint | 80–150 | 30–60 | 60–110 | **250–500** | 120–220 |
| **Builder hours (wing)** | **755–1,440** | **520–1,075** | **750–1,425** | **670–1,280** | **630–1,195** |
| **Midpoint** | **≈1,100** | **≈800** | **≈1,090** | **≈975** | **≈915** |
| Unattended print time | 200–400 h (tooling + ribs) | 500–900 h | 400–800 h | 0 | **2,500–5,000 h** |
| Tooling cash | €9–14k quoted [1], or **€2–4k printed-plug route** | €1–3k (nose mould only) | €1.5–4k | €0.3–0.8k (templates, hot wire) | €0 |
| Print/material cash (wing) | €1.3–2.9k | €1.4–2.5k | €1.5–3.0k | €0.9–1.5k | **€6–7k** |

**Readings:**

1. **The sponsor's build genuinely does save time — about 300 hours, ~27%.** That is real and should not be dismissed. It also removes the tooling procurement dependency, which is the premortem's mode #6 trigger (the contractor slip).
2. **The printed-plug route removes most of the tooling advantage.** If the €9–14k mould quote is replaced by €2–4k of printed plug plus builder fairing time, option A/B's cash disadvantage largely evaporates and only ~300 h of labour separates the routes.
3. **Moldless foam (E) is a trap for this aircraft.** Its 250–500 h of filling and sanding is the largest single line item in the table, and at AR 22 with a 0.26 m tip chord it is worse than the Long-EZ precedent implies.
4. **Printed skins (D) consume 2,500–5,000 h of print time.** On one desktop machine that is 4–8 months of continuous printing; at a bureau it is €6–7k. Neither fits a €60k / 18-month programme.

---

## 13. Open questions

**Aerodynamic**

1. **The clean C_D0 = 0.020 baseline is itself unverified at this Reynolds number.** The flat-plate transition model in §6.7 ignores laminar-separation-bubble drag, and UIUC's measurements show the FX 63-137 has a pronounced "high-drag knee" and non-monotonic Re behaviour below 5×10⁵ [6][M] — which is exactly where the tip sits at light-weight loiter (Re 3.5×10⁵). **Obtain the Stuttgart Profilkatalog or UIUC tabulated polars for FX 63-137 at Re 0.5–1.5×10⁶, smooth and tripped**, before the C_D0 band is treated as settled. This is a data-purchase problem, not a research problem.
2. **Where does transition actually occur on this section at C_L = 1.21?** The entire film-vs-skin argument turns on it. Assumed 45–55% chord [EST]. Settle it with XFOIL/RFOIL at the operating Re *and* with a tufted or IR transition survey on the first wing.
3. **Weave roughness height of Oratex 6000** — not published. Needs a profilometer measurement against the 57 µm admissible roughness [26][DS][UNV].
4. **Shrink-fabric working tension after heat-shrinking** — not published by Lanitz-Prena. The §6.3 bulge table spans a 4× range because of it. One tension measurement on a shrunk test panel collapses that uncertainty [UNV].

**Structural**

5. **Is the wing deflection acceptable at 14.2% of semi-span at limit load?** This pack flags it (§2.3) but does not resolve it. It needs an aeroelastic look — divergence, flaperon reversal, and the effect of a 4.9° tip washout change at 1 g on the spanwise loading the caps were sized for.
6. **Continuous-length pultruded strip:** confirm minimum order quantity and price for ≥5 m continuous rectangular strip from DPP/Van Dijk or Compositesplaza. If a 5 m mill order is affordable, the splice problem in §3.4 disappears entirely and option B gets simpler.
7. **Coupon-test the actual boom tube.** Vendor-quoted compressive strengths that exceed tensile ([4][7]) indicate solver output rather than test. One four-point bend and one torsion test on a 300 mm offcut.
8. **The wing cannot hold the fuel (§2.5, corrected): ~50–64 L usable against 120 L required** — see the correction note at the head of §2.5 (the 56–72 L figure quoted here in earlier drafts used a since-corrected 0.68 shape factor; ~50–64 L is the current figure). This must be resolved before the skin architecture is frozen, because sealed integral tanks and a bonded printed-rib interior are difficult to combine.

**Materials and process**

9. **Fatigue data for printed thermoplastics under 80 Hz engine excitation** — absent from every datasheet consulted. Anything printed within 1 m of the engine is [UNV].
10. **Ethanol (E10) compatibility** of the printed PA12 fittings, the bondlines, and the tank sealant. The EA 9394 data covers JP-4 only [11][DS]; the report specifies "mogas/Jet-A blend class" [1].
11. **Plasma-treated PA12 bond strength** — the literature says "greatly enhanced" without a number [29][M]. If a printed part must ever carry >1 MPa on a bondline, this needs a measured value.
12. **PA6-CF wet property retention** for the printed grade specifically. The manufacturer states there is a loss but publishes no number [15][DS].

**Programme**

13. **Cost and hours to print and fair a segmented wing plug.** §12 estimates €2–4k and 150–300 h. This is the number that decides whether the €9–14k tooling quote in the premortem is avoidable, and it can be settled by printing and fairing a 600 mm test segment for a few hundred euros. **Do this first — it is the cheapest decisive experiment in the whole materials programme.**

---

## 14. Sources

| # | Source | Type |
|---|---|---|
| [1] | `docs/argus7_design_report.md` v1.0, 2026-08-20 (ARGUS-7 Engineering Design Report, incl. §3 mass budget, §4 aero, §5 structures, Annex A premortem, Appendix C assumptions register) | project document |
| [2] | Rock West Composites, P/N 47312-L72, "Rod – Pultruded Carbon Fiber – 0.432 × 72 inch", product datasheet and engineering property table — https://www.rockwestcomposites.com/47312-l72.html | [DS] |
| [3] | Compositesplaza BV (Helmond, NL), "Technical Data Sheet: Compositesplaza pultrusion profiles", v01, 30-10-2017 — https://compositesplaza.com/wp-content/uploads/product-downloads/technical_data_sheet_pultrusion_profiles_version_01_30102017.pdf | [DS] |
| [4] | Rock West Composites, P/N 45285, "2×2 Twill Fabric Carbon Fiber Tube 3.00″", roll-wrapped, engineering property table — https://www.rockwestcomposites.com/45285.html | [DS] |
| [5] | HP Multi Jet Fusion Nylon PA12, Technical Datasheet v2.1 (Weerg/HP) — https://www.weerg.com/hubfs/Datasheets/Datasheets%202024/ENG/EN_NylonPA12.pdf | [DS] |
| [6] | M. S. Selig & B. D. McGranahan, "Wind Tunnel Aerodynamic Tests of Six Airfoils for Use on Small Wind Turbines", AIAA 2004-1188 (FX 63-137 clean and with zigzag trips at 2%/5% chord, Re 1–5×10⁵) — https://m-selig.ae.illinois.edu/pubs/SeligMcGranahan-2004-AIAA-2004-1188.pdf | [M] |
| [7] | Rock West Composites, P/N 35165-U, "Tube – Stock – Filament Wound – Unsanded – 2.875 × 3.155 in (up to 15 ft)", engineering property table — https://www.rockwestcomposites.com/35165-u.html | [DS] |
| [8] | R&G Faserverbundwerkstoffe GmbH, "CARBON fibre rods pultruded round (DPP™ / R&G)" and rectangular-rod catalogue (DPP = Van Dijk Pultrusion Products, NL) — https://www.r-g.de/en/art/700006 | [DS] |
| [9] | CompositesWorld, "Wind blade spar caps: Pultruded to perfection?" — https://www.compositesworld.com/articles/wind-blade-spar-caps-pultruded-to-perfection | [DR] |
| [10] | Sailplane/light-aircraft spar-cap design practice: "a high tensile fibre / tough resin system can be designed for 900 MPa compression strength at ultimate load, with fracture stress above 1000 MPa … the main spar of a glider is quite well protected against impact and without stress raisers" — soaring/homebuilt engineering literature | [DR][UNV — secondary attribution] |
| [11] | Henkel Aerospace, "Hysol® EA 9394 Epoxy Paste Adhesive", technical datasheet — https://exdron.co.il/Exdron-Pdf/Loctite_Hysol_EA9394.pdf | [DS] |
| [12] | Clearwater Composites, "Properties of Carbon Fiber — Properties of Common Carbon Fiber Laminate Designs vs. Metals" — https://www.clearwatercomposites.com/resources/properties-of-carbon-fiber/ | [DS] |
| [13] | CarbonWebshop 90 mm carbon tube range and marketplace listings for 90 × 86 mm roll-wrapped tube — https://www.carbonwebshop.com/carbon-fiber-tubes/carbon-fiber-tubes-90mm/ | [UNV] |
| [14] | EOS GmbH, "CarbonMide PA12-CF" material datasheet (ISO 527-1/-2, ISO 179) — https://www.sculpteo.com/media/imagecontent/CarbonMide.pdf | [DS] |
| [15] | Bambu Lab, "Bambu Filament Technical Data Sheet V3.0 — PA6-CF" — https://wiki.bambulab.com/filament-acc/petcf-ppacf/c750bddfb8e44af6ae9f7dd9625fa458.pdf | [DS] |
| [16] | Polymaker Fiberon PPS-CF10 product data — https://fiberon.polymaker.com/product/pps-cf10/ | [DS] |
| [17] | Aggregated FDM filament vendor data for PA12-CF, PETG-CF and PPS-CF (Polymaker, Raise3D, UltiMaker, Flashforge, Weerg) | [DR][UNV where ranges are given] |
| [18] | Composite airframe solar heating and the white-paint requirement: measured 150 °F (66 °C) white vs >220 °F (>104 °C) black FRP surface at 100 °F (38 °C) ambient; glider epoxy Tg ≈ 190 °F (88 °C) — rec.aviation.soaring / rec.aviation.homebuilt engineering discussion | [M][DR — secondary reporting of a builder measurement] |
| [19] | Room-temperature-cure epoxy Tg and post-cure behaviour: Tg limited by cure temperature, RT systems reaching ~70 °C; post-cure 12–24 h above Tg raising Tg 25–30% — Master Bond technical notes; MDPI *Polymers* 15(2):252 (2023) | [DR] |
| [20] | "Creep Behaviour of Polyamide in Selective Laser Sintering", Solid Freeform Fabrication Symposium proceedings, Univ. of Texas repository (1,000 h tests at 5/10/15/20/35 MPa; 23/60/100 °C; 10 MPa @100 h → 1.7%/2.5%/3.9%) — https://repositories.lib.utexas.edu/server/api/core/bitstreams/d9beaf74-76f1-42f0-bc25-a13e71ddbc72/content | [M] |
| [21] | HP 3D Print Europe, MJF PA12 service pricing from €0.29/cm³ — https://hp3dprint.eu/3d-materials-finishes-pricing/ | [DS] |
| [22] | A. L. Braslow & E. C. Knox, critical roughness Reynolds number Re_k ≈ 600 for fully turbulent flow; Schlichting admissible-roughness criterion Re_k ≈ 100 on freestream velocity — NASA roughness-effects literature, incl. https://ntrs.nasa.gov/api/citations/19660023725/downloads/19660023725.pdf | [M] |
| [23] | B. J. Holmes, C. J. Obara, G. L. Martin & C. S. Domack, "Manufacturing Requirements" (NASA Langley / PRC Kentron), N88-23744 — contains the Fage and Carmichael waviness criteria, the X-21 step and gap tolerances (Re_h = 900 forward-facing, 1,800 aft-facing, 15,000 gap), and the multiple-wave ×1/3 factor — https://ntrs.nasa.gov/api/citations/19880014361/downloads/19880014361.pdf | [M] |
| [24] | B. J. Holmes, C. J. Obara & L. P. Yip, "Natural Laminar Flow Experiments on Modern Airplane Surfaces", NASA TP-2256, June 1984 — Table A1 measured indicated waviness on VariEze, Long-EZ, Cessna P-210 and Bellanca Skyrocket, with allowable h/λ | [M] |
| [25] | Sailplane refinishing practice: waviness gauge reading of 0.004″ (≈0.1 mm) or less considered acceptable — rec.aviation.soaring | [DR] |
| [26] | Lanitz-Prena / BetterAircraftFabric, "Oratex® Specifications and Technical Data" (Oratex 6000 and 600) — https://www.betteraircraftfabric.com/specifications.html | [DS] |
| [27] | Evonik Operations GmbH, "ROHACELL® IG-F Product Information", April 2022 — https://products.evonik.com/assets/35/34/ROHACELL_IG_F_2022_April_EN_243534.pdf | [DS] |
| [28] | MJF PA12 surface roughness: Ra ≈ 11 µm along build direction; Ra 2.54 ± 0.42 to 10.29 ± 2.81 µm after glass-bead blasting — MJF/SLS comparison literature (ScienceDirect S1526612518315123; S221486042031085X) | [M] |
| [29] | Adhesive bonding of powder-bed PA12: MJF PA12 with polyurethane adhesive 5.0 ± 0.35 MPa; Loctite 401+770 3.0 MPa untreated; PA12 surface energy ~40 dyn/cm, up to 3% moisture uptake; plasma pre-treatment beneficial, chemical smoothing detrimental — *Scientific Reports* s41598-025-32559-w; *Polymers* 17(22):3020 | [M] |
| [30] | Clearwater Composites, "Carbon Fiber Tube FAQ — Galvanic Corrosion" (insulate carbon from metal with fibreglass) — https://www.clearwatercomposites.com/resources/faq/carbon-fiber-tubing/ | [DS] |
| [31] | Homebuilt composite aircraft build-time references: Pro-Composites Personal Cruiser ~800 h; Team Tango Tango 2 ~1,000 h (complete aircraft) — Wikipedia / kit manufacturer figures | [DR] |

---

## Appendix — reproducibility

Every `[CALC]` figure in this pack derives from the equations stated inline plus the report's own geometry (`design/argus7_v1.yaml`: S = 3.9 m², AR = 22, taper 0.45, t/c 0.137, C_D0 0.020, e 0.85, C_Lmax 1.6, MTOW 250 kg, fuel 101.5 kg). The five calculation groups are:

1. **Bending and cap sizing** — M(y) = w(s−y)²/2 with w = MTOW·g·n_ult/(2s); A(y) = M(y)/(h(y)·σ); h(y) = 0.1205·c(y); mass = 2ρ∫(A_t+A_c)dy.
2. **Deflection** — double integration of M(y)/EI(y) with EI(y) = E·(A_t+A_c)/2·h(y)².
3. **Endurance** — step integration from 250 kg to (148.5 + Δm) kg at C_L = C_Lmax/1.15², V = √(2W/ρSC_L), P_shaft = ½ρV³SC_D/η_p + P_el/η_alt, fuel flow = BSFC·P_shaft. Validated against the report's own C_D0 = 0.016 sensitivity to within 0.05%.
4. **Surface criteria** — Re_k·ν/U∞ for roughness and steps; h/λ = √(59,000·c·cos²Λ/Re_c^1.5) for waviness (h, λ, c in inches), validated against NASA's own tabulated Cessna P-210 allowable to 4 significant figures.
5. **Panel stiffness and membrane bulge** — δ = 5wL⁴/(384·EI) for supported panels; δ = Δp·s²/(8T) for membranes.

Anyone re-deriving these should get the same answers; where they do not, the discrepancy is more interesting than the number.
