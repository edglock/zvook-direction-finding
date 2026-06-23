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
6. Груба оцінка виконується у смузі `150-650 Hz`.
7. Локальне уточнення виконується у смузі `150-2000 Hz`.
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
- direction tracker;
- WAV і realtime JSON Lines pipeline;
- CLI-скрипти та unit tests.

## Roadmap

- Docs bootstrap: Git, `DOCS/Planning.txt`, архітектура, MVP план.
- Simulation: синтетичні 4-канальні сигнали з відомими `az/el`.
- SRP-PHAT core: geometry, preprocessing, coarse/refine localization.
- WAV mode: обробка 4-канальних WAV кадрами та JSON Lines output.
- Realtime mode: optional `sounddevice`, ring buffer, tracker, JSON Lines output.

## Заплановані CLI

```bash
python -m zvook_doa.simulate --az 60 --el 25 --snr-db 10
python scripts/run_simulation.py --az 60 --el 25 --snr-db 20
python scripts/run_wav.py path/to/4ch.wav
python scripts/run_realtime.py
```

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

Поточний простий benchmark у цьому середовищі: приблизно `152 ms/frame` для
одного synthetic кадру `0.2 s` з default coarse/refine сітками.

## Обмеження

- Система оцінює напрямок, а не дальність.
- Діапазон `700-2000 Hz` використовується для локального уточнення, а не для
  грубої пеленгації.
- Потрібне калібрування затримок і gain каналів.
- `confidence` є обов'язковою частиною результату.
- Realtime режим залежить від реального audio hardware, стабільного драйвера та
  коректного 4-канального input device.

## Документи

- `DOCS/Planning.txt` - оригінальний prompt/spec.
- `DOCS/MVP_PLAN.md` - staged план реалізації.
- `DOCS/ARCHITECTURE.md` - архітектура майбутнього Python пакета.
