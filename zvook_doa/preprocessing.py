"""Frame-level audio preprocessing."""

from __future__ import annotations

import numpy as np


def remove_dc(frame: np.ndarray) -> np.ndarray:
    """Remove per-channel DC offset from a frame."""

    data = np.asarray(frame, dtype=float)
    return data - np.mean(data, axis=0, keepdims=True)


def apply_hann(frame: np.ndarray) -> np.ndarray:
    """Apply a Hann window to a multichannel frame."""

    data = np.asarray(frame, dtype=float)
    window = np.hanning(data.shape[0])[:, None]
    return data * window


def rfft_multichannel(frame: np.ndarray, fs: int) -> tuple[np.ndarray, np.ndarray]:
    """Compute one-frame real FFT for each channel."""

    data = np.asarray(frame, dtype=float)
    if data.ndim != 2:
        raise ValueError("frame must have shape (n_samples, n_channels).")
    freqs = np.fft.rfftfreq(data.shape[0], d=1.0 / fs)
    spectra = np.fft.rfft(data, axis=0)
    return spectra, freqs


def frequency_mask(freqs: np.ndarray, band_hz: tuple[float, float]) -> np.ndarray:
    """Return boolean mask for an inclusive frequency band."""

    low, high = band_hz
    if low < 0.0 or high <= low:
        raise ValueError("band_hz must be a positive (low, high) pair.")
    return (freqs >= low) & (freqs <= high)


def band_limited_spectra(
    spectra: np.ndarray,
    freqs: np.ndarray,
    band_hz: tuple[float, float],
) -> tuple[np.ndarray, np.ndarray]:
    """Select spectra and frequencies inside a frequency band."""

    mask = frequency_mask(freqs, band_hz)
    return spectra[mask], freqs[mask]
