#!/usr/bin/env python
"""Process a 4-channel WAV/FLAC file and print localization JSON Lines."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from zvook_doa.cli import load_array_config, load_calibration
from zvook_doa.realtime import run_wav_jsonl


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("audio_path")
    parser.add_argument("--config", default=None, help="Path to ArrayConfig YAML.")
    parser.add_argument("--calibration", default=None, help="Path to calibration JSON.")
    args = parser.parse_args()
    try:
        run_wav_jsonl(
            args.audio_path,
            config=load_array_config(args.config),
            calibration=load_calibration(args.calibration),
        )
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
