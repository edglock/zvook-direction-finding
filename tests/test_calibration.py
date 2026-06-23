import numpy as np

from zvook_doa.calibration import Calibration, apply_calibration


def test_apply_calibration_compensates_gain_without_delay():
    frame = np.ones((16, 4), dtype=float)
    frame[:, 0] = 2.0
    calibration = Calibration(
        channel_delay_samples=np.zeros(4),
        channel_gain=np.array([2.0, 1.0, 1.0, 1.0]),
    )
    calibrated = apply_calibration(frame, calibration, fs=48000)
    np.testing.assert_allclose(calibrated, np.ones((16, 4)), atol=1e-12)


def test_apply_calibration_accepts_fractional_delays():
    t = np.arange(64, dtype=float) / 48000
    tone = np.sin(2.0 * np.pi * 1000.0 * t)
    frame = np.column_stack([tone, tone, tone, tone])
    calibration = Calibration(
        channel_delay_samples=np.array([0.0, 0.25, -0.5, 1.5]),
        channel_gain=np.ones(4),
    )
    calibrated = apply_calibration(frame, calibration, fs=48000)
    assert calibrated.shape == frame.shape
    assert np.isfinite(calibrated).all()


def test_calibration_rejects_mismatched_shapes():
    try:
        Calibration(
            channel_delay_samples=np.zeros(4),
            channel_gain=np.ones(3),
        )
    except ValueError as exc:
        assert "same shape" in str(exc)
    else:
        raise AssertionError("Expected mismatched calibration shapes to fail.")
