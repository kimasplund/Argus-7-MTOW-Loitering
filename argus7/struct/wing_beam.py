"""Wing spar as a tapered beam, solved with CalculiX.

The mass model sizes the spar caps analytically from root bending moment. That is
enough to get mass right; it says nothing about deflection, about whether the
caps buckle, or about the natural frequencies that decide flutter. This builds the
actual beam and solves it.

Model: a tapered box spar, root to tip, as Timoshenko beam elements. Caps carry
bending, the shear web carries shear and closes the cell for torsion. Section
properties follow the real planform, so I, J and A all taper with chord.

  I_xx  ~ A_cap * h^2 / 2          two caps at +/- h/2
  J     = 4 * A_enclosed^2 / (perimeter / t_web)     Bredt closed-cell torsion
  A     = 2*A_cap + perimeter*t_web

Lift is applied as a distributed load with an elliptic spanload, which is what the
AVL sweep says this wing carries (span efficiency 0.97+), less the relief from
fuel carried in the wing.
"""
from __future__ import annotations

import math
import subprocess
from dataclasses import dataclass
from pathlib import Path

# UD carbon/epoxy, from research/materials_pack.md
E_CARBON = 134e9      # Pa, pultruded UD longitudinal
G_CARBON = 5.0e9      # Pa, matrix-dominated shear
RHO_CARBON = 1600.0   # kg/m3
SIGMA_ALLOW = 600e6   # Pa compression allowable, report section 5

N_ULT = 5.7
GRAV = 9.80665


@dataclass
class BeamStation:
    y: float
    chord: float
    depth: float
    cap_area: float
    web_t: float
    I: float
    J: float
    A: float


def stations(design, n=21):
    """Section properties from root to tip, tapering with the real planform."""
    from argus7.design.geometry import derive_wing
    g = derive_wing(design.wing)
    semi = g.span_m / 2
    tc = design.wing.thickness_ratio
    w_root = design.masses.mtow * GRAV

    # Root cap area from the ultimate root moment, then taper as the local moment.
    m_root = N_ULT * w_root * semi * 0.40 * 0.78
    h_root = tc * g.chord_root_m
    cap_root = m_root / (h_root * SIGMA_ALLOW)

    out = []
    for i in range(n):
        f = i / (n - 1)
        y = f * semi
        chord = g.chord_root_m + f * (g.chord_tip_m - g.chord_root_m)
        depth = tc * chord
        # local bending moment for an elliptic spanload, normalised to the root
        m_local = m_root * (1 - f) ** 2 * (1 + 0.5 * f)
        cap = max(m_local / (depth * SIGMA_ALLOW), cap_root * 0.12)
        box_w = 0.45 * chord                     # spar box spans 15-60% chord
        web_t = 0.0012 + 0.0018 * (1 - f)        # thicker web inboard
        I = cap * depth**2 / 2 + box_w * web_t**3 / 6
        a_encl = box_w * depth
        perim = 2 * (box_w + depth)
        J = 4 * a_encl**2 / (perim / web_t)
        A = 2 * cap + perim * web_t
        out.append(BeamStation(y, chord, depth, cap, web_t, I, J, A))
    return out


def write_inp(design, path: Path, mode="static", n=21):
    """Emit a CalculiX deck. mode is 'static' or 'frequency'."""
    from argus7.design.geometry import derive_wing
    g = derive_wing(design.wing)
    st = stations(design, n)
    semi = g.span_m / 2
    w = design.masses.mtow * GRAV
    # elliptic lift per unit span, ultimate, minus wing-borne fuel relief
    fuel_relief = 0.78
    L = []
    for s in st:
        e = math.sqrt(max(1 - (s.y / semi) ** 2, 0.0))
        L.append(N_ULT * w * fuel_relief * e / (math.pi / 4 * 2 * semi))

    lines = ["*NODE, NSET=NALL"]
    for i, s in enumerate(st, 1):
        lines.append(f"{i}, 0.0, {s.y:.6f}, 0.0")
    lines.append("*ELEMENT, TYPE=B31, ELSET=EALL")
    for i in range(1, len(st)):
        lines.append(f"{i}, {i}, {i+1}")
    # one section per element so the taper is represented
    for i in range(1, len(st)):
        s = st[i - 1]
        # Equivalent rectangle carrying the true A and I. h is the DEPTH:
        #   h = sqrt(12 I / A)  then  b = A / h  gives  b h^3 / 12 = I exactly.
        # Swapping these two understates I by ~10^4 and was worth a 3.3x error
        # against the analytic M/EI integration.
        h = math.sqrt(max(12 * s.I / max(s.A, 1e-9), 1e-8))
        b = max(s.A / max(h, 1e-9), 1e-5)
        lines += [f"*ELSET, ELSET=E{i}", f"{i}",
                  f"*BEAM SECTION, ELSET=E{i}, MATERIAL=CFRP, SECTION=RECT",
                  f"{b:.6f}, {h:.6f}", "1.d0,0.d0,0.d0"]
        # The orientation vector gives the section's local 1-direction. With
        # "0,0,1" the rectangle is rotated 90 degrees and the beam bends about
        # its WEAK axis -- validated against a uniform cantilever, where that
        # choice overstated tip deflection by exactly (h/b)^2 = 4.00. With
        # "1,0,0" the same check matches PL^3/3EI to 0.04%.
    lines += ["*MATERIAL, NAME=CFRP", "*ELASTIC",
              f"{E_CARBON:.6e}, 0.3", "*DENSITY", f"{RHO_CARBON:.1f}",
              "*BOUNDARY", "1, 1, 6"]
    if mode == "static":
        lines += ["*STEP", "*STATIC"]
        lines.append("*CLOAD")
        for i, s in enumerate(st, 1):
            seg = semi / (len(st) - 1)
            f = L[i - 1] * seg * (0.5 if i in (1, len(st)) else 1.0)
            lines.append(f"{i}, 3, {f:.4f}")
        lines += ["*NODE FILE", "U", "*EL FILE", "S", "*END STEP"]
    else:
        lines += ["*STEP", "*FREQUENCY, STORAGE=YES", "8", "*NODE FILE", "U",
                  "*END STEP"]
    path.write_text("\n".join(lines) + "\n")
    return st, L


def run(job: Path):
    r = subprocess.run(["ccx", job.stem], capture_output=True,
                       text=True, timeout=600, cwd=job.parent)
    return r.stdout + r.stderr
