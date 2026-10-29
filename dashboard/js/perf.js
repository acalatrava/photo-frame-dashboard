// Main-thread health. Long tasks are what make a touch screen feel dead, so they are counted and reported with the
// heartbeat; the admin panel shows them next to the frame and a stall can be traced to a time of day.
(function () {
  'use strict';
  var WINDOW_MS = 10 * 60 * 1000, tasks = [];

  function record(ms) {
    var now = Date.now();
    tasks.push([now, ms]);
    while (tasks.length && now - tasks[0][0] > WINDOW_MS) tasks.shift();
  }

  try {
    if (window.PerformanceObserver) {
      new PerformanceObserver(function (list) {
        list.getEntries().forEach(function (e) { record(e.duration); });
      }).observe({ entryTypes: ['longtask'] });
    }
  } catch (e) { /* longtask is not offered by this WebView: the timer below still catches stalls */ }

  // A timer that fires late means the page was busy; this works even where long-task entries do not exist.
  var expected = Date.now() + 1000, lateMax = 0;
  setInterval(function () {
    var late = Date.now() - expected;
    if (late > 250) lateMax = Math.max(lateMax, late);
    expected = Date.now() + 1000;
  }, 1000);

  App.perf = {
    report: function () {
      var now = Date.now(), recent = tasks.filter(function (t) { return now - t[0] <= WINDOW_MS; });
      var max = recent.reduce(function (m, t) { return Math.max(m, t[1]); }, 0);
      var out = { long_tasks_10m: recent.length, longest_ms: Math.round(Math.max(max, lateMax)), timer_late_ms: Math.round(lateMax) };
      lateMax = 0;
      return out;
    }
  };
})();
