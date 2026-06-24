# Zvook Direction Finding

Проєкт системи акустичного виявлення та визначення напрямку на БпЛА за
4-канальним мікрофонним масивом. Базовий режим застосування: defensive
monitoring - виявлення, оцінка напрямку, confidence, логування та операторські
алерти без інтеграції з системами ураження.

## Ціль MVP

Система має оцінювати для одного акустичного джерела:

- `azimuth_deg` - азимут у градусах;
- `elevation_deg` - кут місця у градусах;
- `confidence` - довіра до результату в діапазоні `[0, 1]`.

MVP не оцінює дальність до джерела.

## Геометрія масиву

Масив складається з 4 мікрофонів:

- 3 нижні мікрофони у вершинах рівностороннього трикутника;
- 4-й мікрофон над центром трикутника.

Параметри за замовчуванням із `DOCS/Planning.txt`:

- сторона трикутника `a = 0.25 m`;
- висота верхнього мікрофона `h = 0.20 m`;
- частота дискретизації `fs = 48000 Hz`;
- швидкість звуку `c = 343.0 m/s`.

Конвенції кутів:

- `azimuth 0 deg = +X`;
- азимут зростає в напрямку `+Y`;
- `elevation 0 deg = horizontal`;
- `elevation 90 deg = up`.

## Метод

Базовий алгоритм локалізації - SRP-PHAT:

1. 4-канальний аудіокадр калібрується за затримкою та gain каналів.
2. З кадру прибирається DC, застосовується Hann window.
3. Для кожного каналу рахується `rFFT`.
4. Для пар мікрофонів будуються PHAT cross-spectra.
5. SRP score рахується на сітці напрямків через delay LUT.
6. Груба оцінка виконується у стабільній нижній смузі `120-650 Hz`.
7. Локальне уточнення виконується у повній робочій смузі `120-3000 Hz`.
8. Результат проходить confidence scoring і direction tracker.

TDOA для пари мікрофонів:

```text
tau_ij = -dot(r_i - r_j, u) / c
```

де `r_i`, `r_j` - координати мікрофонів, `u` - одиничний вектор напрямку,
`c` - швидкість звуку.

## Поточний стан

Реалізовано Python MVP:

- конфігурація масиву через `ArrayConfig` та YAML;
- геометрія 4 мікрофонів, direction grid і delay LUT;
- calibration helper з fractional delay compensation;
- preprocessing для одного кадру;
- detector stub з optional ONNX Runtime інтерфейсом;
- SRP-PHAT coarse/refine localizer;
- synthetic plane-wave generator;
- MVP self-check для synthetic matrix і benchmark;
- direction tracker;
- WAV і realtime JSON Lines pipeline;
- CLI-скрипти та unit tests.

## Roadmap

- Docs bootstrap: Git, `DOCS/Planning.txt`, архітектура, MVP план.
- Simulation: синтетичні 4-канальні сигнали з відомими `az/el`.
- SRP-PHAT core: geometry, preprocessing, coarse/refine localization.
- WAV mode: обробка 4-канальних WAV кадрами та JSON Lines output.
- Realtime mode: optional `sounddevice`, ring buffer, tracker, JSON Lines output.

## CLI

```bash
python -m zvook_doa.simulate --az 60 --el 25 --snr-db 10
python scripts/run_simulation.py --az 60 --el 25 --snr-db 20 --config configs/default_array_4mic.yaml
python scripts/run_wav.py path/to/4ch.wav --config configs/default_array_4mic.yaml --calibration configs/calibration_example.json
python scripts/run_wav.py path/to/4ch.wav --config configs/default_array_4mic.yaml --raw
python scripts/run_realtime.py --config configs/default_array_4mic.yaml --calibration configs/calibration_example.json
```

Для тестового `.flac`, записаного решіткою з класу `MicrophoneArray`, використовуй
окрему конфігурацію:

```bash
.venv/bin/python scripts/run_wav.py path/to/recording.flac \
  --config configs/test_array_microphone_class_4mic.yaml \
  --calibration configs/calibration_example.json
```

Ця конфігурація відповідає `distance_mics=0.35`, `height_m4=1.0`,
`base_height=0.65`, нижнім кутам `[0, -120, -240]` і 4-му мікрофону над
мікрофоном `positions[2]`.

## Встановлення та перевірка

```bash
python -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m pytest
```

Перевірені simulation сценарії:

```bash
.venv/bin/python scripts/run_simulation.py --az 0 --el 10
.venv/bin/python scripts/run_simulation.py --az 60 --el 25
.venv/bin/python scripts/run_simulation.py --az 180 --el 45
.venv/bin/python scripts/run_simulation.py --az 315 --el 15
```

Змінити геометрію, `fs`, відстань між нижніми мікрофонами або frequency bands
можна через YAML:

```bash
.venv/bin/python scripts/run_simulation.py --config configs/default_array_4mic.yaml
```

Для експериментів у config є короткі поля:

```yaml
distance_mics: 0.35
analysis_band_hz: [120.0, 3000.0]
coarse_band_hz: [120.0, 650.0]
```

`distance_mics` є alias для сторони нижнього трикутника `triangle_side_m`.
`analysis_band_hz` задає detector band і local refinement band; `coarse_band_hz`
можна залишати нижчим для стабільнішого грубого пошуку.

Калібрування для WAV/FLAC/realtime режимів передається окремим JSON:

```bash
.venv/bin/python scripts/run_wav.py path/to/4ch.wav --calibration configs/calibration_example.json
```

RAW-аналіз запускає SRP-PHAT без detector, tracker, `p_drone` і `confidence`:

```bash
.venv/bin/python scripts/run_wav.py path/to/4ch.flac \
  --config configs/test_array_microphone_class_4mic.yaml \
  --raw > raw_results.jsonl
```

## MVP self-check

Перед реальним тестуванням можна запустити один synthetic health check:

```bash
.venv/bin/python scripts/check_mvp.py
```

Він проганяє стандартну матрицю напрямків, перевіряє максимальну похибку
`<= 5 deg`, міряє середній час обробки одного кадру і друкує JSON-звіт.

Поточний простий benchmark залежить від ширини refine-смуги: для `120-3000 Hz`
орієнтовно `280-285 ms/frame` у тимчасовому test venv на одному synthetic кадрі
`0.2 s`.

## Обмеження

- Система оцінює напрямок, а не дальність.
- Діапазон `650-3000 Hz` використовується для локального уточнення, а не для
  грубої пеленгації.
- Потрібне калібрування затримок і gain каналів.
- `confidence` є обов'язковою частиною результату.
- Realtime режим залежить від реального audio hardware, стабільного драйвера та
  коректного 4-канального input device.

## Документи

- `DOCS/Planning.txt` - оригінальний prompt/spec.
- `DOCS/MVP_PLAN.md` - staged план реалізації.
- `DOCS/ARCHITECTURE.md` - архітектура майбутнього Python пакета.
- `DOCS/STATUS_2026-06-23.md` - поточний MVP статус і verification evidence.
