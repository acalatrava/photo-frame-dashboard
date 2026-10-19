package com.wesbos.homehq;

import android.content.BroadcastReceiver;
import android.content.SharedPreferences;
import android.os.Handler;
import android.os.Looper;
import android.provider.Settings;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.IntentSender;
import android.content.pm.PackageInfo;
import android.content.pm.PackageInstaller;
import android.content.pm.PackageManager;
import android.content.pm.Signature;
import android.app.PendingIntent;
import android.util.Log;

import org.json.JSONException;
import org.json.JSONObject;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.security.MessageDigest;

/**
 * Downloads a new Home HQ build from the backend, checks it, and hands it to Android's installer.
 *
 * Before the installer ever sees the file it must match the SHA-256 the backend advertised, belong to this
 * very package, carry a higher version code and be signed with the same certificate as the running app.
 * Android's own installer enforces the last rule again; checking first gives a clear message instead of a
 * dead end. The install itself still needs one tap on the system dialog: an app that is not a system app,
 * device owner or root cannot install silently.
 */
final class Updater {
  private static final String TAG = "HomeHQ";
  private static final String ACTION_RESULT = "com.wesbos.homehq.UPDATE_RESULT";

  static final String IDLE = "idle", DOWNLOADING = "downloading", READY = "ready",
      INSTALLING = "installing", ERROR = "error";

  private final MainActivity act;
  private final File dir;
  private String state = IDLE;
  private int pct = 0;
  private String error = "";
  private int versionCode = 0;
  private File ready;
  private Thread worker;
  private BroadcastReceiver resultReceiver;
  private final Handler handler = new Handler(Looper.getMainLooper());
  private final SharedPreferences prefs;

  // Android blocks installs from "unknown sources" unless the owner allows them. The kiosk is granted
  // WRITE_SECURE_SETTINGS, so it opens that switch only for the few seconds the installer dialog needs
  // and puts the previous value back afterwards (also at the next start, should the app die in between).
  private static final String PREV_UNKNOWN = "update_prev_unknown";
  private static final String UNKNOWN = "install_non_market_apps";
  private static final long UNKNOWN_WINDOW_MS = 25000;

  Updater(MainActivity act) {
    this.act = act;
    this.dir = new File(act.getFilesDir(), "update");
    this.prefs = act.getSharedPreferences(Bridge.PREFS, Context.MODE_PRIVATE);
    restoreUnknownSources();
    cleanup();
  }

  /** Removes half downloads and builds that are no longer newer than the installed app. */
  private void cleanup() {
    File[] files = dir.listFiles();
    if (files == null) return;
    int installed = installedVersionCode();
    for (File f : files) {
      String n = f.getName();
      boolean stale = n.endsWith(".part");
      if (!stale && n.startsWith("homehq-") && n.endsWith(".apk")) {
        try {
          stale = !UpdateRules.isNewer(Integer.parseInt(n.substring(7, n.length() - 4)), installed);
        } catch (NumberFormatException e) {
          stale = true;
        }
      }
      if (stale) f.delete();
    }
  }

  private int installedVersionCode() {
    try {
      return act.getPackageManager().getPackageInfo(act.getPackageName(), 0).versionCode;
    } catch (PackageManager.NameNotFoundException e) {
      return 0;
    }
  }

  private boolean canWriteSecure() {
    return act.checkSelfPermission("android.permission.WRITE_SECURE_SETTINGS") == PackageManager.PERMISSION_GRANTED;
  }

  private void allowUnknownSources() {
    if (!canWriteSecure()) {
      Log.w(TAG, "WRITE_SECURE_SETTINGS not granted: the installer may show 'Install blocked'");
      return;
    }
    try {
      int now = Settings.Global.getInt(act.getContentResolver(), UNKNOWN, 0);
      if (!prefs.contains(PREV_UNKNOWN)) prefs.edit().putInt(PREV_UNKNOWN, now).apply();
      Settings.Global.putInt(act.getContentResolver(), UNKNOWN, 1);
      Settings.Secure.putInt(act.getContentResolver(), UNKNOWN, 1);
      Log.i(TAG, "Unknown sources allowed for the installer (was " + now + ")");
    } catch (RuntimeException e) {
      Log.w(TAG, "Could not allow unknown sources", e);
    }
  }

  private void restoreUnknownSources() {
    if (!prefs.contains(PREV_UNKNOWN) || !canWriteSecure()) return;
    try {
      int prev = prefs.getInt(PREV_UNKNOWN, 0);
      Settings.Global.putInt(act.getContentResolver(), UNKNOWN, prev);
      Settings.Secure.putInt(act.getContentResolver(), UNKNOWN, prev);
      prefs.edit().remove(PREV_UNKNOWN).apply();
      Log.i(TAG, "Unknown sources restored to " + prev);
    } catch (RuntimeException e) {
      Log.w(TAG, "Could not restore unknown sources", e);
    }
  }

  /** Called when Home HQ is back on screen: an install that was cancelled or timed out can be started again. */
  synchronized void onForeground() {
    Log.i(TAG, "Foreground, update state " + state);
    restoreUnknownSources();
    if (INSTALLING.equals(state)) {
      abandonOwnSessions();
      set(ready != null && ready.exists() ? READY : IDLE, ready != null ? 100 : 0, null);
    }
  }

  private void abandonOwnSessions() {
    try {
      PackageInstaller installer = act.getPackageManager().getPackageInstaller();
      for (PackageInstaller.SessionInfo info : installer.getAllSessions()) {
        if (act.getPackageName().equals(info.getInstallerPackageName())) installer.abandonSession(info.getSessionId());
      }
    } catch (RuntimeException e) {
      Log.w(TAG, "Could not abandon sessions", e);
    }
  }

  synchronized String stateJson() {
    JSONObject o = new JSONObject();
    try {
      o.put("state", state); o.put("pct", pct); o.put("error", error);
      o.put("version_code", versionCode); o.put("installed_code", installedVersionCode());
    } catch (JSONException ignored) { }
    return o.toString();
  }

  private synchronized void set(String s, int p, String err) {
    state = s; pct = p; error = err == null ? "" : err;
    act.emit("update", stateJson());
  }

  /** Starts the download; with install=true the system installer opens as soon as the file is verified. */
  synchronized void download(final String url, final String token, final String sha256, final int code, final boolean install) {
    if (DOWNLOADING.equals(state) || INSTALLING.equals(state)) return;
    if (!UpdateRules.validUrl(url) || !UpdateRules.validSha256(sha256) || token == null || token.isEmpty()) {
      set(ERROR, 0, "Petición de actualización no válida");
      return;
    }
    if (!UpdateRules.isNewer(code, installedVersionCode())) {
      set(ERROR, 0, "Esta versión ya está instalada");
      return;
    }
    if (READY.equals(state) && ready != null && ready.exists() && versionCode == code) {
      if (install) install();
      return;
    }
    versionCode = code;
    set(DOWNLOADING, 0, null);
    worker = new Thread(new Runnable() {
      @Override public void run() {
        try {
          File file = fetch(url, token, sha256, code);
          verifyArchive(file, code);
          synchronized (Updater.this) { ready = file; }
          set(READY, 100, null);
          if (install) install();
        } catch (Exception e) {
          Log.w(TAG, "Update failed", e);
          set(ERROR, 0, e.getMessage() == null ? e.getClass().getSimpleName() : e.getMessage());
        }
      }
    }, "hq-update");
    worker.start();
  }

  private File fetch(String url, String token, String sha256, int code) throws IOException {
    if (!dir.exists() && !dir.mkdirs()) throw new IOException("No se puede crear la carpeta de actualizaciones");
    File part = new File(dir, "homehq-" + code + ".apk.part");
    File out = new File(dir, "homehq-" + code + ".apk");
    HttpURLConnection c = (HttpURLConnection) new URL(url).openConnection();
    c.setConnectTimeout(10000);
    c.setReadTimeout(30000);
    c.setInstanceFollowRedirects(false);
    c.setRequestProperty("Authorization", "Bearer " + token);
    try {
      int status = c.getResponseCode();
      if (status != 200) throw new IOException("El servidor respondió " + status);
      long total = c.getContentLength();
      MessageDigest md = UpdateRules.newDigest();
      try (InputStream in = c.getInputStream(); OutputStream os = new FileOutputStream(part)) {
        byte[] buf = new byte[16384];
        long done = 0;
        int n, last = -1;
        while ((n = in.read(buf)) > 0) {
          os.write(buf, 0, n);
          md.update(buf, 0, n);
          done += n;
          int p = total > 0 ? (int) (done * 100 / total) : 0;
          if (p != last && p % 5 == 0) { last = p; set(DOWNLOADING, p, null); }
        }
      }
      if (!UpdateRules.sameDigest(UpdateRules.hex(md.digest()), sha256)) {
        part.delete();
        throw new IOException("La descarga está corrupta (suma de control distinta)");
      }
    } finally {
      c.disconnect();
    }
    if (out.exists()) out.delete();
    if (!part.renameTo(out)) throw new IOException("No se pudo guardar la actualización");
    return out;
  }

  /** The file must be this app, newer, and signed by the same key as the running copy. */
  private void verifyArchive(File file, int code) throws IOException {
    PackageManager pm = act.getPackageManager();
    PackageInfo archive = pm.getPackageArchiveInfo(file.getAbsolutePath(), PackageManager.GET_SIGNATURES);
    if (archive == null) throw new IOException("El archivo descargado no es un APK válido");
    if (!act.getPackageName().equals(archive.packageName)) throw new IOException("El APK es de otra aplicación");
    if (archive.versionCode != code) throw new IOException("La versión del APK no coincide con la anunciada");
    if (!UpdateRules.isNewer(archive.versionCode, installedVersionCode())) throw new IOException("El APK no es más nuevo que el instalado");
    PackageInfo mine;
    try {
      mine = pm.getPackageInfo(act.getPackageName(), PackageManager.GET_SIGNATURES);
    } catch (PackageManager.NameNotFoundException e) {
      throw new IOException("No se pudo leer la firma de la aplicación");
    }
    if (archive.signatures == null || archive.signatures.length == 0 || mine.signatures == null || mine.signatures.length == 0
        || !digest(archive.signatures[0]).equals(digest(mine.signatures[0]))) {
      throw new IOException("El APK está firmado con otra clave y Android no lo instalaría");
    }
  }

  private static String digest(Signature s) {
    return UpdateRules.sha256(s.toByteArray());
  }

  /** Opens Android's installer for the verified file (one confirmation tap on the frame). */
  synchronized void install() {
    if (ready == null || !ready.exists()) {
      set(ERROR, 0, "No hay ninguna actualización descargada");
      return;
    }
    try {
      abandonOwnSessions();
      PackageInstaller installer = act.getPackageManager().getPackageInstaller();
      PackageInstaller.SessionParams params = new PackageInstaller.SessionParams(PackageInstaller.SessionParams.MODE_FULL_INSTALL);
      params.setAppPackageName(act.getPackageName());
      int id = installer.createSession(params);
      PackageInstaller.Session session = installer.openSession(id);
      try (InputStream in = new FileInputStream(ready); OutputStream out = session.openWrite("homehq", 0, ready.length())) {
        byte[] buf = new byte[65536];
        int n;
        while ((n = in.read(buf)) > 0) out.write(buf, 0, n);
        session.fsync(out);
      }
      listenForResult();
      PendingIntent pi = PendingIntent.getBroadcast(act, id, new Intent(ACTION_RESULT).setPackage(act.getPackageName()),
          PendingIntent.FLAG_UPDATE_CURRENT);
      set(INSTALLING, 100, null);
      allowUnknownSources();
      session.commit(pi.getIntentSender());
      session.close();
    } catch (Exception e) {
      Log.w(TAG, "Install failed", e);
      set(ERROR, 0, "No se pudo abrir el instalador: " + e.getMessage());
    }
  }

  private void listenForResult() {
    if (resultReceiver != null) return;
    resultReceiver = new BroadcastReceiver() {
      @Override public void onReceive(Context context, Intent intent) {
        int status = intent.getIntExtra(PackageInstaller.EXTRA_STATUS, PackageInstaller.STATUS_FAILURE);
        if (status == PackageInstaller.STATUS_PENDING_USER_ACTION) {
          Intent confirm = intent.getParcelableExtra(Intent.EXTRA_INTENT);
          if (confirm != null) act.openSystemScreen(confirm);
          handler.postDelayed(new Runnable() { @Override public void run() { restoreUnknownSources(); } }, UNKNOWN_WINDOW_MS);
        } else if (status == PackageInstaller.STATUS_SUCCESS) {
          Log.i(TAG, "Update installed");
        } else {
          restoreUnknownSources();
          String msg = intent.getStringExtra(PackageInstaller.EXTRA_STATUS_MESSAGE);
          String text = status == PackageInstaller.STATUS_FAILURE_ABORTED ? "Instalación cancelada"
              : status == PackageInstaller.STATUS_FAILURE_BLOCKED ? "Android bloqueó la instalación (orígenes desconocidos)"
              : (msg == null ? "Instalación fallida (" + status + ")" : msg);
          set(ERROR, 0, text);
        }
      }
    };
    act.registerReceiver(resultReceiver, new IntentFilter(ACTION_RESULT));
  }

  void shutdown() {
    if (resultReceiver != null) {
      try { act.unregisterReceiver(resultReceiver); } catch (IllegalArgumentException ignored) { }
      resultReceiver = null;
    }
  }
}
