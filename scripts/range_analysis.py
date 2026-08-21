"""Straight-line range for ARGUS-7 v5.0.

Endurance and range are different problems. Endurance maximises time aloft, so it
flies at minimum power (max C_L^1.5/C_D). Range maximises distance, so it flies at
minimum DRAG (max L/D) -- faster, at a lower lift coefficient.

Breguet range for a propeller aircraft:

    R = (eta_prop / (g * c)) * (L/D) * ln(W_start / W_end)

with c the specific fuel consumption in kg per joule of shaft work. The wrinkle
here is that c is NOT constant: BSFC depends on engine load fraction, and cruising
faster raises the power demand, which raises the load fraction, which IMPROVES
BSFC. So the range optimum sits faster than pure L/D would suggest -- the engine
likes to be worked.

Every number comes from design/argus7_v5.yaml and the repo's own models.
"""
import json, math, pathlib
import numpy as np
import torch
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

from argus7.design.schema import load_design
from argus7.design.geometry import derive_wing
from argus7.mission.atmosphere import isa_numpy
from argus7.opt.coupled import bsfc_at_load

G = 9.80665
d = load_design("design/argus7_v5.yaml")
g = derive_wing(d.wing)
CD0, E, AR = d.aero.cd0, d.aero.oswald_e, g.aspect_ratio
ETA = d.propulsion.prop_eta_loiter
PRATED = d.propulsion.power_max_kw * 1000
BSFC_FULL = 0.2506           # optimiser's full-load value for this point
PAYLOAD_W = d.mission.payload_power_w
ALT = d.mission.loiter_altitude_m
RHO = float(isa_numpy(ALT).density_kgm3)

def bsfc(shaft_w):
    return float(bsfc_at_load(torch.tensor(BSFC_FULL), torch.tensor(shaft_w / PRATED)))

def step_range(v_ms, mass0, fuel_kg, n=400):
    """March the cruise at fixed TAS, returning range (km) and mean values."""
    dm = fuel_kg / n
    dist = 0.0; shafts = []; cls = []
    for i in range(n):
        m = mass0 - (i + 0.5) * dm
        w = m * G
        cl = 2 * w / (RHO * v_ms**2 * g.area_m2)
        if cl > d.aero.cl_max / 1.15**2:      # stall margin
            return None
        cd = CD0 + cl**2 / (math.pi * AR * E)
        drag = 0.5 * RHO * v_ms**2 * g.area_m2 * cd
        shaft = drag * v_ms / ETA + PAYLOAD_W / 0.75
        if shaft > PRATED:                     # cannot hold this speed
            return None
        rate = bsfc(shaft) * (shaft / 1000) / 3600     # kg/s
        dist += v_ms * (dm / rate)
        shafts.append(shaft); cls.append(cl)
    return dist / 1000.0, float(np.mean(shafts)) / 1000, float(np.mean(cls))

M0, FUEL = d.masses.mtow, d.masses.fuel
speeds = np.arange(70, 210, 2.0)
rows = []
for v_kmh in speeds:
    r = step_range(v_kmh / 3.6, M0, FUEL)
    if r: rows.append((v_kmh, *r))
V = np.array([r[0] for r in rows]); R = np.array([r[1] for r in rows])
SH = np.array([r[2] for r in rows]); CLm = np.array([r[3] for r in rows])
i = int(np.argmax(R))

cl_bestld = math.sqrt(CD0 * math.pi * AR * E)
ldmax = cl_bestld / (2 * CD0)
print(f"v5.0: S {g.area_m2:.3f} m2, AR {AR:.2f}, C_D0 {CD0:.5f}, e {E:.4f}, MTOW {M0:.1f} kg, fuel {FUEL:.1f} kg")
print(f"  L/D max {ldmax:.1f} at C_L {cl_bestld:.4f}")
print(f"  BEST RANGE {R[i]:,.0f} km at {V[i]:.0f} km/h TAS  (mean shaft {SH[i]:.2f} kW, mean C_L {CLm[i]:.3f})")
print(f"  time aloft at that speed: {R[i]/V[i]:.1f} h = {R[i]/V[i]/24:.2f} d")
loiter_h = 167.3
print(f"  for comparison, loiter endurance is {loiter_h:.0f} h at ~102 km/h")
slow=[r for r in rows if r[0]<=110]
print(f"  slowest speed that closes at MTOW: {V.min():.0f} km/h -> {R[0]:,.0f} km"
      f"   (below this the stall margin or power limit bites at full fuel)")
j = np.where(R >= 0.99 * R[i])[0]
print(f"  within 1% of best range: {V[j[0]]:.0f}-{V[j[-1]]:.0f} km/h -- a broad optimum")

# payload-range
pay = np.arange(0, 85, 2.5)
pr = []
for p in pay:
    fuel = FUEL + (d.masses.payload - p)      # traded kg-for-kg against payload
    if fuel <= 0: continue
    r = step_range(V[i] / 3.6, M0, fuel)
    if r: pr.append((p, r[0]))
json.dump({"v_kmh": V.tolist(), "range_km": R.tolist(), "best": [float(V[i]), float(R[i])],
           "payload_range": pr}, open("opt_runs/range.json", "w"), indent=2)

OUT = pathlib.Path("figures/current")
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, MUTED, GRID, SURF = "#1a1a19", "#6b6b68", "#e4e4e1", "#fcfcfb"
plt.rcParams.update({"figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
    "axes.edgecolor": GRID, "axes.labelcolor": INK, "text.color": INK, "xtick.color": MUTED,
    "ytick.color": MUTED, "grid.color": GRID, "axes.grid": True, "grid.linewidth": 0.8,
    "axes.axisbelow": True, "font.size": 10, "axes.titlesize": 12, "axes.titleweight": "bold",
    "axes.spines.top": False, "axes.spines.right": False, "lines.linewidth": 2.0})

fig, ax = plt.subplots(figsize=(8, 4.8))
ax.plot(V, R, color=BLUE, zorder=3)
ax.plot([V[i]], [R[i]], "o", ms=10, color=ORANGE, mec=SURF, mew=2, zorder=5)
ax.annotate(f"best range\n{R[i]:,.0f} km at {V[i]:.0f} km/h", (V[i], R[i]),
            xytext=(30, -52), textcoords="offset points", color=ORANGE, fontweight="bold",
            fontsize=10, arrowprops=dict(arrowstyle="-", color=ORANGE, lw=1.2))
ax.axvspan(V[j[0]], V[j[-1]], color=AQUA, alpha=0.12, zorder=0)
ax.text((V[j[0]]+V[j[-1]])/2, R.min()+ (R[i]-R.min())*0.08,
        f"within 1%: {V[j[0]]:.0f}-{V[j[-1]]:.0f} km/h", color="#0f7a55", fontsize=9, ha="center")
ax.set_xlabel("cruise speed, TAS (km/h)"); ax.set_ylabel("still-air range (km)")
ax.set_title("Straight-line range vs cruise speed, ARGUS-7 v5.0")
fig.tight_layout(); fig.savefig(OUT/"range_vs_speed.png", dpi=160); plt.close(fig)

fig, ax = plt.subplots(figsize=(8, 4.4))
P = np.array([p for p, _ in pr]); RR = np.array([r for _, r in pr])
ax.plot(P, RR, color=BLUE, zorder=3)
ax.plot([50], [np.interp(50, P, RR)], "o", ms=10, color=ORANGE, mec=SURF, mew=2, zorder=5)
ax.annotate(f"design payload 50 kg\n{np.interp(50,P,RR):,.0f} km", (50, np.interp(50, P, RR)),
            xytext=(16, 26), textcoords="offset points", color=ORANGE, fontweight="bold",
            fontsize=10, arrowprops=dict(arrowstyle="-", color=ORANGE, lw=1.2))
ax.set_xlabel("payload (kg)"); ax.set_ylabel("still-air range (km)")
ax.set_title("Payload–range, trading payload for fuel at constant MTOW")
fig.tight_layout(); fig.savefig(OUT/"payload_range.png", dpi=160); plt.close(fig)
print("\nwrote figures/current/range_vs_speed.png and payload_range.png")
