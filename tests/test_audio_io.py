import numpy as np
import soundfile as sf

from zvook_doa.audio_io import iter_frames, read_wav_4ch


def test_iter_frames_yields_expected_starts_and_shapes():
    audio = np.zeros((8, 4), dtype=float)
    frames = list(iter_frames(audio, frame_samples=4, hop_samples=2))
    assert [start for start, _ in frames] == [0, 2, 4]
    assert [frame.shape for _, frame in frames] == [(4, 4), (4, 4), (4, 4)]


def test_read_wav_4ch_accepts_four_channel_file(tmp_path):
    path = tmp_path / "four_channel.wav"
    data = np.zeros((16, 4), dtype=float)
    sf.write(path, data, samplerate=48000)
    audio, fs = read_wav_4ch(str(path))
    assert audio.shape == (16, 4)
    assert fs == 48000


def test_read_wav_4ch_rejects_wrong_channel_count(tmp_path):
    path = tmp_path / "two_channel.wav"
    data = np.zeros((16, 2), dtype=float)
    sf.write(path, data, samplerate=48000)
    try:
        read_wav_4ch(str(path))
    except ValueError as exc:
        assert "Expected 4-channel WAV" in str(exc)
    else:
        raise AssertionError("Expected non-4-channel WAV to fail.")
