// Photo slideshow used by the Photos view, ambient mode and the home tile.
(function () {
  'use strict';
  var D = window.DATA;

  function pcfg() {
    var c = App.backend && App.backend.cfg;
    return (c && c.device_config && c.device_config.photos) || {};
  }
  App.photosConfig = pcfg;

  function src(p, big) { return big ? p.screen : p.thumb; }
  App.photoSrc = src;

  function parseDate(p) {
    var a = (p.date || '').split('-');
    return a.length === 3 ? new Date(+a[0], +a[1] - 1, +a[2]) : null;
  }
  App.photoMeta = function (p) {
    var d = parseDate(p), now = App.now();
    if (!d) return { date: '', monthYear: '', kicker: '', onThisDay: false, place: p.caption || '' };
    var years = now.getFullYear() - d.getFullYear();
    var onThisDay = years > 0 && d.getMonth() === now.getMonth() && d.getDate() === now.getDate();
    var kicker = onThisDay ? App.t('years_ago_today', { n: years }) : (years > 0 ? App.t('years_ago', { n: years }) : App.t('this_year'));
    return { date: App.fmt.dateLong(d), monthYear: App.fmt.monthYear(d), kicker: kicker, onThisDay: onThisDay, place: p.caption || '' };
  };

  function shuffle(a) {
    for (var i = a.length - 1; i > 0; i--) { var j = Math.floor(Math.random() * (i + 1)), t = a[i]; a[i] = a[j]; a[j] = t; }
    return a;
  }

  function caption(ps, size) {
    var m = App.photoMeta(ps[0]);
    return '<div class="cap cap--' + (size || 'l') + '">' +
      '<div class="cap-kicker">' + (m.onThisDay ? '<b>' + App.t('on_this_day') + '</b> · ' : '') + m.kicker + (m.place ? ' · ' + App.esc(m.place) : '') + '</div>' +
      '<div class="cap-date serif">' + (ps.length > 1 ? m.monthYear : m.date) + '</div>' +
      '</div>';
  }
  function kb(p, still) {
    var dx = (Math.random() > 0.5 ? 1 : -1) * (1 + Math.random() * 2.5) + '%';
    var dy = (Math.random() > 0.5 ? 1 : -1) * (0.5 + Math.random() * 1.5) + '%';
    return '<div class="kb' + (still ? ' kb--still' : '') + '" style="--dx:' + dx + ';--dy:' + dy + '"><img src="' + src(p, true) + '" alt=""></div>';
  }

  var BUILD = {
    contain: function (ps, o) {
      var p = ps[0];
      return '<div class="slide slide--fit"><img class="blurfill" src="' + src(p) + '" alt=""><img class="fitimg" src="' + src(p, true) + '" alt="">' + (o.captions ? caption(ps) : '') + '</div>';
    },
    cover: function (ps, o) {
      var p = ps[0];
      if (p.o === 'p') {
        return '<div class="slide slide--fit"><img class="blurfill" src="' + src(p) + '" alt=""><img class="fitimg" src="' + src(p, true) + '" alt="">' + (o.captions ? caption(ps) : '') + '</div>';
      }
      return '<div class="slide slide--cover">' + kb(p) + (o.captions ? caption(ps) : '') + '</div>';
    },
    pair: function (ps, o) {
      return '<div class="slide slide--pair"><div class="pane">' + kb(ps[0], true) + '</div><div class="pane">' + kb(ps[1], true) + '</div>' + (o.captions ? caption(ps, 'm') : '') + '</div>';
    },
    collage: function (ps, o) {
      return '<div class="slide slide--collage"><div class="pane pane--a">' + kb(ps[0], true) + '</div><div class="pane pane--b">' + kb(ps[1], true) + '</div><div class="pane pane--c">' + kb(ps[2], true) + '</div>' + (o.captions ? caption(ps, 'm') : '') + '</div>';
    },
    polaroid: function (ps) {
      var p = ps[0], m = App.photoMeta(p), rot = (Math.random() * 5 - 2.5).toFixed(1);
      return '<div class="slide slide--polaroid"><img class="blurfill" src="' + src(p) + '" alt="">' +
        '<figure class="polaroid polaroid--' + p.o + '" style="transform:rotate(' + rot + 'deg)"><div class="polaroid-img"><img src="' + src(p, true) + '" alt=""></div>' +
        '<figcaption class="serif"><i>' + (m.place ? App.esc(m.place) + ', ' : '') + m.monthYear + '</i></figcaption></figure></div>';
    }
  };

  App.Slideshow = function (el, opts) {
    this.el = el;
    this.o = Object.assign({ layout: 'auto', captions: true }, opts || {});
    this.last = null;
    this.queue = [];
    this.history = [];
    this.count = 0;
    this.timer = null;
    this.current = null;
    this.sig = '';
    all.push(this);
  };
  var all = [];
  var S = App.Slideshow.prototype;

  S.interval = function () { return this.o.interval || (pcfg().interval_s || 30) * 1000; };
  S.captionsOn = function () { return this.o.captions && pcfg().show_overlay !== false; };

  // Builds a fresh cycle: chronological or shuffled (on-this-day first), never starting with the photo just shown.
  function signature() { return D.photos.map(function (p) { return p.id; }).join(','); }

  S.refill = function () {
    this.sig = signature();
    var q = D.photos.slice();
    if (pcfg().order === 'chronological') q.sort(function (a, b) { return a.date < b.date ? -1 : a.date > b.date ? 1 : 0; });
    else shuffle(q).sort(function (a, b) { return (App.photoMeta(b).onThisDay ? 1 : 0) - (App.photoMeta(a).onThisDay ? 1 : 0); });
    if (q.length > 1 && this.last && q[0].id === this.last) q.push(q.shift());
    this.queue = q;
  };
  S.take = function (pred) {
    if (!this.queue.length || this.sig !== signature()) this.refill();
    for (var i = 0; i < this.queue.length; i++) if (!pred || pred(this.queue[i])) return this.queue.splice(i, 1)[0];
    return null;
  };
  S.pick = function () {
    var layout = this.o.layout === 'auto' ? 'auto' : this.o.layout, n = this.count++;
    var first = this.take();
    if (!first) return { layout: 'empty', photos: [] };
    var self = this;
    function sibling(pred) {
      return self.take(pred) || D.photos.filter(function (x) { return x !== first && pred(x); })[0];
    }
    if (layout === 'auto') layout = pcfg().fit === 'contain' || first.o === 'p' ? 'contain' : 'cover';
    var ps = [first];
    if (layout === 'pair') {
      if (first.o !== 'p') { first = sibling(function (x) { return x.o === 'p'; }); ps = [first]; }
      ps.push(sibling(function (x) { return x !== first && x.o === 'p'; }));
    }
    if (!ps[0] || (layout === 'pair' && !ps[1])) { layout = 'contain'; ps = [first || D.photos[0]]; }
    if (layout === 'collage') {
      ps.push(sibling(function (x) { return x !== first; }));
      ps.push(sibling(function (x) { return ps.indexOf(x) < 0; }));
    }
    return { layout: layout, photos: ps };
  };

  S.render = function (slide) {
    var self = this;
    this.current = slide;
    var wrap = document.createElement('div');
    var opts = Object.assign({}, this.o, { captions: this.captionsOn() });
    wrap.innerHTML = slide.layout === 'empty'
      ? '<div class="slide slide--empty"><div class="serif">' + App.t('photos_none') + '</div></div>'
      : BUILD[slide.layout](slide.photos, opts);
    if (slide.photos[0]) this.last = slide.photos[0].id;
    var node = wrap.firstChild;
    node.style.opacity = '0';
    // Fallback look if images can't load (offline)
    Array.prototype.forEach.call(node.querySelectorAll('img'), function (im) {
      im.addEventListener('error', function () { im.classList.add('is-broken'); });
    });
    var old = Array.prototype.slice.call(this.el.children);
    this.el.appendChild(node);
    var first = node.querySelector('img:not(.blurfill)');
    var shown = false;
    function show() {
      if (shown) return; shown = true;
      node.classList.add('is-in');
      node.style.opacity = '';
      old.forEach(function (o) { o.remove(); });
    }
    if (first && !first.complete) { first.addEventListener('load', show); first.addEventListener('error', show); setTimeout(show, 2500); }
    else show();
    if (this.o.onChange) this.o.onChange(slide);
  };

  S.next = function () {
    var s = this.pick();
    if (!s) return;
    if (this.current) this.history.push(this.current);
    this.render(s);
    this.restart();
  };
  S.prev = function () {
    if (!this.history.length) return;
    this.render(this.history.pop());
    this.restart();
  };
  S.setLayout = function (l) { this.o.layout = l; this.next(); };
  S.restart = function () {
    var self = this;
    clearInterval(this.timer);
    this.timer = setInterval(function () { self.next(); }, this.interval());
  };
  // The photo set changed (new data from the backend): refresh at once if what is on screen is stale.
  S.sync = function () {
    if (this.sig === signature() && this.current && !(this.current.layout === 'empty' && D.photos.length)) return;
    this.refill();
    if (this.timer) this.next();
    else this.current = null;
  };
  App.on('data', function () { all.forEach(function (s) { s.sync(); }); });
  S.start = function () { if (!this.current || (this.current.layout === 'empty' && D.photos.length)) this.next(); else this.restart(); };
  S.stop = function () { clearInterval(this.timer); this.timer = null; };
})();
