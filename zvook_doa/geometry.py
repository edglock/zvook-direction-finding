"""Microphone geometry, direction grids, and delay lookup tables."""

from __future__ import annotations

import itertools
import math

import numpy as np

from .config import ArrayConfig
from .utils import direction_to_unit


def make_4mic_geometry(config: ArrayConfig) -> np.ndarray:
    """Return microphone coordinates with shape (4, 3), in meters."""

    a = config.triangle_side_m
    h = config.top_height_m
    sqrt3 = math.sqrt(3.0)
    return np.array(
        [
            [a / sqrt3, 0.0, 0.0],
            [-a / (2.0 * sqrt3), a / 2.0, 0.0],
            [-a / (2.0 * sqrt3), -a / 2.0, 0.0],
            [0.0, 0.0, h],
        ],
        dtype=float,
    )


def make_pairs(n_mics: int) -> list[tuple[int, int]]:
    """Return all microphone index pairs i < j."""

    if n_mics < 2:
        raise ValueError("At least two microphones are required.")
    return list(itertools.combinations(range(n_mics), 2))


def direction_grid(
    az_step_deg: float,
    el_step_deg: float,
    min_el_deg: float,
    max_el_deg: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Create an azimuth/elevation grid and corresponding unit vectors."""

    if az_step_deg <= 0.0 or el_step_deg <= 0.0:
        raise ValueError("Grid steps must be positive.")
    if min_el_deg > max_el_deg:
        raise ValueError("min_el_deg must be <= max_el_deg.")

    azimuths = np.arange(0.0, 360.0, az_step_deg, dtype=float)
    elevations = np.arange(
        min_el_deg,
        max_el_deg + el_step_deg * 0.5,
        el_step_deg,
        dtype=float,
    )
    elevations = elevations[elevations <= max_el_deg + 1e-9]

    az_grid, el_grid = np.meshgrid(azimuths, elevations, indexing="xy")
    az_flat = az_grid.ravel()
    el_flat = el_grid.ravel()
    directions = np.vstack(
        [direction_to_unit(az, el) for az, el in zip(az_flat, el_flat, strict=True)]
    )
    return directions, az_flat, el_flat


def delay_lut(
    mic_positions: np.ndarray,
    pairs: list[tuple[int, int]],
    directions: np.ndarray,
    c: float,
) -> np.ndarray:
    """Return TDOA lookup table with shape (n_directions, n_pairs)."""

    positions = np.asarray(mic_positions, dtype=float)
    dirs = np.asarray(directions, dtype=float)
    if positions.ndim != 2 or positions.shape[1] != 3:
        raise ValueError("mic_positions must have shape (n_mics, 3).")
    if dirs.ndim != 2 or dirs.shape[1] != 3:
        raise ValueError("directions must have shape (n_directions, 3).")
    if c <= 0.0:
        raise ValueError("Speed of sound must be positive.")

    pair_deltas = np.array([positions[i] - positions[j] for i, j in pairs], dtype=float)
    return -(dirs @ pair_deltas.T) / c
