// Backend client: pairing, configuration, live data (SSE), offline cache and the shopping queue.
// Credentials never leave the frame: the device token is kept in native preferences when the Android
// shell is present, and in localStorage otherwise (browser preview).
(function () {
  'use strict';
  var D = window.DATA;
  var N = window.HQNative || null;
  var K = { url: 'hq.backend', token: 'hq.token', device: 'hq.device', cache: 'hq.cache.dashboard', cfg: 'hq.cache.config', queue: 'hq.shop.queue', cq: 'hq.chore.queue' };
  var PALETTE_INK = { light: '#111111', dark: '#FFFFFF' };

  // With the Android shell, values (including the device token) live only in native private preferences.
  // In a plain browser (preview) they fall back to localStorage.
  function native() { return !!(N && N.getPref && N.setPref); }
  function sget(k) {
    if (native()) {
      try { return N.getPref(k) || ''; } catch (e) { return ''; }
    }
    try { return localStorage.getItem(k); } catch (e) { return null; }
  }
  function sset(k, v) {
    if (native()) {
      try { N.setPref(k, v == null ? '' : String(v)); } catch (e) { /* ignore */ }
      return;
    }
    try { if (v == null) localStorage.removeItem(k); else localStorage.setItem(k, v); } catch (e) { /* ignore */ }
  }
  function jget(k, fallback) { try { return JSON.parse(sget(k)) || fallback; } catch (e) { return fallback; } }

  var B = App.backend = { online: false, paired: false, cfg: null, lastSync: 0, readonly: false };
  B.store = { get: sget, set: sset };

  // ------------------------------------------------------------ transport
  B.url = function () { return (sget(K.url) || '').replace(/\/+$/, ''); };
  B.setUrl = function (u) {
    u = (u || '').trim().replace(/\/+$/, '');
    if (u && !/^https?:\/\//i.test(u)) u = 'http://' + u;
    sset(K.url, u);
    return u;
  };
  B.token = function () { return sget(K.token) || ''; };

  function setOnline(v) {
    if (B.online === v) return;
    B.online = v;
    // Coming back must repaint with the real state, so an identical payload may not be skipped afterwards.
    B._sig = null;
    if (!v && D.ha) { D.ha.connected = false; App.emit('ha'); App.emit('data'); }
    App.emit('conn', v);
  }

  B.request = function (method, path, body, opts) {
    opts = opts || {};
    var base = opts.base || B.url();
    if (!base) return Promise.reject(new Error('no-backend'));
    var ctl = typeof AbortController !== 'undefined' ? new AbortController() : null;
    var timer = ctl ? setTimeout(function () { ctl.abort(); }, opts.timeout || 15000) : null;
    var headers = { Accept: 'application/json' };
    if (body !== undefined) headers['Content-Type'] = 'application/json';
    if (!opts.anon && B.token()) headers.Authorization = 'Bearer ' + B.token();
    return fetch(base + path, { method: method, headers: headers, body: body === undefined ? undefined : JSON.stringify(body), signal: ctl && ctl.signal, cache: 'no-store' })
      .then(function (r) {
        if (timer) clearTimeout(timer);
        return r.text().then(function (txt) {
          var data = null;
          try { data = txt ? JSON.parse(txt) : null; } catch (e) { data = null; }
          if (r.status === 401 && !opts.anon && B.token()) { B.unpair(true); }
          if (!r.ok) { var err = new Error((data && data.detail) || ('HTTP ' + r.status)); err.status = r.status; throw err; }
          if (!opts.anon) setOnline(true);
          return data;
        });
      }, function (e) {
        if (timer) clearTimeout(timer);
        if (!opts.anon) setOnline(false);
        throw e;
      });
  };

  // ------------------------------------------------------------ locale + time zone
  function applyGeneral(g) {
    var lang = g && g.language === 'en' ? 'en' : 'es-ES';
    var tz = g && g.timezone || 'Europe/Madrid';
    if (g && g.nav_order && App.applyNav) App.applyNav(g.nav_order);
    if (lang !== App.locale || tz !== App.tz) {
      App.locale = lang; App.tz = tz;
      App.initFormat();
    }
  }

  // ------------------------------------------------------------ mapping from API shapes to what the views use
  function hexRgb(hex) {
    var m = /^#?([0-9a-f]{6})$/i.exec(hex || '');
    var n = parseInt(m ? m[1] : '2D5BFF', 16);
    return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
  }
  function mapPerson(p, haState) {
    var c = hexRgb(p.color), lum = (0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]) / 255;
    var home = haState == null ? null : haState === 'home';
    return {
      id: p.id, name: p.name, color: p.color.toUpperCase(), rgb: c.join(' '), ink: lum > 0.62 ? PALETTE_INK.light : PALETTE_INK.dark,
      hasPresence: !!p.has_presence, home: home === null ? false : home, status: home === null ? '' : (home ? 'home' : 'away')
    };
  }
  // Calendar strings are already in the configured time zone. Building the Date from the wall-clock fields
  // keeps every view independent of the frame's own time zone setting.
  function wall(s) {
    var m = /^(\d{4})-(\d{2})-(\d{2})(?:T(\d{2}):(\d{2})(?::(\d{2}))?)?/.exec(s || '');
    if (!m) return new Date(NaN);
    return new Date(+m[1], +m[2] - 1, +m[3], +(m[4] || 0), +(m[5] || 0), +(m[6] || 0));
  }
  function mapEvent(e) {
    var start = wall(e.start), end = wall(e.end);
    if (e.allDay && !(end > start)) end = new Date(+start + 864e5);
    return { id: e.id, title: e.title, start: start, end: end, allDay: !!e.allDay, loc: e.loc || '', notes: e.notes || '', people: e.people || [] };
  }
  function mapWeather(w) {
    if (!w || !w.t) return null;
    var today = App.dayStart(App.now()), base = wall(w.date);
    var shift = Math.round((today - base) / 864e5) * 24;
    if (shift < 0 || shift > 24) return null;
    function slice(a, fill) { var out = []; for (var i = 0; i < 24; i++) { var v = a[i + shift]; out.push(v == null ? fill : v); } return out; }
    var t = slice(w.t, null);
    if (t.every(function (x) { return x == null; })) return null;
    return { hi: w.hi, lo: w.lo, feels: w.feels, humidity: w.humidity, wind: w.wind, t: t, c: slice(w.c, 'cloud'), p: slice(w.p, 0), stale: !!w.stale };
  }
  function mapPhoto(p) {
    var base = B.url();
    return { id: p.id, o: p.o, date: p.date, caption: p.caption || '', thumb: base + p.thumb, screen: base + p.screen };
  }

  B.apply = function (dash, fromCache) {
    var cfg = B.cfg || {};
    var haPeople = (dash.ha && dash.ha.people) || {};
    D.people = (cfg.people || []).map(function (p) { return mapPerson(p, haPeople[p.id]); });
    D.ALL = D.people.map(function (p) { return p.id; });
    D.events = (dash.events || []).map(mapEvent).filter(function (e) { return !isNaN(+e.start); });
    D.ha = dash.ha || { enabled: false, connected: false, entities: [] };
    if (fromCache) D.ha.connected = false;
    D.weather = mapWeather(dash.weather);
    D.photos = (dash.photos || []).map(mapPhoto);
    D.presence = dash.presence || { ha_active: null };
    D.notices = dash.notices || [];
    if (dash.shopping) applyShopping(dash.shopping);
    applyChores(dash.chores);
    D.music = dash.music || { configured: false };
    D.menu = dash.menu || { configured: false, meals: [], weeks: [], start_week: 1, start_date: '' };
    var base = B.url();
    D.cameras = (dash.cameras || []).map(function (c) { return { id: c.id, name: c.name, snapshot: base + c.snapshot, stream: base + c.stream }; });
    B.lastSync = fromCache ? B.lastSync : Date.now();
    App.emit('data');
  };

  function applyShopping(s) {
    D.shopping.provider = s.provider;
    D.shopping.ok = s.ok !== false;
    D.shopping.stale = s.ok === false;
    D.shopping.error = s.error || '';
    D.groceries = (s.items || []).map(function (i) { return { id: i.id, name: i.name, note: i.note || '', done: !!i.done, qty: i.quantity || 1 }; });
    reapplyQueue();
  }

  function applyChores(c) {
    c = c || { day: '', items: [] };
    D.chores = {
      day: c.day, configured: c.configured || 0,
      items: (c.items || []).map(function (i) { return { id: i.id, title: i.title, icon: i.icon || 'tasks', person: i.person_id || '', time: i.time || '', done: !!i.done, once: !!i.once, overdue: !!i.overdue }; })
    };
    (cqueue()).forEach(applyChoreOp);
  }

  // ------------------------------------------------------------ boot, cache and refresh
  // Applies a dashboard payload only when it differs from the last one. Most refreshes bring the same data, and
  // rebuilding every screen for nothing blocks the page (and with it the touch screen) on this slow hardware.
  function ingest(dash) {
    // server_time changes on every call; leaving it out is what lets identical data be recognised.
    var st = dash.server_time;
    delete dash.server_time;
    var raw = JSON.stringify(dash), sig = App.dayStart(App.now()).getTime() + '|' + raw;
    dash.server_time = st;
    if (sig === B._sig) { B.lastSync = Date.now(); return false; }
    B._sig = sig;
    sset(K.cache, '{"at":' + Date.now() + ',"dash":' + raw + '}');
    B.apply(dash, false);
    return true;
  }

  B.sync = function () {
    return B.request('GET', '/api/v1/device/bootstrap').then(function (b) {
      B.cfg = b.config;
      sset(K.cfg, JSON.stringify(b.config));
      applyGeneral(b.config.general);
      App.emit('config', b.config);
      return B.request('GET', '/api/v1/device/dashboard');
    }).then(function (dash) {
      ingest(dash);
      flushQueue(); flushChores();
      B.openStream();
    });
  };

  B.refreshDashboard = function () {
    return B.request('GET', '/api/v1/device/dashboard').then(function (dash) {
      ingest(dash);
    }).catch(function () { /* offline: keep what we have */ });
  };

  B.hydrateFromCache = function () {
    var cfg = jget(K.cfg, null), c = jget(K.cache, null);
    if (!cfg) return false;
    B.cfg = cfg;
    applyGeneral(cfg.general);
    if (c && c.dash) { B.lastSync = c.at; B.apply(c.dash, true); }
    return true;
  };

  var retryTimer = null, retryDelay = 3000;
  function scheduleRetry() {
    clearTimeout(retryTimer);
    retryTimer = setTimeout(boot, retryDelay);
    retryDelay = Math.min(60000, retryDelay * 2);
  }
  function boot() {
    B.sync().then(function () { retryDelay = 3000; }, function (e) {
      if (e && e.status === 401) return;
      scheduleRetry();
    });
  }

  B.start = function () {
    B.paired = !!(B.url() && B.token());
    if (!B.paired) { App.setup.show(); return; }
    var have = B.hydrateFromCache();
    App.setup.hide();
    if (have) App.go(App.current || 'home', { rerender: true });
    boot();
    setInterval(function () { if (B.paired) B.heartbeat(); }, 60000);
    setInterval(function () { if (B.paired && B.online) B.refreshDashboard(); }, 5 * 60000);
    setInterval(function () { if (B.paired && !B.online) boot(); }, 30000);
    setTimeout(function () { B.heartbeat(); }, 5000);
    setInterval(B.telemetry, 5000);
  };

  // Everything that belongs to the previous pairing (cached data, queue, WebView image cache) is dropped so
  // a frame moved to another server never shows the old server's photos or lists.
  function forgetPairing() {
    sset(K.token, null); sset(K.device, null); sset(K.cache, null); sset(K.cfg, null); sset(K.queue, null); sset(K.cq, null);
    B._sig = null;
    D.photos = []; D.chores = { day: '', items: [] }; D.cameras = []; D.events = [];
    D.music = { configured: false };
    D.menu = { configured: false, meals: [], weeks: [], start_week: 1, start_date: '' };
    if (N && N.clearWebCache) { try { N.clearWebCache(); } catch (e) { /* ignore */ } }
  }

  B.unpair = function (revoked) {
    forgetPairing();
    B.paired = false; B.online = false;
    if (B.stream) { B.stream.abort = true; try { B.stream.ctl.abort(); } catch (e) { /* ignore */ } B.stream = null; }
    App.setup.show(revoked ? 'revoked' : null);
  };

  // Light-sensor samples feed the live graph in the admin panel (and the calibration recordings).
  var telemetryT = 0;
  B.telemetry = function () {
    if (!B.paired || !B.online || !App.native.available) return;
    var batch = App.native.sensor.samples.filter(function (s) { return s[0] > telemetryT; });
    if (!batch.length) return;
    var top = batch[batch.length - 1][0];
    return B.request('POST', '/api/v1/device/telemetry', { samples: batch.slice(-300) }, { timeout: 8000 }).then(function (r) {
      telemetryT = top;
      var rec = !!(r && r.recording);
      if (rec !== B.recording) { B.recording = rec; App.emit('recording', rec); }
    }, function () { /* kept for the next round */ });
  };

  B.heartbeat = function () {
    var status = {};
    try { if (N && N.getStatus) status = JSON.parse(N.getStatus()); } catch (e) { /* ignore */ }
    status.online = B.online;
    if (App.display) status.screen = App.display.screen;
    status.ua = (navigator.userAgent.match(/Chrome\/[\d.]+/) || [''])[0];
    if (App.perf) status.perf = App.perf.report();
    var version = '';
    try { version = N && N.getVersion ? N.getVersion() : ''; } catch (e) { version = ''; }
    return B.request('POST', '/api/v1/device/heartbeat', { app_version: version || null, status: status }).then(function (r) {
      if (r && r.server_time) B.checkClock(r.server_time * 1000);
      B.recording = !!(r && r.recording);
      return r;
    }).catch(function () { /* offline */ });
  };

  // The frame's clock may drift (no RTC battery). Report the difference so the UI can warn about it.
  B.clockSkewMs = 0;
  B.checkClock = function (serverMs) {
    B.clockSkewMs = Date.now() - serverMs;
    App.emit('clock', B.clockSkewMs);
  };

  // ------------------------------------------------------------ pairing
  var PAIR = { id: null, secret: null, timer: null };
  B.pairing = {
    begin: function (url, onState) {
      B.setUrl(url);
      clearTimeout(PAIR.timer);
      var info = {};
      try { info = JSON.parse(N && N.getDeviceInfo ? N.getDeviceInfo() : '{}'); } catch (e) { info = {}; }
      var version = '';
      try { version = N && N.getVersion ? N.getVersion() : ''; } catch (e) { version = ''; }
      return B.request('POST', '/api/v1/pairing/request', {
        name: info.name || 'Home HQ', model: info.model || navigator.userAgent.slice(0, 60), app_version: version, screen: screen.width + 'x' + screen.height
      }, { anon: true }).then(function (r) {
        PAIR.id = r.request_id; PAIR.secret = r.poll_secret;
        onState({ status: 'pending', code: r.code, expires_at: r.expires_at });
        poll(onState);
        return r;
      });
    },
    cancel: function () { clearTimeout(PAIR.timer); PAIR.id = null; }
  };
  function poll(onState) {
    clearTimeout(PAIR.timer);
    if (!PAIR.id) return;
    PAIR.timer = setTimeout(function () {
      B.request('POST', '/api/v1/pairing/' + PAIR.id + '/poll', { poll_secret: PAIR.secret }, { anon: true }).then(function (r) {
        if (r.status === 'approved') {
          forgetPairing();
          sset(K.token, r.device_token); sset(K.device, r.device_id);
          PAIR.id = null; PAIR.secret = null;
          B.paired = true;
          onState({ status: 'approved' });
          B.start();
        } else if (r.status === 'pending') {
          poll(onState);
        } else {
          onState({ status: r.status });
        }
      }, function (e) {
        if (e && (e.status === 404 || e.status === 403)) { onState({ status: 'expired' }); return; }
        poll(onState);
      });
    }, 3000);
  }

  // ------------------------------------------------------------ live stream (SSE over fetch so the token stays in a header)
  B.openStream = function () {
    if (B.stream && !B.stream.abort) return;
    var ctl = typeof AbortController !== 'undefined' ? new AbortController() : null;
    var st = B.stream = { ctl: ctl, abort: false };
    fetch(B.url() + '/api/v1/device/events', { headers: { Authorization: 'Bearer ' + B.token(), Accept: 'text/event-stream' }, signal: ctl && ctl.signal, cache: 'no-store' })
      .then(function (r) {
        if (!r.ok || !r.body) throw new Error('stream ' + r.status);
        setOnline(true);
        var reader = r.body.getReader(), dec = new TextDecoder(), buf = '';
        function pump() {
          return reader.read().then(function (x) {
            if (x.done) throw new Error('closed');
            buf += dec.decode(x.value, { stream: true });
            var idx;
            while ((idx = buf.indexOf('\n\n')) >= 0) { handleFrame(buf.slice(0, idx)); buf = buf.slice(idx + 2); }
            return pump();
          });
        }
        return pump();
      })
      .catch(function () { /* fall through to reconnect */ })
      .then(function () {
        if (B.stream === st) B.stream = null;
        if (st.abort || !B.paired) return;
        setOnline(false);
        setTimeout(function () { if (B.paired && !B.stream) { B.refreshDashboard().then(B.openStream); } }, 4000);
      });
  };

  function handleFrame(frame) {
    var ev = 'message', data = '';
    frame.split('\n').forEach(function (l) {
      if (l.indexOf('event:') === 0) ev = l.slice(6).trim();
      else if (l.indexOf('data:') === 0) data += l.slice(5).trim();
    });
    var payload = {};
    try { payload = data ? JSON.parse(data) : {}; } catch (e) { payload = {}; }
    onEvent(ev, payload);
  }

  function onEvent(topic, p) {
    if (topic === 'hello') return;
    if (topic === 'config.changed') { B.sync(); return; }
    if (topic === 'ha.state') {
      var byId = {};
      D.ha.entities.forEach(function (e, i) { byId[e.entity_id] = i; });
      (p.entities || []).forEach(function (s) {
        if (byId[s.entity_id] != null) D.ha.entities[byId[s.entity_id]] = Object.assign({}, D.ha.entities[byId[s.entity_id]], s);
      });
      App.emit('ha');
      return;
    }
    if (topic === 'ha.status') { D.ha.connected = !!p.connected; App.emit('ha'); if (p.connected) B.refreshDashboard(); return; }
    if (topic === 'presence.ha') { D.presence.ha_active = p.active; App.emit('presence'); return; }
    if (topic === 'device.revoked') { B.unpair(true); return; }
    if (topic === 'device.command') { App.emit('command', p.type, p); return; }
    if (topic === 'update.changed') { App.emit('update:published'); return; }
    if (topic === 'recording.changed') { B.recording = !!p.active; App.emit('recording', B.recording); return; }
    // calendar, shopping, photos, weather: refetch the dashboard (small payload, one request)
    B.refreshDashboard();
  }

  // ------------------------------------------------------------ Home Assistant controls
  B.callService = function (entityId, service, data) {
    if (!D.ha.connected || !B.online) return Promise.reject(new Error('offline'));
    return B.request('POST', '/api/v1/device/ha/service', { entity_id: entityId, service: service, data: data || {} });
  };

  // ------------------------------------------------------------ shopping with an offline queue
  // Policy (see backend/app/services/shopping/service.py): operations are optimistic locally, queued with
  // unique ids, and replayed in order once the backend answers. The backend de-duplicates by normalised name
  // and ignores operations on items that no longer exist, so the server snapshot is always the final truth.
  function queue() { return jget(K.queue, []); }
  function saveQueue(q) { sset(K.queue, JSON.stringify(q)); D.shopping.pending = q.length; }
  function newId(prefix) { return prefix + '-' + Date.now().toString(36) + Math.random().toString(36).slice(2, 8); }

  function applyOp(op) {
    var list = D.groceries, it;
    function byId(id) { return list.filter(function (g) { return g.id === id; })[0]; }
    if (op.type === 'add') {
      var n = op.name.trim().toLowerCase();
      it = list.filter(function (g) { return g.name.trim().toLowerCase() === n; })[0];
      if (it) it.done = false;
      else list.push({ id: op.client_id, name: op.name.trim(), note: op.note || '', done: false, qty: 1, local: true });
    } else if (op.type === 'set_done') { it = byId(op.id); if (it) it.done = !!op.done; }
    else if (op.type === 'remove') { D.groceries = list.filter(function (g) { return g.id !== op.id; }); }
    else if (op.type === 'rename') { it = byId(op.id); if (it) it.name = op.name; }
  }
  function reapplyQueue() { var q = queue(); D.shopping.pending = q.length; q.forEach(applyOp); }

  B.shop = function (op) {
    op.op_id = newId('op');
    if (op.type === 'add') op.client_id = newId('tmp');
    applyOp(op);
    B._sig = null;
    var q = queue(); q.push(op); saveQueue(q);
    App.emit('data');
    return flushQueue();
  };

  var flushing = false;
  // Operations queued while a batch is in flight go out right after it; network failures retry on a timer.
  var retryTimer = null;
  function flushQueue() {
    var q = queue();
    if (flushing || !q.length || !B.paired) return Promise.resolve();
    flushing = true;
    var failed = false;
    return B.request('POST', '/api/v1/device/shopping/ops', { ops: q }).then(function (r) {
      var sent = {};
      q.forEach(function (o) { sent[o.op_id] = true; });
      saveQueue(queue().filter(function (o) { return !sent[o.op_id]; }));
      applyShopping(r.shopping);
      App.emit('data');
    }, function (e) {
      // Rejected batches (validation) must not block the queue forever.
      if (e && e.status && e.status >= 400 && e.status < 500 && e.status !== 408 && e.status !== 429 && e.status !== 401) saveQueue([]);
      else failed = true;
    }).then(function () {
      flushing = false;
      if (!queue().length) return;
      if (failed) { clearTimeout(retryTimer); retryTimer = setTimeout(flushQueue, 10000); }
      else return flushQueue();
    });
  }
  B.flushQueue = flushQueue;
  App.on('conn', function (v) { if (v) flushQueue(); });

  // ------------------------------------------------------------ chores with an offline queue
  // Ticks are absolute states ("done" / "not done") for one chore, person and day, so replaying them in order is
  // safe and the last tap wins. The server refuses days other than today or yesterday.
  function cqueue() { return jget(K.cq, []); }
  function ymd(d) { return d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2); }
  function applyChoreOp(op) {
    if (op.day !== D.chores.day) return;
    D.chores.items.forEach(function (i) { if (i.id === op.chore_id && i.person === op.person_id) i.done = op.done; });
  }
  B.chore = function (choreId, personId, done) {
    var op = { chore_id: choreId, person_id: personId || '', done: !!done, day: ymd(App.now()) };
    applyChoreOp(op);
    B._sig = null;
    var q = cqueue(); q.push(op); sset(K.cq, JSON.stringify(q.slice(-200)));
    App.emit('chores');
    return flushChores();
  };
  var flushingChores = false, choreTimer = null;
  function flushChores() {
    var q = cqueue();
    if (flushingChores || !q.length || !B.paired) return Promise.resolve();
    flushingChores = true;
    var failed = false;
    return B.request('POST', '/api/v1/device/chores/done', { ops: q }).then(function (r) {
      sset(K.cq, JSON.stringify(cqueue().slice(q.length)));
      applyChores(r.chores);
      App.emit('chores');
    }, function (e) {
      if (e && e.status && e.status >= 400 && e.status < 500 && e.status !== 408 && e.status !== 429 && e.status !== 401) sset(K.cq, '[]');
      else failed = true;
    }).then(function () {
      flushingChores = false;
      if (!cqueue().length) return;
      if (failed) { clearTimeout(choreTimer); choreTimer = setTimeout(flushChores, 10000); }
      else return flushChores();
    });
  }
  B.flushChores = flushChores;
  App.on('conn', function (v) { if (v) flushChores(); });

  // the cached/replayed queue count is needed before the first sync
  D.shopping.pending = queue().length;
})();
