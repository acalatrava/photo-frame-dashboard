# Home HQ: architecture

Home HQ turns the PF1007L (and similar Android 6 frames) into a family dashboard that talks to a small
backend in your home. The frame never holds a secret: Home Assistant tokens, calendar passwords and the
admin account live only in the backend.

```
 Browser (admin panel, /admin)          Frame 1 .. N (Android app + bundled dashboard)
        |  cookies HttpOnly+SameSite            |  Bearer device token (opaque, per frame)
        v                                       v
 +--------------------------------------------------------------+
 |  Backend (FastAPI, SQLite, Docker)                           |
 |  admin API  | device API + SSE | media (signed URLs) | /health |
 |  services: config, photos, calendar, weather, shopping,      |
 |            chores, cameras (MJPEG relay), Home Assistant     |
 |            (REST + WebSocket), presence                      |
 +-----------------------------+--------------------------------+
                               |
              Home Assistant (REST + WS), Frigate, ICS/CalDAV, Open-Meteo
```

## Components

| Part | Where | Notes |
| --- | --- | --- |
| Backend | `backend/` | Python 3.12, FastAPI, SQLAlchemy 2 on SQLite (WAL), Alembic migrations, Pillow + pillow-heif. |
| Admin panel | `backend/app/static/admin` | Spanish and English. Overview, frames and pairing, screen order, photos, calendars, chores, shopping, cameras, Home Assistant, light sensor, general settings, account. |
| Dashboard | `dashboard/` | Vite app with a fixed 1280x800 stage, touch first. Bundled in the APK, so the frame starts without the network. |
| Android app | `dashboard/kiosk/` | Kiosk WebView, no Gradle. Serves the bundle at `http://appassets.homehq.invalid/`, exposes the `HQNative` bridge only to that page. |

## Chores, cameras and screen order

- Chores are global definitions (title, people, weekdays, week pattern). The ticks live in the `chore_log` table, one row
  per chore, person and local day. Frames queue ticks offline and the backend only accepts today and yesterday.
- Cameras are global too. The backend fetches Frigate, Home Assistant or URL images and relays them as MJPEG through
  signed URLs, so the frame never talks to the camera system. The relay stops when nobody is watching.
- `general.nav_order` is the order of the side rail. The server normalises it (unknown screens are rejected, missing ones are
  appended) and frames apply it on every configuration update. Today first and Settings last are enforced by the frame.
- The calendar views and the Today lanes are laid out by the frame from the data it already has; there is no extra
  endpoint for them.

## Several frames

Everything that is per frame lives in `DeviceConfig`: display and brightness, presence behaviour, photo album
and slideshow options, main view and ambient timers, language, room name. Global settings (language,
time zone, people, calendars, Home Assistant, shopping) are shared. Each frame has its own token, album,
telemetry ring buffer and sensor recordings.

## Security model

- Admin: username and password (argon2), 15 minute access JWT and 7 day refresh token, both in
  `HttpOnly`, `SameSite=Strict` cookies. Refresh tokens rotate; reusing an old one revokes the whole
  family. Logout revokes the refresh token in the database and clears both cookies. Non-GET requests need
  the `X-HomeHQ-Admin: 1` header (CSRF). Rate limited login.
- Frames: pairing needs an admin to type the six digit code shown on the frame. The resulting token is
  random, stored hashed (SHA-256) and can be revoked from the panel. Photos are served through URLs signed
  with a per-frame secret; the signature is stable so the WebView can cache the images, and removing the
  frame invalidates it.
- Secrets (Home Assistant token, calendar passwords) are encrypted with a Fernet key in `data/secrets`
  and never returned by any API.
- CORS only allows the kiosk origin plus `HOMEHQ_CORS_ORIGINS`.
- The `Secure` cookie flag follows the request by default (`HOMEHQ_COOKIE_SECURE=auto`): it is set when the
  request arrived over HTTPS. A plain-HTTP LAN install therefore sends the cookies without `Secure`;
  put the panel behind HTTPS and set `HOMEHQ_COOKIE_SECURE=true` as soon as you can.

## Data flow on the frame

1. The bundle reads the saved backend address and device token from native private preferences (not from
   `localStorage`).
2. It downloads `bootstrap` (configuration) and `dashboard` (events, weather, photos, Home Assistant
   state, shopping), caches both and opens `/api/v1/device/events` (SSE) for live changes.
3. Offline, it keeps showing the cached data, marks Home Assistant as "last known state", disables controls and
   keeps shopping changes in a persisted queue that is replayed in order (policy in [shopping.md](shopping.md)).
4. The light sensor runs natively (`ActivityDetector`) and reports `activity_detected` events and a 1 Hz sample
   stream; samples are uploaded every 5 s for the diagnostics graph. See [light-sensor.md](light-sensor.md).
