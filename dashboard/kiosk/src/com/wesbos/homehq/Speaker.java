package com.wesbos.homehq;

import android.content.Context;
import android.media.AudioManager;
import android.os.Bundle;
import android.speech.tts.TextToSpeech;
import android.speech.tts.UtteranceProgressListener;
import android.util.Log;

import java.util.Locale;

/**
 * Text to speech and the media volume of the frame.
 *
 * Android's speech engine may be missing on these frames, so everything reports whether it is really available and
 * the page falls back to a plain message when it is not. The engine is created lazily, on the main thread.
 */
final class Speaker {
  private static final String TAG = "HomeHQ";

  private final Context ctx;
  private final android.os.Handler main = new android.os.Handler(android.os.Looper.getMainLooper());
  private TextToSpeech tts;
  private volatile boolean ready;
  private volatile boolean failed;
  private String pendingText, pendingLang;
  private int pendingVolume;
  private volatile Hardware.Sink sink;

  Speaker(Context ctx) { this.ctx = ctx.getApplicationContext(); }

  void setSink(Hardware.Sink s) { sink = s; }

  /** True once the engine started; false while it is starting and when there is none. */
  boolean available() {
    ensure();
    return ready;
  }

  boolean unavailable() { return failed; }

  private void ensure() {
    if (tts != null || failed) return;
    main.post(() -> {
      if (tts != null) return;
      try {
        tts = new TextToSpeech(ctx, status -> {
          if (status != TextToSpeech.SUCCESS) { failed = true; Log.w(TAG, "No speech engine"); return; }
          tts.setOnUtteranceProgressListener(new UtteranceProgressListener() {
            @Override public void onStart(String id) { }
            @Override public void onDone(String id) { notifyDone("done"); }
            @Override public void onError(String id) { notifyDone("error"); }
          });
          ready = true;
          if (pendingText != null) { String t = pendingText, l = pendingLang; int v = pendingVolume; pendingText = null; doSpeak(t, l, v); }
        });
      } catch (RuntimeException e) {
        failed = true;
        Log.w(TAG, "Speech engine failed to start", e);
      }
    });
  }

  private void notifyDone(String state) {
    Hardware.Sink s = sink;
    if (s != null) s.emit("tts", "{\"state\":\"" + state + "\"}");
  }

  void speak(String text, String lang, int volumePct) {
    if (text == null || text.trim().isEmpty()) return;
    if (!ready) {
      pendingText = text; pendingLang = lang; pendingVolume = volumePct;
      ensure();
      return;
    }
    doSpeak(text, lang, volumePct);
  }

  private void doSpeak(String text, String lang, int volumePct) {
    main.post(() -> {
      if (tts == null || !ready) return;
      Locale want = lang != null && lang.startsWith("en") ? Locale.UK : new Locale("es", "ES");
      int ok = tts.isLanguageAvailable(want);
      tts.setLanguage(ok >= TextToSpeech.LANG_AVAILABLE ? want : Locale.getDefault());
      Bundle params = new Bundle();
      params.putFloat(TextToSpeech.Engine.KEY_PARAM_VOLUME, Math.max(0.05f, Math.min(1f, volumePct / 100f)));
      tts.speak(text, TextToSpeech.QUEUE_FLUSH, params, "hq-" + System.nanoTime());
    });
  }

  void stop() {
    main.post(() -> { if (tts != null && ready) tts.stop(); });
  }

  void setVolume(int pct) {
    AudioManager am = (AudioManager) ctx.getSystemService(Context.AUDIO_SERVICE);
    if (am == null) return;
    int max = am.getStreamMaxVolume(AudioManager.STREAM_MUSIC);
    am.setStreamVolume(AudioManager.STREAM_MUSIC, Math.round(Math.max(0, Math.min(100, pct)) / 100f * max), 0);
  }

  void shutdown() {
    main.post(() -> { if (tts != null) { tts.stop(); tts.shutdown(); tts = null; ready = false; } });
  }
}
