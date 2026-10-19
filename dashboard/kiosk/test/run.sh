#!/usr/bin/env bash
# Compiles and runs the pure-Java tests (no Android SDK needed).
set -euo pipefail
cd "$(dirname "$0")"
OUT="$(mktemp -d)"
javac -nowarn -d "$OUT" ../src/com/wesbos/homehq/ActivityDetector.java ActivityDetectorTest.java \
  ../src/com/wesbos/homehq/UpdateRules.java UpdateRulesTest.java
java -cp "$OUT" ActivityDetectorTest
java -cp "$OUT" com.wesbos.homehq.UpdateRulesTest
