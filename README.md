# ha-light-blueprints

**Night mode and an artificial sunrise for Home Assistant that hand over cleanly — two importable blueprints, no custom integration.**

Actively maintained. Tested on Home Assistant 2026.11 with Adaptive Lighting 1.32.x. First public release; behaviour may change between versions.

## What this is

Two standalone Home Assistant blueprints that share one idea: **one automation owns the lights at a time**.

- **Night mode** dims selected lights to red in ten interruptible steps, pauses Adaptive Lighting, and restores warm white in the morning. Lights that were off at restore are not switched on; they get their white command the next time they are switched on.
- **Sunrise simulation** ramps selected lights from a deep orange through warm white to an end colour temperature, with a configurable gamma brightness curve. It can pause Adaptive Lighting while it runs.

The night-mode blueprint hands the sunrise lights over at 05:30 (or when the sunrise automation starts). The remaining lights stay in night mode until the regular restore. That handover is what prevents the two automations from fighting over the same entities — the failure mode this project was written to remove.

### When not to use it

- You do not run Adaptive Lighting: the blueprints work, but you lose the profile-pause behaviour that makes the handover meaningful.
- You want a scheduler inside an integration: both blueprints are automations; all scheduling lives in Home Assistant, not in a custom component.
- You need per-light colour correction or calibrated lux control: that belongs in a sensor/lighting pipeline, not here.

## Requirements

| Requirement | Why |
| --- | --- |
| Home Assistant ≥ 2025.9 | Blueprint schema and `today_at()`/`as_timestamp()` templates |
| Adaptive Lighting with `set_manual_control` and `change_switch_settings` | Pausing and resuming profiles |
| `sun.sun` enabled | Real-sunrise restore fallback |
| Five helper entities | Active state, handover flag, dim step and two compact index lists |

Recommended Adaptive Lighting settings: `autoreset_control_seconds: 0` and `detect_non_ha_changes: true`.

## Install

> Replace every placeholder (`<profile>`, `<lampe>`, `<sunrise-automation>`) with entities from your own instance.

### 1. Create the five helpers

Create them in **Settings → Devices & Services → Helpers**, or paste [`examples/helpers.yaml`](examples/helpers.yaml) into your configuration (restart required for YAML helpers).

| Helper | Type | Purpose |
| --- | --- | --- |
| `input_boolean.night_mode_active` | Toggle | Night-mode state |
| `input_number.night_mode_dim_step` | Number, 0–10, step 1 | Current dim step |
| `input_text.night_mode_active_lights` | Text, 255 chars | **1-based indices** of touched lights |
| `input_text.night_mode_pending_lights` | Text, 255 chars | Indices of lights awaiting a white command |
| `input_boolean.night_mode_sunrise_handover` | Toggle | Whether the sunrise lights have been handed over |

The lights are stored as indices because seven full entity IDs exceed the 255-character limit of `input_text`. Keep the **Lights** input in a fixed order.

### 2. Import the blueprints

| Blueprint | Import |
| --- | --- |
| [Night mode](blueprints/night-mode/night-mode.yaml) | [![Import blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Flenucksi%2Fha-light-blueprints%2Fblob%2Fmain%2Fblueprints%2Fnight-mode%2Fnight-mode.yaml) |
| [Sunrise simulation](blueprints/sunrise/sunrise_simulation.yaml) | [![Import blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Flenucksi%2Fha-light-blueprints%2Fblob%2Fmain%2Fblueprints%2Fsunrise%2Fsunrise_simulation.yaml) |

### 3. Create the automations

Use the UI, or adapt [`examples/automations.yaml`](examples/automations.yaml). The example sets:

- start 23:00, all weekdays, 60-minute dimming, 1 % minimum, red
- restore at sunrise, 2700 K / 100 %
- sunrise handover at 05:30, with the sunrise automation and its two lights registered

Manual control: fire `night_mode_start` / `night_mode_restore` events, or trigger the automation directly. Turning the active helper off aborts a running dim sequence.

## Documentation

- [Night mode: behaviour, C2 restore, handover, restart](docs/night-mode.md)
- [Sunrise simulation: modes, parameters, winter values](docs/sunrise.md)

## Licence

Apache-2.0 — see [LICENSE](LICENSE) and [NOTICE](NOTICE).
