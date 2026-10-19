// Screen policy: brightness, presence/activity wake-up and the sleep timer.
// Priority when deciding whether the screen may sleep: real Home Assistant presence, then the light-sensor
// "activity" inference, then the inactivity schedule. A touch always wins (manual).
(function () {
  'use strict';
  var D = window.DATA, N = App.native;
  var S = App.display = { screen: 'on', lastActive: Date.now(), lastLightActivity: 0, lastHaPresence: 0, lux: null, brightness: null };

  function cfg() { return (App.backend.cfg && App.backend.cfg.device_config) || {}; }
  function dsp() { return cfg().display || { brightness_mode: 'automatic', brightness_min: 15, brightness_max: 100, inactivity_timeout: 60, screen_off: 'black', night_mode: true, night_start: '22:00', night_end: '07:00', night_brightness: 5 }; }
  function prs() { return cfg().presence || { enabled: true, provider: 'light_sensor', activity_hold_s: 45, ha_hold_seconds: 120 }; }

  function hm(s) { var p = (s || '00:00').split(':'); return (+p[0]) * 60 + (+p[1]); }
  App.isNight = function () {
    var d = dsp();
    if (d.night_mode === false) return false;
    var now = App.now(), m = now.getHours() * 60 + now.getMinutes(), a = hm(d.night_start), b = hm(d.night_end);
    return a > b ? (m >= a || m < b) : (m >= a && m < b);
  };

  // ------------------------------------------------------------ brightness
  function target() {
    var d = dsp();
    if (S.screen !== 'on') return 1;
    if (d.brightness_mode === 'always_on' || d.brightness_mode === 'manual') return App.isNight() && d.night_mode ? d.night_brightness : d.brightness_max;
    if (App.isNight() && d.night_mode) return d.night_brightness;
    var lux = S.lux == null ? 120 : S.lux;
    var k = Math.max(0, Math.min(1, Math.log(lux + 1) / Math.log(400)));
    return Math.round(d.brightness_min + (d.brightness_max - d.brightness_min) * k);
  }
  var lastSent = null;
  function applyBrightness() {
    var b = target();
    if (b === lastSent) return;
    lastSent = b;
    S.brightness = b;
    N.setBrightness(b);
  }
  App.on('minute', applyBrightness);

  // ------------------------------------------------------------ black-out / sleep / wake
  function overlay() {
    var el = document.getElementById('blackout');
    if (!el) {
      el = document.createElement('div');
      el.id = 'blackout';
      document.getElementById('stage').appendChild(el);
    }
    if (!el.dataset.bound) {
      el.dataset.bound = '1';
      el.addEventListener('pointerdown', function (e) { e.preventDefault(); S._wakeTouch = Date.now(); S.wake('touch'); });
    }
    return el;
  }
  S.sleep = function (how) {
    if (S.screen !== 'on') return;
    how = how || dsp().screen_off;
    if (how === 'never') return;
    var done = how === 'off' ? N.sleep('off') : false;
    S.screen = done ? 'off' : 'black';
    overlay().classList.add('is-on');
    lastSent = null; applyBrightness();
    App.emit('screen', S.screen);
  };
  S.wake = function (why) {
    S.lastActive = Date.now();
    if (S.screen === 'on') return;
    S.screen = 'on';
    N.wake();
    overlay().classList.remove('is-on');
    lastSent = null; applyBrightness();
    if (why !== 'touch' && App.mode === 'day') { App.setMode(App.isNight() ? 'night' : 'ambient'); }
    App.emit('screen', 'on');
  };

  // ------------------------------------------------------------ presence inputs
  function usesLight() { var p = prs(); return p.enabled !== false && (p.provider === 'light_sensor' || p.provider === 'combined'); }
  function usesHa() { var p = prs(); return p.enabled !== false && (p.provider === 'homeassistant' || p.provider === 'combined'); }

  App.on('native:activity', function (p) {
    if (!usesLight()) return;
    S.lastLightActivity = Date.now();
    App.emit('activity', p);
    S.wake('activity');
  });
  App.on('presence', function () {
    if (!usesHa()) return;
    if (D.presence.ha_active === true) { S.lastHaPresence = Date.now(); S.wake('ha'); }
  });
  App.on('native:lux', function (p) {
    S.lux = p.lux;
    var now = Date.now();
    if (!S._bt || now - S._bt > 2000) { S._bt = now; applyBrightness(); }
  });

  document.addEventListener('pointerdown', function () { S.lastActive = Date.now(); }, true);

  // The touch that wakes the screen must not also press whatever is under the finger.
  document.addEventListener('click', function (e) {
    if (S._wakeTouch && Date.now() - S._wakeTouch < 800) { e.stopPropagation(); e.preventDefault(); S._wakeTouch = 0; }
  }, true);

  // ------------------------------------------------------------ sleep timer
  App.on('second', function () {
    if (S.screen !== 'on' || App.mode === 'day') return;
    var d = dsp(), now = Date.now();
    if (d.screen_off === 'never' || d.brightness_mode === 'always_on') return;
    if (now - S.lastActive < d.inactivity_timeout * 1000) return;
    var p = prs();
    if (usesHa() && (D.presence.ha_active === true || now - S.lastHaPresence < (p.ha_hold_seconds || 120) * 1000)) return;
    if (usesLight() && now - S.lastLightActivity < (p.activity_hold_s || 45) * 1000) return;
    S.sleep(d.screen_off);
  });

  // ------------------------------------------------------------ configuration + remote commands
  App.on('config', function (c) {
    var dc = c.device_config || {};
    if (dc.layout) { App.idle.home = dc.layout.home_after_s; App.idle.ambient = dc.layout.ambient_after_s; }
    N.applyConfig(dc);
    lastSent = null; applyBrightness();
    if (dc.layout && dc.layout.default_view && !S._startView) { S._startView = true; if (App.views[dc.layout.default_view]) App.go(dc.layout.default_view); }
  });
  App.on('command', function (type) {
    if (type === 'wake') S.wake('command');
    else if (type === 'sleep') S.sleep(dsp().screen_off === 'never' ? 'black' : dsp().screen_off);
    else if (type === 'reload') { N.available ? N.reload() : location.reload(); }
    else if (type === 'identify') App.toast(App.t('identify_toast', { name: App.esc((App.backend.cfg && App.backend.cfg.device.name) || '') }), { icon: 'bell', ms: 8000 });
  });
})();
