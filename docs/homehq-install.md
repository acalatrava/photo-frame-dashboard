# Home HQ: install, configuration, backups and updates

## 1. Backend (Docker)

```sh
cp .env.example .env          # optional, every variable has a default
docker compose up -d --build
docker compose logs homehq | grep -i password   # first start only
```

Open `http://<server>:8787/admin/`, log in as `admin` and change the password when asked. If
`HOMEHQ_ADMIN_PASSWORD` is empty the initial password is random: it is printed once in the log and written to
`data/secrets/initial-admin-password.txt`. Delete that file after the first login.

The `data/` volume holds everything: `db/` (SQLite), `photos/`, `secrets/` (master key), `recordings/`, `logs/`
(rotating, 2 MB x 5). The container runs as an unprivileged user, restarts on its own
(`restart: unless-stopped`) and exposes `GET /health` (also the Docker healthcheck).

To use another host port set `HOMEHQ_PORT` in `.env`.

### Automatic discovery (mDNS)

Multicast does not cross Docker's bridge network. To let frames find the backend by themselves use host networking:

```sh
docker compose -f docker-compose.yml -f docker-compose.mdns.yml up -d
```

The service then listens on the host's port 8787 and announces `_homehq._tcp`. Check it from a Mac with
`dns-sd -B _homehq._tcp`. Without it the frame still works: type the address by hand during setup.

### HTTPS

Put a reverse proxy (Caddy, Traefik, nginx) in front, forward `X-Forwarded-Proto` and `X-Forwarded-For`, then set
`HOMEHQ_TRUST_PROXY=true` and `HOMEHQ_COOKIE_SECURE=true`. Frames accept `http://` or `https://` backend addresses.

## 2. Environment variables

| Variable | Default | Meaning |
| --- | --- | --- |
| `HOMEHQ_PORT` | `8787` | Host port published by compose. |
| `HOMEHQ_ADMIN_USER` / `HOMEHQ_ADMIN_PASSWORD` | `admin` / random | Initial admin account (created once). |
| `HOMEHQ_SECRET_KEY` | generated | Base64 Fernet key for stored secrets. Empty: `data/secrets/master.key`. |
| `HOMEHQ_COOKIE_SECURE` | `auto` | `auto`, `true` or `false`. See the security note in [homehq-architecture.md](homehq-architecture.md). |
| `HOMEHQ_TRUST_PROXY` | `false` | Trust `X-Forwarded-*` headers. Only behind a proxy you control. |
| `HOMEHQ_CORS_ORIGINS` | empty | Extra allowed browser origins, comma separated. |
| `HOMEHQ_MDNS_ENABLED` | `false` | Announce `_homehq._tcp` (needs host networking). |
| `HOMEHQ_ACCESS_TOKEN_MINUTES` / `HOMEHQ_REFRESH_TOKEN_DAYS` | `15` / `7` | Admin session lifetimes. |
| `HOMEHQ_PAIRING_TTL_SECONDS` | `600` | Validity of a pairing code. |
| `HOMEHQ_PHOTO_MAX_UPLOAD_MB` | `40` | Largest accepted photo. |
| `HOMEHQ_LOG_LEVEL` | `INFO` | Log level. |

## 3. Android app

Build (needs JDK 17 and Android build-tools; see [building-for-the-frame.md](building-for-the-frame.md)):

```sh
cd dashboard && npm ci
cd kiosk
ANDROID_HOME=$HOME/Library/Android/sdk BUILD_TOOLS=$ANDROID_HOME/build-tools/36.0.0 ./build.sh
adb install -r build/homehq.apk
```

`build.sh` builds the dashboard with Vite and packs it into the APK (`assets/app`).

> **Warning, PF1007L:** `adb install -r` clears the "always open Home HQ as Home" choice. Until you set it again,
> pressing Home or force-stopping the app starts **AiMOR**, which turns Wi-Fi on and connects to the vendor's
> command server (TCP 7806). Right after every install run
> `adb shell am start -a android.intent.action.MAIN -c android.intent.category.HOME`, tap **Home HQ** and
> **Siempre** on the frame, and keep the vendor ports blocked (see [aimor-remote-root-shell.md](aimor-remote-root-shell.md))
> or AiMOR disabled. Do not use `am force-stop com.wesbos.homehq` on a frame that has Wi-Fi.

Make Home HQ the Home app: `adb shell am start -n com.wesbos.homehq/.MainActivity --ez home true`, then the chooser
above (Android 6 has no `cmd package set-home-activity`).

If a previous setup saved another dashboard URL, the app keeps loading it. Go back to the bundled dashboard with
`adb shell am start -n com.wesbos.homehq/.MainActivity --es url app`.

Put the frame to sleep for real (optional, see [light-sensor.md](light-sensor.md)): enable the device administrator once,

```sh
adb shell dpm set-active-admin com.wesbos.homehq/.AdminReceiver
```

Then follow [homehq-pairing.md](homehq-pairing.md). Set the frame's time zone with
`adb shell setprop persist.sys.timezone Europe/Madrid`; the dashboard itself always formats time with the zone
configured in the admin panel, using the frame's own clock.

## 4. Backups

Stop nothing: SQLite runs in WAL mode, so copy the database consistently:

```sh
docker compose exec homehq python -c "import sqlite3; s=sqlite3.connect('/data/db/homehq.sqlite3'); d=sqlite3.connect('/data/db/backup.sqlite3'); s.backup(d)"
tar czf homehq-$(date +%F).tgz data/db/backup.sqlite3 data/photos data/secrets
```

Keep `data/secrets/master.key` with the database: without it the Home Assistant token and calendar passwords
cannot be decrypted (you would just enter them again). Restore by putting the files back into `data/` and
starting the container.

## 5. Updating

```sh
git pull
docker compose up -d --build     # add the -f override if you use mDNS
```

Alembic migrations run on start. Back up first. After a backend update the frame keeps working.

After an app update the frames can install it over the network, with no cable: build with `kiosk/build.sh`, publish
with `kiosk/publish.sh --publish` (or in the panel under *Updates*), and tap **Instalar** on the frame. See
[homehq-updates.md](homehq-updates.md). The first install of an update-capable build, and any frame that has not
been given the `WRITE_SECURE_SETTINGS` grant, still use `adb install -r`. Pairing and the offline cache survive
reinstalls.
