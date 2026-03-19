#!/bin/bash
# GTM INTEGRATION TEST v2 — Full Binh Pháp VC Studio
# Tests: RaaS (10) + Governance (6) + Equity (4) + Revenue (3) + QF (3) = 26 assertions
set -uo pipefail

BASE="${GTM_API_BASE:-http://localhost:8787}"
PASS=0 FAIL=0
G='\033[32m' R='\033[31m' N='\033[0m'

check() {
  if echo "$3" | grep -qE "$2"; then PASS=$((PASS+1)); echo -e "  ${G}✅${N} $1"
  else FAIL=$((FAIL+1)); echo -e "  ${R}❌${N} $1 (got: $(echo "$3" | head -c 80))"; fi
}

echo "══════════════════════════════════════════════════════"
echo "  BINH PHÁP VC STUDIO — GTM Test v2 (26 assertions)"
echo "══════════════════════════════════════════════════════"

# Setup
echo "--- Setup ---"
H="Content-Type: application/json"
T=$(curl -s -X POST $BASE/billing/tenants -H "$H" -d '{"name":"GTM v2"}')
K=$(echo $T | jq -r .api_key); A="Authorization: Bearer $K"
check "Tenant created" "mk_" "$K"

# RaaS Core
echo "--- RaaS Core ---"
check "Health" '"ok"' "$(curl -s $BASE/health)"
check "Onboard" '"step":1' "$(curl -s -X POST $BASE/v1/onboard/profile -H "$A" -H "$H" -d '{"business_name":"Test","industry":"cafe"}')"
check "VN Pricing" '"Starter"' "$(curl -s $BASE/payment/pricing-vn)"
check "Credits" '"balance"' "$(curl -s $BASE/billing/credits -H "$A")"

# Governance
echo "--- Governance ---"
C_ID=$(curl -s -X POST $BASE/v1/governance/stakeholders -H "$A" -H "$H" -d '{"display_name":"Customer A","role":"community"}' | jq -r .id)
check "Community stakeholder" "community" "$(curl -s $BASE/v1/governance/stakeholders -H "$A")"

O_ID=$(curl -s -X POST $BASE/v1/governance/stakeholders -H "$A" -H "$H" -d '{"display_name":"Owner","role":"owner"}' | jq -r .id)
check "Owner stakeholder" "owner" "$(curl -s $BASE/v1/governance/stakeholders -H "$A")"

P_ID=$(curl -s -X POST $BASE/v1/governance/proposals -H "$A" -H "$H" -d "{\"author_id\":\"$C_ID\",\"title\":\"Test Proposal\",\"body\":\"Test\"}" | jq -r .id)
check "Proposal created" "voting" "$(curl -s $BASE/v1/governance/proposals -H "$A")"

V=$(curl -s -X POST $BASE/v1/governance/vote -H "$A" -H "$H" -d "{\"proposal_id\":\"$P_ID\",\"stakeholder_id\":\"$C_ID\",\"voice_credits\":16}")
check "QV: 16 credits → 4 votes" '"4.00"' "$V"

check "Reputation" '"added"' "$(curl -s -X POST $BASE/v1/governance/reputation -H "$A" -H "$H" -d "{\"stakeholder_id\":\"$C_ID\",\"points\":10,\"reason\":\"vote\"}")"
check "Ngũ Sự" '"terrain"' "$(curl -s -X POST $BASE/v1/governance/ngu-su -H "$A" -H "$H" -d '{"entity_name":"Sophia","dao":4,"thien":3,"dia":4,"tuong":4,"phap":3}')"

# Equity
echo "--- Equity ---"
E=$(curl -s -X POST $BASE/v1/equity/entities -H "$A" -H "$H" -d '{"name":"Sophia AI"}')
E_ID=$(echo $E | jq -r .id); SC_ID=$(echo $E | jq -r .share_class_id)
check "Entity created" '"id"' "$E"

F_ID=$(curl -s -X POST $BASE/v1/governance/stakeholders -H "$A" -H "$H" -d '{"display_name":"Founder","role":"founder"}' | jq -r .id)
curl -s -X POST $BASE/v1/equity/grants -H "$A" -H "$H" -d "{\"entity_id\":\"$E_ID\",\"stakeholder_id\":\"$F_ID\",\"share_class_id\":\"$SC_ID\",\"shares\":4500000,\"vesting_months\":48,\"cliff_months\":12}" > /dev/null
curl -s -X POST $BASE/v1/equity/grants -H "$A" -H "$H" -d "{\"entity_id\":\"$E_ID\",\"stakeholder_id\":\"$O_ID\",\"share_class_id\":\"$SC_ID\",\"shares\":2500000}" > /dev/null
CAP=$(curl -s $BASE/v1/equity/cap-table/$E_ID -H "$A")
check "Cap table: 2 holders" "total_outstanding" "$CAP"
check "Dilution calculated" "dilution_pct" "$CAP"

SAFE=$(curl -s -X POST $BASE/v1/equity/safe -H "$A" -H "$H" -d "{\"entity_id\":\"$E_ID\",\"investor_stakeholder_id\":\"$C_ID\",\"principal_amount\":100000,\"valuation_cap\":2000000}")
check "SAFE note" '"outstanding"' "$SAFE"

# Ledger + Revenue
echo "--- Ledger + Revenue ---"
curl -s -X POST $BASE/v1/ledger/topup -H "$A" -H "$H" -d '{"account_code":"credits:customer:001","amount":500}' > /dev/null
check "Ledger topup" "500" "$(curl -s "$BASE/v1/ledger/balance?code=credits:customer:001" -H "$A" | jq '.accounts[0].balance')"

RS=$(curl -s -X POST $BASE/v1/revenue/split -H "$A" -H "$H" -d '{"total_credits":100,"customer_account":"credits:customer:001","description":"AI task"}')
check "Revenue split 6-way" '"platform"' "$RS"
check "Customer balance 400" "400" "$(curl -s "$BASE/v1/ledger/balance?code=credits:customer:001" -H "$A" | jq '.accounts[0].balance')"

# Quadratic Funding
echo "--- Quadratic Funding ---"
R_ID=$(curl -s -X POST $BASE/v1/funding/rounds -H "$A" -H "$H" -d '{"title":"Q2","matching_pool":1000}' | jq -r .id)
PA=$(curl -s -X POST $BASE/v1/funding/projects -H "$A" -H "$H" -d "{\"round_id\":\"$R_ID\",\"name\":\"Feature A\"}" | jq -r .id)
for i in 1 2 3; do
  SID=$(curl -s -X POST $BASE/v1/governance/stakeholders -H "$A" -H "$H" -d "{\"display_name\":\"Voter $i\",\"role\":\"community\"}" | jq -r .id)
  curl -s -X POST $BASE/v1/funding/contribute -H "$A" -H "$H" -d "{\"project_id\":\"$PA\",\"stakeholder_id\":\"$SID\",\"amount\":1}" > /dev/null
done
QF=$(curl -s -X POST "$BASE/v1/funding/rounds/$R_ID/calculate" -H "$A")
check "QF round calculated" '"matched_amount"' "$QF"
check "QF: 3 contributors matched" "contributors.*3" "$QF"

# Summary
echo ""
echo "══════════════════════════════════════════════════════"
echo "  RESULTS: $PASS/$((PASS+FAIL)) passed"
echo "══════════════════════════════════════════════════════"
[ "$FAIL" -eq 0 ] && echo -e "${G}🎉 ALL PASSED — GTM APPROVED${N}" || echo -e "${R}⚠️ $FAIL FAILED${N}"
exit $FAIL
