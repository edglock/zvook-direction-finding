#!/usr/bin/env python
"""Generate a synthetic frame and run SRP-PHAT localization."""

from __future__ import annotations

import argparse
import json

from zvook_doa.cli import load_array_config
from zvook_doa.geometry import make_4mic_geometry
from zvook_doa.simulate import simulate_plane_wave
from zvook_doa.srp_phat import SRPPHATLocalizer
from zvook_doa.utils import angular_distance_deg, json_ready


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--az", type=float, default=60.0)
    parser.add_argument("--el", type=float, default=25.0)
    parser.add_argument("--snr-db", type=float, default=20.0)
    parser.add_argument("--signal-type", choices=["chirp", "noise", "tones"], default="chirp")
    parser.add_argument("--config", default=None, help="Path to ArrayConfig YAML.")
    args = parser.parse_args()

    config = load_array_config(args.config)
    positions = make_4mic_geometry(config)
    frame = simulate_plane_wave(
        azimuth_deg=args.az,
        elevation_deg=args.el,
        duration_s=config.frame_duration_s,
        fs=config.fs,
        mic_positions=positions,
        signal_type=args.signal_type,
        snr_db=args.snr_db,
        speed_of_sound=config.speed_of_sound,
    )
    result = SRPPHATLocalizer(config, positions).locate(frame)
    result["true_azimuth_deg"] = args.az
    result["true_elevation_deg"] = args.el
    result["angular_error_deg"] = angular_distance_deg(
        args.az,
        args.el,
        float(result["azimuth_deg"]),
        float(result["elevation_deg"]),
    )
    print(json.dumps(json_ready(result), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
