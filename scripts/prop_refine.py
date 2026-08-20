"""Refine the best fixed-pitch props, and price variable pitch against them."""
import math, json, itertools
from argus7.prop.bemt import constant_pitch_blade, run_bemt
from argus7.mission.atmosphere import isa_numpy
from argus7.design.schema import load_design
from argus7.design.geometry import derive_wing

d=load_design('design/argus7_v2.yaml'); g=derive_wing(d.wing)
P_RATED=d.propulsion.power_max_kw*1000; ALT=d.mission.loiter_altitude_m
rho_l=float(isa_numpy(ALT).density_kgm3); rho_sl=float(isa_numpy(0.0).density_kgm3)
cl=1.21; W=(d.masses.mtow-0.5*d.masses.fuel)*9.80665
V_l=math.sqrt(2*W/(rho_l*g.area_m2*cl))
cd=d.aero.cd0+cl**2/(math.pi*g.aspect_ratio*d.aero.oswald_e)
T_req=W/(cl/cd); V_cl=30.0
BOOM=0.6206-0.045

print("=== FIXED PITCH, refined grid ===")
print(f"{'D':>5} {'rpm':>5} {'B':>2} {'p/D':>5} {'eta':>7} {'absorb':>7} {'tipM':>6} {'score':>7}")
best=[]
for D,rpm,B,pd in itertools.product([0.88,0.92,0.96,1.00,1.04],[1900,2050,2200,2350],[2,3],
                                    [0.90,0.95,1.00,1.05,1.10]):
    if D/2 > BOOM-0.05: continue
    bl=constant_pitch_blade(D,pd*D,blades=B)
    try:
        L=run_bemt(bl,rpm,V_l,rho_l)
        if not (L.converged and L.thrust_n>=T_req*0.97 and L.tip_mach<0.75): continue
        C=None
        for rc in (rpm,rpm*1.1,rpm*1.2,rpm*1.3,rpm*1.4):
            c=run_bemt(bl,rc,V_cl,rho_sl)
            if c.converged and (C is None or abs(c.power_w-P_RATED)<abs(C.power_w-P_RATED)): C=c
        if C is None: continue
        ab=C.power_w/P_RATED
        if not (0.92<=ab<=1.12): continue
        score=L.eta-0.30*abs(ab-1.0)
        best.append((score,D,rpm,B,pd,L.eta,ab,L.tip_mach,C.rpm))
    except Exception: continue
best.sort(reverse=True)
for s,D,rpm,B,pd,eta,ab,tm,cr in best[:10]:
    print(f"{D:5.2f} {rpm:5.0f} {B:2d} {pd:5.2f} {eta:7.4f} {ab:7.3f} {tm:6.3f} {s:7.4f}")

print("\n=== VARIABLE PITCH: same disc, pitch free at each condition ===")
s,D,rpm,B,pd,eta_fix,ab,tm,cr = best[0]
eta_vp=0; pd_vp=None
for p in [0.55,0.65,0.75,0.85,0.95,1.05,1.15]:
    bl=constant_pitch_blade(D,p*D,blades=B)
    L=run_bemt(bl,rpm,V_l,rho_l)
    if L.converged and L.thrust_n>=T_req*0.97 and L.eta>eta_vp: eta_vp,pd_vp=L.eta,p
print(f"  best disc {D:.2f} m, {B} blades, {rpm:.0f} rpm")
print(f"  fixed pitch p/D {pd:.2f} -> eta_loiter {eta_fix:.4f}")
print(f"  variable, loiter-optimal p/D {pd_vp:.2f} -> eta_loiter {eta_vp:.4f}   gain {100*(eta_vp/eta_fix-1):+.2f}%")

# endurance impact vs the 0.84 assumed in the mission sim
print("\n=== ENDURANCE IMPACT (mission sim assumes eta_prop = 0.84) ===")
for tag,e in [("fixed pitch",eta_fix),("variable pitch",eta_vp)]:
    print(f"  {tag:15s} eta {e:.4f} -> endurance x {e/0.84:.4f} = {117.05*e/0.84:.1f} h ({117.05*e/0.84/24:.2f} d), "
          f"{117.05*(e/0.84-1):+.1f} h vs assumed")
# reduction ratio
print(f"\n=== REDUCTION RATIO (small 4-stroke peaks ~7000-8000 rpm) ===")
for erpm in (6500,7500,8500):
    print(f"  engine {erpm} rpm -> reduction {erpm/rpm:.2f}:1 for {rpm:.0f} prop rpm")
print(f"\n  boom clearance: prop radius {D/2:.3f} m vs boom inner {BOOM:.3f} m -> {1000*(BOOM-D/2):.0f} mm")
json.dump({"D":D,"rpm":rpm,"blades":B,"pitch_ratio":pd,"eta_fixed":eta_fix,
           "eta_variable":eta_vp,"pitch_ratio_vp":pd_vp,"absorb_ratio":ab,
           "climb_rpm":cr,"tip_mach":tm}, open('opt_runs/prop_final.json','w'), indent=2)
