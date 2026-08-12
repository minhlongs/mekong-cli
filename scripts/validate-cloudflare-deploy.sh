#!/usr/bin/env bash
# Validate Cloudflare Workers Deployment Configuration
# Checks that all wrangler.toml files have valid configuration (no placeholders)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

echo "========================================"
echo "Cloudflare Deployment Validation"
echo "========================================"
echo ""

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ERRORS=0
WARNINGS=0

check_file() {
    local file=$1
    local pattern=$2
    local description=$3

    echo "Checking $file: $description"

    if grep -q "$pattern" "$file" 2>/dev/null; then
        echo -e "${RED}  ✗ Found placeholder:${NC} $(grep "$pattern" "$file" | head -1 | tr -d '[:space:]')"
        ((ERRORS++))
    else
        echo -e "${GREEN}  ✓ OK${NC}"
    fi
}

check_exists() {
    local file=$1
    local description=$2

    echo "Checking $description..."

    if [ -f "$file" ]; then
        echo -e "${GREEN}  ✓ Exists: $file${NC}"
    else
        echo -e "${RED}  ✗ Missing: $file${NC}"
        ((ERRORS++))
    fi
}

check_command() {
    local cmd=$1
    local description=$2

    echo "Checking $description..."
    if command -v "$cmd" &> /dev/null; then
        echo -e "${GREEN}  ✓ Available: $(command -v $cmd)${NC}"
    else
        echo -e "${YELLOW}  ⚠ Not found (optional)${NC}"
        ((WARNINGS++))
    fi
}

# Check wrangler.toml files exist
echo "========================================"
echo "File Existence Checks"
echo "========================================"
check_exists "apps/dashboard/wrangler.toml" "Dashboard wrangler.toml"
check_exists "apps/api/wrangler.toml" "API Worker wrangler.toml"
check_exists "packages/mekong-engine/wrangler.toml" "Mekong Engine wrangler.toml"
check_exists "packages/zalo-parser/wrangler.toml" "Zalo Parser wrangler.toml"

# Check for placeholders in API Worker config
echo ""
echo "========================================"
echo "API Worker Configuration"
echo "========================================"
check_file "apps/api/wrangler.toml" "replace_with_.*_id" "No placeholder IDs"
check_file "apps/api/wrangler.toml" "00000000-0000-0000-0000-000000000000" "No zero UUIDs"

# Check for valid database IDs (UUID format)
echo ""
echo "Validating UUID formats in apps/api/wrangler.toml..."
if grep -q 'database_id = "[0-9a-f-]\{36\}"' apps/api/wrangler.toml 2>/dev/null; then
    echo -e "${GREEN}  ✓ Database IDs appear valid (UUID format)${NC}"
else
    echo -e "${RED}  ✗ Database IDs missing or invalid${NC}"
    ((ERRORS++))
fi

if grep -q 'id = "[0-9a-f-]\{36\}"' apps/api/wrangler.toml 2>/dev/null; then
    echo -e "${GREEN}  ✓ KV IDs appear valid (UUID format)${NC}"
else
    echo -e "${RED}  ✗ KV IDs missing or invalid${NC}"
    ((ERRORS++))
fi

# Check Zalo Parser config
echo ""
echo "========================================"
echo "Zalo Parser Configuration"
echo "========================================"
check_file "packages/zalo-parser/wrangler.toml" "00000000-0000-0000-0000-000000000000" "Valid database ID"

# Check project name consistency
echo ""
echo "========================================"
echo "Project Name Consistency"
echo "========================================"
echo "Checking dashboard project name..."
DASHBOARD_NAME=$(grep '^name = ' apps/dashboard/wrangler.toml | cut -d'"' -f2)
if [ "$DASHBOARD_NAME" = "mekong-ide" ]; then
    echo -e "${GREEN}  ✓ Dashboard project name: $DASHBOARD_NAME${NC}"
else
    echo -e "${YELLOW}  ⚠ Dashboard project name: $DASHBOARD_NAME (expected: mekong-ide)${NC}"
    ((WARNINGS++))
fi

# Check deployment scripts exist
echo ""
echo "========================================"
echo "Deployment Scripts"
echo "========================================"
check_exists "scripts/deploy-dashboard.sh" "Dashboard deploy script"
check_exists "scripts/setup-cloudflare-complete.sh" "Complete setup script"

# Check CI/CD workflow
echo ""
echo "========================================"
echo "CI/CD Configuration"
echo "========================================"
check_exists ".github/workflows/deploy-cf.yml" "Cloudflare deploy workflow"

# Check migrations exist
echo ""
echo "========================================"
echo "Database Migrations"
echo "========================================"
check_exists "apps/api/migrations/sessions/001_initial.sql" "Sessions migration"
check_exists "apps/api/migrations/audit/001_initial.sql" "Audit migration"

# Check required tools
echo ""
echo "========================================"
echo "Required Tools"
echo "========================================"
check_command "wrangler" "Wrangler CLI"
check_command "node" "Node.js"
check_command "pnpm" "pnpm"

# Summary
echo ""
echo "========================================"
echo "Validation Summary"
echo "========================================"

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed! Deployment configuration is valid.${NC}"
    echo ""
    echo "You can now:"
    echo "  1. Run: ./scripts/setup-cloudflare-complete.sh (if not already run)"
    echo "  2. Test: cd apps/api && pnpm dev"
    echo "  3. Deploy: pnpm run deploy:staging"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠ Passed with $WARNINGS warning(s)${NC}"
    echo "Review warnings above before proceeding."
    exit 0
else
    echo -e "${RED}✗ Failed with $ERRORS error(s) and $WARNINGS warning(s)${NC}"
    echo ""
    echo "Please fix the errors above before deploying."
    echo "Run ./scripts/setup-cloudflare-complete.sh to create missing resources."
    exit 1
fi
