#!/usr/bin/env bash
#
# Quick API Worker Rollback
# Rolls back the API Worker to a specific good commit
#
# Usage:
#   ./scripts/quick-rollback-api.sh <commit-sha>
#   ./scripts/quick-rollback-api.sh HEAD~2  # Rollback 2 commits
#
# Requirements:
#   - Must be run from mekong-cli root
#   - wrangler must be installed and logged in
#
# Exit codes:
#   0 - Success
#   1 - Error

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

GOOD_COMMIT="${1:-}"

if [[ -z "$GOOD_COMMIT" ]]; then
    echo "Usage: $0 <good-commit-sha>"
    echo ""
    echo "Recent commits for apps/api:"
    git log --oneline -5 apps/api || echo "  (no commits found)"
    echo ""
    echo "Examples:"
    echo "  $0 abc123def      # Rollback to specific commit"
    echo "  $0 HEAD~1         # Rollback one commit"
    echo "  $0 HEAD~3         # Rollback three commits"
    exit 1
fi

# Verify commit exists
if ! git cat-file -e "$GOOD_COMMIT^{commit}" 2>/dev/null; then
    echo "ERROR: Commit not found: $GOOD_COMMIT" >&2
    exit 1
fi

echo "🚨 API Worker Rollback"
echo "====================="
echo "Target commit: $GOOD_COMMIT"
echo ""
echo "This will:"
echo "  1. Checkout the API code from the good commit"
echo "  2. Deploy to production"
echo "  3. Return to main branch"
echo ""
read -p "Type 'YES' to confirm: " CONFIRM
if [[ "$CONFIRM" != "YES" ]]; then
    echo "Rollback cancelled."
    exit 0
fi

# Check if there are uncommitted changes in apps/api
if git diff --quiet apps/api/; then
    echo "✓ Working tree clean for apps/api"
else
    echo "WARNING: Uncommitted changes in apps/api/"
    git status apps/api/ --short
    read -p "Stash changes and continue? (YES/no): " STASH
    if [[ "${STASH:-YES}" == "YES" ]]; then
        git stash push apps/api/
        STASHED=true
    else
        echo "Aborting due to uncommitted changes."
        exit 1
    fi
fi

# Checkout the good version of the API
echo ""
echo "==> Checking out $GOOD_COMMIT for apps/api..."
git checkout "$GOOD_COMMIT" -- apps/api/

# Deploy
echo "==> Deploying API Worker..."
cd apps/api

if ! npm run deploy; then
    echo ""
    echo "ERROR: Deployment failed!" >&2
    echo "Attempting to return to main branch..."
    cd "$REPO_ROOT"
    git checkout main -- apps/api/
    exit 1
fi

# Return to main (keep the deployed code)
cd "$REPO_ROOT"
git checkout main -- apps/api/

if [[ "${STASHED:-false}" == "true" ]]; then
    echo ""
    echo "Note: Changes were stashed. Recover with: git stash pop"
fi

echo ""
echo "✅ API Worker rollback complete"
echo ""
echo "Verification:"
echo "  curl https://api.cashclaw.cc/health"
echo ""
echo "To view logs:"
echo "  wrangler tail mekong-api"
