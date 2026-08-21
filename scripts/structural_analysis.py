"""Full structural analysis of ARGUS-7 v5.0. CalculiX + analytic aeroelasticity.

Four questions, in order of how much each could change the design:
  1. flutter and divergence -- unvalidated, and could cap V_max below the power limit
  2. static +5.7g ultimate  -- does the spar survive, and how far does the tip move
  3. compression-cap buckling -- the report says this governs the sizing
  4. boom torsion modes -- the 22.7 Hz first-torsion against prop 1P
"""
import json, math, re
from pathlib import Path
from argus7.design.schema import load_design
from argus7.design.geometry import derive_wing, derive_booms
from argus7.mission.atmosphere import isa_numpy
from argus7.struct.wing_beam import (write_inp, run, stations, E_CARBON, G_CARBON,
                                     RHO_CARBON, SIGMA_ALLOW, N_ULT, GRAV)

d = load_design("design/argus7_v5.yaml")
g = derive_wing(d.wing); semi = g.span_m / 2
st = stations(d, 21)
res = {}

def frd_max_disp(p: Path):
    """Max |D3| over all nodes. CalculiX expands beams, so node ids are not ours."""
    best = 0.0; block = False
    for line in p.read_text().splitlines():
        if line.startswith(" -4") and "DISP" in line: block = True; continue
        if block:
            if line.startswith(" -3"): break
            if line.startswith(" -1"):
                body = line[3:]
                vals = [body[10+12*i:10+12*(i+1)] for i in range(3)]
                try: best = max(best, abs(float(vals[2])))
                except ValueError: pass
    return best

# ---- 1. static ultimate ----------------------------------------------------
write_inp(d, Path("fea_runs/wing_static.inp"), "static"); run(Path("fea_runs/wing_static.inp"))
tip = frd_max_disp(Path("fea_runs/wing_static.frd"))
w = d.masses.mtow * GRAV
M = [N_ULT*w*semi*0.40*0.78*(1-i/20)**2*(1+0.5*i/20) for i in range(21)]
dy = semi/20; th=[0.0]; de=[0.0]
for i in range(1,21):
    k0=M[i-1]/(E_CARBON*st[i-1].I); k1=M[i]/(E_CARBON*st[i].I)
    th.append(th[-1]+(k0+k1)/2*dy); de.append(de[-1]+(th[i-1]+th[i])/2*dy)
sig = M[0]/(st[0].depth*st[0].cap_area)
res["static"] = dict(tip_mm=tip*1000, tip_pct_semispan=100*tip/semi,
                     limit_tip_pct=100*tip/semi*3.8/5.7, analytic_mm=de[-1]*1000,
                     root_stress_MPa=sig/1e6, allowable_MPa=SIGMA_ALLOW/1e6,
                     margin=SIGMA_ALLOW/sig-1)
print("=== 1. STATIC +5.7 g ULTIMATE ===")
print(f"  tip deflection      {tip*1000:8.1f} mm = {100*tip/semi:.2f}% semi-span")
print(f"  at limit (+3.8 g)   {tip*1000*3.8/5.7:8.1f} mm = {100*tip/semi*3.8/5.7:.2f}%")
print(f"  analytic M/EI check {de[-1]*1000:8.1f} mm  -> FEA/analytic {tip/de[-1] if de[-1] else 0:.3f}")
print(f"  root cap stress     {sig/1e6:8.0f} MPa vs {SIGMA_ALLOW/1e6:.0f} allowable, margin {SIGMA_ALLOW/sig-1:+.1%}")

# ---- 2. modal --------------------------------------------------------------
write_inp(d, Path("fea_runs/wing_modal.inp"), "frequency"); out = run(Path("fea_runs/wing_modal.inp"))
dat = Path("fea_runs/wing_modal.dat")
freqs = []
if dat.exists():
    grab = False
    for line in dat.read_text().splitlines():
        if "MODE NO" in line: grab = True; continue
        if grab:
            f = line.split()
            if len(f) >= 4:
                try: freqs.append(float(f[3]))       # cycles/time = Hz
                except ValueError: pass
            elif freqs: break
res["modes_hz"] = freqs[:6]
print("\n=== 2. MODAL (CalculiX) ===")
for i,f in enumerate(freqs[:6],1): print(f"  mode {i}: {f:8.2f} Hz")

# ---- 3. buckling of the compression cap ------------------------------------
b_cap = math.sqrt(st[0].cap_area*4); t_cap = st[0].cap_area/b_cap
rib = 0.35
sig_cr = math.pi**2*E_CARBON/(12*(1-0.3**2))*(t_cap/rib)**2
res["buckling"] = dict(cap_width_mm=b_cap*1000, cap_t_mm=t_cap*1000,
                       rib_pitch_m=rib, sigma_cr_MPa=sig_cr/1e6, applied_MPa=sig/1e6,
                       margin=sig_cr/sig-1)
print("\n=== 3. COMPRESSION-CAP BUCKLING ===")
print(f"  cap {b_cap*1000:.0f} x {t_cap*1000:.1f} mm, rib pitch {rib*1000:.0f} mm")
print(f"  critical {sig_cr/1e6:.0f} MPa vs applied {sig/1e6:.0f} MPa -> margin {sig_cr/sig-1:+.1%}")

# ---- 4. divergence and flutter --------------------------------------------
GJ = G_CARBON*st[0].J
rho = float(isa_numpy(d.mission.loiter_altitude_m).density_kgm3)
a_w = 2*math.pi*g.aspect_ratio/(2+math.sqrt(g.aspect_ratio**2+4))
e_ac = 0.25*g.mac_m
q_div = GJ*math.pi**2/(4*semi**2*a_w*g.mac_m*e_ac)
v_div = math.sqrt(2*q_div/rho)
m_wing = 0.5*(d.masses.airframe*0.6)
r2 = (0.25*g.mac_m)**2
w_t = math.sqrt(GJ/(m_wing*r2*semi**2/3)) if m_wing>0 else 0
v_flut = 0.55*w_t*g.mac_m/2*math.sqrt(2/(math.pi*rho*g.mac_m**2/(4*m_wing/(2*semi))))
res["aeroelastic"] = dict(GJ_kNm2=GJ/1e3, v_div_kmh=v_div*3.6,
                          torsion_hz=w_t/(2*math.pi), v_flutter_kmh=v_flut*3.6)
print("\n=== 4. AEROELASTIC (analytic, first-order) ===")
print(f"  root GJ {GJ/1e3:.1f} kN.m2, wing first torsion ~{w_t/(2*math.pi):.1f} Hz")
print(f"  DIVERGENCE speed   {v_div*3.6:7.0f} km/h TAS")
print(f"  flutter estimate   {v_flut*3.6:7.0f} km/h TAS")
print(f"  power-limited V_max is 207 km/h")
lim = min(v_div*3.6, v_flut*3.6)
print(f"  -> aeroelastic limit {'is ABOVE the power limit, so power governs' if lim>207 else 'CAPS the aircraft BELOW its power limit'}")

# ---- 5. boom torsion -------------------------------------------------------
bg = derive_booms(d); r_out = d.booms.diameter_m/2; t_b = 0.0018
J_b = math.pi*((r_out)**4-(r_out-t_b)**4)/2
GJ_b = G_CARBON*J_b
tp_m = 2.0
I_p = tp_m*(0.4*g.mac_m)**2
f_bt = 1/(2*math.pi)*math.sqrt(GJ_b/(I_p*bg.length_m))
res["boom"] = dict(length_m=bg.length_m, GJ_kNm2=GJ_b/1e3, torsion_hz=f_bt,
                   prop_1p_hz=d.propulsion.prop_rpm/60, bpf_hz=d.propulsion.prop_rpm*2/60)
print("\n=== 5. BOOM TORSION vs PROP EXCITATION ===")
print(f"  boom {bg.length_m:.2f} m, GJ {GJ_b/1e3:.1f} kN.m2 -> first torsion {f_bt:.1f} Hz")
print(f"  prop 1P {d.propulsion.prop_rpm/60:.1f} Hz, blade passage {d.propulsion.prop_rpm*2/60:.1f} Hz")
sep = min(abs(f_bt-d.propulsion.prop_rpm/60), abs(f_bt-d.propulsion.prop_rpm*2/60))
print(f"  nearest separation {sep:.1f} Hz -> {'OK' if sep>5 else 'RESONANCE RISK'}")
json.dump(res, open("fea_runs/structural.json","w"), indent=2)
print("\nwrote fea_runs/structural.json")
