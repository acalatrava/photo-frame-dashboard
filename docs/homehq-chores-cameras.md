# Home HQ: chores, cameras and Frigate

## Chores (*Tareas*)

Admin panel > *Tareas*. A chore has a title, an icon, an optional time, the people who do it and the weekdays it applies to.

- Every selected person gets **their own check** each day: "Hacer la cama" for two children is two checks. A chore
  with nobody selected is one shared check for the whole house ("Casa" column on the frame).
- No weekday selected means every day.
- **Weeks it repeats**: every week, even weeks, odd weeks, or every N weeks (2 to 12) counting from a starting week.
  Even/odd use the ISO week number (the week of 19 October 2026 is week 43, odd). ISO years with 53 weeks have two odd
  weeks in a row at the New Year, which is why *Cada varias semanas* is the reliable option for a strict alternation.
  Example: "Cambiar las sábanas", Saturday, every 2 weeks starting this week.
- The *Hoy* screen shows each person's pending chores under their calendar events; tap one to tick it (a message offers
  to undo). Shared chores only appear in the *Tareas* tab and in the counter of the *Tareas* card.
- On the frame the *Tareas* tab appears as soon as at least one chore exists. Tap a chore to tick it, tap again to undo.
  The *Hoy* screen shows how far each person is.
- Completion is stored per local day (server time zone), so every day starts clean without a reset job. Ticks are absolute
  states ("done" / "not done"): the last tap wins, even when two frames disagree. A frame that is offline queues its
  taps and replays them (today or yesterday only) when it reconnects. History older than 120 days is deleted.
- People do not need a Home Assistant account.

## Cameras (*Cámaras*)

Admin panel > *Cámaras*. Sources:

| Source | Needs | How it is fetched |
| --- | --- | --- |
| Frigate | Frigate URL (for example `http://192.168.1.10:5000`) | `GET /api/<camera>/latest.jpg` |
| Home Assistant camera | the `camera.*` entity (it is authorised automatically) | `GET /api/camera_proxy/<entity>` |
| Image URL | any JPEG snapshot URL | plain GET |

Use *Detectar cámaras de Frigate* to list the cameras and pick them from a menu, then *Vista previa* to check one.

Design: the frames never talk to Frigate or Home Assistant. The backend fetches snapshots and republishes them as a
multipart MJPEG stream from a signed per-device URL (`/media/cam/<device>/<camera>/stream`), which the WebView shows in
a plain image. Credentials stay on the server, no extra ports are opened on the frame, and every Frigate version works.
The grid refreshes a snapshot every 3 s; tapping a camera opens the live stream (1 to 10 frames per second, set per camera).
Limits: at most 8 simultaneous streams, a stream is cut after 15 minutes, and the frame leaves the stream when you
change tab or after 5 minutes. Frigate's own `Authentication` (port 8971) is not supported yet: use the unauthenticated
port 5000 from your LAN, or put the URL behind your network rules.

Status: automated tests use a mock Frigate and a mock Home Assistant; it has not been tried against real cameras.

## Orden de las pantallas

En el panel de administración, **Marcos → Pantallas**, puedes cambiar el orden de la barra lateral del marco con los botones subir/bajar. «Hoy» siempre es la primera y «Ajustes» siempre la última, pegada al reloj; el resto es libre. El orden es global (`general.nav_order`) y los marcos lo aplican al recibir la configuración, sin reiniciar.
