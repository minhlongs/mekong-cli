#!/bin/bash
# GTM INTEGRATION TEST — Binh Pháp VC Studio
# Run: bash scripts/gtm-integration-test.sh
# Requires: mekong-engine running locally (npx wrangler dev --local)
set -uo pipefail

BASE="http://localhost:8787"
PASS=0 FAIL=0
RED='\033[31m' GREEN='\033[32m' NC='\033[0m'

check() {
  local label=$1 expected=$2 actual=$3
  if echo "$actual" | grep -qE "$expected"; then
    echo -e "  ${GREEN}✅${NC} $label"
    PASS=$((PASS + 1))
  else
    echo -e "  ${RED}❌${NC} $label (expected: $expected, got: $actual)"
    FAIL=$((FAIL + 1))
  fi
}

echo "═══════════════════════════════════════════════"
echo "   BINH PHÁP VC STUDIO — GTM Integration Test"
echo "═══════════════════════════════════════════════"
echo ""

# 1. Health
echo "--- Health Check ---"
HEALTH=$(curl -s $BASE/health)
check "API healthy" '"status":"ok"' "$HEALTH"

# 2. Create tenant
echo "--- Tenant Creation ---"
TENANT=$(curl -s -X POST $BASE/billing/tenants -H "Content-Type: application/json" -d '{"name":"GTM Test Studio"}')
API_KEY=$(echo $TENANT | jq -r .api_key 2>/dev/null)
check "Tenant created" "mk_" "$API_KEY"

# 3. Onboarding
echo "--- Onboarding Flow ---"
ON1=$(curl -s -X POST "$BASE/v1/onboard/profile" -H "Authorization: Bearer $API_KEY" -H "Content-Type: application/json" \
  -d '{"business_name":"Cafe Binh Phap","industry":"cafe","address":"123 Nguyen Hue"}')
check "Onboard step 1" '"step":1' "$ON1"

# 4. Governance: Register stakeholders
echo "--- Governance: Stakeholders ---"
S_COMMUNITY=$(curl -s -X POST "$BASE/v1/governance/stakeholders" -H "Authorization: Bearer $API_KEY" -H "Content-Type: application/json" \
  -d '{"display_name":"Nguyen Van A","role":"community"}')
check "Community registered (level 6)" '"governance_level":6' "$S_COMMUNITY"

S_OWNER=$(curl -s -X POST "$BASE/v1/governance/stakeholders" -H "Authorization: Bearer $API_KEY" -H "Content-Type: application/json" \
  -d '{"display_name":"Lam (Owner)","role":"owner"}')
check "Owner registered (level 1)" '"governance_level":1' "$S_OWNER"

COMMUNITY_ID=$(echo $S_COMMUNITY | jq -r .id)
OWNER_ID=$(echo $S_OWNER | jq -r .id)

# 5. Governance: Create proposal
echo "--- Governance: Proposals ---"
PROP=$(curl -s -X POST "$BASE/v1/governance/proposals" -H "Authorization: Bearer $API_KEY" -H "Content-Type: application/json" \
  -d "{\"author_id\":\"$COMMUNITY_ID\",\"title\":\"Add Zalo Pay integration\",\"body\":\"Community needs Zalo Pay for payments\"}")
check "Proposal created" '"proposal_type":"feature"' "$PROP"
PROP_ID=$(echo $PROP | jq -r .id)

# 6. Governance: Quadratic Vote (9 credits → √9 = 3 votes)
echo "--- Governance: Quadratic Voting ---"
VOTE=$(curl -s -X POST "$BASE/v1/governance/vote" -H "Authorization: Bearer $API_KEY" -H "Content-Type: application/json" \
  -d "{\"proposal_id\":\"$PROP_ID\",\"stakeholder_id\":\"$COMMUNITY_ID\",\"voice_credits\":9,\"direction\":\"for\"}")
check "QV: 9 credits → 3 votes" '"votes_cast":"3.00"' "$VOTE"

# 7. Reputation
echo "--- Reputation ---"
REP=$(curl -s -X POST "$BASE/v1/governance/reputation" -H "Authorization: Bearer $API_KEY" -H "Content-Type: application/json" \
  -d "{\"stakeholder_id\":\"$COMMUNITY_ID\",\"dimension\":\"governance\",\"points\":10,\"reason\":\"First vote cast\"}")
check "Reputation added" '"added":10' "$REP"

# 8. Ngũ Sự Score
echo "--- Ngu Su ---"
NGUSU=$(curl -s -X POST "$BASE/v1/governance/ngu-su" -H "Authorization: Bearer $API_KEY" -H "Content-Type: application/json" \
  -d '{"entity_name":"Sophia AI Video","dao":4.2,"thien":3.5,"dia":3.8,"tuong":4.0,"phap":3.2}')
check "Ngu Su scored" '"terrain"' "$NGUSU"

# 9. Ledger: Topup
echo "--- Ledger ---"
TOPUP=$(curl -s -X POST "$BASE/v1/ledger/topup" -H "Authorization: Bearer $API_KEY" -H "Content-Type: application/json" \
  -d '{"account_code":"credits:customer:001","amount":100}')
check "Ledger topup 100" '"credited":100' "$TOPUP"

# 10. Ledger: Transfer (double-entry)
XFER=$(curl -s -X POST "$BASE/v1/ledger/transfer" -H "Authorization: Bearer $API_KEY" -H "Content-Type: application/json" \
  -d '{"from_code":"credits:customer:001","to_code":"revenue:platform","amount":25,"description":"AI task fee"}')
check "Ledger transfer balanced" '"amount":25' "$XFER"

# 11. Ledger: Balance check
BAL=$(curl -s "$BASE/v1/ledger/balance?code=credits:customer:001" -H "Authorization: Bearer $API_KEY")
BALANCE=$(echo $BAL | jq -r '.accounts[0].balance')
check "Balance = 75 after topup 100 - transfer 25" "75" "$BALANCE"

# 12. Treasury
echo "--- Treasury ---"
TRES=$(curl -s "$BASE/v1/governance/treasury" -H "Authorization: Bearer $API_KEY")
check "Treasury exists" '"balance"' "$TRES"

# 13. Reports still work
echo "--- Reports (existing) ---"
OVERVIEW=$(curl -s "$BASE/v1/reports/overview" -H "Authorization: Bearer $API_KEY")
check "Reports overview" '"today_messages"' "$OVERVIEW"

# 14. VN Pricing still works
echo "--- Payment (existing) ---"
PRICING=$(curl -s "$BASE/payment/pricing-vn")
check "VN pricing" '"Starter"' "$PRICING"

echo ""
echo "═══════════════════════════════════════════════"
echo "   RESULTS: $PASS passed, $FAIL failed"
echo "═══════════════════════════════════════════════"

if [ "$FAIL" -eq 0 ]; then
  echo -e "${GREEN}ALL TESTS PASSED — Ready for GTM!${NC}"
  exit 0
else
  echo -e "${RED}$FAIL tests failed — fix before GTM${NC}"
  exit 1
fi
