"""MVP validation helpers for synthetic smoke tests and benchmarks."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

from .config import ArrayConfig
from .geometry import make_4mic_geometry
from .simulate import simulate_plane_wave
from .srp_phat import SRPPHATLocalizer
from .utils import angular_distance_deg


@dataclass(frozen=True, slots=True)
class SimulationCase:
    """One synthetic direction-finding validation case."""

    azimuth_deg: float
    elevation_deg: float


DEFAULT_SIMULATION_CASES: tuple[SimulationCase, ...] = (
    SimulationCase(0.0, 10.0),
    SimulationCase(60.0, 25.0),
    SimulationCase(180.0, 45.0),
    SimulationCase(315.0, 15.0),
)


def run_simulation_case(
    config: ArrayConfig,
    case: SimulationCase,
    snr_db: float = 20.0,
    signal_type: str = "chirp",
) -> dict[str, float | str]:
    """Generate one synthetic frame, localize it, and return error metrics."""

    positions = make_4mic_geometry(config)
    frame = simulate_plane_wave(
        azimuth_deg=case.azimuth_deg,
        elevation_deg=case.elevation_deg,
        duration_s=config.frame_duration_s,
        fs=config.fs,
        mic_positions=positions,
        signal_type=signal_type,
        snr_db=snr_db,
        speed_of_sound=config.speed_of_sound,
    )
    result = SRPPHATLocalizer(config, positions).locate(frame)
    error = angular_distance_deg(
        case.azimuth_deg,
        case.elevation_deg,
        float(result["azimuth_deg"]),
        float(result["elevation_deg"]),
    )
    return {
        "true_azimuth_deg": case.azimuth_deg,
        "true_elevation_deg": case.elevation_deg,
        "estimated_azimuth_deg": float(result["azimuth_deg"]),
        "estimated_elevation_deg": float(result["elevation_deg"]),
        "angular_error_deg": error,
        "confidence": float(result["confidence"]),
        "status": str(result["status"]),
    }


def run_simulation_matrix(
    config: ArrayConfig,
    cases: tuple[SimulationCase, ...] = DEFAULT_SIMULATION_CASES,
    snr_db: float = 20.0,
    max_error_deg: float = 5.0,
) -> dict[str, object]:
    """Run the standard synthetic direction matrix and summarize pass/fail."""

    results = [run_simulation_case(config, case, snr_db=snr_db) for case in cases]
    worst_error = max(float(item["angular_error_deg"]) for item in results)
    return {
        "passed": worst_error <= max_error_deg,
        "max_error_deg": max_error_deg,
        "worst_error_deg": worst_error,
        "cases": results,
    }


def benchmark_localizer(
    config: ArrayConfig,
    iterations: int = 10,
    case: SimulationCase = SimulationCase(60.0, 25.0),
    snr_db: float = 20.0,
) -> dict[str, float | int]:
    """Measure average processing time for one synthetic frame."""

    if iterations <= 0:
        raise ValueError("iterations must be positive.")

    positions = make_4mic_geometry(config)
    frame = simulate_plane_wave(
        azimuth_deg=case.azimuth_deg,
        elevation_deg=case.elevation_deg,
        duration_s=config.frame_duration_s,
        fs=config.fs,
        mic_positions=positions,
        snr_db=snr_db,
        speed_of_sound=config.speed_of_sound,
    )
    localizer = SRPPHATLocalizer(config, positions)
    localizer.locate(frame)

    start = perf_counter()
    for _ in range(iterations):
        localizer.locate(frame)
    elapsed_s = perf_counter() - start
    return {
        "iterations": iterations,
        "avg_ms_per_frame": (elapsed_s / iterations) * 1000.0,
        "frame_duration_ms": config.frame_duration_s * 1000.0,
    }
