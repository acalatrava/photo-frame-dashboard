// Casa: live Home Assistant entities. Controls only work while the backend reports a live HA connection.
(function () {
  'use strict';
  var D = window.DATA, V = { el: null, busy: {}, filter: 'all' };
  var NUMERIC = { temperature: '°C', humidity: '%' };

  function meta(e) { return (D.ha.meta && D.ha.meta[e.entity_id]) || {}; }
  function name(e) { return meta(e).name || (e.attributes && e.attributes.friendly_name) || e.entity_id; }
  function icon(e, fallback) { return meta(e).icon || fallback; }
  // A custom colour tints the tile; the text colour is picked for contrast.
  function tint(e, on) {
    var c = meta(e).color, m = /^#([0-9a-f]{6})$/i.exec(c || '');
    if (!m || !on) return '';
    var n = parseInt(m[1], 16), lum = (0.299 * (n >> 16) + 0.587 * ((n >> 8) & 255) + 0.114 * (n & 255)) / 255;
    return ' style="background:' + c + ';color:' + (lum > 0.62 ? '#111' : '#fff') + '"';
  }
  function domain(e) { return e.entity_id.split('.')[0]; }
  function live() { return D.ha.connected && App.backend.online; }
  function pct(e) { var b = e.attributes.brightness; return b == null ? null : Math.round(b / 255 * 100); }
  function num(v) { var n = parseFloat(v); return isNaN(n) ? v : (Math.round(n * 10) / 10).toString().replace('.', App.locale === 'en' ? '.' : ','); }
  function dis() { return live() ? '' : ' disabled'; }

  function lightTile(e) {
    var on = e.state === 'on', p = pct(e);
    return '<div class="hz-tile hz-light' + (on ? ' is-on' : '') + '"' + tint(e, on) + '>' +
      '<button class="hz-main"' + dis() + ' data-toggle="' + e.entity_id + '">' + App.icon(icon(e, 'bulb'), 34) +
      '<span class="hz-name">' + App.esc(name(e)) + '</span><span class="hz-state">' + (e.state === 'unavailable' ? App.t('unavailable') : on ? (p != null ? p + '%' : App.t('on')) : App.t('off')) + '</span></button>' +
      (on && e.attributes.brightness != null ? '<input class="hz-slider" type="range" min="1" max="100" value="' + (p || 100) + '" data-bright="' + e.entity_id + '"' + dis() + '>' : '') +
      '</div>';
  }
  function switchTile(e) {
    var on = e.state === 'on';
    return '<div class="hz-tile' + (on ? ' is-on' : '') + '"' + tint(e, on) + '><button class="hz-main"' + dis() + ' data-toggle="' + e.entity_id + '">' + App.icon(icon(e, 'bolt'), 34) +
      '<span class="hz-name">' + App.esc(name(e)) + '</span><span class="hz-state">' + (e.state === 'unavailable' ? App.t('unavailable') : on ? App.t('on') : App.t('off')) + '</span></button></div>';
  }
  function climateTile(e) {
    var a = e.attributes, set = a.temperature, step = a.target_temp_step || 0.5;
    var mode = e.state, action = a.hvac_action;
    return '<div class="hz-tile hz-climate' + (mode !== 'off' && mode !== 'unavailable' ? ' is-on' : '') + '">' +
      '<div class="hz-cl-head">' + App.icon('thermo', 30) + '<span class="hz-name">' + App.esc(name(e)) + '</span><span class="hz-state">' + App.t('hvac_' + mode) + (action && action !== 'idle' && action !== 'off' ? ' · ' + App.t('hvac_' + action) : '') + '</span></div>' +
      '<div class="hz-cl-row"><div class="hz-cl-now"><b class="num">' + (a.current_temperature != null ? num(a.current_temperature) : '–') + '°</b><small>' + App.t('inside') + '</small></div>' +
      (set != null ? '<div class="hz-cl-set"><button' + dis() + ' data-temp="' + e.entity_id + '" data-d="' + (-step) + '" aria-label="-">' + App.icon('minus', 26) + '</button><b class="num">' + num(set) + '°</b><button' + dis() + ' data-temp="' + e.entity_id + '" data-d="' + step + '" aria-label="+">' + App.icon('plus', 26) + '</button></div>' : '') + '</div>' +
      (a.hvac_modes && a.hvac_modes.length > 1 ? '<div class="seg hz-modes">' + a.hvac_modes.slice(0, 4).map(function (m) {
        return '<button' + dis() + ' class="' + (m === mode ? 'is-on' : '') + '" data-hvac="' + e.entity_id + '" data-mode="' + m + '">' + App.t('hvac_' + m) + '</button>';
      }).join('') + '</div>' : '') + '</div>';
  }
  function sensorTile(e) {
    var dc = e.attributes.device_class, unit = e.attributes.unit_of_measurement || NUMERIC[dc] || '';
    var icon = dc === 'humidity' ? 'drop' : dc === 'temperature' ? 'thermo' : 'bolt';
    var val = e.state === 'unavailable' || e.state === 'unknown' ? '–' : num(e.state);
    return '<div class="hz-tile hz-sensor"><div class="hz-s-ic">' + App.icon(icon, 28) + '</div><span class="hz-name">' + App.esc(name(e)) + '</span><b class="num">' + val + '<small>' + App.esc(unit) + '</small></b></div>';
  }
  function binaryTile(e) {
    var on = e.state === 'on', dc = e.attributes.device_class;
    var label = on ? App.t('bin_on_' + (dc === 'door' || dc === 'window' || dc === 'opening' ? 'open' : dc === 'motion' || dc === 'occupancy' || dc === 'presence' ? 'motion' : 'generic')) :
      App.t('bin_off_' + (dc === 'door' || dc === 'window' || dc === 'opening' ? 'open' : dc === 'motion' || dc === 'occupancy' || dc === 'presence' ? 'motion' : 'generic'));
    return '<div class="hz-tile hz-sensor' + (on ? ' is-on' : '') + '"><div class="hz-s-ic">' + App.icon('person', 28) + '</div><span class="hz-name">' + App.esc(name(e)) + '</span><b>' + label + '</b></div>';
  }
  function actionTile(e) {
    var scene = domain(e) === 'scene', m = meta(e);
    return '<button class="hz-tile hz-action' + (m.color ? ' is-tinted' : '') + '"' + dis() + ' data-run="' + e.entity_id + '"' + tint(e, true) + '>' + App.icon(icon(e, scene ? 'film' : 'bolt'), 52) +
      '<span class="hz-name">' + App.esc(name(e)) + '</span></button>';
  }

  var COVER_STATE = { open: 'cover_open', closed: 'cover_closed', opening: 'cover_opening', closing: 'cover_closing' };
  function coverTile(e) {
    var a = e.attributes, feat = a.supported_features == null ? 11 : a.supported_features, pos = a.current_position;
    var moving = e.state === 'opening' || e.state === 'closing';
    var state = e.state === 'unavailable' ? App.t('unavailable') : (COVER_STATE[e.state] ? App.t(COVER_STATE[e.state]) : e.state) + (pos != null && !moving ? ' · ' + pos + '%' : '');
    var id = e.entity_id;
    return '<div class="hz-tile hz-cover' + (e.state === 'open' || moving ? ' is-on' : '') + '"' + tint(e, e.state !== 'closed') + '>' +
      '<div class="hz-cv-head">' + App.icon(icon(e, 'blinds'), 34) + '<span class="hz-name">' + App.esc(name(e)) + '</span></div>' +
      '<span class="hz-state">' + state + '</span>' +
      '<div class="hz-cv-btns">' +
      (feat & 1 ? '<button' + dis() + ' data-cover="' + id + '" data-svc="open_cover" aria-label="' + App.t('cover_up') + '">' + App.icon('up', 38) + '</button>' : '') +
      (feat & 8 ? '<button' + dis() + ' data-cover="' + id + '" data-svc="stop_cover" aria-label="' + App.t('cover_stop') + '">' + App.icon('stop', 30) + '</button>' : '') +
      (feat & 2 ? '<button' + dis() + ' data-cover="' + id + '" data-svc="close_cover" aria-label="' + App.t('cover_down') + '">' + App.icon('down', 38) + '</button>' : '') +
      '</div>' +
      ((feat & 4) && pos != null ? '<input class="hz-slider" type="range" min="0" max="100" value="' + pos + '" data-pos="' + id + '"' + dis() + '>' : '') +
      '</div>';
  }

  function group(title, tiles, cls) {
    return tiles.length ? '<section class="hz-group"><div class="label">' + title + '</div><div class="hz-grid' + (cls ? ' ' + cls : '') + '">' + tiles.join('') + '</div></section>' : '';
  }

  function html() {
    var ents = D.ha.entities.slice();
    var by = function (d, fn) { return ents.filter(function (e) { return domain(e) === d; }).map(fn); };
    var sensors = ents.filter(function (e) { return domain(e) === 'sensor'; }).map(sensorTile);
    var bin = ents.filter(function (e) { return domain(e) === 'binary_sensor'; }).map(binaryTile);
    var status = !D.ha.enabled ? '' : (live() ? '<span class="hz-live"><i></i>' + App.t('live') + '</span>' :
      '<span class="hz-live is-off"><i></i>' + App.t(D.ha.connected ? 'no_backend' : 'ha_down') + '</span>');
    var head = '<header class="hz-head"><div><div class="label">' + App.t('house_kicker') + '</div><h1 class="serif">' + App.t('nav_house') + '</h1></div>' + status + '</header>';
    if (!D.ha.enabled || !ents.length) {
      return '<div class="hz">' + head + '<div class="hz-empty serif">' + App.t(D.ha.enabled ? 'house_no_entities' : 'house_not_configured') + '<br><i>' + App.t('house_hint') + '</i></div></div>';
    }
    return '<div class="hz">' + head + (!live() ? '<div class="hz-banner">' + App.icon('bolt', 24) + '<span>' + App.t('house_last_state') + '</span></div>' : '') +
      '<div class="hz-body">' +
      group(App.t('g_scenes'), ents.filter(function (e) { return domain(e) === 'scene' || domain(e) === 'script'; }).map(actionTile), 'hz-grid--scenes') +
      group(App.t('g_climate'), by('climate', climateTile)) +
      group(App.t('g_lights'), by('light', lightTile)) +
      group(App.t('g_covers'), by('cover', coverTile)) +
      group(App.t('g_switches'), by('switch', switchTile)) +
      group(App.t('g_sensors'), sensors.concat(bin)) +
      '</div></div>';
  }

  function paint() {
    if (!V.el) return;
    var sc = V.el.querySelector('.hz-body');
    var top = sc ? sc.scrollTop : 0;
    V.el.innerHTML = html();
    sc = V.el.querySelector('.hz-body');
    if (sc) sc.scrollTop = top;
  }

  function call(id, service, data, tile) {
    if (V.busy[id]) return;
    V.busy[id] = true;
    if (tile) tile.classList.add('is-busy');
    App.backend.callService(id, service, data).catch(function (e) {
      App.toast(App.t(e && e.message === 'offline' ? 'ha_offline_toast' : 'ha_error_toast'), { icon: 'bolt', tone: 'error', ms: 4000 });
    }).then(function () { delete V.busy[id]; if (tile) tile.classList.remove('is-busy'); });
  }
  function find(id) { return D.ha.entities.filter(function (e) { return e.entity_id === id; })[0]; }

  var sliderTimer = null;
  function onClick(ev) {
    var t;
    if ((t = ev.target.closest('[data-toggle]'))) {
      var e = find(t.dataset.toggle);
      call(t.dataset.toggle, e && e.state === 'on' ? 'turn_off' : 'turn_on', {}, t.closest('.hz-tile'));
    } else if ((t = ev.target.closest('[data-run]'))) {
      call(t.dataset.run, 'turn_on', {}, t);
      App.toast(App.t('ran', { name: App.esc(name(find(t.dataset.run))) }), { icon: 'check', ms: 2500 });
    } else if ((t = ev.target.closest('[data-cover]'))) {
      call(t.dataset.cover, t.dataset.svc, {}, t.closest('.hz-tile'));
    } else if ((t = ev.target.closest('[data-temp]'))) {
      var c = find(t.dataset.temp), a = c.attributes;
      var next = Math.round((a.temperature + parseFloat(t.dataset.d)) * 10) / 10;
      next = Math.max(a.min_temp || 7, Math.min(a.max_temp || 30, next));
      call(t.dataset.temp, 'set_temperature', { temperature: next });
    } else if ((t = ev.target.closest('[data-hvac]'))) {
      call(t.dataset.hvac, 'set_hvac_mode', { hvac_mode: t.dataset.mode });
    }
  }
  function onInput(ev) {
    var t = ev.target.closest('[data-bright],[data-pos]');
    if (!t) return;
    clearTimeout(sliderTimer);
    sliderTimer = setTimeout(function () {
      if (t.dataset.pos) call(t.dataset.pos, 'set_cover_position', { position: +t.value });
      else call(t.dataset.bright, 'turn_on', { brightness_pct: +t.value });
    }, 350);
  }

  App.register('house', {
    minutely: false,
    show: function (el) {
      if (!V.el) { V.el = el; el.addEventListener('click', onClick); el.addEventListener('input', onInput); }
      paint();
    }
  });
  App.on('ha', function () { if (App.current === 'house') paint(); else if (App.views.house) App.views.house._dirty = true; });
  App.on('conn', function () { if (App.current === 'house') paint(); });
})();
