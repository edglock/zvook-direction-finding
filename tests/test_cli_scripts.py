import sys

from scripts import run_realtime, run_simulation, run_wav


def test_run_wav_cli_prints_clear_error(monkeypatch, capsys):
    def fail(*args, **kwargs):
        raise ValueError("Expected 4-channel WAV, got 2 channels.")

    monkeypatch.setattr(run_wav, "run_wav_jsonl", fail)
    monkeypatch.setattr(sys, "argv", ["run_wav.py", "bad.wav"])
    assert run_wav.main() == 2
    captured = capsys.readouterr()
    assert "error: Expected 4-channel WAV" in captured.err


def test_run_realtime_cli_prints_clear_error(monkeypatch, capsys):
    def fail(*args, **kwargs):
        raise RuntimeError("Realtime input requires optional dependency 'sounddevice'.")

    monkeypatch.setattr(run_realtime, "run_realtime_jsonl", fail)
    monkeypatch.setattr(sys, "argv", ["run_realtime.py"])
    assert run_realtime.main() == 2
    captured = capsys.readouterr()
    assert "error: Realtime input requires optional dependency" in captured.err


def test_run_simulation_cli_prints_clear_error(monkeypatch, capsys):
    def fail(*args, **kwargs):
        raise ValueError("Configuration YAML must contain a mapping.")

    monkeypatch.setattr(run_simulation, "load_array_config", fail)
    monkeypatch.setattr(sys, "argv", ["run_simulation.py", "--config", "bad.yaml"])
    assert run_simulation.main() == 2
    captured = capsys.readouterr()
    assert "error: Configuration YAML must contain a mapping." in captured.err
