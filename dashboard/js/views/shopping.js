// Compra: one shared list. Pending items first, completed items below, works offline (see backend.js).
(function () {
  'use strict';
  var D = window.DATA;
  var V = { el: null, query: '', pending: {}, confirm: null };

  function open() { return D.groceries.filter(function (g) { return !g.done; }).reverse(); }
  function done() { return D.groceries.filter(function (g) { return g.done; }).reverse(); }
  function byId(id) { return D.groceries.filter(function (g) { return g.id === id; })[0]; }

  function row(g, isDone) {
    return '<div class="s-row' + (V.pending[g.id] ? ' is-checking' : '') + (isDone ? ' is-done' : '') + '" data-id="' + App.esc(g.id) + '">' +
      '<button class="s-hit" data-check="' + App.esc(g.id) + '" aria-label="' + App.esc(isDone ? App.t('shop_reopen') : App.t('shop_complete')) + '">' +
      '<span class="s-box">' + App.icon('check', 22) + '</span>' +
      '<span class="s-name"><b>' + App.esc(g.name) + '</b>' + (g.note ? '<small>' + App.esc(g.note) + '</small>' : '') + '</span></button>' +
      '<button class="s-edit" data-edit="' + App.esc(g.id) + '" aria-label="' + App.esc(App.t('shop_edit')) + '">' + App.icon('pencil', 24) + '</button>' +
      '</div>';
  }

  function listHTML() {
    var o = open(), d = done();
    var h = '';
    if (o.length) h += '<div class="s-cat"><div class="s-cat-h"><span class="label">' + App.t('shop_pending') + '</span><span class="label">' + o.length + '</span></div>' + o.map(function (g) { return row(g, false); }).join('') + '</div>';
    else h += '<div class="s-empty serif">' + App.t('shop_empty') + '<br><i>' + App.t('shop_empty2') + '</i></div>';
    if (d.length) h += '<div class="s-cat s-cat--done"><div class="s-cat-h"><span class="label">' + App.t('shop_done') + '</span><span class="label">' + d.length + '</span></div>' +
      d.map(function (g) { return row(g, true); }).join('') +
      '<button class="btn btn--ghost s-clear" data-clear>' + App.icon('trash', 22) + App.t('shop_clear', { n: d.length }) + '</button></div>';
    return h;
  }

  function syncHTML() {
    var s = D.shopping, parts = [];
    var cls = 'is-ok', txt;
    if (!App.backend.online) { cls = 'is-warn'; txt = App.t('shop_offline'); }
    else if (s.stale) { cls = 'is-warn'; txt = App.t('shop_provider_down'); }
    else txt = App.t(s.provider === 'homeassistant' ? 'shop_synced_ha' : 'shop_synced_local');
    parts.push('<div class="s-sync ' + cls + '">' + App.icon(cls === 'is-ok' ? 'check' : 'wifioff', 22) + '<span>' + txt + '</span></div>');
    if (s.pending) parts.push('<div class="s-sync is-warn">' + App.icon('clock', 22) + '<span>' + App.t('shop_pending_sync', { n: s.pending }) + '</span></div>');
    return parts.join('');
  }

  function suggestHTML() {
    var q = V.query.trim().toLowerCase();
    var recent = done().slice(0, 8);
    if (q) {
      var exists = D.groceries.filter(function (g) { return g.name.trim().toLowerCase() === q; })[0];
      return '<div class="label">' + App.t('shop_add_label') + '</div><button class="s-ac-row s-ac-row--new" data-add="' + App.esc(V.query.trim()) + '"><b>' + App.t('shop_add_named', { name: App.esc(V.query.trim()) }) + '</b>' +
        (exists ? '<span class="label">' + App.t(exists.done ? 'shop_reopen' : 'shop_on_list') + '</span>' : '') + App.icon('plus', 26) + '</button>';
    }
    if (!recent.length) return '<p class="s-hint">' + App.t('shop_hint') + '</p>';
    return '<div class="label">' + App.t('shop_again') + '</div><div class="s-usuals">' + recent.map(function (g) {
      return '<button class="s-tile" data-reopen="' + App.esc(g.id) + '"><b>' + App.esc(g.name) + '</b><span>' + App.icon('plus', 16) + App.t('shop_reopen') + '</span></button>';
    }).join('') + '</div>';
  }

  function paintAll() {
    if (!V.el || !V.el.firstChild) return;
    var l = V.el.querySelector('.s-list'), st = l.scrollTop;
    l.innerHTML = listHTML(); l.scrollTop = st;
    V.el.querySelector('.s-count').innerHTML = '<span class="num">' + open().length + '</span> ' + App.t('shop_to_get');
    V.el.querySelector('.s-status').innerHTML = syncHTML();
    V.el.querySelector('.s-suggest').innerHTML = suggestHTML();
  }

  function render() {
    V.el.innerHTML = '<div class="shop">' +
      '<header class="s-head"><div><div class="label">' + App.t('shop_kicker') + '</div><h1 class="serif">' + App.t('nav_shopping') + '</h1></div><div class="s-count"></div></header>' +
      '<div class="s-list"></div>' +
      '<aside class="s-side">' +
      '  <div class="s-add"><label class="s-input-wrap">' + App.icon('plus', 30) + '<input class="s-input" placeholder="' + App.esc(App.t('shop_placeholder')) + '" autocomplete="off" autocapitalize="sentences" enterkeyhint="done" maxlength="200"></label></div>' +
      '  <div class="s-status"></div><div class="s-suggest"></div>' +
      '</aside></div>';
    var input = V.el.querySelector('.s-input');
    input.value = V.query;
    input.addEventListener('input', function () { V.query = input.value; V.el.querySelector('.s-suggest').innerHTML = suggestHTML(); });
    input.addEventListener('keydown', function (e) { if (e.key === 'Enter' && input.value.trim()) add(input.value); });
    paintAll();
  }

  function add(name) {
    name = name.trim();
    if (!name) return;
    var existing = D.groceries.filter(function (g) { return g.name.trim().toLowerCase() === name.toLowerCase(); })[0];
    App.backend.shop({ type: 'add', name: name });
    V.query = '';
    var input = V.el.querySelector('.s-input');
    if (input) input.value = '';
    App.toast(existing && !existing.done ? App.t('shop_already', { name: App.esc(existing.name) }) : App.t('shop_added', { name: App.esc(name) }), { icon: 'cart', ms: 2500 });
  }

  function toggle(g) {
    var to = !g.done;
    if (!to) { App.backend.shop({ type: 'set_done', id: g.id, done: false }); return; }
    V.pending[g.id] = true;
    var rowEl = V.el.querySelector('[data-id="' + g.id.replace(/"/g, '') + '"]');
    if (rowEl) rowEl.classList.add('is-checking');
    var undone = false;
    setTimeout(function () {
      delete V.pending[g.id];
      if (undone) return;
      App.backend.shop({ type: 'set_done', id: g.id, done: true });
    }, 1100);
    App.toast(App.t('shop_checked', { name: App.esc(g.name) }), {
      icon: 'check', ms: 1800, undo: function () { undone = true; delete V.pending[g.id]; paintAll(); }
    });
  }

  function editSheet(g) {
    App.sheet('<div class="sheet-pad"><div class="label">' + App.t('shop_edit') + '</div>' +
      '<input class="big-input serif s-rename" maxlength="200" value="' + App.esc(g.name) + '" autocapitalize="sentences">' +
      '<div class="sheet-actions"><button class="btn btn--ghost" data-del>' + App.icon('trash', 22) + App.t('delete') + '</button>' +
      '<button class="btn btn--solid" data-save>' + App.t('save') + '</button></div></div>', {
      cls: 'sheet--wide',
      onMount: function (s, close) {
        var input = s.querySelector('.s-rename');
        s.addEventListener('click', function (e) {
          if (e.target.closest('[data-save]')) {
            var n = input.value.trim();
            if (n && n !== g.name) App.backend.shop({ type: 'rename', id: g.id, name: n });
            close();
          } else if (e.target.closest('[data-del]')) {
            App.backend.shop({ type: 'remove', id: g.id });
            close();
          }
        });
        input.addEventListener('keydown', function (e) { if (e.key === 'Enter') s.querySelector('[data-save]').click(); });
      }
    });
  }

  function onClick(e) {
    var t;
    if ((t = e.target.closest('[data-check]'))) { var g = byId(t.dataset.check); if (g) toggle(g); }
    else if ((t = e.target.closest('[data-edit]'))) { var g2 = byId(t.dataset.edit); if (g2) editSheet(g2); }
    else if ((t = e.target.closest('[data-add]'))) add(t.dataset.add);
    else if ((t = e.target.closest('[data-reopen]'))) App.backend.shop({ type: 'set_done', id: t.dataset.reopen, done: false });
    else if (e.target.closest('[data-clear]')) {
      var n = done().length;
      App.sheet('<div class="sheet-pad"><div class="label">' + App.t('shop_done') + '</div><h2 class="serif sheet-h">' + App.t('shop_clear_q', { n: n }) + '</h2>' +
        '<div class="sheet-actions"><button class="btn btn--ghost" data-close>' + App.t('cancel') + '</button><button class="btn btn--solid" data-go-clear>' + App.t('delete') + '</button></div></div>', {
        onMount: function (s, close) {
          s.querySelector('[data-go-clear]').addEventListener('click', function () {
            done().forEach(function (g) { App.backend.shop({ type: 'remove', id: g.id }); });
            close();
          });
        }
      });
    }
  }

  App.register('shopping', {
    show: function (el) {
      if (!V.el) { V.el = el; el.addEventListener('click', onClick); }
      render();
    }
  });
  App.on('data', function () { if (App.current === 'shopping') paintAll(); });
  App.on('conn', function () { if (App.current === 'shopping') paintAll(); });
})();
