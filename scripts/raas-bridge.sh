#!/usr/bin/env bash
# raas-bridge.sh — CLI bridge to RaaS Gateway API
# Usage: mekong-raas <command> [args]

set -euo pipefail

GATEWAY_URL="${MEKONG_GATEWAY_URL:-https://raas.agencyos.network}"
CREDS_FILE="${HOME}/.mekong/credentials"

# Color helpers
cyan() { printf '\033[36m%s\033[0m' "$1"; }
red() { printf '\033[31m%s\033[0m' "$1"; }
green() { printf '\033[32m%s\033[0m' "$1"; }

# Load token from credentials file
load_token() {
  if [[ ! -f "$CREDS_FILE" ]]; then
    echo "$(red 'No credentials found.') Run: mekong-raas signup" >&2
    exit 1
  fi
  MEKONG_TOKEN=$(grep '^token=' "$CREDS_FILE" | cut -d= -f2-)
  if [[ -z "${MEKONG_TOKEN:-}" ]]; then
    echo "$(red 'Invalid credentials.') Run: mekong-raas signup" >&2
    exit 1
  fi
}

# Auth header
auth_header() { echo "Authorization: Bearer ${MEKONG_TOKEN}"; }

# API call helper
api() {
  local method="$1" path="$2"
  shift 2
  curl -s -X "$method" -H "$(auth_header)" -H "Content-Type: application/json" "$@" "${GATEWAY_URL}${path}"
}

# Commands
cmd_signup() {
  local name email
  read -rp "Your name: " name
  read -rp "Your email: " email

  local result
  result=$(curl -s -X POST -H "Content-Type: application/json" \
    -d "{\"name\":\"${name}\",\"email\":\"${email}\"}" \
    "${GATEWAY_URL}/v1/tenants/signup")

  local token
  token=$(echo "$result" | python3 -c "import sys,json; print(json.load(sys.stdin).get('token',''))" 2>/dev/null)

  if [[ -n "$token" && "$token" != "None" ]]; then
    mkdir -p "$(dirname "$CREDS_FILE")"
    echo "token=${token}" > "$CREDS_FILE"
    chmod 600 "$CREDS_FILE"
    echo "$(green 'Account created!') 10 free credits."
    echo "Token saved to ${CREDS_FILE}"
  else
    local err
    err=$(echo "$result" | python3 -c "import sys,json; print(json.load(sys.stdin).get('error','Unknown error'))" 2>/dev/null)
    echo "$(red 'Signup failed:') ${err}"
    exit 1
  fi
}

cmd_login() {
  local token
  read -rsp "Paste your API token: " token
  echo
  mkdir -p "$(dirname "$CREDS_FILE")"
  echo "token=${token}" > "$CREDS_FILE"
  chmod 600 "$CREDS_FILE"
  echo "$(green 'Logged in.') Token saved."
}

cmd_credits() {
  load_token
  api GET /credits | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(f'Balance: {d.get(\"balance\",0)} MCU')
print(f'Earned:  {d.get(\"totalEarned\",0)} | Spent: {d.get(\"totalSpent\",0)}')
"
}

cmd_submit() {
  load_token
  local goal="${1:-}"
  local complexity="${2:-standard}"

  if [[ -z "$goal" ]]; then
    read -rp "Goal: " goal
  fi

  api POST /v1/missions -d "{\"goal\":\"${goal}\",\"complexity\":\"${complexity}\"}" | python3 -c "
import sys,json
d=json.load(sys.stdin)
if 'error' in d:
    print(f'Error: {d[\"error\"]}')
else:
    print(f'Mission: {d.get(\"id\",\"?\")[:12]}...')
    print(f'Status:  {d.get(\"status\")} | Cost: {d.get(\"creditsCost\")} MCU')
"
}

cmd_missions() {
  load_token
  api GET /v1/missions | python3 -c "
import sys,json
d=json.load(sys.stdin)
ms=d.get('missions',[])
print(f'Total: {d.get(\"total\",0)} missions\n')
for m in ms[:10]:
    print(f'{m[\"id\"][:8]}  {m[\"status\"]:12s}  {m[\"creditsCost\"]}MCU  {m[\"goal\"][:50]}')
"
}

cmd_result() {
  load_token
  local mission_id="${1:-}"
  if [[ -z "$mission_id" ]]; then
    echo "Usage: mekong-raas result <mission-id>" >&2
    exit 1
  fi
  api GET "/v1/missions/${mission_id}" | python3 -c "
import sys,json
d=json.load(sys.stdin)
if 'error' in d:
    print(f'Error: {d[\"error\"]}')
else:
    print(f'Mission: {d[\"id\"]}')
    print(f'Status:  {d[\"status\"]}')
    print(f'Goal:    {d[\"goal\"]}')
    result = d.get('result')
    if result:
        print(f'\n--- Result ---\n{result}')
    elif d['status'] == 'queued':
        print('\nMission is queued — check back shortly.')
    elif d['status'] == 'failed':
        print(f'\nError: {d.get(\"errorMessage\",\"Unknown\")}')
"
}

cmd_profile() {
  load_token
  api GET /v1/tenants/profile | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(f'Name:    {d.get(\"name\")}')
print(f'Email:   {d.get(\"email\")}')
print(f'Tier:    {d.get(\"tier\")}')
print(f'Balance: {d.get(\"balance\")} MCU')
"
}

cmd_apikey() {
  load_token
  local name="${1:-CLI Key}"
  api POST /v1/tenants/api-keys -d "{\"name\":\"${name}\"}" | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(f'API Key: {d.get(\"apiKey\")}')
print(f'Key ID:  {d.get(\"keyId\")}')
print('Save this key — it cannot be retrieved again.')
"
}

cmd_upgrade() {
  load_token
  api GET /v1/tenants/upgrade | python3 -c "
import sys,json
d=json.load(sys.stdin)
c=d.get('currentTier',{})
print(f'Current: {c.get(\"name\")} (\${c.get(\"price\",0)}/mo)')
print()
for u in d.get('upgrades',[]):
    print(f'  {u[\"name\"]:10s} \${u[\"price\"]:>5}/mo  {u[\"credits\"]} MCU  {u.get(\"dailyLimit\",-1)} missions/day')
    print(f'            {u.get(\"checkoutUrl\",\"\")}')
"
}

cmd_templates() {
  curl -s "${GATEWAY_URL}/v1/missions/templates" | python3 -c "
import sys,json
for t in json.load(sys.stdin):
    print(f'  [{t[\"complexity\"]:8s}] {t[\"id\"]:20s} {t[\"goal\"][:60]}')
"
}

cmd_redeem() {
  load_token
  local code="${1:-}"
  if [[ -z "$code" ]]; then
    echo "Usage: mekong-raas redeem <code>" >&2
    exit 1
  fi
  api POST /v1/credits/redeem -d "{\"code\":\"${code}\"}" | python3 -c "
import sys,json
d=json.load(sys.stdin)
if 'error' in d:
    print(f'Error: {d[\"error\"]}')
else:
    print(f'Redeemed: {d.get(\"credits\",0)} MCU')
    print(f'Balance:  {d.get(\"balance\",0)} MCU')
"
}

cmd_feedback() {
  load_token
  local type="${1:-}"
  local message="${2:-}"
  if [[ -z "$type" || -z "$message" ]]; then
    echo "Usage: mekong-raas feedback <type> <message>" >&2
    exit 1
  fi
  api POST /v1/credits/feedback -d "{\"type\":\"${type}\",\"message\":\"${message}\"}" | python3 -c "
import sys,json
d=json.load(sys.stdin)
if 'error' in d:
    print(f'Error: {d[\"error\"]}')
else:
    print(f'Feedback submitted. {d.get(\"message\",\"Thank you!\")}')
"
}

cmd_leaderboard() {
  curl -s "${GATEWAY_URL}/marketplace/leaderboard" | python3 -c "
import sys,json
d=json.load(sys.stdin)
entries=d.get('leaderboard',d) if isinstance(d,dict) else d
print('Rank  Referrals  Credits  Name')
print('─' * 40)
for i,e in enumerate(entries[:10],1):
    print(f'  {i:2d}  {e.get(\"referrals\",0):>9}  {e.get(\"credits\",0):>7}  {e.get(\"name\",\"?\")}')
"
}

cmd_reviews() {
  local mission_id="${1:-}"
  if [[ -z "$mission_id" ]]; then
    echo "Usage: mekong-raas reviews <mission-id>" >&2
    exit 1
  fi
  curl -s "${GATEWAY_URL}/marketplace/${mission_id}/reviews" | python3 -c "
import sys,json
d=json.load(sys.stdin)
reviews=d.get('reviews',[]) if isinstance(d,dict) else d
print(f'Reviews: {len(reviews)}\n')
for r in reviews:
    print(f'  [{r.get(\"rating\",\"?\")}/5] {r.get(\"comment\",\"\")[:70]}')
    print(f'         — {r.get(\"author\",\"anonymous\")}')
"
}

cmd_health_deep() {
  curl -s "${GATEWAY_URL}/health/deep" | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(f'Status: {d.get(\"status\")}')
for svc,info in d.get('services',{}).items():
    status=info.get('status') if isinstance(info,dict) else info
    print(f'  {svc:20s} {status}')
"
}

cmd_trial_extend() {
  load_token
  api POST /v1/tenants/trial-extend | python3 -c "
import sys,json
d=json.load(sys.stdin)
if 'error' in d:
    print(f'Error: {d[\"error\"]}')
else:
    print(f'Trial extended! Bonus: {d.get(\"bonusCredits\",10)} MCU')
    print(f'Balance: {d.get(\"balance\",0)} MCU')
"
}

cmd_settings() {
  load_token
  local webhook_url="${1:-}"
  if [[ -z "$webhook_url" ]]; then
    echo "Usage: mekong-raas settings <webhook-url>" >&2
    exit 1
  fi
  api PUT /v1/tenants/settings -d "{\"webhook_url\":\"${webhook_url}\"}" | python3 -c "
import sys,json
d=json.load(sys.stdin)
if 'error' in d:
    print(f'Error: {d[\"error\"]}')
else:
    print(f'Settings updated.')
    print(f'Webhook: {d.get(\"webhook_url\",\"?\")}')
"
}

cmd_referral() {
  load_token
  api GET /v1/tenants/referrals | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(f'Code:     {d.get(\"referralCode\")}')
print(f'Link:     {d.get(\"referralLink\")}')
print(f'Referred: {d.get(\"totalReferred\")} users')
print(f'Earned:   {d.get(\"creditsEarned\")} MCU')
"
}

cmd_pricing() {
  curl -s "${GATEWAY_URL}/billing/pricing" | python3 -c "
import sys,json
d=json.load(sys.stdin)
print('Tier         Price    Credits')
print('─' * 35)
for t in d.get('tiers',[]):
    print(f'{t[\"name\"]:12s} \${t[\"price\"]:>5}/mo  {t[\"credits\"]} MCU')
"
}

cmd_marketplace() {
  local search="${1:-}"
  local url="${GATEWAY_URL}/marketplace?limit=10"
  [[ -n "$search" ]] && url="${url}&q=${search}"
  curl -s "$url" | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(f'Marketplace: {d.get(\"total\",0)} public missions\n')
for m in d.get('missions',[]):
    print(f'  {m[\"id\"][:8]}  [{m[\"complexity\"]:8s}]  {m[\"goal\"][:60]}')
    if m.get('author'): print(f'            by {m[\"author\"]}')
"
}

cmd_alerts() {
  load_token
  api GET /v1/alerts | python3 -c "
import sys,json
d=json.load(sys.stdin)
alerts=d.get('alerts',[])
if not alerts: print('No unread alerts.'); exit()
for a in alerts:
    print(f'  [{a[\"type\"]:18s}] {a[\"message\"][:70]}')
"
}

cmd_buy() {
  load_token
  local pack="${1:-credits-10}"
  api POST /billing/stripe/checkout -d "{\"packId\":\"${pack}\"}" | python3 -c "
import sys,json
d=json.load(sys.stdin)
if 'checkoutUrl' in d:
    print(f'Checkout URL: {d[\"checkoutUrl\"]}')
    print('Open this URL in your browser to complete purchase.')
else:
    print(f'Error: {d.get(\"error\",\"Unknown\")}')
"
}

cmd_packs() {
  curl -s "${GATEWAY_URL}/billing/stripe/packs" | python3 -c "
import sys,json
d=json.load(sys.stdin)
print('Credit Packs:')
print('─' * 40)
for p in d.get('packs',[]):
    print(f'  {p[\"id\"]:15s} {p[\"credits\"]:>5} MCU  \${p[\"priceInCents\"]/100:.0f}')
"
}

cmd_help() {
  echo "mekong-raas — CLI bridge to RaaS Gateway"
  echo ""
  echo "Commands:"
  echo "  signup          Create free account (10 MCU)"
  echo "  login           Set API token"
  echo "  credits         Check credit balance"
  echo "  submit          Submit a mission"
  echo "  result          Get mission result"
  echo "  missions        List your missions"
  echo "  profile         View tenant profile"
  echo "  apikey          Generate API key"
  echo "  upgrade         Compare tier upgrades"
  echo "  templates       List mission templates"
  echo "  referral        Referral stats + link"
  echo "  pricing         View pricing tiers"
  echo "  marketplace     Browse public missions"
  echo "  alerts          View unread alerts"
  echo "  buy             Buy credit pack"
  echo "  packs           List credit packs"
  echo "  redeem          Redeem a coupon code"
  echo "  feedback        Submit feedback"
  echo "  leaderboard     Referral leaderboard"
  echo "  reviews         Reviews for a mission"
  echo "  health-deep     Deep system health check"
  echo "  trial-extend    Get 10 bonus credits"
  echo "  settings        Update tenant settings (webhook URL)"
  echo ""
  echo "Usage:"
  echo "  mekong-raas signup"
  echo "  mekong-raas submit \"Build a REST API\" standard"
  echo "  mekong-raas credits"
  echo "  mekong-raas redeem COUPON123"
  echo "  mekong-raas feedback bug \"Mission got stuck\""
  echo "  mekong-raas reviews <mission-id>"
  echo "  mekong-raas settings https://mysite.com/webhook"
}

# Route command
case "${1:-help}" in
  signup)   cmd_signup ;;
  login)    cmd_login ;;
  credits)  cmd_credits ;;
  submit)   shift; cmd_submit "$@" ;;
  result)   shift; cmd_result "$@" ;;
  missions) cmd_missions ;;
  profile)  cmd_profile ;;
  apikey)   shift; cmd_apikey "${1:-CLI Key}" ;;
  upgrade)  cmd_upgrade ;;
  templates) cmd_templates ;;
  referral) cmd_referral ;;
  pricing)      cmd_pricing ;;
  marketplace)  shift; cmd_marketplace "${1:-}" ;;
  alerts)       cmd_alerts ;;
  buy)          shift; cmd_buy "${1:-credits-10}" ;;
  packs)        cmd_packs ;;
  redeem)       shift; cmd_redeem "$@" ;;
  feedback)     shift; cmd_feedback "$@" ;;
  leaderboard)  cmd_leaderboard ;;
  reviews)      shift; cmd_reviews "$@" ;;
  health-deep)  cmd_health_deep ;;
  trial-extend) cmd_trial_extend ;;
  settings)     shift; cmd_settings "$@" ;;
  help|*)       cmd_help ;;
esac
