// Sounds, made on the fly with Web Audio so nothing has to be bundled or downloaded, plus text to speech.
(function () {
  'use strict';
  var N = App.native, ctx = null;

  function context() {
    if (!ctx) {
      var C = window.AudioContext || window.webkitAudioContext;
      if (!C) return null;
      try { ctx = new C(); } catch (e) { return null; }
    }
    if (ctx.state === 'suspended' && ctx.resume) ctx.resume();
    return ctx;
  }
  // Browsers (not the kiosk) only allow sound after a touch.
  document.addEventListener('pointerdown', function () { context(); }, true);

  var BELL = [[1, 1], [2.4, 0.55], [4.1, 0.28], [6.2, 0.12]];
  var SOFT = [[1, 1], [2, 0.25]];

  // A voice is [frequency, start (s), length (s), gain, partials, wave].
  var SOUNDS = {
    chime: function () {
      return [[784, 0, 2.2, 0.5, BELL], [659, 0.6, 2.2, 0.5, BELL], [523, 1.2, 2.2, 0.5, BELL], [392, 1.8, 3.2, 0.55, BELL]];
    },
    bell: function () {
      return [[587, 0, 3.2, 0.6, BELL], [587, 1.5, 3.2, 0.45, BELL]];
    },
    soft: function () {
      return [[523, 0, 1.4, 0.5, SOFT, 'triangle'], [784, 0.35, 1.8, 0.45, SOFT, 'triangle']];
    },
    beep: function () {
      return [[1000, 0, 0.16, 0.5, [[1, 1]], 'square'], [1000, 0.28, 0.16, 0.5, [[1, 1]], 'square'], [1000, 0.56, 0.16, 0.5, [[1, 1]], 'square']];
    },
    melody: function () {
      var n = [523, 659, 784, 1047, 784, 1047], v = [];
      n.forEach(function (f, i) { v.push([f, i * 0.28, i === n.length - 1 ? 1.6 : 0.5, 0.45, SOFT, 'triangle']); });
      return v;
    }
  };
  var LENGTH = { chime: 5, bell: 4.7, soft: 2.2, beep: 0.8, melody: 3.2 };

  function voice(c, out, v, t0) {
    var f = v[0], start = t0 + v[1], len = v[2], gain = v[3], parts = v[4], wave = v[5] || 'sine';
    parts.forEach(function (p) {
      var o = c.createOscillator(), g = c.createGain();
      o.type = wave;
      o.frequency.value = f * p[0];
      var peak = gain * p[1] * 0.5, end = start + len / (p[0] > 3 ? 2.5 : 1);
      g.gain.setValueAtTime(0.0001, start);
      g.gain.linearRampToValueAtTime(peak, start + 0.012);
      g.gain.exponentialRampToValueAtTime(0.0001, end);
      o.connect(g); g.connect(out);
      o.start(start); o.stop(end + 0.05);
    });
  }

  // Plays a named sound at a volume from 1 to 100 and returns a handle whose stop() fades it out.
  function play(name, volume) {
    var c = context();
    if (!c || !SOUNDS[name]) return { stop: function () {}, seconds: 0 };
    var out = c.createGain();
    out.gain.value = Math.max(0.02, Math.min(1, (volume == null ? 70 : volume) / 100));
    out.connect(c.destination);
    var t0 = c.currentTime + 0.05;
    SOUNDS[name]().forEach(function (v) { voice(c, out, v, t0); });
    return {
      seconds: LENGTH[name],
      stop: function () {
        try { out.gain.setTargetAtTime(0.0001, c.currentTime, 0.05); setTimeout(function () { out.disconnect(); }, 400); } catch (e) { /* already gone */ }
      }
    };
  }

  // Text to speech: the Android engine when the frame has one, the browser's own otherwise (desktop preview).
  function speak(text, volume) {
    if (!text) return false;
    var lang = App.locale || 'es-ES';
    if (N.available && !N.ttsMissing()) { N.speak(text, lang, volume == null ? 80 : volume); return true; }
    if (window.speechSynthesis && window.SpeechSynthesisUtterance) {
      try {
        var u = new window.SpeechSynthesisUtterance(text);
        u.lang = lang; u.volume = Math.max(0.05, Math.min(1, (volume == null ? 80 : volume) / 100));
        window.speechSynthesis.cancel(); window.speechSynthesis.speak(u);
        return true;
      } catch (e) { /* no voice installed */ }
    }
    return false;
  }
  function stopSpeaking() {
    if (N.available) N.stopSpeaking();
    try { if (window.speechSynthesis) window.speechSynthesis.cancel(); } catch (e) { /* ignore */ }
  }

  App.audio = {
    names: Object.keys(SOUNDS), play: play, speak: speak, stopSpeaking: stopSpeaking,
    seconds: function (name) { return LENGTH[name] || 0; },
    speaks: function () { return N.available ? !N.ttsMissing() : !!window.speechSynthesis; }
  };

  // The engine takes a moment to start, so it is woken up early; a frame without one is then known to be silent.
  App.on('ready', function () { setTimeout(function () { if (N.available) N.ttsAvailable(); }, 4000); });
})();
