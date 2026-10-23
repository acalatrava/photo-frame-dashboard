// Menú: the weekly menu as a grid of days, with today's column framed. The frame receives every week of the
// rotation and works out which one applies, so it keeps showing the right menu across a Monday while offline.
(function () {
  'use strict';
  var D = window.DATA, V = { el: null, offset: 0 };
  var ORDER = ['breakfast', 'midmorning', 'lunch', 'snack', 'dinner'];
  var DAY_MS = 864e5;

  function dayNum(d) { return Math.floor(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()) / DAY_MS); }
  function weekday(n) { return (((n + 3) % 7) + 7) % 7; }
  function mondayNum(n) { return n - weekday(n); }
  function mod(a, n) { return ((a % n) + n) % n; }

  function parseDay(s) {
    var m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(s || '');
    return m ? Math.floor(Date.UTC(+m[1], +m[2] - 1, +m[3]) / DAY_MS) : null;
  }

  // Same rule as the backend: weeks counted from the Monday of the anchor date.
  function weekIndex(menu, mondayN) {
    var anchor = parseDay(menu.start_date);
    anchor = anchor == null ? mondayN : mondayNum(anchor);
    return mod(menu.start_week - 1 + Math.round((mondayN - anchor) / 7), menu.weeks.length);
  }

  function rows(menu, week) {
    return ORDER.filter(function (m) { return menu.meals.indexOf(m) > -1; }).map(function (m) {
      var shared = (week.shared && week.shared[m] || '').trim();
      var cells = week.days.map(function (d) { return (d[m] || '').trim(); });
      return { meal: m, shared: shared, cells: cells, empty: !shared && !cells.some(Boolean) };
    }).filter(function (r) { return !r.empty; });
  }

  function dayHead(date, col, isToday, isPast) {
    return '<div style="grid-row:1;grid-column:' + col + '" class="mn-dh' + (isToday ? ' is-today' : '') + (isPast ? ' is-past' : '') + '"><small>' + App.fmt.dayShort(date) +
      '</small><b class="num">' + date.getDate() + '</b>' + (isToday ? '<em>' + App.t('mn_today') + '</em>' : '') + '</div>';
  }

  function chips(menu, curIdx, shownIdx) {
    if (menu.weeks.length < 2) return '';
    return '<div class="mn-chips" role="group">' + menu.weeks.map(function (w, i) {
      return '<button class="mn-chip' + (i === shownIdx ? ' is-on' : '') + (i === curIdx ? ' is-now' : '') + '" data-pick="' + i + '"><b class="num">' + (i + 1) + '</b></button>';
    }).join('') + '</div>';
  }

  function empty() {
    return '<div class="mn"><header class="mn-head"><div><div class="label">' + App.t('mn_kicker') + '</div><h1 class="serif">' + App.t('nav_menu') +
      '</h1></div></header><div class="mn-empty serif">' + App.t('mn_none') + '<br><i>' + App.t('mn_none2') + '</i></div></div>';
  }

  function html() {
    var menu = D.menu;
    if (!menu || !menu.configured || !menu.weeks.length) return empty();
    var now = App.now(), todayN = dayNum(now);
    var viewMonday = mondayNum(todayN) + V.offset * 7;
    var curIdx = weekIndex(menu, mondayNum(todayN)), idx = weekIndex(menu, viewMonday);
    var week = menu.weeks[idx], rs = rows(menu, week);
    var isCurrent = V.offset === 0, todayCol = isCurrent ? weekday(todayN) : -1;
    var first = new Date(now.getFullYear(), now.getMonth(), now.getDate() + (viewMonday - todayN));
    var last = App.addDays(first, 6);
    var range = App.fmt.dayMonthShort(first) + ' – ' + App.fmt.dayMonthShort(last);

    var head = '<header class="mn-head"><div><div class="label">' + range + (week.name ? ' · ' + App.esc(week.name) : '') + '</div><h1 class="serif">' + App.t('nav_menu') + '</h1></div>' +
      '<div class="mn-nav">' + chips(menu, curIdx, idx) +
      (isCurrent ? '' : '<button class="mn-back" data-off="0">' + App.t('mn_back') + '</button>') +
      '<button class="mn-arrow" data-off="' + (V.offset - 1) + '" aria-label="' + App.t('mn_prev') + '">' + App.icon('left', 28) + '</button>' +
      '<div class="mn-wk"><small>' + App.t('mn_week') + '</small><b class="num">' + (idx + 1) + '</b></div>' +
      '<button class="mn-arrow" data-off="' + (V.offset + 1) + '" aria-label="' + App.t('mn_next') + '">' + App.icon('right', 28) + '</button></div></header>';

    var grid = dayHeaders(first, todayCol, isCurrent) + rs.map(function (r, ri) { return rowHtml(r, ri + 2, todayCol, isCurrent); }).join('');
    var frame = todayCol > -1 ? '<div class="mn-frame" style="grid-column:' + (todayCol + 2) + ';grid-row:1/' + (rs.length + 2) + '"></div>' : '';
    var body = rs.length
      ? '<div class="mn-grid mn-n' + rs.length + '" style="grid-template-rows:auto repeat(' + rs.length + ',minmax(0,1fr))">' + grid + frame + '</div>'
      : '<div class="mn-empty serif">' + App.t('mn_week_empty') + '</div>';
    return '<div class="mn">' + head + body + '</div>';
  }

  function dayHeaders(first, todayCol, isCurrent) {
    var out = '';
    for (var i = 0; i < 7; i++) out += dayHead(App.addDays(first, i), i + 2, i === todayCol, isCurrent && i < todayCol);
    return out;
  }

  function rowHtml(r, rowNo, todayCol, isCurrent) {
    var out = '<div class="mn-lab mn-r--' + r.meal + '" style="grid-row:' + rowNo + ';grid-column:1"><b>' + App.t('meal_' + r.meal) + '</b></div>';
    if (r.shared) return out + '<div class="mn-cell mn-shared mn-r--' + r.meal + '" style="grid-row:' + rowNo + ';grid-column:2/9"><span>' + App.esc(r.shared) + '</span></div>';
    return out + r.cells.map(function (t, i) {
      return '<div class="mn-cell mn-r--' + r.meal + (i === todayCol ? ' is-today' : '') + (isCurrent && i < todayCol ? ' is-past' : '') + '" style="grid-row:' + rowNo + ';grid-column:' + (i + 2) + '"><span>' + App.esc(t) + '</span></div>';
    }).join('');
  }

  function paint() { if (V.el) V.el.innerHTML = html(); }

  App.register('menu', {
    minutely: true,
    hide: function () { V.offset = 0; },
    show: function (el) {
      if (!V.el) {
        V.el = el;
        el.addEventListener('click', function (e) {
          var off = e.target.closest('[data-off]'), pick = e.target.closest('[data-pick]');
          if (off) { V.offset = +off.dataset.off; paint(); return; }
          if (pick && D.menu && D.menu.weeks.length) {
            var todayN = dayNum(App.now());
            V.offset = mod(+pick.dataset.pick - weekIndex(D.menu, mondayNum(todayN)), D.menu.weeks.length);
            paint();
          }
        });
      }
      paint();
    }
  });
  App.menuWeek = function (date) {
    var m = D.menu;
    return m && m.configured && m.weeks.length ? weekIndex(m, mondayNum(dayNum(date))) : -1;
  };
})();
