#!/usr/bin/env bash
#
# Full System Rollback
# Emergency rollback of all components to last known good state
#
# Usage:
#   ./scripts/full-rollback.sh <commit-sha>
#   ./scripts/full-rollback.sh HEAD~1  # Rollback one commit
#
# WARNING: This will roll back ALL deployed components:
#   - Dashboard (Cloudflare Pages)
#   - API Worker
#   - Mekong Engine Worker
#   - Zalo Parser Worker
#
# Exit codes:
#   0 - Success
#   1 - Error

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$REPO_ROOT"

GOOD_COMMIT="${1:-HEAD~1}"

echo "🚨 FULL SYSTEM ROLLBACK"
echo "======================="
echo "Target commit: $GOOD_COMMIT"
echo ""
echo "Components to roll back:"
echo "  [1] Dashboard (apps/dashboard)"
echo "  [2] API Gateway (apps/api)"
echo "  [3] Mekong Engine (packages/mekong-engine)"
echo "  [4] Zalo Parser (packages/zalo-parser)"
echo ""

# Verify commit exists
if ! git cat-file -e "$GOOD_COMMIT^{commit}" 2>/dev/null; then
    echo "ERROR: Commit not found: $GOOD_COMMIT" >&2
    echo ""
    echo "Recent commits:"
    git log --oneline -5
    exit 1
fi

# Check if working tree is clean
if ! git diff --quiet; then
    echo "WARNING: Uncommitted changes detected!"
    git status --short
    echo ""
    read -p "Stash changes and continue? (YES/no): " STASH_CHOICE
    if [[ "${STASH_CHOICE:-YES}" == "YES" ]]; then
        git stash push --include-untracked -m "rollback-$(date +%Y%m%d-%H%M%S)"
        STASHED=true
    else
        echo "Aborting due to uncommitted changes."
        exit 1
    fi
fi

# Double confirmation
echo "This action will deploy the code from commit $GOOD_COMMIT"
echo "and cannot be undone without another deploy."
echo ""
read -p "Type 'ROLLBACK' to confirm: " CONFIRM
if [[ "$CONFIRM" != "ROLLBACK" ]]; then
    echo "Rollback cancelled."
    # Restore stash if we stashed
    if [[ "${STASHED:-false}" == "true" ]]; then
        git stash pop || true
    fi
    exit 0
fi

ROLLBACK_START=$(date +%s)
FAILED=0

# Function to rollback a component
rollback_component() {
    local name="$1"
    local path="$2"
    local deploy_cmd="$3"

    echo ""
    echo "==> Rolling back: $name"
    if git checkout "$GOOD_COMMIT" -- "$path"; then
        echo "    ✓ Code checked out"

        if (cd "$path" && $deploy_cmd); then
            echo "    ✓ Deployed"
            return 0
        else
            echo "    ✗ Deploy failed" >&2
            return 1
        fi
    else
        echo "    ✗ Checkout failed" >&2
        return 1
    fi
}

# 1. Dashboard
if rollback_component "Dashboard" "apps/dashboard" "npm run build && npx wrangler pages deploy .next/static --project-name=mekong-ide --branch=production 2>/dev/null || npm run deploy"; then
    :
else
    FAILED=1
fi

# 2. API Worker
if rollback_component "API Gateway" "apps/api" "npm run deploy"; then
    :
else
    FAILED=1
fi

# 3. Mekong Engine Worker
if rollback_component "Mekong Engine" "packages/mekong-engine" "npm run deploy"; then
    :
else
    FAILED=1
fi

# 4. Zalo Parser Worker
if rollback_component "Zalo Parser" "packages/zalo-parser" "npm run deploy"; then
    :
else
    FAILED=1
fi

# Return to main branch (keep deployed code)
echo ""
echo "==> Returning to main branch..."
git checkout main -- apps/dashboard/ apps/api/ packages/mekong-engine/ packages/zalo-parser/

# Restore stash if we stashed
if [[ "${STASHED:-false}" == "true" ]]; then
    echo ""
    echo "Note: Changes were stashed. Recover with: git stash pop"
fi

ROLLBACK_END=$(date +%s)
DURATION=$((ROLLBACK_END - ROLLBACK_START))

echo ""
echo "═══════════════════════════════════════"
if [[ $FAILED -eq 0 ]]; then
    echo "✅ Full system rollback complete"
else
    echo "⚠️  Rollback completed with errors"
fi
echo "═══════════════════════════════════════"
echo "Duration: $((DURATION / 60))m $((DURATION % 60))s"
echo ""

echo "Verification checklist:"
echo "  [ ] Dashboard:  https://ide.mekongmind.com"
echo "  [ ] API health:  curl https://api.cashclaw.cc/health"
echo "  [ ] Payment flow: ./scripts/smoke-test-payment.sh"
echo ""
echo "View logs:"
echo "  wrangler tail mekong-api"
echo "  wrangler tail mekong-engine"
echo "  wrangler tail zalo-parser"
echo ""

if [[ $FAILED -ne 0 ]]; then
    echo "Some components failed to rollback. Check logs above."
    exit 1
fi

exit 0
