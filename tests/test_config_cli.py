import json

from zvook_doa.calibration import Calibration
from zvook_doa.cli import load_array_config, load_calibration
from zvook_doa.config import ArrayConfig


def test_load_array_config_defaults_when_path_is_none():
    config = load_array_config()
    assert isinstance(config, ArrayConfig)
    assert config.fs == 48000
    assert config.detection_band_hz == (120.0, 3000.0)
    assert config.coarse_band_hz == (120.0, 650.0)
    assert config.refine_band_hz == (120.0, 3000.0)


def test_load_array_config_from_yaml(tmp_path):
    path = tmp_path / "array.yaml"
    path.write_text(
        "\n".join(
            [
                "fs: 16000",
                "triangle_side_m: 0.3",
                "coarse_band_hz: [200, 600]",
            ]
        ),
        encoding="utf-8",
    )
    config = load_array_config(path)
    assert config.fs == 16000
    assert config.triangle_side_m == 0.3
    assert config.coarse_band_hz == (200.0, 600.0)


def test_load_array_config_accepts_experiment_aliases(tmp_path):
    path = tmp_path / "array.yaml"
    path.write_text(
        "\n".join(
            [
                "distance_mics: 0.35",
                "analysis_band_hz: [120, 3000]",
                "coarse_band_hz: [120, 650]",
            ]
        ),
        encoding="utf-8",
    )
    config = load_array_config(path)
    assert config.triangle_side_m == 0.35
    assert config.detection_band_hz == (120.0, 3000.0)
    assert config.refine_band_hz == (120.0, 3000.0)
    assert config.coarse_band_hz == (120.0, 650.0)


def test_load_array_config_rejects_duplicate_distance_fields(tmp_path):
    path = tmp_path / "array.yaml"
    path.write_text("distance_mics: 0.35\ntriangle_side_m: 0.25\n", encoding="utf-8")
    try:
        load_array_config(path)
    except ValueError as exc:
        assert "distance_mics or triangle_side_m" in str(exc)
    else:
        raise AssertionError("Expected duplicate distance config fields to fail.")


def test_load_calibration_from_json(tmp_path):
    path = tmp_path / "calibration.json"
    path.write_text(
        json.dumps(
            {
                "channel_delay_samples": [0.0, 0.25, -0.5, 1.0],
                "channel_gain": [1.0, 1.1, 0.9, 1.0],
            }
        ),
        encoding="utf-8",
    )
    calibration = load_calibration(path)
    assert isinstance(calibration, Calibration)
    assert calibration.channel_delay_samples.shape == (4,)
    assert calibration.channel_gain.shape == (4,)


def test_load_calibration_returns_none_without_path():
    assert load_calibration() is None
