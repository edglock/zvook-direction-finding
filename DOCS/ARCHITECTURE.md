# Architecture

Архітектура описує майбутній Python MVP для акустичного виявлення та
пеленгації БпЛА. На поточному bootstrap етапі код ще не реалізований.

## System Overview

```text
4-channel audio input
  -> calibration
  -> preprocessing
  -> detector
  -> SRP-PHAT localizer
  -> confidence scoring
  -> direction tracker
  -> JSON Lines output
```

Система працює кадрами:

- frame duration: `0.2 s`;
- hop duration: `0.05 s`;
- default sample rate: `48000 Hz`;
- frame shape: `(n_samples, 4)`.

## Geometry and Direction Convention

Мікрофони:

- `r1 = [a / sqrt(3), 0, 0]`
- `r2 = [-a / (2 * sqrt(3)), a / 2, 0]`
- `r3 = [-a / (2 * sqrt(3)), -a / 2, 0]`
- `r4 = [0, 0, h]`

Default values:

- `a = 0.25 m`
- `h = 0.20 m`
- `c = 343.0 m/s`

Direction convention:

- `azimuth 0 deg = +X`
- azimuth increases toward `+Y`
- `elevation 0 deg = horizontal`
- `elevation 90 deg = up`

Delay convention:

```text
tau_ij = t_i - t_j = -dot(r_i - r_j, u) / c
```

Усі координати зберігаються в метрах, усі затримки в секундах, кути в public API
повертаються у градусах.

## Planned Python Modules

- `config`: `ArrayConfig`, YAML loading, default bands and timing.
- `geometry`: microphone positions, pairs, direction grids, delay LUT.
- `calibration`: channel delay and gain compensation, including fractional
  sample delays.
- `preprocessing`: DC removal, Hann window, `rFFT`, frequency masks.
- `detector`: replaceable drone detector stub with future ONNX/TFLite path.
- `srp_phat`: coarse localization, local refinement, robust subband scoring.
- `tracker`: unit-vector direction smoothing and low-confidence hold.
- `audio_io`: 4-channel WAV reading and optional realtime input adapter.
- `realtime`: ring buffer and frame-by-frame JSON Lines pipeline.
- `simulate`: synthetic plane-wave signal generation for repeatable tests.
- `utils`: shared numeric helpers.

## Data Flow

Input frame:

```text
frame: np.ndarray, shape (n_samples, 4)
```

Spectrum:

```text
X: np.ndarray, shape (n_freqs, 4)
freqs: np.ndarray, shape (n_freqs,)
```

Localization result:

```json
{
  "azimuth_deg": 60.0,
  "elevation_deg": 25.0,
  "confidence": 0.82,
  "coarse_azimuth_deg": 60.0,
  "coarse_elevation_deg": 24.0,
  "srp_peak": 123.4,
  "srp_peak_to_sidelobe": 2.1,
  "valid_frequency_bands_hz": [[150, 350], [350, 550]],
  "status": "ok"
}
```

Realtime JSON Lines add `timestamp` and `p_drone`.

## Frequency Bands

- Detection band: `120-3000 Hz`.
- Coarse localization band: `120-650 Hz`.
- Local refinement band: `120-3000 Hz`.

The higher `650-3000 Hz` range is used for local refinement only. This keeps the
coarse search more robust while still allowing sharper local estimates when the
signal quality supports it.

## Failure Modes and Status

Expected statuses:

- `ok`: localization confidence is acceptable.
- `low_confidence`: SRP/detector evidence is weak or inconsistent.
- `tracked`: tracker accepted the latest measurement.
- `hold`: tracker holds/predicts because measurement confidence is low.
- `init`: tracker has no stable prior state yet.

Important failure sources:

- wrong channel order;
- uncalibrated channel delays;
- low SNR;
- wind and handling noise;
- reflections and multi-source scenes;
- audio device not providing true synchronous 4-channel input.

## Dependencies

Required for core MVP:

- Python `>=3.11`
- `numpy`
- `scipy`
- `pyyaml`
- `soundfile`

Optional:

- `sounddevice` for realtime input;
- `onnxruntime` for future detector backend.

`pyroomacoustics` is not part of the core implementation. It may be used only as
a reference implementation during research.
