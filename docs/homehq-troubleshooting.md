# Home HQ: troubleshooting

| Symptom | Check |
| --- | --- |
| The frame asks for the server on every start | The token is stored in the app's private preferences. `adb shell pm clear com.wesbos.homehq` or "unpair" deletes it. A frame removed from *Marcos* also returns to setup. |
| "No se puede cargar el panel" screen | Only appears when a custom `--es url` was launched. Reload with the two-finger long press, or start the app again without extras. |
| Setup cannot reach the backend | The frame must be on Wi-Fi (two-finger hold > *Ajustes Wi-Fi*). Test `curl http://SERVER:8787/health` from another machine. Docker publishes the port; on a firewall allow TCP 8787. |
| No server in the discovery list | mDNS needs host networking: [homehq-install.md](homehq-install.md). Typing the address always works. |
| The pairing code is rejected | Type the code shown *now* on the frame. Codes expire after 10 minutes and are rate limited. |
| Admin login fails or loops | Cookies are `SameSite=Strict`. Open the panel at the same address you log in at. With `HOMEHQ_COOKIE_SECURE=true` the panel must be served over HTTPS. Login is limited to 8 attempts per 15 minutes per client. |
| Clock "differs X min from the server" in *Ajustes* | The frame's own clock is off. Fix its time (`adb shell date`, or enable network time). The dashboard uses the frame clock with the configured time zone. |
| Photos do not appear | The frame needs an album (*Marcos > frame > Fotos*). Upload JPEG, PNG, WebP or HEIC in *Fotos*; HEIC is converted to JPEG. |
| Home Assistant says "Sin conexión" | *Home Assistant > Probar conexión*. Check URL, token and TLS. The dashboard keeps the last state until it reconnects. |
| The screen wakes by itself | Lower the sensitivity or raise `min_abs_lux`, record a calibration ([light-sensor.md](light-sensor.md)). Flickering lamps and TV light cause activity. |
| `off` mode behaves like `black` | The device administrator is not active: `adb shell dpm set-active-admin com.wesbos.homehq/.AdminReceiver`. |
| Typing hides the field | The keyboard covers half of the screen; the dashboard lifts the focused field. If it does not, reload the app. |
| Stuck in Android settings | The frame has no Back or Home button. Home HQ returns by itself 5 minutes after it opens an Android screen. To return sooner from a computer: `adb shell input keyevent KEYCODE_HOME`. |
| After a restart ADB no longer connects | USB ADB is temporary on these frames (`persist.sys.usb.config=mass_storage`). Make it persistent beforehand with `setprop persist.sys.usb.config mass_storage,adb` (USB only), see [pf1007l-start-here.md](pf1007l-start-here.md). |
| "Instalación bloqueada" when updating the app | The frame lacks the secure-settings grant: `adb shell pm grant com.wesbos.homehq android.permission.WRITE_SECURE_SETTINGS`. More in [homehq-updates.md](homehq-updates.md). |
| An event is in nobody's column on Today | It has no person: its calendar is linked to nobody and its notes carry no `@user:name` tag. That is the intended meaning of a family event; it shows in the next-up card and in the calendar. Link the calendar to people, or tag the event. |
| An `@user:` tag does nothing | The name must match a person's id, name or first name (case and accents do not matter) and the calendar must have synced since. An unknown name is ignored. Check *General* for the exact names. |
| An emoji shows as an empty box | Frames before version 3.0 use the Android 6 system font, which stops at Unicode 8; update the app ([homehq-updates.md](homehq-updates.md)). From 3.0 on the frame has its own emoji font. |
| Backend does not start | `docker compose logs homehq`. `HOMEHQ_SECRET_KEY` must be a valid Fernet key (32 url-safe base64 bytes) or empty. |

Logs: `data/logs/homehq.log` (rotating). On the frame: `adb logcat -s HomeHQ chromium`. Remote WebView debugging is off by default;
turn it on only while debugging with `adb shell am start -n com.wesbos.homehq/.MainActivity --ez debug true`.
