#!/usr/bin/env python
"""Run realtime 4-channel localization and print JSON Lines."""

from __future__ import annotations

import argparse

from zvook_doa.realtime import run_realtime_jsonl


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", default=None)
    args = parser.parse_args()
    run_realtime_jsonl(device=args.device)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
