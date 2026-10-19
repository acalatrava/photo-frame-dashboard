# Home HQ: audit and verification status

Frame: AEEZO / AiMOR PF1007L, Allwinner A33, Android 6.0.1 (ARMv7), 1280x800 touch, light sensor `LTR-C216R-14`,
no PIR, no working microphone, system WebView updated to 106, root over ADB, Home HQ as the Home app.

## Findings that shaped the design

- **Security (vendor).** The AiMOR app accepts remote root commands from the vendor server (TCP 7806, unencrypted), the
  `com.yhk.qeota` updater can install APKs and `com.DeviceTest` has an unprotected receiver. See
  [aimor-remote-root-shell.md](aimor-remote-root-shell.md). **Nothing was disabled or blocked on this frame**: ADB here is
  only temporary (`persist.sys.usb.config` is `mass_storage`), so disabling AiMOR could lock you out. The frame is
  still off Wi-Fi. Do the lockdown (section 8 of that document) before it joins your network.
- **Incident during testing.** `adb install -r` removed the preferred Home app, and a later `am force-stop com.wesbos.homehq`
  made Android start AiMOR as Home (14:03). AiMOR enabled Wi-Fi, the frame joined the saved network "Casa" and AiMOR opened
  its connection to the vendor server (52.202.24.174:7806) for about 9 minutes, until it was contained at 14:12 (vendor
  ports blocked with iptables, AiMOR force-stopped, Wi-Fi off, Home HQ set as Home again). No new APKs appeared in
  `/data/app` and the logs show no vendor action, but the channel gives the vendor root, so treat the frame as exposed
  for that window. The iptables rule lives in memory only. If you want to be certain, check the frame and do the lockdown.
- **Android 6 limits.** The screen can only be turned off for real through a device administrator (`lockNow`); a partial wake
  lock is needed to keep the CPU, Wi-Fi and light sensor alive meanwhile. The minimum backlight is clamped to 10/255.
- **Light sensor.** One lux value, no direction, reports on change only (a 1 Hz tick feeds the detector). It reports duplicates
  about 1 lux apart in the same millisecond. It can only be a rough "activity" signal.
- **Soft keyboard.** About half of the screen and it does not resize the window, so the dashboard lifts the focused field.
- **Time.** The frame's time zone was Europe/Brussels; set to Europe/Madrid. The dashboard formats with `Intl.DateTimeFormat`
  in the zone configured on the server, from the frame's own clock, and warns when it differs from the server by over 2 minutes.

## Verification status

Labels: **implemented** (code exists), **auto-tested** (unit/integration tests, mocks allowed), **real-service tested**
(against the real service), **hardware tested** (on the real frame), **pending validation**.

| Area | Status | Evidence / limits |
| --- | --- | --- |
| Backend API, auth (JWT cookies, refresh rotation and reuse detection), pairing, per-device tokens, config validation, SSE | auto-tested | 48 pytest tests. |
| Backend on Docker host (`ssh docker`, `/root/HomeHQ`), `/health`, volumes, restart policy | real-service tested | Running healthy on port 8787. |
| mDNS announcement `_homehq._tcp` | real-service tested | Seen from a Mac with `dns-sd -B` using the host-network override. The frame itself has not discovered it (no Wi-Fi yet). |
| Photo upload, HEIC to JPEG, thumbnails, per-device album | auto-tested; hardware tested for display | Slideshow images from the backend rendered on the frame. HEIC only with the generated test files. |
| Home Assistant REST/WebSocket, authorization, reconnection | auto-tested (mock HA) | **Not tested against a real HA.** |
| Shopping (local, HA `todo`, offline queue, conflict policy) | auto-tested (mock HA); browser-tested | Not tested with a real Alexa list. Availability of the Alexa list in HA for Spanish accounts is unverified. |
| Calendar ICS | auto-tested; browser-tested with a local ICS | CalDAV, real providers and DST on a real calendar are pending validation. |
| Spanish localization, `Europe/Madrid`, Monday week start, 24 h | hardware tested (screenshots of the frame) | 168 i18n keys with a coverage check. DST transitions only via tests. |
| Dashboard in the bundled APK, WebView 106 | hardware tested | Loads from `appassets.homehq.invalid`, no remote server needed. |
| Pairing with admin approval on the frame | hardware tested | Over `adb reverse` (temporary, testing only). |
| Offline start with cache, "last known state", auto-reconnect | hardware tested | Link cut and restored with `adb reverse --remove`. Mobile-style network flapping not tested. |
| Light-sensor reading, telemetry upload, graph data | hardware tested | Real lux values reach the backend. |
| `ActivityDetector` logic | auto-tested | Synthetic data only, including the sensor's 1 lux flicker. Defaults lowered to 2.5 lux / 5 % after the first hardware report that a finger did not register; **still to be confirmed on the frame**. |
| Screen `black`, touch wake, `off` through device admin, wake command with sensor alive | hardware tested | Details in [light-sensor.md](light-sensor.md). Wake by light activity itself was not exercised (no way to change the light from here). |
| Autostart at boot as Home | pending validation | Home app set before; a reboot was not done here (reboots hang on some of these units, see the setup guide). |
| Frame on Wi-Fi, paired with the backend, lockdown of AiMOR/qeota/DeviceTest | hardware tested | Packages disabled (`pm list packages -d`) and APKs backed up in `backups/vendor-apks/`. A router rule blocking `imsconnect.efercro.com` is still recommended (the iptables rule is in memory only). mDNS discovery on the frame is not verified. |
| Chores (per person, per day, offline queue) | auto-tested; browser-tested | Not yet used on the frame with real chores. |
| Blinds (`cover.*`) and entity name/icon/colour customisation | auto-tested (mock HA); browser-tested | **Not tested against a real HA or real blinds.** |
| Cameras: Frigate, Home Assistant camera, image URL (MJPEG relay) | auto-tested (mock Frigate and mock HA); browser-tested | **Not tested against a real Frigate or real cameras**; frame WebView playback of the stream is untested. |
| HTTPS, `Secure` cookies | pending validation | `HOMEHQ_COOKIE_SECURE=auto` by default: on plain HTTP the cookies are not `Secure`. |
| Screen order (`general.nav_order`), calendar week/month week numbers, Today lanes with "see all" | auto-tested (order); browser-tested; hardware tested (rail order and Today) | The calendar views were checked in the browser with demo data, not on the frame. |
| Admin panel redesign | browser-tested | Checked in Overview, Screens and Chores; the other pages share the same styles. |
| Automatic return from Android settings (5 minute alarm) | hardware tested | Opened Android settings from the frame's *Ajustes* and Home HQ came back by itself at the five minute mark. |
