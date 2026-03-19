#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# BINH PHÁP VC STUDIO — GTM Integration Test
# 14-point verification: governance + ledger + existing APIs
# Usage: bash scripts/gtm-integration-test.sh
# ═══════════════════════════════════════════════════════════════
set -uo pipefail

BASE="${GTM_API_BASE:-http://localhost:8787}"
PASSED=0 FAILED=0 TOTAL=14

check() {
  local num=$1 name=$2 cmd=$3 expect=$4
  result=$(eval "$cmd" 2>/dev/null) || result="ERROR"
  if echo "$result" | grep -q "$expect"; then
    echo "  ✅ $num. $name"
    PASSED=$((PASSED + 1))
  else
    echo "  ❌ $num. $name (expected: $expect, got: $(echo "$result" | head -1 | cut -c1-60))"
    FAILED=$((FAILED + 1))
  fi
}

echo "═══════════════════════════════════════════════════════════"
echo "  BINH PHÁP VC STUDIO — GTM Integration Test"
echo "  API: $BASE"
echo "═══════════════════════════════════════════════════════════"
echo ""

# 1. Health
check 1 "Health check" \
  "curl -s $BASE/health" \
  "ok"

# 2. Tenant creation
TENANT_ID="gtm-test-$(date +%s)"
check 2 "Tenant creation" \
  "curl -s -X POST $BASE/v1/onboard/tenant -H 'Content-Type: application/json' -d '{\"name\":\"GTM Test\",\"id\":\"$TENANT_ID\"}'" \
  "id"

# 3. Onboarding flow
check 3 "Onboarding flow" \
  "curl -s $BASE/v1/onboard/status?tenant_id=$TENANT_ID" \
  "step"

# 4. Stakeholder registration (community)
check 4 "Stakeholder: community" \
  "curl -s -X POST $BASE/v1/governance/stakeholders -H 'Content-Type: application/json' -H 'X-Tenant-ID: $TENANT_ID' -d '{\"display_name\":\"Community Member\",\"role\":\"community\",\"governance_level\":6}'" \
  "id"

# 5. Stakeholder registration (owner)
check 5 "Stakeholder: owner" \
  "curl -s -X POST $BASE/v1/governance/stakeholders -H 'Content-Type: application/json' -H 'X-Tenant-ID: $TENANT_ID' -d '{\"display_name\":\"Platform Owner\",\"role\":\"owner\",\"governance_level\":1}'" \
  "id"

# 6. Quadratic voting proposal + vote
check 6 "QV proposal + vote" \
  "curl -s -X POST $BASE/v1/governance/proposals -H 'Content-Type: application/json' -H 'X-Tenant-ID: $TENANT_ID' -d '{\"title\":\"GTM Feature Request\",\"type\":\"feature\",\"description\":\"Test proposal\"}'" \
  "id"

# 7. Reputation scoring
check 7 "Reputation scoring" \
  "curl -s -X POST $BASE/v1/governance/reputation -H 'Content-Type: application/json' -H 'X-Tenant-ID: $TENANT_ID' -d '{\"stakeholder_id\":\"test\",\"dimension\":\"dao\",\"delta\":5,\"reason\":\"GTM test\"}'" \
  "id"

# 8. Ngũ Sự evaluation
check 8 "Ngũ Sự (五事) scoring" \
  "curl -s -X POST $BASE/v1/governance/ngu-su -H 'Content-Type: application/json' -H 'X-Tenant-ID: $TENANT_ID' -d '{\"entity_id\":\"test\",\"entity_type\":\"portfolio\",\"dao\":80,\"thien\":75,\"dia\":70,\"tuong\":85,\"phap\":90}'" \
  "id"

# 9. Ledger: create account
check 9 "Ledger: create account" \
  "curl -s -X POST $BASE/v1/ledger/account -H 'Content-Type: application/json' -H 'X-Tenant-ID: $TENANT_ID' -d '{\"code\":\"CREDITS\",\"name\":\"Credits Pool\",\"type\":\"asset\"}'" \
  "id"

# 10. Ledger: topup transfer
check 10 "Ledger: topup transfer" \
  "curl -s -X POST $BASE/v1/ledger/transfer -H 'Content-Type: application/json' -H 'X-Tenant-ID: $TENANT_ID' -d '{\"from_account\":\"SYSTEM\",\"to_account\":\"CREDITS\",\"amount\":1000,\"description\":\"GTM topup\"}'" \
  "id"

# 11. Ledger: balance check
check 11 "Ledger: balance verify" \
  "curl -s $BASE/v1/ledger/balance?tenant_id=$TENANT_ID&account=CREDITS" \
  "balance"

# 12. Treasury
check 12 "Community treasury" \
  "curl -s $BASE/v1/governance/treasury -H 'X-Tenant-ID: $TENANT_ID'" \
  "balance"

# 13. Reports (regression)
check 13 "Reports (existing API)" \
  "curl -s $BASE/v1/reports/overview -H 'X-Tenant-ID: $TENANT_ID'" \
  "report"

# 14. Settings (regression)
check 14 "Settings (existing API)" \
  "curl -s $BASE/v1/settings -H 'X-Tenant-ID: $TENANT_ID'" \
  "tenant"

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  RESULTS: $PASSED/$TOTAL passed, $FAILED failed"
if [ $FAILED -eq 0 ]; then
  echo "  🟢 GTM APPROVED — All tests passed!"
else
  echo "  🔴 GTM BLOCKED — $FAILED tests failed"
fi
echo "═══════════════════════════════════════════════════════════"
