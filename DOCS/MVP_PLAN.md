# MVP Plan

Цей план розбиває `DOCS/Planning.txt` на етапи, які можна реалізовувати та
перевіряти окремо. Поточний стан: Python MVP реалізований, проходить synthetic
validation і готовиться до тестування користувачем на реальному аудіо/hardware.

## MVP-0: Repo and Docs Bootstrap

Deliverables:

- Ініціалізований Git repository.
- `DOCS/Planning.txt` як verbatim копія source prompt.
- `README.md`, `DOCS/MVP_PLAN.md`, `DOCS/ARCHITECTURE.md`.

Acceptance criteria:

- `git status --short --branch` працює без помилки.
- `DOCS/Planning.txt` має 330 рядків, як source file.
- Документи не стверджують, що DSP pipeline вже реалізований.

Verification:

```bash
git status --short --branch
wc -l /home/edglock/Завантажене/Planning.txt DOCS/Planning.txt
find . -maxdepth 2 -type f | sort
```

## MVP-1: Python Skeleton, Config, Geometry

Deliverables:

- `pyproject.toml` з Python `>=3.11`.
- Package `zvook_doa/`.
- `config.py` з `ArrayConfig` і YAML loading.
- `geometry.py` з 4-mic geometry, mic pairs, direction grid, delay LUT.
- `configs/default_array_4mic.yaml`.
- Tests for geometry and TDOA sign convention.

Acceptance criteria:

- Координати мікрофонів відповідають spec.
- `make_pairs(4)` повертає 6 пар.
- `delay_lut` використовує `tau_ij = -dot(r_i - r_j, u) / c`.

Verification:

```bash
pytest tests/test_geometry.py tests/test_tdoa_sign.py
```

## MVP-2: Preprocessing, Simulation, SRP-PHAT Core

Deliverables:

- `preprocessing.py` для DC removal, Hann window, `rFFT`, frequency masking.
- `simulate.py` для synthetic 4-channel plane wave data.
- `srp_phat.py` з coarse grid, local refine grid, vectorized/chunked scoring.
- `scripts/run_simulation.py`.

Acceptance criteria:

- Synthetic `az=60 deg`, `el=25 deg`, `snr_db=20` локалізується з похибкою
  менше 5 градусів.
- `score_grid` не має Python-loop по кожному direction.
- Усі кути в API повертаються в градусах.

Verification:

```bash
pytest tests/test_srp_synthetic.py
python scripts/run_simulation.py --az 60 --el 25 --snr-db 20
```

## MVP-3: Detector Stub, Confidence, Tracker

Deliverables:

- `detector.py` з `DroneDetector.predict()`.
- Stub energy-based `p_drone` у смузі `80-2000 Hz`.
- Optional ONNX Runtime interface без обов'язкової залежності `onnxruntime`.
- `compute_confidence()` на основі `p_drone`, SRP peak-to-sidelobe,
  valid subbands і optional track quality.
- `tracker.py` з unit-vector smoothing і коректним переходом `359 -> 1 deg`.

Acceptance criteria:

- Confidence не дорівнює просто `p_drone`.
- Low-confidence measurement переводить tracker у hold/prediction behavior.
- Tracker не ламається на wrap-around азимуту.

Verification:

```bash
pytest tests/test_tracker.py
pytest
```

## MVP-4: WAV Pipeline and JSON Lines Output

Deliverables:

- `audio_io.py` для читання 4-канального WAV через `soundfile`.
- `scripts/run_wav.py`.
- Frame processing з `frame_duration_s = 0.2` і `hop_duration_s = 0.05`.
- JSON Lines output для кожного кадру.

Acceptance criteria:

- WAV mode відхиляє файли не з 4 каналами зрозумілою помилкою.
- Кожен JSON line містить timestamp, `p_drone`, `azimuth_deg`,
  `elevation_deg`, `confidence`, coarse result, SRP metadata і `status`.

Verification:

```bash
python scripts/run_wav.py path/to/4ch.wav
pytest
```

## MVP-5: Realtime Input

Deliverables:

- `realtime.py` з audio input -> ring buffer -> frame each hop -> detector ->
  SRP-PHAT -> tracker -> JSON Lines.
- `scripts/run_realtime.py`.
- Optional `sounddevice` support.

Acceptance criteria:

- Якщо `sounddevice` не встановлений, CLI показує зрозумілу помилку.
- Realtime mode не є обов'язковим для unit tests.
- Pipeline працює близько до realtime на CPU для одного 0.2 s кадру.

Verification:

```bash
python scripts/run_realtime.py
pytest
```

## Post-MVP Validation

- Запустити simulation для напрямків:
  - `az=0`, `el=10`
  - `az=60`, `el=25`
  - `az=180`, `el=45`
  - `az=315`, `el=15`
- Додати benchmark часу обробки одного `0.2 s` кадру в `README.md`.
- Провести реальне калібрування каналів перед польовими тестами.

## User Testing Gate

Перед передачею на тестування:

```bash
.venv/bin/python -m pytest
.venv/bin/python scripts/check_mvp.py
```

Очікувано:

- усі unit tests проходять;
- `scripts/check_mvp.py` повертає exit code `0`;
- synthetic matrix має `worst_error_deg <= 5.0`;
- benchmark друкує `avg_ms_per_frame` для поточної машини.
