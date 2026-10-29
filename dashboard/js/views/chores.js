// Tareas: one column per person (plus one for shared chores). Tapping a chore ticks it on or off for today.
(function () {
  'use strict';
  var D = window.DATA, V = { el: null };

  function groups() {
    var out = [], byId = {};
    D.chores.items.forEach(function (i) {
      var key = byId[i.person] == null ? (byId[i.person] = out.push({ id: i.person, items: [] }) - 1) : byId[i.person];
      out[key].items.push(i);
    });
    var order = D.people.map(function (p) { return p.id; });
    out.sort(function (a, b) {
      var ia = a.id ? order.indexOf(a.id) : 999, ib = b.id ? order.indexOf(b.id) : 999;
      return ia - ib;
    });
    return out;
  }

  function column(g) {
    var p = g.id ? App.person(g.id) : D.family;
    var done = g.items.filter(function (i) { return i.done; }).length, all = done === g.items.length;
    return '<section class="ch-col' + (all ? ' is-all' : '') + '" style="' + App.pstyle(p) + '">' +
      '<header class="ch-colhead">' + App.avatar(p, 46) + '<b>' + (g.id ? App.esc(p.name) : App.t('ch_shared')) + '</b>' +
      '<span class="ch-count num">' + done + '/' + g.items.length + '</span></header>' +
      '<div class="ch-list">' + g.items.map(function (i) {
        return '<button class="ch-item' + (i.done ? ' is-done' : '') + '" data-chore="' + App.esc(i.id) + '" data-person="' + App.esc(i.person) + '">' +
          '<span class="ch-ic">' + App.icon(i.done ? 'check' : i.icon, 34) + '</span>' +
          '<span class="ch-tx"><b>' + App.esc(i.title) + '</b>' +
          (i.overdue ? '<small class="ch-late">' + App.t('ch_overdue') + '</small>' : i.time ? '<small>' + App.esc(i.time) + '</small>' : i.once ? '<small>' + App.t('ch_once') + '</small>' : '') + '</span></button>';
      }).join('') + (all ? '<div class="ch-all serif">' + App.t('ch_all_done') + '</div>' : '') + '</div></section>';
  }

  function html() {
    var gs = groups(), now = App.now();
    var total = D.chores.items.length, done = D.chores.items.filter(function (i) { return i.done; }).length;
    var head = '<header class="ch-head"><div><div class="label">' + App.fmt.day(now) + ' ' + App.fmt.dayMonth(now) + '</div><h1 class="serif">' + App.t('nav_chores') + '</h1></div>' +
      (total ? '<div class="ch-total">' + App.ring(done, total, 76) + '<b class="num">' + done + '/' + total + '</b></div>' : '') + '</header>';
    if (!gs.length) return '<div class="ch">' + head + '<div class="ch-empty serif">' + App.t('ch_none') + '<br><i>' + App.t('ch_none2') + '</i></div></div>';
    return '<div class="ch">' + head + '<div class="ch-cols" style="grid-template-columns:repeat(' + Math.min(gs.length, 4) + ',1fr)">' + gs.map(column).join('') + '</div></div>';
  }

  function paint() {
    if (!V.el) return;
    var sc = V.el.querySelector('.ch-cols'), tops = [];
    if (sc) tops = App.$$('.ch-list', V.el).map(function (l) { return l.scrollTop; });
    V.el.innerHTML = html();
    App.$$('.ch-list', V.el).forEach(function (l, i) { l.scrollTop = tops[i] || 0; });
  }

  App.register('chores', {
    minutely: true,
    show: function (el) {
      if (!V.el) {
        V.el = el;
        el.addEventListener('click', function (e) {
          var b = e.target.closest('[data-chore]');
          if (!b) return;
          var item = D.chores.items.filter(function (i) { return i.id === b.dataset.chore && i.person === b.dataset.person; })[0];
          if (item) App.backend.chore(item.id, item.person, !item.done);
        });
      }
      paint();
    }
  });
  App.on('chores', function () { if (App.current === 'chores') paint(); else if (App.views.chores) App.views.chores._dirty = true; });
})();
