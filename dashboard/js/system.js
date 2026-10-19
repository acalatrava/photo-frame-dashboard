// Banners and backend notices.
(function () {
  'use strict';
  var D = window.DATA, $ = App.$;
  var shown = {};

  App.banner = function (opts) {
    var box = $('#banners');
    var b = document.createElement('div');
    b.className = 'banner banner--' + (opts.tone || 'amber');
    b.innerHTML = App.icon(opts.icon || 'bell', 30) + '<div class="banner-text"><b>' + App.esc(opts.title) + '</b><span>' + App.esc(opts.sub || '') + '</span></div>' +
      (opts.action ? '<button class="banner-btn banner-btn--solid" data-act>' + App.esc(opts.action) + '</button>' : '') +
      '<button class="banner-btn" data-x>' + App.esc(opts.dismiss || App.t('dismiss')) + '</button>';
    box.appendChild(b);
    b.classList.add('is-in');
    function kill() { b.remove(); }
    b.querySelector('[data-x]').onclick = kill;
    if (opts.action) b.querySelector('[data-act]').onclick = function () { kill(); opts.onAction(); };
    if (opts.ms) setTimeout(kill, opts.ms);
    return kill;
  };

  // Each backend notice is announced once per app run; dismissing it keeps it quiet until the next restart.
  App.on('data', function () {
    (D.notices || []).forEach(function (n) {
      if (shown[n.id]) return;
      shown[n.id] = true;
      App.banner({ tone: 'amber', icon: 'calendar', title: App.t('notice_calendar', { name: n.source || '' }), sub: n.message || '' });
    });
  });

  App.on('ready', function () {
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') App.closeSheet();
    });
  });
})();
