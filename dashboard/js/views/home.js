// Home / Today: the glanceable overview. Never scrolls.
(function () {
  'use strict';
  var D = window.DATA, V = {};

  function clock() {
    var n = App.now();
    return '<div class="h-time num">' + App.fmt.time(n, false) + '<span class="h-ampm">' + App.fmt.ampm(n) + '</span></div>' +
      '<div class="h-date"><b>' + App.fmt.day(n) + '</b> ' + App.fmt.dayMonth(n) + '</div>';
  }

  function weather() {
    var w = App.weatherNow();
    if (!w) return '<div class="h-wx-say"><b>' + App.t('wx_none') + '</b></div>';
    var hours = App.hourly(7);
    var tmin = Math.min.apply(null, hours.map(function (h) { return h.t; }));
    var tmax = Math.max.apply(null, hours.map(function (h) { return h.t; }));
    return '<div class="h-wx-top">' +
      '<span class="h-wx-icon">' + App.icon(w.cond, 60) + '</span>' +
      '<span class="h-wx-temp num">' + w.temp + '°</span>' +
      '<span class="h-wx-meta"><b>' + w.label + '</b><span>' + App.t('wx_hi_lo', { hi: w.hi, lo: w.lo }) + '</span></span>' +
      '</div>' +
      '<div class="h-wx-say"><b>' + w.summary + '.</b> ' + w.advice + '.' + (w.stale ? ' <i>' + App.t('stale') + '</i>' : '') + '</div>' +
      '<div class="h-wx-hours">' + hours.map(function (h) {
        var lift = tmax === tmin ? 0 : Math.round((h.t - tmin) / (tmax - tmin) * 8);
        return '<div class="h-hr' + (h.p >= 50 ? ' is-wet' : '') + '"><span class="h-hr-l">' + h.label + '</span>' +
          '<span class="h-hr-i" style="transform:translateY(' + -lift + 'px)">' + App.icon(h.c, 22) + '</span><b>' + h.t + '°</b></div>';
      }).join('') + '</div>';
  }

  function hero() {
    var e = App.nextEvent(), now = App.now();
    if (!e) {
      var tomorrow = App.timedOn(App.addDays(now, 1))[0];
      return '<div class="h-hero h-hero--empty" data-go="calendar">' +
        '<div class="label label--light">' + App.t('rest_of_day') + '</div>' +
        '<div class="h-hero-title serif">' + App.t('nothing_else') + '<br><i>' + App.t('enjoy_quiet') + '</i></div>' +
        (tomorrow ? '<div class="h-hero-meta">' + App.t('tomorrow_starts', { title: '<b>' + App.esc(tomorrow.title) + '</b>', time: App.fmt.time(tomorrow.start) }) + '</div>' : '') +
        '</div>';
    }
    var p = App.evColor(e);
    var mins = (e.start - now) / 60000;
    var who = e.people.map(function (id) { return App.person(id).name; });
    var whoText = App.isFamily(e) ? App.t('everyone') : who.join(' + ');
    var big = mins < 100
      ? '<div class="h-hero-count num">' + Math.max(0, Math.round(mins)) + '<small>min</small></div>'
      : '<div class="h-hero-count num">' + App.fmt.time(e.start, false) + '<small>' + App.fmt.ampm(e.start) + '</small></div>';
    return '<button class="h-hero" style="' + App.pstyle(p) + '" data-ev="' + App.esc(e.id) + '">' +
      '<div class="h-hero-main">' +
      '  <div class="label label--on">' + App.t('next_up') + (whoText ? ' · ' + App.esc(whoText) : '') + '</div>' +
      '  <div class="h-hero-title serif">' + App.esc(e.title) + '</div>' +
      '  <div class="h-hero-meta">' + App.fmt.range(e.start, e.end) + (e.loc ? ' · ' + App.esc(e.loc) : '') + '</div>' +
      '  <div class="h-hero-foot">' + (e.people.length > 1 ? App.dots(e.people, 22) : '') + '</div>' +
      '</div>' + big + '</button>';
  }

  // The lanes have a fixed height, so each person's events and chores share a pixel budget instead of fixed counts.
  var LANE_CHROME = 62, EV_H = 66, CHIP_H = 55, MORE_H = 42;
  function laneBudget() {
    var el = V.el && V.el.querySelector('.h-lanes');
    return Math.max(200, (el && el.clientHeight || 320) - LANE_CHROME);
  }

  function laneChips(mine, room) {
    var left = mine.filter(function (i) { return !i.done; });
    if (!left.length) return '<div class="h-ch-done">' + App.icon('check', 22) + App.t('ch_all_done') + '</div>';
    var more = left.length > room ? left.length - room : 0;
    var shown = left.slice(0, room);
    return '<div class="h-ch">' + shown.map(function (i) {
      return '<button class="h-chip" data-chore="' + App.esc(i.id) + '" data-person="' + App.esc(i.person) + '">' + App.icon(i.icon, 22) + '<span>' + App.esc(i.title) + '</span></button>';
    }).join('') + (more > 0 ? '<button class="h-ch-more" data-go="chores">' + App.t('more_n', { n: more }) + ' · ' + App.t('ch_see_all') + '</button>' : '') + '</div>';
  }

  function lanes() {
    var now = App.now();
    if (!D.people.length) return '<div class="h-free serif">' + App.t('no_people') + '</div>';
    var budget = laneBudget();
    var el = V.el && V.el.querySelector('.h-lanes');
    if (el) el.style.gridTemplateColumns = 'repeat(' + Math.max(2, Math.min(4, D.people.length)) + ', 1fr)';
    return D.people.map(function (p) {
      var list = App.timedOn(now, p.id).filter(function (e) { return e.end > now; });
      var mine = D.chores.items.filter(function (i) { return i.person === p.id; });
      var pending = mine.filter(function (i) { return !i.done; }).length;
      // Chores get at least one slot (they are what people act on); events use the rest, up to three.
      var evMax = Math.min(3, list.length, Math.max(mine.length ? 1 : 0, Math.floor((budget - (pending ? CHIP_H : 0)) / EV_H)));
      var shown = list.slice(0, evMax), moreEv = list.length - shown.length;
      var used = shown.length * EV_H + (moreEv > 0 ? MORE_H : 0);
      var room = Math.floor((budget - used) / CHIP_H);
      if (pending > room) room = Math.max(1, Math.floor((budget - used - MORE_H) / CHIP_H));
      return '<div class="h-lane" style="' + App.pstyle(p) + '">' +
        '<div class="h-lane-head">' + App.avatar(p, 30) + '<b>' + App.esc(p.name) + '</b></div>' +
        shown.map(function (e) {
          var cur = e.start <= now;
          return '<button class="h-ev' + (cur ? ' is-now' : '') + '" data-ev="' + App.esc(e.id) + '">' +
            '<span class="h-ev-t">' + (cur ? App.t('now') : App.fmt.time(e.start, false)) + '</span>' +
            '<span class="h-ev-n">' + App.esc(e.title) + '</span></button>';
        }).join('') +
        (moreEv > 0 ? '<button class="h-more" data-go="calendar">' + App.t('more_n', { n: moreEv }) + '</button>' : '') +
        (!list.length && !mine.length ? '<div class="h-free serif"><i>' + App.t('free') + '</i> ' + App.t('rest_of_day_l') + '</div>' : '') +
        (mine.length ? laneChips(mine, room) : '') + '</div>';
    }).join('');
  }

  function ring(done, total, size) {
    var r = size / 2 - 5, c = 2 * Math.PI * r, f = total ? done / total : 0;
    return '<svg class="ring" width="' + size + '" height="' + size + '" viewBox="0 0 ' + size + ' ' + size + '">' +
      '<circle cx="' + size / 2 + '" cy="' + size / 2 + '" r="' + r + '" class="ring-bg"/>' +
      '<circle cx="' + size / 2 + '" cy="' + size / 2 + '" r="' + r + '" class="ring-fg" stroke-dasharray="' + (c * f) + ' ' + c + '" transform="rotate(-90 ' + size / 2 + ' ' + size / 2 + ')"/></svg>';
  }
  App.ring = ring;

  // Today's agenda progress: timed events already finished vs. all of today's.
  function agenda() {
    var now = App.now(), list = App.timedOn(now), allDay = App.allDayOn(now);
    var done = list.filter(function (e) { return e.end <= now; }).length;
    var left = list.length - done;
    return '<div class="label">' + App.t('today') + '</div><div class="h-rings"><div class="h-ring' + (list.length && !left ? ' is-done' : '') + '">' + ring(done, list.length, 64) +
      '<b class="num">' + (list.length && !left ? '✓' : done + '/' + list.length) + '</b><span>' + App.t('events') + '</span></div>' +
      '<div class="h-ring"><b class="num">' + allDay.length + '</b><span>' + App.t('all_day') + '</span></div></div>';
  }

  // With chores configured, the card shows how far each person is; otherwise it keeps the agenda progress.
  function choresCard() {
    var items = D.chores.items, done = items.filter(function (i) { return i.done; }).length;
    var who = D.people.map(function (p) {
      var mine = items.filter(function (i) { return i.person === p.id; });
      if (!mine.length) return '';
      var d = mine.filter(function (i) { return i.done; }).length;
      return '<span class="h-cw' + (d === mine.length ? ' is-done' : '') + '" style="' + App.pstyle(p) + '">' + App.avatar(p, 30) + '<b class="num">' + d + '/' + mine.length + '</b></span>';
    }).join('');
    var shared = items.filter(function (i) { return !i.person; });
    if (shared.length) {
      var sd = shared.filter(function (i) { return i.done; }).length;
      who += '<span class="h-cw' + (sd === shared.length ? ' is-done' : '') + '" style="' + App.pstyle(D.family) + '">' + App.avatar(D.family, 30) + '<b class="num">' + sd + '/' + shared.length + '</b></span>';
    }
    return '<div class="label">' + App.t('nav_chores') + '</div><div class="h-chrow"><div class="h-ring' + (items.length && done === items.length ? ' is-done' : '') + '">' + ring(done, items.length, 64) +
      '<b class="num">' + (items.length && done === items.length ? '✓' : done + '/' + items.length) + '</b></div><div class="h-cws">' + who + '</div></div>';
  }

  function shopping() {
    var open = D.groceries.filter(function (g) { return !g.done; });
    var recent = open.slice(-3).reverse();
    return '<div class="label">' + App.t('nav_shopping') + '</div>' +
      '<div class="h-stat"><span class="num">' + open.length + '</span><small>' + App.t('items_to_get') + '</small></div>' +
      '<ul class="h-recent">' + recent.map(function (g) {
        return '<li><i></i>' + App.esc(g.name) + '</li>';
      }).join('') + '</ul>';
  }

  function status() {
    if (!D.ha.enabled) return '<div class="label">' + App.t('nav_house') + '</div><div class="h-st-row">' + App.icon('bulb', 24) + '<span>' + App.t('ha_not_configured') + '</span></div>';
    var ents = D.ha.entities;
    var lights = ents.filter(function (e) { return e.entity_id.indexOf('light.') === 0 && e.state === 'on'; }).length;
    var temp = ents.filter(function (e) { return e.attributes.device_class === 'temperature' && !isNaN(parseFloat(e.state)); })[0];
    var clim = ents.filter(function (e) { return e.entity_id.indexOf('climate.') === 0 && e.attributes.current_temperature != null; })[0];
    var t = temp ? parseFloat(temp.state) : clim ? clim.attributes.current_temperature : null;
    return '<div class="label">' + App.t('nav_house') + (D.ha.connected ? '' : ' · ' + App.t('stale')) + '</div>' +
      '<div class="h-st-row">' + App.icon('bulb', 24) + '<b class="num">' + lights + '</b><span>' + App.t('lights_on') + '</span></div>' +
      (t != null ? '<div class="h-st-row">' + App.icon('thermo', 24) + '<b class="num">' + (Math.round(t * 10) / 10).toString().replace('.', App.locale === 'en' ? '.' : ',') + '°</b><span>' + App.t('inside') + '</span></div>' : '') +
      '<div class="h-st-row' + (D.ha.connected ? '' : ' is-warn') + '">' + App.icon(D.ha.connected ? 'check' : 'wifioff', 24) + '<span>' + App.t(D.ha.connected ? 'ha_live' : 'ha_down') + '</span></div>';
  }

  function paintChores() {
    var card = V.el.querySelector('.h-chores'), has = D.chores.configured > 0;
    card.dataset.go = has ? 'chores' : 'calendar';
    card.innerHTML = has ? choresCard() : agenda();
  }

  function paint() {
    var el = V.el;
    el.querySelector('.h-clock').innerHTML = clock();
    el.querySelector('.h-weather').innerHTML = weather();
    el.querySelector('.h-hero-slot').innerHTML = hero();
    el.querySelector('.h-lanes').innerHTML = lanes();
    paintChores();
    el.querySelector('.h-shop').innerHTML = shopping();
    el.querySelector('.h-status').innerHTML = status();
  }

  function photoCaption(s) {
    var cap = V.el.querySelector('.h-photo-cap');
    if (!s.photos[0]) { cap.innerHTML = ''; return; }
    var m = App.photoMeta(s.photos[0]);
    V.el.querySelector('.h-photo-cap').innerHTML = '<b>' + (m.onThisDay ? App.t('on_this_day') + ' · ' : '') + m.kicker + '</b>' + (m.place ? '<span>' + App.esc(m.place) + '</span>' : '');
  }

  App.register('home', {
    show: function (el) {
      V.el = el;
      if (!el.firstChild) {
        el.innerHTML = '<div class="home">' +
          '<div class="h-clock" data-go="calendar"></div>' +
          '<div class="h-weather"></div>' +
          '<div class="h-main"><div class="h-hero-slot"></div><div class="h-lanes" ></div></div>' +
          '<div class="h-side">' +
          '  <button class="h-photo" data-go="photos"><div class="h-photo-stage"></div><div class="h-photo-cap"></div></button>' +
          '  <button class="h-chores card" data-go="calendar"></button>' +
          '  <div class="h-duo"><button class="h-shop card" data-go="shopping"></button><button class="h-status card" data-go="house"></button></div>' +
          '</div></div>';
        el.addEventListener('click', function (e) {
          var ch = e.target.closest('[data-chore]');
          if (ch) {
            var id = ch.dataset.chore, who = ch.dataset.person;
            var item = D.chores.items.filter(function (i) { return i.id === id && i.person === who; })[0];
            App.backend.chore(id, who, true);
            App.toast(App.t('ch_done_toast', { name: App.esc(item ? item.title : '') }), { icon: 'check', ms: 5000, undo: function () { App.backend.chore(id, who, false); } });
            return;
          }
          var ev = e.target.closest('[data-ev]');
          if (ev) { App.eventSheet(App.findEvent(ev.dataset.ev)); return; }
          var g = e.target.closest('[data-go]');
          if (g) App.go(g.dataset.go);
        });
        V.slides = new App.Slideshow(el.querySelector('.h-photo-stage'), { layout: 'auto', captions: false, onChange: photoCaption });
      }
      paint();
      V.slides.start();
    },
    resume: function () { V.slides.start(); },
    hide: function () { if (V.slides) V.slides.stop(); }
  });
  // Every minute: just the clock and next-up countdown (cheap, even while hidden). Weather on the hour.
  App.on('minute', function (n) {
    if (!V.el || !V.el.firstChild) return;
    V.el.querySelector('.h-clock').innerHTML = clock();
    V.el.querySelector('.h-hero-slot').innerHTML = hero();
    paintChores();
    if (n.getMinutes() === 0) { V.el.querySelector('.h-weather').innerHTML = weather(); V.el.querySelector('.h-lanes').innerHTML = lanes(); }
  });
  App.on('data', function () { if (App.current === 'home') paint(); });
  App.on('chores', function () { if (App.current === 'home') paint(); else if (App.views.home) App.views.home._dirty = true; });
})();
