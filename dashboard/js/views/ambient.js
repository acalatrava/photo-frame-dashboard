// Ambient (idle photo frame) and Night (dim red clock) overlays.
(function () {
  'use strict';
  var D = window.DATA, $ = App.$;
  var amb = { show: null }, shiftTimer = null;

  var DEFAULT_WIDGETS = ['time', 'date', 'weather', 'calendar', 'people'];

  // Which pieces of information go over the photos is a per-frame setting (photos.widgets).
  function widgets() {
    var w = App.photosConfig().widgets;
    return Array.isArray(w) ? w : DEFAULT_WIDGETS;
  }

  function tasksPill() {
    var items = D.chores.items, done = items.filter(function (i) { return i.done; }).length;
    if (!items.length) return '';
    return '<div class="amb-next amb-tasks">' + App.icon(done === items.length ? 'check' : 'tasks', 22) + App.t('nav_chores') + ' <b class="num">' + done + '/' + items.length + '</b></div>';
  }

  function ambientInfo() {
    var on = widgets(), n = App.now(), w = on.indexOf('weather') >= 0 && App.weatherNow(), next = on.indexOf('calendar') >= 0 && App.nextEvent();
    var left = (on.indexOf('time') >= 0 ? '<div class="amb-time num">' + App.fmt.time(n, false) + '</div>' : '') +
      (on.indexOf('date') >= 0 ? '<div class="amb-date' + (on.indexOf('time') < 0 ? ' amb-date--alone' : '') + '">' + App.fmt.day(n) + ', ' + App.fmt.dayMonth(n) + '</div>' : '');
    var right = (w ? '<div class="amb-wx">' + App.icon(w.cond, 44) + '<span class="num">' + w.temp + '°</span><small>' + w.summary + '</small></div>' : '') +
      (next ? '<div class="amb-next" style="' + App.pstyle(App.evColor(next)) + '"><i></i>' + App.esc(next.title) + ' · ' + App.fmt.time(next.start) + '</div>' : '') +
      (on.indexOf('tasks') >= 0 ? tasksPill() : '') +
      (on.indexOf('people') >= 0 ? '<div class="amb-who">' + D.people.filter(function (p) { return p.hasPresence; }).map(function (p) { return App.avatar(p, 34, p.home ? '' : 'avatar--away'); }).join('') + '</div>' : '');
    var amb = $('#ambient');
    if (amb) amb.classList.toggle('amb--bare', !left && !right);
    return (left ? '<div class="amb-clock">' + left + '</div>' : '') + (right ? '<div class="amb-right">' + right + '</div>' : '');
  }
  function nightInfo() {
    var n = App.now(), tomorrow = App.addDays(n, n.getHours() < 6 ? 0 : 1);
    var first = App.timedOn(tomorrow)[0], w = App.weatherNow();
    return '<div class="nt-time num">' + App.fmt.time(n, false) + '</div>' +
      '<div class="nt-line">' + (w ? App.icon(w.cond, 26) + ' ' + w.temp + '° · ' : '') +
      (first ? App.t('first_up', { when: App.fmt.rel(first.start).toLowerCase() }) + ': <b>' + App.esc(first.title) + '</b> ' + App.fmt.time(first.start) : App.t('nothing_early')) + '</div>';
  }

  function paint() {
    if (App.mode === 'ambient') $('#ambient .amb-info').innerHTML = ambientInfo();
    if (App.mode === 'night') $('#night .nt-inner').innerHTML = nightInfo();
  }

  // Nudge static content a few px every minute so nothing sits still for hours (image retention)
  function pixelShift() {
    var x = Math.round(Math.random() * 8 - 4), y = Math.round(Math.random() * 8 - 4);
    App.$$('.amb-info, .nt-inner').forEach(function (el) { el.style.transform = 'translate(' + x + 'px,' + y + 'px)'; });
  }

  App.on('ready', function () {
    $('#ambient').innerHTML = '<div class="amb-stage"></div><div class="amb-scrim"></div><div class="amb-info"></div>';
    $('#night').innerHTML = '<div class="nt-inner"></div>';
    amb.show = new App.Slideshow($('#ambient .amb-stage'), { layout: 'auto', captions: false });
    $('#ambient').addEventListener('click', function () { App.setMode('day'); App.go('home'); });
    $('#night').addEventListener('click', function () { App.setMode('nightdash'); });
  });

  App.on('mode', function (m) {
    clearInterval(shiftTimer);
    if (m === 'ambient') { amb.show.start(); paint(); shiftTimer = setInterval(pixelShift, 60000); }
    else amb.show.stop();
    if (m === 'night') { paint(); shiftTimer = setInterval(pixelShift, 60000); }
    App.resetIdle();
  });
  App.on('minute', paint);
  // A dark screen needs no photo changes or image downloads.
  App.on('screen', function (s) {
    if (!amb.show) return;
    if (s !== 'on') amb.show.stop();
    else if (App.mode === 'ambient') amb.show.start();
  });
  // Colours chosen in the admin panel for the clock over the photos and for the night clock.
  var HEX = /^#[0-9a-f]{6}$/i;
  function applyColors() {
    var dc = (App.backend.cfg && App.backend.cfg.device_config) || {};
    var ink = dc.photos && HEX.test(dc.photos.text_color) ? dc.photos.text_color : '#FFFFFF';
    var night = dc.display && HEX.test(dc.display.night_color) ? dc.display.night_color : '#C22C1C';
    $('#ambient').style.setProperty('--amb-ink', ink);
    $('#night').style.setProperty('--night-ink', night);
  }
  App.on('config', function () { applyColors(); if (App.mode === 'ambient') paint(); });
})();
