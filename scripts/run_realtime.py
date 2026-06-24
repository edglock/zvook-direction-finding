#!/usr/bin/env python
"""Run realtime 4-channel localization and print JSON Lines."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from zvook_doa.cli import load_array_config, load_calibration
from zvook_doa.realtime import run_realtime_jsonl


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", default=None)
    parser.add_argument("--config", default=None, help="Path to ArrayConfig YAML.")
    parser.add_argument("--calibration", default=None, help="Path to calibration JSON.")
    parser.add_argument("--raw", action="store_true", help="Run SRP-PHAT without detector/confidence output.")
    args = parser.parse_args()
    try:
        run_realtime_jsonl(
            config=load_array_config(args.config),
            device=args.device,
            calibration=load_calibration(args.calibration),
            raw=args.raw,
        )
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
