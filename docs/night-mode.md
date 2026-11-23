# Night Mode (rig-for-red replacement)

Night mode is a submarine-style lighting routine for lights managed by
Adaptive Lighting: in the evening the lights turn red and dim down in ten
steps, while the Adaptive Lighting profile switches are paused; in the morning
the night ends and Adaptive Lighting takes over again.

It is implemented as an automation blueprint, not as an integration. No
Adaptive Lighting Python code or services are added or changed. All lighting
control uses the services Adaptive Lighting already provides:

- `adaptive_lighting.set_manual_control`
- `adaptive_lighting.change_switch_settings` (only for sleep mode)
- `switch.turn_on` / `switch.turn_off` for the profile and sleep-mode switches
- `light.turn_on` for the red dim and the white restore

## Requirements

Create four helpers in **Settings → Devices & Services → Helpers** before
importing the blueprint:

| Helper | Type | Purpose |
| --- | --- | --- |
| `input_boolean.night_mode_active` | Toggle | Stores whether the night is active. |
| `input_number.night_mode_dim_step` | Number (0–10, step 1) | Stores the current dim step for diagnostics. |
| `input_text.night_mode_active_lights` | Text (255 chars) | Comma-separated **1-based indices** of the lights in the Lights list that were active during the night. |
| `input_text.night_mode_pending_lights` | Text (255 chars) | Indices of lights that still need a white command the next time they are switched on. |

Indices are used instead of entity IDs because seven full entity IDs would
exceed the 255 character limit of `input_text`. The index is the position of a
light in the **Lights** input of the blueprint, starting at 1. Keep that list
in a fixed order.

## Setup

1. Import [`night-mode.yaml`](../blueprints/night-mode/night-mode.yaml) via
   **Settings → Automations & scenes → Blueprints → Import Blueprint** (or use
   the import badge in the [README](../README.md#2-import-the-blueprints)).
2. Create an automation from the blueprint and select:
   - the four helpers above,
   - the Adaptive Lighting **main profile switches** to pause,
   - the lights to control, in a fixed order,
   - optional sleep-mode switches if you use sleep mode,
   - start time, weekdays, dim duration and minimum brightness,
   - night color (`red`, `blue`, or a custom RGB color),
   - restore mode and — if a sunrise automation is selected — its entity and
     the lights it controls.
3. Optionally add buttons or a Zigbee button action that fires the events
   `night_mode_start` and `night_mode_restore` (see below).

The automation uses `mode: parallel` so a manual restore is never blocked by a
running dim sequence.

## Behavior

### Activation

At `start_time` (on the selected weekdays) or on a `night_mode_start` event:

1. `input_boolean.night_mode_active` turns on, the dim step resets to 0, the
   touched-light indices are written and the pending list is cleared.
2. `adaptive_lighting.set_manual_control` marks the lights as manually
   controlled, so Adaptive Lighting stops adapting them.
3. Either the profile switches turn off, or — with *Use Adaptive Lighting sleep
   mode* enabled — `sleep_rgb_or_color_temp` is set to `rgb_color`,
   `sleep_rgb_color` to the night color, and the sleep-mode switches turn on.
4. The lights that are on are set to the night color, then dimmed from 255 to
   the configured minimum in ten steps. Each step sets the step helper and uses
   a `light.turn_on` transition equal to one tenth of the dim duration, then
   waits for that interval before the next step. An empty light list never
   aborts the sequence (the step loop still runs).

### Lights switched on during the night

If a light from the Lights list is switched on while the night is active, its
index is added to the touched list and it is set to the night color — unless a
configured restore is less than ten minutes away. Lights that turn off during
the night **stay in the touched list**; this is what makes the white restore
possible in the morning.

### Restore (C2)

### Sunrise handover

The **Sunrise lights** are ordinary night-mode lights until the handover: they
are dimmed red and tracked like every other light. The handover happens at
`sunrise_handover_time` (default 05:30) or when the selected sunrise automation
starts (`automation_triggered`), whichever comes first. It removes the sunrise
light indices from the touched and pending lists and clears their manual
control, while the rest of the lights **stay in night mode**. The sunrise
automation then owns their color and brightness.

The night ends at one of these triggers:

- `night_mode_restore` event,
- the fixed restore time (if configured),
- real sunrise (only when no sunrise automation is selected).

The restore sequence is deliberately ordered so a failing light command can
never leave Adaptive Lighting paused:

1. Active helper off, dim step 0.
2. `adaptive_lighting.set_manual_control` clears manual control and the profile
   switches turn on again (or sleep mode is disabled).
3. For every light in the touched list:
   - **on** at restore → set to the restore color temperature (default 2700 K)
     and brightness (default 100 %) with a short transition (default 2 s),
   - **off** at restore → its index goes into the pending list. The light is not
     switched on now. The next time it is switched on, it is set to white
     instead of red and the index is removed from the pending list.
   - Lights already handed over to the sunrise automation are no longer in the
     touched list and are therefore skipped here.
4. Touched list cleared, `night_mode_restored` event fired.

This is the C2 strategy: no light is switched on just to restore its color, but
no light comes back red either.

### Restart during the night

On Home Assistant startup the automation checks the active helper. If it is
still on, the night is considered over: both index helpers and the dim step are
reset, manual control is cleared, sleep mode (if used) is turned off and the
profile switches turn on. Adaptive Lighting is never left paused indefinitely.

## Manual control

Fire an event from any automation, script or button:

```yaml
action: event.fire
data:
  event_type: night_mode_start
```

```yaml
action: event.fire
data:
  event_type: night_mode_restore
```

Alternatively, call `automation.trigger` on the created automation. To abort
dimming without a full restore, turn `input_boolean.night_mode_active` off; the
dim loop checks this helper before each step.

## Migration from rig-for-red

| rig-for-red setting | Blueprint input |
| --- | --- |
| `lights` | Lights |
| `schedule_days`, `schedule_time` | Days of week, Start time |
| `dim_duration_minutes`, `min_brightness_pct` | Dim duration, Minimum brightness |
| `rgb_preset`, `rgb_custom` | Night color, Custom RGB color |
| `restore_at_sunrise: true` | Restore mode: At sunrise |
| `restore_at_sunrise: false`, `restore_time` | Restore mode: At a fixed time, Fixed restore time |
| `adaptive_lighting_switches` | Adaptive Lighting profile switches |
| `al_sleep_mode: true` | Use Adaptive Lighting sleep mode (+ sleep-mode switches) |
| `enable_debug_logging` | Not available; use Home Assistant's logger |

`rig_for_red.trigger_rig` / `rig_for_red.restore_lights` become
`night_mode_start` / `night_mode_restore` events. The `sensor.rig_for_red_state`
entity is replaced by the helper states and the `night_mode_started` /
`night_mode_restored` events.

## Known limitations

- No second scheduler lives in Adaptive Lighting; the weekly schedule is part
  of the automation. This keeps the change upstream-friendly.
- The touched/pending lists use **indices**, not entity IDs. If you reorder the
  Lights input after a night started, the indices point at different lights.
  Both helpers are cleared on activation and on restore, so the risk is limited
  to an active night.
- Lights that are `unavailable` are skipped by the white commands
  (`continue_on_error`). They are restored on their next turn-on via the
  pending list.
- Do not run this at the same time as the `adaptive_lighting.sunrise` service;
  use the **Sunrise automation** input instead so the morning automation has
  priority.
- The restart behavior always ends the night; it does not resume a partially
  completed dim sequence. This is intentional and documented.

## Verification

1. Trigger `night_mode_start` manually and watch the step helper count 1–10.
2. Turn the active helper off mid-dim and confirm the loop stops.
3. Switch a light off before activation, then on again: it turns red (unless a
   restore is imminent).
4. Fire `night_mode_restore` and confirm 2700 K / 100 %, manual control cleared
   and profile switches on. A light that was off at restore must come back
   white, not red, the next time it is switched on.
5. Start the selected sunrise automation while the night is active and confirm
   the sunrise lights are handed over (helper indices removed, no red override)
   while the other lights stay in night mode.
6. Restart Home Assistant with the active helper on and confirm all Adaptive
   Lighting switches end up on and manual control is empty.
