"""Final optimisation: 8 variables, part-load BSFC, engine right-sizing, corrected tank."""
import json, time, torch
from argus7.opt.design_space import calibrate
from argus7.opt.coupled import evaluate_full, refine_augmented_lagrangian
import argus7.opt.coupled as C

torch.set_default_dtype(torch.float32)
dev="cuda"; k=calibrate()
NAMES=["wing_area_m2","aspect_ratio","taper_ratio","thickness_ratio","mtow_kg","altitude_m","bsfc_full","engine_kw"]
LO=torch.tensor([2.5,14.0,0.30,0.10,180.0,4000.0,0.250,4.0],device=dev)
HI=torch.tensor([6.0,30.0,0.70,0.20,320.0,4500.0,0.320,20.0],device=dev)

def describe(x):
    ev=evaluate_full(x.unsqueeze(0),k)
    d={n:float(v) for n,v in zip(NAMES,x.tolist())}
    for kk in ("endurance_h","cd0","oswald_e","fuel_kg","tank_kg","empty_kg","span_m",
               "load_fraction","bsfc_eff","climb_kw_req","violation"):
        d[kk]=float(ev[kk].squeeze())
    d["feasible"]=bool(ev["feasible"].squeeze()); d["endurance_d"]=d["endurance_h"]/24.0
    return d

out={"calibration_k":k}
N,CH=32_000_000,2_000_000
eng=torch.quasirandom.SobolEngine(dimension=8,scramble=True,seed=11)
best={"e":-1.0,"x":None}; nf=0
t=time.perf_counter(); done=0
while done<N:
    m=min(CH,N-done)
    x=LO+eng.draw(m).to(dev)*(HI-LO)
    ev=evaluate_full(x,k); f=ev["feasible"]; nf+=int(f.sum())
    if bool(f.any()):
        em=torch.where(f,ev["endurance_h"],torch.full_like(ev["endurance_h"],-1.0))
        j=int(torch.argmax(em))
        if float(em[j])>best["e"]: best={"e":float(em[j]),"x":x[j].clone()}
    done+=m; del x,ev
dt=time.perf_counter()-t
out["stage1"]={"n":N,"seconds":dt,"rate_M_per_s":N/dt/1e6,"n_feasible":nf,"pct":100*nf/N}
print(f"STAGE 1: {N:,} in {dt:.1f}s ({N/dt/1e6:.2f} M/s), feasible {nf:,} ({100*nf/N:.2f}%)",flush=True)
print("DOE best:",json.dumps(describe(best["x"]),indent=2),flush=True)

# refine using the full evaluator
C.evaluate_coupled = lambda x,kc,**kw: evaluate_full(x,kc,**kw)
xr,_=refine_augmented_lagrangian(best["x"],k,LO,HI,outer=12,inner=150)
out["best"]=describe(xr); torch.save(xr.cpu(),"design/opt_final.pt")
print("REFINED:",json.dumps(out["best"],indent=2),flush=True)

xb=torch.tensor([3.9,22.0,0.45,0.1371,250.0,4000.0,0.257,17.0],device=dev)
out["baseline_v1"]=describe(xb)
print("BASELINE v1.0 honest:",json.dumps(out["baseline_v1"],indent=2),flush=True)
json.dump(out,open("opt_runs/final.json","w"),indent=2)
print("WROTE opt_runs/final.json",flush=True)
