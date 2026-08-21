"""Denser MTOW sweep with gradient refinement at each cap, to remove DOE noise."""
import json, torch
src=open("scripts/run_optimisation_layout.py").read().split("N,CH=")[0]
ns={}; exec(compile(src,"lay","exec"), ns)
evaluate=ns["evaluate"]; NAMES=ns["NAMES"]; dev=ns["dev"]; LO=ns["LO"]; HI=ns["HI"]
CAPS=[180.,200.,225.,250.,300.,350.,400.,450.,500.,600.]
rows=[]
for cap in CAPS:
    lo=LO.clone(); hi=HI.clone(); hi[4]=cap
    eng=torch.quasirandom.SobolEngine(dimension=11,scramble=True,seed=97)
    best={"e":-1.,"x":None}; done=0; N=24_000_000
    while done<N:
        m=min(2_000_000,N-done)
        x=lo+eng.draw(m).to(dev)*(hi-lo); ev=evaluate(x); f=ev["feasible"]
        if bool(f.any()):
            em=torch.where(f,ev["endurance_h"],torch.full_like(ev["endurance_h"],-1.))
            j=int(torch.argmax(em))
            if float(em[j])>best["e"]: best={"e":float(em[j]),"x":x[j].clone()}
        done+=m; del x,ev
    if best["x"] is None: continue
    # refine
    z=torch.logit(torch.clamp((best["x"]-lo)/(hi-lo),1e-4,1-1e-4)).clone().requires_grad_(True)
    mu=torch.tensor(10.0,device=dev); lam=torch.zeros((),device=dev)
    for _ in range(5):
        opt=torch.optim.Adam([z],lr=0.02)
        for _ in range(60):
            opt.zero_grad()
            xx=lo+torch.sigmoid(z)*(hi-lo); ev=evaluate(xx.unsqueeze(0)); gg=ev["violation"].squeeze()
            (-ev["endurance_h"].squeeze()+lam*gg+0.5*mu*gg**2).backward(); opt.step()
        with torch.no_grad():
            xx=lo+torch.sigmoid(z)*(hi-lo)
            lam=lam+mu*evaluate(xx.unsqueeze(0))["violation"].squeeze(); mu=mu*2.5
    with torch.no_grad(): xr=lo+torch.sigmoid(z)*(hi-lo)
    ev=evaluate(xr.unsqueeze(0))
    if not bool(ev["feasible"].squeeze()):
        xr=best["x"]; ev=evaluate(xr.unsqueeze(0))
    d={n:float(v) for n,v in zip(NAMES,xr.tolist())}
    rows.append(dict(cap=cap, hours=float(ev["endurance_h"]), days=float(ev["endurance_h"])/24,
        mtow=d["mtow_kg"], span=float(ev["span_m"]), S=d["wing_area_m2"], AR=d["aspect_ratio"],
        taper=d["taper_ratio"], tc=d["thickness_ratio"], engine=d["engine_kw"],
        x_le=d["x_le_frac"], Vh=d["tail_volume"], arm=d["tail_arm_frac"],
        sm_full=float(ev["sm_full"]), sm_dry=float(ev["sm_dry"]),
        fuel=float(ev["fuel_kg"]), tank=float(ev["tank_kg"]), empty=float(ev["empty_kg"]),
        load=float(ev["load"]), bsfc=float(ev["bsfc_eff"]), cd0=float(ev["cd0"]), e=float(ev["oswald_e"])))
    r=rows[-1]
    print(f"{cap:6.0f} -> {r['days']:5.2f} d  MTOW {r['mtow']:6.1f}  span {r['span']:5.2f}  S {r['S']:5.2f}  "
          f"AR {r['AR']:5.1f}  kW {r['engine']:5.2f}  SM {r['sm_full']*100:+5.1f}/{r['sm_dry']*100:+5.1f}", flush=True)
json.dump(rows, open("opt_runs/mtow_scaling2.json","w"), indent=2)
print("WROTE opt_runs/mtow_scaling2.json", flush=True)
