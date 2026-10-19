package com.wesbos.homehq;

/**
 * Infers coarse "something is happening in the room" activity from an ambient light sensor.
 *
 * It does not detect people. A shadow, a light switch, a screen or a passing cloud can all trigger it, so the
 * result is only ever reported as activity. The detector has no Android dependencies so it can be unit tested
 * with plain javac.
 *
 * How it works:
 *  - Samples may arrive irregularly (on-change sensors), so smoothing is time weighted.
 *  - A slow baseline follows the room's normal light. It barely moves while activity is flagged.
 *  - A sustained offset (a lamp that stays on, the sun coming out) is a new normal: the baseline is re-seated
 *    after {@code reseatMs} and the activity flag ends.
 *  - A trigger needs the smoothed value to leave the baseline by max(minAbsLux, minRel * baseline).
 *    Activity ends below half of that threshold (hysteresis) once the hold time has passed.
 *  - Triggers must persist for {@code debounceMs} and are at least {@code minGapMs} apart.
 */
public final class ActivityDetector {

  /** Tunable parameters; defaults match the backend's PresenceConfig. */
  public static final class Params {
    public double minAbsLux = 2.5;
    public double minRelChange = 0.05;
    public long minGapMs = 2000;
    public long holdMs = 45000;
    public long debounceMs = 250;
    public double smoothTauMs = 600;
    public double baselineTauMs = 15000;
    public long reseatMs = 25000;

    public Params copy() {
      Params p = new Params();
      p.minAbsLux = minAbsLux; p.minRelChange = minRelChange; p.minGapMs = minGapMs; p.holdMs = holdMs;
      p.debounceMs = debounceMs; p.smoothTauMs = smoothTauMs; p.baselineTauMs = baselineTauMs; p.reseatMs = reseatMs;
      return p;
    }

    /** Scales thresholds for a sensitivity label: "low", "medium" (default) or "high". */
    public Params withSensitivity(String s) {
      Params p = copy();
      if ("low".equals(s)) { p.minAbsLux *= 1.8; p.minRelChange *= 1.8; }
      else if ("high".equals(s)) { p.minAbsLux *= 0.55; p.minRelChange *= 0.55; }
      return p;
    }
  }

  /** What one sample produced. */
  public static final class Result {
    public double smoothed;
    public double baseline;
    public boolean active;
    /** True when this sample raised a new activity event (respecting the minimum gap). */
    public boolean event;
  }

  private Params p;
  private boolean init;
  private long lastT;
  private double smoothed;
  private double baseline;
  private boolean active;
  private long aboveSince = -1;
  private long offsetSince = -1;
  private long lastEventT = Long.MIN_VALUE / 2;
  private long lastTriggerT = Long.MIN_VALUE / 2;

  public ActivityDetector(Params params) { this.p = params; }

  public synchronized void setParams(Params params) { this.p = params; }

  public synchronized void reset() {
    init = false; active = false; aboveSince = -1; offsetSince = -1;
    lastEventT = Long.MIN_VALUE / 2; lastTriggerT = Long.MIN_VALUE / 2;
  }

  private double threshold() {
    return Math.max(p.minAbsLux, p.minRelChange * Math.max(baseline, 1.0));
  }

  public synchronized Result onSample(long tMs, double lux) {
    Result r = new Result();
    if (!init) {
      init = true; lastT = tMs; smoothed = lux; baseline = lux;
      r.smoothed = smoothed; r.baseline = baseline; r.active = false;
      return r;
    }
    long dt = Math.max(0, tMs - lastT);
    lastT = tMs;
    smoothed += (lux - smoothed) * (1 - Math.exp(-dt / p.smoothTauMs));

    double delta = Math.abs(smoothed - baseline);
    double th = threshold();
    boolean beyond = delta >= th;

    if (beyond) {
      if (aboveSince < 0) aboveSince = tMs;
      if (offsetSince < 0) offsetSince = tMs;
      if (tMs - aboveSince >= p.debounceMs && tMs - lastEventT >= p.minGapMs) {
        r.event = true;
        lastEventT = tMs;
        lastTriggerT = tMs;
        active = true;
      }
      if (tMs - offsetSince >= p.reseatMs) {
        baseline = smoothed;
        offsetSince = -1;
        aboveSince = -1;
        active = false;
      }
    } else {
      aboveSince = -1;
      offsetSince = -1;
      if (active && delta < th * 0.5 && tMs - lastTriggerT >= p.holdMs) active = false;
    }

    // The baseline learns slowly, and almost not at all while activity is flagged.
    double tau = active ? p.baselineTauMs * 8 : p.baselineTauMs;
    if (!beyond) baseline += (smoothed - baseline) * (1 - Math.exp(-dt / tau));

    r.smoothed = smoothed;
    r.baseline = baseline;
    r.active = active;
    return r;
  }

  public synchronized boolean isActive() { return active; }
}
