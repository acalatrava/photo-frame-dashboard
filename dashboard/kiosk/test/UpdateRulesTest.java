package com.wesbos.homehq;

import java.io.ByteArrayInputStream;

public class UpdateRulesTest {
  static int failures = 0;

  static void check(String name, boolean ok) {
    System.out.println((ok ? "PASS  " : "FAIL  ") + name);
    if (!ok) failures++;
  }

  public static void main(String[] args) throws Exception {
    check("accepts the backend APK endpoint over http", UpdateRules.validUrl("http://192.168.1.177:8787/api/v1/device/update/apk"));
    check("accepts https with a path prefix", UpdateRules.validUrl("https://hq.example.com/hq/api/v1/device/update/apk"));
    check("rejects other paths", !UpdateRules.validUrl("http://192.168.1.177:8787/api/v1/admin/status"));
    check("rejects other schemes", !UpdateRules.validUrl("file:///sdcard/evil/api/v1/device/update/apk"));
    check("rejects user info tricks", !UpdateRules.validUrl("http://good@evil.example/api/v1/device/update/apk"));
    check("rejects the endpoint hidden in a query", !UpdateRules.validUrl("http://evil.example/x?a=/api/v1/device/update/apk"));
    check("rejects null and absurd lengths", !UpdateRules.validUrl(null) && !UpdateRules.validUrl("http://a/" + "x".repeat(400) + UpdateRules.APK_PATH));

    check("a newer version code is accepted", UpdateRules.isNewer(7, 6));
    check("the same or older version code is refused", !UpdateRules.isNewer(6, 6) && !UpdateRules.isNewer(5, 6));

    check("sha256 of 'abc' matches the known digest",
        UpdateRules.sha256("abc".getBytes("UTF-8")).equals("ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"));
    check("streaming sha256 equals the one-shot digest",
        UpdateRules.sha256(new ByteArrayInputStream(new byte[100000])).equals(UpdateRules.sha256(new byte[100000])));
    check("digests compare ignoring case", UpdateRules.sameDigest("ABCDEF", "abcdef") && !UpdateRules.sameDigest("a", null));
    check("only 64 hex characters are a sha256", UpdateRules.validSha256("ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")
        && !UpdateRules.validSha256("xyz") && !UpdateRules.validSha256(null));

    System.out.println(failures == 0 ? "ALL PASSED" : failures + " FAILED");
    System.exit(failures == 0 ? 0 : 1);
  }
}
