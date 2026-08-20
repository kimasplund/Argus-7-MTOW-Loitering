from __future__ import annotations
from pathlib import Path
import numpy as np

DATA = Path(__file__).resolve().parents[2] / "data" / "airfoils"


def naca4(code: str, n: int = 121) -> np.ndarray:
    """4-digit NACA section in Selig order (TE -> upper -> LE -> lower -> TE)."""
    m, p, t = int(code[0]) / 100.0, int(code[1]) / 10.0, int(code[2:]) / 100.0
    beta = np.linspace(0.0, np.pi, n)
    x = (1 - np.cos(beta)) / 2.0                       # cosine clustering at LE/TE
    yt = 5 * t * (0.2969*np.sqrt(x) - 0.1260*x - 0.3516*x**2
                  + 0.2843*x**3 - 0.1036*x**4)         # closed-TE coefficient
    if m == 0.0:
        yc, dyc = np.zeros_like(x), np.zeros_like(x)
    else:
        yc = np.where(x < p, m/p**2*(2*p*x - x**2), m/(1-p)**2*((1-2*p) + 2*p*x - x**2))
        dyc = np.where(x < p, 2*m/p**2*(p - x), 2*m/(1-p)**2*(p - x))
    th = np.arctan(dyc)
    xu, yu = x - yt*np.sin(th), yc + yt*np.cos(th)
    xl, yl = x + yt*np.sin(th), yc - yt*np.cos(th)
    upper = np.column_stack([xu, yu])[::-1]            # TE -> LE
    lower = np.column_stack([xl, yl])[1:]              # LE -> TE
    return np.vstack([upper, lower])


def load_airfoil(name: str) -> np.ndarray:
    """Load an airfoil .dat file and normalise x to 0..1.

    Auto-detects the file's coordinate convention:

    - Selig format: a title line followed directly by coordinates already
      in TE -> upper -> LE -> lower -> TE order. First coordinate pair has
      both values <= 1.0. Used as-is.

    - Lednicer format (e.g. the UIUC/Selig database's raw .dat files, such
      as fx63137.dat): a title line, then a point-count header line (e.g.
      "49.0 49.0" -- NOT a coordinate), then two separate LE -> TE surface
      blocks (upper, then lower). Detected when the first numeric pair has
      either value > 1.0 (a real normalised coordinate never does). The
      header is dropped, the remaining points are split into the two
      surfaces at the index where x resets toward zero (i.e. where x drops
      after climbing toward the TE), and reassembled into Selig order so
      everything downstream sees one consistent convention.
    """
    path = DATA / f"{name.lower().replace('-', '').replace(' ', '')}.dat"
    rows = []
    for line in path.read_text().splitlines():
        parts = line.split()
        if len(parts) != 2:
            continue
        try:
            rows.append((float(parts[0]), float(parts[1])))
        except ValueError:
            continue                                    # title or header line
    pts = np.array(rows, dtype=float)

    if pts[0, 0] > 1.0 or pts[0, 1] > 1.0:
        # Lednicer: drop the point-count header, then split the two
        # LE -> TE surface blocks at the point where x resets toward zero.
        pts = pts[1:]
        split = len(pts)
        for i in range(1, len(pts)):
            if pts[i, 0] < pts[i - 1, 0]:
                split = i
                break
        upper, lower = pts[:split], pts[split:]
        c = np.vstack([upper[::-1], lower[1:]])         # TE -> LE -> TE, Selig order
    else:
        c = pts.copy()                                  # already Selig order

    x0, x1 = c[:, 0].min(), c[:, 0].max()
    c[:, 0] = (c[:, 0] - x0) / (x1 - x0)
    c[:, 1] = c[:, 1] / (x1 - x0)
    return c


def max_thickness(coords: np.ndarray) -> float:
    """Max thickness/chord, measured by interpolating upper and lower surfaces."""
    le = int(np.argmin(coords[:, 0]))
    upper, lower = coords[:le + 1][::-1], coords[le:]
    xs = np.linspace(0.0, 1.0, 400)
    yu = np.interp(xs, upper[:, 0], upper[:, 1])
    yl = np.interp(xs, lower[:, 0], lower[:, 1])
    return float(np.max(yu - yl))


def scale_airfoil(coords: np.ndarray, chord: float, twist_rad: float,
                  le_pos: tuple[float, float, float]) -> np.ndarray:
    """Place a normalised section in the project frame.

    Project frame: x aft, y starboard, z up. The section is scaled by `chord`,
    rotated by `twist_rad` about the leading edge (negative = washout: the
    trailing edge rises, nose rotates down), and translated so its leading
    edge sits at `le_pos`.

    Rotation convention: with xc, zc measured aft/up from the (unrotated)
    leading edge, xr = xc*cos(t) + zc*sin(t), zr = -xc*sin(t) + zc*cos(t).
    For t < 0 (washout) this raises the trailing edge (xc > 0) above the
    leading edge in z, matching "negative = washout" and reversed Prandtl
    bell spanload assumptions this design depends on. The naive
    xr = xc*ct - zc*st / zr = xc*st + zc*ct convention is inverted: it
    drops the trailing edge for negative twist (washin), not washout.
    """
    xc, zc = coords[:, 0] * chord, coords[:, 1] * chord
    ct, st = np.cos(twist_rad), np.sin(twist_rad)
    xr = xc * ct + zc * st
    zr = -xc * st + zc * ct
    x0, y0, z0 = le_pos
    return np.column_stack([xr + x0, np.full_like(xr, y0), zr + z0])
