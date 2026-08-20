"""Geometry-coupled optimisation. Writes opt_runs/coupled.json."""
import json, time, torch
from argus7.opt.design_space import calibrate
from argus7.opt.coupled import evaluate_coupled, refine_augmented_lagrangian, cd0_from_geometry, oswald_from_planform

torch.set_default_dtype(torch.float32)
dev = "cuda"
k = calibrate()
# wing_area, AR, taper, t/c, MTOW, altitude, BSFC
LO = torch.tensor([2.5, 14.0, 0.30, 0.10, 180.0, 4000.0, 0.25], device=dev)
HI = torch.tensor([6.0, 30.0, 0.70, 0.20, 320.0, 4500.0, 0.32], device=dev)
NAMES = ["wing_area_m2","aspect_ratio","taper_ratio","thickness_ratio","mtow_kg","altitude_m","bsfc_kg_per_kwh"]

def describe(x):
    ev = evaluate_coupled(x.unsqueeze(0), k)
    d = {n: float(v) for n, v in zip(NAMES, x.tolist())}
    d.update({kk: float(vv) if kk != "feasible" else bool(vv) for kk, vv in
              ((kk, ev[kk].squeeze()) for kk in ("endurance_h","cd0","oswald_e","fuel_kg","tank_kg","empty_kg","span_m","violation","feasible"))})
    d["endurance_d"] = d["endurance_h"]/24.0
    return d

out = {"calibration_k": k}
N, CH = 24_000_000, 2_000_000
eng = torch.quasirandom.SobolEngine(dimension=7, scramble=True, seed=7)
best = {"e": -1.0, "x": None}; nfeas = 0
t = time.perf_counter(); done = 0
while done < N:
    m = min(CH, N-done)
    x = LO + eng.draw(m).to(dev)*(HI-LO)
    ev = evaluate_coupled(x, k)
    f = ev["feasible"]; nfeas += int(f.sum())
    if bool(f.any()):
        em = torch.where(f, ev["endurance_h"], torch.full_like(ev["endurance_h"], -1.0))
        j = int(torch.argmax(em))
        if float(em[j]) > best["e"]:
            best = {"e": float(em[j]), "x": x[j].clone()}
    done += m; del x, ev
dt = time.perf_counter()-t
out["stage1"] = {"n": N, "seconds": dt, "rate_M_per_s": N/dt/1e6, "n_feasible": nfeas, "pct_feasible": 100*nfeas/N}
print(f"STAGE 1 coupled: {N:,} in {dt:.1f}s ({N/dt/1e6:.2f} M/s), feasible {nfeas:,} ({100*nfeas/N:.3f}%)", flush=True)
print("best feasible from DOE:", json.dumps(describe(best["x"]), indent=2), flush=True)

xr, _ = refine_augmented_lagrangian(best["x"], k, LO, HI, outer=12, inner=150)
out["best_feasible"] = describe(xr)
torch.save(xr.cpu(), "design/opt_coupled.pt")
print("STAGE 2 augmented-Lagrangian:", json.dumps(out["best_feasible"], indent=2), flush=True)

xb = torch.tensor([3.9,22.0,0.45,0.1371,250.0,4000.0,0.270], device=dev)
out["baseline_v1_coupled"] = describe(xb)
print("BASELINE under the same coupled model:", json.dumps(out["baseline_v1_coupled"], indent=2), flush=True)
json.dump(out, open("opt_runs/coupled_alt4000.json","w"), indent=2)
print("WROTE opt_runs/coupled.json", flush=True)
