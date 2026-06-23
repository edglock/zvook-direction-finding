#!/usr/bin/env python
"""Process a 4-channel WAV file and print localization JSON Lines."""

from __future__ import annotations

import argparse

from zvook_doa.cli import load_array_config, load_calibration
from zvook_doa.realtime import run_wav_jsonl


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("wav_path")
    parser.add_argument("--config", default=None, help="Path to ArrayConfig YAML.")
    parser.add_argument("--calibration", default=None, help="Path to calibration JSON.")
    args = parser.parse_args()
    run_wav_jsonl(
        args.wav_path,
        config=load_array_config(args.config),
        calibration=load_calibration(args.calibration),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
