"""Configuration loading for the acoustic array."""

from __future__ import annotations

from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any

import yaml


@dataclass(slots=True)
class ArrayConfig:
    """Runtime configuration for the 4-microphone array."""

    fs: int = 48000
    speed_of_sound: float = 343.0
    triangle_side_m: float = 0.25
    top_height_m: float = 0.20
    base_height_m: float = 0.0
    lower_angles_deg: tuple[float, float, float] = (0.0, 120.0, -120.0)
    top_mic_anchor: str = "center"
    frame_duration_s: float = 0.2
    hop_duration_s: float = 0.05
    detection_band_hz: tuple[float, float] = (50.0, 2000.0)
    coarse_band_hz: tuple[float, float] = (150.0, 650.0)
    refine_band_hz: tuple[float, float] = (150.0, 2000.0)
    coarse_az_step_deg: float = 3.0
    coarse_el_step_deg: float = 3.0
    refine_radius_deg: float = 15.0
    refine_step_deg: float = 0.5
    min_elevation_deg: float = 0.0
    max_elevation_deg: float = 90.0

    @property
    def frame_samples(self) -> int:
        """Number of samples in one processing frame."""

        return int(round(self.fs * self.frame_duration_s))

    @property
    def hop_samples(self) -> int:
        """Number of samples between consecutive frame starts."""

        return int(round(self.fs * self.hop_duration_s))

    @classmethod
    def from_yaml(cls, path: str | Path) -> "ArrayConfig":
        """Load configuration values from a YAML file."""

        with Path(path).open("r", encoding="utf-8") as handle:
            raw = yaml.safe_load(handle) or {}
        if not isinstance(raw, dict):
            raise ValueError("Configuration YAML must contain a mapping.")

        valid_names = {field.name for field in fields(cls)}
        unknown = set(raw) - valid_names
        if unknown:
            raise ValueError(f"Unknown ArrayConfig fields: {sorted(unknown)}")

        data: dict[str, Any] = {}
        tuple_fields = {
            "detection_band_hz": 2,
            "coarse_band_hz": 2,
            "refine_band_hz": 2,
            "lower_angles_deg": 3,
        }
        for key, value in raw.items():
            if key in tuple_fields:
                expected_len = tuple_fields[key]
                if not isinstance(value, (list, tuple)) or len(value) != expected_len:
                    raise ValueError(f"{key} must contain exactly {expected_len} numbers.")
                data[key] = tuple(float(item) for item in value)
            else:
                data[key] = value
        return cls(**data)
