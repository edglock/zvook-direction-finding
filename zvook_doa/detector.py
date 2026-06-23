"""Drone detector interface and lightweight energy-based stub."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .preprocessing import frequency_mask, rfft_multichannel


@dataclass(slots=True)
class DroneDetector:
    """Replaceable detector facade.

    The MVP uses an energy-ratio heuristic. onnx_model_path is reserved for a
    future ONNX Runtime backend without making onnxruntime a required dependency.
    """

    fs: int = 48000
    band_hz: tuple[float, float] = (80.0, 2000.0)
    onnx_model_path: str | None = None
    _onnx_session: object | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        self._onnx_session = None
        if self.onnx_model_path is not None:
            try:
                import onnxruntime as ort  # type: ignore
            except ImportError as exc:
                raise RuntimeError(
                    "onnxruntime is required when onnx_model_path is provided."
                ) from exc
            self._onnx_session = ort.InferenceSession(self.onnx_model_path)

    def predict(
        self,
        frame: np.ndarray,
        freqs: np.ndarray | None = None,
        spectra: np.ndarray | None = None,
    ) -> dict[str, float | np.ndarray | None]:
        """Estimate drone probability and optional frequency weights."""

        if self._onnx_session is not None:
            raise NotImplementedError("ONNX detector backend is not implemented yet.")

        if spectra is None or freqs is None:
            spectra, freqs = rfft_multichannel(frame, self.fs)

        power = np.mean(np.abs(spectra) ** 2, axis=1)
        band = frequency_mask(freqs, self.band_hz)
        total = float(np.sum(power) + 1e-12)
        band_energy = float(np.sum(power[band]) + 1e-12)
        ratio = band_energy / total

        selected_power = power[band]
        weights = np.zeros_like(freqs, dtype=float)
        if selected_power.size:
            norm = float(np.max(selected_power) + 1e-12)
            weights[band] = np.sqrt(selected_power / norm)

        p_drone = float(np.clip((ratio - 0.15) / 0.65, 0.0, 1.0))
        return {"p_drone": p_drone, "frequency_weights": weights}
