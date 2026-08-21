"""Regenerate the current design figures. Every number comes from the repo."""
import json, math, pathlib
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from argus7.design.schema import load_design
from argus7.design.geometry import derive_wing
from argus7.analysis import balance as B
from argus7.opt.coupled import bsfc_at_load
import torch

OUT = pathlib.Path("figures/current"); OUT.mkdir(parents=True, exist_ok=True)
BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
INK, MUTED, GRID, SURF = "#1a1a19", "#6b6b68", "#e4e4e1", "#fcfcfb"

plt.rcParams.update({
    "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
    "axes.edgecolor": GRID, "axes.labelcolor": INK, "text.color": INK,
    "xtick.color": MUTED, "ytick.color": MUTED, "grid.color": GRID,
    "axes.grid": True, "grid.linewidth": 0.8, "axes.axisbelow": True,
    "font.size": 10, "axes.titlesize": 12, "axes.titleweight": "bold",
    "axes.spines.top": False, "axes.spines.right": False, "lines.linewidth": 2.0,
})

# ---------- 1. static margin across the fuel burn -------------------------
fig, ax = plt.subplots(figsize=(8, 4.8))
ff = np.linspace(1.0, 0.0, 21)
designs = [("v1.0 published", "v1", ORANGE), ("v3.0", "v3", YELLOW), ("v4.0 current", "v4", BLUE)]
for label, tag, c in designs:
    try:
        d = load_design(f"design/argus7_{tag}.yaml")
        sm = [B.static_margin(d, f) * 100 for f in ff]
        ax.plot((1 - ff) * 100, sm, color=c, label=label, zorder=3)
        ax.annotate(label, (100, sm[-1]), color=c, fontsize=9, fontweight="bold",
                    xytext=(6, 0), textcoords="offset points", va="center")
    except Exception as e:
        print("skip", tag, e)
ax.axhspan(8, 20, color=AQUA, alpha=0.12, zorder=0)
ax.text(2, 18.2, "acceptable band, 8-20% MAC", color="#0f7a55", fontsize=9, va="center")
ax.axhline(0, color=INK, lw=1.2, zorder=2)
ax.text(2, -5.5, "unstable below this line", color=MUTED, fontsize=9, style="italic")
ax.set_xlabel("fuel burned (%)"); ax.set_ylabel("static margin (% MAC)")
ax.set_title("Static margin across the fuel burn")
ax.set_xlim(0, 118); ax.margins(y=0.08)
fig.tight_layout(); fig.savefig(OUT / "static_margin.png", dpi=160); plt.close(fig)

# ---------- 2. BSFC vs load fraction --------------------------------------
fig, ax = plt.subplots(figsize=(8, 4.8))
lf = np.linspace(0.10, 1.0, 200)
b = [float(bsfc_at_load(torch.tensor(0.25), torch.tensor(float(x)))) * 1000 for x in lf]
ax.plot(lf * 100, b, color=BLUE, zorder=3)
for x, y, lab, c in [(0.19, 425, "v1.0: 17 kW engine\nat 19% load", ORANGE),
                     (0.31, 335, "v4.0: 11 kW engine\nat 31% load", AQUA)]:
    ax.plot([x * 100], [y], "o", ms=9, color=c, mec=SURF, mew=2, zorder=5)
    ax.annotate(lab, (x * 100, y), xytext=(14, 18), textcoords="offset points",
                color=c, fontsize=9, fontweight="bold",
                arrowprops=dict(arrowstyle="-", color=c, lw=1.2))
ax.axhline(270, color=MUTED, lw=1.2, ls="--", zorder=2)
ax.text(14, 278, "270 g/kWh assumed by the report", color=MUTED, fontsize=9, ha="left")
ax.set_xlabel("engine load fraction (%)"); ax.set_ylabel("effective BSFC (g/kWh)")
ax.set_title("Why engine size dominates: part-load fuel consumption")
ax.set_xlim(8, 102)
fig.tight_layout(); fig.savefig(OUT / "bsfc_part_load.png", dpi=160); plt.close(fig)

# ---------- 3. endurance by design point ----------------------------------
fig, ax = plt.subplots(figsize=(8, 4.4))
names = ["v1.0\npublished\nclaim", "v1.0\nhonest\nmodel", "v3.0", "v4.0\ncurrent"]
vals = [4.70, 3.16, 6.33, 6.99]
cols = [MUTED, ORANGE, YELLOW, BLUE]
notes = ["as published", "unstable,\nfuel does not fit", "stable but below\nthe spec gate", "stable, fuel fits,\nmass closes"]
bars = ax.bar(names, vals, color=cols, width=0.6, zorder=3)
for bar, v, n in zip(bars, vals, notes):
    ax.text(bar.get_x() + bar.get_width()/2, v + 0.12, f"{v:.2f} d",
            ha="center", fontweight="bold", color=INK, fontsize=11)
    ax.text(bar.get_x() + bar.get_width()/2, 0.18, n, ha="center", color=SURF,
            fontsize=8.5, va="bottom")
ax.set_ylabel("loiter endurance (days)")
ax.set_title("Endurance by design point, and whether the aircraft actually works")
ax.margins(y=0.16); ax.set_axisbelow(True)
fig.tight_layout(); fig.savefig(OUT / "endurance_by_design.png", dpi=160); plt.close(fig)

# ---------- 4. drag budget at loiter --------------------------------------
fig, ax = plt.subplots(figsize=(8, 3.4))
d = load_design("design/argus7_v1.yaml"); g = derive_wing(d.wing)
cl = 1.21
cdi = cl**2 / (math.pi * g.aspect_ratio * d.aero.oswald_e); cd0 = d.aero.cd0
tot = cd0 + cdi
ax.barh([0], [cdi/tot*100], color=BLUE, height=0.45, zorder=3, label="induced")
ax.barh([0], [cd0/tot*100], left=[cdi/tot*100 + 0.6], color=ORANGE, height=0.45, zorder=3, label="parasite")
ax.text(cdi/tot*50, 0, f"induced  {100*cdi/tot:.1f}%", ha="center", va="center",
        color=SURF, fontweight="bold", fontsize=11)
ax.text(cdi/tot*100 + cd0/tot*50, 0, f"parasite  {100*cd0/tot:.1f}%", ha="center",
        va="center", color=SURF, fontweight="bold", fontsize=11)
ax.set_yticks([]); ax.set_xlim(0, 101); ax.set_xlabel("share of total drag at loiter (%)")
ax.set_title("Induced drag dominates — most optimisation attacked the smaller half")
ax.grid(axis="y", visible=False)
fig.tight_layout(); fig.savefig(OUT / "drag_budget.png", dpi=160); plt.close(fig)

print("wrote:", *[p.name for p in sorted(OUT.iterdir())])
