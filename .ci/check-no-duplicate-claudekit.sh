#!/usr/bin/env bash
# scripts/check-no-duplicate-claudekit.sh
#
# CI guard: fails if any stock claudekit primitive (subagent or skill bundle
# whose canonical lives in ~/.claude/) is duplicated bit-identical inside
# ~/mekong-cli/.claude/. Diverged forks are allowed but must include a
# "Why-override" header in their SKILL.md / agent .md.
#
# Usage:
#   bash scripts/check-no-duplicate-claudekit.sh        # exit 1 on violation
#   bash scripts/check-no-duplicate-claudekit.sh --fix  # auto-remove violations
#
# Exits 0 when clean. Designed to be hooked into pre-commit (.husky/pre-commit
# or pre-push) and CI workflows.

set -euo pipefail

GLOBAL_CK="${GLOBAL_CLAUDEKIT:-$HOME/.claude}"
MEKONG_CK="${MEKONG_CLAUDEKIT:-$(cd "$(dirname "$0")/.." && pwd)/.claude}"
FIX_MODE="${1:-}"

violations=0

# ── Stock subagents — bit-identical duplication is forbidden ──────────────────
if [ -d "$GLOBAL_CK/agents" ] && [ -d "$MEKONG_CK/agents" ]; then
  while IFS= read -r global_file; do
    name=$(basename "$global_file")
    mekong_file="$MEKONG_CK/agents/$name"
    [ -f "$mekong_file" ] || continue
    if diff -q "$global_file" "$mekong_file" >/dev/null 2>&1; then
      echo "❌ duplicate stock agent: $name"
      if [ "$FIX_MODE" = "--fix" ]; then
        rm -- "$mekong_file"
        echo "   removed (canonical kept at $global_file)"
      fi
      violations=$((violations + 1))
    fi
  done < <(find "$GLOBAL_CK/agents" -maxdepth 1 -name '*.md' -type f)
fi

# ── Stock skill bundles — directories that are bit-identical ─────────────────
if [ -d "$GLOBAL_CK/skills" ] && [ -d "$MEKONG_CK/skills" ]; then
  while IFS= read -r -d '' global_dir; do
    name=$(basename "$global_dir")
    mekong_dir="$MEKONG_CK/skills/$name"
    [ -d "$mekong_dir" ] || continue
    if [ -z "$(diff -rq "$global_dir" "$mekong_dir" 2>&1)" ]; then
      echo "❌ duplicate stock skill: $name"
      if [ "$FIX_MODE" = "--fix" ]; then
        rm -rf -- "$mekong_dir"
        echo "   removed (canonical kept at $global_dir)"
      fi
      violations=$((violations + 1))
    fi
  done < <(find "$GLOBAL_CK/skills" -mindepth 1 -maxdepth 1 -type d -print0)
fi

if [ "$violations" -gt 0 ] && [ "$FIX_MODE" != "--fix" ]; then
  echo
  echo "Found $violations claudekit duplicate(s). Re-run with --fix to remove."
  echo "Or add a 'Why-override' header to keep the override deliberate."
  exit 1
fi

echo "✅ No identical claudekit duplicates in mekong-cli"
exit 0
