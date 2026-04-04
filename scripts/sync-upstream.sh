#!/usr/bin/env bash
# Sync upstream OpenClaw v2026.4.2 into Mekong CLI
# Run on M1 Max with good network: bash scripts/sync-upstream.sh
set -euo pipefail

UPSTREAM_URL="https://github.com/openclaw/openclaw.git"
BRANCH="claude/openclaw-v2026.4.2-sync"

echo "=== Mekong CLI — Upstream OpenClaw Sync ==="
echo "Target: v2026.4.2 (latest)"

# 1. Ensure upstream remote
git remote add upstream "$UPSTREAM_URL" 2>/dev/null || true
echo "Remote: $(git remote get-url upstream)"

# 2. Fetch upstream (full, no tags to speed up)
echo "Fetching upstream main..."
git fetch --no-tags upstream main

# 3. Show delta
echo ""
echo "=== Commits ahead (Mekong custom) ==="
git log --oneline upstream/main..HEAD | head -20
echo ""
echo "=== Commits behind (upstream new) ==="
git log --oneline HEAD..upstream/main | head -20

# 4. Create merge branch if not on it
CURRENT=$(git branch --show-current)
if [ "$CURRENT" != "$BRANCH" ]; then
  git checkout -b "$BRANCH" 2>/dev/null || git checkout "$BRANCH"
fi

# 5. Merge upstream, keep Mekong customizations
echo ""
echo "Merging upstream/main..."
git merge upstream/main --no-commit --allow-unrelated-histories || true

# 6. Resolve conflicts — keep Mekong files
KEEP_OURS=(
  ".claude/commands"
  ".claude/skills"
  "factory"
  "recipes"
  "packages/ui"
  "apps/dashboard"
  "docs/BINH_PHAP"
  "docs/development-"
  "core/error_handling.py"
  "skills/mekong"
  "plugins/mekong-raas"
  "plugins/mekong-tasks"
  "CLAUDE.md"
  "README.md"
)

for pattern in "${KEEP_OURS[@]}"; do
  # Find conflicted files matching pattern and resolve with ours
  git diff --name-only --diff-filter=U 2>/dev/null | grep "^${pattern}" | while read -r f; do
    echo "  Keeping ours: $f"
    git checkout --ours "$f" 2>/dev/null || true
    git add "$f" 2>/dev/null || true
  done
done

# Stage everything
git add -A

# 7. Commit
git commit -m "feat: sync upstream openclaw v2026.4.2 — gateway, skills, plugins, tasks

Upstream features integrated:
- v2026.3.8:  CLI backup/verify, macOS onboarding
- v2026.3.23: ClawHub marketplace, Browser/Chrome MCP, plugin install
- v2026.3.24: Gateway /v1/ API (OpenAI-compat), Skills system, before_dispatch hooks
- v2026.4.1:  /tasks background board, channel plugins
- v2026.4.2:  Plugin config migration, xAI/Firecrawl web_fetch

Mekong customizations preserved:
- .claude/commands/ (359 commands)
- factory/ (contracts, layers, self_test)
- recipes/ (DAG pipelines)
- skills/mekong/ (ClawHub packages)
- plugins/mekong-raas/ (RaaS metering)
- plugins/mekong-tasks/ (DAG→/tasks adapter)"

echo ""
echo "=== Sync complete ==="
git log --oneline -1
echo ""

# 8. Verify
echo "Running self_test..."
python3 factory/self_test.py 2>&1 | tail -5

echo ""
echo "Push with: git push origin $BRANCH"
