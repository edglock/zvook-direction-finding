from zvook_doa.config import ArrayConfig
from zvook_doa.geometry import make_4mic_geometry
from zvook_doa.simulate import simulate_plane_wave
from zvook_doa.srp_phat import SRPPHATLocalizer
from zvook_doa.utils import angular_distance_deg


def test_srp_synthetic_coarse_refine_under_five_degrees():
    config = ArrayConfig()
    positions = make_4mic_geometry(config)
    frame = simulate_plane_wave(
        azimuth_deg=60.0,
        elevation_deg=25.0,
        duration_s=config.frame_duration_s,
        fs=config.fs,
        mic_positions=positions,
        signal_type="chirp",
        snr_db=20.0,
        speed_of_sound=config.speed_of_sound,
    )
    result = SRPPHATLocalizer(config, positions).locate(frame)
    error = angular_distance_deg(60.0, 25.0, result["azimuth_deg"], result["elevation_deg"])
    assert error < 5.0
    assert result["status"] in {"ok", "low_confidence"}
