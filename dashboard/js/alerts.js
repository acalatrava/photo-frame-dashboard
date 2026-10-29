// Things that make noise or take over the screen: the chime on the hour, alarms, and triggers sent from outside
// (Home Assistant opening a camera when the doorbell rings, an announcement from the panel...).
(function () {
  'use strict';
  var $ = App.$, N = App.native;
  var A = App.alerts = { active: null };
  var fired = {}, snoozed = [], lastTouch = 0, appliedVolume = null;

  function dc() { return (App.backend.cfg && App.backend.cfg.device_config) || {}; }
  function sounds() { return dc().sounds || {}; }
  function alarms() { return (App.backend.cfg && App.backend.cfg.alarms) || []; }
  function two(n) { return (n < 10 ? '0' : '') + n; }
  function hm(s) { var p = (s || '00:00').split(':'); return (+p[0]) * 60 + (+p[1]); }
  function ymd(n) { return n.getFullYear() + '-' + two(n.getMonth() + 1) + '-' + two(n.getDate()); }

  document.addEventListener('pointerdown', function () { lastTouch = Date.now(); }, true);

  // ------------------------------------------------------------ the alert card
  function layer() { return $('#alert'); }

  function close() {
    var a = A.active;
    if (!a) return;
    clearInterval(a.loop); clearTimeout(a.stop); clearInterval(a.keep);
    if (a.handle) a.handle.stop();
    App.audio.stopSpeaking();
    A.active = null;
    layer().classList.remove('is-open');
    layer().innerHTML = '';
  }

  // o: { title, message, sound, speak, volume, duration_s, snooze_min, kicker, onSnooze }
  function show(o) {
    close();
    App.display.wake('alert');
    App.resetIdle();
    var a = A.active = { o: o };
    var snooze = o.snooze_min > 0;
    var el = layer();
    el.innerHTML = '<div class="al-card">' +
      '<div class="al-kicker">' + App.icon('bell', 30, 'al-bell') + '<span>' + App.esc(o.kicker || '') + '</span></div>' +
      '<div class="al-title serif">' + App.esc(o.title || '') + '</div>' +
      (o.message && o.message !== o.title ? '<div class="al-msg">' + App.esc(o.message) + '</div>' : '') +
      '<div class="al-actions">' +
      (snooze ? '<button class="al-btn" data-snooze>' + App.t('al_snooze', { n: o.snooze_min }) + '</button>' : '') +
      '<button class="al-btn al-btn--solid" data-stop>' + App.t(snooze ? 'al_stop' : 'al_close') + '</button></div></div>';
    el.classList.add('is-open');
    el.querySelector('[data-stop]').onclick = close;
    if (snooze) el.querySelector('[data-snooze]').onclick = function () {
      if (o.onSnooze) o.onSnooze();
      close();
    };

    var vol = o.volume || 80, name = o.sound && o.sound !== 'none' ? o.sound : null;
    function ring() { if (name) { if (a.handle) a.handle.stop(); a.handle = App.audio.play(name, vol); } }
    function say() { if (o.speak && o.message) App.audio.speak(o.message, vol); }
    ring(); say();
    if (name) a.loop = setInterval(ring, Math.max(2500, (App.audio.seconds(name) + 1.5) * 1000));
    if (o.speak && o.message) a.say = setInterval(say, 20000);
    // The frame must not drift off to sleep or fall back to Today while the alert is on.
    a.keep = setInterval(function () { App.display.lastActive = Date.now(); App.resetIdle(); }, 1000);
    if (o.duration_s > 0) a.stop = setTimeout(close, o.duration_s * 1000);
  }
  A.show = show;
  A.close = close;

  // ------------------------------------------------------------ chime on the hour
  function quiet(n, c) {
    if (!c.quiet) return false;
    var m = n.getHours() * 60 + n.getMinutes(), a = hm(c.quiet_start), b = hm(c.quiet_end);
    return a > b ? (m >= a || m < b) : (m >= a && m < b);
  }

  function chime(n, c) {
    var name = c.sound;
    if (name === 'speak') {
      if (App.audio.speaks()) { App.audio.speak(App.t('chime_say', { h: n.getHours(), m: n.getMinutes() }), 70); return; }
      name = 'chime';
    }
    App.audio.play(name, 70);
  }

  // ------------------------------------------------------------ alarms
  function due(a, n) {
    if (a.time !== two(n.getHours()) + ':' + two(n.getMinutes())) return false;
    if (a.date) return a.date === ymd(n);
    var wd = (n.getDay() + 6) % 7;
    return !a.days || !a.days.length || a.days.indexOf(wd) >= 0;
  }

  function ring(a, n) {
    show({
      kicker: App.t('al_alarm') + ' · ' + a.time, title: a.name || a.message || App.t('al_alarm'), message: a.message,
      sound: a.sound, speak: a.speak, volume: a.volume, duration_s: a.duration_s, snooze_min: a.snooze_min,
      onSnooze: function () { snoozed.push({ alarm: a, at: Date.now() + a.snooze_min * 60000 }); }
    });
  }

  App.on('second', function (n) {
    var stamp = ymd(n) + ' ' + two(n.getHours()) + ':' + two(n.getMinutes()), key;
    var c = sounds().chime;
    if (c && c.enabled && !A.active && (n.getMinutes() === 0 || (c.every === 'half' && n.getMinutes() === 30))) {
      key = 'c ' + stamp;
      if (!fired[key]) { fired[key] = 1; if (!quiet(n, c)) chime(n, c); }
    }
    alarms().forEach(function (a) {
      key = 'a ' + a.id + ' ' + stamp;
      if (!fired[key] && due(a, n)) { fired[key] = 1; ring(a, n); }
    });
    for (var i = snoozed.length - 1; i >= 0; i--) {
      if (Date.now() >= snoozed[i].at) { var s = snoozed.splice(i, 1)[0]; ring(s.alarm, n); }
    }
    var keys = Object.keys(fired);
    if (keys.length > 200) keys.slice(0, 100).forEach(function (k) { delete fired[k]; });
  });

  // ------------------------------------------------------------ triggers from outside
  function showView(p) {
    App.display.wake('trigger');
    App.setMode('day');
    App.closeSheet();
    App.go(p.view);
    if (p.view === 'cameras' && p.camera && App.cameras) App.cameras.open(p.camera);
    App.resetIdle();
    var shownAt = Date.now(), ms = p.duration_s > 0 ? p.duration_s * 1000 : 0;
    App.pin(ms || Infinity);
    if (!ms) return;
    // Back to what the frame was doing once the time is up, unless somebody has started using it.
    setTimeout(function () {
      if (lastTouch > shownAt) return;
      App.pin(0);
      if (App.current === p.view) App.go('home');
      App.resetIdle();
    }, ms);
  }

  App.on('command', function (type, p) {
    if (type !== 'trigger' || !p) return;
    if (p.action === 'wake') App.display.wake('trigger');
    else if (p.action === 'sleep') App.display.sleepNow();
    else if (p.action === 'show_view') showView(p);
    else if (p.action === 'alert') {
      show({ kicker: App.t('al_notice'), title: p.message || '', message: p.message, sound: p.sound, speak: !!p.speak,
        volume: p.volume, duration_s: p.duration_s, snooze_min: 0 });
    }
  });

  // ------------------------------------------------------------ volume of the frame
  App.on('config', function () {
    var v = sounds().volume;
    if (v != null && v !== appliedVolume) { appliedVolume = v; N.setVolume(v); }
  });

  App.on('ready', function () {
    layer().addEventListener('click', function (e) { e.stopPropagation(); });
  });
})();
