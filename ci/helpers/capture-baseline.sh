#!/usr/bin/env bash
set -euo pipefail

URL="${1:?Usage: capture-baseline.sh <url>}"
SAMPLE_COUNT="${BASELINE_SAMPLE_COUNT:-9}"
TMP_FILE="$(mktemp)"
trap 'rm -f "$TMP_FILE"' EXIT

for _ in $(seq 1 "$SAMPLE_COUNT"); do
  curl --fail --silent --show-error --max-time 20 \
    --output /dev/null --write-out '%{time_total}\n' "$URL" >> "$TMP_FILE"
done

sort -n "$TMP_FILE" | awk -v count="$SAMPLE_COUNT" '
  NR == int((count + 1) / 2) { printf "%.0f\n", $1 * 1000 }
'
