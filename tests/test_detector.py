import numpy as np

from zvook_doa.detector import DroneDetector


def test_drone_detector_stub_returns_probability_and_weights():
    fs = 48000
    t = np.arange(int(0.2 * fs), dtype=float) / fs
    tone = np.sin(2.0 * np.pi * 300.0 * t)
    frame = np.column_stack([tone, tone, tone, tone])
    result = DroneDetector(fs=fs).predict(frame)
    assert 0.0 <= result["p_drone"] <= 1.0
    assert result["frequency_weights"] is not None
    assert result["frequency_weights"].shape[0] == frame.shape[0] // 2 + 1
