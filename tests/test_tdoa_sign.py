from zvook_doa.config import ArrayConfig
from zvook_doa.geometry import delay_lut, make_4mic_geometry, make_pairs
from zvook_doa.utils import direction_to_unit


def test_source_on_positive_x_reaches_r1_earlier():
    config = ArrayConfig()
    positions = make_4mic_geometry(config)
    pairs = make_pairs(4)
    delays = delay_lut(
        positions,
        pairs,
        direction_to_unit(0.0, 0.0)[None, :],
        config.speed_of_sound,
    )
    pair_to_delay = dict(zip(pairs, delays[0], strict=True))
    assert pair_to_delay[(0, 1)] < 0.0
    assert pair_to_delay[(0, 2)] < 0.0
