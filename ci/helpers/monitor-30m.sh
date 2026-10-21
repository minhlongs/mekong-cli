#!/usr/bin/env bash
set -euo pipefail

: "${API_URL:?API_URL is required}"
: "${DASHBOARD_URL:?DASHBOARD_URL is required}"
: "${SITE_URL:?SITE_URL is required}"
: "${API_BASELINE_MS:?API_BASELINE_MS is required}"
: "${DASHBOARD_BASELINE_MS:?DASHBOARD_BASELINE_MS is required}"
: "${SITE_BASELINE_MS:?SITE_BASELINE_MS is required}"
: "${SECURITY_ALERT_URL:?SECURITY_ALERT_URL must point to the active security alert feed}"

SAMPLE_COUNT="${MONITOR_SAMPLE_COUNT:-30}"
INTERVAL_SECONDS="${MONITOR_INTERVAL_SECONDS:-60}"
PROBES_PER_TARGET="${MONITOR_PROBES_PER_TARGET:-2}"
ERROR_LIMIT_PERCENT="${ERROR_LIMIT_PERCENT:-5}"
RELEASE_TMP_ROOT="${RELEASE_TMP_ROOT:-${TMPDIR:-/tmp}}"
TMP_DIR="$(mktemp -d "$RELEASE_TMP_ROOT/mekong-monitor.XXXXXX")"
PROBE_LOG="$TMP_DIR/probes.tsv"
trap 'rm -rf "$TMP_DIR"' EXIT

probe() {
  local name="$1" url="$2" baseline_ms="$3" kind="$4"
  local body="$TMP_DIR/$name.body" response code seconds latency_ms healthy=1

  if ! response="$(curl --silent --show-error --max-time 20 \
    --output "$body" --write-out '%{http_code} %{time_total}' "$url")"; then
    response="000 0"
    healthy=0
  fi

  read -r code seconds <<< "$response"
  latency_ms="$(awk -v seconds="${seconds:-0}" 'BEGIN { printf "%.0f", seconds * 1000 }')"
  if [[ "$code" != 2* ]]; then
    healthy=0
  elif [[ "$kind" == "api" ]]; then
    jq -e '.status == "ok" and .database.connected == true and .bindings.d1 == true and .bindings.kv == true and .bindings.queue == true and .pilot.invite_only == true and .pilot.llm_only == true' "$body" >/dev/null || healthy=0
  elif [[ "$kind" == "dashboard" ]]; then
    grep -qi 'synthetic' "$body" || healthy=0
  else
    grep -q 'Interactive demo only' "$body" || healthy=0
  fi

  printf '%s\t%s\t%s\t%s\n' "$(date +%s)" "$healthy" "$latency_ms" "$name" >> "$PROBE_LOG"
  printf '%s: HTTP %s, %sms, healthy=%s\n' "$name" "$code" "$latency_ms" "$healthy"

  if awk -v latency="$latency_ms" -v baseline="$baseline_ms" \
    'BEGIN { exit !(baseline > 0 && latency > baseline * 2) }'; then
    echo "ERROR: $name latency exceeded twice its pre-deploy median baseline" >&2
    return 1
  fi
}

for sample in $(seq 1 "$SAMPLE_COUNT"); do
  echo "==> Production monitor sample $sample/$SAMPLE_COUNT"
  ./ci/helpers/check-security-alert.sh
  for attempt in $(seq 1 "$PROBES_PER_TARGET"); do
    probe api "${API_URL%/}/health" "$API_BASELINE_MS" api
    probe dashboard "$DASHBOARD_URL" "$DASHBOARD_BASELINE_MS" dashboard
    probe site "${SITE_URL%/}/" "$SITE_BASELINE_MS" site
    if [[ "$attempt" -lt "$PROBES_PER_TARGET" ]]; then
      sleep 1
    fi
  done

  now="$(date +%s)"
  window_start="$((now - 600))"
  awk -F '\t' -v start="$window_start" -v limit="$ERROR_LIMIT_PERCENT" '
    $1 >= start { total[$4]++; if ($2 == 0) failures[$4]++ }
    END {
      failed = 0
      for (target in total) {
        if (total[target] >= 20) {
          count = failures[target] + 0
          rate = count * 100 / total[target]
          printf "10-minute %s synthetic probe error rate: %.2f%% (%d/%d)\n", target, rate, count, total[target]
          if (rate > limit) failed = 1
        }
      }
      if (failed) exit 1
    }
  ' "$PROBE_LOG" || {
    echo "ERROR: synthetic probe error rate exceeded ${ERROR_LIMIT_PERCENT}% in the rolling 10-minute window" >&2
    exit 1
  }

  sleep "$INTERVAL_SECONDS"
done

echo "==> Completed ${SAMPLE_COUNT} production monitor samples"
