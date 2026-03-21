#!/usr/bin/env bash
# raas-bridge.sh — CLI bridge to RaaS Gateway API
# Usage: mekong-raas <command> [args]

set -euo pipefail

GATEWAY_URL="${MEKONG_GATEWAY_URL:-https://raas-gateway.agencyos-openclaw.workers.dev}"
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

cmd_help() {
  echo "mekong-raas — CLI bridge to RaaS Gateway"
  echo ""
  echo "Commands:"
  echo "  signup       Create free account (10 MCU)"
  echo "  login        Set API token"
  echo "  credits      Check credit balance"
  echo "  submit       Submit a mission"
  echo "  missions     List your missions"
  echo "  profile      View tenant profile"
  echo "  apikey       Generate API key"
  echo "  pricing      View pricing tiers"
  echo ""
  echo "Usage:"
  echo "  mekong-raas signup"
  echo "  mekong-raas submit \"Build a REST API\" standard"
  echo "  mekong-raas credits"
}

# Route command
case "${1:-help}" in
  signup)   cmd_signup ;;
  login)    cmd_login ;;
  credits)  cmd_credits ;;
  submit)   shift; cmd_submit "$@" ;;
  missions) cmd_missions ;;
  profile)  cmd_profile ;;
  apikey)   shift; cmd_apikey "${1:-CLI Key}" ;;
  pricing)  cmd_pricing ;;
  help|*)   cmd_help ;;
esac
