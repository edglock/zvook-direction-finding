#!/usr/bin/env python
"""Run MVP synthetic validation and benchmark checks."""

from __future__ import annotations

import argparse
import json

from zvook_doa.cli import load_array_config
from zvook_doa.utils import json_ready
from zvook_doa.validation import benchmark_localizer, run_simulation_matrix


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/default_array_4mic.yaml")
    parser.add_argument("--snr-db", type=float, default=20.0)
    parser.add_argument("--max-error-deg", type=float, default=5.0)
    parser.add_argument("--benchmark-iterations", type=int, default=10)
    args = parser.parse_args()

    config = load_array_config(args.config)
    matrix = run_simulation_matrix(
        config,
        snr_db=args.snr_db,
        max_error_deg=args.max_error_deg,
    )
    benchmark = benchmark_localizer(
        config,
        iterations=args.benchmark_iterations,
        snr_db=args.snr_db,
    )
    payload = {
        "passed": bool(matrix["passed"]),
        "simulation": matrix,
        "benchmark": benchmark,
    }
    print(json.dumps(json_ready(payload), indent=2, ensure_ascii=False))
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
