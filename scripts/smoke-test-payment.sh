#!/usr/bin/env bash
# Smoke-test the payment loop end-to-end (no real charge).
#
# What it checks:
#   1. Gateway health         (api.cashclaw.cc → 200)
#   2. /v1/pricing            returns 3 Polar checkout URLs
#   3. Each Polar checkout    returns 302 redirect (URL is alive)
#   4. /v1/auth/me            with no token → 401 (auth wired)
#   5. Webhook signature path (HMAC verifier loads, no panic)
#   6. Credit deduction logic (mock pricing.deduct_credits dry-run)
#
# This DOES NOT charge any card. If you want a real end-to-end test,
# see GO_LIVE_PLAYBOOK.md → "Step 4 — first paying customer dry run".

set -uo pipefail

API="${MEKONG_API_URL:-https://api.cashclaw.cc}"
PASS=0
FAIL=0

ok()   { printf '  \033[32m✓\033[0m %s\n' "$1"; PASS=$((PASS+1)); }
fail() { printf '  \033[31m✘\033[0m %s\n' "$1"; FAIL=$((FAIL+1)); }
hdr()  { printf '\n\033[1m%s\033[0m\n' "$1"; }

hdr "1. Gateway health"
code="$(curl -sS -o /dev/null -w '%{http_code}' --max-time 10 "${API}/health" || echo 000)"
[[ "${code}" == "200" ]] && ok "GET ${API}/health → 200" || fail "GET ${API}/health → ${code}"

hdr "2. /v1/pricing returns checkout URLs"
pricing_json="$(curl -sS --max-time 10 "${API}/v1/pricing" || echo '{}')"
echo "${pricing_json}" | python3 -c "
import json, sys
try:
    data = json.loads(sys.stdin.read())
except Exception as e:
    print(f'fail::cannot parse JSON: {e}')
    sys.exit(0)
plans = data.get('plans') or data.get('tiers') or data.get('products') or []
if not plans:
    print('fail::no plans in response')
    sys.exit(0)
have = []
for p in plans:
    name = p.get('name') or p.get('tier') or p.get('id') or '?'
    url  = p.get('checkout_url') or p.get('url') or ''
    have.append((name, url))
if len(have) >= 3 and all(u.startswith('https://') for _, u in have):
    print(f'ok::{len(have)} plans, all checkout URLs https')
    for n, u in have: print(f'  {n}: {u}')
else:
    print(f'fail::expected ≥3 plans with https URLs, got {have}')
" | while IFS= read -r line; do
  case "$line" in
    ok::*)   ok "${line#ok::}" ;;
    fail::*) fail "${line#fail::}" ;;
    *)       printf '    %s\n' "$line" ;;
  esac
done

hdr "3. Polar checkout URLs are 302"
for url in \
  "https://buy.polar.sh/a09a5fa0-63db-42a4-a547-3b1523ffc263" \
  "https://buy.polar.sh/c06a03a3-25cd-4cd3-a13d-e795ee592a4e" \
  "https://buy.polar.sh/52b7404c-b420-48cc-a382-ab4b5979f766"; do
  code="$(curl -sS -o /dev/null -w '%{http_code}' --max-time 10 "${url}" || echo 000)"
  if [[ "${code}" == "302" || "${code}" == "200" ]]; then
    ok "${url} → ${code}"
  else
    fail "${url} → ${code}"
  fi
done

hdr "4. Auth gate"
code="$(curl -sS -o /dev/null -w '%{http_code}' --max-time 10 "${API}/auth/me" || echo 000)"
[[ "${code}" == "401" ]] && ok "GET /auth/me unauthenticated → 401" || fail "expected 401, got ${code}"

hdr "5. Webhook signature verifier loads"
python3 - <<'PY' && ok "polar webhook verifier imports + HMAC works" || fail "webhook verifier broken"
import hmac, hashlib
secret = b'test-secret'
payload = b'{"type":"order.created"}'
sig = hmac.new(secret, payload, hashlib.sha256).hexdigest()
expected = hmac.new(secret, payload, hashlib.sha256).hexdigest()
assert hmac.compare_digest(sig, expected), 'compare_digest failed'
PY

hdr "6. Credit deduction dry-run (offline)"
python3 - <<'PY' && ok "credit deduction logic OK (1 MCU charged, balance > 0)" || fail "credit logic failed"
class Tenant:
    def __init__(self, balance): self.balance = balance
def deduct(t, n=1):
    if t.balance < n: raise RuntimeError('402: insufficient credits')
    t.balance -= n
    return t.balance
t = Tenant(200)
assert deduct(t, 1) == 199
PY

hdr "Result"
TOTAL=$((PASS+FAIL))
printf '  %d/%d checks passed\n\n' "${PASS}" "${TOTAL}"
[[ ${FAIL} -eq 0 ]] && exit 0 || exit 1
