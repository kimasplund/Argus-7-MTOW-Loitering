"""Batched, GPU-resident NeuralFoil surrogate for the optimiser's inner loop.

WHY THIS EXISTS RATHER THAN JUST CALLING `neuralfoil`
-----------------------------------------------------
The reference `neuralfoil` package is a numpy implementation. Every call
re-normalises the airfoil, re-fits its 8-per-side Kulfan (CST) weights through
aerosandbox, re-reads the network parameters out of a dict, and evaluates six
512-wide layers on the CPU -- twice, because NeuralFoil evaluates the network
both forwards and alpha-flipped and averages the two to embed its symmetry
invariant. For a single polar that is fine. For an optimiser inner loop that
wants tens of thousands of (alpha, Re) cases per design iteration it is the
bottleneck.

This module keeps the same network and the same weights but:

  * fits the Kulfan parameters ONCE per airfoil, at construction;
  * uploads the weights to the GPU ONCE, at construction, and keeps them there;
  * evaluates the whole batch as dense matmuls in torch;
  * truncates the last layer to the 6 outputs we actually use (confidence, CL,
    CD, CM, Top_Xtr, Bot_Xtr) instead of computing all 198, which includes 192
    boundary-layer outputs this module does not expose;
  * chunks the batch so a large sweep cannot blow up device memory.

It is a PORT, not a re-derivation: tests/test_neural.py asserts agreement with
the reference `neuralfoil` package to float32 round-off. If the two ever
disagree beyond that, this module is wrong and the reference is right.

PRECISION
---------
The weights are float32, as NeuralFoil ships them, and the batch is evaluated
in float32. Agreement with the reference implementation (which promotes to
float64) is then ~1e-6 in CL -- three orders of magnitude tighter than
NeuralFoil's own error against XFOIL, so it costs nothing physical. That
holds only in true fp32: if a caller has globally enabled TF32 matmuls
(`torch.set_float32_matmul_precision("high"/"medium")` or
`torch.backends.cuda.matmul.allow_tf32 = True`) the agreement degrades to
~1e-3. This module does not mutate that global state; it is the caller's.

WHAT IT IS NOT
--------------
It is not XFOIL. NeuralFoil is a neural regression fitted to XFOIL runs, so it
inherits XFOIL's physics plus a training error of its own. `validate_against_xfoil`
exists to measure that gap at a handful of points and report it, not to hide it.
Every result also carries `analysis_confidence`; anything below
CONFIDENCE_WARN_THRESHOLD is flagged in `PolarResult.warnings` rather than
silently trusted.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Sequence

import numpy as np
import torch

# ---------------------------------------------------------------------------
# Module-level constants. Every assumed value is sourced here.
# ---------------------------------------------------------------------------

#: Below this analysis_confidence, NeuralFoil is extrapolating away from its
#: training distribution and its output must not be trusted without a check
#: against XFOIL. 0.9 is the threshold set by the Phase 2 module specification.
CONFIDENCE_WARN_THRESHOLD: float = 0.9

#: Largest of NeuralFoil's eight networks. Slowest per case and most accurate;
#: on the GPU the cost difference is irrelevant next to the kernel-launch
#: overhead, so there is no reason for the optimiser to use anything smaller.
DEFAULT_MODEL_SIZE: str = "xxxlarge"

#: Critical amplification factor for natural transition (the e^N method).
#: 9.0 is XFOIL's "average wind tunnel" default and is the value used by the
#: programme's verified XFOIL sequence (OPER / VPAR / N 9), so the two codes
#: are being asked the same question.
DEFAULT_N_CRIT: float = 9.0

#: Cases per device-side chunk. The widest activation is (chunk, 512) float32,
#: i.e. 134 MB at this chunk size, and two forward passes are live at once, so
#: the peak is a few hundred MB -- comfortable on a 12 GB card while still deep
#: enough to saturate it.
DEFAULT_MAX_CHUNK: int = 65_536

#: Number of inputs in NeuralFoil's input latent space. Asserted against the
#: loaded weights at construction rather than trusted.
_N_INPUTS: int = 25

#: Indices of the outputs this module exposes, in NeuralFoil's output vector.
_N_OUTPUTS_USED: int = 6  # confidence, CL, CD, CM, Top_Xtr, Bot_Xtr


# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PolarResult:
    """Aerodynamic coefficients for a batch of cases.

    All arrays share the broadcast shape of the (alpha, Re, ...) inputs, so
    scalar inputs give 0-d arrays and a (n_alpha, 1) x (1, n_Re) pair gives a
    (n_alpha, n_Re) grid.

    `low_confidence` is the elementwise mask analysis_confidence <
    CONFIDENCE_WARN_THRESHOLD, and `warnings` is non-empty whenever any element
    of that mask is set. Callers that care about trustworthiness should check
    one of those two rather than assuming the numbers are good.
    """

    CL: np.ndarray
    CD: np.ndarray
    CM: np.ndarray
    analysis_confidence: np.ndarray
    top_xtr: np.ndarray
    bot_xtr: np.ndarray
    low_confidence: np.ndarray
    warnings: tuple[str, ...] = ()
    model_size: str = DEFAULT_MODEL_SIZE
    device: str = "cpu"

    # Dict-style access, so code written against the reference neuralfoil
    # package's return value keeps working.
    def __getitem__(self, key: str) -> Any:
        aliases = {
            "Top_Xtr": "top_xtr",
            "Bot_Xtr": "bot_xtr",
        }
        return getattr(self, aliases.get(key, key))

    def keys(self) -> tuple[str, ...]:
        return ("analysis_confidence", "CL", "CD", "CM", "Top_Xtr", "Bot_Xtr")

    @property
    def confident(self) -> bool:
        """True when every case in the batch is at or above the threshold."""
        return not bool(np.any(self.low_confidence))


# ---------------------------------------------------------------------------
# The surrogate
# ---------------------------------------------------------------------------

class NeuralFoilSurrogate:
    """A single airfoil's NeuralFoil network, resident on one device.

    Construct once per (airfoil, model_size, device) and call `polar` many
    times. Construction does the expensive, geometry-dependent work: airfoil
    normalisation, the CST fit, and the upload of the network parameters.
    """

    def __init__(
        self,
        coords: np.ndarray,
        model_size: str = DEFAULT_MODEL_SIZE,
        device: str | torch.device | None = None,
        dtype: torch.dtype = torch.float32,
    ) -> None:
        import neuralfoil.main as _nfmain

        if model_size not in _nfmain._allowable_model_sizes:
            raise ValueError(
                f"Unknown model_size {model_size!r}. NeuralFoil provides "
                f"{sorted(_nfmain._allowable_model_sizes)}."
            )

        coords = np.asarray(coords, dtype=float)
        if coords.ndim != 2 or coords.shape[1] != 2:
            raise ValueError(
                f"coords must be an (N, 2) Selig-ordered array, got shape "
                f"{coords.shape}. argus7.cad.airfoil_coords.load_airfoil "
                f"returns exactly this."
            )

        self.model_size = model_size
        self.dtype = dtype
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = torch.device(device)

        # --- geometry: normalise and fit CST weights, once -----------------
        # This mirrors neuralfoil.get_aero_from_airfoil exactly, including the
        # quarter-chord moment correction that its normalisation implies. It
        # is the whole reason the reference implementation is slow per call,
        # and the whole reason this class is worth having.
        import aerosandbox as asb

        norm = asb.Airfoil(coordinates=coords).normalize(return_dict=True)
        kulfan = norm["airfoil"].to_kulfan_airfoil(
            n_weights_per_side=8, normalize_coordinates=False
        ).kulfan_parameters
        self._delta_alpha_deg = float(norm["rotation_angle"])
        self._scale = float(norm["scale_factor"])
        x_tr_le = float(norm["x_translation"])
        y_tr_le = float(norm["y_translation"])
        self._x_translation_qc = (
            -x_tr_le
            + 0.25 * (1.0 / self._scale * np.cos(np.deg2rad(self._delta_alpha_deg)))
            - 0.25
        )
        self._y_translation_qc = -y_tr_le + 0.25 * (
            1.0 / self._scale * np.sin(np.deg2rad(-self._delta_alpha_deg))
        )

        geom = np.concatenate([
            np.asarray(kulfan["upper_weights"], dtype=float).ravel(),
            np.asarray(kulfan["lower_weights"], dtype=float).ravel(),
            [float(kulfan["leading_edge_weight"])],
            [float(kulfan["TE_thickness"]) * 50.0],
        ])
        if geom.size != 18:
            raise ValueError(
                f"Expected 18 geometry inputs (8 upper + 8 lower CST weights, "
                f"LE weight, scaled TE thickness), got {geom.size}."
            )
        self._geom = torch.as_tensor(geom, dtype=dtype, device=self.device)

        # --- network parameters, uploaded once -----------------------------
        params = _nfmain._nn_parameters[model_size]
        layer_indices = sorted({int(k.split(".")[1]) for k in params})
        last = layer_indices[-1]
        self._layers: list[tuple[torch.Tensor, torch.Tensor]] = []
        for i in layer_indices:
            w = np.asarray(params[f"net.{i}.weight"])
            b = np.asarray(params[f"net.{i}.bias"])
            if i == last:
                # Only the first six outputs are exposed; the remaining 192 are
                # boundary-layer quantities. Truncating the final layer is
                # exact, not an approximation.
                w, b = w[:_N_OUTPUTS_USED], b[:_N_OUTPUTS_USED]
            self._layers.append((
                torch.as_tensor(w, dtype=dtype, device=self.device).contiguous(),
                torch.as_tensor(b, dtype=dtype, device=self.device).contiguous(),
            ))
        if self._layers[0][0].shape[1] != _N_INPUTS:
            raise ValueError(
                f"NeuralFoil's first layer expects {self._layers[0][0].shape[1]} "
                f"inputs but this module builds {_N_INPUTS}."
            )

        # --- training-distribution statistics, for analysis_confidence ------
        dist = _nfmain._scaled_input_distribution
        self._mean = torch.as_tensor(
            np.asarray(dist["mean_inputs_scaled"]).reshape(1, -1),
            dtype=dtype, device=self.device,
        )
        self._inv_cov = torch.as_tensor(
            np.asarray(dist["inv_cov_inputs_scaled"]), dtype=dtype, device=self.device
        )
        self._n_inputs_dist = int(dist["N_inputs"])

    # -- introspection ----------------------------------------------------

    @property
    def weights(self) -> list[torch.Tensor]:
        """Every resident parameter tensor, weights and biases interleaved."""
        return [t for layer in self._layers for t in layer]

    def synchronize(self) -> None:
        """Block until queued device work has finished (no-op on CPU).

        Needed for honest timing: torch's CUDA calls are asynchronous, so a
        benchmark that does not synchronize measures the launch, not the work.
        """
        if self.device.type == "cuda":
            torch.cuda.synchronize(self.device)

    # -- evaluation --------------------------------------------------------

    def polar(
        self,
        alpha: Any,
        Re: Any,
        n_crit: Any = DEFAULT_N_CRIT,
        xtr_upper: Any = 1.0,
        xtr_lower: Any = 1.0,
        max_chunk: int = DEFAULT_MAX_CHUNK,
    ) -> PolarResult:
        """Evaluate a batch of cases.

        alpha (deg), Re, n_crit, xtr_upper and xtr_lower are broadcast against
        one another with numpy's rules; the result arrays take the broadcast
        shape. A mismatch that numpy cannot broadcast raises ValueError.
        """
        if max_chunk < 1:
            raise ValueError(f"max_chunk must be >= 1, got {max_chunk}")

        arrays = [np.asarray(v, dtype=float)
                  for v in (alpha, Re, n_crit, xtr_upper, xtr_lower)]
        try:
            shape = np.broadcast_shapes(*(a.shape for a in arrays))
        except ValueError as e:
            raise ValueError(
                f"alpha, Re, n_crit, xtr_upper and xtr_lower must broadcast "
                f"together; got shapes {[a.shape for a in arrays]}."
            ) from e
        flat = [np.broadcast_to(a, shape).reshape(-1) for a in arrays]
        n_cases = int(np.prod(shape)) if shape else 1

        if np.any(flat[1] <= 0.0):
            raise ValueError("Re must be strictly positive.")

        out = np.empty((n_cases, _N_OUTPUTS_USED), dtype=np.float64)
        with torch.inference_mode():
            for lo in range(0, n_cases, max_chunk):
                hi = min(lo + max_chunk, n_cases)
                x = self._build_inputs(
                    flat[0][lo:hi], flat[1][lo:hi], flat[2][lo:hi],
                    flat[3][lo:hi], flat[4][lo:hi],
                )
                out[lo:hi] = self._forward(x).to(torch.float64).cpu().numpy()

        confidence = out[:, 0]
        CL = out[:, 1] / 2.0
        CD = np.exp((out[:, 2] - 2.0) * 2.0)
        CM = out[:, 3] / 20.0
        # Moment correction implied by the normalisation applied at
        # construction (see neuralfoil.get_aero_from_airfoil).
        CM = CM - CL * self._x_translation_qc + CD * self._y_translation_qc
        top_xtr = np.clip(out[:, 4], 0.0, 1.0)
        bot_xtr = np.clip(out[:, 5], 0.0, 1.0)

        low = confidence < CONFIDENCE_WARN_THRESHOLD
        warnings: list[str] = []
        if bool(np.any(low)):
            n_low = int(np.count_nonzero(low))
            warnings.append(
                f"low analysis_confidence: {n_low} of {n_cases} case(s) below "
                f"{CONFIDENCE_WARN_THRESHOLD} (min {confidence.min():.3f}). "
                f"NeuralFoil is extrapolating outside its training "
                f"distribution here; check these points against XFOIL before "
                f"trusting them."
            )

        def shaped(a: np.ndarray) -> np.ndarray:
            return a.reshape(shape) if shape else a.reshape(())

        return PolarResult(
            CL=shaped(CL),
            CD=shaped(CD),
            CM=shaped(CM),
            analysis_confidence=shaped(confidence),
            top_xtr=shaped(top_xtr),
            bot_xtr=shaped(bot_xtr),
            low_confidence=shaped(low),
            warnings=tuple(warnings),
            model_size=self.model_size,
            device=str(self.device),
        )

    # -- internals ---------------------------------------------------------

    def _build_inputs(
        self,
        alpha: np.ndarray,
        Re: np.ndarray,
        n_crit: np.ndarray,
        xtr_upper: np.ndarray,
        xtr_lower: np.ndarray,
    ) -> torch.Tensor:
        """Assemble NeuralFoil's 25-column input latent space for a chunk."""
        n = alpha.size
        # np.array(..., order="C") rather than asarray: broadcast_to hands us
        # read-only views, and torch.as_tensor on one warns about undefined
        # behaviour on write.
        t = lambda a: torch.as_tensor(  # noqa: E731
            np.array(a, dtype=np.float64, order="C"),
            dtype=self.dtype, device=self.device)

        # The airfoil was rotated and rescaled during normalisation, so the
        # network must be asked about the rotated alpha and the rescaled Re.
        a_rad = t(np.deg2rad(alpha + self._delta_alpha_deg))
        re_net = t(Re / self._scale)

        x = torch.empty((n, _N_INPUTS), dtype=self.dtype, device=self.device)
        x[:, :18] = self._geom.unsqueeze(0)
        x[:, 18] = torch.sin(2.0 * a_rad)
        x[:, 19] = torch.cos(a_rad)
        x[:, 20] = 1.0 - torch.cos(a_rad) ** 2
        x[:, 21] = (torch.log(re_net) - 12.5) / 3.5
        x[:, 22] = (t(n_crit) - 9.0) / 4.5
        x[:, 23] = t(xtr_upper)
        x[:, 24] = t(xtr_lower)
        return x

    def _net(self, x: torch.Tensor) -> torch.Tensor:
        for i, (w, b) in enumerate(self._layers):
            x = torch.addmm(b, x, w.t())
            if i != len(self._layers) - 1:
                x = torch.nn.functional.silu(x)  # NeuralFoil's swish, beta=1
        return x

    def _mahalanobis(self, x: torch.Tensor) -> torch.Tensor:
        d = x - self._mean
        return torch.sum((d @ self._inv_cov) * d, dim=1)

    def _forward(self, x: torch.Tensor) -> torch.Tensor:
        """One fused NeuralFoil evaluation: forward pass + alpha-flipped pass.

        NeuralFoil was trained to be evaluated both ways and averaged, which
        embeds the "symmetry across alpha" invariant. Skipping the flipped pass
        would halve the cost and change the answer, so it is not optional.
        """
        scale_conf = 1.0 / (2.0 * self._n_inputs_dist)

        y = self._net(x)
        y[:, 0] = y[:, 0] - self._mahalanobis(x) * scale_conf

        xf = x.clone()
        xf[:, :8] = x[:, 8:16] * -1.0     # lower CST weights become upper
        xf[:, 8:16] = x[:, :8] * -1.0     # ... and vice versa
        xf[:, 16] = -1.0 * x[:, 16]       # LE weight
        xf[:, 18] = -1.0 * x[:, 18]       # sin(2 alpha)
        xf[:, 23] = x[:, 24]              # xtr_upper <-> xtr_lower
        xf[:, 24] = x[:, 23]

        yf = self._net(xf)
        yf[:, 0] = yf[:, 0] - self._mahalanobis(xf) * scale_conf

        y_un = yf.clone()
        y_un[:, 1] = yf[:, 1] * -1.0      # CL
        y_un[:, 3] = yf[:, 3] * -1.0      # CM
        y_un[:, 4] = yf[:, 5]             # Top_Xtr <-> Bot_Xtr
        y_un[:, 5] = yf[:, 4]

        fused = (y + y_un) / 2.0
        fused[:, 0] = torch.sigmoid(fused[:, 0])
        return fused


# ---------------------------------------------------------------------------
# Convenience API
# ---------------------------------------------------------------------------

_CACHE: dict[tuple, NeuralFoilSurrogate] = {}

#: Cache bound. An optimiser that perturbs the section every iteration would
#: otherwise accumulate one full set of resident GPU weights per geometry --
#: 5.4 MB of parameters for xxxlarge, so a few thousand iterations would fill
#: the card. Oldest entry is evicted first.
_CACHE_MAX_ENTRIES: int = 8


def get_surrogate(
    coords: np.ndarray,
    model_size: str = DEFAULT_MODEL_SIZE,
    device: str | torch.device | None = None,
    dtype: torch.dtype = torch.float32,
) -> NeuralFoilSurrogate:
    """Cached surrogate lookup.

    The optimiser's inner loop calls `polar()` with the same coordinates over
    and over; without this cache each call would repeat the CST fit and the
    weight upload, which is precisely the cost this module exists to remove.
    """
    coords = np.asarray(coords, dtype=float)
    # Resolve the device BEFORE it enters the key. `None`, "cuda" and
    # torch.device("cuda") all name the same device, and keying on the raw
    # argument gave each of them its own resident copy of the weights --
    # which is precisely the duplication this cache exists to prevent.
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
    device = torch.device(device)
    key = (coords.tobytes(), coords.shape, model_size, str(device), str(dtype))
    s = _CACHE.get(key)
    if s is None:
        s = NeuralFoilSurrogate(coords, model_size=model_size,
                                device=device, dtype=dtype)
        while len(_CACHE) >= _CACHE_MAX_ENTRIES:
            _CACHE.pop(next(iter(_CACHE)))
        _CACHE[key] = s
    return s


def polar(
    coords: np.ndarray,
    alpha: Any,
    Re: Any,
    model_size: str = DEFAULT_MODEL_SIZE,
    n_crit: Any = DEFAULT_N_CRIT,
    xtr_upper: Any = 1.0,
    xtr_lower: Any = 1.0,
    device: str | torch.device | None = None,
    max_chunk: int = DEFAULT_MAX_CHUNK,
) -> PolarResult:
    """Evaluate a NeuralFoil polar for `coords` over broadcast alpha and Re.

    Args:
        coords: (N, 2) Selig-ordered airfoil coordinates, as returned by
            argus7.cad.airfoil_coords.load_airfoil.
        alpha: angle(s) of attack, degrees. Scalar or array-like.
        Re: Reynolds number(s). Scalar or array-like, broadcast with alpha.
        model_size: one of NeuralFoil's eight networks; see DEFAULT_MODEL_SIZE.
        n_crit: e^N transition amplification factor; see DEFAULT_N_CRIT.
        device: 'cuda', 'cpu', or None to pick CUDA when it is available.

    Returns:
        PolarResult. Check `.warnings` / `.low_confidence` before trusting it.
    """
    return get_surrogate(coords, model_size=model_size,
                         device=device).polar(
        alpha=alpha, Re=Re, n_crit=n_crit,
        xtr_upper=xtr_upper, xtr_lower=xtr_lower, max_chunk=max_chunk,
    )


# ---------------------------------------------------------------------------
# XFOIL cross-check
# ---------------------------------------------------------------------------

#: Panel count for the XFOIL cross-check. Rule (d) of the programme's XFOIL
#: findings: below ~280 panels XFOIL puts transition several percent of chord
#: too far forward with no warning at all, which would make this comparison
#: measure the panelling rather than the two methods.
XFOIL_PANELS: int = 300


def _default_xfoil_runner(
    airfoil_name: str,
    alphas: Sequence[float],
    Re: float,
    n_crit: float,
    n_panels: int,
) -> list[dict]:
    """Adapter onto argus7.aero.xfoil_driver.polar_sweep.

    The driver owns the hard-won XFOIL invocation rules (Selig temp file from
    the project loader, no PLOP, two blank lines out of PPAR, panel-count
    floor, log assertions). This module deliberately does not duplicate any of
    them -- it only translates the driver's XFoilResult into the plain dicts
    this comparison works in.

    require_converged=False on purpose: XFOIL does not converge at every alpha
    on every section, and a sweep that raises on the first bad point tells you
    nothing about the good ones. Convergence is reported per point instead.
    """
    try:
        from argus7.aero import xfoil_driver
    except ImportError as e:  # pragma: no cover - depends on sibling module
        raise RuntimeError(
            "validate_against_xfoil needs argus7.aero.xfoil_driver, which is "
            "not importable. Pass an explicit `runner=` callable instead."
        ) from e

    results = xfoil_driver.polar_sweep(
        airfoil_name, Re=Re, alpha=list(alphas), n_panels=n_panels,
        ncrit=n_crit, require_converged=False,
    )
    return [
        {
            "CL": float(r.cl),
            "CD": float(r.cd),
            "CM": float(r.cm),
            "converged": bool(r.converged),
            "x_tr_upper": float(r.x_tr_upper),
        }
        for r in results
    ]


def validate_against_xfoil(
    airfoil_name: str = "fx63137",
    alpha: Sequence[float] = (0.0, 2.0, 4.0, 6.0),
    Re: float = 1.0e6,
    model_size: str = DEFAULT_MODEL_SIZE,
    n_crit: float = DEFAULT_N_CRIT,
    n_panels: int = XFOIL_PANELS,
    coords: np.ndarray | None = None,
    runner: Callable[..., list[dict]] | None = None,
    device: str | torch.device | None = None,
) -> list[dict]:
    """Compare this surrogate against XFOIL at a handful of points.

    This measures a DISCREPANCY BETWEEN TWO DIFFERENT METHODS, and that is all
    it measures. NeuralFoil is a neural regression fitted to XFOIL runs, so a
    few percent of CD spread is expected and is not evidence that either code
    is broken. Nothing here asserts agreement; the caller chooses a band and a
    human should read the numbers.

    Both codes are given the same section: `coords` defaults to
    argus7.cad.airfoil_coords.load_airfoil(airfoil_name), which is also what
    the XFOIL driver writes into its Selig temp file. Passing `coords`
    explicitly (e.g. a perturbed section) while the driver still resolves
    `airfoil_name` from the data directory would compare two different
    airfoils, so do that only deliberately.

    Args:
        airfoil_name: bare name, e.g. "fx63137". Not a path -- see the XFOIL
            driver's rule (a).
        alpha: angles of attack in degrees.
        Re: chord Reynolds number, the same for both codes.
        runner: callable(airfoil_name, alphas, Re, n_crit, n_panels) returning
            one dict per alpha with "CL", "CD", "CM" and "converged". A row
            that omits "converged" is recorded as NOT converged.
            Defaults to an adapter onto argus7.aero.xfoil_driver.polar_sweep.

    Returns:
        One dict per alpha with both codes' CL/CD/CM, the signed deltas
        (neural minus xfoil; dCD_rel is relative to the XFOIL value),
        NeuralFoil's analysis_confidence, whether that fell below
        CONFIDENCE_WARN_THRESHOLD, and whether XFOIL converged at that point.
    """
    if coords is None:
        from argus7.cad.airfoil_coords import load_airfoil
        coords = load_airfoil(airfoil_name)

    run = runner if runner is not None else _default_xfoil_runner
    alphas = [float(a) for a in np.atleast_1d(np.asarray(alpha, dtype=float))]

    nf = polar(coords, alpha=alphas, Re=Re, model_size=model_size,
               n_crit=n_crit, device=device)
    xf_rows = run(airfoil_name, alphas, Re, n_crit, n_panels)
    if len(xf_rows) != len(alphas):
        raise RuntimeError(
            f"XFOIL runner returned {len(xf_rows)} points for {len(alphas)} "
            f"requested alphas."
        )

    rows: list[dict] = []
    for i, a in enumerate(alphas):
        xf = xf_rows[i]
        cl_n, cd_n, cm_n = float(nf.CL[i]), float(nf.CD[i]), float(nf.CM[i])
        cl_x, cd_x, cm_x = float(xf["CL"]), float(xf["CD"]), float(xf["CM"])
        rows.append({
            "alpha": a,
            "Re": float(Re),
            "CL_neural": cl_n, "CL_xfoil": cl_x, "dCL": cl_n - cl_x,
            "CD_neural": cd_n, "CD_xfoil": cd_x, "dCD": cd_n - cd_x,
            "dCD_rel": (cd_n - cd_x) / cd_x if cd_x != 0.0 else float("nan"),
            "CM_neural": cm_n, "CM_xfoil": cm_x, "dCM": cm_n - cm_x,
            "analysis_confidence": float(nf.analysis_confidence[i]),
            "low_confidence": bool(nf.low_confidence[i]),
            # A runner that does not report convergence is recorded as NOT
            # converged. XFOIL emits perfectly plausible CL/CD/Cm for a point
            # that never converged -- that is the whole point of the
            # programme's XFOIL rule (e) -- so "no information" must not
            # default to "trust it".
            "converged": bool(xf.get("converged", False)),
        })
    return rows
