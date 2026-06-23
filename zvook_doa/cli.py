"""Shared CLI loading helpers."""

from __future__ import annotations

from pathlib import Path

from .calibration import Calibration
from .config import ArrayConfig


def load_array_config(path: str | Path | None = None) -> ArrayConfig:
    """Load ArrayConfig from YAML or return defaults when path is omitted."""

    if path is None:
        return ArrayConfig()
    return ArrayConfig.from_yaml(path)


def load_calibration(path: str | Path | None = None) -> Calibration | None:
    """Load optional channel calibration from JSON."""

    if path is None:
        return None
    return Calibration.from_json(path)
