// First-run flow: find the backend (mDNS list or manual address), pair with admin approval, then start.
(function () {
  'use strict';
  var N = App.native;
  var el = null, S = { url: '', code: null, expires: 0, msg: '', phase: 'url', timer: null, tick: null };

  function root() {
    if (!el) {
      el = document.getElementById('setup');
      if (!el) { el = document.createElement('div'); el.id = 'setup'; document.getElementById('stage').appendChild(el); }
    }
    return el;
  }
  function discovered() {
    var list = N.discovered();
    return list.map(function (d) {
      return '<button class="su-found" data-url="' + App.esc(d.url) + '">' + App.icon('home', 28) + '<span><b>' + App.esc(d.name) + '</b><small>' + App.esc(d.url) + '</small></span></button>';
    }).join('');
  }

  function paint() {
    var r = root();
    var focused = r.querySelector('input') && document.activeElement === r.querySelector('input');
    if (S.phase === 'code') {
      var left = Math.max(0, Math.round((S.expires - Date.now()) / 1000));
      r.innerHTML = '<div class="su-card">' +
        '<div class="label">' + App.t('setup_step2') + '</div><h1 class="serif">' + App.t('setup_code_title') + '</h1>' +
        '<div class="su-code num">' + (S.code || '').replace(/(\d{3})(\d{3})/, '$1 $2') + '</div>' +
        '<p>' + App.t('setup_code_help') + '</p><p class="su-small">' + App.esc(S.url) + ' · ' + App.t('setup_expires', { s: Math.floor(left / 60) + ':' + ('0' + (left % 60)).slice(-2) }) + '</p>' +
        (S.msg ? '<p class="su-err">' + App.esc(S.msg) + '</p>' : '') +
        '<div class="su-actions"><button class="btn btn--ghost" data-back>' + App.t('back') + '</button></div></div>';
      return;
    }
    if (focused) { var f = r.querySelector('.su-list'); if (f) f.innerHTML = discovered(); return; }
    r.innerHTML = '<div class="su-card">' +
      '<div class="label">Home HQ · ' + App.t('setup_step1') + '</div><h1 class="serif">' + App.t('setup_title') + '</h1>' +
      (S.msg ? '<p class="su-err">' + App.esc(S.msg) + '</p>' : '<p>' + App.t('setup_help') + '</p>') +
      '<div class="su-list">' + discovered() + '</div>' +
      '<label class="su-input-wrap">' + App.icon('home', 28) + '<input class="su-input" inputmode="url" autocapitalize="none" autocomplete="off" spellcheck="false" placeholder="192.168.1.10:8787" value="' + App.esc(S.url) + '"></label>' +
      '<div class="su-actions"><button class="btn btn--solid" data-connect>' + App.t('setup_connect') + '</button></div></div>';
  }

  function connect(url) {
    S.msg = '';
    url = App.backend.setUrl(url);
    if (!url) { S.msg = App.t('setup_need_url'); paint(); return; }
    S.url = url;
    App.backend.request('GET', '/health', undefined, { anon: true, timeout: 6000 }).then(function (h) {
      if (!h || h.status !== 'ok') throw new Error('bad');
      return App.backend.pairing.begin(url, onPair);
    }).catch(function (e) {
      S.msg = App.t(e && e.status === 429 ? 'setup_rate' : 'setup_unreachable');
      S.phase = 'url';
      paint();
    });
  }
  function onPair(st) {
    if (st.status === 'pending') { S.phase = 'code'; S.code = st.code; S.expires = new Date(st.expires_at).getTime(); S.msg = ''; paint(); }
    else if (st.status === 'approved') { /* backend.start() hides the screen */ }
    else if (st.status === 'rejected') { S.phase = 'url'; S.msg = App.t('setup_rejected'); paint(); }
    else { S.msg = App.t('setup_expired'); connect(S.url); }
  }

  App.setup = {
    show: function (reason) {
      S.phase = 'url'; S.msg = reason === 'revoked' ? App.t('setup_revoked') : '';
      S.url = App.backend.url();
      root().classList.add('is-open');
      N.discover();
      paint();
      clearInterval(S.tick);
      S.tick = setInterval(paint, 2000);
    },
    hide: function () {
      if (el) { el.classList.remove('is-open'); el.innerHTML = ''; }
      clearInterval(S.tick);
      N.stopDiscover();
    }
  };

  App.on('ready', function () {
    root().addEventListener('click', function (e) {
      var t;
      if ((t = e.target.closest('[data-url]'))) connect(t.dataset.url);
      else if (e.target.closest('[data-connect]')) connect(root().querySelector('.su-input').value);
      else if (e.target.closest('[data-back]')) { App.backend.pairing.cancel(); S.phase = 'url'; S.msg = ''; paint(); }
    });
    root().addEventListener('keydown', function (e) { if (e.key === 'Enter' && e.target.classList.contains('su-input')) connect(e.target.value); });
    root().addEventListener('input', function (e) { if (e.target.classList.contains('su-input')) S.url = e.target.value; });
  });
})();
