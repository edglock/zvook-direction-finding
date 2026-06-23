"""Direction tracker with unit-vector smoothing."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .utils import direction_to_unit, unit_to_direction


@dataclass(slots=True)
class DirectionTracker:
    """Simple tracker that smooths direction vectors instead of raw azimuth."""

    min_update_confidence: float = 0.35
    smoothing: float = 0.35
    unit_vector: np.ndarray | None = None
    last_timestamp: float | None = None
    track_confidence: float = 0.0

    def update(
        self,
        measurement_az_deg: float,
        measurement_el_deg: float,
        confidence: float,
        timestamp: float,
    ) -> dict[str, float | str]:
        """Update the track with one direction measurement."""

        measurement = direction_to_unit(measurement_az_deg, measurement_el_deg)
        if self.unit_vector is None:
            self.unit_vector = measurement
            self.last_timestamp = timestamp
            self.track_confidence = float(np.clip(confidence, 0.0, 1.0))
            az, el = unit_to_direction(self.unit_vector)
            return {
                "azimuth_deg": az,
                "elevation_deg": el,
                "track_confidence": self.track_confidence,
                "status": "init",
            }

        self.last_timestamp = timestamp
        if confidence < self.min_update_confidence:
            self.track_confidence = max(0.0, self.track_confidence * 0.92)
            az, el = unit_to_direction(self.unit_vector)
            return {
                "azimuth_deg": az,
                "elevation_deg": el,
                "track_confidence": self.track_confidence,
                "status": "hold",
            }

        alpha = float(np.clip(self.smoothing * confidence, 0.05, 0.85))
        updated = (1.0 - alpha) * self.unit_vector + alpha * measurement
        norm = float(np.linalg.norm(updated))
        if norm > 0.0:
            updated = updated / norm
        self.unit_vector = updated
        self.track_confidence = min(1.0, 0.8 * self.track_confidence + 0.2 * confidence)
        az, el = unit_to_direction(self.unit_vector)
        return {
            "azimuth_deg": az,
            "elevation_deg": el,
            "track_confidence": self.track_confidence,
            "status": "tracked",
        }
