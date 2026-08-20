"""XFOIL 6.99 driver for ARGUS-7.

This module exists to encode a set of failure modes that were expensive to
find and are invisible once fixed. Read this docstring before changing the
command sequence.

Every rule below is enforced in code, not left to the caller's discipline:

(a) **Never hand XFOIL a raw UIUC ``.dat`` file.** XFOIL 6.99's Lednicer
    auto-detection does not fire on the repository's own
    ``data/airfoils/fx63137.dat``; it ingests the ``49. 49.`` point-count
    header as a coordinate pair and then SIGFPEs. The driver always writes a
    fresh Selig-ordered temp file from
    :func:`argus7.cad.airfoil_coords.load_airfoil`, which already normalises
    both conventions to one.

(b) **Never send ``PLOP`` / ``G F``.** The usual "disable graphics" incantation
    itself SIGFPEs in this build. Piping to stdin headless needs no such
    toggle -- XFOIL simply never opens a plot window.

(c) **``PPAR`` needs two blank lines.** It re-displays its whole menu after
    every parameter, so one blank line commits the change and re-prints, and
    the second one leaves the menu. One blank line leaves the script one
    prompt out of step for the rest of the run.

(d) **Never fewer than 280 panel nodes.** XFOIL's ``PANE`` default of 160
    puts upper-surface transition roughly five points of chord too far
    forward at the ARGUS-7 loiter condition -- with no crash, no warning and
    a perfectly converged solution. Measured on FX 63-137 at C_L = 1.21,
    Re 992,372: N=160 -> x_tr 0.4508, 200 -> 0.4833, 260 -> 0.4965,
    300 -> 0.5023, 360 -> 0.5010. Five points of chord is worth about
    -1.1 h of endurance (research/riblets_pack.md). :data:`MIN_PANELS`
    refuses anything below 280 and :func:`run_xfoil` defaults to 300.

(e) **Assert on the log, always.** A prompt-driven script that has
    desynchronised still produces plausible-looking numbers. Two real
    examples caught here: issuing ``PACC`` before ``VISC`` makes XFOIL
    reject ``VISC`` with "Polar is being accumulated. Cannot change its
    parameters in midstream." and quietly return an *inviscid* answer with
    zero "not recognized" messages; and ``VPAR / XTR`` with both values on
    one line is silently ignored, reporting natural transition instead.
    :func:`check_log` therefore verifies the "not recognized" count, that
    the viscous prompt was actually reached, the panel count and Ncrit that
    XFOIL echoed back, and that the number of solve attempts in the log
    equals the number of points requested.

Verified command sequence (this is the one that reproduces the reference
results; changes to it must be re-verified against
``tests/test_xfoil_driver.py``)::

    LOAD <selig temp file>
    PPAR / N <n_panels> / T 1.0 / <blank> / <blank>
    OPER
      VPAR / N <ncrit> / <blank>
      VPAR / <blank>            ! re-display so the log can be checked
      VISC <Re> / ITER <max_iter>
      CL <cl>   (or  ALFA <deg>)
      DUMP <file>
    <blank>
    QUIT

Transition convention
---------------------
``x_tr_upper`` / ``x_tr_lower`` are the points at which the shape factor H
first falls below :data:`H_TURBULENT` moving aft from the leading edge, i.e.
where the boundary layer is *fully turbulent*. This is deliberately not
XFOIL's e^N transition *onset*, which lies ahead of it (3.2 points of chord
at the root loiter point, 4.5 at the tip, but only 0.7 at C_L 1.7 -- the gap
is not a constant) and is markedly more panel-density sensitive. The H-based
point is the more stable number and it is the physically correct boundary for
anything that needs a developed turbulent layer. Both are reported: the e^N
onset is available as ``xtr_onset_upper`` / ``xtr_onset_lower``.

**x_tr == 1.0 is ambiguous and must be disambiguated.** H never falling below
:data:`H_TURBULENT` on a surface means one of two opposite things: the run is
genuinely laminar to the trailing edge, or the boundary layer transitioned and
then separated without reattaching, so H rises instead of falling. The second
case is real on this section at low Reynolds number -- ``run_xfoil("fx63137",
1e5, cl=1.0)`` returns ``converged=True``, ``x_tr_upper == 1.0`` and
``xtr_onset_upper == 0.136`` with a peak H of 20.4 and c_d = 0.156 (17x the
loiter value). Use :attr:`XFoilResult.separated_upper` /
:attr:`~XFoilResult.separated_lower`, which are exactly this distinction, or
read :attr:`~XFoilResult.h_max_upper` yourself. Never take ``x_tr == 1.0`` as
"100% laminar" without checking.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np

from argus7.cad.airfoil_coords import load_airfoil, naca4

__all__ = [
    "MIN_PANELS",
    "DEFAULT_PANELS",
    "H_TURBULENT",
    "H_LAMINAR_SEPARATION",
    "XFoilError",
    "XFoilResult",
    "run_xfoil",
    "polar_sweep",
    "write_selig_file",
    "build_script",
    "invoke_xfoil",
    "check_log",
    "parse_dump",
    "transition_from_dump",
]

# --- Constants ------------------------------------------------------------

#: Hard floor on panel nodes. Below this XFOIL is wrong without saying so --
#: see rule (d) in the module docstring. The measured sweep at the loiter
#: condition puts x_tr at 0.4508 / 0.4833 / 0.4965 / 0.5023 / 0.5010 for
#: 160 / 200 / 260 / 300 / 360 nodes: the answer is converged somewhere
#: between 260 and 300, and 160 -- XFOIL's own default -- is 5.2 points of
#: chord forward of it. 280 is the floor because it sits above the knee with
#: margin; it is not a value to relax when a run feels slow.
MIN_PANELS = 280

#: Default panel count. 300 is the value all the verified ARGUS-7 reference
#: results were produced at (research/riblets_pack.md, reproducibility
#: appendix), and the sweep shows it is converged: 360 moves x_tr by 0.0013.
DEFAULT_PANELS = 300

#: Shape factor below which the boundary layer is taken as fully turbulent.
#: H ~ 2.6 at a laminar stagnation point, ~2.2-2.6 through the laminar run,
#: and falls to ~1.4-1.9 once turbulent; 2.0 is the standard dividing line
#: and is the criterion used for every published ARGUS-7 x_tr figure.
H_TURBULENT = 2.0

#: Shape factor above which a boundary layer that never reached
#: :data:`H_TURBULENT` is taken to have separated rather than stayed laminar.
#: Laminar separation is conventionally placed at H = 3.5-4.0 (Thwaites'
#: criterion gives H ~ 3.55 at zero wall shear; Cebeci & Bradshaw quote
#: 3.5-4.0). 4.0 is chosen because the attached reference case measures a
#: peak H of 3.22 on the upper surface, and the separated Re 1e5 case
#: measures 20.4 -- the threshold is nowhere near either.
H_LAMINAR_SEPARATION = 4.0

#: PPAR "TE/LE panel density ratio". 1.0 (uniform) is part of the verified
#: sequence; XFOIL's own default of 0.15 starves the trailing edge.
TE_LE_DENSITY_RATIO = 1.0

#: Default Newton iteration budget for one viscous solve. XFOIL's own
#: default is 10, which is not enough to converge a high-lift low-Re section
#: at fixed C_L; 300 is what the reference runs used.
DEFAULT_MAX_ITER = 300

#: Default Ncrit -- standard free-air e^N amplification (0.07% turbulence
#: level). The ARGUS-7 reference survey uses 9.
DEFAULT_NCRIT = 9

#: XFOIL 6.99's DUMP columns, in order. The build in use writes the first 12
#: for airfoil-surface nodes and the first 8 for wake nodes, even though the
#: header names 14. Index 7 is H, and everything downstream depends on that.
DUMP_COLUMNS = ("s", "x", "y", "Ue/Vinf", "Dstar", "Theta", "Cf", "H",
                "H*", "P", "m", "K", "tau", "Di")
H_COLUMN = 7
X_COLUMN = 1

_VISCOUS_PROMPT = ".OPERv"


def _xfoil_binary() -> str:
    """Locate the XFOIL executable.

    ``XFOIL_BIN`` in the environment wins, then ``PATH``, then the
    repository's ``vendor/bin``.
    """
    override = os.environ.get("XFOIL_BIN")
    if override:
        return override
    found = shutil.which("xfoil")
    if found:
        return found
    vendor = Path(__file__).resolve().parents[2] / "vendor" / "bin" / "xfoil"
    if vendor.exists():
        return str(vendor)
    raise XFoilError(
        "XFOIL executable not found: it is not on PATH, not at "
        f"{vendor}, and XFOIL_BIN is unset.")


# --- Errors and results ---------------------------------------------------

class XFoilError(RuntimeError):
    """Raised for anything that makes an XFOIL result untrustworthy.

    That includes refused inputs, a crashed or timed-out process, a log that
    shows the prompt-driven script desynchronised, and (by default) a
    solution that did not converge.
    """


@dataclass(frozen=True)
class XFoilResult:
    """One converged (or attempted) viscous XFOIL operating point."""

    airfoil: str
    reynolds: float
    mach: float
    ncrit: float
    n_panels: int
    mode: str                    # "cl" or "alpha"
    alpha_deg: float
    cl: float
    cd: float
    cdf: float                   # friction part of cd
    cdp: float                   # pressure part of cd
    cm: float                    # about the quarter chord
    x_tr_upper: float            # H < H_TURBULENT, fully turbulent
    x_tr_lower: float
    xtr_onset_upper: float       # XFOIL's own e^N onset, for comparison
    xtr_onset_lower: float
    converged: bool
    dump: np.ndarray = field(repr=False)      # (n_panels, >=8) surface nodes
    wake: np.ndarray = field(repr=False)      # (n_wake, >=8) wake nodes
    log: str = field(repr=False)

    @property
    def ld(self) -> float:
        """Section lift-to-drag ratio at this point."""
        return self.cl / self.cd

    @property
    def laminar_fraction_upper(self) -> float:
        """Fraction of upper-surface chord ahead of the fully-turbulent point.

        Meaningless when :attr:`separated_upper` is true: the surface never
        reaches H < 2 because it separated, not because it stayed laminar,
        and this property would then read 1.0 on a stalled section. Check
        :attr:`separated_upper` first.
        """
        return self.x_tr_upper

    def _surface_h(self, upper: bool) -> np.ndarray:
        """Shape factor along one surface, leading edge -> trailing edge."""
        dump = np.asarray(self.dump, dtype=float)
        le = int(np.argmin(dump[:, X_COLUMN]))
        side = dump[:le + 1][::-1] if upper else dump[le:]
        return side[:, H_COLUMN]

    @property
    def h_max_upper(self) -> float:
        """Peak shape factor on the upper surface (3.2 attached, >10 separated)."""
        return float(self._surface_h(True).max())

    @property
    def h_max_lower(self) -> float:
        """Peak shape factor on the lower surface."""
        return float(self._surface_h(False).max())

    @property
    def separated_upper(self) -> bool:
        """True when ``x_tr_upper`` is 1.0 because the flow separated.

        The H < :data:`H_TURBULENT` criterion returns 1.0 both for a surface
        that is genuinely laminar to the trailing edge and for one that
        transitioned and then separated without reattaching -- opposite
        physics, identical number. This separates them: no turbulent station
        anywhere *and* a peak H past :data:`H_LAMINAR_SEPARATION`.
        """
        h = self._surface_h(True)
        return bool((h >= H_TURBULENT).all() and h.max() > H_LAMINAR_SEPARATION)

    @property
    def separated_lower(self) -> bool:
        """As :attr:`separated_upper`, for the lower surface."""
        h = self._surface_h(False)
        return bool((h >= H_TURBULENT).all() and h.max() > H_LAMINAR_SEPARATION)


# --- Input validation -----------------------------------------------------

def _check_airfoil_name(name: str) -> str:
    """Refuse anything that looks like a path to a coordinate file.

    Rule (a): a raw UIUC ``.dat`` handed to XFOIL's LOAD is a SIGFPE waiting
    to happen. Callers pass the *name* of an airfoil; this module does the
    loading.
    """
    if not isinstance(name, str) or not name.strip():
        raise XFoilError("airfoil_name must be a non-empty string, e.g. 'fx63137'.")
    looks_like_path = ("/" in name) or ("\\" in name) or (os.sep in name)
    if name.lower().endswith(".dat") or looks_like_path:
        raise XFoilError(
            f"Refusing airfoil_name={name!r}: this driver never passes a raw "
            ".dat file to XFOIL's LOAD. XFOIL 6.99's Lednicer detection does "
            "not fire on the UIUC files in data/airfoils, so it reads the "
            "point-count header as a coordinate and SIGFPEs. Pass the bare "
            "airfoil name (e.g. 'fx63137'); the driver writes a Selig temp "
            "file from argus7.cad.airfoil_coords.load_airfoil() itself.")
    return name


def _check_panels(n_panels: int) -> int:
    if int(n_panels) != n_panels:
        raise XFoilError(f"n_panels must be an integer, got {n_panels!r}.")
    n_panels = int(n_panels)
    if n_panels < MIN_PANELS:
        raise XFoilError(
            f"Refusing n_panels={n_panels}: the floor is {MIN_PANELS}. "
            "Too few panels is XFOIL's silent-error mode -- the run converges "
            "cleanly, emits no warning, and puts transition several points of "
            "chord too far forward. Measured on FX 63-137 at C_L=1.21, "
            "Re 992372: N=160 gives x_tr 0.4508 against 0.5023 at N=300, and "
            "no repanelling at all costs +27% drag. If you genuinely want to "
            "study the panel sensitivity, use build_script()/invoke_xfoil() "
            "directly, as tests/test_xfoil_driver.py does.")
    return n_panels


# --- Geometry file --------------------------------------------------------

def write_selig_file(airfoil_name: str, path: str | Path) -> Path:
    """Write ``airfoil_name`` as a labelled Selig-ordered file XFOIL can LOAD.

    The coordinates come from :func:`argus7.cad.airfoil_coords.load_airfoil`
    (or :func:`~argus7.cad.airfoil_coords.naca4` for a ``naca####`` name), so
    Lednicer files are already converted and normalised. The first line is a
    name XFOIL cannot mistake for a coordinate pair.
    """
    _check_airfoil_name(airfoil_name)
    key = airfoil_name.lower().replace("-", "").replace(" ", "")
    if re.fullmatch(r"naca\d{4}", key):
        coords = naca4(key[4:])
    else:
        coords = load_airfoil(airfoil_name)

    label = re.sub(r"[^A-Za-z0-9]", "", airfoil_name).upper() or "AIRFOIL"
    if not any(ch.isalpha() for ch in label):
        label = "AF" + label            # never let the title parse as numbers

    path = Path(path)
    with path.open("w") as fh:
        fh.write(label + "\n")
        for x, y in coords:
            fh.write(f"{x:12.7f}{y:12.7f}\n")
    return path


# --- Command script -------------------------------------------------------

def build_script(af_filename: str, reynolds: float,
                 points: Sequence[tuple[str, float]],
                 dump_filenames: Sequence[str],
                 n_panels: int,
                 ncrit: float = DEFAULT_NCRIT,
                 max_iter: int = DEFAULT_MAX_ITER,
                 mach: float = 0.0) -> str:
    """Assemble the verified XFOIL command script.

    ``points`` is a sequence of ``("cl", value)`` / ``("alpha", value)``
    pairs, each paired with a filename in ``dump_filenames``.

    Filenames must be *bare* names, resolved against the working directory
    the process is launched in: XFOIL truncates long paths in its command
    line and then reports ``File OPEN error. Nonexistent file: /``, which is
    how this was found.

    This function is public so that the panel-sensitivity study -- which has
    to reach past :func:`run_xfoil`'s panel guard on purpose -- can build a
    deliberately unsafe script without a back door in the safe API.
    """
    if len(points) != len(dump_filenames):
        raise XFoilError("points and dump_filenames must be the same length.")
    for name in (af_filename, *dump_filenames):
        if "/" in name or "\\" in name:
            raise XFoilError(
                f"{name!r}: XFOIL silently truncates long paths. Pass bare "
                "filenames and run the process with cwd set to their directory.")

    lines: list[str] = [
        f"LOAD {af_filename}",
        "PPAR",
        f"N {int(n_panels)}",
        f"T {TE_LE_DENSITY_RATIO}",
        "",                       # rule (c): commit + re-display ...
        "",                       # ... and leave the menu
        "OPER",
        "VPAR",
        f"N {ncrit}",
        "",
        "VPAR",                   # re-enter purely so the log echoes the
        "",                       # *post-change* Ncrit for check_log()
    ]
    if mach:
        lines.append(f"MACH {mach}")
    # VISC must come after any polar-accumulation setup, never before -- and
    # this driver never accumulates a polar at all. See rule (e).
    lines += [f"VISC {reynolds:.10g}", f"ITER {int(max_iter)}"]
    for (mode, value), dump_name in zip(points, dump_filenames):
        cmd = "CL" if mode == "cl" else "ALFA"
        lines += [f"{cmd} {value:.10g}", f"DUMP {dump_name}"]
    lines += ["", "QUIT", ""]
    return "\n".join(lines)


def invoke_xfoil(script: str, workdir: str | Path, timeout: float = 600.0) -> str:
    """Run XFOIL headless on ``script`` in ``workdir`` and return its stdout.

    No ``PLOP`` is sent (rule (b)): that toggle SIGFPEs in this build, and
    piping to stdin needs no graphics suppression.
    """
    workdir = Path(workdir)
    try:
        proc = subprocess.run(
            [_xfoil_binary()], input=script, cwd=str(workdir),
            capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise XFoilError(
            f"XFOIL did not finish within {timeout} s. Its stdin is a fixed "
            "script, so a hang means the prompt sequence desynchronised and "
            "XFOIL is waiting for input that will never come.") from exc
    if proc.returncode != 0:
        tail = "\n".join(proc.stdout.splitlines()[-25:])
        raise XFoilError(
            f"XFOIL exited with code {proc.returncode} "
            f"(negative means a signal; -8 is SIGFPE, the classic raw-.dat or "
            f"PLOP crash). Last output:\n{tail}")
    return proc.stdout


# --- Log assertions -------------------------------------------------------

_RE_NOT_RECOGNIZED = re.compile(r"not recognized")
_RE_PANELS = re.compile(r"Number of panel nodes\s+(\d+)")
_RE_NCRIT = re.compile(r"Ncrit[TB]?\s*=\s*([\d.]+)")
_RE_SOLVE_START = re.compile(r"(?m)^\s*1\s+rms:")
# MRCHUE/MRCHDU report inner boundary-layer marching failures constantly on a
# healthy run. Only VISCAL's message means the operating point failed.
_RE_VISCAL_FAIL = re.compile(r"VISCAL:\s+Convergence failed")
_RE_FORCES = re.compile(
    r"a\s*=\s*(-?[\d.]+)\s+CL\s*=\s*(-?[\d.]+)\s*\n"
    r"\s*Cm\s*=\s*(-?[\d.]+)\s+CD\s*=\s*(-?[\d.]+)\s*=>\s*"
    r"CDf\s*=\s*(-?[\d.]+)\s+CDp\s*=\s*(-?[\d.]+)")
_RE_TRANSITION = re.compile(
    r"Side\s+(\d)\s+(free|forced)\s+transition at x/c =\s*(-?[\d.]+)")


def check_log(log: str, *, n_panels: int, ncrit: float, n_points: int) -> list[str]:
    """Verify the run stayed in step, and split the log into per-point segments.

    Raises :class:`XFoilError` on any structural problem. Returns one log
    segment per requested operating point, in order, so the caller can read
    each point's forces and convergence state from its own segment.

    What is checked, and why each check exists:

    * zero ``not recognized`` -- one desynchronised prompt shifts every
      later command by one and the output still looks plausible;
    * the viscous prompt ``.OPERv`` was reached -- ``VISC`` can be *refused*
      (e.g. after ``PACC``) and XFOIL then answers inviscidly, silently;
    * the panel count XFOIL echoed back is the one asked for -- proves the
      two blank lines after ``PPAR`` landed;
    * the Ncrit XFOIL echoed back *after* the change is the one asked for;
    * one solve was attempted per requested point -- catches a dropped or
      duplicated operating-point command.
    """
    n_bad = len(_RE_NOT_RECOGNIZED.findall(log))
    if n_bad:
        raise XFoilError(
            f"XFOIL reported {n_bad} unrecognised command(s). The script is "
            "out of step with XFOIL's prompts; every number after the first "
            "one is untrustworthy.")

    if _VISCOUS_PROMPT not in log:
        raise XFoilError(
            "XFOIL never reached its viscous prompt ('.OPERv'), so VISC did "
            "not take effect and any forces in this log are INVISCID. The "
            "usual cause is issuing a command that locks the operating "
            "state (PACC) before VISC, which XFOIL refuses without emitting "
            "'not recognized'.")

    panels = _RE_PANELS.findall(log)
    if not panels:
        raise XFoilError("XFOIL never echoed a panel count; PPAR did not run.")
    if int(panels[-1]) != int(n_panels):
        raise XFoilError(
            f"XFOIL is panelled with {panels[-1]} nodes, not the requested "
            f"{n_panels}. PPAR did not commit -- it re-displays its menu "
            "after every parameter and needs two blank lines to commit and "
            "exit.")

    ncrits = _RE_NCRIT.findall(log)
    if not ncrits:
        raise XFoilError("XFOIL never echoed Ncrit; VPAR did not run.")
    if abs(float(ncrits[-1]) - float(ncrit)) > 1e-6:
        raise XFoilError(
            f"XFOIL is running Ncrit={ncrits[-1]}, not the requested {ncrit}.")

    segments = _RE_SOLVE_START.split(log)[1:]
    if len(segments) != n_points:
        raise XFoilError(
            f"XFOIL attempted {len(segments)} viscous solve(s) but "
            f"{n_points} operating point(s) were requested. The prompt "
            "sequence desynchronised.")
    return segments


def _forces_from_segment(segment: str) -> tuple[float, float, float, float, float, float]:
    """Last (alpha, CL, Cm, CD, CDf, CDp) block in one solve's output."""
    blocks = _RE_FORCES.findall(segment)
    if not blocks:
        raise XFoilError(
            "No force block found for this operating point; XFOIL produced "
            "no 'a = ... CL = ...' output.")
    a, cl, cm, cd, cdf, cdp = blocks[-1]
    return float(a), float(cl), float(cm), float(cd), float(cdf), float(cdp)


def _onset_from_segment(segment: str) -> tuple[float, float]:
    """XFOIL's own e^N transition onset, last reported, per surface."""
    upper = lower = float("nan")
    for side, _kind, xc in _RE_TRANSITION.findall(segment):
        if side == "1":
            upper = float(xc)
        else:
            lower = float(xc)
    return upper, lower


# --- DUMP parsing ---------------------------------------------------------

def parse_dump(path: str | Path) -> tuple[np.ndarray, np.ndarray]:
    """Read an XFOIL ``DUMP`` file into (surface nodes, wake nodes).

    The file is ragged: airfoil-surface rows carry the full boundary-layer
    state (12 numeric columns in this build) and wake rows carry a shorter
    subset (8). Columns are :data:`DUMP_COLUMNS`; H is at index
    :data:`H_COLUMN` = 7.
    """
    rows: list[list[float]] = []
    for line in Path(path).read_text().splitlines():
        parts = line.split()
        if not parts or parts[0].startswith("#"):
            continue
        try:
            rows.append([float(v) for v in parts])
        except ValueError:
            continue                      # header or stray text
    if not rows:
        raise XFoilError(f"{path}: XFOIL wrote no dump rows.")

    width = max(len(r) for r in rows)
    if width <= H_COLUMN:
        raise XFoilError(
            f"{path}: dump has only {width} columns, so there is no H column "
            f"at index {H_COLUMN}. The dump is not the expected format.")
    surface = np.array([r for r in rows if len(r) == width], dtype=float)
    narrow = [r for r in rows if len(r) != width]
    n_wake = min((len(r) for r in narrow), default=0)
    wake = (np.array([r[:n_wake] for r in narrow], dtype=float)
            if narrow else np.empty((0, width)))
    return surface, wake


def transition_from_dump(dump: np.ndarray,
                         h_turbulent: float = H_TURBULENT
                         ) -> tuple[float, float]:
    """(x_tr_upper, x_tr_lower) by the H < ``h_turbulent`` criterion.

    ``dump`` is the surface block from :func:`parse_dump`, in XFOIL's node
    order (trailing edge -> upper -> leading edge -> lower -> trailing edge).
    Each surface is walked from the leading edge aft and the first station
    whose shape factor H (column index 7) has dropped below the threshold is
    returned. A surface that never crosses the threshold returns 1.0.

    Beware that 1.0 carries two opposite meanings: a run that really is
    laminar to the trailing edge, and one that transitioned and then
    separated without reattaching, so H climbs away from the threshold
    instead of falling through it. This function cannot tell them apart from
    a single number -- :attr:`XFoilResult.separated_upper` can, and does.
    """
    dump = np.asarray(dump, dtype=float)
    if dump.ndim != 2 or dump.shape[1] <= H_COLUMN:
        raise XFoilError(
            f"transition_from_dump needs a 2-D dump with more than "
            f"{H_COLUMN} columns; got shape {dump.shape}.")
    le = int(np.argmin(dump[:, X_COLUMN]))
    upper = dump[:le + 1][::-1]           # leading edge -> trailing edge
    lower = dump[le:]                     # leading edge -> trailing edge

    out = []
    for surface in (upper, lower):
        if surface.shape[0] == 0:
            out.append(1.0)
            continue
        turbulent = surface[:, H_COLUMN] < h_turbulent
        if not turbulent.any():
            out.append(1.0)
        else:
            out.append(float(surface[int(np.argmax(turbulent)), X_COLUMN]))
    return out[0], out[1]


# --- The runner -----------------------------------------------------------

def _normalise_points(cl, alpha) -> tuple[str, list[float]]:
    if (cl is None) == (alpha is None):
        raise XFoilError(
            "Give exactly one of cl= or alpha=. Fixed-C_L mode is what the "
            "ARGUS-7 loiter analysis uses; fixed-alpha is for polars that "
            "must span the stall.")
    if cl is not None:
        values = [cl] if np.isscalar(cl) else list(cl)
        return "cl", [float(v) for v in values]
    values = [alpha] if np.isscalar(alpha) else list(alpha)
    return "alpha", [float(v) for v in values]


def _run_points(airfoil_name: str, reynolds: float, mode: str,
                values: Sequence[float], n_panels: int, ncrit: float,
                max_iter: int, mach: float, timeout: float,
                require_converged: bool) -> list[XFoilResult]:
    airfoil_name = _check_airfoil_name(airfoil_name)
    reynolds = float(reynolds)
    if not np.isfinite(reynolds) or reynolds <= 0.0:
        raise XFoilError(f"Reynolds number must be positive and finite, got {reynolds!r}.")
    if mach < 0.0 or mach >= 1.0:
        raise XFoilError(f"mach must be in [0, 1), got {mach!r}.")
    if not values:
        raise XFoilError("No operating points requested.")

    points = [(mode, v) for v in values]
    dump_names = [f"dump{i:03d}.txt" for i in range(len(points))]

    with tempfile.TemporaryDirectory(prefix="argus7_xfoil_") as tmp:
        tmpdir = Path(tmp)
        write_selig_file(airfoil_name, tmpdir / "af.dat")
        script = build_script("af.dat", reynolds, points, dump_names,
                              n_panels=n_panels, ncrit=ncrit,
                              max_iter=max_iter, mach=mach)
        log = invoke_xfoil(script, tmpdir, timeout=timeout)
        segments = check_log(log, n_panels=n_panels, ncrit=ncrit,
                             n_points=len(points))

        results: list[XFoilResult] = []
        for (pt_mode, value), dump_name, segment in zip(points, dump_names, segments):
            converged = _RE_VISCAL_FAIL.search(segment) is None
            alpha_deg, cl_out, cm, cd, cdf, cdp = _forces_from_segment(segment)
            onset_u, onset_l = _onset_from_segment(segment)

            dump_path = tmpdir / dump_name
            if not dump_path.exists():
                raise XFoilError(
                    f"XFOIL did not write {dump_name}. The DUMP command did "
                    "not reach XFOIL in the state the script assumed.")
            surface, wake = parse_dump(dump_path)
            if converged and surface.shape[0] != int(n_panels):
                raise XFoilError(
                    f"DUMP has {surface.shape[0]} surface nodes but the "
                    f"airfoil is panelled with {n_panels}. The dump does not "
                    "belong to the requested paneling.")
            x_tr_u, x_tr_l = transition_from_dump(surface)

            if require_converged and not converged:
                raise XFoilError(
                    f"XFOIL did not converge at {pt_mode}={value:g}, "
                    f"Re={reynolds:.0f}, Ncrit={ncrit}, N={n_panels} "
                    f"(ITER={max_iter}). Raise max_iter, step towards the "
                    "point from a converged one, or pass "
                    "require_converged=False and read the .converged flag.")

            results.append(XFoilResult(
                airfoil=airfoil_name, reynolds=reynolds, mach=float(mach),
                ncrit=float(ncrit), n_panels=int(n_panels), mode=pt_mode,
                alpha_deg=alpha_deg, cl=cl_out, cd=cd, cdf=cdf, cdp=cdp,
                cm=cm, x_tr_upper=x_tr_u, x_tr_lower=x_tr_l,
                xtr_onset_upper=onset_u, xtr_onset_lower=onset_l,
                converged=converged, dump=surface, wake=wake, log=log))
    return results


def run_xfoil(airfoil_name: str, Re: float, cl: float | None = None,
              alpha: float | None = None, n_panels: int = DEFAULT_PANELS,
              ncrit: float = DEFAULT_NCRIT, timeout: float = 600.0,
              mach: float = 0.0, max_iter: int = DEFAULT_MAX_ITER,
              require_converged: bool = True) -> XFoilResult:
    """Run one viscous XFOIL point and return an :class:`XFoilResult`.

    Parameters
    ----------
    airfoil_name:
        Bare airfoil name, e.g. ``"fx63137"`` or ``"naca2412"``. A path or a
        ``.dat`` filename is refused -- see rule (a).
    Re:
        Chord Reynolds number.
    cl, alpha:
        Exactly one. ``cl`` runs XFOIL's fixed-C_L mode (what the ARGUS-7
        loiter survey uses); ``alpha`` is in degrees.
    n_panels:
        Panel nodes. Refused below :data:`MIN_PANELS` -- see rule (d).
    ncrit:
        e^N amplification factor. 9 is standard free air.
    require_converged:
        Default ``True``: a non-converged point raises rather than returning
        numbers that look fine. Pass ``False`` to inspect ``.converged``
        yourself (that is what :func:`polar_sweep` does).

    Notes
    -----
    ``x_tr_upper`` / ``x_tr_lower`` use the H < 2.0 fully-turbulent
    criterion, not XFOIL's e^N onset; both are on the result.
    """
    n_panels = _check_panels(n_panels)
    mode, values = _normalise_points(cl, alpha)
    if len(values) != 1:
        raise XFoilError("run_xfoil takes a single operating point; use polar_sweep().")
    return _run_points(airfoil_name, Re, mode, values, n_panels, ncrit,
                       max_iter, mach, timeout, require_converged)[0]


def polar_sweep(airfoil_name: str, Re: float,
                cl: Iterable[float] | None = None,
                alpha: Iterable[float] | None = None,
                n_panels: int = DEFAULT_PANELS, ncrit: float = DEFAULT_NCRIT,
                timeout: float = 600.0, mach: float = 0.0,
                max_iter: int = DEFAULT_MAX_ITER,
                require_converged: bool = False) -> list[XFoilResult]:
    """Sweep a list of C_L or alpha values, one :class:`XFoilResult` each.

    Each point is run in its own XFOIL session. That costs a re-load and a
    re-panel per point (tens of milliseconds) and buys two things worth more
    than the time: a point that fails cannot leave a corrupted
    boundary-layer state for the points after it, and every point carries a
    log that can be checked on its own.

    ``require_converged`` defaults to ``False`` here -- a sweep is expected
    to run into points that do not converge, and the caller should filter on
    ``.converged`` rather than lose the whole sweep to one bad point.
    """
    n_panels = _check_panels(n_panels)
    mode, values = _normalise_points(cl, alpha)
    results: list[XFoilResult] = []
    for value in values:
        results.extend(_run_points(airfoil_name, Re, mode, [value], n_panels,
                                   ncrit, max_iter, mach, timeout,
                                   require_converged))
    return results
