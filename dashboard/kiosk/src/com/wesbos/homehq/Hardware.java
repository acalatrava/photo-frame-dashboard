package com.wesbos.homehq;

import android.app.admin.DevicePolicyManager;
import android.content.ComponentName;
import android.content.Context;
import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;
import android.os.Handler;
import android.os.Looper;
import android.os.PowerManager;
import android.util.Log;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.util.ArrayDeque;

/**
 * Light sensor, activity detection and real screen off/on for the frame.
 *
 * One instance lives for the whole process, so sensing continues while the activity is paused (for example
 * when the screen is really off). Samples are taken from sensor callbacks and from a one second tick, because
 * the frame's light sensor only reports when the value changes.
 */
final class Hardware implements SensorEventListener {
  static final String TAG = "HomeHQ";
  static final int LOG_MAX = 900;
  static final long TICK_MS = 1000;

  /** Receives events destined for the page; may be called on the main thread. */
  interface Sink { void emit(String event, String json); }

  private static Hardware instance;

  static synchronized Hardware get(Context c) {
    if (instance == null) instance = new Hardware(c.getApplicationContext());
    return instance;
  }

  private final Context ctx;
  private final Handler main = new Handler(Looper.getMainLooper());
  private final SensorManager sm;
  private final Sensor light;
  private final PowerManager pm;
  private final DevicePolicyManager dpm;
  private final ComponentName admin;
  private final ArrayDeque<double[]> log = new ArrayDeque<>();
  private final ActivityDetector detector = new ActivityDetector(new ActivityDetector.Params());
  private PowerManager.WakeLock cpuLock;

  private volatile Sink sink;
  private volatile boolean lightEnabled = true;
  private ActivityDetector.Params base = new ActivityDetector.Params();
  private String sensitivity = "medium";
  private String override = "";
  private boolean started;
  private double lastLux = -1;
  private long lastSampleT;
  private long lastEventT;
  private double lastBaseline;
  private boolean lastActive;
  volatile String screen = "on";

  private final Runnable tick = new Runnable() {
    @Override public void run() {
      long now = System.currentTimeMillis();
      if (lastLux >= 0 && now - lastSampleT >= TICK_MS - 100) feed(now, lastLux);
      main.postDelayed(this, TICK_MS);
    }
  };

  private Hardware(Context c) {
    ctx = c;
    sm = (SensorManager) c.getSystemService(Context.SENSOR_SERVICE);
    light = sm != null ? sm.getDefaultSensor(Sensor.TYPE_LIGHT) : null;
    pm = (PowerManager) c.getSystemService(Context.POWER_SERVICE);
    dpm = (DevicePolicyManager) c.getSystemService(Context.DEVICE_POLICY_SERVICE);
    admin = new ComponentName(c, AdminReceiver.class);
  }

  void setSink(Sink s) { sink = s; }

  synchronized void start() {
    if (started) return;
    started = true;
    if (light != null) sm.registerListener(this, light, SensorManager.SENSOR_DELAY_NORMAL);
    else Log.w(TAG, "No light sensor on this device");
    main.postDelayed(tick, TICK_MS);
  }

  synchronized void stop() {
    if (!started) return;
    started = false;
    if (sm != null) sm.unregisterListener(this);
    main.removeCallbacks(tick);
    releaseCpuLock();
  }

  // ------------------------------------------------------------ configuration
  /** Applies the presence section of the device configuration pushed by the backend. */
  synchronized void applyPresence(JSONObject p) {
    if (p == null) return;
    ActivityDetector.Params b = new ActivityDetector.Params();
    b.minAbsLux = p.optDouble("min_abs_lux", b.minAbsLux);
    b.minRelChange = p.optDouble("min_rel_change", b.minRelChange);
    b.minGapMs = (long) (p.optDouble("min_event_gap_s", b.minGapMs / 1000.0) * 1000);
    b.holdMs = (long) (p.optDouble("activity_hold_s", b.holdMs / 1000.0) * 1000);
    base = b;
    sensitivity = p.optString("sensitivity", "medium");
    String provider = p.optString("provider", "light_sensor");
    lightEnabled = p.optBoolean("enabled", true) && ("light_sensor".equals(provider) || "combined".equals(provider));
    refreshParams();
  }

  synchronized void setSensitivityOverride(String v) {
    override = v == null ? "" : v;
    refreshParams();
  }

  private void refreshParams() {
    String s = override.isEmpty() ? sensitivity : override;
    detector.setParams(base.withSensitivity(s));
  }

  // ------------------------------------------------------------ sensing
  @Override public void onSensorChanged(SensorEvent e) {
    if (e.values == null || e.values.length == 0) return;
    long now = System.currentTimeMillis();
    // This sensor delivers two near-simultaneous readings per cycle (differing by about 1 lux); keep the first.
    if (now - lastEventT < 50) return;
    lastEventT = now;
    lastLux = e.values[0];
    feed(now, lastLux);
  }

  @Override public void onAccuracyChanged(Sensor s, int accuracy) { }

  private void feed(long t, double lux) {
    ActivityDetector.Result r = detector.onSample(t, lux);
    lastSampleT = t;
    lastBaseline = r.baseline;
    lastActive = r.active;
    synchronized (log) {
      log.addLast(new double[] {t, lux, r.baseline, r.active ? 1 : 0});
      while (log.size() > LOG_MAX) log.removeFirst();
    }
    Sink s = sink;
    if (s == null) return;
    try {
      JSONObject o = new JSONObject();
      o.put("t", t); o.put("lux", round(lux)); o.put("baseline", round(r.baseline)); o.put("active", r.active);
      s.emit("lux", o.toString());
      if (r.event && lightEnabled) {
        JSONObject a = new JSONObject();
        a.put("t", t); a.put("lux", round(lux)); a.put("delta", round(r.smoothed - r.baseline));
        s.emit("activity", a.toString());
      }
    } catch (JSONException ignored) { }
  }

  private static double round(double v) { return Math.round(v * 10.0) / 10.0; }

  JSONObject sensorInfo() {
    JSONObject o = new JSONObject();
    try {
      o.put("hasSensor", light != null);
      if (light != null) {
        o.put("name", light.getName()); o.put("vendor", light.getVendor());
        o.put("maxRange", light.getMaximumRange()); o.put("resolution", light.getResolution());
        o.put("minDelayUs", light.getMinDelay());
      }
      o.put("lux", lastLux < 0 ? JSONObject.NULL : round(lastLux));
      o.put("baseline", round(lastBaseline)); o.put("active", lastActive);
    } catch (JSONException ignored) { }
    return o;
  }

  JSONArray sensorLog() {
    JSONArray a = new JSONArray();
    synchronized (log) {
      for (double[] s : log) {
        JSONArray row = new JSONArray();
        try { row.put((long) s[0]); row.put(round(s[1])); row.put(round(s[2])); row.put((int) s[3]); } catch (JSONException ignored) { }
        a.put(row);
      }
    }
    return a;
  }

  // ------------------------------------------------------------ screen
  boolean adminActive() { return dpm != null && dpm.isAdminActive(admin); }

  String screenCapability() { return adminActive() ? "device_admin (lockNow)" : "black_only"; }

  /**
   * Turns the screen really off when the app is a device administrator; returns false otherwise so the caller can
   * fall back to a black overlay. A partial wake lock keeps the CPU (and so the light sensor) running meanwhile.
   */
  boolean sleepReal() {
    if (!adminActive()) return false;
    try {
      acquireCpuLock();
      dpm.lockNow();
      screen = "off";
      return true;
    } catch (SecurityException e) {
      Log.w(TAG, "lockNow refused", e);
      releaseCpuLock();
      return false;
    }
  }

  /** Brings the screen back after a real off (touch cannot do it, only a wake-up). */
  @SuppressWarnings("deprecation")
  void wakeReal() {
    PowerManager.WakeLock w = pm.newWakeLock(PowerManager.SCREEN_BRIGHT_WAKE_LOCK
        | PowerManager.ACQUIRE_CAUSES_WAKEUP | PowerManager.ON_AFTER_RELEASE, "homehq:wake");
    w.acquire(3000);
    releaseCpuLock();
  }

  private void acquireCpuLock() {
    if (cpuLock == null) cpuLock = pm.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "homehq:sensor");
    if (!cpuLock.isHeld()) cpuLock.acquire();
  }

  private void releaseCpuLock() {
    if (cpuLock != null && cpuLock.isHeld()) cpuLock.release();
  }

  boolean isInteractive() { return pm.isInteractive(); }

  Context context() { return ctx; }
}
