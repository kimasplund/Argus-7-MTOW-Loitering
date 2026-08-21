"""Mutation testing: does the suite actually have teeth?

A passing suite proves nothing about a suite. The only way to know whether a test
would catch a defect is to inject one and watch. Each mutant below is a plausible
edit -- a sign flip, an off-by-one exponent, a loosened constant, a dropped term --
of the kind a real change would introduce.

A mutant that SURVIVES is a hole in the suite, and is the whole point of the run.
"""
import subprocess, pathlib, shutil, sys, tempfile, json

REPO = pathlib.Path(__file__).resolve().parent.parent

MUTANTS = [
    # (file, find, replace, description, which tests should catch it)
    ("argus7/design/geometry.py", "b  = math.sqrt(AR * S)", "b  = math.sqrt(AR * S) * 1.001",
     "span 0.1% wrong", "closure"),
    ("argus7/design/geometry.py", "mac = (2.0 / 3.0) * cr", "mac = (2.0 / 4.0) * cr",
     "MAC formula 2/3 -> 2/4", "closure"),
    ("argus7/design/geometry.py", "TOL = 1e-9", "TOL = 1e-1",
     "closure tolerance loosened 1e8x", "closure guard itself"),
    ("argus7/cad/airfoil_coords.py", "xr = xc * ct + zc * st", "xr = xc * ct - zc * st",
     "twist rotation sign flipped (the bug that appeared twice)", "washout tests"),
    ("argus7/mission/sim.py", "cl_stall_limited = cl_max / stall_margin**2",
     "cl_stall_limited = cl_max / stall_margin", "stall margin squared -> linear",
     "loiter CL / endurance gates"),
    ("argus7/mission/sim.py", "drag = weight / ld", "drag = weight / (ld * 1.05)",
     "drag 5% low", "Breguet + report gates"),
    ("argus7/mission/sim.py", "return cd0 + cl**2 / (torch.pi * aspect_ratio * oswald_e)",
     "return cd0 + cl**2 / (torch.pi * aspect_ratio)", "Oswald factor dropped from polar",
     "polar + endurance gates"),
    ("argus7/mission/atmosphere.py", "LAPSE_RATE_KM = -0.0065", "LAPSE_RATE_KM = -0.0064",
     "ISA lapse rate 1.5% wrong", "atmosphere table tests"),
    ("argus7/opt/design_space.py", "SIGMA_CAP_PA = 600e6", "SIGMA_CAP_PA = 800e6",
     "spar allowable raised 33% (makes wings lighter for free)", "mass model"),
    ("argus7/opt/design_space.py", "k_area=0.6062", "k_area=0.68",
     "the NACA-4 shape factor this project already caught once", "fuel volume"),
    # --- mutants aimed at the new CG/balance module -------------------------
    ("argus7/analysis/balance.py", "    w = c ** 2", "    w = c",
     "fuel spanwise weighting exponent dropped (chord^2 -> chord) in fuel_centroid_x",
     "fuel station / CG travel"),
    ("argus7/analysis/balance.py",
     "tail_term = vh * (a_t / a_w) * (1.0 - de_da) * ETA_TAIL",
     "tail_term = vh * (a_t / a_w) * ETA_TAIL",
     "downwash term (1 - de/da) dropped from the neutral-point tail term",
     "neutral point + AVL cross-check"),
    ("argus7/analysis/balance.py",
     "tan_half = tan_le - (2.0 / aspect_ratio) * (1.0 - taper_ratio) / (1.0 + taper_ratio)",
     "tan_half = tan_le + (2.0 / aspect_ratio) * (1.0 - taper_ratio) / (1.0 + taper_ratio)",
     "sign flipped in the LE->half-chord sweep conversion in lift_curve_slope_per_rad",
     "lift-curve slopes / neutral point"),
]

def run(cmd, cwd, timeout=900):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                          timeout=timeout).returncode

results = []
for path, find, repl, desc, expect in MUTANTS:
    with tempfile.TemporaryDirectory() as td:
        work = pathlib.Path(td) / "repo"
        shutil.copytree(REPO, work, ignore=shutil.ignore_patterns(
            ".git", ".venv", "vendor", "__pycache__", "*.pyc", "opt_runs",
            "figures", "model_v2", "archive", ".superpowers"))
        (work / "vendor").symlink_to(REPO / "vendor")
        f = work / path
        src = f.read_text()
        if find not in src:
            results.append(dict(desc=desc, status="NOT_APPLIED", note=f"pattern absent in {path}"))
            print(f"  [SKIP] {desc}  (pattern not found)", flush=True)
            continue
        f.write_text(src.replace(find, repl, 1))
        rc = run([str(REPO / ".venv/bin/pytest"), "tests/", "-x", "-q", "-p", "no:warnings",
                  "--deselect", "tests/test_cad_render.py"], work)
        caught = rc != 0
        results.append(dict(desc=desc, expect=expect, caught=caught))
        print(f"  [{'KILLED ' if caught else 'SURVIVED'}] {desc}", flush=True)

na = [r for r in results if r.get("status") == "NOT_APPLIED"]
if na:
    print("\nNOT APPLIED -- these mutants tested nothing at all:")
    for r in na:
        print(f"  - {r['desc']}   ({r['note']})")
killed = sum(1 for r in results if r.get("caught"))
total = sum(1 for r in results if "caught" in r)
print(f"\nMutation score: {killed}/{total} killed ({100*killed/max(total,1):.0f}%)")
surv = [r for r in results if r.get("caught") is False]
if surv:
    print("\nSURVIVORS -- these are holes in the suite:")
    for r in surv:
        print(f"  - {r['desc']}   (expected to be caught by: {r['expect']})")
json.dump(results, open(REPO / "opt_runs/mutation.json", "w"), indent=2)
