# Home HQ: user guide

Home HQ is a family dashboard for Android photo frames (built and tested on the PF1007L / AiMOR, Android 6,
1280x800). It has two parts:

- **The frame**: an Android app that shows the dashboard full screen. The dashboard is bundled in the app, so it
  starts without the network.
- **The backend**: a small Docker service with an admin web panel. It holds the photos, the calendars, the chores and
  every secret (Home Assistant token, calendar passwords). The frame never stores any of them.

This page explains what you see on the frame, what you can configure in the panel, and how the pieces behave.
For installation see [homehq-install.md](homehq-install.md); for how it is built, [homehq-architecture.md](homehq-architecture.md).

## The frame, screen by screen

The side rail on the left lists the screens. **Today** is always first and **Settings** is always last, next to the
clock. The screens in between (calendar, photos, chores, house, cameras, shopping) follow the order you choose in the
panel. Chores and cameras only appear when something is configured for them.

### Today (*Hoy*)

- The clock, the date, the weather (current conditions, next hours and a one-line hint) and who is at home.
- A hero card with the next event ("A continuación") and a countdown, or the first event of tomorrow when today is over.
- One lane per person (two to four columns, depending on how many people are configured). Each lane shows that
  person's events for the rest of the day and their pending chores. Tap a chore to tick it; a toast offers *Deshacer*.
  When there is not enough room, a **+N más · ver todas** button opens the chores screen. A person with no events and
  no chores sees "Libre el resto del día".
- A photo card, a chores progress card (a ring and one counter per person), the shopping list and the house status.

### Calendar (*Calendario*)

Day, three days, week and month views, all starting on Monday.

- **Week** is the calendar week (Monday to Sunday), not the next seven days, and the title shows the ISO week number
  ("Semana 43").
- **Month** has a week-number column and the current day is a strong coloured cell.
- In the week view the current day is a tinted column. The *Hoy* button jumps back to today.
- Events are coloured by person. Events with no person are shown for everyone.

### Photos (*Fotos*)

A slideshow of the album assigned to the frame, with a date and caption overlay if enabled. After a configurable idle
time the frame goes to the photos (ambient mode); a touch brings it back to Today.

### Chores (*Tareas*)

A grid with one card per chore and one tick box per assigned person, for today and yesterday. Ticks work offline: they
are queued on the frame and sent when the connection is back. See [homehq-chores-cameras.md](homehq-chores-cameras.md).

### House (*Casa*)

Home Assistant entities you authorised: lights, switches, scenes, blinds (open, close, stop) and sensors, with the
names, icons and colours you chose. Offline it shows the last known state and disables the controls.

### Cameras (*Cámaras*)

Live view of Frigate, Home Assistant or plain image-URL cameras. The backend takes the pictures and relays them to the
frame as MJPEG; the frame never connects to the camera system directly.

### Shopping (*Compra*)

The shopping list, either local to the server or a Home Assistant `todo.*` list (for example the Alexa list).
Changes made offline are queued and replayed in order; the conflict policy is in [shopping.md](shopping.md).

### Settings (*Ajustes*)

Connection state, display and screen-off mode, the light-sensor activity graph with its sensitivity switch (low,
medium, high), the app, WebView and device versions, a **Sync now** button, a long-press button to unpair and an
**Android** button for the system settings.

## Touch gestures on the frame

| Gesture | What it does |
| --- | --- |
| Tap anywhere on a black or dimmed screen | Wakes it. |
| Two fingers held still for 1.5 s | Opens the maintenance menu: open the launcher, Android settings, Wi-Fi settings, reload the panel. |
| Hold *Mantén pulsado para desvincular* for 1.5 s | Unpairs the frame from the server. |

### Getting out of Android settings

The frame has no Back or Home buttons. Whenever Home HQ opens an Android screen (the **Android** button in Settings,
or the menu entries for Android settings and Wi-Fi), it schedules an automatic return and shows the message
"Volverás a Home HQ automáticamente en 5 minutos". Five minutes later Home HQ comes back to the front by itself, even
if Android reclaimed the app's memory in the meantime. If you come back sooner (for example you finished and the
screen went back through another route), the pending return is cancelled. Do your Wi-Fi or settings change within
those five minutes; open the screen again if you need more time.

From a computer, `adb shell input keyevent KEYCODE_HOME` takes the frame straight back.

## The admin panel

Open `http://<server>:8787/admin/`. The first login uses `HOMEHQ_ADMIN_PASSWORD` from `.env` (a random one is generated and logged on first start if it is empty) and asks you to change it. The panel
is in Spanish or English (button at the bottom of the side bar) and follows the system's light or dark theme.

| Section | What it is for |
| --- | --- |
| **Resumen** | Health at a glance: Home Assistant, weather, number of paired frames, server version, calendar sources. |
| **Marcos** | Pair new frames (type the six digit code the frame shows) and edit each one: name, room, language, brightness and night mode, screen-off mode, presence (light sensor and/or Home Assistant), photo album and slideshow options, start view, idle timers and which people it shows. Commands: wake, sleep, reload, identify, revoke. |
| **Pantallas** | The order of the side rail. Up and down buttons for the middle screens; Today first and Settings last are fixed. The order is global and the frames apply it as soon as they receive the configuration. |
| **Fotos** | Albums, drag and drop upload (JPEG, PNG, WebP, HEIC), captions (double-click a photo), delete. |
| **Calendarios** | ICS or CalDAV sources, owners, refresh interval, *Sync now*. |
| **Tareas** | Chores: title, icon, time, who does it, weekdays and week pattern (every week, even weeks, odd weeks, every N weeks from a start date). |
| **Compra** | Local list or a Home Assistant `todo.*` list. |
| **Cámaras** | Frigate address and detection, Home Assistant cameras, image URLs, preview. |
| **Home Assistant** | URL, long-lived token (stored encrypted, never shown again), TLS check, test connection, authorised entities and their customisation. |
| **Sensor de luz** | Live lux reading and calibration recordings (CSV download). |
| **General** | Language, time zone, location for the weather, and the people (name, colour, optional `person.*` entity for presence). |
| **Cuenta** | Change the admin password. |

Changes reach connected frames immediately over a live connection, with no restart.

## Several frames

Everything that belongs to one frame (display, presence, photos, start view, people shown) is stored per frame.
Everything shared (language, time zone, people, calendars, chores, Home Assistant, cameras, screen order) is global.

## What stays safe

- The admin session uses short-lived tokens in `HttpOnly` cookies with refresh rotation and reuse detection; logout
  revokes the refresh token. See the security model in [homehq-architecture.md](homehq-architecture.md).
- A frame only works after an administrator approves its pairing code, and its token can be revoked at any time.
- On the PF1007L the vendor apps (AiMOR, qeota, DeviceTest) must stay disabled. They accept remote commands from the
  vendor's servers; read [aimor-remote-root-shell.md](aimor-remote-root-shell.md).

## Restarting the frame

The frame boots into Home HQ because it is the only enabled Home app. After a restart it reconnects to Wi-Fi, shows the
cached data while it syncs and continues. Before restarting, check these:

1. `adb shell pm list packages -d` still lists the vendor apps as disabled (that setting survives restarts).
2. Home HQ is the only app that answers the Home intent.
3. USB ADB is only temporary on these frames (`persist.sys.usb.config` is `mass_storage`), so a restart ends
   your ADB access. If you want to keep it, `setprop persist.sys.usb.config mass_storage,adb` makes USB ADB persistent
   (USB only, never the Wi-Fi variant). See [pf1007l-start-here.md](pf1007l-start-here.md).
4. `adb reboot` hangs on many of these units; unplug the power for a few seconds instead.

## Where everything else is documented

| Topic | Document |
| --- | --- |
| Install, variables, backups, updates | [homehq-install.md](homehq-install.md) |
| Pairing a frame | [homehq-pairing.md](homehq-pairing.md) |
| Home Assistant and the Alexa list | [homehq-homeassistant.md](homehq-homeassistant.md) |
| Chores, cameras, Frigate, screen order | [homehq-chores-cameras.md](homehq-chores-cameras.md) |
| Light sensor and screen control | [light-sensor.md](light-sensor.md) |
| Shopping conflicts | [shopping.md](shopping.md) |
| Kiosk app | [../dashboard/kiosk/README.md](../dashboard/kiosk/README.md) |
| Problems | [homehq-troubleshooting.md](homehq-troubleshooting.md) |
| What was really tested | [homehq-audit.md](homehq-audit.md) |
