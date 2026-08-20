# Cross-check audit: independent re-derivation of the ARGUS-7 v2.0 challenger

**Date:** 2026-08-20 · **Role:** independent cross-check auditor, per
`2026-08-20-gauntlet-preregistration.md` §"Judging protocol" · **Posture:** the
challenger is assumed wrong until shown otherwise.

Every number below was re-derived from the design variables with my own code:
my own ISA from the ICAO defining constants, my own adaptive-quadrature Breguet
integration, my own AVL decks, my own NeuralFoil runs, my own shoelace
integration of the pinned FX 63-137 coordinates. `argus7.mission.sim` was not
called. Where I agree with the repository I say so; where I do not, the
discrepancy is the finding.

**Verdict: DO NOT ADOPT. G2 fails as recorded, G6 fails, G7 fails.** The gates
are conjunctive. The endurance *improvement* is real and survives every
correction I can justify — but it is not 7.14 days, and this is not the design
that delivers it.

---

## 1. The endurance re-derives exactly. That is not the same as being right.

| Case | Repository | My independent derivation | Δ |
|---|---|---|---|
| Champion, published polar (C_D0 0.020, e 0.85) | 112.8 h (report) | **112.977 h** | +0.16% |
| Champion, coupled model's own aero | 119.414 h | **119.415 h** | +0.001% |
| **Challenger** | **171.403 h** | **171.404 h** | **+0.001%** |

Method: C_L = min(√(3·C_D0·π·AR·e), C_Lmax/1.15²); C_D = C_D0 + C_L²/(π·AR·e);
V = √(2W/ρSC_L); P_shaft = (W/(L/D))·V/0.84 + 500/0.75; ṁ = BSFC·P/3600;
E = ∫dm/ṁ by adaptive quadrature to 1e-12 relative. Challenger operating point:
C_L 1.2098, C_D 0.04570, L/D 26.47, ρ 0.95686 kg/m³, TAS 100.9 → 74.8 km/h,
shaft 4.11 kW.

**The integrator is not the problem.** The 120-step midpoint rule the repository
uses agrees with exact quadrature to better than 0.001% on both designs. So does
the analytic Breguet form. Six significant figures of agreement means the
arithmetic has been checked and passed; it says nothing about the model.

### The champion's own published sensitivity table is wrong on two of three anchors

| Anchor | Report claims | I derive | Verdict |
|---|---|---|---|
| C_D0 0.020 → 0.016 | +0.36 d | **+0.358 d** (+8.59 h) | ✅ 0.6% |
| BSFC 270 → 250 g/kWh | +0.5 d | **+0.377 d** (+9.04 h) | ❌ report high by 33% |
| 4,000 m → 3,000 m | +0.23 d | **+0.198 d** (+4.74 h) | ❌ report high by 16% |

Endurance is *exactly* inversely proportional to BSFC in this model (BSFC enters
ṁ linearly and nothing else). +0.5 d therefore requires 244 g/kWh, not 250. The
C_D0 anchor reproduces, which corroborates `research/riblets_pack.md`'s
appendix; the other two do not, and both are levers the challenger leans on.

### Where the +52.0 h actually comes from

Applied cumulatively to the champion at 119.414 h:

| Step | ΔE |
|---|---|
| BSFC 0.270 → 0.250 | **+9.55 h** |
| altitude 4,000 → 2,500 m | **+8.01 h** |
| S 3.9 → 6.0 m² | +23.97 h |
| AR 22 → 18.36 | −12.75 h |
| C_D0 0.016947 → 0.016066 | +2.12 h |
| e 0.8500 → 0.8565 | +0.56 h |
| MTOW 250 → 278.2 kg | −21.98 h |
| fuel 101.5 → 125.2 kg | +42.51 h |

**Apply BSFC 0.250 and altitude 2,500 m to the champion's unchanged airframe and
you get +17.56 h (+14.7%) for no design change at all** — 34% of the challenger's
entire margin, bought by pinning two bounds. The geometry-attributable gain is
+30.08 h (+25.2%).

---

## 2. Mass model: my primary attack fails, but the fixed non-wing mass does not survive

I reproduce `k_cal = 4.225741615220753`, wing 32.5000 kg at the baseline and
37.0156 kg for the challenger; empty 103.0156 kg against the recorded 103.0149.

### The AR^1.5 scaling is real and it is defensible

I verified the exponent analytically rather than trusting the docstring:
cap_area ∝ W·(b/2)²(1+λ)/((t/c)·S) and m_cap ∝ cap_area·(b/2), giving
**m_cap ∝ W·AR^1.5·√S/(t/c)** exactly as claimed. Effective exponents on *total*
wing mass at the baseline (the spar term is 14.56 kg of 32.50 kg):

| | this model | Raymer GA regression (6th ed. eq. 15.46) |
|---|---|---|
| d ln W_wing / d ln AR | **0.67** | 0.60 |
| d ln W_wing / d ln(t/c) | **−0.45** | −0.30 |

**Independent ratio test.** I evaluated Raymer's regression on both design points
and compared the *ratio* (the absolute value is meaningless — it is an aluminium
light-aircraft fit):

- Raymer: challenger/champion wing mass = **1.150**
- This model: **1.139**
- Disagreement: **−1.0%**

**The "54% larger wing for only +4.5 kg" is correct.** It is +4.52 kg, and it is
right because a lower AR (18.36 vs 22) and a 46% deeper spar (t/c 0.20 vs
0.1371) genuinely buy back what the extra area and the extra 28 kg of MTOW cost.
The spar cap actually gets *lighter* (14.56 → 9.42 kg) and the +4.52 kg is
almost entirely the area-proportional skin/rib term. I set out to break this and
could not. Two independent methods agree to 1%.

### But k = 4.226 is doing far more work than "one dimensionless coefficient" implies

Stripped of the calibration, the derived physics returns **3.45 kg** of spar cap
at the baseline. k inflates it to 14.56 kg. So **76% of the only term that
carries the AR and t/c physics is the fitted constant.** Most of that is
probably a missing factor of 2 (the formula integrates one semi-span's caps and
never doubles for the second wing), leaving ~2.1 of genuine fudge. The scaling
survives this — k is a pure multiplier and cancels from every ratio — but the
docstring's framing ("one number is fitted, the rest is derived") understates it.

### The fixed 28 kg non-wing airframe is where it breaks

`empty_mass_kg` charges 28 kg of non-wing airframe and 7 kg of recovery
regardless of size. The challenger's wing is 2.19× larger in the S·MAC product
that sizes a tail:

| | champion | challenger |
|---|---|---|
| S·MAC | 1.7208 m³ | 3.7618 m³ (×2.186) |
| tail area at constant V_h, same 3.2 m arm | 0.310 m² | **0.678 m²** |
| tail wetted area | 1.139 m² | **2.490 m²** |

Honest re-charge — tails ∝ S_h, fuselage ∝ MTOW, booms fixed (arm unchanged),
misc fixed, recovery ∝ MTOW — takes 35.0 kg to **43.08 kg: +8.08 kg the model
never charges.** At the challenger's design point that is **−15.21 h
(171.40 → 156.20 h, −8.9%)**.

### The spar cap has no minimum-gauge or panel-buckling floor

σ_cap is held at 600 MPa for every design in the space.

| | cap area | spar depth | root chord | cap laminate @0.25c width | b/t |
|---|---|---|---|---|---|
| champion | 422.7 mm² | 79.6 mm | 0.581 m | 2.91 mm | 50 |
| **challenger** | **241.2 mm²** | 175.9 mm | 0.880 m | **1.10 mm** | **200** |

At a 0.35c cap width the challenger's laminate is 0.78 mm — five plies of UD
carbon at b/t 393. The 600 MPa allowable already carries a buckling knockdown,
and panel buckling scales as (t/b)²: the challenger's wider, thinner cap is the
one *least* entitled to it. Dropping it to 450 MPa adds ~3.1 kg. Not decisive,
but it is a free pass the model hands to exactly the design that exploits t/c.

---

## 3. Fuel volume: the constraint is not overstated. It is mis-specified by ~1.6× — which is worse.

This is the gate that matters most and it is the finding that decides the audit.

I integrated the pinned `data/airfoils/fx63137.dat` directly (Lednicer→Selig,
97 points, t/c 0.13712 at x/c 0.3085 — checksum geometry confirmed).

**`k_area = 0.6062` is exactly right.** I measure A/(t·c) = **0.60620**. Under
pure thickness scaling about the camber line the coefficient is preserved
identically, so it is valid at t/c 0.20 too. No attack available.

**`chord_frac = 0.50` is wrong, in the conservative direction.** The airfoil is
thickest at 31% chord, so a 50%-chord box centred on it holds far more than 50%
of the section area:

| spar stations | box width | fraction of section area held |
|---|---|---|
| 0.15c–0.65c | 0.50c | **71.6%** |
| 0.20c–0.70c | 0.50c | 68.1% |
| 0.25c–0.75c | 0.50c | 63.3% |
| 0.25c–0.65c | 0.40c | 56.1% |

**`span_frac = 0.80` is wrong, in the conservative direction.** Volume goes as
∫c²dy, and the outer 20% of a tapered wing is nearly empty:

| taper | true volume fraction inboard of 0.8·b/2 | model uses |
|---|---|---|
| **0.30 (challenger)** | **0.9402** | 0.80 |
| 0.45 (champion) | 0.9070 | 0.80 |
| 0.60 | 0.8744 | 0.80 |

Combined, with `net_frac` 0.88 retained and 4% ullage-plus-unusable added:

| | model capacity | geometry-honest capacity | fuel required |
|---|---|---|---|
| champion | 39.27 kg | **66.74 kg** | 101.50 kg |
| **challenger** | **125.22 kg** | **~300 kg** | 125.23 kg |

**Consequences, in order of severity:**

1. **The challenger's design point is an artifact.** It sits exactly on a wall
   that is in the wrong place. Re-optimising with honest tank geometry (same
   bounds, same everything else) moves the optimum to **S 6.0, AR 24.0,
   MTOW 320 kg, span 12.0 m → 218.4 h**. The challenger is **21% below the
   optimum of its own corrected problem.** The tank constraint stops binding
   entirely; MTOW ≤ 320 and span ≤ 12 bind instead.
2. **The champion's headline infeasibility is itself overstated by 78%.** It is
   short by 34.8 kg on honest geometry, not 62 kg. Still a hard fail, but the
   number the programme has been quoting is wrong.
3. **The ullage arithmetic in the claim is computed on the wrong base.** Against
   the model's capacity, 3% ullage gives margin −3.76 kg and 5% gives −6.26 kg,
   so "6.78–6.93 d" is a reasonable arithmetic consequence of a wrong capacity.
   Against honest geometry the margin is +187 kg and ullage costs nothing at all.

**As recorded, the challenger is infeasible.** `opt_runs/coupled.json` carries
`"violation": 6.927e-05` and `"feasible": false` under the key `best_feasible`.
6.927e-5 × 50 = **fuel exceeds tank by 3.46 g.** Physically trivial — but G2 says
"no exception", and the artifact's own flag says false.

---

## 4. Aero coupling: the Oswald surface holds up; the C_D0 build-up does not

### The AVL fit is sound — I re-ran it

I rebuilt the decks myself and ran `vendor/bin/avl` (12 sections, 24 spanwise
panels, tip-bunched, matched C_L 1.21, `a c 1.21` then `x`, per the
`riblets_pack.md` verification note):

| planform | my AVL | fitted surface | Δ |
|---|---|---|---|
| AR 22, λ 0.45, tw −3° (champion) | 0.9786 | 0.9786 | 0.0000 |
| AR 18, λ 0.30, tw −3° (table node) | 0.9617 | 0.9634 | −0.0017 |
| AR 22, λ 0.30, tw −3° (table node) | 0.9555 | 0.9572 | −0.0017 |
| **AR 18.356, λ 0.30, tw −3° (challenger)** | **0.9611** | **0.9629** | **−0.0018** |

The stored table reproduces to four decimals — the 45-run sweep is real, not
asserted. The fitted surface over-states the challenger's inviscid e by
**+0.0018 (+0.19%)**, worth about +0.15 h. Negligible. The fit's quadratic-in-
twist term is poor at the extremes (±0.017 at 0° and −6°) but the design twist
is −3°.

**One caveat the fit does not carry: it is not panel-converged.** On the
challenger planform e falls monotonically with refinement — 0.9611 (12×24) →
0.9584 (16×32) → 0.9572 (20×36) → 0.9564 (12×36), i.e. **−0.5%** and still
moving. The whole surface is built on the coarsest of those. The bias is small
and it runs against the challenger, but the coefficients are quoted to six
figures they have not earned.

I also confirm the lumped composition: 1/e_eff = 1/e_inv + K_visc·π·AR returns
0.85005 at the champion (the design file's 0.85, by construction) and 0.85650 at
the challenger. **K_visc = 0.002237 is design-independent** — it is
ΔC_D = K_visc·C_L² = 0.00328 at C_L 1.21, **7.2% of the challenger's total C_D**,
calibrated once on a 13.7% section at Re 7.75e5 and applied unchanged to a 20%
section at Re 9.8e5. It also double-books against the thickness multiplier: the
wing's profile drag at lift is represented twice, in two terms neither of which
knows about the other.

### The C_D0 model does not reproduce its own calibration anchor

`coupled.py` states `CD0_BASELINE = 0.01529 # argus7.aero.buildup at the v1
point`. **At the v1 point the function returns 0.016947 — 10.8% high.** The
comment is false as coded.

Cause: `wetted_area_m2` uses S_wet/S_ref = 2(1 + 1.2·t/c) = **2.3290**. I
measured the real arc length of the pinned coordinates:

| t/c | true perimeter/chord | model 2(1+1.2 t/c) | error |
|---|---|---|---|
| 0.1371 | 2.0664 | 2.3290 | **+12.7%** |
| 0.170 | 2.0855 | 2.4080 | +15.5% |
| **0.200** | **2.1052** | **2.4800** | **+17.8%** |

The true section barely grows with thickness (+1.9% from t/c 0.137 to 0.20); the
model thinks it grows +6.5%. Direction of bias: it **over**-charges the
challenger relative to the champion. Fixing it costs the challenger only −0.57 h.
Conservative — but the calibration chain is broken and should be said so.

### The real defect: fixed non-wing wetted area amortised over a growing S_ref

`SWET_NONWING = 7.23 m²` is constant, and C_D0 = C_fe·S_wet/S_ref. Growing the
wing from 3.9 to 6.0 m² therefore **lowers C_D0 from 0.016947 to 0.016066
(−5.2%) purely by division**, while E ∝ √(ρS) adds more on top. **That is why S
pins its 6.0 bound.** The coupled model was written to stop the optimiser buying
C_D0 for free; it left this door open.

The fuselage, booms and turret genuinely are fixed. The tail is not — it is
15.8% of that 7.23 m² and it scales with S·MAC/l. Charging it at constant tail
volume coefficient (1.139 → 2.490 m²) raises the challenger's C_D0 to 0.017048
(+6.1%) and costs **−2.76 h**.

And the level itself is optimistic: `argus7/aero/buildup.py`'s own docstring
says its 0.0154 omits the payload turret ("~0.007 in C_D0, more than a third of
the report's total"), cooling drag (5–10%), fuselage base drag and gear. A
modest +0.0035 allowance costs the challenger **−9.46 h**.

### The thickness penalty: verified, slightly under-charged, and Re-blind

I re-measured it with NeuralFoil (xxlarge) on the same thickness-scaled
coordinates, trimmed to C_L 1.2098:

| t/c | my C_D at Re 1e6 | relative | model 1+2.5(t/c−0.137) |
|---|---|---|---|
| 0.1371 | 0.008090 | 1.0000 | 1.0002 |
| 0.170 | 0.008824 | 1.0907 | 1.0825 |
| **0.200** | **0.009497** | **1.1739** | **1.1575** |

Real penalty **+17.4%**, model **+15.75%** — the challenger is under-charged by
1.6 points on wing profile drag. Small. The larger issue is that the multiplier
is fitted at a single Reynolds number and applied everywhere, and the challenger
flies slower:

| station | Re | C_D at C_L 1.21 |
|---|---|---|
| champion tip, light loiter (27.5 m/s, 0.261 m, 4,000 m) | 3.54e5 | 0.011444 |
| **challenger tip, light loiter (20.8 m/s, 0.264 m, 2,500 m)** | **3.07e5** | **0.015008** |

**+31% at the tip, not +17%** — and `riblets_pack.md` §"open questions" already
flags the FX 63-137's non-monotonic high-drag knee below Re 5e5 as exactly the
regime the tip occupies at light loiter. Span-weighting the penalty is worth
roughly −1.4 h. Not decisive; symptomatic.

### The C_Lmax attack fails, and I should say so plainly

I expected a 20%-thick section to lose C_Lmax and drag the loiter C_L down with
it. NeuralFoil says the opposite:

| section | Re | C_Lmax |
|---|---|---|
| t/c 0.1371 (champion) | 7.75e5 | 1.877 |
| **t/c 0.200 (challenger)** | 9.84e5 | **1.972** |

Holding C_Lmax = 1.60 for every design is **conservative for the challenger**,
not generous. The residual risk is three-dimensional, not sectional: taper 0.30
pinned at its lower bound with only −3° washout is the classic tip-stall
planform, and 3D C_Lmax and departure behaviour are not modelled anywhere in
this stack.

---

## 5. Part-load BSFC: the finding that destroys the absolute claim

`argus7/prop/engine.py` — this project's own module, already in the repository —
states in its constants block that the report's flat 270 g/kWh is applied "at a
point that is only ~20% of the engine's rating" and that the load-dependent map
moves 4.70 d to **3.95 d**.

I implemented the Willans relation independently rather than calling it:
P_f = φ·P_rated·(n/n_r)(F₀+(1−F₀)n/n_r) = 1,585 W at the design gearing;
BSFC(P_b) = BSFC_rated/(1+φ)·(1+P_f/P_b).

| | flat BSFC | part-load | loiter BSFC | days |
|---|---|---|---|---|
| champion (rated 270) | 119.41 h | **93.08 h** (−22.1%) | 314 g/kWh | 3.88 d |
| **challenger (rated 250)** | **171.40 h** | **129.97 h** (−24.2%) | **294 g/kWh** | **5.42 d** |

My 314 g/kWh lands within 2.4% of the module's own 321.3. The challenger is
penalised slightly *more* because it runs at slightly lower absolute shaft power.

**The challenger's BSFC 0.250 is not merely at a favourable bound. It is 18%
below what this project's own engine deck computes for the actual operating
point, and 24% below the only verified BSFC on the report's engine shortlist
(330 g/kWh, RCV DF70LC and Orbital HFDI-150).** The 7.14 d headline is 5.42 d
the moment the engine is modelled instead of assumed. That correction applies to
both designs and does not overturn G1 — it overturns the number in the title.

---

## 6. Mission-requirement regression at 2,500 m

Report §1, *"locked with sponsor"*: **loiter band 3,000–4,500 m AGL.** The
challenger loiters at **2,500 m** — below the locked band, at the optimiser's
lower bound. Using the report's own θ* = 20.3° suburban elevation-angle model:

| altitude | service radius | coverage area | vs 4,000 m |
|---|---|---|---|
| 4,000 m (champion) | 10.81 km | 367.3 km² | 100% |
| 3,000 m (band floor) | 8.11 km | 206.6 km² | 56% |
| **2,500 m (challenger)** | **6.76 km** | **143.5 km²** | **39%** |

**The challenger buys +8.0 h of endurance by giving up 61% of the primary
mission product.** The report anticipated this exactly — "loiter at 3,000 m
instead of 4,000 m → +0.23 d (costs coverage)" — and the optimiser went a
further 500 m past the floor because nothing in the objective knows coverage
exists.

Secondary: loiter TAS falls to **74.8 km/h (20.8 m/s)** at end of mission against
the champion's 98.8 km/h. Station-keeping margin against wind roughly halves,
and 20.8 m/s at 2,500 m over a disaster zone is not a comfortable number.

---

## 7. Bound pinning: five of seven, not four

| variable | bounds | challenger | at bound? |
|---|---|---|---|
| wing area | 2.5 – **6.0** | **6.000** | ✅ max |
| aspect ratio | 14 – 30 | 18.356 | interior |
| taper | **0.30** – 0.70 | **0.300** | ✅ min |
| t/c | 0.10 – **0.20** | **0.200** | ✅ max |
| MTOW | 180 – 320 | 278.24 | interior* |
| altitude | **2500** – 5000 | **2500** | ✅ min |
| BSFC | **0.25** – 0.32 | **0.250** | ✅ min |

\* MTOW is interior only because the mis-specified tank constraint pins it there.

The pre-registration is explicit: *"Any challenger sitting at the low C_D0 bound
is exploiting this and must be discounted"* — written about C_D0, but the
principle is general and the run replaced C_D0 with geometry precisely so that
this test would mean something. Five of seven at bounds is the signature of a
model being read at its corners, and I re-confirmed it survives correction: in
**every** corrected model I re-optimised (M1–M5 below), five bounds remain
pinned. Only the identity of the pinned set changes.

### Where the optimum actually goes, correction by correction

Same bounds, same objective, differential evolution, my own re-implementation
(verified to reproduce the repository to 0.001 h at both design points):

| model | S | AR | MTOW | alt | E | pinned |
|---|---|---|---|---|---|---|
| **M0** repo as published | 6.000 | 18.43 | 278.0 | 2500 | 171.40 h | 5/7 |
| **M1** + honest tank + 4% ullage | 5.999 | 24.00 | **320** | 2500 | **218.36 h** | 5/7 |
| **M2** + tail at constant V_h | 5.693 | 25.29 | **320** | 2500 | 215.47 h | 5/7 |
| **M3** + non-wing & recovery mass scaled | 4.881 | **29.50** | **320** | 2500 | 200.55 h | 5/7 |
| **M4** + true airfoil perimeter | 4.943 | 29.13 | **320** | 2500 | 198.98 h | 5/7 |
| **M5** + turret/cooling/base +0.0035 | 5.045 | 28.54 | **320** | 2500 | 185.78 h | 5/7 |

Two things fall out. First, **the challenger is not the optimum of any corrected
problem** — it is 8–21% below. Second, once the tank stops binding, **AR runs to
29.5 of a 30 bound** in M3–M5. That is precisely the runaway G5 was written to
prevent. G5 passed on the challenger only because a different, wrongly-placed
constraint happened to be holding AR down.

---

## 8. Gate verdicts

Conjunctive. All must pass.

### G1 — endurance ≥ +5%, same simulator on both: **PASS (discounted margin +25.2%)**

171.403 vs 119.414 = **+43.5%**, and I reproduce both to six significant figures.
It survives every correction I can justify: with honest tank geometry, tail
scaling, non-wing mass scaling, true perimeter and 4% ullage all applied to both
designs, the challenger still leads **+30.3%**; with part-load BSFC on top,
+39.6%. There is no correction in my hands that takes it below +5%.

**But 14.7 points of the 43.5 come from pinning BSFC and altitude on an otherwise
unchanged champion airframe.** Under the pre-registration's own discounting rule
the design-attributable improvement is **+25.2%**. That still clears the gate.
**PASS.**

### G2 — fuel ≤ wing tank capacity, no exception: **FAIL**

Two independent reasons.

1. **As recorded, it violates.** `opt_runs/coupled.json` reports
   `"violation": 6.927e-05` and, under the key `best_feasible`,
   `"feasible": false`. Fuel exceeds tank by **3.46 g**. Physically nothing;
   3.5 g off MTOW fixes it. But "no exception" admits no exception, and the
   Stage-1 DOE's genuinely feasible best (163.30 h, `violation: 0.0`) was
   available and was not what got reported.
2. **The constraint is mis-specified by ~1.6× and therefore sitting on it means
   nothing.** `chord_frac` 0.50 against a measured 0.716; `span_frac` 0.80
   against a c²-weighted 0.940. A challenger whose entire shape is determined by
   pressing against a wall in the wrong place has not demonstrated feasibility;
   it has demonstrated the wall.

**FAIL.**

### G3 — span ≤ 12.0 m: **PASS**

√(18.356412887573242 × 6.0) = **10.4947 m**. 12.5% margin. Verified independently.

### G4 — mass closure exact: **PASS**

103.0149 + 50 + 125.2262 = **278.2411 = MTOW**, exact to float32. I re-derived
empty mass from the design variables without touching the optimiser output:
37.0156 (wing) + 28 + 25 + 6 + 7 = **103.0156 kg**, matching to 0.7 g. Closes.

### G5 — structural scaling honoured, not a fixed constant: **PASS, for the wrong reason**

The AR^1.5 physics is genuinely in the code and I verified the exponent
analytically. The wing-mass *ratio* between the two designs agrees with Raymer's
independent regression to 1.0%. The gate is satisfied on its letter.

On its stated intent — *"an optimiser with a fixed empty mass will run AR to its
bound; this gate confirms it did not"* — it passed by accident. AR stayed at
18.36 because the mis-specified tank constraint held it there. Repair the tank
and AR goes to 29.5 of 30 (M3–M5). **The mass model is not, on its own, strong
enough pushback.** And a fixed empty mass is exactly what the *non-wing* 28 kg
still is: +8.08 kg undercharged, worth −15.2 h.

### G6 — regulatory band declared, not silently crossed: **FAIL**

MTOW moves **250 → 278.24 kg (+11.3%)** and the artifact carries no band
declaration whatsoever — `coupled.json` records a float. The report's entire §9
regulatory case (SORA 2.5, SAIL III–IV, MoC Light-UAS 2511/2512, ground-risk
class from the 3–4 kJ touchdown energy) is built at 250 kg, and touchdown energy
scales with mass. Every corrected model I ran pushes MTOW to its **320 kg** bound,
i.e. +28% on the champion, with the same silence. The gate says "not silently
crossing". This crossed silently. **FAIL.**

### G7 — buildability: AR ≤ 25, span ≤ 12 m, engine matched to a real §6 unit: **FAIL**

AR 18.36 ✅ and span 10.49 m ✅. The engine does not match.

Report §6's shortlist contains exactly one unit rated for this MTOW — the 250 cc
class, ~17 kW — and its BSFC is explicitly *"not published — must be dyno-mapped;
design assumes 270 g/kWh, target ≤250"*. The challenger **requires** 250 g/kWh as
a flat constant. That is the shortlist's aspirational target, not a matched unit.
The only shortlist entries with **verified** BSFC are the RCV DF70LC and the
Orbital HFDI-150, both at **330 g/kWh** — at which the challenger returns
**129.9 h**, still +8.8% over the champion, but nothing like 7.14 d.

Compounding: MTOW 278.2 kg raises the climb requirement from 12.2 to ~13.6 kW
against the same 17 kW rating, while `argus7/prop/bemt.py` already establishes
that the specified 0.813 m disc at 2,100 rpm absorbs at most ~6.4 kW inside the
speed envelope and 3.7 kW at a realistic static pitch/D. The propulsion set
closes *less* well at 278 kg than at 250 kg. **FAIL.**

### G8 — loiter C_L ≤ C_Lmax/1.15²: **PASS**

C_L = **1.20983** = 1.6/1.3225 exactly. The min-power C_L is 1.5428, so the stall
constraint binds as designed — the challenger did not escape it by moving to a
polar where min-power C_L falls below the stall limit. NeuralFoil independently
puts the thickened section's 2D C_Lmax at **1.972** against the champion's 1.877,
so the fixed 1.60 is conservative *for the challenger*. **PASS**, with the
unmodelled 3D tip-stall risk of taper 0.30 + (−3°) washout noted and not scored.

### Summary

| Gate | Verdict |
|---|---|
| G1 endurance ≥ +5% | ✅ PASS (+43.5% raw, +25.2% discounted) |
| G2 fuel ≤ tank | ❌ **FAIL** (recorded violation; constraint mis-specified ~1.6×) |
| G3 span ≤ 12 m | ✅ PASS (10.49 m) |
| G4 mass closure | ✅ PASS (exact) |
| G5 AR^1.5 honoured | ⚠️ PASS on the letter, by accident on the intent |
| G6 regulatory band declared | ❌ **FAIL** (250 → 278.2 kg, undeclared) |
| G7 buildability / real engine | ❌ **FAIL** (250 g/kWh is a target, not a unit) |
| G8 stall margin | ✅ PASS (C_L 1.2098) |

**Conjunctive result: DO NOT ADOPT.**

Per the pre-registration's decision rule — *"Any of G2–G8 fails → do not adopt;
report the best design that does pass"* — here is that design.

### The best gate-respecting design I can find

Constraints: span ≤ 12 m, **AR ≤ 25** (G7), **altitude ≥ 3,000 m** (report §1's
locked band), **MTOW ≤ 250 kg** (holds the champion's declared regulatory band),
honest tank geometry, 4% ullage, tail scaled at constant V_h, non-wing and
recovery mass scaled, true airfoil perimeter:

> **S 4.569 m², AR 25.0, taper 0.300, t/c 0.200, MTOW 250 kg, loiter 3,000 m,
> BSFC 250 g/kWh, span 10.69 m, empty 100.0 kg, fuel 100.0 kg against a tank of
> 170.5 kg.**
>
> **141.5 h (5.89 d)** on a flat BSFC; **106.3 h (4.43 d)** on the part-load map.
> **+20.6% / +15.6% over the champion evaluated in the same model** — and it is
> feasible with 70 kg of tank margin.

That is a real, defensible improvement over the champion, it clears G1 twice
over, and it is not the challenger.

---

## 9. The single most likely way this result is wrong

**The wing fuel-volume model is mis-specified by roughly 1.6×, and therefore the
challenger is not the constrained optimum — it is the shape of a design pressed
against a wall that is in the wrong place.**

Everything distinctive about the challenger is that wall's fingerprint: S at its
6.0 maximum, t/c at its 0.20 maximum, taper at its 0.30 minimum, MTOW settling
at 278.2 kg. All four are volume-buying moves, and the augmented-Lagrangian
refinement drove the design onto the constraint to within 3.5 grams precisely
because that constraint is what was binding. Move the wall to where the geometry
actually puts it — `chord_frac` 0.716 not 0.50, `span_frac` 0.940 not 0.80, both
measured off the repository's own pinned coordinates — and the constraint stops
binding altogether, MTOW and span take over as the active set, and the optimum
goes to **218 h** with the challenger 21% behind it.

This is not the same failure as the champion's. The champion asserted a design
and never checked whether the fuel fit. The challenger checked, against a
capacity model built from three guessed fractions (0.50 / 0.80 / 0.88), two of
which I have now measured and found wrong by 43% and 17.5% respectively in the
*conservative* direction. Being wrong conservatively still invalidates an
optimum: a binding constraint in the wrong location distorts every variable that
touches it.

The runner-up threat, and it is close, is the **flat BSFC at 20% engine load**.
The repository already contains the module that refutes it and quantifies the
refutation (4.70 d → 3.95 d), and my independent Willans line agrees within 2.4%.
That one does not change the *ranking* — it applies to both designs — but it
turns 7.14 d into 5.42 d, and 5.42 d does not meet the programme's 5–7 day
target in the way the headline implies.

### What would settle it

**Measure the tank, do not model it.** The repository already builds this
geometry: `argus7/cad/model.py`, `to_openscad.py`, and OpenSCAD is installed.
Loft the challenger wing (S 6.0, AR 18.356, taper 0.30, t/c 0.20 scaled about
the camber line), place real front and rear spar webs at their design chord
stations, subtract skin laminate thickness, spar-cap volume, rib flanges and the
flaperon cutout, and integrate the remaining cavity directly. **One measured
number replaces three guessed fractions.**

- If it returns ≈125 kg, the challenger is the constrained optimum, G2 is sound,
  and the 3.5 g violation is bookkeeping. Adopt it subject to G6 and G7.
- If it returns 200–300 kg as my area integrals say it will, the tank constraint
  is not the active one, **the entire optimisation must be re-run**, and this
  challenger is discarded — not because it is infeasible, but because it is the
  wrong answer to a question that was posed incorrectly.

Second, and cheap: resolve the φ = 0.1325 vs φ = 0.18 contradiction that
`engine.py` flags in its own constants block and refuses to resolve, then run the
mission on the load-dependent BSFC map instead of a flat constant, for **both**
designs. That decides whether the programme's headline is 7.1 days or 5.4.

Third, and cheapest: add a coverage-area or altitude-floor term to the objective.
The optimiser went 500 m below a sponsor-locked mission band and gave away 61% of
the mission product for 8 hours, because nothing in the objective function knew
the mission existed.

---

## Reproducibility

All figures above were produced with standalone scripts that import nothing from
`argus7.opt` or `argus7.mission` except `argus7.cad.airfoil_coords.load_airfoil`
(for the AVL deck, to guarantee the same section the sweep used). ISA from the
ICAO Doc 7488/3 defining constants; endurance by `scipy.integrate.quad` to 1e-12
relative, cross-checked against a 120-step midpoint rule and the analytic Breguet
form; airfoil area, perimeter and box fractions by trapezoidal integration of the
pinned Lednicer→Selig coordinates on a 4,001-point grid; AVL 3.36 from
`vendor/bin/avl` with decks written fresh; NeuralFoil `model_size="xxlarge"` with
`analysis_confidence` ≥ 0.956 on every quoted point; re-optimisation by
`scipy.optimize.differential_evolution` (popsize 45, tol 1e-11, polish), verified
to reproduce the repository's own evaluator to 0.001 h at both design points
before any correction was switched on.

Where I could not break the challenger, I have said so: the endurance arithmetic,
the wing-mass ratio, `k_area`, the AVL surface, and the stall margin all survived
attack. The result does not fail because the sums are wrong. It fails because
three of the eight gates say no, and because the constraint that shaped it is in
the wrong place.
