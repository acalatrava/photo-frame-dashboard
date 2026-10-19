// Thin wrapper around the Android shell (window.HQNative). Every call is safe in a plain browser, where
// the shell does not exist and the hardware features simply report "unavailable".
(function () {
  'use strict';
  var N = window.HQNative || null;
  var listeners = {};
  var H = App.native = { available: !!N, sensor: { lux: null, baseline: null, active: false, hasSensor: null, samples: [] } };

  function call(name, args, fallback) {
    try {
      if (N && typeof N[name] === 'function') return N[name].apply(N, args || []);
    } catch (e) { /* bridge hiccup: treat as unavailable */ }
    return fallback;
  }
  function json(name, args, fallback) {
    var raw = call(name, args, null);
    if (raw == null || raw === '') return fallback;
    try { return JSON.parse(raw); } catch (e) { return fallback; }
  }

  H.version = function () { return call('getVersion', [], ''); };
  H.webview = function () { return (navigator.userAgent.match(/Chrome\/([\d.]+)/) || [])[1] || ''; };
  H.info = function () { return json('getDeviceInfo', [], {}); };
  H.status = function () { return json('getStatus', [], {}); };
  H.discover = function () { call('startDiscovery', [], null); };
  H.stopDiscover = function () { call('stopDiscovery', [], null); };
  H.discovered = function () { return json('getDiscovered', [], []); };
  H.applyConfig = function (cfg) { call('applyConfig', [JSON.stringify(cfg)], null); };
  H.setSensitivityOverride = function (v) { call('setSensitivityOverride', [v || ''], null); };
  H.sensorInfo = function () { return json('getSensorInfo', [], { hasSensor: false }); };
  H.sensorLog = function () { return json('getSensorLog', [], []); };
  H.setBrightness = function (pct) { call('setBrightness', [pct], null); };
  H.wake = function () { call('wakeScreen', [], null); };
  H.sleep = function (mode) { return call('sleepScreen', [mode || 'black'], false); };
  H.reload = function () { call('reload', [], null); };
  H.openSettings = function () { call('openAndroidSettings', [], null); };

  H.on = function (ev, fn) { (listeners[ev] = listeners[ev] || []).push(fn); };
  // Called by the Android shell: window.HQ.onNative('activity', {...})
  window.HQ = window.HQ || {};
  window.HQ.onNative = function (ev, payload) {
    if (typeof payload === 'string') { try { payload = JSON.parse(payload); } catch (e) { payload = {}; } }
    if (ev === 'lux' && payload) {
      H.sensor.lux = payload.lux; H.sensor.baseline = payload.baseline; H.sensor.active = !!payload.active;
      H.sensor.samples.push([payload.t, payload.lux, payload.baseline, payload.active ? 1 : 0]);
      if (H.sensor.samples.length > 900) H.sensor.samples.shift();
    }
    (listeners[ev] || []).forEach(function (fn) { fn(payload); });
    App.emit('native:' + ev, payload);
  };
})();
