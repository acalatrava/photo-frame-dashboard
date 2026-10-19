# Home HQ: updating the frame app over the network

Frames update the Android app from the backend, so a new release does not need a USB cable. You build the APK once,
upload it to the backend, publish it, and each frame offers (or downloads) it. The dashboard is bundled in the APK, so
this also ships every dashboard change.

Installing still takes **one tap on the frame**. See [Why one tap is needed](#why-one-tap-is-needed).

## Release in four steps

1. Raise the version in `dashboard/kiosk/build.sh` (`--version-code` must be higher than the last release;
   `--version-name` is only a label).
2. Build: `bash dashboard/kiosk/build.sh` (it also builds the dashboard and runs nothing on the frame).
3. Upload and publish, either from the script:

   ```sh
   cd dashboard/kiosk
   HOMEHQ_URL=http://192.168.1.177:8787 HOMEHQ_ADMIN_PASSWORD='...' ./publish.sh --publish "What changed"
   ```

   or in the panel: **Frames > Updates**, drop `kiosk/build/homehq.apk`, then press **Publish**.
4. Each frame learns about it at once (the backend sends an `update.changed` event) and otherwise within six hours.
   To move one frame now, open its editor under **Frames** and press **Update now**: the frame wakes up and opens
   the Android install dialog; tap **Instalar**.

The very first update-capable build (version code 7 or later) has to be installed with `adb install -r`, like any
build before it. From then on the frames can update themselves.

## What the frame does

**Frames > Updates > Behaviour** decides what the frames do with a published version:

| Mode | The frame |
| --- | --- |
| `off` | Ignores published versions. (**Update now** from the panel still works.) |
| `notify` (default) | Shows an orange dot on *Ajustes* and one toast per version. *Ajustes > App update* has **Download and install**. |
| `auto` | As `notify`, and also downloads and verifies the file in the background, so installing is a single tap. |

On the frame, *Ajustes > App update* shows the installed version, the published one, the release notes and the status
(downloading with a progress bar, ready, installing, or the error). Nothing is ever installed without the Android dialog.

After the installation the Android shell restarts the app by itself (it listens for `MY_PACKAGE_REPLACED`), so the
frame comes back to the dashboard without anyone touching it. If the install dialog is ignored, Home HQ returns on its
own after five minutes, as for any Android screen, and the update can be started again.

## Safety model

The backend only offers what an admin published, and only to paired frames:

- **Admin upload**: needs the admin session and the CSRF header. The backend opens the APK and rejects it unless it is a
  real APK for `com.wesbos.homehq`, has a version code, and is signed with the same certificate as the releases it
  already holds (so a frame is never sent something Android would refuse). A second upload of the same `versionCode`
  with different content is refused (`409`); the same file twice is a no-op.
- **Download**: `GET /api/v1/device/update/apk` needs the frame's bearer token. The frame passes the URL to the Android
  shell, which only accepts the backend's APK path (no other URL, scheme or host tricks).
- **Before the installer ever sees the file** the shell checks that it matches the SHA-256 the backend advertised, that
  it is this same package, that its version code is higher than the installed one, and that it is signed with the
  **same certificate as the running app**. Android's installer enforces the signature rule again, so a build signed
  with another key can never replace Home HQ.
- **Unknown sources**: Android blocks installs from outside a store unless the owner allows them. The kiosk holds
  `WRITE_SECURE_SETTINGS` (granted once with adb, see below), so it switches `install_non_market_apps` on only while the
  install dialog is opening, then puts the previous value back, 25 seconds later at the latest and again whenever the
  app comes back to the foreground or starts.
- Downloaded files live in the app's private storage and are deleted when they are no longer newer than the installed
  app.

### Signing key

`build.sh` signs with `~/.android/debug.keystore`. That works and updates are consistent as long as every release is
built with the same keystore, but a debug key is not secret. For a stronger setup create a private key and point
`build.sh` at it. Changing the key later means one `adb uninstall` and a fresh `adb install` (the pairing is lost and the
frame has to be paired again), because Android refuses to update an app with a different key. Keep a copy of whichever
keystore you use: if it is lost, no frame can be updated over the network again.

### Why one tap is needed

A normal app on Android 6 cannot install packages silently. That needs system privileges, root, or being the device
owner. The frame's `adb shell` is root, but the app is not. The options that would remove the tap were not built:
making Home HQ the device owner (it is then very hard to undo) or letting the accessibility service click the dialog
(which would mean reading other apps' windows). The tap is also the owner's confirmation that an update may happen.

## One-time setup on each frame

The kiosk needs `WRITE_SECURE_SETTINGS` for the unknown-sources switch (the same permission that keeps the navigation
buttons enabled):

```sh
adb shell pm grant com.wesbos.homehq android.permission.WRITE_SECURE_SETTINGS
adb shell dumpsys package com.wesbos.homehq | grep WRITE_SECURE_SETTINGS   # should print granted=true
```

The grant survives updates installed over the network. Without it the Android dialog says **Instalación bloqueada**;
press **Ajustes** there, turn on *Orígenes desconocidos*, and try again, or grant the permission.

## API

| Call | Who | Notes |
| --- | --- | --- |
| `GET /api/v1/admin/updates` | admin | `{mode, published, releases[]}` |
| `POST /api/v1/admin/updates?filename=&notes=` | admin | Raw APK body (limit `HOMEHQ_APK_MAX_UPLOAD_MB`, default 80). Returns `{release, created}`. |
| `POST /api/v1/admin/updates/{versionCode}/publish` | admin | Also pushes `update.changed` to the frames. |
| `POST /api/v1/admin/updates/unpublish` | admin | Frames stop being offered anything. |
| `DELETE /api/v1/admin/updates/{versionCode}` | admin | A published version has to be withdrawn first. |
| `PUT /api/v1/admin/updates/settings` | admin | `{"mode": "off" \| "notify" \| "auto"}`; the mode reaches the frames as `config.updates.mode`. |
| `POST /api/v1/admin/devices/{id}/command` | admin | `{"type": "update"}`: the frame checks, wakes and starts the install. |
| `GET /api/v1/device/update` | frame | `{mode, package, release}`; `release` has `version_code`, `version_name`, `size`, `sha256`, `cert_sha256`, `notes`. |
| `GET /api/v1/device/update/apk` | frame | The published APK. |

Releases are plain files under `data/updates/<versionCode>/` (`homehq.apk` and `meta.json`) with `data/updates/published.json`
naming the current one, so they are included in the usual `data/` backup.

## Rolling back

Android does not install a lower version code over a higher one, so there is no "go back" button. To undo a bad
release, withdraw it (**Retire**) so no more frames pick it up, fix the problem, and publish a **new** build with a
higher version code. A frame that already installed the bad one gets the fixed one the same way.

## Troubleshooting

| Symptom | Cause and fix |
| --- | --- |
| "Instalación bloqueada" dialog | `WRITE_SECURE_SETTINGS` is not granted. Grant it (above) or use **Ajustes** in the dialog. |
| "El APK está firmado con otra clave" on the frame, or "firmado con otra clave que las versiones anteriores" in the panel | The build was signed with a different keystore than the installed app. Use the original keystore. |
| "Ya existe la versión N con otro contenido" | You rebuilt without raising `--version-code`. Raise it and build again. |
| "La descarga está corrupta" | The download was cut or altered. Try again; if it repeats, check the network between the frame and the backend. |
| "Esta versión ya está instalada" / no button | The published version code is not higher than the installed one. |
| The dialog never appears after **Update now** | The frame is offline (the command is delivered live and not queued) or updates are blocked by a stuck state: reload the app and press the button in *Ajustes*. |
| Nothing happens in `off` mode | By design. Use **Update now** for a one-off update. |

## Verification status

Tested:

- Backend: APK inspection (binary manifest in UTF-8 and UTF-16 form, signature certificate, a real build), upload
  validation, size limit, duplicate and conflict handling, foreign-key rejection, publish and delete rules, mode
  validation, device authentication, download integrity (`backend/tests/test_updates.py`).
- The frame's pure checks: URL filtering, version comparison and digests (`dashboard/kiosk/test/UpdateRulesTest.java`).
- On a real PF1007L (Android 6.0.1), served by the production backend: two complete network updates
  (version code 9 to 10 and 10 to 11): download with SHA-256 and signature checks, the Android confirmation dialog,
  automatic restart into the new version, and the unknown-sources switch back at its original value afterwards. The
  *Ajustes* card and the orange dot were seen on the frame. The update was started by calling the dashboard's own
  update function over the WebView debug port (not by tapping the card button, because the frame's 60 second
  screen-off made the taps unreliable), and the tap on **Instalar** was sent over adb.
- `publish.sh` against a local backend: login, upload, publish, a wrong password, and a re-upload of the same file.

Not tested: the **Update now** command end to end (the backend accepts it, but the frame side of that path has not been run); a frame going to sleep or losing Wi-Fi in the middle of a download (the file is discarded and the next
attempt starts again); the Android dialog when `WRITE_SECURE_SETTINGS` is missing beyond what is described above; and
more than one frame updating at the same time.
