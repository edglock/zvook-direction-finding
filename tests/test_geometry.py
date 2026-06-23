import math

import numpy as np

from zvook_doa.config import ArrayConfig
from zvook_doa.geometry import delay_lut, direction_grid, make_4mic_geometry, make_pairs


def test_make_4mic_geometry_default_coordinates():
    config = ArrayConfig()
    positions = make_4mic_geometry(config)
    a = config.triangle_side_m
    h = config.top_height_m
    sqrt3 = math.sqrt(3.0)
    expected = np.array(
        [
            [a / sqrt3, 0.0, 0.0],
            [-a / (2.0 * sqrt3), a / 2.0, 0.0],
            [-a / (2.0 * sqrt3), -a / 2.0, 0.0],
            [0.0, 0.0, h],
        ]
    )
    np.testing.assert_allclose(positions, expected)


def test_make_pairs_for_four_mics():
    assert make_pairs(4) == [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]


def test_delay_lut_shape_and_formula():
    config = ArrayConfig()
    positions = make_4mic_geometry(config)
    pairs = make_pairs(4)
    directions, _, _ = direction_grid(90.0, 45.0, 0.0, 90.0)
    delays = delay_lut(positions, pairs, directions, config.speed_of_sound)
    assert delays.shape == (directions.shape[0], len(pairs))
    expected = -np.dot(positions[0] - positions[1], directions[0]) / config.speed_of_sound
    assert delays[0, 0] == expected
