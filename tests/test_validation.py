from zvook_doa.config import ArrayConfig
from zvook_doa.validation import (
    SimulationCase,
    benchmark_localizer,
    run_simulation_case,
    run_simulation_matrix,
)


def test_run_simulation_case_returns_error_metrics():
    config = ArrayConfig()
    result = run_simulation_case(config, SimulationCase(60.0, 25.0), snr_db=20.0)
    assert result["angular_error_deg"] < 5.0
    assert 0.0 <= result["confidence"] <= 1.0


def test_run_simulation_matrix_reports_passed():
    config = ArrayConfig()
    matrix = run_simulation_matrix(
        config,
        cases=(SimulationCase(0.0, 10.0), SimulationCase(315.0, 15.0)),
        snr_db=20.0,
        max_error_deg=5.0,
    )
    assert matrix["passed"] is True
    assert len(matrix["cases"]) == 2


def test_benchmark_localizer_reports_positive_timing():
    config = ArrayConfig()
    result = benchmark_localizer(config, iterations=1)
    assert result["iterations"] == 1
    assert result["avg_ms_per_frame"] > 0.0
    assert result["frame_duration_ms"] == 200.0
