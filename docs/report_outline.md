# Outline — Engineering Design Report: 200 kg MTOW Ultra-Long-Endurance UAV
Source of truth: ../research/design_pack.md (all numbers verified by computation)
Figures: ../figures/design-pack/fig1..fig9 (PNG)

1. Mission Requirements & Design Philosophy (~1,500 w) — from the engineering dialogue: ring-wing origin, convergence to planar high-AR; requirements table; design drivers
2. Configuration Selection (~2,000 w) — planar vs delta vs annular vs multirotor/VTOL; quantified trades; fig6
3. Aerodynamic Design (~2,500 w) — airfoil down-select w/ measured data (FX 63-137), geometry, spanload/twist (Prandtl bell), drag polar buildup, L/D; fig2, fig9
4. Stability & Control (~1,500 w) — neutral point 55% MAC, SM 10%, V-tail (Vh 0.50/Vv 0.025), fuel-at-CG, trim-drag math
5. Propulsion (~2,500 w) — engine trade table (RCV DF140LC vs PCX160 vs NW-88 vs 3W/Wankel), BSFC reality at part load, belt reduction, propeller, fuel system, takeoff/climb
6. Thermal Management & Lubrication (~1,500 w) — 2.5 kW heat rejection, radiator sizing (Rotax rule), Meredith duct (R&M 1683), oil system for 100+ h
7. Structures & Mass Properties (~1,800 w) — +5.7 g ultimate, RBM 15.2 kN·m, UD T700 caps/Rohacell web, calibrated 8.6 kg/m² wing, mass budget; fig5
8. Mission Performance (~2,000 w) — power-required curves, cruise-climb schedule, verified 9,128 km/78.2 h, payload-range, sensitivity; fig1, fig3, fig4, fig7, fig8
9. Benchmarks & Validation (~1,500 w) — VA001 (121 h measured), Orion, Condor, Zephyr; honest positioning
10. Verification Appendix — Gemini Audit (~1,800 w) — claim-by-claim table, what held/failed, methods & model validation, error found & fixed during verification
11. Premortem (external — now merged into argus7_design_report.md, Annex A)
12. Conclusions & Recommended Build Path (~1,200 w) — decision gate, test plan, next steps
+ Executive summary (written at assembly) + References
