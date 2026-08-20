"""Stage 1-3 design-point optimisation. Writes opt_runs/result.json."""
import json, time, torch
from argus7.opt.design_space import calibrate
from argus7.opt.optimise import sobol_search, refine, describe

torch.set_default_dtype(torch.float32)
k = calibrate()
out = {"calibration_k": k}
print(f"mass model calibrated k={k:.5f}", flush=True)

N = 8_000_000
t = time.perf_counter()
best, best_feas, n_feas = sobol_search(N, k, device="cuda", seed=1)
dt = time.perf_counter() - t
out["stage1"] = {"n": N, "seconds": dt, "rate_M_per_s": N/dt/1e6,
                 "n_feasible": n_feas, "pct_feasible": 100*n_feas/N}
print(f"STAGE 1: {N:,} in {dt:.1f}s ({N/dt/1e6:.2f} M/s), feasible {n_feas:,} ({100*n_feas/N:.3f}%)", flush=True)

if best_feas["x"] is not None:
    xr, _ = refine(best_feas["x"], k, steps=1200, enforce_feasible=True)
    out["best_feasible"] = describe(xr, k)
    torch.save(xr.cpu(), "design/opt_feasible.pt")
    print("STAGE 2 feasible:", json.dumps(out["best_feasible"], indent=2), flush=True)

xu, _ = refine(best["x"], k, steps=1200, enforce_feasible=False)
out["best_unconstrained"] = describe(xu, k)
torch.save(xu.cpu(), "design/opt_unconstrained.pt")
print("STAGE 2 unconstrained:", json.dumps(out["best_unconstrained"], indent=2), flush=True)

xb = torch.tensor([3.9, 22.0, 0.45, 0.1371, 250.0, 4000.0, 0.020, 0.85, 0.270], device="cuda")
out["baseline_v1"] = describe(xb, k)
print("BASELINE:", json.dumps(out["baseline_v1"], indent=2), flush=True)

json.dump(out, open("opt_runs/result.json", "w"), indent=2)
print("WROTE opt_runs/result.json", flush=True)
