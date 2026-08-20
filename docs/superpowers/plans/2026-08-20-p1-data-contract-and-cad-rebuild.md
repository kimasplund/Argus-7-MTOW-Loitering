# ARGUS-7 Phase P1 — Data Contract & CAD Rebuild Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the defective `model/argus7_model.scad` with a parametric, airfoil-lofted, correctly-axed CAD model generated from a single validated parameter file, with closure guards that make the known geometry-drift failures unrepresentable.

**Architecture:** One YAML file is the sole source of truth. `geometry.py` derives every dependent quantity and asserts closure at load time. `cad/` builds a B-rep solid with build123d from those derived values and exports STEP + STL + a regenerated OpenSCAD file. No module hardcodes geometry; no header comment is hand-written.

**Tech Stack:** Python 3.14, pydantic (schema), PyYAML, build123d/OCP (B-rep CAD), numpy, trimesh (mesh validation), pytest. Fallback `.venv-cad` on Python 3.12 if OCP wheels misbehave on 3.14.

**Spec:** `docs/superpowers/specs/2026-08-20-argus7-cad-sim-optimisation-design.md`

## Global Constraints

- **Axis convention (project-wide, never deviate):** `x` = aft along fuselage (nose at x=0, tail at +x); `y` = starboard span; `z` = up. This is the fix for Defect 1 and every module assumes it.
- **Single source of truth:** geometry lives only in `design/*.yaml`. Any module that hardcodes a chord, span, area or MAC is a defect.
- **Generated files carry generated headers.** Header comments in `.scad`/`.step` output are emitted from the loaded parameters, never typed by hand.
- **Closure tolerance:** 1e-9 relative on all derived-geometry identities.
- **Units:** SI throughout — metres, kilograms, radians internally; degrees only at the YAML boundary, converted on load.
- **v1.0 parameters are transcribed as published**, including the §2 tail inconsistency. Corrections happen in v2, never by silently editing v1.

---

### Task 1: Design schema, parameter file, and closure guards

This is the structural fix for Defect 2. Everything downstream depends on it.

**Files:**
- Create: `argus7/__init__.py`, `argus7/design/__init__.py`
- Create: `argus7/design/schema.py`
- Create: `argus7/design/geometry.py`
- Create: `design/argus7_v1.yaml`
- Test: `tests/test_geometry_closure.py`

**Interfaces:**
- Consumes: nothing (foundation task)
- Produces:
  - `load_design(path: str | Path) -> Design` — pydantic model, raises `ClosureError` on inconsistency
  - `Design.wing` with fields `area_m2, aspect_ratio, taper_ratio, airfoil, twist_tip_deg, dihedral_deg, sweep_le_deg, thickness_ratio, incidence_deg`
  - `WingGeometry` dataclass with `span_m, chord_root_m, chord_tip_m, mac_m, mac_y_m, area_m2, aspect_ratio`
  - `derive_wing(wing) -> WingGeometry`
  - `tail_volume_h(design) -> float`
  - `ClosureError(Exception)`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_geometry_closure.py
import math
import pytest
from argus7.design.geometry import derive_wing, tail_volume_h, ClosureError
from argus7.design.schema import load_design

REPORT = dict(span=9.263, c_root=0.5807, c_tip=0.2613, mac=0.4412)  # report §2

def test_v1_matches_report_section_2():
    """Regression guard for Defect 2: the superseded Gemini chords must never return."""
    g = derive_wing(load_design("design/argus7_v1.yaml").wing)
    assert g.span_m       == pytest.approx(REPORT["span"],   abs=1e-3)
    assert g.chord_root_m == pytest.approx(REPORT["c_root"], abs=1e-3)
    assert g.chord_tip_m  == pytest.approx(REPORT["c_tip"],  abs=1e-3)
    assert g.mac_m        == pytest.approx(REPORT["mac"],    abs=1e-3)

def test_superseded_gemini_chords_are_rejected():
    """c_root=0.674 implies S=4.525 and AR=19.0 - must not validate against S=3.9/AR=22."""
    g = derive_wing(load_design("design/argus7_v1.yaml").wing)
    assert abs(g.chord_root_m - 0.674) > 0.05

def test_closure_identities_hold():
    g = derive_wing(load_design("design/argus7_v1.yaml").wing)
    assert abs(g.area_m2 - (g.span_m / 2) * (g.chord_root_m + g.chord_tip_m)) < 1e-9
    assert abs(g.aspect_ratio - g.span_m**2 / g.area_m2) < 1e-9

def test_inconsistent_design_raises(tmp_path):
    """A YAML asserting a chord that contradicts S/AR/taper must fail loudly."""
    bad = tmp_path / "bad.yaml"
    bad.write_text(
        "name: bad\nvariant: test\n"
        "wing: {area_m2: 3.9, aspect_ratio: 22.0, taper_ratio: 0.45,\n"
        "       chord_root_m_assert: 0.674, airfoil: FX63-137, twist_tip_deg: -3.0,\n"
        "       dihedral_deg: 3.0, sweep_le_deg: 1.0, thickness_ratio: 0.137, incidence_deg: 2.0}\n"
    )
    with pytest.raises(ClosureError):
        load_design(bad)

@pytest.mark.xfail(reason=(
    "Report section 2 tail row does not close: S_h=0.31 m2 with arm=3.2 m gives "
    "V_h=0.577, not the stated 0.68 (17.9% discrepancy). Either S_h should be "
    "0.366 m2 or V_h is 0.577. Transcribed as published; resolved in v2, not by "
    "silently editing v1."))
def test_report_stated_tail_volume():
    assert tail_volume_h(load_design("design/argus7_v1.yaml")) == pytest.approx(0.68, abs=0.005)

def test_tail_volume_actual_value_is_pinned():
    """Pin the real computed value so a future edit cannot drift it unnoticed."""
    assert tail_volume_h(load_design("design/argus7_v1.yaml")) == pytest.approx(0.5765, abs=1e-3)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_geometry_closure.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'argus7'`

- [ ] **Step 3: Write the schema**

```python
# argus7/design/schema.py
from __future__ import annotations
from pathlib import Path
import yaml
from pydantic import BaseModel, Field

class Wing(BaseModel):
    area_m2: float = Field(gt=0)
    aspect_ratio: float = Field(gt=0)
    taper_ratio: float = Field(gt=0, le=1)
    airfoil: str
    twist_tip_deg: float          # negative = washout
    dihedral_deg: float
    sweep_le_deg: float
    thickness_ratio: float = Field(gt=0, lt=0.5)
    incidence_deg: float
    chord_root_m_assert: float | None = None   # optional cross-check, not a source of truth

class Fuselage(BaseModel):
    length_m: float = Field(gt=0)
    max_diameter_m: float = Field(gt=0)

class Booms(BaseModel):
    length_m: float = Field(gt=0)
    diameter_m: float = Field(gt=0)
    y_station_frac: float = Field(gt=0, lt=1)

class Tail(BaseModel):
    type: str
    area_h_m2: float = Field(gt=0)
    arm_m: float = Field(gt=0)
    dihedral_deg: float
    taper_ratio: float = Field(gt=0, le=1)
    airfoil: str

class Propulsion(BaseModel):
    engine_displacement_cc: float
    power_max_kw: float
    reduction_ratio: float
    prop_diameter_m: float
    prop_rpm: float

class Masses(BaseModel):
    airframe: float; powertrain: float; avionics: float
    recovery: float; payload: float; fuel: float; mtow: float

class Mission(BaseModel):
    payload_mass_kg: float
    payload_power_w: float
    loiter_altitude_m: float

class Aero(BaseModel):
    cd0: float; oswald_e: float; cl_max: float

class Design(BaseModel):
    name: str
    variant: str
    wing: Wing
    fuselage: Fuselage | None = None
    booms: Booms | None = None
    tail: Tail | None = None
    propulsion: Propulsion | None = None
    masses: Masses | None = None
    mission: Mission | None = None
    aero: Aero | None = None

def load_design(path: str | Path) -> Design:
    from argus7.design.geometry import check_closure
    data = yaml.safe_load(Path(path).read_text())
    design = Design(**data)
    check_closure(design)
    return design
```

- [ ] **Step 4: Write the geometry derivation and closure guard**

```python
# argus7/design/geometry.py
from __future__ import annotations
import math
from dataclasses import dataclass

TOL = 1e-9

class ClosureError(Exception):
    """Raised when a design's stated geometry contradicts its derived geometry."""

@dataclass(frozen=True)
class WingGeometry:
    span_m: float
    chord_root_m: float
    chord_tip_m: float
    mac_m: float
    mac_y_m: float          # spanwise station of the MAC
    area_m2: float
    aspect_ratio: float

def derive_wing(wing) -> WingGeometry:
    S, AR, lam = wing.area_m2, wing.aspect_ratio, wing.taper_ratio
    b  = math.sqrt(AR * S)
    cr = S / ((b / 2.0) * (1.0 + lam))
    ct = lam * cr
    mac = (2.0 / 3.0) * cr * (1.0 + lam + lam**2) / (1.0 + lam)
    mac_y = (b / 6.0) * (1.0 + 2.0 * lam) / (1.0 + lam)
    return WingGeometry(b, cr, ct, mac, mac_y, S, AR)

def tail_volume_h(design) -> float:
    """Horizontal tail volume coefficient V_h = S_h * l_h / (S_w * MAC)."""
    g = derive_wing(design.wing)
    return design.tail.area_h_m2 * design.tail.arm_m / (g.area_m2 * g.mac_m)

def check_closure(design) -> None:
    g = derive_wing(design.wing)
    identities = {
        "S = (b/2)(c_root + c_tip)": g.area_m2 - (g.span_m / 2) * (g.chord_root_m + g.chord_tip_m),
        "AR = b^2 / S":              g.aspect_ratio - g.span_m**2 / g.area_m2,
        "c_tip = taper * c_root":    g.chord_tip_m - design.wing.taper_ratio * g.chord_root_m,
    }
    for name, residual in identities.items():
        if abs(residual) > TOL:
            raise ClosureError(f"{name} violated by {residual:.3e}")
    assert_ = design.wing.chord_root_m_assert
    if assert_ is not None and abs(assert_ - g.chord_root_m) > 1e-3:
        raise ClosureError(
            f"stated chord_root_m_assert={assert_:.4f} contradicts derived "
            f"{g.chord_root_m:.4f} from S={g.area_m2}, AR={g.aspect_ratio}, "
            f"taper={design.wing.taper_ratio}")
```

- [ ] **Step 5: Write the v1.0 parameter file**

```yaml
# design/argus7_v1.yaml
# ARGUS-7 v1.0 as published in docs/argus7_design_report.md section 2.
# Transcribed verbatim including the section-2 tail inconsistency (see
# tests/test_geometry_closure.py::test_report_stated_tail_volume).
name: ARGUS-7
variant: v1.0

mission:
  payload_mass_kg: 50.0
  payload_power_w: 500.0
  loiter_altitude_m: 4000.0

wing:
  area_m2: 3.9
  aspect_ratio: 22.0
  taper_ratio: 0.45
  airfoil: FX63-137
  twist_tip_deg: -3.0
  dihedral_deg: 3.0
  sweep_le_deg: 1.0
  thickness_ratio: 0.137
  incidence_deg: 2.0

fuselage: {length_m: 3.4, max_diameter_m: 0.48}
booms:    {length_m: 3.2, diameter_m: 0.09, y_station_frac: 0.134}
tail:     {type: inverted_v, area_h_m2: 0.31, arm_m: 3.2,
           dihedral_deg: -42.0, taper_ratio: 0.55, airfoil: NACA0010}
propulsion: {engine_displacement_cc: 250.0, power_max_kw: 17.0,
             reduction_ratio: 2.3, prop_diameter_m: 0.813, prop_rpm: 2100.0}
masses:   {airframe: 60.5, powertrain: 25.0, avionics: 6.0, recovery: 7.0,
           payload: 50.0, fuel: 101.5, mtow: 250.0}
aero:     {cd0: 0.020, oswald_e: 0.85, cl_max: 1.6}
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_geometry_closure.py -v`
Expected: 5 PASSED, 1 XFAIL (the documented report §2 tail discrepancy)

- [ ] **Step 7: Commit**

```bash
git add argus7/ design/ tests/test_geometry_closure.py
git commit -m "feat(design): parameter schema with geometry closure guards

Single source of truth for all geometry. Closure assertions make the
superseded-chord regression (Defect 2) unrepresentable. Documents the
report section-2 tail volume discrepancy as an xfail rather than
silently picking a value."
```

---

### Task 2: Airfoil coordinate library

**Files:**
- Create: `argus7/cad/__init__.py`, `argus7/cad/airfoil_coords.py`
- Create: `data/airfoils/fx63137.dat`, `data/airfoils/naca0010.dat`
- Test: `tests/test_airfoil_coords.py`

**Interfaces:**
- Consumes: nothing
- Produces:
  - `load_airfoil(name: str) -> np.ndarray` — (N,2) array, Selig order (TE→upper→LE→lower→TE), x normalised 0..1
  - `naca4(code: str, n: int = 121) -> np.ndarray`
  - `scale_airfoil(coords, chord, twist_rad, le_pos) -> np.ndarray` — (N,3) points in the project frame
  - `max_thickness(coords) -> float`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_airfoil_coords.py
import numpy as np, pytest
from argus7.cad.airfoil_coords import load_airfoil, naca4, max_thickness, scale_airfoil

def test_naca0010_thickness_is_10_percent():
    assert max_thickness(naca4("0010")) == pytest.approx(0.10, abs=0.002)

def test_naca0012_thickness_is_12_percent():
    assert max_thickness(naca4("0012")) == pytest.approx(0.12, abs=0.002)

def test_naca0010_is_symmetric():
    c = naca4("0010")
    assert abs(c[:, 1].max() + c[:, 1].min()) < 1e-6

def test_fx63137_thickness_matches_its_name():
    """FX 63-137 is 13.7% thick by designation."""
    assert max_thickness(load_airfoil("fx63137")) == pytest.approx(0.137, abs=0.005)

def test_coordinates_are_normalised():
    c = load_airfoil("fx63137")
    assert c[:, 0].min() == pytest.approx(0.0, abs=1e-6)
    assert c[:, 0].max() == pytest.approx(1.0, abs=1e-6)

def test_scale_airfoil_applies_chord_and_twist():
    c = naca4("0010")
    out = scale_airfoil(c, chord=0.5, twist_rad=0.0, le_pos=(1.0, 2.0, 0.3))
    assert out.shape[1] == 3
    # chord runs aft along +x from the leading edge
    assert out[:, 0].max() - out[:, 0].min() == pytest.approx(0.5, abs=1e-6)
    assert out[:, 1].min() == pytest.approx(2.0, abs=1e-6)  # constant span station

def test_twist_rotates_about_leading_edge():
    c = naca4("0010")
    a = scale_airfoil(c, 1.0, 0.0, (0.0, 0.0, 0.0))
    b = scale_airfoil(c, 1.0, np.deg2rad(-3.0), (0.0, 0.0, 0.0))
    assert b[:, 2].max() != pytest.approx(a[:, 2].max(), abs=1e-6)
    # leading edge is the pivot and must not move
    le_a, le_b = a[np.argmin(a[:, 0])], b[np.argmin(b[:, 0])]
    assert np.allclose(le_a, le_b, atol=1e-6)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_airfoil_coords.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'argus7.cad'`

- [ ] **Step 3: Implement the coordinate library**

```python
# argus7/cad/airfoil_coords.py
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
    """Load a Selig-format .dat file, skipping the title line, and normalise x to 0..1."""
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
    c = np.array(rows)
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
    rotated by `twist_rad` about the leading edge (negative = washout, nose down),
    and translated so its leading edge sits at `le_pos`.
    """
    xc, zc = coords[:, 0] * chord, coords[:, 1] * chord
    ct, st = np.cos(twist_rad), np.sin(twist_rad)
    xr = xc * ct - zc * st
    zr = xc * st + zc * ct
    x0, y0, z0 = le_pos
    return np.column_stack([xr + x0, np.full_like(xr, y0), zr + z0])
```

- [ ] **Step 4: Fetch the FX 63-137 coordinates**

```bash
mkdir -p data/airfoils
curl -sS "https://m-selig.ae.illinois.edu/ads/coord/fx63137.dat" -o data/airfoils/fx63137.dat
head -3 data/airfoils/fx63137.dat
.venv/bin/python -c "
from argus7.cad.airfoil_coords import load_airfoil, max_thickness
print('t/c =', max_thickness(load_airfoil('fx63137')))"
```

Expected: `t/c ≈ 0.137`. If the UIUC fetch fails, generate a placeholder with
`naca4('4413')` (similar camber and thickness class), record the substitution in
`data/airfoils/README.md`, and open it as a known gap — do **not** silently
substitute without recording it.

- [ ] **Step 5: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_airfoil_coords.py -v`
Expected: 7 PASSED

- [ ] **Step 6: Commit**

```bash
git add argus7/cad/ data/airfoils/ tests/test_airfoil_coords.py
git commit -m "feat(cad): airfoil coordinate library with NACA4 generator

Real section coordinates replace the sphere-hull massing that stood in
for an airfoil (Defect 3). Twist rotates about the leading edge."
```

---

### Task 3: Lofted wing solid

**Files:**
- Create: `argus7/cad/model.py`
- Test: `tests/test_cad_wing.py`

**Interfaces:**
- Consumes: `load_design`, `derive_wing` (Task 1); `load_airfoil`, `naca4`, `scale_airfoil` (Task 2)
- Produces:
  - `build_wing(design, n_sections: int = 9) -> build123d.Part` — full wing, both halves, origin at wing root leading edge
  - `section_stations(design, n) -> list[tuple[float, float, float, float]]` — `(y, chord, twist_rad, x_le)` per station

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_cad_wing.py
import math, pytest
from argus7.design.schema import load_design
from argus7.design.geometry import derive_wing
from argus7.cad.model import build_wing, section_stations

@pytest.fixture(scope="module")
def design(): return load_design("design/argus7_v1.yaml")

@pytest.fixture(scope="module")
def wing(design): return build_wing(design)

def test_wing_spans_along_y_not_x(wing, design):
    """REGRESSION GUARD FOR DEFECT 1: the wing must span across the airframe,
    not along it. The original SCAD spanned the wing along the fuselage axis."""
    bb = wing.bounding_box()
    span_extent  = bb.max.Y - bb.min.Y
    chord_extent = bb.max.X - bb.min.X
    assert span_extent > 8.0, f"wing spans only {span_extent:.2f} m in y"
    assert span_extent > 5 * chord_extent, "wing is not spanwise-dominant in y"

def test_wing_span_matches_derived_geometry(wing, design):
    g = derive_wing(design.wing)
    bb = wing.bounding_box()
    assert (bb.max.Y - bb.min.Y) == pytest.approx(g.span_m, rel=0.02)

def test_wing_is_symmetric_about_centreline(wing):
    bb = wing.bounding_box()
    assert bb.max.Y == pytest.approx(-bb.min.Y, abs=1e-3)

def test_wing_planform_area_matches_spec(wing, design):
    """Loft volume / span / mean-thickness should recover S within meshing tolerance."""
    g = derive_wing(design.wing)
    approx_area = wing.volume / (0.68 * design.wing.thickness_ratio * g.mac_m)
    assert approx_area == pytest.approx(g.area_m2, rel=0.15)

def test_wing_solid_is_valid(wing):
    assert wing.is_valid()
    assert wing.volume > 0

def test_stations_apply_linear_taper_and_washout(design):
    g = derive_wing(design.wing)
    st = section_stations(design, 9)
    root, tip = st[0], st[-1]
    assert root[1] == pytest.approx(g.chord_root_m, rel=1e-6)
    assert tip[1]  == pytest.approx(g.chord_tip_m,  rel=1e-6)
    assert root[2] == pytest.approx(0.0, abs=1e-9)
    assert tip[2]  == pytest.approx(math.radians(design.wing.twist_tip_deg), rel=1e-6)

def test_dihedral_raises_the_tip(design, wing):
    bb = wing.bounding_box()
    g = derive_wing(design.wing)
    expected_rise = (g.span_m / 2) * math.tan(math.radians(design.wing.dihedral_deg))
    assert bb.max.Z > 0.5 * expected_rise
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_cad_wing.py -v`
Expected: FAIL — `ImportError: cannot import name 'build_wing'`

- [ ] **Step 3: Implement the wing loft**

```python
# argus7/cad/model.py
from __future__ import annotations
import math
import numpy as np
from build123d import Part, Polyline, make_face, loft, Plane, Vector

from argus7.design.geometry import derive_wing
from argus7.cad.airfoil_coords import load_airfoil, naca4, scale_airfoil

def _section_coords(name: str) -> np.ndarray:
    return naca4(name[4:]) if name.upper().startswith("NACA") else load_airfoil(name)

def section_stations(design, n: int = 9):
    """(y, chord, twist_rad, x_le) at n stations from root to tip."""
    g = derive_wing(design.wing)
    semi = g.span_m / 2.0
    sweep = math.radians(design.wing.sweep_le_deg)
    out = []
    for i in range(n):
        f = i / (n - 1)                                  # 0 at root, 1 at tip
        y = f * semi
        chord = g.chord_root_m + f * (g.chord_tip_m - g.chord_root_m)
        twist = f * math.radians(design.wing.twist_tip_deg)
        x_le = y * math.tan(sweep)
        out.append((y, chord, twist, x_le))
    return out

def _section_face(design, y, chord, twist, x_le, dihedral_rad, coords):
    z = y * math.tan(dihedral_rad)
    pts = scale_airfoil(coords, chord, twist, (x_le, y, z))
    verts = [Vector(*p) for p in pts]
    if (verts[0] - verts[-1]).length > 1e-9:
        verts.append(verts[0])                            # close the section
    return make_face(Polyline(*verts))

def build_wing(design, n_sections: int = 9) -> Part:
    """Full wing, both halves, lofted through real airfoil sections.

    Origin is the root leading edge. x aft, y starboard, z up.
    """
    coords = _section_coords(design.wing.airfoil)
    dihedral = math.radians(design.wing.dihedral_deg)
    faces = [_section_face(design, y, c, t, x, dihedral, coords)
             for (y, c, t, x) in section_stations(design, n_sections)]
    starboard = loft(faces)
    port = starboard.mirror(Plane.XZ)
    return starboard + port
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_cad_wing.py -v`
Expected: 7 PASSED

If `loft` rejects the section wires, reduce `n_sections` to 5 and confirm the
sections are planar and consistently oriented before increasing again.

- [ ] **Step 5: Commit**

```bash
git add argus7/cad/model.py tests/test_cad_wing.py
git commit -m "feat(cad): lofted wing with real sections, twist and dihedral

Includes the Defect 1 regression guard: the wing must span along y and
be spanwise-dominant, which the original SCAD model was not."
```

---

### Task 4: Fuselage, booms, inverted-V tail and installed items

**Files:**
- Modify: `argus7/cad/model.py`
- Test: `tests/test_cad_airframe.py`

**Interfaces:**
- Consumes: `build_wing`, `section_stations` (Task 3)
- Produces:
  - `build_fuselage(design) -> Part`
  - `build_booms(design) -> Part`
  - `build_tail(design) -> Part`
  - `build_installed_items(design) -> Part` — EO/IR gimbal ball, parachute bay, prop disc, antenna blade
  - `build_aircraft(design) -> Part` — the assembled model

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_cad_airframe.py
import pytest
from argus7.design.schema import load_design
from argus7.design.geometry import derive_wing
from argus7.cad.model import build_fuselage, build_booms, build_tail, build_aircraft

@pytest.fixture(scope="module")
def design(): return load_design("design/argus7_v1.yaml")

def test_fuselage_runs_along_x(design):
    """REGRESSION GUARD FOR DEFECT 1, other half: the fuselage must be the
    long axis in x while the wing is long in y. In the original SCAD both
    ran along y."""
    bb = build_fuselage(design).bounding_box()
    length = bb.max.X - bb.min.X
    width  = bb.max.Y - bb.min.Y
    assert length == pytest.approx(design.fuselage.length_m, rel=0.05)
    assert length > 4 * width

def test_wing_and_fuselage_axes_are_perpendicular(design):
    """The precise defect: wing long axis and fuselage long axis must differ."""
    fus = build_fuselage(design).bounding_box()
    from argus7.cad.model import build_wing
    wing = build_wing(design).bounding_box()
    fus_long  = "X" if (fus.max.X - fus.min.X) > (fus.max.Y - fus.min.Y) else "Y"
    wing_long = "X" if (wing.max.X - wing.min.X) > (wing.max.Y - wing.min.Y) else "Y"
    assert fus_long == "X" and wing_long == "Y"

def test_booms_are_spaced_in_y_and_run_along_x(design):
    bb = build_booms(design).bounding_box()
    g = derive_wing(design.wing)
    expected_sep = 2 * design.booms.y_station_frac * (g.span_m / 2)
    assert (bb.max.Y - bb.min.Y) == pytest.approx(expected_sep, rel=0.2)
    assert (bb.max.X - bb.min.X) == pytest.approx(design.booms.length_m, rel=0.15)

def test_tail_sits_aft_of_the_wing(design):
    assert build_tail(design).bounding_box().min.X > 0.5 * design.tail.arm_m

def test_inverted_v_tail_dips_below_boom_line(design):
    """Inverted V means the panels angle downward from the boom."""
    assert build_tail(design).bounding_box().min.Z < 0.0

def test_full_aircraft_is_valid_and_within_envelope(design):
    ac = build_aircraft(design)
    g = derive_wing(design.wing)
    bb = ac.bounding_box()
    assert ac.is_valid()
    assert (bb.max.Y - bb.min.Y) == pytest.approx(g.span_m, rel=0.03)
    assert (bb.max.X - bb.min.X) < 1.5 * design.fuselage.length_m + design.tail.arm_m
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_cad_airframe.py -v`
Expected: FAIL — `ImportError: cannot import name 'build_fuselage'`

- [ ] **Step 3: Implement the airframe components**

```python
# append to argus7/cad/model.py
from build123d import Cylinder, Sphere, Box, Location, Rotation, Axis

def build_fuselage(design) -> Part:
    """Pod along +x: nose at x=0, engine/prop end at x=length. Lofted from
    circular stations so it is a true solid of revolution class, not a sphere hull."""
    L, R = design.fuselage.length_m, design.fuselage.max_diameter_m / 2.0
    # (x_fraction, radius_fraction) - nose, max section, aft taper to engine
    stations = [(0.00, 0.15), (0.08, 0.62), (0.22, 1.00), (0.55, 0.96),
                (0.80, 0.70), (1.00, 0.34)]
    faces = []
    for xf, rf in stations:
        pl = Plane(origin=(xf * L, 0, 0), z_dir=(1, 0, 0))
        faces.append(pl * make_face(pl.location * Circle(max(rf * R, 1e-3)).wire()))
    return loft(faces)

def build_booms(design) -> Part:
    """Twin booms: spaced in y, running along x, carrying the tail."""
    g = derive_wing(design.wing)
    y = design.booms.y_station_frac * (g.span_m / 2.0)
    r = design.booms.diameter_m / 2.0
    L = design.booms.length_m
    x0 = -0.25 * L                                       # boom starts ahead of the wing
    boom = Cylinder(radius=r, height=L, rotation=(0, 90, 0))
    starboard = Location((x0 + L / 2, y, 0)) * boom
    port      = Location((x0 + L / 2, -y, 0)) * boom
    return starboard + port

def build_tail(design) -> Part:
    """Inverted-V tail: two panels angled downward from the boom ends.

    area_h_m2 is the projected horizontal area, so each panel's true area is
    S_h / (2 cos^2(dihedral)).
    """
    g = derive_wing(design.wing)
    y_boom = design.booms.y_station_frac * (g.span_m / 2.0)
    gam = math.radians(design.tail.dihedral_deg)          # negative = inverted
    panel_area = design.tail.area_h_m2 / (2.0 * math.cos(gam) ** 2)
    lam = design.tail.taper_ratio
    panel_span = math.sqrt(panel_area * 3.0)              # AR 3 tail panel
    c_root = 2 * panel_area / (panel_span * (1 + lam))
    coords = _section_coords(design.tail.airfoil)
    x_te = design.tail.arm_m
    parts = []
    for sgn in (+1, -1):
        faces = []
        for f in (0.0, 1.0):
            chord = c_root * (1 + f * (lam - 1))
            span_off = f * panel_span
            y = sgn * (y_boom + span_off * math.cos(gam))
            z = span_off * math.sin(gam)
            pts = scale_airfoil(coords, chord, 0.0, (x_te, y, z))
            verts = [Vector(*p) for p in pts]
            if (verts[0] - verts[-1]).length > 1e-9:
                verts.append(verts[0])
            faces.append(make_face(Polyline(*verts)))
        parts.append(loft(faces))
    return parts[0] + parts[1]

def build_installed_items(design) -> Part:
    """EO/IR gimbal, parachute bay hump, pusher prop disc, comms antenna blade."""
    L, R = design.fuselage.length_m, design.fuselage.max_diameter_m / 2.0
    gimbal = Location((0.55 * R + 0.30, 0, -R - 0.06)) * Sphere(0.15)
    chute  = Location((0.95, 0, R * 0.75)) * Sphere(0.14)
    d = design.propulsion.prop_diameter_m
    prop = Location((L + 0.06, 0, 0)) * Cylinder(radius=d / 2, height=0.02,
                                                 rotation=(0, 90, 0))
    ant = Location((1.45, 0, -R - 0.08)) * Box(0.18, 0.012, 0.14)
    return gimbal + chute + prop + ant

def build_aircraft(design) -> Part:
    """Assembled model. Wing root LE is placed at 22% of fuselage length."""
    wing = Location((0.22 * design.fuselage.length_m, 0, 0.05)) * build_wing(design)
    return wing + build_fuselage(design) + build_booms(design) \
                + build_tail(design) + build_installed_items(design)
```

Add `Circle` to the `build123d` import list at the top of the file.

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_cad_airframe.py -v`
Expected: 6 PASSED

- [ ] **Step 5: Commit**

```bash
git add argus7/cad/model.py tests/test_cad_airframe.py
git commit -m "feat(cad): fuselage, booms, inverted-V tail and installed items

Fuselage runs along x, wing spans y - the perpendicularity is now an
explicit test, closing Defect 1."
```

---

### Task 5: Export to STEP, STL and regenerated OpenSCAD

**Files:**
- Create: `argus7/cad/export.py`
- Create: `argus7/cad/to_openscad.py`
- Test: `tests/test_cad_export.py`

**Interfaces:**
- Consumes: `build_aircraft` (Task 4), `derive_wing` (Task 1)
- Produces:
  - `export_model(design, outdir: Path) -> dict[str, Path]` — writes `argus7.step`, `argus7.stl`, returns paths
  - `emit_openscad(design, path: Path) -> Path` — regenerated `.scad` with a **generated** header
  - `check_watertight(stl_path) -> bool`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_cad_export.py
import pytest, trimesh
from pathlib import Path
from argus7.design.schema import load_design
from argus7.design.geometry import derive_wing
from argus7.cad.export import export_model, check_watertight
from argus7.cad.to_openscad import emit_openscad

@pytest.fixture(scope="module")
def design(): return load_design("design/argus7_v1.yaml")

@pytest.fixture(scope="module")
def exported(design, tmp_path_factory):
    return export_model(design, tmp_path_factory.mktemp("cad"))

def test_step_and_stl_are_written(exported):
    assert exported["step"].exists() and exported["step"].stat().st_size > 10_000
    assert exported["stl"].exists()  and exported["stl"].stat().st_size > 10_000

def test_stl_is_watertight(exported):
    assert check_watertight(exported["stl"])

def test_stl_span_matches_design(exported, design):
    m = trimesh.load(exported["stl"])
    g = derive_wing(design.wing)
    assert (m.bounds[1][1] - m.bounds[0][1]) == pytest.approx(g.span_m, rel=0.03)

def test_openscad_header_is_generated_not_handwritten(design, tmp_path):
    """Defect 2 was a hand-typed header that drifted from the real geometry."""
    g = derive_wing(design.wing)
    text = emit_openscad(design, tmp_path / "m.scad").read_text()
    assert f"{g.mac_m:.4f}" in text
    assert f"{g.chord_root_m:.4f}" in text
    assert "0.674" not in text, "superseded Gemini root chord reappeared"
    assert "GENERATED" in text.upper()

def test_openscad_output_parses(design, tmp_path):
    import shutil, subprocess
    if shutil.which("openscad") is None:
        pytest.skip("openscad not installed")
    p = emit_openscad(design, tmp_path / "m.scad")
    r = subprocess.run(["openscad", "-o", str(tmp_path / "m.stl"), str(p)],
                       capture_output=True, timeout=300)
    assert r.returncode == 0, r.stderr.decode()[:2000]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_cad_export.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'argus7.cad.export'`

- [ ] **Step 3: Implement export and OpenSCAD emission**

```python
# argus7/cad/export.py
from __future__ import annotations
from pathlib import Path
import trimesh
from build123d import export_step, export_stl
from argus7.cad.model import build_aircraft

def export_model(design, outdir: str | Path) -> dict[str, Path]:
    outdir = Path(outdir); outdir.mkdir(parents=True, exist_ok=True)
    ac = build_aircraft(design)
    step, stl = outdir / "argus7.step", outdir / "argus7.stl"
    export_step(ac, str(step))
    export_stl(ac, str(stl), tolerance=1e-3, angular_tolerance=0.1)
    return {"step": step, "stl": stl}

def check_watertight(stl_path: str | Path) -> bool:
    m = trimesh.load(str(stl_path))
    return bool(m.is_watertight)
```

```python
# argus7/cad/to_openscad.py
from __future__ import annotations
import math
from pathlib import Path
from argus7.design.geometry import derive_wing
from argus7.cad.airfoil_coords import load_airfoil, naca4
from argus7.cad.model import section_stations, _section_coords

def emit_openscad(design, path: str | Path) -> Path:
    """Emit a viewable .scad whose header and geometry both come from the
    loaded design. Nothing here is hand-typed, which is what Defect 2 was."""
    g = derive_wing(design.wing)
    coords = _section_coords(design.wing.airfoil)
    poly = ", ".join(f"[{x:.5f},{y:.5f}]" for x, y in coords)
    lines = [
        "// ==== GENERATED FILE - DO NOT EDIT ====",
        f"// Generated by argus7.cad.to_openscad from design '{design.name}' "
        f"variant {design.variant}.",
        "// Edit design/*.yaml and regenerate. Hand-editing reintroduces the",
        "// geometry-drift defect this pipeline exists to prevent.",
        f"// S = {g.area_m2:.4f} m2 | AR = {g.aspect_ratio:.4f} | b = {g.span_m:.4f} m",
        f"// c_root = {g.chord_root_m:.4f} m | c_tip = {g.chord_tip_m:.4f} m "
        f"| MAC = {g.mac_m:.4f} m",
        "// Axes: x aft, y starboard, z up.",
        "$fn = 64;",
        f"airfoil = [{poly}];",
        "",
        "module section(chord, twist, x_le, y, z) {",
        "    translate([x_le, y, z]) rotate([0, -twist, 0])",
        "        linear_extrude(height=0.001)",
        "            polygon(points=[for (p = airfoil) [p[0]*chord, p[1]*chord]]);",
        "}",
        "",
        "module wing() {",
    ]
    stations = section_stations(design, 15)
    dih = math.radians(design.wing.dihedral_deg)
    for (y0, c0, t0, x0), (y1, c1, t1, x1) in zip(stations, stations[1:]):
        z0, z1 = y0 * math.tan(dih), y1 * math.tan(dih)
        for sgn in (1, -1):
            lines.append(
                f"    hull() {{ section({c0:.5f}, {math.degrees(t0):.4f}, {x0:.5f}, "
                f"{sgn * y0:.5f}, {z0:.5f});"
                f" section({c1:.5f}, {math.degrees(t1):.4f}, {x1:.5f}, "
                f"{sgn * y1:.5f}, {z1:.5f}); }}")
    L = design.fuselage.length_m
    R = design.fuselage.max_diameter_m / 2
    yb = design.booms.y_station_frac * (g.span_m / 2)
    lines += [
        "}",
        "",
        "module fuselage() {",
        f"    hull() {{ translate([{0.22*L:.4f},0,0]) sphere({R:.4f});",
        f"             translate([{0.80*L:.4f},0,0]) sphere({0.70*R:.4f});",
        f"             translate([{L:.4f},0,0]) sphere({0.34*R:.4f});",
        f"             translate([0.02,0,0]) sphere({0.15*R:.4f}); }}",
        "}",
        "",
        "module booms() {",
        f"    for (s = [1,-1]) translate([{-0.25*design.booms.length_m:.4f}, "
        f"s*{yb:.4f}, 0]) rotate([0,90,0]) "
        f"cylinder(d={design.booms.diameter_m:.4f}, h={design.booms.length_m:.4f});",
        "}",
        "",
        f"translate([{0.22*L:.4f}, 0, 0.05]) wing();",
        "fuselage();",
        "booms();",
    ]
    p = Path(path); p.write_text("\n".join(lines) + "\n")
    return p
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_cad_export.py -v`
Expected: 5 PASSED (the last may SKIP if `openscad` is absent)

- [ ] **Step 5: Commit**

```bash
git add argus7/cad/export.py argus7/cad/to_openscad.py tests/test_cad_export.py
git commit -m "feat(cad): STEP/STL export and generated OpenSCAD

The .scad header is emitted from loaded parameters, so it cannot drift
from the geometry it describes."
```

---

### Task 6: Replace the defective model, render, and document

**Files:**
- Create: `argus7/cad/render.py`
- Create: `scripts/build_model.py`
- Delete then regenerate: `model/argus7_model.scad`
- Modify: `README.md:60-75` (the "Known gaps" section)
- Test: `tests/test_regression_defects.py`

**Interfaces:**
- Consumes: everything above
- Produces:
  - `render_views(stl_path, outdir) -> list[Path]` — three-view + isometric PNGs
  - `scripts/build_model.py` — one command regenerating every CAD artifact

- [ ] **Step 1: Write the failing regression test**

```python
# tests/test_regression_defects.py
"""One test per defect found in the original model/argus7_model.scad.
These must never pass by accident again."""
import re, pytest
from pathlib import Path
from argus7.design.schema import load_design
from argus7.design.geometry import derive_wing

SCAD = Path("model/argus7_model.scad")

def test_defect2_superseded_chords_absent_from_committed_model():
    text = SCAD.read_text()
    assert "0.674" not in text, "superseded Gemini root chord is back"
    assert "0.303" not in text, "superseded Gemini tip chord is back"

def test_committed_model_matches_the_design_file():
    g = derive_wing(load_design("design/argus7_v1.yaml").wing)
    text = SCAD.read_text()
    assert f"{g.chord_root_m:.4f}" in text
    assert f"{g.mac_m:.4f}" in text

def test_defect3_model_contains_a_real_airfoil():
    text = SCAD.read_text()
    assert "airfoil = [" in text
    n = len(re.findall(r"\[-?\d+\.\d+,-?\d+\.\d+\]", text))
    assert n > 50, f"only {n} section coordinates - not a real airfoil"

def test_model_is_marked_generated():
    assert "GENERATED" in SCAD.read_text().upper()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_regression_defects.py -v`
Expected: FAIL — the committed `model/argus7_model.scad` still contains `0.674`

- [ ] **Step 3: Write the renderer and build script**

```python
# argus7/cad/render.py
from __future__ import annotations
import subprocess, shutil
from pathlib import Path

VIEWS = {"top": (0, 0, 0), "front": (90, 0, 0), "side": (90, 0, 90),
         "iso": (55, 0, 25)}

def render_views(scad_path: str | Path, outdir: str | Path) -> list[Path]:
    """Render orthographic views with OpenSCAD's headless camera."""
    if shutil.which("openscad") is None:
        raise RuntimeError("openscad not installed - run scripts/setup_env.sh")
    outdir = Path(outdir); outdir.mkdir(parents=True, exist_ok=True)
    out = []
    for name, (rx, ry, rz) in VIEWS.items():
        png = outdir / f"argus7_{name}.png"
        subprocess.run(
            ["openscad", "--autocenter", "--viewall", "--imgsize=1600,1200",
             f"--camera=0,0,0,{rx},{ry},{rz},0", "-o", str(png), str(scad_path)],
            check=True, capture_output=True, timeout=600)
        out.append(png)
    return out
```

```python
# scripts/build_model.py
"""Regenerate every CAD artifact from design/argus7_v1.yaml."""
from pathlib import Path
from argus7.design.schema import load_design
from argus7.cad.export import export_model, check_watertight
from argus7.cad.to_openscad import emit_openscad
from argus7.cad.render import render_views

def main(design_path="design/argus7_v1.yaml"):
    design = load_design(design_path)
    paths = export_model(design, Path("model"))
    scad = emit_openscad(design, Path("model/argus7_model.scad"))
    print(f"STEP {paths['step']}\nSTL  {paths['stl']}\nSCAD {scad}")
    print(f"watertight: {check_watertight(paths['stl'])}")
    for p in render_views(scad, Path("figures/cad")):
        print(f"render {p}")

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Regenerate the model and run the regression tests**

```bash
.venv/bin/python scripts/build_model.py
.venv/bin/pytest tests/test_regression_defects.py -v
```

Expected: 4 PASSED. `model/argus7_model.scad` is now generated, carries real
airfoil coordinates, and contains no superseded chord values.

- [ ] **Step 5: Run the whole suite**

Run: `.venv/bin/pytest tests/ -v`
Expected: all PASS, exactly 1 XFAIL (the documented report §2 tail discrepancy)

- [ ] **Step 6: Update the README "Known gaps" section**

Replace the first two bullets of `README.md`'s "Known gaps" with:

```markdown
- The CAD model is generated from `design/argus7_v1.yaml` by
  `scripts/build_model.py`. Do not hand-edit `model/argus7_model.scad` — it is
  overwritten on every build, and hand-editing is what caused the original
  geometry drift.
- **Report §2 tail row does not close:** S_h = 0.31 m² with arm 3.2 m gives
  V_h = 0.577, not the stated 0.68 (17.9% off). Either S_h should be 0.366 m²
  or V_h is 0.577. Tracked as an xfail in
  `tests/test_geometry_closure.py::test_report_stated_tail_volume`, to be
  resolved in v2 rather than by silently editing v1.
```

- [ ] **Step 7: Commit**

```bash
git add argus7/cad/render.py scripts/build_model.py model/ figures/cad/ \
        README.md tests/test_regression_defects.py
git commit -m "feat(cad): regenerate model from design file, retire hand-edited SCAD

Replaces the defective hand-written model. All four defects now carry
regression tests: wing/fuselage axis collision, superseded chords,
missing airfoil, and hand-written headers."
```

---

## Self-Review

**Spec coverage.** §5 data contract → Task 1. §6.4/§10 `cad/` → Tasks 2–6. Global
constraint "generated headers" → Tasks 5–6. Defects 1/2/3 from spec §1 → regression
tests in Tasks 3, 4 and 6. The report §2 tail discrepancy discovered during planning
→ Task 1 xfail plus README entry. Spec §6.1–6.3 (aero, prop, struct), §7
(optimisation) and §9 (gauntlet) are **out of scope for P1 by design** — they are
phases P2–P5 and get their own plans.

**Placeholder scan.** No TBD/TODO. Every code step carries runnable code. The one
conditional branch (UIUC fetch failure in Task 2 Step 4) specifies the exact
fallback and requires recording it rather than silently substituting.

**Type consistency.** `load_design` returns `Design` (Task 1) and is consumed under
that name in Tasks 3–6. `derive_wing` returns `WingGeometry` with `span_m`,
`chord_root_m`, `chord_tip_m`, `mac_m` — used consistently throughout.
`section_stations` returns `(y, chord, twist_rad, x_le)` in Task 3 and is unpacked
in that order in Tasks 4 and 5. `_section_coords` is defined in Task 3 and imported
by `to_openscad` in Task 5. `export_model` returns `dict[str, Path]` keyed
`"step"`/`"stl"`, matching its use in Tasks 5 and 6.
