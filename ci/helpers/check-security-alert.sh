#!/usr/bin/env bash
set -euo pipefail

: "${SECURITY_ALERT_URL:?SECURITY_ALERT_URL is required}"
RELEASE_TMP_ROOT="${RELEASE_TMP_ROOT:-${TMPDIR:-/tmp}}"
TMP_FILE="$(mktemp "$RELEASE_TMP_ROOT/mekong-security-alert.XXXXXX")"
trap 'rm -f "$TMP_FILE"' EXIT

AUTH_HEADER=()
if [[ -n "${SECURITY_ALERT_TOKEN:-}" ]]; then
  AUTH_HEADER=(-H "Authorization: Bearer $SECURITY_ALERT_TOKEN")
fi

if ! status="$(curl --silent --max-time 20 --output "$TMP_FILE" --write-out '%{http_code}' \
  "${AUTH_HEADER[@]}" "$SECURITY_ALERT_URL" 2>/dev/null)"; then
  echo "ERROR: security alert feed could not be reached" >&2
  exit 1
fi

if [[ "$status" != "200" ]] || ! jq -e '.active == false' "$TMP_FILE" >/dev/null 2>&1; then
  echo "ERROR: security alert feed is active, invalid, or unhealthy" >&2
  exit 1
fi
