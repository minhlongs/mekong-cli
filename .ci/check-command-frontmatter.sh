#!/usr/bin/env bash
# .ci/check-command-frontmatter.sh
#
# CI guard: every .md file under .claude/commands/ MUST declare a non-empty
# `description:` in YAML frontmatter — Claude Code's command palette uses
# that string as the human-readable label. Files without it render as
# "<command>" with no help, which is the slash-command equivalent of an
# invisible skill.
#
# Companion to .ci/check-skill-frontmatter.sh and
# .ci/check-no-duplicate-claudekit.sh. Hooked into .husky/pre-commit.
#
# Usage:
#   bash .ci/check-command-frontmatter.sh                # exit 1 on violation
#   bash .ci/check-command-frontmatter.sh --staged-only  # only staged files
#
# Exit 0 when clean.

set -euo pipefail

MEKONG_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCOPE="${1:-}"

cd "$MEKONG_ROOT"

if [ "$SCOPE" = "--staged-only" ]; then
  files=$(git diff --cached --name-only --diff-filter=ACM \
            -- '.claude/commands/**/*.md' '.claude/commands/*.md' 2>/dev/null \
          | grep -vE '\.local\.md$|/private/' || true)
else
  # Skip private/local drafts — they're per-developer and gitignored anyway.
  files=$(find .claude/commands -name "*.md" -type f 2>/dev/null \
          | grep -vE '\.local\.md$|/private/' || true)
fi

if [ -z "$files" ]; then
  echo "✅ No command .md files in scope"
  exit 0
fi

violations=0
total=0

while IFS= read -r f; do
  [ -z "$f" ] && continue
  total=$((total + 1))
  if ! grep -q '^description:[[:space:]]\+\S' "$f"; then
    echo "❌ missing or empty 'description:' in $f"
    violations=$((violations + 1))
  fi
done <<< "$files"

if [ "$violations" -gt 0 ]; then
  echo
  echo "Found $violations violation(s) across $total command file(s)."
  echo "Fix: add YAML frontmatter at the top of the file:"
  echo "  ---"
  echo "  description: \"What this command does — 1 line\""
  echo "  argument-hint: \"<optional args>\""
  echo "  ---"
  exit 1
fi

echo "✅ $total/$total command files have compliant frontmatter"
exit 0
