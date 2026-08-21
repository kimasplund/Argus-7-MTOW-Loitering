"""Where does endurance actually stop? Sweep the MTOW cap with stability enforced."""
import json, torch, importlib.util, sys
spec=importlib.util.spec_from_file_location("lay","scripts/run_optimisation_layout.py")
# reuse the evaluate() from the layout script without re-running its main block
src=open("scripts/run_optimisation_layout.py").read()
src=src.split("N,CH=")[0]
ns={}; exec(compile(src,"lay","exec"), ns)
evaluate=ns["evaluate"]; NAMES=ns["NAMES"]; dev=ns["dev"]
LO=ns["LO"].clone(); HI=ns["HI"].clone()
rows=[]
for cap in (200.,250.,300.,400.,500.,600.):
    lo=LO.clone(); hi=HI.clone(); hi[4]=cap
    eng=torch.quasirandom.SobolEngine(dimension=11,scramble=True,seed=41)
    best={"e":-1.,"x":None}; done=0; N=40_000_000
    while done<N:
        m=min(2_000_000,N-done)
        x=lo+eng.draw(m).to(dev)*(hi-lo); ev=evaluate(x); f=ev["feasible"]
        if bool(f.any()):
            em=torch.where(f,ev["endurance_h"],torch.full_like(ev["endurance_h"],-1.))
            j=int(torch.argmax(em))
            if float(em[j])>best["e"]: best={"e":float(em[j]),"x":x[j].clone()}
        done+=m; del x,ev
    if best["x"] is None:
        print(f"{cap:6.0f} kg: no stable feasible design"); continue
    d={n:float(v) for n,v in zip(NAMES,best["x"].tolist())}
    ev=evaluate(best["x"].unsqueeze(0))
    rows.append(dict(cap=cap, hours=best["e"], days=best["e"]/24, mtow=d["mtow_kg"],
                     span=float(ev["span_m"]), S=d["wing_area_m2"], AR=d["aspect_ratio"],
                     engine=d["engine_kw"], sm_full=float(ev["sm_full"]),
                     x_le=d["x_le_frac"], fuel=float(ev["fuel_kg"])))
    r=rows[-1]
    print(f"{cap:6.0f} kg cap -> {r['days']:5.2f} d  MTOW {r['mtow']:6.1f}  span {r['span']:5.2f} m  "
          f"S {r['S']:5.2f}  AR {r['AR']:5.1f}  engine {r['engine']:5.2f} kW  SM {r['sm_full']*100:+5.1f}%", flush=True)
json.dump(rows, open("opt_runs/mtow_scaling.json","w"), indent=2)
