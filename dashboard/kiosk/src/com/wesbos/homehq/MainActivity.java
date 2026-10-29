package com.wesbos.homehq;

import android.app.Activity;
import android.app.AlarmManager;
import android.app.AlertDialog;
import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;
import android.graphics.Bitmap;
import android.graphics.Color;
import android.content.res.AssetManager;
import android.net.ConnectivityManager;
import android.net.NetworkInfo;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.provider.Settings;
import android.util.Log;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.View;
import android.view.WindowManager;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.Toast;
import android.widget.TextView;

import org.json.JSONObject;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.HashMap;
import java.util.Map;

/**
 * Full-screen kiosk WebView for the Home HQ wall frame.
 * - The dashboard is bundled in the APK (assets/app) and served to the WebView at
 *   http://appassets.homehq.invalid/, so the frame starts instantly and works without the network.
 *   Only that bundled page receives the HQNative bridge (see Bridge).
 * - Immersive mode hides the status + navigation bars (true 1280x800).
 * - Controls: hold two fingers still on the screen for 1.5s for launcher/settings/Wi-Fi/reload.
 * - Remote debugging is OFF unless launched with the debug extra (every app on this device
 *   gets root, so the devtools socket should only exist while actively debugging):
 *     adb shell am start -n com.wesbos.homehq/.MainActivity --ez debug true
 * - Show another web dashboard instead (saved; it never gets the bridge), or go back to the bundled one:
 *     adb shell am start -n com.wesbos.homehq/.MainActivity --es url <url>
 *     adb shell am start -n com.wesbos.homehq/.MainActivity --es url app
 * - Offer the kiosk as a Home app (--ez home false undoes it), then pick it:
 *     adb shell am start -n com.wesbos.homehq/.MainActivity --ez home true
 *     adb shell cmd package set-home-activity com.wesbos.homehq/.Home
 */
public class MainActivity extends Activity {
  static final String TAG = "HomeHQ";
  static final String APP_HOST = "appassets.homehq.invalid";
  static final String APP_URL = "http://" + APP_HOST + "/index.html";
  static final String ASSET_DIR = "app";
  static final String EXTRA_URL = "url";
  static final String PREFS = "kiosk";
  static final String PREF_URL = "url";
  static final long EXIT_HOLD_MS = 1500;
  static final long RETRY_MS = 5000;
  static final long STALL_MS = 15000;
  static final long NAV_CHECK_MS = 5000;
  static final long NAV_REBIND_MS = 1000;
  static final float EXIT_SLOP_PX = 60;

  private WebView web;
  private Hardware hw;
  private Bridge bridge;
  private volatile String currentUrl = "";
  private volatile int lastBrightness = 100;
  private String userAgent = "";
  private final Handler handler = new Handler(Looper.getMainLooper());
  // Not cleared in onDestroy, so a navigation rebind that has started always finishes.
  private final Handler rebindHandler = new Handler(Looper.getMainLooper());
  private final int[] exitIds = new int[2];
  private final float[] exitX = new float[2];
  private final float[] exitY = new float[2];
  private boolean exitArmed;
  private String retryUrl;
  private boolean pageFailed;
  private LinearLayout offline;
  private TextView offlineTitle, offlineText;

  private final Runnable retry = new Runnable() {
    @Override
    public void run() {
      if (retryUrl == null) return;
      web.loadUrl(retryUrl);
      // A retry started while Wi-Fi is joining can hang for about a minute with no error and no
      // finish, so no further retry is posted. Start a new one if it is still pending.
      handler.removeCallbacks(stall);
      handler.postDelayed(stall, STALL_MS);
    }
  };

  private final Runnable stall = new Runnable() {
    @Override
    public void run() {
      if (retryUrl == null || offline.getVisibility() != View.VISIBLE) return;
      Log.w(TAG, "Retry still pending after " + STALL_MS + " ms, starting a new one");
      retry.run();
    }
  };

  // On frames that start Wi-Fi after boot, the error screen is up when Wi-Fi connects. Retry then,
  // and correct the "Connect to Wi-Fi?" text, instead of waiting for the next error.
  private final BroadcastReceiver networkChange = new BroadcastReceiver() {
    @Override
    public void onReceive(Context context, Intent intent) {
      if (retryUrl == null || offline.getVisibility() != View.VISIBLE || !wifiConnected()) return;
      Log.i(TAG, "Wi-Fi connected, retrying now");
      showOffline();
      handler.removeCallbacks(retry);
      handler.removeCallbacks(stall);
      handler.post(retry);
    }
  };

  private final Runnable showControls = new Runnable() {
    @Override
    public void run() {
      exitArmed = false;
      Log.i(TAG, "Two-finger hold: opening controls");
      new AlertDialog.Builder(MainActivity.this)
          .setTitle("Home HQ")
          .setItems(new String[] {"Abrir el launcher", "Ajustes de Android", "Ajustes Wi-Fi", "Recargar el panel"},
              (dialog, which) -> {
                if (which == 0) openLauncher();
                else if (which == 1) openSystemScreen(new Intent(Settings.ACTION_SETTINGS));
                else if (which == 2) openWifiSettings();
                else web.reload();
              })
          .setNegativeButton("Volver al panel", null).show();
    }
  };

  @Override
  protected void onCreate(Bundle state) {
    super.onCreate(state);
    applyDebugFlag(getIntent());
    applyHomeFlag(getIntent());
    keepNavigationEnabled();
    getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON
        | WindowManager.LayoutParams.FLAG_FULLSCREEN
        | WindowManager.LayoutParams.FLAG_SHOW_WHEN_LOCKED
        | WindowManager.LayoutParams.FLAG_TURN_SCREEN_ON
        | WindowManager.LayoutParams.FLAG_DISMISS_KEYGUARD);

    web = new WebView(this);
    WebSettings s = web.getSettings();
    s.setJavaScriptEnabled(true);
    s.setDomStorageEnabled(true);
    s.setUseWideViewPort(true);
    s.setMediaPlaybackRequiresUserGesture(false);
    s.setAllowFileAccess(false);
    s.setAllowContentAccess(false);
    userAgent = s.getUserAgentString();
    hw = Hardware.get(this);
    bridge = new Bridge(this, hw);
    web.addJavascriptInterface(bridge, "HQNative");
    hw.setSink((event, json) -> emit(event, json));
    bridge.speaker().setSink((event, json) -> emit(event, json));
    hw.start();
    // Keep navigation inside the kiosk. When the kiosk starts at boot before Wi-Fi is up, the
    // first load fails and would stay on the error page, so retry failed main-frame loads.
    // The offline screen covers WebView's error page until a load succeeds.
    web.setWebViewClient(new WebViewClient() {
      @Override
      public void onPageStarted(WebView view, String url, Bitmap icon) {
        pageFailed = false;
        currentUrl = url == null ? "" : url;
      }

      @Override
      public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
        return serveAsset(request);
      }

      @Override
      public void onPageCommitVisible(WebView view, String url) {
        // The retry reached the server and is drawing; let a slow page finish.
        handler.removeCallbacks(stall);
      }

      @Override
      public void onPageFinished(WebView view, String url) {
        if (!pageFailed) {
          offline.setVisibility(View.GONE);
          handler.removeCallbacks(stall);
        }
      }

      @Override
      @SuppressWarnings("deprecation")
      public void onReceivedError(WebView view, int code, String desc, String failingUrl) {
        Log.w(TAG, "Load failed (" + desc + "), retrying in " + RETRY_MS + " ms");
        pageFailed = true;
        showOffline();
        retryUrl = failingUrl;
        handler.removeCallbacks(retry);
        handler.removeCallbacks(stall);
        handler.postDelayed(retry, RETRY_MS);
      }
    });
    FrameLayout root = new FrameLayout(this);
    root.addView(web);
    root.addView(buildOffline());
    setContentView(root);

    String url = urlFrom(getIntent());
    retryUrl = url != null ? url : savedUrl();
    web.loadUrl(retryUrl);
    @SuppressWarnings("deprecation")
    IntentFilter connectivity = new IntentFilter(ConnectivityManager.CONNECTIVITY_ACTION);
    registerReceiver(networkChange, connectivity);
  }

  @Override
  protected void onResume() {
    super.onResume();
    cancelSystemScreenReturn();
    if (bridge != null) bridge.onForeground();
    NavigationService.setDashboardVisible(true);
  }

  @Override
  protected void onPause() {
    cancelExit();
    NavigationService.setDashboardVisible(false);
    super.onPause();
  }

  @Override
  protected void onNewIntent(Intent intent) {
    super.onNewIntent(intent);
    setIntent(intent);
    applyDebugFlag(intent);
    applyHomeFlag(intent);
    String url = urlFrom(intent);
    if (url != null) {
      handler.removeCallbacks(retry);
      handler.removeCallbacks(stall);
      retryUrl = url;
      web.loadUrl(url);
    }
  }

  /**
   * A "url" extra (adb only) points the kiosk at another web dashboard and is remembered; the value "app" goes back
   * to the bundled dashboard. Other pages never receive the HQNative bridge.
   */
  private String urlFrom(Intent intent) {
    String url = intent.getStringExtra(EXTRA_URL);
    if (url == null) return null;
    if ("app".equals(url)) {
      getSharedPreferences(PREFS, MODE_PRIVATE).edit().remove(PREF_URL).apply();
      return APP_URL;
    }
    String scheme = Uri.parse(url).getScheme();
    if (!"http".equalsIgnoreCase(scheme) && !"https".equalsIgnoreCase(scheme)) {
      Log.w(TAG, "Ignoring non-web kiosk URL: " + url);
      return null;
    }
    getSharedPreferences(PREFS, MODE_PRIVATE).edit().putString(PREF_URL, url).apply();
    return url;
  }

  private String savedUrl() {
    return getSharedPreferences(PREFS, MODE_PRIVATE).getString(PREF_URL, APP_URL);
  }

  // ------------------------------------------------------------ bundled app
  /** True while the page in the WebView is the one served from this APK. Safe to call from any thread. */
  /** Sends an event to the bundled page; safe to call from any thread. */
  void emit(String event, String json) {
    handler.post(() -> {
      if (web != null && pageIsBundled()) {
        web.evaluateJavascript("window.HQ&&window.HQ.onNative&&window.HQ.onNative('" + event + "'," + json + ")", null);
      }
    });
  }

  boolean pageIsBundled() {
    String u = currentUrl;
    return u.startsWith("http://" + APP_HOST + "/");
  }

  private static final Map<String, String> MIME = new HashMap<>();
  static {
    MIME.put("html", "text/html"); MIME.put("js", "text/javascript"); MIME.put("mjs", "text/javascript");
    MIME.put("css", "text/css"); MIME.put("json", "application/json"); MIME.put("png", "image/png");
    MIME.put("jpg", "image/jpeg"); MIME.put("jpeg", "image/jpeg"); MIME.put("svg", "image/svg+xml");
    MIME.put("woff", "font/woff"); MIME.put("woff2", "font/woff2"); MIME.put("webmanifest", "application/manifest+json");
    MIME.put("ico", "image/x-icon");
  }

  private WebResourceResponse serveAsset(WebResourceRequest request) {
    Uri uri = request.getUrl();
    if (uri == null || !APP_HOST.equalsIgnoreCase(uri.getHost())) return null;
    String path = uri.getPath() == null || uri.getPath().equals("/") ? "/index.html" : uri.getPath();
    Map<String, String> headers = new HashMap<>();
    headers.put("Cache-Control", path.startsWith("/assets/") ? "public, max-age=31536000, immutable" : "no-cache");
    if (path.contains("..") || !"GET".equalsIgnoreCase(request.getMethod())) {
      return new WebResourceResponse("text/plain", "UTF-8", 404, "Not Found", headers, new ByteArrayInputStream(new byte[0]));
    }
    try {
      InputStream in = getAssets().open(ASSET_DIR + path, AssetManager.ACCESS_STREAMING);
      String ext = path.substring(path.lastIndexOf('.') + 1).toLowerCase();
      String mime = MIME.containsKey(ext) ? MIME.get(ext) : "application/octet-stream";
      return new WebResourceResponse(mime, mime.startsWith("text/") || mime.endsWith("json") ? "UTF-8" : null, 200, "OK", headers, in);
    } catch (IOException e) {
      return new WebResourceResponse("text/plain", "UTF-8", 404, "Not Found", headers, new ByteArrayInputStream(new byte[0]));
    }
  }

  String userAgent() { return userAgent; }

  String screenSize() {
    return getResources().getDisplayMetrics().widthPixels + "x" + getResources().getDisplayMetrics().heightPixels;
  }

  // ------------------------------------------------------------ screen control (called from the bridge)
  void applyDisplay(JSONObject display) { /* brightness and sleeping are decided by the page; nothing to keep */ }

  /** 0..100. Values of 1 or less switch the backlight off while the screen stays "on" (touch still works). */
  void setBrightnessPct(int pct) {
    if (pct != lastBrightness) hw.noteBrightnessChange();
    lastBrightness = pct;
    runOnUiThread(() -> {
      WindowManager.LayoutParams lp = getWindow().getAttributes();
      lp.screenBrightness = pct <= 1 ? 0f : Math.min(1f, pct / 100f);
      getWindow().setAttributes(lp);
    });
  }

  boolean sleep(String mode) {
    if (!"off".equals(mode)) return false;
    return hw.sleepReal();
  }

  void wake() {
    if ("off".equals(hw.screen)) hw.wakeReal();
    hw.screen = "on";
    runOnUiThread(() -> getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON));
  }

  void clearWebCache() {
    runOnUiThread(() -> web.clearCache(true));
  }

  void reloadPage() {
    runOnUiThread(() -> web.loadUrl(APP_URL));
  }

  private int dp(float v) {
    return (int) TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_DIP, v, getResources().getDisplayMetrics());
  }

  private View buildOffline() {
    offline = new LinearLayout(this);
    offline.setOrientation(LinearLayout.VERTICAL);
    offline.setGravity(Gravity.CENTER);
    offline.setBackgroundColor(Color.rgb(17, 17, 17));
    offline.setVisibility(View.GONE);
    offline.setClickable(true); // keep taps off the error page underneath

    offlineTitle = new TextView(this);
    offlineTitle.setTextColor(Color.WHITE);
    offlineTitle.setTextSize(TypedValue.COMPLEX_UNIT_SP, 40);
    offlineTitle.setGravity(Gravity.CENTER);
    offline.addView(offlineTitle);

    offlineText = new TextView(this);
    offlineText.setTextColor(Color.rgb(170, 170, 170));
    offlineText.setTextSize(TypedValue.COMPLEX_UNIT_SP, 20);
    offlineText.setGravity(Gravity.CENTER);
    offlineText.setPadding(dp(24), dp(12), dp(24), dp(28));
    offline.addView(offlineText);

    Button wifi = new Button(this);
    wifi.setText("Abrir ajustes Wi-Fi");
    wifi.setTextSize(TypedValue.COMPLEX_UNIT_SP, 22);
    wifi.setPadding(dp(32), dp(16), dp(32), dp(16));
    wifi.setOnClickListener(v -> openWifiSettings());
    offline.addView(wifi, new LinearLayout.LayoutParams(
        LinearLayout.LayoutParams.WRAP_CONTENT, LinearLayout.LayoutParams.WRAP_CONTENT));
    return offline;
  }

  private boolean wifiConnected() {
    ConnectivityManager cm = (ConnectivityManager) getSystemService(CONNECTIVITY_SERVICE);
    @SuppressWarnings("deprecation")
    NetworkInfo n = cm != null ? cm.getNetworkInfo(ConnectivityManager.TYPE_WIFI) : null;
    return n != null && n.isConnected();
  }

  private void showOffline() {
    if (wifiConnected()) {
      offlineTitle.setText("No se puede cargar el panel");
      offlineText.setText("El Wi-Fi está conectado. Reintentando cada pocos segundos.");
    } else {
      offlineTitle.setText("¿Conectar al Wi-Fi?");
      offlineText.setText("El marco no está en el Wi-Fi. El panel volverá solo cuando lo esté.");
    }
    offline.setVisibility(View.VISIBLE);
  }

  private void openWifiSettings() {
    try {
      openSystemScreen(new Intent(Settings.ACTION_WIFI_SETTINGS));
    } catch (Exception e) {
      Log.w(TAG, "No Wi-Fi settings screen, opening Settings", e);
      openSystemScreen(new Intent(Settings.ACTION_SETTINGS));
    }
  }

  /**
   * Some frames (PF1007L) run a vendor BackgroundManagerService that drops the navigation service
   * after the kiosk is updated or force-stopped, leaving no way back from Settings. If the owner
   * opted in by granting WRITE_SECURE_SETTINGS, put the service back on the enabled list:
   *   adb shell pm grant com.wesbos.homehq android.permission.WRITE_SECURE_SETTINGS
   * Android 6 also leaves the service listed but unbound after the kiosk's process is killed (the
   * Denver PFF-1015's low-RAM mode kills it on every app switch), so rebind it if it isn't running.
   */
  private void keepNavigationEnabled() {
    if (checkSelfPermission("android.permission.WRITE_SECURE_SETTINGS") != PackageManager.PERMISSION_GRANTED) return;
    String cur = Settings.Secure.getString(getContentResolver(), Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES);
    String others = withoutNavigation(cur);
    if (!isNavigationListed(cur)) {
      setNavigationServices(others.isEmpty() ? navigationService() : others + ":" + navigationService());
      Log.i(TAG, "Re-enabled navigation service");
      return;
    }
    // Some firmware keeps the selected service but resets only the master switch at boot.
    int enabled = Settings.Secure.getInt(getContentResolver(), Settings.Secure.ACCESSIBILITY_ENABLED, 0);
    if (enabled != 1) {
      setAccessibilityEnabled();
      return;
    }
    handler.postDelayed(() -> {
      if (NavigationService.isConnected()) return;
      // Writing the same list doesn't notify Android, so take the service off and put it back.
      setNavigationServices(others);
      rebindHandler.postDelayed(() -> setNavigationServices(cur), NAV_REBIND_MS);
      Log.i(TAG, "Navigation service listed but not running, rebinding");
    }, NAV_CHECK_MS);
  }

  private String navigationService() {
    return getPackageName() + "/" + NavigationService.class.getName();
  }

  private boolean isNavigationEntry(String entry) {
    return new ComponentName(this, NavigationService.class).equals(ComponentName.unflattenFromString(entry));
  }

  private boolean isNavigationListed(String services) {
    if (services == null) return false;
    for (String entry : services.split(":")) {
      if (isNavigationEntry(entry)) return true;
    }
    return false;
  }

  /** The enabled services list without the navigation service. */
  private String withoutNavigation(String services) {
    if (services == null) return "";
    StringBuilder rest = new StringBuilder();
    for (String entry : services.split(":")) {
      if (entry.isEmpty() || isNavigationEntry(entry)) continue;
      if (rest.length() > 0) rest.append(':');
      rest.append(entry);
    }
    return rest.toString();
  }

  private void setNavigationServices(String services) {
    try {
      Settings.Secure.putString(getContentResolver(), Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES, services);
      if (Settings.Secure.getInt(getContentResolver(), Settings.Secure.ACCESSIBILITY_ENABLED, 0) != 1) {
        Settings.Secure.putString(getContentResolver(), Settings.Secure.ACCESSIBILITY_ENABLED, "1");
      }
    } catch (SecurityException e) {
      Log.w(TAG, "Could not update navigation service", e);
    }
  }

  /** Master switch only: a correct services list is left untouched. */
  private void setAccessibilityEnabled() {
    try {
      Settings.Secure.putString(getContentResolver(), Settings.Secure.ACCESSIBILITY_ENABLED, "1");
    } catch (SecurityException e) {
      Log.w(TAG, "Could not update accessibility master switch", e);
    }
  }

  private void openLauncher() {
    Intent home = new Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_HOME);
    for (ResolveInfo info : getPackageManager().queryIntentActivities(home, 0)) {
      String pkg = info.activityInfo.packageName;
      if (pkg.equals(getPackageName()) || pkg.equals("com.android.settings")) continue;
      startActivity(new Intent(home).setComponent(new ComponentName(pkg, info.activityInfo.name)));
      return;
    }
    openSystemScreen(new Intent(Settings.ACTION_SETTINGS));
  }

  private static final long SYSTEM_SCREEN_MS = 5 * 60 * 1000L;

  private PendingIntent returnIntent() {
    Intent back = new Intent(this, MainActivity.class)
        .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_REORDER_TO_FRONT | Intent.FLAG_ACTIVITY_SINGLE_TOP);
    return PendingIntent.getActivity(this, 7, back, PendingIntent.FLAG_UPDATE_CURRENT);
  }

  /**
   * Opens an Android screen and schedules an automatic return to Home HQ. The frame has no Back or Home
   * buttons, so without this there would be no way out. An alarm is used instead of a timer so it still
   * fires if the system reclaims the app's memory in the meantime.
   */
  void openSystemScreen(Intent screen) {
    AlarmManager alarms = (AlarmManager) getSystemService(Context.ALARM_SERVICE);
    alarms.set(AlarmManager.RTC_WAKEUP, System.currentTimeMillis() + SYSTEM_SCREEN_MS, returnIntent());
    Toast.makeText(this, "Volverás a Home HQ automáticamente en 5 minutos", Toast.LENGTH_LONG).show();
    startActivity(screen.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
  }

  private void cancelSystemScreenReturn() {
    ((AlarmManager) getSystemService(Context.ALARM_SERVICE)).cancel(returnIntent());
  }

  @Override
  protected void onDestroy() {
    unregisterReceiver(networkChange);
    handler.removeCallbacksAndMessages(null);
    if (hw != null) hw.setSink(null);
    if (bridge != null) bridge.shutdown();
    if (web != null) web.destroy();
    super.onDestroy();
  }

  /** Remote debugging only when explicitly requested; any normal launch turns it back off. */
  private void applyDebugFlag(Intent intent) {
    boolean debug = intent != null && intent.getBooleanExtra("debug", false);
    WebView.setWebContentsDebuggingEnabled(debug);
    Log.i(TAG, "WebView remote debugging " + (debug ? "ON" : "off"));
  }

  /** Turns the Home alias on or off. The shell can't enable a component of a release app. */
  private void applyHomeFlag(Intent intent) {
    if (intent == null || !intent.hasExtra("home")) return;
    boolean home = intent.getBooleanExtra("home", false);
    getPackageManager().setComponentEnabledSetting(new ComponentName(this, getPackageName() + ".Home"),
        home ? PackageManager.COMPONENT_ENABLED_STATE_ENABLED : PackageManager.COMPONENT_ENABLED_STATE_DEFAULT,
        PackageManager.DONT_KILL_APP);
    Log.i(TAG, "Home alias " + (home ? "on" : "off"));
  }

  /** Watches for the two-finger exit hold; all touches still go to the page. */
  @Override
  public boolean dispatchTouchEvent(MotionEvent e) {
    switch (e.getActionMasked()) {
      case MotionEvent.ACTION_POINTER_DOWN:
        if (e.getPointerCount() == 2) {
          for (int i = 0; i < 2; i++) {
            exitIds[i] = e.getPointerId(i);
            exitX[i] = e.getX(i);
            exitY[i] = e.getY(i);
          }
          exitArmed = true;
          handler.removeCallbacks(showControls);
          handler.postDelayed(showControls, EXIT_HOLD_MS);
        } else {
          cancelExit(); // 3+ fingers
        }
        break;
      case MotionEvent.ACTION_MOVE:
        if (exitArmed) {
          for (int i = 0; i < 2; i++) {
            int idx = e.findPointerIndex(exitIds[i]);
            if (idx < 0 || Math.hypot(e.getX(idx) - exitX[i], e.getY(idx) - exitY[i]) > EXIT_SLOP_PX) {
              cancelExit();
              break;
            }
          }
        }
        break;
      case MotionEvent.ACTION_POINTER_UP:
      case MotionEvent.ACTION_UP:
      case MotionEvent.ACTION_CANCEL:
        cancelExit();
        break;
      default:
        break;
    }
    return super.dispatchTouchEvent(e);
  }

  private void cancelExit() {
    if (!exitArmed) return;
    exitArmed = false;
    handler.removeCallbacks(showControls);
  }

  @Override
  public void onWindowFocusChanged(boolean hasFocus) {
    super.onWindowFocusChanged(hasFocus);
    if (hasFocus) hideSystemUi();
  }

  private void hideSystemUi() {
    getWindow().getDecorView().setSystemUiVisibility(
        View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
            | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
            | View.SYSTEM_UI_FLAG_FULLSCREEN
            | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
            | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
            | View.SYSTEM_UI_FLAG_LAYOUT_STABLE);
  }

  @Override
  public void onBackPressed() {
    if (web.canGoBack()) web.goBack();
  }
}
