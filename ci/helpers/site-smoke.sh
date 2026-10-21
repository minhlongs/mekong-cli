#!/usr/bin/env bash
set -euo pipefail

SITE_URL="${1:?Usage: site-smoke.sh <site-url>}"
SITE_URL="${SITE_URL%/}"

PAGE="$(curl --fail --silent --show-error --retry 10 --retry-delay 2 --retry-all-errors "${SITE_URL}/")"
[[ "$PAGE" == *'Interactive demo only'* ]]
APP_PAGE="$(curl --fail --silent --show-error "${SITE_URL}/app/")"
[[ "$APP_PAGE" == *'<div id="root"'* ]]

STATUS="$(curl --fail --silent --show-error "${SITE_URL}/api/v1/status")"
printf '%s' "$STATUS" | jq -e '.demo_only == true and .status == "demo" and .active_agents == 0' >/dev/null

SIMULATION="$(curl --fail --silent --show-error \
  -H 'Content-Type: application/json' \
  -X POST \
  --data '{"amount":250000,"order_id":"smoke-demo"}' \
  "${SITE_URL}/api/v1/vietqr/simulate")"
printf '%s' "$SIMULATION" | jq -e '.success == true and .simulated == true and .demo_only == true and .verified == false' >/dev/null

printf 'Site demo smoke passed: %s\n' "$SITE_URL"
