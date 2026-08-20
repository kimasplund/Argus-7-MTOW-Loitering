"""Propeller design sweep for ARGUS-7 v2.0.

Two operating points must BOTH be satisfied by one propeller:
  LOITER  - 122 hours here, so efficiency directly multiplies endurance
  CLIMB   - must absorb the engine's rated power without over- or under-loading

Fixed-pitch props cannot optimise both; the sweep quantifies the penalty and
compares against variable pitch.
"""
import json, itertools, math
import numpy as np
from argus7.prop.bemt import constant_pitch_blade, run_bemt
from argus7.mission.atmosphere import isa_numpy
from argus7.design.schema import load_design
from argus7.design.geometry import derive_wing

d = load_design('design/argus7_v2.yaml'); g = derive_wing(d.wing)
P_RATED_W = d.propulsion.power_max_kw * 1000.0
ALT = d.mission.loiter_altitude_m

# --- loiter condition from the design point -------------------------------
atm = isa_numpy(ALT); rho_loiter = float(atm.density_kgm3)
rho_sl = float(isa_numpy(0.0).density_kgm3)
cl = 1.21
W_mid = (d.masses.mtow - 0.5*d.masses.fuel) * 9.80665
V_loiter = math.sqrt(2*W_mid/(rho_loiter*g.area_m2*cl))
cd = d.aero.cd0 + cl**2/(math.pi*g.aspect_ratio*d.aero.oswald_e)
D_loiter = W_mid/(cl/cd)
P_thrust_loiter = D_loiter * V_loiter
print(f"LOITER: {ALT:.0f} m, rho {rho_loiter:.4f}, V {V_loiter:.2f} m/s ({V_loiter*3.6:.1f} km/h)")
print(f"        thrust required {D_loiter:.1f} N, useful power {P_thrust_loiter/1000:.3f} kW")
print(f"CLIMB : sea level, engine rated {P_RATED_W/1000:.2f} kW\n")

# boom clearance: prop tip must clear the boom inner surface at y=+/-0.6206
BOOM_INNER = 0.6206 - 0.045
results = []
for D, rpm_l, B, pitch_ratio in itertools.product(
        [0.70,0.80,0.90,1.00,1.10,1.20], [1400,1700,2000,2300,2600],
        [2,3], [0.55,0.70,0.85,1.00,1.15]):
    if D/2 > BOOM_INNER - 0.05:      # keep >=50 mm to the booms
        continue
    blade = constant_pitch_blade(D, pitch_ratio*D, blades=B)
    try:
        L = run_bemt(blade, rpm_l, V_loiter, rho_loiter)
        if not L.converged or L.eta <= 0 or L.thrust_n <= 0:
            continue
        # scale rpm so shaft power at loiter matches what the airframe needs
        need = P_thrust_loiter / max(L.eta, 1e-6)
        # climb: same blade, sea level, best-climb speed ~1.2 Vstall
        V_cl = 30.0
        best_absorb = None
        for rpm_c in (rpm_l, rpm_l*1.15, rpm_l*1.3, rpm_l*1.45):
            C = run_bemt(blade, rpm_c, V_cl, rho_sl)
            if C.converged and C.power_w > 0:
                if best_absorb is None or abs(C.power_w-P_RATED_W) < abs(best_absorb.power_w-P_RATED_W):
                    best_absorb = C
        if best_absorb is None: continue
        results.append(dict(D=D, rpm=rpm_l, B=B, pitch_ratio=pitch_ratio,
                            eta_loiter=L.eta, cp_loiter=L.cp, J_loiter=L.j,
                            thrust_loiter=L.thrust_n, shaft_loiter_kw=L.power_w/1000,
                            tip_mach=L.tip_mach, climb_rpm=best_absorb.rpm,
                            climb_kw=best_absorb.power_w/1000, climb_eta=best_absorb.eta,
                            absorb_ratio=best_absorb.power_w/P_RATED_W))
    except Exception:
        continue

ok = [r for r in results if r['thrust_loiter'] >= D_loiter*0.97 and r['tip_mach'] < 0.75]
ok.sort(key=lambda r: -r['eta_loiter'])
print(f"{len(results)} converged, {len(ok)} meet loiter thrust and tip-Mach\n")
print(f"{'D(m)':>5} {'rpm':>5} {'B':>2} {'p/D':>5} {'eta_loit':>9} {'J':>5} {'tipM':>5} {'climb kW':>9} {'absorb':>7}")
for r in ok[:15]:
    print(f"{r['D']:5.2f} {r['rpm']:5.0f} {r['B']:2d} {r['pitch_ratio']:5.2f} "
          f"{r['eta_loiter']:9.4f} {r['J_loiter']:5.2f} {r['tip_mach']:5.3f} "
          f"{r['climb_kw']:9.2f} {r['absorb_ratio']:7.2f}")
json.dump(ok, open('opt_runs/prop_sweep.json','w'), indent=2)
print(f"\nWROTE opt_runs/prop_sweep.json ({len(ok)} candidates)")
