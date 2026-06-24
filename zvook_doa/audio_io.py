"""Audio IO helpers for WAV and optional realtime input."""

from __future__ import annotations

from collections.abc import Iterator

import numpy as np
import soundfile as sf


def read_audio_4ch(path: str) -> tuple[np.ndarray, int]:
    """Read a 4-channel audio file supported by soundfile, including WAV/FLAC."""

    data, fs = sf.read(path, always_2d=True, dtype="float64")
    if data.shape[1] != 4:
        raise ValueError(f"Expected 4-channel audio, got {data.shape[1]} channels.")
    return data, int(fs)


def read_wav_4ch(path: str) -> tuple[np.ndarray, int]:
    """Read a 4-channel audio file. Kept for backward-compatible imports."""

    return read_audio_4ch(path)


def iter_frames(audio: np.ndarray, frame_samples: int, hop_samples: int) -> Iterator[tuple[int, np.ndarray]]:
    """Yield overlapping frames as (start_sample, frame)."""

    if frame_samples <= 0 or hop_samples <= 0:
        raise ValueError("frame_samples and hop_samples must be positive.")
    for start in range(0, audio.shape[0] - frame_samples + 1, hop_samples):
        yield start, audio[start : start + frame_samples]


def require_sounddevice():
    """Import sounddevice or raise a clear runtime error."""

    try:
        import sounddevice as sd  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "Realtime input requires optional dependency 'sounddevice'. "
            "Install with: pip install .[realtime]"
        ) from exc
    return sd
