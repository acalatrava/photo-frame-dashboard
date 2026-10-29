package com.wesbos.homehq;

import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageInfo;
import android.net.wifi.WifiInfo;
import android.net.wifi.WifiManager;
import android.os.Build;
import android.os.Handler;
import android.os.HandlerThread;
import android.os.SystemClock;
import android.provider.Settings;
import android.util.Log;
import android.webkit.JavascriptInterface;

import org.json.JSONException;
import org.json.JSONObject;

/**
 * window.HQNative: what the bundled dashboard may ask of the frame. Only the app's own bundled page receives
 * this object (see MainActivity), and every call re-checks that the page is still the bundled one.
 */
final class Bridge {
  private static final String TAG = "HomeHQ";
  static final String PREFS = "hq";

  private final MainActivity act;
  private final Hardware hw;
  private final Discovery discovery;
  private final Updater updater;
  private final Speaker speaker;
  private final SharedPreferences prefs;
  // Cached copies of the dashboard and configuration live in their own file, so saving a small preference never
  // rewrites hundreds of kilobytes of cache.
  private final SharedPreferences cachePrefs;
  private static final String CACHE_PREFIX = "hq.cache.";
  private final HandlerThread statusThread = new HandlerThread("hq-status");
  private volatile String statusJson = "{}";

  Bridge(MainActivity act, Hardware hw) {
    this.act = act;
    this.hw = hw;
    this.discovery = new Discovery(act);
    this.updater = new Updater(act);
    this.speaker = new Speaker(act);
    this.prefs = act.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    this.cachePrefs = act.getSharedPreferences(PREFS + "_cache", Context.MODE_PRIVATE);
    statusThread.start();
    final Handler h = new Handler(statusThread.getLooper());
    h.post(new Runnable() {
      @Override public void run() {
        statusJson = buildStatus();
        h.postDelayed(this, 15000);
      }
    });
  }

  Speaker speaker() { return speaker; }

  private boolean trusted() { return act.pageIsBundled(); }

  void shutdown() { discovery.stop(); updater.shutdown(); speaker.shutdown(); statusThread.quitSafely(); }
  void onForeground() { updater.onForeground(); }

  // ------------------------------------------------------------ preferences
  private SharedPreferences store(String key) {
    return key.startsWith(CACHE_PREFIX) ? cachePrefs : prefs;
  }

  @JavascriptInterface public String getPref(String key) {
    if (!trusted() || key == null) return "";
    String v = store(key).getString(key, null);
    // Before the cache had its own file these keys were kept with the other preferences.
    return v != null ? v : (store(key) == prefs ? "" : prefs.getString(key, ""));
  }

  @JavascriptInterface public void setPref(String key, String value) {
    if (!trusted() || key == null || key.length() > 80) return;
    SharedPreferences.Editor e = store(key).edit();
    if (value == null || value.isEmpty()) e.remove(key); else e.putString(key, value);
    e.apply();
  }

  @JavascriptInterface public void clearWebCache() {
    if (trusted()) act.clearWebCache();
  }

  // ------------------------------------------------------------ information
  @JavascriptInterface public String getVersion() {
    try {
      PackageInfo p = act.getPackageManager().getPackageInfo(act.getPackageName(), 0);
      return p.versionName + " (" + p.versionCode + ")";
    } catch (Exception e) { return ""; }
  }

  @JavascriptInterface public String getDeviceInfo() {
    if (!trusted()) return "{}";
    JSONObject o = new JSONObject();
    try {
      o.put("model", Build.MODEL); o.put("manufacturer", Build.MANUFACTURER);
      o.put("android", Build.VERSION.RELEASE); o.put("sdk", Build.VERSION.SDK_INT);
      o.put("screen", act.screenSize());
    } catch (JSONException ignored) { }
    return o.toString();
  }

  /** Answered from a copy refreshed every 15 seconds, because asking Android for Wi-Fi details can block. */
  @JavascriptInterface public String getStatus() {
    return trusted() ? statusJson : "{}";
  }

  private String buildStatus() {
    JSONObject o = new JSONObject();
    try {
      o.put("screen", hw.screen);
      o.put("screen_cap", hw.screenCapability());
      o.put("interactive", hw.isInteractive());
      o.put("uptime_s", SystemClock.elapsedRealtime() / 1000);
      o.put("webview_ua", act.userAgent());
      JSONObject s = hw.sensorInfo();
      o.put("lux", s.opt("lux")); o.put("sensor", s.optString("name", "")); o.put("active", s.optBoolean("active"));
      WifiManager wm = (WifiManager) act.getApplicationContext().getSystemService(Context.WIFI_SERVICE);
      if (wm != null && wm.isWifiEnabled()) {
        WifiInfo wi = wm.getConnectionInfo();
        if (wi != null) { o.put("wifi_rssi", wi.getRssi()); o.put("wifi_ip", intToIp(wi.getIpAddress())); }
      } else {
        o.put("wifi", "off");
      }
    } catch (JSONException ignored) { }
    return o.toString();
  }

  private static String intToIp(int ip) {
    return (ip & 0xff) + "." + ((ip >> 8) & 0xff) + "." + ((ip >> 16) & 0xff) + "." + ((ip >> 24) & 0xff);
  }

  // ------------------------------------------------------------ discovery
  @JavascriptInterface public void startDiscovery() { if (trusted()) discovery.start(); }
  @JavascriptInterface public void stopDiscovery() { discovery.stop(); }
  @JavascriptInterface public String getDiscovered() { return trusted() ? discovery.json() : "[]"; }

  // ------------------------------------------------------------ configuration and sensor
  @JavascriptInterface public void applyConfig(String json) {
    if (!trusted() || json == null) return;
    try {
      JSONObject cfg = new JSONObject(json);
      hw.applyPresence(cfg.optJSONObject("presence"));
      act.applyDisplay(cfg.optJSONObject("display"));
    } catch (JSONException e) {
      Log.w(TAG, "Bad config from page", e);
    }
  }

  @JavascriptInterface public void setSensitivityOverride(String v) {
    if (trusted()) hw.setSensitivityOverride(v);
  }

  @JavascriptInterface public String getSensorInfo() { return trusted() ? hw.sensorInfo().toString() : "{}"; }
  @JavascriptInterface public String getSensorLog() { return trusted() ? hw.sensorLog().toString() : "[]"; }

  // ------------------------------------------------------------ sound
  @JavascriptInterface public void speak(String text, String lang, int volumePct) { if (trusted()) speaker.speak(text, lang, volumePct); }
  @JavascriptInterface public void stopSpeaking() { if (trusted()) speaker.stop(); }
  @JavascriptInterface public boolean ttsAvailable() { return trusted() && speaker.available(); }
  @JavascriptInterface public boolean ttsMissing() { return trusted() && speaker.unavailable(); }
  @JavascriptInterface public void setVolume(int pct) { if (trusted()) speaker.setVolume(pct); }

  // ------------------------------------------------------------ screen
  @JavascriptInterface public void setBrightness(int pct) { if (trusted()) act.setBrightnessPct(pct); }

  @JavascriptInterface public void wakeScreen() { if (trusted()) act.wake(); }

  /** Returns true when the screen was really switched off; false means the page should draw its black overlay. */
  @JavascriptInterface public boolean sleepScreen(String mode) { return trusted() && act.sleep(mode); }

  // ------------------------------------------------------------ app updates
  /** Downloads the build from the backend and verifies it; install=true also opens the system installer. */
  @JavascriptInterface public void downloadUpdate(String url, String token, String sha256, int versionCode, boolean install) {
    if (trusted()) updater.download(url, token, sha256, versionCode, install);
  }

  @JavascriptInterface public void installUpdate() { if (trusted()) updater.install(); }
  @JavascriptInterface public String getUpdateState() { return trusted() ? updater.stateJson() : "{}"; }

  // ------------------------------------------------------------ misc
  @JavascriptInterface public void reload() { if (trusted()) act.reloadPage(); }

  @JavascriptInterface public void openAndroidSettings() {
    if (!trusted()) return;
    act.runOnUiThread(() -> act.openSystemScreen(new Intent(Settings.ACTION_SETTINGS)));
  }
}
