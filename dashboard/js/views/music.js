// Música: shows what Spotify is playing and drives the Spotify Connect speakers of the house. The frame itself
// makes no sound here; the backend talks to Spotify and the frame only sends commands and draws the answer.
(function () {
  'use strict';
  var V = { el: null, st: null, devices: [], lists: null, results: null, tab: 'lists', q: '', err: '', poll: 0, tick: 0, sig: '', at: 0, busy: false };

  function req(method, path, body) { return App.backend.request(method, path, body, { timeout: 9000 }); }
  function esc(s) { return App.esc(s == null ? '' : s); }
  function fmt(ms) { var s = Math.max(0, Math.round(ms / 1000)); return Math.floor(s / 60) + ':' + (s % 60 < 10 ? '0' : '') + (s % 60); }

  function fail(e) {
    V.err = e && e.status === 409 ? 'off' : 'err';
    paintAll();
  }

  function refresh() {
    if (!V.el || App.current !== 'music' || V.busy) return;
    V.busy = true;
    req('GET', '/api/v1/device/music/state').then(function (s) {
      V.st = s; V.at = Date.now(); V.err = '';
      if (!s.active || !V.devices.length) return loadDevices();
    }).then(function () { V.busy = false; paintNow(); }, function (e) { V.busy = false; fail(e); });
  }
  function loadDevices() {
    return req('GET', '/api/v1/device/music/devices').then(function (d) { V.devices = d; paintSpeakers(); });
  }
  function loadLists() {
    if (V.lists) return;
    req('GET', '/api/v1/device/music/playlists').then(function (l) { V.lists = l; paintBrowse(); }, function () { V.lists = []; paintBrowse(); });
  }

  function targetDevice() {
    if (V.st && V.st.active && V.st.device && V.st.device.id) return V.st.device.id;
    var active = V.devices.filter(function (d) { return d.active; })[0] || V.devices[0];
    return active ? active.id : null;
  }
  function control(body) {
    return req('POST', '/api/v1/device/music/control', body).then(function () {
      setTimeout(function () { V.busy = false; refresh(); }, 700);
    }, function (e) {
      App.toast(e.status === 404 ? App.t('mu_nodev2') : (e.message || App.t('mu_err')), { icon: 'bell', ms: 5000 });
    });
  }
  function playPause() {
    var st = V.st;
    if (st && st.active && st.playing) { st.playing = false; paintNow(true); return control({ action: 'pause' }); }
    var dev = targetDevice();
    if (st && st.active) { st.playing = true; paintNow(true); }
    return control({ action: 'play', device_id: dev || undefined });
  }
  function playUri(uri) {
    var dev = targetDevice();
    if (!dev) { App.toast(App.t('mu_nodev2'), { icon: 'bell', ms: 5000 }); return; }
    return control({ action: 'play', uri: uri, device_id: dev });
  }
  function bump(delta) {
    var cur = V.st && V.st.device && V.st.device.volume != null ? V.st.device.volume : 30;
    var v = Math.max(0, Math.min(100, cur + delta));
    if (V.st && V.st.device) { V.st.device.volume = v; paintNow(true); }
    return control({ action: 'volume', volume: v, device_id: targetDevice() || undefined });
  }

  // ------------------------------------------------------------ drawing
  function art(url, cls) {
    return url ? '<img class="' + cls + '" src="' + esc(url) + '" alt="" referrerpolicy="no-referrer">' : '<div class="' + cls + ' mu-noart">' + App.icon('music', 40) + '</div>';
  }

  function nowHtml() {
    if (V.err === 'off') return '<div class="mu-msg serif">' + App.t('mu_off') + '<br><i>' + App.t('mu_off2') + '</i></div>';
    if (V.err === 'err' && !V.st) return '<div class="mu-msg serif">' + App.t('mu_err') + '</div>';
    var s = V.st;
    if (!s || !s.active || !s.track) {
      var none = V.devices.length === 0 && s;
      return '<div class="mu-msg serif">' + (none ? App.t('mu_nodev') + '<br><i>' + App.t('mu_nodev2') + '</i>' : App.t('mu_nothing') + '<br><i>' + App.t('mu_nothing2') + '</i>') + '</div>' +
        (V.devices.length ? '<div class="mu-ctl"><button class="mu-play" data-act="play" aria-label="Play">' + App.icon('play', 44) + '</button></div>' : '');
    }
    var tr = s.track, vol = s.device && s.device.volume != null ? s.device.volume : null;
    return art(tr.art, 'mu-art') +
      '<div class="mu-info"><b class="mu-title serif">' + esc(tr.name) + '</b><span class="mu-artist">' + esc(tr.artists) + '</span>' +
      '<small class="mu-album">' + esc(tr.album) + '</small></div>' +
      '<div class="mu-bar"><i id="muBar"></i></div><div class="mu-times num"><span id="muPos">0:00</span><span>' + fmt(tr.duration_ms) + '</span></div>' +
      '<div class="mu-ctl"><button class="mu-sk" data-act="previous" aria-label="Previous">' + App.icon('skipp', 40) + '</button>' +
      '<button class="mu-play" data-act="play" aria-label="Play or pause">' + App.icon(s.playing ? 'pause' : 'play', 44) + '</button>' +
      '<button class="mu-sk" data-act="next" aria-label="Next">' + App.icon('skipn', 40) + '</button></div>' +
      (vol == null ? '' : '<div class="mu-vol"><button class="mu-sk" data-vol="-10" aria-label="Volume down">' + App.icon('minus', 30) + '</button>' +
        App.icon('vol', 30) + '<b class="num">' + vol + '</b><button class="mu-sk" data-vol="10" aria-label="Volume up">' + App.icon('plus', 30) + '</button></div>');
  }

  function speakersHtml() {
    var cur = V.st && V.st.active && V.st.device ? V.st.device.id : null;
    return V.devices.map(function (d) {
      return '<button class="mu-spk' + (d.id === cur || (!cur && d.active) ? ' is-on' : '') + '" data-dev="' + esc(d.id) + '">' + esc(d.name) + '</button>';
    }).join('');
  }

  function rowsHtml(items) {
    if (items == null) return '<div class="mu-empty">…</div>';
    if (!items.length) return '<div class="mu-empty">' + App.t('mu_empty') + '</div>';
    return items.map(function (i) {
      return '<button class="mu-row" data-uri="' + esc(i.uri) + '">' + art(i.art, 'mu-thumb') +
        '<span class="mu-rt"><b>' + esc(i.name) + '</b><small>' + esc(i.sub) + '</small></span>' +
        '<em>' + App.t('mu_' + i.kind) + '</em></button>';
    }).join('');
  }

  function browseHtml() {
    return '<div class="mu-tabs"><button class="mu-tab' + (V.tab === 'lists' ? ' is-on' : '') + '" data-tab="lists">' + App.t('mu_lists') + '</button>' +
      '<button class="mu-tab' + (V.tab === 'search' ? ' is-on' : '') + '" data-tab="search">' + App.t('mu_search') + '</button></div>' +
      (V.tab === 'search' ? '<form class="mu-form" id="muForm"><input id="muQ" type="search" enterkeyhint="search" autocomplete="off" placeholder="' + esc(App.t('mu_search_ph')) + '" value="' + esc(V.q) + '"><button type="submit" aria-label="Search">' + App.icon('search', 30) + '</button></form>' : '') +
      '<div class="mu-list">' + rowsHtml(V.tab === 'search' ? V.results : V.lists) + '</div>';
  }

  function shell() {
    return '<div class="mu"><header class="mu-head"><div><div class="label">' + App.t('mu_kicker') + '</div><h1 class="serif">' + App.t('nav_music') + '</h1></div>' +
      '<div class="mu-spks" id="muSpk"></div></header>' +
      '<div class="mu-body"><section class="mu-now card" id="muNow"></section><section class="mu-browse" id="muBrowse"></section></div></div>';
  }

  function paintSpeakers() { var el = V.el && V.el.querySelector('#muSpk'); if (el) el.innerHTML = speakersHtml(); }
  function paintBrowse() { var el = V.el && V.el.querySelector('#muBrowse'); if (el) { el.innerHTML = browseHtml(); } }
  // Only rebuild the card when something visible changed; polling must not keep the page busy.
  function paintNow(force) {
    if (!V.el) return;
    var s = V.st, sig = JSON.stringify([V.err, s && s.active, s && s.playing, s && s.track && s.track.uri, s && s.device && s.device.volume, V.devices.length]);
    if (force || sig !== V.sig) { V.sig = sig; var el = V.el.querySelector('#muNow'); if (el) el.innerHTML = nowHtml(); paintSpeakers(); }
    progress();
  }
  function paintAll() { V.sig = ''; paintNow(true); }
  function progress() {
    var s = V.st; if (!V.el || !s || !s.active || !s.track) return;
    var pos = s.progress_ms + (s.playing ? Date.now() - V.at : 0), dur = s.track.duration_ms || 1;
    pos = Math.min(pos, dur);
    var bar = V.el.querySelector('#muBar'), t = V.el.querySelector('#muPos');
    if (bar) bar.style.width = (pos / dur * 100).toFixed(1) + '%';
    if (t) t.textContent = fmt(pos);
  }

  function search() {
    var q = (V.q || '').trim();
    if (!q) return;
    V.results = null; paintBrowse();
    req('GET', '/api/v1/device/music/search?q=' + encodeURIComponent(q)).then(function (r) { V.results = r; paintBrowse(); }, function () { V.results = []; paintBrowse(); });
  }

  function start() {
    stop();
    refresh(); loadLists();
    V.poll = setInterval(refresh, 5000);
    V.tick = setInterval(progress, 1000);
  }
  function stop() { clearInterval(V.poll); clearInterval(V.tick); V.poll = V.tick = 0; }

  App.register('music', {
    hide: stop,
    show: function (el) {
      if (!V.el) {
        V.el = el;
        el.innerHTML = shell();
        el.addEventListener('click', function (e) {
          var b;
          if ((b = e.target.closest('[data-act]'))) { b.dataset.act === 'play' ? playPause() : control({ action: b.dataset.act, device_id: targetDevice() || undefined }); }
          else if ((b = e.target.closest('[data-vol]'))) bump(+b.dataset.vol);
          else if ((b = e.target.closest('[data-dev]'))) { control({ action: 'transfer', device_id: b.dataset.dev }); }
          else if ((b = e.target.closest('[data-tab]'))) { V.tab = b.dataset.tab; paintBrowse(); }
          else if ((b = e.target.closest('[data-uri]'))) playUri(b.dataset.uri);
        });
        el.addEventListener('input', function (e) { if (e.target.id === 'muQ') V.q = e.target.value; });
        el.addEventListener('submit', function (e) { e.preventDefault(); search(); });
      }
      paintBrowse(); paintAll();
      start();
    }
  });
  App.on('mode', function (m) { if (m !== 'day') stop(); });
})();
