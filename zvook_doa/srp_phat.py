"""SRP-PHAT direction localization."""

from __future__ import annotations

from dataclasses import dataclass, field
import math

import numpy as np

from .calibration import Calibration, apply_calibration
from .config import ArrayConfig
from .geometry import delay_lut, direction_grid, make_pairs
from .preprocessing import apply_hann, frequency_mask, remove_dc, rfft_multichannel
from .utils import angular_distance_deg, clamp, direction_to_unit, wrap_azimuth_deg


def _peak_to_sidelobe(scores: np.ndarray) -> float:
    values = np.asarray(scores, dtype=float)
    if values.size < 2:
        return 0.0
    shifted = values - float(np.min(values))
    order = np.sort(shifted)
    peak = float(order[-1])
    sidelobe = float(order[-2])
    if peak <= 1e-12:
        return 0.0
    return peak / (sidelobe + 1e-12)


def compute_confidence(
    p_drone: float,
    peak_to_sidelobe: float,
    number_of_valid_bands: int,
    score: float,
    track_quality: float | None = None,
) -> float:
    """Combine detector, SRP shape, valid bands, and optional tracker quality."""

    p = clamp(float(p_drone), 0.0, 1.0)
    psl_score = clamp((float(peak_to_sidelobe) - 1.0) / 0.35, 0.0, 1.0)
    band_score = clamp(number_of_valid_bands / 4.0, 0.0, 1.0)
    srp_score = clamp(math.log1p(max(float(score), 0.0)) / 6.0, 0.0, 1.0)
    confidence = 0.35 * p + 0.35 * psl_score + 0.2 * band_score + 0.1 * srp_score
    if track_quality is not None:
        confidence = 0.85 * confidence + 0.15 * clamp(track_quality, 0.0, 1.0)
    return clamp(confidence, 0.0, 1.0)


@dataclass(slots=True)
class SRPPHATLocalizer:
    """SRP-PHAT localizer for a fixed microphone array."""

    config: ArrayConfig
    mic_positions: np.ndarray
    chunk_size: int = 512
    robust_subbands: bool = True
    pairs: list[tuple[int, int]] = field(init=False)
    coarse_directions: np.ndarray = field(init=False)
    coarse_azimuth_deg: np.ndarray = field(init=False)
    coarse_elevation_deg: np.ndarray = field(init=False)
    coarse_delay_lut: np.ndarray = field(init=False)
    _cached_freqs: np.ndarray | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        self.mic_positions = np.asarray(self.mic_positions, dtype=float)
        self.pairs = make_pairs(self.mic_positions.shape[0])
        (
            self.coarse_directions,
            self.coarse_azimuth_deg,
            self.coarse_elevation_deg,
        ) = direction_grid(
            self.config.coarse_az_step_deg,
            self.config.coarse_el_step_deg,
            self.config.min_elevation_deg,
            self.config.max_elevation_deg,
        )
        self.coarse_delay_lut = delay_lut(
            self.mic_positions,
            self.pairs,
            self.coarse_directions,
            self.config.speed_of_sound,
        )
        self._cached_freqs = None

    def compute_phat_cross_spectra(
        self,
        spectra: np.ndarray,
        freqs: np.ndarray,
        band_hz: tuple[float, float],
        frequency_weights: np.ndarray | None = None,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray | None]:
        """Compute PHAT cross spectra for all microphone pairs."""

        mask = frequency_mask(freqs, band_hz)
        selected = spectra[mask]
        selected_freqs = freqs[mask]
        if selected.size == 0:
            raise ValueError(f"No FFT bins found in band {band_hz}.")

        phat = []
        eps = 1e-12
        for i, j in self.pairs:
            cross = selected[:, i] * np.conj(selected[:, j])
            phat.append(cross / (np.abs(cross) + eps))
        phat_arr = np.asarray(phat)

        selected_weights = None
        if frequency_weights is not None:
            weights = np.asarray(frequency_weights, dtype=float)
            if weights.shape == freqs.shape:
                selected_weights = weights[mask]
            elif weights.shape == selected_freqs.shape:
                selected_weights = weights
            else:
                raise ValueError("frequency_weights must match freqs or selected_freqs shape.")
        return phat_arr, selected_freqs, selected_weights

    def score_grid(
        self,
        phat: np.ndarray,
        selected_freqs: np.ndarray,
        delays: np.ndarray,
        weights: np.ndarray | None = None,
    ) -> np.ndarray:
        """Score all directions using the frequency-domain SRP-PHAT formula."""

        if phat.ndim != 2:
            raise ValueError("phat must have shape (n_pairs, n_freqs).")
        if weights is None:
            weights_arr = np.ones(selected_freqs.shape, dtype=float)
        else:
            weights_arr = np.asarray(weights, dtype=float)
        pair_freq = phat * weights_arr[None, :]

        scores = np.empty(delays.shape[0], dtype=float)
        omega = 2.0 * np.pi * selected_freqs
        for start in range(0, delays.shape[0], self.chunk_size):
            stop = min(start + self.chunk_size, delays.shape[0])
            chunk_delays = delays[start:stop]
            phase = np.exp(1j * chunk_delays[:, :, None] * omega[None, None, :])
            scores[start:stop] = np.real(phase * pair_freq[None, :, :]).sum(axis=(1, 2))
        return scores

    def locate_coarse(
        self,
        spectra: np.ndarray,
        freqs: np.ndarray,
        frequency_weights: np.ndarray | None = None,
    ) -> dict[str, object]:
        """Run coarse SRP-PHAT localization."""

        phat, selected_freqs, weights = self.compute_phat_cross_spectra(
            spectra,
            freqs,
            self.config.coarse_band_hz,
            frequency_weights,
        )
        scores = self.score_grid(phat, selected_freqs, self.coarse_delay_lut, weights)
        best = int(np.argmax(scores))
        top_indices = np.argsort(scores)[-5:][::-1].astype(int).tolist()
        return {
            "azimuth_deg": float(self.coarse_azimuth_deg[best]),
            "elevation_deg": float(self.coarse_elevation_deg[best]),
            "score": float(scores[best]),
            "scores": scores,
            "top_indices": top_indices,
            "peak_to_sidelobe": _peak_to_sidelobe(scores),
        }

    def make_local_grid(
        self,
        azimuth_deg: float,
        elevation_deg: float,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Create a local refinement grid around a coarse direction."""

        radius = self.config.refine_radius_deg
        step = self.config.refine_step_deg
        az_offsets = np.arange(-radius, radius + step * 0.5, step, dtype=float)
        el_offsets = np.arange(-radius, radius + step * 0.5, step, dtype=float)
        az_values = np.array([wrap_azimuth_deg(azimuth_deg + off) for off in az_offsets])
        el_values = np.array(
            [
                clamp(elevation_deg + off, self.config.min_elevation_deg, self.config.max_elevation_deg)
                for off in el_offsets
            ],
            dtype=float,
        )
        az_grid, el_grid = np.meshgrid(az_values, el_values, indexing="xy")
        az_flat = az_grid.ravel()
        el_flat = el_grid.ravel()
        directions = np.vstack(
            [direction_to_unit(az, el) for az, el in zip(az_flat, el_flat, strict=True)]
        )
        return directions, az_flat, el_flat

    def locate_refined(
        self,
        spectra: np.ndarray,
        freqs: np.ndarray,
        coarse_result: dict[str, object],
        frequency_weights: np.ndarray | None = None,
    ) -> dict[str, object]:
        """Run local refinement around the coarse SRP-PHAT result."""

        coarse_az = float(coarse_result["azimuth_deg"])
        coarse_el = float(coarse_result["elevation_deg"])
        directions, azimuths, elevations = self.make_local_grid(coarse_az, coarse_el)
        local_delays = delay_lut(
            self.mic_positions,
            self.pairs,
            directions,
            self.config.speed_of_sound,
        )

        valid_bands: list[tuple[float, float]] = []
        combined_scores = np.zeros(directions.shape[0], dtype=float)
        bands = [self.config.refine_band_hz]
        if self.robust_subbands:
            low, high = self.config.refine_band_hz
            edges = np.arange(low, high, 200.0)
            bands = [(float(edge), float(min(edge + 200.0, high))) for edge in edges]

        for band in bands:
            try:
                phat, selected_freqs, weights = self.compute_phat_cross_spectra(
                    spectra,
                    freqs,
                    band,
                    frequency_weights,
                )
            except ValueError:
                continue
            scores = self.score_grid(phat, selected_freqs, local_delays, weights)
            best = int(np.argmax(scores))
            distance = angular_distance_deg(
                float(azimuths[best]),
                float(elevations[best]),
                coarse_az,
                coarse_el,
            )
            psl = _peak_to_sidelobe(scores)
            if not self.robust_subbands or distance <= 15.0 or psl >= 1.01:
                combined_scores += scores
                valid_bands.append(band)

        if not valid_bands:
            phat, selected_freqs, weights = self.compute_phat_cross_spectra(
                spectra,
                freqs,
                self.config.refine_band_hz,
                frequency_weights,
            )
            combined_scores = self.score_grid(phat, selected_freqs, local_delays, weights)
            valid_bands = [self.config.refine_band_hz]

        best = int(np.argmax(combined_scores))
        return {
            "azimuth_deg": float(azimuths[best]),
            "elevation_deg": float(elevations[best]),
            "score": float(combined_scores[best]),
            "valid_bands_hz": valid_bands,
            "peak_to_sidelobe": _peak_to_sidelobe(combined_scores),
        }

    def locate(
        self,
        frame: np.ndarray,
        calibration: Calibration | None = None,
        detector_result: dict[str, object] | None = None,
    ) -> dict[str, object]:
        """Run the full single-frame localization pipeline."""

        data = np.asarray(frame, dtype=float)
        if calibration is not None:
            data = apply_calibration(data, calibration, self.config.fs)
        data = apply_hann(remove_dc(data))
        spectra, freqs = rfft_multichannel(data, self.config.fs)
        self._cached_freqs = freqs

        weights = None
        p_drone = 1.0
        if detector_result is not None:
            p_drone = float(detector_result.get("p_drone", 1.0))
            raw_weights = detector_result.get("frequency_weights")
            if raw_weights is not None:
                weights = np.asarray(raw_weights, dtype=float)

        coarse = self.locate_coarse(spectra, freqs, weights)
        refined = self.locate_refined(spectra, freqs, coarse, weights)
        confidence = compute_confidence(
            p_drone=p_drone,
            peak_to_sidelobe=float(refined["peak_to_sidelobe"]),
            number_of_valid_bands=len(refined["valid_bands_hz"]),
            score=float(refined["score"]),
        )
        return {
            "azimuth_deg": float(refined["azimuth_deg"]),
            "elevation_deg": float(refined["elevation_deg"]),
            "confidence": confidence,
            "coarse_azimuth_deg": float(coarse["azimuth_deg"]),
            "coarse_elevation_deg": float(coarse["elevation_deg"]),
            "srp_peak": float(refined["score"]),
            "srp_peak_to_sidelobe": float(refined["peak_to_sidelobe"]),
            "valid_frequency_bands_hz": list(refined["valid_bands_hz"]),
            "status": "ok" if confidence >= 0.35 else "low_confidence",
        }

    def locate_raw(
        self,
        frame: np.ndarray,
        calibration: Calibration | None = None,
    ) -> dict[str, object]:
        """Run SRP-PHAT localization without detector or confidence scoring."""

        data = np.asarray(frame, dtype=float)
        if calibration is not None:
            data = apply_calibration(data, calibration, self.config.fs)
        data = apply_hann(remove_dc(data))
        spectra, freqs = rfft_multichannel(data, self.config.fs)
        self._cached_freqs = freqs

        coarse = self.locate_coarse(spectra, freqs)
        refined = self.locate_refined(spectra, freqs, coarse)
        return {
            "azimuth_deg": float(refined["azimuth_deg"]),
            "elevation_deg": float(refined["elevation_deg"]),
            "coarse_azimuth_deg": float(coarse["azimuth_deg"]),
            "coarse_elevation_deg": float(coarse["elevation_deg"]),
            "srp_peak": float(refined["score"]),
            "srp_peak_to_sidelobe": float(refined["peak_to_sidelobe"]),
            "valid_frequency_bands_hz": list(refined["valid_bands_hz"]),
            "status": "raw",
        }
