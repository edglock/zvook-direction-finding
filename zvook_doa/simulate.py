"""Synthetic 4-channel plane-wave signal generation."""

from __future__ import annotations

import argparse
import json

import numpy as np
from scipy.signal import chirp

from .config import ArrayConfig
from .geometry import make_4mic_geometry
from .utils import direction_to_unit, json_ready


def _base_signal(signal_type: str, duration_s: float, fs: int, rng: np.random.Generator) -> np.ndarray:
    n_samples = int(round(duration_s * fs))
    t = np.arange(n_samples, dtype=float) / fs
    if signal_type == "chirp":
        return chirp(t, f0=120.0, f1=3000.0, t1=max(duration_s, 1e-9), method="linear")
    if signal_type == "noise":
        return rng.standard_normal(n_samples)
    if signal_type == "tones":
        return (
            0.7 * np.sin(2.0 * np.pi * 180.0 * t)
            + 0.5 * np.sin(2.0 * np.pi * 320.0 * t)
            + 0.3 * np.sin(2.0 * np.pi * 720.0 * t)
        )
    raise ValueError("signal_type must be one of: chirp, noise, tones.")


def simulate_plane_wave(
    azimuth_deg: float,
    elevation_deg: float,
    duration_s: float,
    fs: int,
    mic_positions: np.ndarray,
    signal_type: str = "chirp",
    snr_db: float = 20.0,
    speed_of_sound: float = 343.0,
    seed: int = 1234,
) -> np.ndarray:
    """Generate synthetic multichannel data for a far-field plane wave."""

    rng = np.random.default_rng(seed)
    source = _base_signal(signal_type, duration_s, fs, rng)
    direction = direction_to_unit(azimuth_deg, elevation_deg)
    delays = -(np.asarray(mic_positions, dtype=float) @ direction) / speed_of_sound

    spectra = np.fft.rfft(source)
    freqs = np.fft.rfftfreq(source.size, d=1.0 / fs)
    channels = []
    for delay_s in delays:
        phase = np.exp(-1j * 2.0 * np.pi * freqs * delay_s)
        channels.append(np.fft.irfft(spectra * phase, n=source.size))
    frame = np.column_stack(channels)

    signal_power = float(np.mean(frame**2))
    noise_power = signal_power / (10.0 ** (snr_db / 10.0))
    noise = rng.standard_normal(frame.shape) * np.sqrt(noise_power)
    return frame + noise


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for synthetic signal generation and quick inspection."""

    parser = argparse.ArgumentParser()
    parser.add_argument("--az", type=float, default=60.0)
    parser.add_argument("--el", type=float, default=25.0)
    parser.add_argument("--duration-s", type=float, default=0.2)
    parser.add_argument("--snr-db", type=float, default=20.0)
    parser.add_argument("--signal-type", choices=["chirp", "noise", "tones"], default="chirp")
    args = parser.parse_args(argv)

    config = ArrayConfig()
    frame = simulate_plane_wave(
        azimuth_deg=args.az,
        elevation_deg=args.el,
        duration_s=args.duration_s,
        fs=config.fs,
        mic_positions=make_4mic_geometry(config),
        signal_type=args.signal_type,
        snr_db=args.snr_db,
        speed_of_sound=config.speed_of_sound,
    )
    print(json.dumps(json_ready({"shape": frame.shape, "rms": float(np.sqrt(np.mean(frame**2)))})))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
