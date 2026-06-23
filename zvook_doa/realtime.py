"""Realtime frame pipeline and JSON Lines output."""

from __future__ import annotations

from collections import deque
import json
import queue
import sys
import time

import numpy as np

from .audio_io import iter_frames, read_wav_4ch, require_sounddevice
from .config import ArrayConfig
from .detector import DroneDetector
from .geometry import make_4mic_geometry
from .preprocessing import apply_hann, remove_dc, rfft_multichannel
from .srp_phat import SRPPHATLocalizer
from .tracker import DirectionTracker
from .utils import json_ready


def process_frame(
    frame: np.ndarray,
    timestamp: float,
    config: ArrayConfig,
    detector: DroneDetector,
    localizer: SRPPHATLocalizer,
    tracker: DirectionTracker,
) -> dict[str, object]:
    """Run detector, localizer, and tracker for one frame."""

    spectra, freqs = rfft_multichannel(apply_hann(remove_dc(frame)), config.fs)
    detector_result = detector.predict(frame, freqs=freqs, spectra=spectra)
    result = localizer.locate(frame, detector_result=detector_result)
    tracked = tracker.update(
        float(result["azimuth_deg"]),
        float(result["elevation_deg"]),
        float(result["confidence"]),
        timestamp,
    )
    result["azimuth_deg"] = tracked["azimuth_deg"]
    result["elevation_deg"] = tracked["elevation_deg"]
    result["status"] = tracked["status"] if result["status"] == "ok" else result["status"]
    return {
        "timestamp": timestamp,
        "p_drone": detector_result["p_drone"],
        **result,
    }


def run_wav_jsonl(path: str, config: ArrayConfig | None = None) -> None:
    """Process a 4-channel WAV file and print JSON Lines."""

    config = config or ArrayConfig()
    audio, fs = read_wav_4ch(path)
    if fs != config.fs:
        raise ValueError(f"WAV fs={fs} does not match config fs={config.fs}.")
    detector = DroneDetector(fs=config.fs)
    localizer = SRPPHATLocalizer(config, make_4mic_geometry(config))
    tracker = DirectionTracker()
    for start, frame in iter_frames(audio, config.frame_samples, config.hop_samples):
        timestamp = start / config.fs
        record = process_frame(frame, timestamp, config, detector, localizer, tracker)
        print(json.dumps(json_ready(record), ensure_ascii=False), flush=True)


def run_realtime_jsonl(config: ArrayConfig | None = None, device: int | str | None = None) -> None:
    """Read realtime audio via sounddevice and print JSON Lines."""

    config = config or ArrayConfig()
    sd = require_sounddevice()
    detector = DroneDetector(fs=config.fs)
    localizer = SRPPHATLocalizer(config, make_4mic_geometry(config))
    tracker = DirectionTracker()

    block_queue: queue.Queue[np.ndarray] = queue.Queue(maxsize=32)

    def callback(indata, frames, time_info, status) -> None:  # type: ignore[no-untyped-def]
        if status:
            print(status, file=sys.stderr)
        try:
            block_queue.put_nowait(np.asarray(indata, dtype=float).copy())
        except queue.Full:
            pass

    ring: deque[np.ndarray] = deque()
    buffered = 0
    with sd.InputStream(
        samplerate=config.fs,
        channels=4,
        blocksize=config.hop_samples,
        dtype="float64",
        device=device,
        callback=callback,
    ):
        while True:
            block = block_queue.get()
            ring.append(block)
            buffered += block.shape[0]
            while buffered >= config.frame_samples:
                joined = np.vstack(list(ring))
                frame = joined[: config.frame_samples]
                timestamp = time.time()
                record = process_frame(frame, timestamp, config, detector, localizer, tracker)
                print(json.dumps(json_ready(record), ensure_ascii=False), flush=True)
                keep = joined[config.hop_samples :]
                ring.clear()
                if keep.size:
                    ring.append(keep)
                buffered = keep.shape[0]
