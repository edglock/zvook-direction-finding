"""Small numeric helpers shared across modules."""

from __future__ import annotations

import math
from typing import Any

import numpy as np


def clamp(value: float, low: float, high: float) -> float:
    """Clamp a scalar value to an inclusive range."""

    return max(low, min(high, value))


def wrap_azimuth_deg(azimuth_deg: float) -> float:
    """Wrap azimuth to the [0, 360) interval."""

    return float(azimuth_deg % 360.0)


def direction_to_unit(azimuth_deg: float, elevation_deg: float) -> np.ndarray:
    """Convert azimuth/elevation in degrees to a 3-D unit vector."""

    az = math.radians(azimuth_deg)
    el = math.radians(elevation_deg)
    cos_el = math.cos(el)
    return np.array(
        [cos_el * math.cos(az), cos_el * math.sin(az), math.sin(el)],
        dtype=float,
    )


def unit_to_direction(vector: np.ndarray) -> tuple[float, float]:
    """Convert a 3-D vector to azimuth/elevation in degrees."""

    v = np.asarray(vector, dtype=float)
    norm = float(np.linalg.norm(v))
    if norm <= 0.0:
        raise ValueError("Cannot convert a zero vector to direction.")
    v = v / norm
    az = math.degrees(math.atan2(v[1], v[0])) % 360.0
    el = math.degrees(math.asin(clamp(float(v[2]), -1.0, 1.0)))
    return az, el


def angular_distance_deg(
    azimuth_a_deg: float,
    elevation_a_deg: float,
    azimuth_b_deg: float,
    elevation_b_deg: float,
) -> float:
    """Great-circle angular distance between two directions."""

    a = direction_to_unit(azimuth_a_deg, elevation_a_deg)
    b = direction_to_unit(azimuth_b_deg, elevation_b_deg)
    dot = clamp(float(np.dot(a, b)), -1.0, 1.0)
    return math.degrees(math.acos(dot))


def json_ready(value: Any) -> Any:
    """Convert numpy scalars/arrays and tuples into JSON-serializable values."""

    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, tuple):
        return [json_ready(item) for item in value]
    if isinstance(value, list):
        return [json_ready(item) for item in value]
    if isinstance(value, dict):
        return {key: json_ready(item) for key, item in value.items()}
    return value
