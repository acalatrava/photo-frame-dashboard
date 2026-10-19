// Photos: full-bleed editorial slideshow with layout modes.
(function () {
  'use strict';
  var V = { el: null, show: null, layout: 'auto', loud: false };
  function layouts() { return [['auto', App.t('ly_auto')], ['cover', App.t('ly_cover')], ['pair', App.t('ly_pair')], ['collage', App.t('ly_collage')], ['polaroid', App.t('ly_polaroid')]]; }

  App.register('photos', {
    show: function (el) {
      if (!V.el) {
        V.el = el;
        el.innerHTML = '<div class="photos">' +
          '<div class="ph-stage"></div>' +
          '<button class="ph-zone ph-zone--l" data-prev aria-label="' + App.esc(App.t('prev')) + '"></button>' +
          '<button class="ph-zone ph-zone--c" data-loud aria-label="' + App.esc(App.t('details')) + '"></button>' +
          '<button class="ph-zone ph-zone--r" data-next aria-label="' + App.esc(App.t('next')) + '"></button>' +
          '<div class="ph-top"><div class="seg seg--glass">' + layouts().map(function (l) {
            return '<button data-layout="' + l[0] + '" class="' + (l[0] === V.layout ? 'is-on' : '') + '">' + l[1] + '</button>';
          }).join('') + '</div></div>' +
          '<div class="ph-bottom">' +
          '  <button class="ph-btn" data-prev>' + App.icon('left', 30) + '</button>' +
          '  <button class="ph-btn" data-next>' + App.icon('right', 30) + '</button>' +
          '</div></div>';
        V.show = new App.Slideshow(el.querySelector('.ph-stage'), { layout: V.layout });
        el.addEventListener('click', function (e) {
          var t = e.target.closest('button');
          if (!t) return;
          if (t.hasAttribute('data-next')) V.show.next();
          if (t.hasAttribute('data-prev')) V.show.prev();
          if (t.hasAttribute('data-loud')) { V.loud = !V.loud; el.querySelector('.photos').classList.toggle('is-loud', V.loud); }
          if (t.dataset.layout) {
            V.layout = t.dataset.layout;
            App.$$('[data-layout]', el).forEach(function (b) { b.classList.toggle('is-on', b === t); });
            V.show.setLayout(V.layout);
          }
        });
      }
      V.show.start();
    },
    resume: function () { V.show.start(); },
    hide: function () { if (V.show) V.show.stop(); }
  });
})();
