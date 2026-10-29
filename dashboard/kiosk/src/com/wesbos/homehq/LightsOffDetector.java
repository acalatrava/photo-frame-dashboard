package com.wesbos.homehq;

import java.util.ArrayDeque;

/**
 * Notices the moment somebody switches the room light off: the reading collapses to almost nothing within seconds.
 *
 * It fires when the level has stayed below {@code offLux} for {@code confirmMs} after being at least
 * {@code minBeforeLux} (and at least {@code 1 / maxRatio} times higher) during the last {@code windowMs}. A slow
 * sunset never gets there, and a shadow does not fall below the absolute level. After firing it waits for the light
 * to come back before it can fire again. Plain Java so it can be unit tested without Android.
 */
public final class LightsOffDetector {
  public static final class Params {
    public double offLux = 10;
    public double minBeforeLux = 25;
    public double maxRatio = 0.35;
    public long windowMs = 6000;
    public long confirmMs = 1500;
    public long rearmMs = 30000;
  }

  private final Params p;
  private final ArrayDeque<double[]> history = new ArrayDeque<>();
  private long lowSince = -1;
  private long lastFire = Long.MIN_VALUE / 2;
  private long suppressUntil = Long.MIN_VALUE / 2;
  private boolean armed = true;

  public LightsOffDetector(Params params) { this.p = params; }

  public synchronized void setOffLux(double v) { p.offLux = v; p.minBeforeLux = Math.max(25, v * 2.5); }

  /** The frame changed its own brightness, which moves the reading without anything happening in the room. */
  public synchronized void suppressUntil(long tMs) { suppressUntil = Math.max(suppressUntil, tMs); }

  public synchronized void reset() {
    history.clear(); lowSince = -1; armed = true;
  }

  /** Returns true on the sample that confirms the light went off. */
  public synchronized boolean onSample(long tMs, double lux) {
    history.addLast(new double[] {tMs, lux});
    while (!history.isEmpty() && tMs - history.peekFirst()[0] > p.windowMs) history.removeFirst();

    if (!armed) {
      if (lux >= p.offLux * 1.5 && tMs - lastFire >= p.rearmMs) armed = true;
      return false;
    }

    double ref = 0;
    for (double[] h : history) ref = Math.max(ref, h[1]);
    boolean collapsed = lux < p.offLux && ref >= p.minBeforeLux && lux <= ref * p.maxRatio;
    if (!collapsed || tMs < suppressUntil) {
      lowSince = -1;
      return false;
    }
    if (lowSince < 0) lowSince = tMs;
    if (tMs - lowSince >= p.confirmMs) {
      armed = false;
      lastFire = tMs;
      lowSince = -1;
      return true;
    }
    return false;
  }
}
