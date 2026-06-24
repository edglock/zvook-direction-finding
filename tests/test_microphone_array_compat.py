import numpy as np

from zvook_doa.config import ArrayConfig
from zvook_doa.geometry import make_4mic_geometry


def test_microphone_array_class_geometry_is_supported():
    config = ArrayConfig(
        triangle_side_m=0.35,
        top_height_m=1.0,
        base_height_m=0.65,
        lower_angles_deg=(0.0, -120.0, -240.0),
        top_mic_anchor="mic3",
    )
    positions = make_4mic_geometry(config)
    radius = 0.35 / np.sqrt(3.0)
    expected = np.array(
        [
            [radius, 0.0, 0.65],
            [radius * np.cos(np.deg2rad(-120.0)), radius * np.sin(np.deg2rad(-120.0)), 0.65],
            [radius * np.cos(np.deg2rad(-240.0)), radius * np.sin(np.deg2rad(-240.0)), 0.65],
            [radius * np.cos(np.deg2rad(-240.0)), radius * np.sin(np.deg2rad(-240.0)), 1.0],
        ]
    )
    np.testing.assert_allclose(positions, expected, atol=1e-12)


def test_test_array_yaml_loads_microphone_class_geometry():
    config = ArrayConfig.from_yaml("configs/test_array_microphone_class_4mic.yaml")
    assert config.triangle_side_m == 0.35
    assert config.top_height_m == 1.0
    assert config.base_height_m == 0.65
    assert config.lower_angles_deg == (0.0, -120.0, -240.0)
    assert config.top_mic_anchor == "mic3"
