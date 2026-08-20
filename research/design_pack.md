# VERIFIED DESIGN DATA PACK — 200 kg MTOW Ultra-Long-Endurance UAV
Every number below was recomputed from first principles (Python, ISA atmosphere, component drag buildup, physics-based structure, discretized Breguet mission simulation with altitude-scheduled engine loading). Research inputs came from three specialist data packs (aerodynamics, powertrain, benchmarks/structures) built from primary sources (UIUC LSATs, NASA TM/NTRS, NACA, manufacturer datasheets, FAI records).

## 0. Mission requirements (from user dialogue)
- MTOW 200 kg; payload 30–50 kg (design point 40 kg); fuel Jet-A1/JP-8 or mogas
- Extreme straight-line range, gentle turning only; cruise 3,000–4,500 m; non-stop multi-day
- Powerplant: mass-produced small 4-stroke (Honda eSP+ class) or purpose UAV heavy-fuel engine; belt reduction; large slow prop

## 1. Final configuration (the answer to "planar vs ring")
High-aspect-ratio **planar** monoplane, twin-boom inverted V-tail, pusher prop.
- Wing: S = 3.8 m², AR = 20, span b = 8.72 m, taper 0.45, root chord 0.601 m, tip 0.271 m, MAC 0.457 m, t/c 13%
- Airfoil: **Wortmann FX 63-137** (primary) — measured Clmax ≈1.7 (soft stall), bucket CL 0.5–1.2, (Cl/Cd)max ≈104–119 @ Re 500k [M: UIUC/NREL LSATs Vol.4; Stuttgart Profilkatalog]. Cruise CL ≈1.0 sits inside its measured bucket. S1223 rejected (Cm ≈ −0.29 → trim drag/structure; high-lift not needed). E387/SD7037 rejected (bucket tops at CL ~0.9–1.0, Clmax 1.25 — no gust margin).
- Cruise Re ≈ 0.7–0.9M (MAC 0.457 m, 30–35 m/s, 3,500–4,800 m)
- Fuselage pod 3.3 m × 0.5 m; twin booms 2.3 m × 0.09 m; inverted V-tail, combined area 0.46 m² (Vh 0.50, Vv 0.025, arm 2.6 m), ~45° dihedral class
- Fixed light gear (belly-protection skids), antennas — misc flat-plate f = 0.033 m²

## 2. Verified masses (calibrated to measured sailplane practice)
- Wing complete (UD T700 spar caps, Rohacell web, sandwich skins, ribs, flaperons, integral tanks): **32.7 kg** (8.6 kg/m²; defensible band 8–12 kg/m² per ASW 27B = 12.9 kg/m² measured [DS])
- Ultimate root bending moment: **15.2 kN·m** at +5.7 g with 85 kg fuel-in-wing relief (no-relief value 19.6 kN·m); spar-cap mass 4.8 kg at 550 MPa design allowable (T700 compressive mean ~1,400 MPa → conservative)
- Empty 82.2 kg (incl. +8% contingency) = wing 32.7, pod 9.7, booms+tail 4.4, gear 4.9, powerplant 15.1, thermal/lube 1.7, avionics+electrical 10.3, contingency ~3.4
- MTOW = 82.2 + 40 payload + 77.8 fuel (97 L Jet-A1) = 200 kg ✓

## 3. Verified aerodynamics
- L/D max = **23.0 at CL 1.01** (3,500 m, 165 kg). Drag polar: CD = cd_airfoil(CL,Re) + CD0_nonwing (~0.0084+0.0087 misc) + CL²/(π·AR·e), e=0.90
- Cruise: CL 1.0, TAS 106–123 km/h over mission, drag ≈ 85–160 N
- Neutral point 55% MAC; **static margin 10%** (CG at 45% MAC) — Gemini's 33% SM would cost ~+8% trim drag (+0.36%/1% SM per Lyu & Martins) and is corrected
- Fuel tanks centered at 45% MAC (CG station) → CG travel <0.5% MAC full→empty (VA001/A330 trim-tank practice)
- Stall: 83 km/h SL/MTOW at Clmax 1.6

## 4. Verified powertrain
- **Primary: RCV DF140LC** — 140 cc 4-cyl rotating-valve 4-stroke, 8.61 kW @ 8,800 rpm on JP-8/Jet-A1, 4.8 kg complete (+1.5 kg alt/mount/ECU misc), **BSFC 330 g/kWh [DS]**, TBO 500 h fixed-wing, oil-in-fuel 1:25. Quote-only price (~$15–35k class).
- **Budget: Honda PCX160 eSP+** — 156.9 cc, 60.0×55.5 mm, CR 12.0:1, 11.8 kW @ 8,500, 14.7 Nm @ 6,500, oil 0.9–1.0 L, ACG ~255 W, PGM-FI [DS Honda]; stripped-engine est. 15.5 kg [UNV — must weigh donor]; cruise BSFC ~330–420 g/kWh at 20–40% load [EST from cross-engine evidence]; mogas only. ~€800–1,500.
- Reduction: Gates Poly Chain GT Carbon toothed belt, **2.73:1** (98–99% efficient [MEAS]); prop 32 in (0.81 m) carbon ground-adjustable (Mejzlik/Helix class), cruise 2,200 rpm, tip 93 m/s, helical Mach 0.30 @3,500 m; η_prop budgeted **0.81** (measured large-prop band 0.75–0.85 [UIUC Vol.4]); UAV-scale VP prop is a product gap (<9 kg class) — fixed/ground-adjustable selected
- Power available at 3,500 m: RCV 5.6 kW continuous (σ^0.95 derate, 0.92 continuous factor); takeoff T/W 0.23, ROC ~2.9 m/s at MTOW/SL
- Engine loading schedule: cruise-climb holds load fraction ~0.6 early → 0.39 late (BSFC sweet-spot tracking)

## 5. Verified thermal & lubrication
- Heat to coolant ≈ 0.9 × shaft power at part load [DR from ScienceDirect energy-balance reviews] → 2.5 kW at cruise → radiator face **~47 cm²** (Rotax 912 rule: 17–20 cm²/kW [DS install manual]), core ~0.4 kg (0.1–0.2 kg/kW); oil cooler ~0.5 kW
- Meredith-effect ducted radiator (R&M No.1683, 1935 [primary located]): diffuser face Mach ≤0.1, exit nozzle matched to flight speed; P-51 net cooling drag ~3% of total (vs 6–10% typical); model credits 3% installation drag — conservative per Miley 1988 critique
- Oil: consumption budget 3–5 g/h × 80 h = 0.24–0.40 kg → **auxiliary 2.0 L make-up sump** + level sensor + external oil cooler; stock 0.9–1.0 L sump alone insufficient (Gemini conclusion confirmed)
- Iridium plug (NGK Laser class): 100-h mission not plug-limited [EST]; dual 10 µm fuel filters

## 6. Verified mission performance (discretized Breguet, 1 kg fuel steps, altitude-scheduled)
**RCV route, 40 kg payload:** RANGE **9,128 km** | ENDURANCE **78.2 h (3.3 days)** | avg 117 km/h
- Profile: 197 kg @ 3,400 m/123 km/h/3.45 kW/1.14 kg/h → 127 kg @ 4,800 m/106 km/h/1.96 kW/0.65 kg/h
- Reserves: 5 kg fuel + 2 kg climb allowance already deducted
**PCX160 route, 40 kg payload:** 8,625 km | 71.4 h (−5.5%)
**Payload–range (RCV):** 0 kg → 12,956 km/109 h · 10 → 12,061/102 · 20 → 11,127/95 · 30 → 10,151/87 · 40 → 9,128/78 · 50 → 8,054/69
**Sensitivity:** empty +10% → −14%; BSFC +10% → −9%; η_prop 0.77 → −5%; CD0 +15% → −3%; CI diesel (250 g/kWh, what-if — no production engine exists in 5–15 kW class [verified product gap]) → +10%
**CI-diesel + PCX-mass what-if:** 10,273 km / 86 h — quantifies the payoff if a light CI engine appears

## 7. Annular (ring) wing — the originating question, settled quantitatively
Same MTOW/speed/altitude: ring D=3.0 m, c=0.5 m vs planar b=8.72 m:
- Induced: ring e_span=2 theory (Kroo/Prandtl: closed loop = ½ induced drag of same-span monoplane [D]) gives b_eff=√2·D=4.24 m vs planar 8.72·√0.90 → ring Di 160 N vs planar 41 N
- Profile+misc: ring ~52 N vs planar ~44 N (wetted 2πDc ≈ 9.4 m² vs 7.7 m²)
- **L/D: ring 9.3 vs planar 23.0 → ring needs 2.48× power → ~40% of the range.** Plus: all measured ring data stops at d/c≤3 (NACA TN-4117; Traub 2009: e>1 measured but "gains mitigated by significant CDmin" and upper/lower stall asymmetry pitch problems); our d/c≈18 extrapolation unverifiable; hoop structure heavier.
- VERDICT: planar wins decisively for this mission. Gemini's conclusion confirmed; its reasoning (+55% wetted area) replaced with the correct mechanism (span deficit + wetted area + stall asymmetry). Box wing (h/b 0.2, e≈1.46, −32% induced [Kroo/Demasi]) noted as the only non-planar option worth further study — not at this scale.

## 8. Gemini output audit (what held / what didn't)
| Gemini claim | Verdict | Verified value |
|---|---|---|
| S=3.0 m², b=7.35 m, AR=18 | suboptimal but close | S=3.8, b=8.72, AR=20 |
| L/Dmax 26.66 @ CL 0.933 | optimistic ~16% | 23.0 @ CL 1.01 |
| Cruise 95 km/h @ 3,500 m with S=3.0 | **physically impossible** (needs CL 2.2) | 106–123 km/h |
| Range 16,000 km / 120+ h | **overstated ~75%/~53%** (BSFC 230 & η_prop 0.84–0.86 & light structure) | 9,128 km / 78 h |
| RBM 7,552 N·m vs 11.2 kN·m | internally inconsistent; both low | 15.2 kN·m ultimate w/ relief |
| Static margin 33% | **wrong** — huge trim drag | 10% (neutral pt 55% MAC) |
| Wing dry 22 kg | ~33% light vs practice | 32.7 kg (8.6 kg/m²) |
| V-tail 0.655 m², SM 33% | oversized | 0.46 m² |
| 4-stroke > 2-stroke, EFI, belt reduction, Jet-A1, aux oil system, liquid cooling w/ Meredith, fuel-at-CG | **all confirmed** | adopted |
| Sources: scooter blogs, Reddit, IL-2 game forum | inadequate | replaced w/ UIUC/NASA/NACA/datasheets/FAI |

## 9. Benchmarks (measured)
- **VA001** (closest analog): 272 kg MTOW design, record flight 191.3 kg, 10.97 m span, 4-cycle diesel (undisclosed), **121 h 24 min (2017)** landing with 3 days fuel; **8 days 50 min (2021)**; measured burn 0.53 kg/h JP-8; derived L/D 29–39 [DR, contested — R1 estimates 18–25]; payload 13.6 kg
- Aurora Orion: 80 h (2014), 2× Austro AE300 diesel, 11,050 lb class
- Boeing Condor: 61 m span, AR 36.6, 58 h (1988)
- Zephyr S (solar, different physics): 64 days (2022), 75 kg MTOW
- Beihang Feng Ru 3-100: 80 h 46 min, 25–100 kg class (2021)
- Our 78 h @ 200 kg with spark-ignited BSFC 330 is honest against VA001's CI-diesel advantage

## 10. Figures (in `../figures/design-pack/`)
fig1 mission profile · fig2 drag polar+L/D · fig3 power required/available · fig4 grid-search heatmap · fig5 mass breakdown · fig6 annular vs planar · fig7 sensitivity tornado · fig8 payload-range · fig9 plan view

## 11. Key open risks for premortem
- RCV engine: quote-only, $15–35k class, sole-source UK, oil-in-fuel 1:25 logistics; PCX160 route needs CVT/PTO re-engineering + weighing donor
- No production CI engine in 5–15 kW class (the +10–32% range lever is locked behind a product gap)
- η_prop 0.81 assumed on a not-yet-designed prop; measured band 0.75–0.85
- 200 kg MTOW = regulated category (certification/airspace for 3+ day autonomous flight; BVLOS waivers; export control if dual-use)
- Wing Clmax 1.6 assumed with clean FX 63-137; contamination (icing at −8 to −14 °C cruise band!) — pitot/stall margin; Jet-A1 fine to −47 °C but water contamination in 97 L over 4 days
- Single engine, single point of failure over 78 h; alternator load for avionics ~200 W continuous
- 8.72 m one-piece wing transport/assembly; launcher or runway for 83 km/h stall class
