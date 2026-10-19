# Home HQ: light sensor as an "activity" detector, and screen control

The PF1007L has a light sensor (`LTR-C216R-14`, reported by Android as `LTR-C216R-14 sensor LIGHT`) and **no**
presence (PIR), camera or working microphone. A change in ambient light (a person walking by, a lamp, a shadow) can
hint that something is happening in the room, but it cannot tell a person from a cloud. Home HQ therefore emits
`activity_detected` and never `person_detected`; the UI says "actividad", not "presencia".

## Detector (`ActivityDetector.java`)

Runs on the frame, one sample per second (the sensor only reports on change, so a 1 Hz tick feeds the last value).

1. Smoothing: exponential and time weighted, time constant 0.6 s.
2. Adaptive baseline: exponential (15 s) that follows the room's normal light. It does not learn while the
   smoothed value is outside the threshold and learns 8 times slower while activity is flagged.
3. Trigger: the smoothed value has to leave the baseline by more than `max(min_abs_lux, min_rel_change x baseline)`
   (2.5 lux and 5 % by default). The absolute floor dominates in dark rooms, the relative one in bright rooms.
   On the PF1007L the sensor reports whole lux (about 61 with a 1 lux flicker in a lit room), so a finger or a shadow
   close to it has to move the reading by about 3 lux. The first defaults (8 lux and 25 %) needed almost covering
   the sensor; frames that still had those exact defaults are migrated automatically, custom values are kept.
4. Debounce: the change must last 250 ms. `min_event_gap_s` (2 s) limits the event rate.
5. Hysteresis and hold: the activity flag ends only when the offset falls under half the threshold **and**
   `activity_hold_s` (45 s) has passed since the last trigger.
6. A sustained offset (a lamp that stays on, the sun coming out) is a new normal: after 25 s the baseline is re-seated
   and the flag ends, so it does not keep the screen awake forever.

Sensitivity `low`, `medium`, `high` scales the thresholds by 1.8, 1 and 0.55. Everything is configurable per frame in the
admin panel (*Marcos > frame > Presencia / actividad*) and can be overridden for a test from the frame's settings.

## What the screen does

Priority when deciding whether the screen may sleep: **real Home Assistant presence > light activity > schedule
(inactivity timer, night mode) > manual**. A touch always wakes the screen, and the touch that wakes it is not
passed to the UI. Options per frame (`screen_off`): `never`, `black`, `off`.

Measured on a real PF1007L (Android 6.0.1):

| Mode | How | Result |
| --- | --- | --- |
| `black` | black overlay and window brightness 0 | Display stays on, backlight at the system minimum (clamped to 10/255, so a faint glow remains), touch wakes it, light sensor keeps reporting. |
| `off` | `DevicePolicyManager.lockNow()` (needs the device administrator) plus a partial wake lock | Display really off (`Display Power: state=OFF`), CPU and Wi-Fi stay up, light sensor and telemetry keep reporting, `wake` command from the backend turns it on with no keyguard. Touch does not wake a screen that is really off. |

Without the device administrator the app falls back to `black`. Activate it once:

```sh
adb shell dpm set-active-admin com.wesbos.homehq/.AdminReceiver
```

The partial wake lock draws a little more power than a normal sleeping tablet; a wall frame is on mains power.

## Calibration

1. Admin panel > *Sensor de luz*: the live graph shows lux, baseline and activity for the selected frame (samples are
   uploaded every 5 seconds).
2. *Iniciar grabación* records a CSV (time, lux, baseline, active) on the server (`data/recordings`). Walk past the
   frame, switch lamps on and off, let the sun move, then stop and download the CSV.
3. Raise `min_abs_lux` / `min_rel_change` or lower the sensitivity if the screen wakes by itself (a dim room with a
   flickering lamp); lower them if it does not react.

On the frame itself, the sensor section of *Ajustes* shows the current lux, the baseline, the activity state and the same graph.

## Known limits

- Sensor values reported in this unit's room: about 61 lux in daylight indoors, with two near-simultaneous readings that
  differ by about 1 lux; the app keeps the first of each pair.
- The detector was validated against synthetic data and on-device only at rest. Its real-world thresholds still need a
  calibration session in your room.
- A static person is invisible to it: the activity state expires after `activity_hold_s`.
