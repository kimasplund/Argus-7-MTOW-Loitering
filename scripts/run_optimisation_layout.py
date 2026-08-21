"""Full-layout optimisation: 11 variables, stability as a HARD constraint.

Adds the three layout variables the earlier runs lacked -- wing station, tail
volume, tail arm -- and requires 5% <= static margin <= 15% MAC at BOTH full fuel
and dry. The previous design was adopted against a stability gate nothing could
evaluate; this makes it a constraint the search cannot escape.
"""
import json, time, torch
from argus7.opt.design_space import calibrate, wing_mass_kg, wing_fuel_capacity_kg
from argus7.opt.coupled import cd0_from_geometry, oswald_from_planform, bsfc_at_load, climb_power_required_w, PROP_ETA
from argus7.opt.layout import static_margin_envelope, wing_geometry
from argus7.mission.sim import simulate_loiter, loiter_cl, drag_polar
from argus7.mission.atmosphere import isa

torch.set_default_dtype(torch.float32)
dev="cuda"; k=calibrate()
NAMES=["wing_area_m2","aspect_ratio","taper_ratio","thickness_ratio","mtow_kg",
       "altitude_m","bsfc_full","engine_kw","x_le_frac","tail_volume","tail_arm_frac"]
# Bounds opened at the sponsor's direction: run the optimiser free, ignore
# regulatory bands. MTOW to 600 kg, taper to 1.0 (untapered allowed), wing area
# to 12 m2, span limit relaxed 12 -> 20 m. Whatever binds is now information.
LO=torch.tensor([2.5,12.0,0.25,0.10,150.0,4000.0,0.250, 3.0,0.10,0.30,0.50],device=dev)
HI=torch.tensor([12.0,35.0,1.00,0.22,600.0,4500.0,0.320,40.0,0.75,1.60,2.00],device=dev)
SM_LO, SM_HI = 0.05, 0.15

def evaluate(x):
    S,AR,lam,tc,mtow,alt,bsfc_f,pkw,xle,Vh,arm_f = (x[...,i] for i in range(11))
    cd0=cd0_from_geometry(S,tc); e=oswald_from_planform(AR,lam)
    span,c_root,mac,_=wing_geometry(S,AR,lam)
    m_wing=wing_mass_kg(S,AR,lam,mtow,tc,k)
    airframe=m_wing+28.0
    powertrain=25.0*pkw/17.0
    empty=airframe+powertrain+6.0+7.0
    fuel=mtow-empty-50.0
    tank=wing_fuel_capacity_kg(S,AR,lam,tc)
    clmax=torch.full_like(S,1.6)

    rho=isa(alt).density_kgm3
    cl=loiter_cl(cd0,AR,e,clmax); cd=drag_polar(cl,cd0,AR,e)
    w_mid=(mtow-0.5*torch.clamp(fuel,min=0.))*9.80665
    v_mid=torch.sqrt(2*w_mid/(rho*S*cl))
    shaft=w_mid/(cl/cd)*v_mid/PROP_ETA+500.0/0.75
    load=shaft/(pkw*1000.0)
    bsfc=bsfc_at_load(bsfc_f,load)
    r=simulate_loiter(mass_total_kg=mtow,mass_fuel_kg=torch.clamp(fuel,min=1e-3),
        wing_area_m2=S,aspect_ratio=AR,cd0=cd0,oswald_e=e,cl_max=clmax,altitude_m=alt,
        bsfc_kg_per_kwh=bsfc,payload_power_w=torch.full_like(S,500.),
        prop_efficiency=0.858,n_steps=120)

    sm_full,sm_dry=static_margin_envelope(S,AR,lam,tc,mtow,xle,Vh,arm_f,
        fuel_kg=torch.clamp(fuel,min=0.),wing_mass_kg=m_wing,airframe_kg=airframe,
        powertrain_kg=powertrain,avionics_kg=torch.full_like(S,6.),
        recovery_kg=torch.full_like(S,7.),payload_kg=torch.full_like(S,50.))

    p_climb=climb_power_required_w(mtow,S,AR,cd0,e,clmax)
    v = (torch.clamp(span-20.0,min=0.)/20.0
         + torch.clamp(fuel-tank,min=0.)/50.0
         + torch.clamp(-fuel,min=0.)/50.0
         + torch.clamp(p_climb-pkw*1000.,min=0.)/5000.0
         + torch.clamp(load-1.0,min=0.)
         + torch.clamp(SM_LO-sm_full,min=0.)*10 + torch.clamp(sm_full-SM_HI,min=0.)*10
         + torch.clamp(SM_LO-sm_dry ,min=0.)*10 + torch.clamp(sm_dry -SM_HI,min=0.)*10)
    return dict(endurance_h=r.endurance_h,cd0=cd0,oswald_e=e,fuel_kg=fuel,tank_kg=tank,
                empty_kg=empty,span_m=span,load=load,bsfc_eff=bsfc,sm_full=sm_full,
                sm_dry=sm_dry,mac=mac,violation=v,feasible=v<=1e-6)

def describe(x):
    ev=evaluate(x.unsqueeze(0)); d={n:float(v) for n,v in zip(NAMES,x.tolist())}
    for kk in ("endurance_h","cd0","oswald_e","fuel_kg","tank_kg","empty_kg","span_m",
               "load","bsfc_eff","sm_full","sm_dry","mac","violation"):
        d[kk]=float(ev[kk].squeeze())
    d["feasible"]=bool(ev["feasible"].squeeze()); d["endurance_d"]=d["endurance_h"]/24
    return d

N,CH=200_000_000,2_000_000
eng=torch.quasirandom.SobolEngine(dimension=11,scramble=True,seed=31)
best={"e":-1.,"x":None}; nf=0; t=time.perf_counter(); done=0
while done<N:
    m=min(CH,N-done)
    x=LO+eng.draw(m).to(dev)*(HI-LO); ev=evaluate(x); f=ev["feasible"]; nf+=int(f.sum())
    if bool(f.any()):
        em=torch.where(f,ev["endurance_h"],torch.full_like(ev["endurance_h"],-1.))
        j=int(torch.argmax(em))
        if float(em[j])>best["e"]: best={"e":float(em[j]),"x":x[j].clone()}
    done+=m; del x,ev
dt=time.perf_counter()-t
print(f"STAGE 1: {N:,} in {dt:.1f}s ({N/dt/1e6:.1f} M/s), STABLE+feasible {nf:,} ({100*nf/N:.3f}%)",flush=True)
if best["x"] is None:
    print("NO FEASIBLE STABLE DESIGN FOUND", flush=True); raise SystemExit
out={"best":describe(best["x"]),"stage1":{"n":N,"n_feasible":nf,"pct":100*nf/N}}
print(json.dumps(out["best"],indent=2),flush=True)
torch.save(best["x"].cpu(),"design/opt_layout.pt")
# gradient refinement under an augmented Lagrangian
z=torch.logit(torch.clamp((best["x"]-LO)/(HI-LO),1e-4,1-1e-4)).clone().requires_grad_(True)
mu=torch.tensor(10.0,device=dev); lam=torch.zeros((),device=dev)
for _ in range(12):
    opt=torch.optim.Adam([z],lr=0.02)
    for _ in range(150):
        opt.zero_grad()
        xx=LO+torch.sigmoid(z)*(HI-LO); ev=evaluate(xx.unsqueeze(0))
        gg=ev["violation"].squeeze()
        (-ev["endurance_h"].squeeze()+lam*gg+0.5*mu*gg**2).backward(); opt.step()
    with torch.no_grad():
        xx=LO+torch.sigmoid(z)*(HI-LO)
        lam=lam+mu*evaluate(xx.unsqueeze(0))["violation"].squeeze(); mu=mu*2.5
with torch.no_grad(): xr=LO+torch.sigmoid(z)*(HI-LO)
out["refined"]=describe(xr); torch.save(xr.cpu(),"design/opt_layout_refined.pt")
print("REFINED:",json.dumps(out["refined"],indent=2),flush=True)
json.dump(out,open("opt_runs/layout.json","w"),indent=2)
print("WROTE opt_runs/layout.json",flush=True)
