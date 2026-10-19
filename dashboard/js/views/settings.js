// Ajustes: connection, screen, activity sensor diagnostics, about. Diagnostics read real native data only.
(function () {
  'use strict';
  var D = window.DATA, N = App.native;
  var V = { el: null, timer: null, sens: '' };
  var SENS_KEY = 'hq.sens.override';

  function cfg() { return (App.backend.cfg && App.backend.cfg.device_config) || {}; }
  function fmtAgo(ts) {
    if (!ts) return App.t('never');
    var s = Math.round((Date.now() - ts) / 1000);
    return s < 60 ? App.t('ago_s', { n: s }) : s < 3600 ? App.t('ago_m', { n: Math.round(s / 60) }) : App.t('ago_h', { n: Math.round(s / 3600) });
  }

  function connection() {
    var b = App.backend, c = b.cfg || {};
    var skew = Math.round(b.clockSkewMs / 1000);
    return '<section class="st-card"><div class="label">' + App.t('st_connection') + '</div>' +
      '<div class="st-kv"><span>' + App.t('st_server') + '</span><b>' + App.esc(b.url() || '–') + '</b>' +
      '<span>' + App.t('st_state') + '</span><b class="' + (b.online ? 'is-ok' : 'is-bad') + '">' + App.t(b.online ? 'st_online' : 'st_offline') + '</b>' +
      '<span>' + App.t('st_last_sync') + '</span><b>' + fmtAgo(b.lastSync) + '</b>' +
      '<span>' + App.t('st_frame') + '</span><b>' + App.esc((c.device && c.device.name) || '–') + '</b>' +
      '<span>' + App.t('st_ha') + '</span><b>' + App.t(!D.ha.enabled ? 'st_ha_off' : D.ha.connected ? 'st_online' : 'st_offline') + '</b></div>' +
      (Math.abs(skew) > 120 ? '<div class="st-warn">' + App.icon('clock', 22) + App.t('st_clock_skew', { m: Math.round(Math.abs(skew) / 60) }) + '</div>' : '') +
      '<div class="st-actions"><button class="btn btn--ghost" data-sync>' + App.t('st_sync_now') + '</button>' +
      '<button class="btn btn--ghost st-hold" data-unpair>' + App.t('st_unpair_hold') + '</button></div></section>';
  }

  function screenCard() {
    var d = cfg().display || {}, st = N.status();
    return '<section class="st-card"><div class="label">' + App.t('st_screen') + '</div>' +
      '<div class="st-kv"><span>' + App.t('st_brightness') + '</span><b>' + (App.display.brightness != null ? App.display.brightness + '%' : '–') + ' · ' + App.t('bm_' + (d.brightness_mode || 'automatic')) + '</b>' +
      '<span>' + App.t('st_night') + '</span><b>' + (d.night_mode === false ? App.t('off') : (d.night_start + ' – ' + d.night_end)) + '</b>' +
      '<span>' + App.t('st_sleep') + '</span><b>' + App.t('so_' + (d.screen_off || 'black')) + (d.screen_off === 'never' ? '' : ' · ' + d.inactivity_timeout + ' s') + '</b>' +
      (st.screen_cap ? '<span>' + App.t('st_cap') + '</span><b>' + App.esc(st.screen_cap) + '</b>' : '') + '</div>' +
      '<div class="st-actions"><button class="btn btn--ghost" data-sleep>' + App.t('st_sleep_now') + '</button></div></section>';
  }

  function sensorCard() {
    var info = N.sensorInfo(), s = N.sensor, p = cfg().presence || {};
    var sens = V.sens || p.sensitivity || 'medium';
    var live = N.available && info.hasSensor;
    return '<section class="st-card st-card--wide"><div class="label">' + App.t('st_activity') + '</div>' +
      (live ? '<div class="st-sens-row"><div class="st-kv"><span>' + App.t('st_sensor') + '</span><b>' + App.esc(info.name || '') + '</b>' +
        '<span>' + App.t('st_lux') + '</span><b class="num" data-lux>' + (s.lux == null ? '–' : (Math.round(s.lux * 10) / 10)) + '</b>' +
        '<span>' + App.t('st_baseline') + '</span><b class="num" data-base>' + (s.baseline == null ? '–' : (Math.round(s.baseline * 10) / 10)) + '</b>' +
        '<span>' + App.t('st_activity_now') + '</span><b data-act class="' + (s.active ? 'is-ok' : '') + '">' + App.t(s.active ? 'st_active' : 'st_quiet') + '</b></div>' +
        '<div class="seg st-sens">' + ['low', 'medium', 'high'].map(function (k) { return '<button data-sens="' + k + '" class="' + (sens === k ? 'is-on' : '') + '">' + App.t('sens_' + k) + '</button>'; }).join('') + '</div></div>' +
        '<canvas class="st-chart" width="1100" height="170"></canvas><p class="st-note">' + App.t('st_activity_note') + '</p>' +
        (App.backend.recording ? '<div class="st-warn">' + App.icon('bolt', 22) + App.t('st_recording') + '</div>' : '')
        : '<p class="st-note">' + App.t(N.available ? 'st_no_sensor' : 'st_no_native') + '</p>') + '</section>';
  }

  // Updates only exist inside the Android shell; a plain browser has nothing to install.
  function updateCard() {
    if (!N.available) return '';
    var u = App.updates, r = u.release(), st = u.state, avail = u.available(), off = u.mode() === 'off', busy = st.state === 'downloading' || st.state === 'installing';
    var status = st.state === 'downloading' ? App.t('up_downloading', { n: st.pct })
      : st.state === 'installing' ? App.t('up_installing')
      : st.state === 'error' ? App.t('up_error', { m: App.esc(st.error) })
      : st.state === 'ready' ? App.t('up_ready')
      : avail ? App.t(off ? 'up_off' : 'up_found') : App.t('up_current');
    var canInstall = !busy && (st.state === 'ready' || (avail && !off));
    var label = st.state === 'ready' ? 'up_install_now' : st.state === 'error' ? 'up_retry' : 'up_download_install';
    return '<section class="st-card"><div class="label">' + App.t('up_title') + '</div><div class="st-kv">' +
      '<span>' + App.t('up_installed') + '</span><b>' + App.esc(N.version() || '–') + '</b>' +
      '<span>' + App.t('up_available') + '</span><b>' + (r ? App.esc(r.version_name) + ' (' + r.version_code + ')' : '–') + '</b></div>' +
      (avail && r && r.notes ? '<p class="st-note">' + App.esc(r.notes) + '</p>' : '') +
      '<div class="st-warn' + (st.state === 'error' ? ' is-bad' : avail ? '' : ' is-calm') + '">' + App.icon(st.state === 'error' ? 'bolt' : avail ? 'bolt' : 'check', 22) + status + '</div>' +
      (st.state === 'downloading' ? '<div class="st-progress"><i style="width:' + st.pct + '%"></i></div>' : '') +
      '<div class="st-actions">' + (canInstall ? '<button class="btn" data-up-install>' + App.t(label) + '</button>' : '') +
      (busy ? '' : '<button class="btn btn--ghost" data-up-check>' + App.t('up_check') + '</button>') + '</div></section>';
  }

  function aboutCard() {
    var i = N.info();
    return '<section class="st-card"><div class="label">' + App.t('st_about') + '</div><div class="st-kv">' +
      '<span>' + App.t('st_app') + '</span><b>' + App.esc(N.version() || 'web') + '</b>' +
      '<span>WebView</span><b>' + App.esc(N.webview() || '–') + '</b>' +
      '<span>' + App.t('st_device') + '</span><b>' + App.esc(i.model || navigator.platform) + '</b>' +
      '<span>' + App.t('st_language') + '</span><b>' + App.esc(App.locale) + ' · ' + App.esc(App.tz) + '</b></div>' +
      (N.available ? '<div class="st-actions"><button class="btn btn--ghost" data-android>' + App.t('st_android') + '</button></div>' : '') + '</section>';
  }

  function drawChart() {
    var cv = V.el && V.el.querySelector('.st-chart');
    if (!cv) return;
    var samples = N.sensor.samples.slice(-300);
    var ctx = cv.getContext('2d'), w = cv.width, h = cv.height;
    ctx.clearRect(0, 0, w, h);
    if (samples.length < 2) { ctx.fillStyle = '#7A756B'; ctx.font = '20px sans-serif'; ctx.fillText(App.t('st_waiting'), 20, 40); return; }
    var max = 1, min = Infinity;
    samples.forEach(function (s) { max = Math.max(max, s[1], s[2] || 0); min = Math.min(min, s[1], s[2] == null ? s[1] : s[2]); });
    var span = Math.max(1, max - min);
    function x(i) { return 10 + (w - 20) * i / (samples.length - 1); }
    function y(v) { return h - 14 - (h - 28) * (v - min) / span; }
    ctx.fillStyle = 'rgba(0,163,108,.18)';
    samples.forEach(function (s, i) { if (s[3]) ctx.fillRect(x(i) - 2, 0, 4, h); });
    ctx.lineWidth = 3;
    ctx.strokeStyle = '#7A756B'; ctx.setLineDash([8, 6]); ctx.beginPath();
    samples.forEach(function (s, i) { if (s[2] == null) return; if (i === 0) ctx.moveTo(x(i), y(s[2])); else ctx.lineTo(x(i), y(s[2])); });
    ctx.stroke(); ctx.setLineDash([]);
    ctx.strokeStyle = '#111111'; ctx.beginPath();
    samples.forEach(function (s, i) { if (i === 0) ctx.moveTo(x(i), y(s[1])); else ctx.lineTo(x(i), y(s[1])); });
    ctx.stroke();
  }

  function paint() {
    if (!V.el) return;
    var body = V.el.querySelector('.st-body'), keep = body ? body.scrollTop : 0;
    V.el.innerHTML = '<div class="st"><header class="st-head"><div><div class="label">' + App.t('st_kicker') + '</div><h1 class="serif">' + App.t('nav_settings') + '</h1></div></header>' +
      '<div class="st-body">' + connection() + screenCard() + updateCard() + aboutCard() + sensorCard() + '</div></div>';
    body = V.el.querySelector('.st-body');
    if (body) body.scrollTop = keep;
    drawChart();
  }
  function live() {
    if (!V.el) return;
    var s = N.sensor;
    var l = V.el.querySelector('[data-lux]'), b = V.el.querySelector('[data-base]'), a = V.el.querySelector('[data-act]');
    if (l) l.textContent = s.lux == null ? '–' : Math.round(s.lux * 10) / 10;
    if (b) b.textContent = s.baseline == null ? '–' : Math.round(s.baseline * 10) / 10;
    if (a) { a.textContent = App.t(s.active ? 'st_active' : 'st_quiet'); a.className = s.active ? 'is-ok' : ''; }
    drawChart();
  }

  function onClick(e) {
    var t;
    if (e.target.closest('[data-sync]')) { App.backend.sync().then(paint, paint); }
    else if (e.target.closest('[data-sleep]')) { App.display.sleep(cfg().display && cfg().display.screen_off !== 'never' ? cfg().display.screen_off : 'black'); }
    else if (e.target.closest('[data-android]')) N.openSettings();
    else if (e.target.closest('[data-up-install]')) App.updates.install();
    else if (e.target.closest('[data-up-check]')) App.updates.check(true).then(paint, function () { App.toast(App.t('up_check_failed'), { icon: 'bolt', ms: 4000 }); });
    else if ((t = e.target.closest('[data-sens]'))) {
      V.sens = t.dataset.sens;
      try { localStorage.setItem(SENS_KEY, V.sens); } catch (x) { /* ignore */ }
      N.setSensitivityOverride(V.sens);
      App.toast(App.t('st_sens_set', { v: App.t('sens_' + V.sens) }), { icon: 'check', ms: 2500 });
      paint();
    }
  }

  App.register('settings', {
    show: function (el) {
      if (!V.el) {
        V.el = el; el.addEventListener('click', onClick);
        try { V.sens = localStorage.getItem(SENS_KEY) || ''; } catch (x) { V.sens = ''; }
        var un = el;
        App.hold = App.hold; // press-and-hold helper from the shell
      }
      paint();
      clearInterval(V.timer);
      V.timer = setInterval(live, 1000);
      var u = V.el.querySelector('[data-unpair]');
      if (u) App.hold(u, 1500, { done: function () { App.backend.unpair(false); }, cancel: function () { App.toast(App.t('st_keep_holding'), { ms: 2000, icon: 'lock' }); } });
    },
    hide: function () { clearInterval(V.timer); },
    resume: function () { clearInterval(V.timer); V.timer = setInterval(live, 1000); paint(); var u = V.el.querySelector('[data-unpair]'); if (u) App.hold(u, 1500, { done: function () { App.backend.unpair(false); } }); }
  });
  App.on('data', function () { if (App.current === 'settings') paint(); });
  App.on('conn', function () { if (App.current === 'settings') paint(); });
  App.on('update', function () { if (App.current === 'settings') paint(); });
})();
