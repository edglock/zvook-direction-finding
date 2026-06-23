"""Channel calibration helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

import numpy as np


@dataclass(slots=True)
class Calibration:
    """Per-channel delay and gain calibration."""

    channel_delay_samples: np.ndarray
    channel_gain: np.ndarray

    def __post_init__(self) -> None:
        self.channel_delay_samples = np.asarray(self.channel_delay_samples, dtype=float)
        self.channel_gain = np.asarray(self.channel_gain, dtype=float)
        if self.channel_delay_samples.shape != self.channel_gain.shape:
            raise ValueError("Delay and gain arrays must have the same shape.")
        if self.channel_delay_samples.ndim != 1:
            raise ValueError("Calibration arrays must be one-dimensional.")

    @classmethod
    def from_json(cls, path: str | Path) -> "Calibration":
        """Load calibration values from JSON."""

        with Path(path).open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        return cls(
            channel_delay_samples=np.asarray(data["channel_delay_samples"], dtype=float),
            channel_gain=np.asarray(data["channel_gain"], dtype=float),
        )


def apply_calibration(frame: np.ndarray, calibration: Calibration, fs: int) -> np.ndarray:
    """Apply gain and fractional-delay compensation to a frame.

    Positive channel_delay_samples means the channel is delayed and should be
    advanced during compensation.
    """

    data = np.asarray(frame, dtype=float)
    if data.ndim != 2:
        raise ValueError("frame must have shape (n_samples, n_channels).")
    if data.shape[1] != calibration.channel_gain.shape[0]:
        raise ValueError("Calibration channel count does not match frame.")
    if fs <= 0:
        raise ValueError("fs must be positive.")

    gains = np.where(np.abs(calibration.channel_gain) < 1e-12, 1.0, calibration.channel_gain)
    compensated = data / gains[None, :]

    freqs_cycles_per_sample = np.fft.rfftfreq(compensated.shape[0], d=1.0)
    spectra = np.fft.rfft(compensated, axis=0)
    phase = np.exp(
        1j
        * 2.0
        * np.pi
        * freqs_cycles_per_sample[:, None]
        * calibration.channel_delay_samples[None, :]
    )
    shifted = np.fft.irfft(spectra * phase, n=compensated.shape[0], axis=0)
    return shifted.real
