#!/usr/bin/env python
"""Process a 4-channel WAV file and print localization JSON Lines."""

from __future__ import annotations

import argparse

from zvook_doa.realtime import run_wav_jsonl


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("wav_path")
    args = parser.parse_args()
    run_wav_jsonl(args.wav_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
