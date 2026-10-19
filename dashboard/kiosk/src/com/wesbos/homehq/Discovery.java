package com.wesbos.homehq;

import android.content.Context;
import android.net.nsd.NsdManager;
import android.net.nsd.NsdServiceInfo;
import android.net.wifi.WifiManager;
import android.util.Log;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.util.ArrayDeque;
import java.util.LinkedHashMap;
import java.util.Map;

/** Finds Home HQ backends advertising _homehq._tcp on the LAN. Manual entry always remains available. */
final class Discovery {
  private static final String TAG = "HomeHQ";
  private static final String TYPE = "_homehq._tcp.";

  private final NsdManager nsd;
  private final WifiManager wifi;
  private final Map<String, String[]> found = new LinkedHashMap<>();
  private final ArrayDeque<NsdServiceInfo> pending = new ArrayDeque<>();
  private WifiManager.MulticastLock lock;
  private NsdManager.DiscoveryListener listener;
  private boolean resolving;

  Discovery(Context c) {
    nsd = (NsdManager) c.getSystemService(Context.NSD_SERVICE);
    wifi = (WifiManager) c.getApplicationContext().getSystemService(Context.WIFI_SERVICE);
  }

  synchronized void start() {
    if (listener != null || nsd == null) return;
    try {
      if (wifi != null) {
        lock = wifi.createMulticastLock("homehq-mdns");
        lock.setReferenceCounted(false);
        lock.acquire();
      }
    } catch (SecurityException e) {
      Log.w(TAG, "No multicast lock", e);
    }
    listener = new NsdManager.DiscoveryListener() {
      @Override public void onStartDiscoveryFailed(String t, int code) { Log.w(TAG, "NSD start failed " + code); stop(); }
      @Override public void onStopDiscoveryFailed(String t, int code) { }
      @Override public void onDiscoveryStarted(String t) { Log.i(TAG, "NSD discovery started"); }
      @Override public void onDiscoveryStopped(String t) { }
      @Override public void onServiceFound(NsdServiceInfo info) { enqueue(info); }
      @Override public void onServiceLost(NsdServiceInfo info) {
        synchronized (Discovery.this) { found.remove(info.getServiceName()); }
      }
    };
    try {
      nsd.discoverServices(TYPE, NsdManager.PROTOCOL_DNS_SD, listener);
    } catch (RuntimeException e) {
      Log.w(TAG, "NSD discover failed", e);
      listener = null;
    }
  }

  synchronized void stop() {
    if (listener != null && nsd != null) {
      try { nsd.stopServiceDiscovery(listener); } catch (RuntimeException ignored) { }
    }
    listener = null;
    pending.clear();
    resolving = false;
    if (lock != null && lock.isHeld()) lock.release();
  }

  // Android 6 resolves one service at a time; extra requests fail with FAILURE_ALREADY_ACTIVE, so queue them.
  private synchronized void enqueue(NsdServiceInfo info) {
    pending.add(info);
    next();
  }

  private synchronized void next() {
    if (resolving || pending.isEmpty() || nsd == null) return;
    NsdServiceInfo info = pending.poll();
    resolving = true;
    try {
      nsd.resolveService(info, new NsdManager.ResolveListener() {
        @Override public void onResolveFailed(NsdServiceInfo i, int code) { done(); }
        @Override public void onServiceResolved(NsdServiceInfo i) {
          if (i.getHost() != null) {
            String host = i.getHost().getHostAddress();
            synchronized (Discovery.this) {
              found.put(i.getServiceName(), new String[] {i.getServiceName(), "http://" + host + ":" + i.getPort()});
            }
          }
          done();
        }
      });
    } catch (RuntimeException e) {
      done();
    }
  }

  private synchronized void done() {
    resolving = false;
    next();
  }

  synchronized String json() {
    JSONArray a = new JSONArray();
    for (String[] f : found.values()) {
      try { a.put(new JSONObject().put("name", f[0]).put("url", f[1])); } catch (JSONException ignored) { }
    }
    return a.toString();
  }
}
