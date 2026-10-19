// Cámaras: a grid of refreshing snapshots; tapping one opens a live stream. The backend does all the talking to
// Frigate / Home Assistant, so the frame only ever loads images from Home HQ.
(function () {
  'use strict';
  var D = window.DATA;
  var V = { el: null, timer: null, live: null, liveSince: 0, keep: null, tick: 0 };
  var GRID_MS = 3000, LIVE_MAX_MS = 5 * 60000;

  function cols(n) { return n <= 1 ? 1 : n <= 4 ? 2 : 3; }

  function html() {
    var head = '<header class="cm-head"><div><div class="label">' + App.t('cam_kicker') + '</div><h1 class="serif">' + App.t('nav_cameras') + '</h1></div>' +
      (App.backend.online ? '' : '<span class="cm-off">' + App.icon('wifioff', 22) + App.t('no_backend') + '</span>') + '</header>';
    if (!D.cameras.length) return '<div class="cm">' + head + '<div class="cm-empty serif">' + App.t('cam_none') + '<br><i>' + App.t('cam_none2') + '</i></div></div>';
    var n = D.cameras.length;
    return '<div class="cm">' + head + '<div class="cm-grid" style="grid-template-columns:repeat(' + cols(n) + ',1fr)' + (n <= 2 ? ';grid-auto-rows:1fr' : '') + '">' +
      D.cameras.map(function (c, i) {
        return '<button class="cm-tile" data-cam="' + i + '"><img alt="" data-snap="' + i + '" src="' + App.esc(c.snapshot) + '&t=' + Date.now() + '"><span class="cm-name">' + App.icon('camera', 22) + App.esc(c.name) + '</span></button>';
      }).join('') + '</div></div><div class="cm-live" hidden></div>';
  }

  function refreshGrid() {
    if (V.live || App.current !== 'cameras' || !App.backend.online) return;
    App.$$('[data-snap]', V.el).forEach(function (img) {
      var cam = D.cameras[+img.dataset.snap];
      if (!cam || img.dataset.busy) return;
      var probe = new Image();
      img.dataset.busy = '1';
      probe.onload = function () { img.src = probe.src; delete img.dataset.busy; img.parentNode.classList.remove('is-bad'); };
      probe.onerror = function () { delete img.dataset.busy; img.parentNode.classList.add('is-bad'); };
      probe.src = cam.snapshot + '&t=' + Date.now();
    });
  }

  function openLive(i) {
    var cam = D.cameras[i], box = V.el.querySelector('.cm-live');
    if (!cam || !box) return;
    V.live = i; V.liveSince = Date.now();
    box.hidden = false;
    box.innerHTML = '<img alt="" src="' + App.esc(cam.stream) + '&t=' + Date.now() + '">' +
      '<div class="cm-bar"><b>' + App.icon('camera', 26) + App.esc(cam.name) + '</b><span class="cm-badge">' + App.t('live') + '</span>' +
      '<button class="cm-btn" data-retry>' + App.t('cam_reload') + '</button><button class="cm-btn cm-btn--x" data-close aria-label="' + App.t('back') + '">' + App.icon('x', 30) + '</button></div>' +
      '<div class="cm-err" hidden>' + App.t('cam_error') + '</div>';
    var img = box.querySelector('img'), err = box.querySelector('.cm-err');
    img.onerror = function () { err.hidden = false; };
    img.onload = function () { err.hidden = true; };
    // A person watching a camera is not idle: keep the screen from falling back to Today for a few minutes.
    clearInterval(V.keep);
    V.keep = setInterval(function () {
      if (Date.now() - V.liveSince > LIVE_MAX_MS) closeLive(); else App.resetIdle();
    }, 5000);
  }

  function closeLive() {
    clearInterval(V.keep);
    V.live = null;
    var box = V.el && V.el.querySelector('.cm-live');
    if (!box) return;
    var img = box.querySelector('img');
    if (img) img.src = 'about:blank';
    box.innerHTML = ''; box.hidden = true;
  }

  App.register('cameras', {
    minutely: false,
    show: function (el) {
      if (!V.el) {
        V.el = el;
        el.addEventListener('click', function (e) {
          var t;
          if (e.target.closest('[data-close]')) closeLive();
          else if (e.target.closest('[data-retry]')) { var i = V.live; closeLive(); openLive(i); }
          else if ((t = e.target.closest('[data-cam]'))) openLive(+t.dataset.cam);
        });
      }
      closeLive();
      el.innerHTML = html();
      clearInterval(V.timer);
      V.timer = setInterval(refreshGrid, GRID_MS);
    },
    resume: function () { clearInterval(V.timer); V.timer = setInterval(refreshGrid, GRID_MS); refreshGrid(); },
    // Leaving the view must drop the stream connection, otherwise the server keeps pushing frames.
    hide: function () { closeLive(); clearInterval(V.timer); }
  });
  App.on('mode', function (m) { if (m !== 'day' && V.el) closeLive(); });
})();
