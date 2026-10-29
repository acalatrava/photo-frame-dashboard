# Home HQ: sound, alarms, triggers and music

Everything here is configured in the admin panel. Frame hardware behaviour (sound output, text-to-speech, the light
sensor) was written and unit-tested but has not been verified on a real PF1007L; see the status table at the end.

## Hourly chime

*Marcos > your frame > Sonido*. Turn on **Sonar a las horas en punto**, choose every hour or every half hour, and pick
the sound (chime, bell, soft, or say the time aloud). **No molestar** keeps the frame silent between two times; the
window may cross midnight (22:00 to 08:00). The master volume of the frame is the same section (it sets Android's media
volume). The chime never plays while an alarm or alert is on screen.

## Alarms

*Alarmas* in the side bar. Each alarm has a time, the weekdays (none selected means every day) or one specific date, a
sound (melody, chime, bell, soft, beep, or none), an optional message shown full screen, and **Leer el mensaje en voz
alta**. It rings on every frame unless you pick some. It stops by itself after the chosen number of seconds and has a
**Posponer** button (set the minutes to 0 to hide it). **Probar ahora** sends it to the frames immediately.

An alarm needs a sound or a message. Alarms wake the screen and stay on top until stopped.

### Speech

The frame first uses Android's text-to-speech engine, if the device has one, and otherwise the WebView's
`speechSynthesis`. Android 6 builds for these frames often ship no engine, in which case nothing is spoken and the
message is only shown. Use **Probar sonido y voz** in the frame's *Sonido* section to find out. Installing a TTS engine
APK (for example Google Speech Services) on the frame fixes it.

## Triggers (Home Assistant and scripts)

`POST /api/v1/trigger` lets an outside system act on the frames right now. Create a key in *Agentes (MCP)* with the scope
**Solo disparadores**. That scope can do nothing else: it is refused by the rest of the admin API and by `/mcp`, so a
leaked Home Assistant key cannot read or change your configuration. A `read` key is refused here; a `full` key works.

```json
{"action": "show_view", "view": "cameras", "camera": "puerta", "device": "Salón", "duration_s": 30}
{"action": "alert", "message": "Llaman a la puerta", "speak": true, "sound": "bell", "duration_s": 20}
{"action": "wake"}
{"action": "sleep"}
```

`device` is a frame id or name; leave it out for all frames. `show_view` wakes the screen, opens the view (and the
camera, when given) and keeps it there for `duration_s` seconds (0 keeps it until someone touches the frame), then goes
back to Today unless someone started using the frame. The reply says which frames received it and which are offline
(`{"sent": [...], "offline": [...]}`); an offline frame does not get the trigger later. The endpoint is limited to
120 calls per 10 minutes per address.

The *Agentes (MCP)* page shows a ready `rest_command` snippet for Home Assistant (`homehq_camera`, `homehq_aviso`).

## Screen off when the light goes out

*Marcos > frame > Presencia*, **Apagar la pantalla al detectar que se apaga la luz** (on by default). If the light
sensor falls sharply to almost nothing (below `lights_off_lux`, 10 lux by default) the frame turns its screen off. The
frame's own brightness changes are ignored for 12 seconds so it does not react to itself, and a touch in the last ten
seconds or an alert on screen prevents it. The drop does not count as activity, so it cannot wake the screen again.

## One-off chores

In *Tareas*, **Nueva tarea de una vez**. Pick the day it is due. It shows on the frame from that day and stays there,
flagged *Pendiente de antes* once the day has passed, until somebody ticks it. After it is done it disappears the next
day. With several people assigned each one has their own checkbox.

## Spotify

*Spotify* in the side bar. The frames do not play audio themselves: the backend talks to the Spotify Web API and the
frame's **Música** screen controls your Spotify Connect speakers (Echo, Sonos, Chromecast, a phone...), shows what is
playing, and lets you start a playlist or search for a song. Spotify only lets **Premium** accounts control playback.

1. Create an app at developer.spotify.com/dashboard and add `http://127.0.0.1:8787/callback` (or your https address) as its
   Redirect URI. Spotify rejects plain `http` addresses that are not loopback.
2. Paste its Client ID in the panel and save. No client secret is used (PKCE).
3. Press **Guardar y conectar**, accept the permission, and paste the address Spotify sends you to (the page does not
   load, that is fine) into the panel. The refresh token is stored encrypted; disconnecting deletes it.

Frames cannot be a Spotify speaker themselves (the Web Playback SDK needs a newer browser than Android 6's WebView).
A speaker must be awake in Spotify to appear in the list. Cover art loads straight from Spotify's CDN, so the frame
needs internet access for the pictures.

## Smoother frame

The photo cross-fade, a single bottom shade (only under a caption) and the freezes of the touch screen are covered in
[light-sensor.md](light-sensor.md) and [homehq-troubleshooting.md](homehq-troubleshooting.md). The light sensor now runs on its own
thread, status is cached natively instead of being computed on each call, and the page skips rebuilding screens when
the data has not changed. Each frame reports `long_tasks_10m`, `longest_ms` and `timer_late_ms` in its heartbeat so a
freeze can be measured.

## Verification status

| Part | Status |
| --- | --- |
| Alarm, trigger, chime and chore logic in the page | exercised in a browser with simulated clock and commands |
| Backend schema, trigger scopes, alarms, one-off chores, Spotify with a mocked Spotify | covered by automated tests |
| Lights-off detector | unit-tested with synthetic readings; not tried on the real sensor |
| Sound, native TTS, volume control on the frame | built, not run on the frame |
| Touch freeze fixes | measures added; not confirmed on hardware |
| Real Spotify account | not tried (needs your credentials) |
