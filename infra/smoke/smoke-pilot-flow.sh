#!/usr/bin/env bash
# Smoke-test the VN Pilot live gateway — read-only synthetic monitoring.
#
# Hits every dashboard-relevant endpoint, validates response schema, exits
# 0 (all healthy) / 1 (any failure). Safe to run every minute via cron;
# does NOT mutate state (no /signup, /response, /convert calls — those
# are covered by tests/vn/).
#
# Usage:
#   ./infra/smoke/smoke-pilot-flow.sh                              # against prod
#   GATEWAY=http://localhost:8000 ./infra/smoke/smoke-pilot-flow.sh   # local
#   VERBOSE=1 ./infra/smoke/smoke-pilot-flow.sh                    # dump full responses
#
# Exit codes:
#   0 — all checks pass
#   1 — any check failed (curl error, HTTP non-200, schema mismatch)
#   2 — dependency missing (curl, jq)

set -uo pipefail

GATEWAY="${GATEWAY:-https://gateway.cashclaw.cc}"
VERBOSE="${VERBOSE:-0}"
TIMEOUT="${TIMEOUT:-10}"
FAILS=0
CHECKS=0

# --- Dependencies ---
for bin in curl jq; do
  if ! command -v "$bin" >/dev/null 2>&1; then
    echo "❌ Missing dependency: $bin" >&2
    exit 2
  fi
done

# --- Helpers ---
hr() { printf '%s\n' "----------------------------------------"; }

pass() {
  CHECKS=$((CHECKS + 1))
  printf "  ✅ %s\n" "$1"
}

fail() {
  CHECKS=$((CHECKS + 1))
  FAILS=$((FAILS + 1))
  printf "  ❌ %s\n" "$1"
}

# Fetch body into tmpfile + return HTTP code via stdout. No pass/fail calls
# here (would lose counter state in subshell). Caller compares code and reads
# tmpfile, then calls pass/fail in parent shell.
# Args: <url> <tmpfile_path>
fetch_to_file() {
  local url="$1" tmpfile="$2"
  curl -sS --max-time "$TIMEOUT" -o "$tmpfile" -w "%{http_code}" "$url" 2>/dev/null \
    || echo "curl_error"
}

# Verify a JSON body file has all required keys. Calls pass/fail directly.
# Args: <description> <body_file> <key1> [key2 ...]
check_keys() {
  local desc="$1" file="$2"
  shift 2
  local missing=()
  for k in "$@"; do
    if ! jq -e ". | has(\"$k\")" "$file" >/dev/null 2>&1; then
      missing+=("$k")
    fi
  done
  if [ "${#missing[@]}" -eq 0 ]; then
    pass "$desc — schema OK"
  else
    fail "$desc — missing keys: ${missing[*]}"
  fi
}

# Compose fetch + HTTP-200 check; returns 0 if 200, 1 otherwise. Tmpfile
# already contains body for the caller to inspect.
# Args: <desc> <url> <tmpfile>
check_200() {
  local desc="$1" url="$2" tmp="$3" code
  code=$(fetch_to_file "$url" "$tmp")
  if [ "$code" = "200" ]; then
    pass "$desc — HTTP 200"
    return 0
  else
    fail "$desc — HTTP $code"
    [ "$VERBOSE" = "1" ] && cat "$tmp" >&2
    return 1
  fi
}

# --- Run checks ---
echo "🔍 Smoke-testing $GATEWAY at $(date -u +%Y-%m-%dT%H:%M:%SZ)"
hr

TMP=$(mktemp)
trap 'rm -f "$TMP"' EXIT

# 1. Gateway health
if check_200 "gateway /healthz" "$GATEWAY/healthz" "$TMP"; then
  check_keys "/healthz" "$TMP" status version
fi

# 2. Pilot router health
if check_200 "/v1/pilot/health" "$GATEWAY/v1/pilot/health" "$TMP"; then
  check_keys "/v1/pilot/health" "$TMP" status service
fi

# 3. Pilot stats (post-Round-9: must include trial + converted)
if check_200 "/v1/pilot/stats" "$GATEWAY/v1/pilot/stats" "$TMP"; then
  check_keys "/v1/pilot/stats" "$TMP" \
    total_pilots active_pilots converted_pilots trial_pilots \
    capacity_remaining by_type by_source
  trial=$(jq -r '.trial_pilots // 0' "$TMP")
  converted=$(jq -r '.converted_pilots // 0' "$TMP")
  active=$(jq -r '.active_pilots // 0' "$TMP")
  if [ "$((trial + converted))" = "$active" ]; then
    pass "/v1/pilot/stats — invariant trial+converted==active ($active)"
  else
    fail "/v1/pilot/stats — invariant violated: $trial+$converted != $active"
  fi
fi

# 4. Pilot revenue (post-Round-6)
if check_200 "/v1/pilot/revenue" "$GATEWAY/v1/pilot/revenue" "$TMP"; then
  check_keys "/v1/pilot/revenue" "$TMP" \
    conversions unique_converted_users conversion_rate mrr_vnd by_tier \
    target_mrr_vnd target_conversions
fi

# 5. Pilot recent timeline (post-Round-5)
if check_200 "/v1/pilot/recent" "$GATEWAY/v1/pilot/recent?limit=5" "$TMP"; then
  check_keys "/v1/pilot/recent" "$TMP" signups nps_responses
fi

# 6. Pricing (public tier display)
if check_200 "/v1/pricing/vn" "$GATEWAY/v1/pricing/vn" "$TMP"; then
  if jq -e 'type == "object"' "$TMP" >/dev/null; then
    pass "/v1/pricing/vn — JSON object"
  else
    fail "/v1/pricing/vn — not a JSON object"
  fi
fi

# 7. Admin gate enforcement — /convert without token MUST 401 or 503
http_code=$(curl -sS -o /dev/null -w "%{http_code}" --max-time "$TIMEOUT" \
  -X POST -H "Content-Type: application/json" \
  -d '{"user_id":"opc_smoke_test","tier":"x","monthly_vnd":1}' \
  "$GATEWAY/v1/pilot/convert" 2>/dev/null) || http_code="curl_error"
case "$http_code" in
  401|503)
    pass "/v1/pilot/convert auth gate — HTTP $http_code (expected, no token)"
    ;;
  *)
    fail "/v1/pilot/convert auth gate — HTTP $http_code (expected 401 or 503)"
    ;;
esac

# --- Summary ---
hr
if [ "$FAILS" -eq 0 ]; then
  echo "✅ All $CHECKS checks passed."
  exit 0
else
  echo "❌ $FAILS/$CHECKS checks FAILED."
  exit 1
fi
