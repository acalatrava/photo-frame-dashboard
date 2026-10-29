import com.wesbos.homehq.LightsOffDetector;

/** Plain-Java checks for the "light switched off" detector. Run with kiosk/test/run.sh. */
public class LightsOffDetectorTest {
  static int failures = 0;

  static void check(boolean ok, String what) {
    System.out.println((ok ? "PASS  " : "FAIL  ") + what);
    if (!ok) failures++;
  }

  static LightsOffDetector fresh() { return new LightsOffDetector(new LightsOffDetector.Params()); }

  /** Feeds a level once per second; returns how many times the detector fired. */
  static int feed(LightsOffDetector d, long[] clock, double lux, int seconds) {
    int fired = 0;
    for (int i = 0; i < seconds; i++) {
      clock[0] += 1000;
      if (d.onSample(clock[0], lux)) fired++;
    }
    return fired;
  }

  public static void main(String[] args) {
    {
      LightsOffDetector d = fresh(); long[] c = {0};
      feed(d, c, 120, 60);
      int fired = feed(d, c, 2, 10);
      check(fired == 1, "a lit room that goes dark fires once (fired=" + fired + ")");
      check(feed(d, c, 2, 120) == 0, "it does not fire again while the room stays dark");
    }
    {
      LightsOffDetector d = fresh(); long[] c = {0};
      feed(d, c, 150, 60);
      check(feed(d, c, 60, 10) == 0, "a shadow that halves the light does not fire");
    }
    {
      LightsOffDetector d = fresh(); long[] c = {0};
      int fired = 0;
      for (double lux = 300; lux > 0.5; lux *= 0.97) fired += feed(d, c, lux, 3);
      check(fired == 0, "a slow sunset fades to almost nothing without firing (fired=" + fired + ")");
    }
    {
      LightsOffDetector d = fresh(); long[] c = {0};
      feed(d, c, 8, 120);
      check(feed(d, c, 1, 20) == 0, "a room that was already dim has nothing to switch off");
    }
    {
      LightsOffDetector d = fresh(); long[] c = {0};
      feed(d, c, 120, 60);
      check(feed(d, c, 2, 1) == 0, "the drop must last a moment before it counts");
      check(feed(d, c, 120, 5) == 0, "a flicker that comes straight back never fires");
    }
    {
      LightsOffDetector d = fresh(); long[] c = {0};
      feed(d, c, 120, 60);
      d.suppressUntil(c[0] + 15_000);
      check(feed(d, c, 2, 12) == 0, "a drop caused by the frame's own brightness change is ignored");
    }
    {
      LightsOffDetector d = fresh(); long[] c = {0};
      feed(d, c, 120, 60);
      feed(d, c, 2, 10);
      feed(d, c, 120, 60);
      int again = feed(d, c, 1, 10);
      check(again == 1, "after the light comes back it can fire again (fired=" + again + ")");
    }
    if (failures > 0) { System.out.println(failures + " failed"); System.exit(1); }
    System.out.println("All good");
  }
}
