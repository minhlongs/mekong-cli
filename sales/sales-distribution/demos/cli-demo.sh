#!/bin/bash
# RaaS Live Demo Script — 5 Minute CLI Walkthrough
# Usage: ./cli-demo.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "╔══════════════════════════════════════════════════════════╗"
echo "║           Raas LIVE DEMO — 5 Minute Walkthrough          ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Step 1: Authentication
echo -e "${BLUE}STEP 1: Authentication${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Command: mekong auth:login"
echo ""
read -p "Press Enter to execute..."
echo ""
# Uncomment in production:
# mekong auth:login
echo -e "${GREEN}✓ Authenticated as: demo@agencyos.network${NC}"
echo ""
echo ""

# Step 2: Check Credits
echo -e "${BLUE}STEP 2: Check Credit Balance${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Command: mekong credits:balance"
echo ""
read -p "Press Enter to execute..."
echo ""
# Uncomment in production:
# mekong credits:balance
echo -e "${GREEN}┌─────────────────────────────────────┐${NC}"
echo -e "${GREEN}│  Tier: Pro                          │${NC}"
echo -e "${GREEN}│  Credits: 200                       │${NC}"
echo -e "${GREEN}│  Used: 47                           │${NC}"
echo -e "${GREEN}│  Remaining: 153                     │${NC}"
echo -e "${GREEN}└─────────────────────────────────────┘${NC}"
echo ""
echo ""

# Step 3: Create Mission
echo -e "${BLUE}STEP 3: Submit Mission${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Command: mekong mission:create \"Add JWT authentication with refresh tokens\""
echo ""
read -p "Press Enter to execute..."
echo ""

MISSION_ID=$(uuidgen 2>/dev/null || echo "msn_$(date +%s)")

# Uncomment in production:
# mekong mission:create "Add JWT authentication with refresh tokens"

echo -e "${GREEN}✓ Mission submitted${NC}"
echo ""
echo -e "${YELLOW}┌─────────────────────────────────────┐${NC}"
echo -e "${YELLOW}│  Mission ID: $MISSION_ID            │${NC}"
echo -e "${YELLOW}│  Description: JWT auth + refresh    │${NC}"
echo -e "${YELLOW}│  Estimated Cost: 3 credits          │${NC}"
echo -e "${YELLOW}│  Status: QUEUED                     │${NC}"
echo -e "${YELLOW}└─────────────────────────────────────┘${NC}"
echo ""
echo ""

# Step 4: Watch Execution
echo -e "${BLUE}STEP 4: Watch Agent Execution${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Command: mekong mission:status --live $MISSION_ID"
echo ""
read -p "Press Enter to execute..."
echo ""

# Simulated live progress
echo -e "${BLUE}Agent Team Execution:${NC}"
echo ""

echo -ne "${YELLOW}[1/4] Planner Agent...  ${NC}"
sleep 1
echo -e "${GREEN}✓${NC}"
echo "         Generated architecture plan (4 endpoints, JWT strategy)"

echo -ne "${YELLOW}[2/4] Coder Agent...      ${NC}"
sleep 1.5
echo -e "${GREEN}✓${NC}"
echo "         Created: auth.controller.ts, auth.service.ts, jwt.strategy.ts"
echo "         Created: auth.guard.ts, refresh-token.entity.ts"

echo -ne "${YELLOW}[3/4] Tester Agent...     ${NC}"
sleep 1
echo -e "${GREEN}✓${NC}"
echo "         Unit tests: 12/12 passing"
echo "         Integration tests: 4/4 passing"

echo -ne "${YELLOW}[4/4] Reviewer Agent...   ${NC}"
sleep 1
echo -e "${GREEN}✓${NC}"
echo "         Security audit: PASSED"
echo "         Code quality: A (98/100)"
echo "         Type checking: PASSED"

echo ""
echo -e "${GREEN}┌─────────────────────────────────────┐${NC}"
echo -e "${GREEN}│  ✅ MISSION COMPLETE                │${NC}"
echo -e "${GREEN}│  Credits Deducted: 3                │${NC}"
echo -e "${GREEN}│  Files Created: 5                   │${NC}"
echo -e "${GREEN}│  Tests Passing: 16/16               │${NC}"
echo -e "${GREEN}└─────────────────────────────────────┘${NC}"
echo ""
echo ""

# Step 5: Test Deployed API
echo -e "${BLUE}STEP 5: Test Deployed API${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Command: curl -X POST https://demo-client.vercel.app/api/auth/register \\"
echo "         -H \"Content-Type: application/json\" \\"
echo "         -d '{\"email\":\"test@example.com\",\"password\":\"secure123\"}'"
echo ""
read -p "Press Enter to execute..."
echo ""

# Uncomment in production:
# curl -X POST https://demo-client.vercel.app/api/auth/register \
#   -H "Content-Type: application/json" \
#   -d '{"email":"test@example.com","password":"secure123"}'

echo -e "${GREEN}Response:${NC}"
echo "{"
echo "  \"success\": true,"
echo "  \"user\": {"
echo "    \"id\": \"usr_abc123\","
echo "    \"email\": \"test@example.com\","
echo "    \"createdAt\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\""
echo "  },"
echo "  \"accessToken\": \"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...\""
echo "}"
echo ""
echo ""

# Step 6: Show Credit History
echo -e "${BLUE}STEP 6: Credit History${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Command: mekong credits:history --limit 5"
echo ""
read -p "Press Enter to execute..."
echo ""

# Uncomment in production:
# mekong credits:history --limit 5

echo -e "${GREEN}┌────────────────────────────────────────────────┐${NC}"
echo -e "${GREEN}│  DATE       │ DESCRIPTION           │ CREDITS  │${NC}"
echo -e "${GREEN}│  ─────────────────────────────────────────────  │${NC}"
echo -e "${GREEN}│  Today      │ JWT authentication    │ -3       │${NC}"
echo -e "${GREEN}│  Yesterday  │ User CRUD endpoints   │ -3       │${NC}"
echo -e "${GREEN}│  Yesterday  │ Password reset flow   │ -1       │${NC}"
echo -e "${GREEN}│  Mar 17     │ Dashboard component   │ -1       │${NC}"
echo -e "${GREEN}│  Mar 16     │ API rate limiting     │ -3       │${NC}"
echo -e "${GREEN}└────────────────────────────────────────────────┘${NC}"
echo ""
echo ""

# Summary
echo "╔══════════════════════════════════════════════════════════╗"
echo "║                      DEMO COMPLETE                       ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║                                                          ║"
echo "║  In 5 minutes, we:                                       ║"
echo "║  ✓ Submitted a mission                                   ║"
echo "║  ✓ Watched 4 AI agents execute autonomously              ║"
echo "║  ✓ Deployed production-ready authentication              ║"
echo "║  ✓ Tested the live API endpoint                          ║"
echo "║  ✓ Tracked credit usage                                  ║"
echo "║                                                          ║"
echo "║  What took 4-6 hours → Done in 5 minutes                 ║"
echo "║                                                          ║"
echo "║  Questions?                                              ║"
echo "║  📧 sales@agencyos.network                               ║"
echo "║  🌐 agencyos.network/demo                                ║"
echo "║                                                          ║"
echo "╚══════════════════════════════════════════════════════════╝"
