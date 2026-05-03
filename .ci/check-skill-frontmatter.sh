#!/usr/bin/env bash
# .ci/check-skill-frontmatter.sh
#
# CI guard: every SKILL.md under .claude/skills/ MUST declare `name:` and
# `description:` in YAML frontmatter — without these fields Claude Code's
# skill auto-loader silently skips the file (the skill becomes invisible).
#
# Companion to .ci/check-no-duplicate-claudekit.sh. Both run from
# .husky/pre-commit so non-compliant SKILL.md never enters history again.
#
# Usage:
#   bash .ci/check-skill-frontmatter.sh                # exit 1 on violation
#   bash .ci/check-skill-frontmatter.sh --staged-only  # only staged files
#
# Exit 0 when clean.

set -euo pipefail

MEKONG_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCOPE="${1:-}"

cd "$MEKONG_ROOT"

if [ "$SCOPE" = "--staged-only" ]; then
  files=$(git diff --cached --name-only --diff-filter=ACM \
            -- '.claude/skills/**/SKILL.md' 2>/dev/null || true)
else
  files=$(find .claude/skills -name SKILL.md -type f 2>/dev/null || true)
fi

if [ -z "$files" ]; then
  echo "✅ No SKILL.md files in scope"
  exit 0
fi

violations=0
total=0

while IFS= read -r f; do
  [ -z "$f" ] && continue
  total=$((total + 1))
  if ! grep -q '^name:[[:space:]]\+\S' "$f"; then
    echo "❌ missing or empty 'name:' in $f"
    violations=$((violations + 1))
  fi
  if ! grep -q '^description:[[:space:]]\+\S' "$f"; then
    echo "❌ missing or empty 'description:' in $f"
    violations=$((violations + 1))
  fi
done <<< "$files"

if [ "$violations" -gt 0 ]; then
  echo
  echo "Found $violations frontmatter violation(s) across $total SKILL.md file(s)."
  echo "Fix: add YAML frontmatter at the top of the file:"
  echo "  ---"
  echo "  name: my-skill-name"
  echo "  description: \"When to activate this skill\""
  echo "  ---"
  exit 1
fi

echo "✅ $total/$total SKILL.md files have compliant frontmatter"
exit 0
