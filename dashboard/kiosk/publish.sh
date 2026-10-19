#!/usr/bin/env bash
# Uploads kiosk/build/homehq.apk to a Home HQ backend and (optionally) publishes it, so the frames update over
# the network instead of over USB. Build first with ./build.sh and raise --version-code there.
#
#   HOMEHQ_URL=http://192.168.1.177:8787 HOMEHQ_ADMIN_PASSWORD=... ./publish.sh [--publish] ["release notes"]
set -euo pipefail
cd "$(dirname "$0")"

URL="${HOMEHQ_URL:?Set HOMEHQ_URL, e.g. http://192.168.1.177:8787}"
URL="${URL%/}"
USER_NAME="${HOMEHQ_ADMIN_USER:-admin}"
: "${HOMEHQ_ADMIN_PASSWORD:?Set HOMEHQ_ADMIN_PASSWORD}"
APK="${HOMEHQ_APK:-build/homehq.apk}"
PUBLISH=0
if [ "${1:-}" = "--publish" ]; then PUBLISH=1; shift; fi
NOTES="${1:-}"

[ -f "$APK" ] || { echo "No APK at $APK: run ./build.sh first" >&2; exit 1; }

urlencode() {
  local LC_ALL=C
  local s="$1" out="" c i
  for ((i = 0; i < ${#s}; i++)); do
    c="${s:i:1}"
    case "$c" in
      [a-zA-Z0-9.~_-]) out+="$c" ;;
      *) out+="$(printf '%%%02X' "$(($(printf '%d' "'$c") & 255))")" ;;
    esac
  done
  printf '%s' "$out"
}

json_escape() { printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g'; }

JAR="$(mktemp)"
trap 'rm -f "$JAR"' EXIT
ADMIN=(-H "X-HomeHQ-Admin: 1")

# The password is fed through a file descriptor rather than the command line, so it never shows up in `ps`.
curl -fsS -c "$JAR" "${ADMIN[@]}" -H "Content-Type: application/json" -X POST "$URL/api/v1/admin/auth/login" \
  --data-binary @<(printf '{"username":"%s","password":"%s"}' "$(json_escape "$USER_NAME")" "$(json_escape "$HOMEHQ_ADMIN_PASSWORD")") >/dev/null

QUERY="filename=$(urlencode "$(basename "$APK")")&notes=$(urlencode "$NOTES")"
RESP="$(curl -sS -b "$JAR" "${ADMIN[@]}" -H "Content-Type: application/octet-stream" -X POST \
  -w '\n%{http_code}' --data-binary @"$APK" "$URL/api/v1/admin/updates?$QUERY")"
CODE="${RESP##*$'\n'}"
BODY="${RESP%$'\n'*}"
if [ "$CODE" != "200" ]; then
  echo "Upload refused ($CODE): $BODY" >&2
  exit 1
fi
VERSION_CODE="$(printf '%s' "$BODY" | sed -n 's/.*"version_code":\([0-9]*\).*/\1/p')"
VERSION_NAME="$(printf '%s' "$BODY" | sed -n 's/.*"version_name":"\([^"]*\)".*/\1/p')"
if printf '%s' "$BODY" | grep -q '"created":false'; then
  echo "Home HQ $VERSION_NAME (versionCode $VERSION_CODE) was already uploaded."
else
  echo "Uploaded Home HQ $VERSION_NAME (versionCode $VERSION_CODE)."
fi

if [ "$PUBLISH" = "1" ]; then
  curl -fsS -b "$JAR" "${ADMIN[@]}" -X POST "$URL/api/v1/admin/updates/$VERSION_CODE/publish" >/dev/null
  echo "Published: the frames will be offered it now."
else
  echo "Not published yet: publish it from Admin > Updates, or re-run with --publish."
fi
