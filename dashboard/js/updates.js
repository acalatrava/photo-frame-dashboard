// App updates over the network. The backend publishes a build; this module asks which one is current,
// hands the download to the Android shell and reports progress. Everything is a no-op in a plain browser.
(function () {
  'use strict';
  var N = App.native, B = App.backend;
  var CHECK_EVERY = 6 * 3600 * 1000, MIN_GAP = 10 * 60 * 1000;
  var TOASTED = 'hq.update.toasted';
  var U = App.updates = { info: null, state: { state: 'idle', pct: 0, error: '' }, checkedAt: 0, checking: false };

  U.installedCode = function () {
    var m = /\((\d+)\)\s*$/.exec(N.version() || '');
    return m ? parseInt(m[1], 10) : 0;
  };
  U.release = function () { return U.info && U.info.release; };
  U.available = function () {
    var r = U.release();
    return !!(N.available && r && r.version_code > U.installedCode());
  };
  U.mode = function () { return (U.info && U.info.mode) || ((B.cfg && B.cfg.updates && B.cfg.updates.mode) || 'notify'); };

  function busy() { return U.state.state === 'downloading' || U.state.state === 'installing'; }

  U.check = function (force) {
    if (!N.available || !B.paired || U.checking) return Promise.resolve(U.info);
    if (!force && Date.now() - U.checkedAt < MIN_GAP) return Promise.resolve(U.info);
    U.checking = true;
    return B.request('GET', '/api/v1/device/update').then(function (info) {
      U.info = info; U.checkedAt = Date.now(); U.checking = false;
      App.emit('update', U);
      if (U.available() && info.mode !== 'off') {
        if (info.mode === 'auto' && !busy() && U.state.state === 'idle') U.start(false);
        announce();
      }
      return info;
    }, function (e) { U.checking = false; throw e; });
  };

  // One reminder per version, so a frame left on the clock does not nag.
  function announce() {
    var r = U.release(), seen = '';
    try { seen = localStorage.getItem(TOASTED) || ''; } catch (e) { seen = ''; }
    if (seen === String(r.version_code)) return;
    try { localStorage.setItem(TOASTED, String(r.version_code)); } catch (e) { /* ignore */ }
    App.toast(App.t('up_toast', { v: App.esc(r.version_name) }), { icon: 'bolt', ms: 9000 });
  }

  // install=false only downloads and verifies; install=true then opens Android's installer.
  U.start = function (install) {
    var r = U.release();
    if (!N.available || !r || busy()) return;
    N.downloadUpdate(B.url() + '/api/v1/device/update/apk', B.token(), r.sha256, r.version_code, !!install);
  };

  U.install = function () {
    if (U.state.state === 'ready') N.installUpdate(); else U.start(true);
  };

  App.on('native:update', function (st) {
    U.state = st || U.state;
    App.emit('update', U);
  });

  // The admin asked this frame to update now: wake the screen so the confirmation dialog is seen.
  App.on('command', function (type) {
    if (type !== 'update') return;
    U.check(true).then(function () {
      if (!U.available()) { App.toast(App.t('up_current'), { icon: 'check', ms: 4000 }); return; }
      if (App.display && App.display.wake) App.display.wake('command');
      U.start(true);
    }, function () { /* offline: nothing to do */ });
  });

  App.on('update:published', function () { U.check(true); });
  App.on('config', function () { U.check(false); });
  setInterval(function () { U.check(true); }, CHECK_EVERY);
  setTimeout(function () { U.check(false); }, 20000);

  App.on('update', function () {
    var b = document.querySelector('.rail-item[data-go="settings"]');
    if (b) b.classList.toggle('has-update', U.available() && U.mode() !== 'off');
  });
})();
