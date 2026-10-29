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
| The Menú screen is missing on the frame | It only appears once the menu has at least one week (*Menú semanal* in the panel) and is not hidden in *Pantallas*. |
| The menu shows the wrong week | Set it with *Semana actual > Esta semana es la… > Aplicar*. Weeks change on Monday according to the frame's clock and time zone, so check the clock note above first. |
| An agent gets 401 or 429 from `/mcp` | 401: the token is wrong, revoked or expired (see *Agentes (MCP)*). 429: 30 wrong tokens from one address in 15 minutes; wait, or fix the token. Behind a proxy without `HOMEHQ_TRUST_PROXY=true` every client shares the proxy's address. |
| An agent gets 403 on publishing or deleting an APK, creating tokens or changing the password | By design: those need a logged-in panel session, not an API token ([homehq-mcp.md](homehq-mcp.md)). `kiosk/publish.sh` logs in with the admin password, so it still works. |
| Login is blocked right after changing proxy settings | The limiter counts per client address. Behind a proxy set `HOMEHQ_TRUST_PROXY=true` and `HOMEHQ_TRUSTED_PROXY_HOPS`; otherwise all users look like one address. |
| An alarm or the chime makes no sound | Check *Sonido > Volumen del marco* is above 0 and the frame is not inside the *No molestar* window. Use *Probar ahora* on the alarm. The chime is off by default. |
| Spoken text is silent | The frame has no text-to-speech engine (common on Android 6). The message is still shown. Install a TTS engine APK, then *Probar sonido y voz*. |
| `/api/v1/trigger` returns 403 | The key's scope is `read`. Use a `trigger` or `full` key. A `trigger` key is refused everywhere else, by design. |
| A trigger reports the frame under `offline` | The frame has no live connection to the server at that moment; triggers are not queued. |
| The screen turns off by itself when the light goes out | That is *Apagar la pantalla al detectar que se apaga la luz*; turn it off in *Presencia*, or lower `lights_off_lux`. |
| The Música screen is missing | It appears once Spotify is enabled and connected (*Spotify* in the panel) and is not hidden in *Pantallas*. |
| Spotify says there is no active device | Open Spotify on a speaker so it registers as a Connect device, then pick it at the top of the Música screen. |
| Backend does not start | `docker compose logs homehq`. `HOMEHQ_SECRET_KEY` must be a valid Fernet key (32 url-safe base64 bytes) or empty. |

Logs: `data/logs/homehq.log` (rotating). On the frame: `adb logcat -s HomeHQ chromium`. Remote WebView debugging is off by default;
turn it on only while debugging with `adb shell am start -n com.wesbos.homehq/.MainActivity --ez debug true`.
