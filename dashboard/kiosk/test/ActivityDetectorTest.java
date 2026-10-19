import com.wesbos.homehq.ActivityDetector;
import java.util.Random;

/** Plain-Java checks for the light-activity heuristic. Run with kiosk/test/run.sh. */
public class ActivityDetectorTest {
  static int failures = 0;

  static void check(boolean ok, String what) {
    System.out.println((ok ? "PASS  " : "FAIL  ") + what);
    if (!ok) failures++;
  }

  static ActivityDetector fresh(String sensitivity) {
    return new ActivityDetector(new ActivityDetector.Params().withSensitivity(sensitivity));
  }

  /** Feeds a constant level with noise for the given duration; returns the number of events raised. */
  static int feed(ActivityDetector d, long[] clock, double lux, double noise, long ms, long stepMs, Random rnd) {
    int events = 0;
    for (long t = 0; t < ms; t += stepMs) {
      clock[0] += stepMs;
      if (d.onSample(clock[0], Math.max(0, lux + rnd.nextGaussian() * noise)).event) events++;
    }
    return events;
  }

  public static void main(String[] args) {
    Random rnd = new Random(7);

    {
      ActivityDetector d = fresh("medium"); long[] c = {0};
      int ev = feed(d, c, 120, 1.5, 10 * 60_000, 500, rnd);
      check(ev == 0 && !d.isActive(), "steady room with sensor noise raises no activity");
    }

    {
      ActivityDetector d = fresh("medium"); long[] c = {0};
      feed(d, c, 120, 1.0, 60_000, 500, rnd);
      int ev = feed(d, c, 60, 1.0, 4000, 250, rnd);
      ev += feed(d, c, 120, 1.0, 5000, 250, rnd);
      check(ev >= 1, "a shadow passing the sensor raises activity (events=" + ev + ")");
      check(d.isActive(), "activity stays flagged during the hold time");
      feed(d, c, 120, 1.0, 50_000, 500, rnd);
      check(!d.isActive(), "activity ends after the hold time once the light is back to normal");
    }

    {
      ActivityDetector d = fresh("medium"); long[] c = {0};
      int ev = 0;
      for (int i = 0; i <= 300; i++) ev += feed(d, c, 100 + i, 0.3, 6000, 500, rnd);
      check(ev == 0, "slow daylight drift from 100 to 400 lux over 30 min raises nothing (events=" + ev + ")");
    }

    {
      ActivityDetector d = fresh("medium"); long[] c = {0};
      feed(d, c, 40, 0.5, 60_000, 500, rnd);
      int ev = feed(d, c, 300, 0.5, 20_000, 500, rnd);
      check(ev >= 1, "a lamp switched on raises activity at first (events=" + ev + ")");
      feed(d, c, 300, 0.5, 60_000, 500, rnd);
      int later = feed(d, c, 300, 0.5, 5 * 60_000, 500, rnd);
      check(later == 0, "the new steady light becomes the baseline and stops triggering");
      check(!d.isActive(), "activity ends once the baseline is re-seated");
    }

    {
      ActivityDetector.Params p = new ActivityDetector.Params();
      p.minGapMs = 10_000;
      ActivityDetector d = new ActivityDetector(p); long[] c = {0};
      feed(d, c, 120, 0.5, 60_000, 500, rnd);
      int ev = 0;
      for (int i = 0; i < 6; i++) { ev += feed(d, c, 60, 0.5, 1500, 250, rnd); ev += feed(d, c, 120, 0.5, 1500, 250, rnd); }
      check(ev <= 2, "events respect the minimum gap (events=" + ev + " in 18 s with a 10 s gap)");
    }

    {
      ActivityDetector low = fresh("low"), high = fresh("high"); long[] c1 = {0}, c2 = {0};
      feed(low, c1, 100, 0.3, 60_000, 500, rnd);
      feed(high, c2, 100, 0.3, 60_000, 500, rnd);
      int a = feed(low, c1, 92, 0.3, 3000, 250, rnd);
      int b = feed(high, c2, 92, 0.3, 3000, 250, rnd);
      check(a == 0 && b >= 1, "an 8% dip is ignored on low sensitivity but caught on high (low=" + a + ", high=" + b + ")");
    }

    {
      ActivityDetector d = fresh("medium"); long[] c = {0};
      feed(d, c, 3, 0.2, 60_000, 500, rnd);
      int ev = feed(d, c, 8, 0.2, 4000, 250, rnd);
      check(ev >= 1, "in a dark room the absolute threshold (2.5 lux) is what matters (events=" + ev + ")");
    }

    {
      ActivityDetector d = fresh("medium");
      ActivityDetector.Result r = d.onSample(1000, 50);
      check(!r.event && !r.active && r.baseline == 50, "the first sample only seeds the baseline");
      d.onSample(1000, 50);
      check(true, "samples with identical timestamps do not divide by zero");
    }

    {
      // The real sensor reports whole lux with a +/-1 flicker around 61: a finger close to it moves the value by a few lux.
      ActivityDetector d = fresh("medium"); long[] c = {0};
      int quiet = 0;
      for (int i = 0; i < 240; i++) quiet += feed(d, c, i % 2 == 0 ? 61 : 60, 0, 500, 500, rnd);
      check(quiet == 0, "the +/-1 lux flicker of the real sensor raises nothing (events=" + quiet + ")");
      int ev = feed(d, c, 55, 0.4, 3000, 500, rnd);
      check(ev >= 1, "a finger lowering the reading from 61 to 55 lux is noticed (events=" + ev + ")");
    }

    System.out.println(failures == 0 ? "ALL PASSED" : failures + " FAILED");
    System.exit(failures == 0 ? 0 : 1);
  }
}
