package com.wesbos.homehq;

import java.io.IOException;
import java.io.InputStream;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.Locale;

/** The pure checks behind over-the-network updates, kept free of Android classes so they can be unit tested. */
final class UpdateRules {
  private UpdateRules() { }

  static final String APK_PATH = "/api/v1/device/update/apk";

  /** The page may only ask for the backend's APK endpoint, never an arbitrary download. */
  static boolean validUrl(String url) {
    if (url == null || url.length() > 300) return false;
    String u = url.toLowerCase(Locale.ROOT);
    if (!(u.startsWith("http://") || u.startsWith("https://"))) return false;
    int q = u.indexOf('?');
    String noQuery = q < 0 ? u : u.substring(0, q);
    return noQuery.endsWith(APK_PATH) && u.indexOf('@') < 0 && u.indexOf(' ') < 0;
  }

  /** A frame only ever moves forward: Android would refuse a downgrade anyway. */
  static boolean isNewer(int candidate, int installed) {
    return candidate > installed;
  }

  static boolean validSha256(String hex) {
    return hex != null && hex.matches("[0-9a-fA-F]{64}");
  }

  static String hex(byte[] bytes) {
    StringBuilder sb = new StringBuilder(bytes.length * 2);
    for (byte b : bytes) sb.append(String.format(Locale.ROOT, "%02x", b & 0xff));
    return sb.toString();
  }

  static String sha256(byte[] data) {
    try {
      return hex(MessageDigest.getInstance("SHA-256").digest(data));
    } catch (NoSuchAlgorithmException e) {
      throw new IllegalStateException(e);
    }
  }

  static MessageDigest newDigest() {
    try {
      return MessageDigest.getInstance("SHA-256");
    } catch (NoSuchAlgorithmException e) {
      throw new IllegalStateException(e);
    }
  }

  static String sha256(InputStream in) throws IOException {
    MessageDigest md = newDigest();
    byte[] buf = new byte[16384];
    int n;
    while ((n = in.read(buf)) > 0) md.update(buf, 0, n);
    return hex(md.digest());
  }

  static boolean sameDigest(String a, String b) {
    return a != null && b != null && a.equalsIgnoreCase(b);
  }
}
