#!/usr/bin/env bash
# .ci/check-agent-frontmatter.sh
#
# CI guard: every .md file under .claude/agents/ MUST declare `name:` and
# `description:` per the Claude Code subagent spec. Without these, Claude
# Code's Task tool can't dispatch the subagent — it becomes invisible and
# any `Task(subagent_type="<name>")` call fails at runtime.
#
# Companion to .ci/check-skill-frontmatter.sh + check-command-frontmatter.sh.
#
# Usage:
#   bash .ci/check-agent-frontmatter.sh                # exit 1 on violation
#   bash .ci/check-agent-frontmatter.sh --staged-only  # only staged files
#
# Exit 0 when clean.

set -euo pipefail

MEKONG_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCOPE="${1:-}"

cd "$MEKONG_ROOT"

if [ "$SCOPE" = "--staged-only" ]; then
  files=$(git diff --cached --name-only --diff-filter=ACM \
            -- '.claude/agents/**/*.md' '.claude/agents/*.md' 2>/dev/null || true)
else
  files=$(find .claude/agents -name "*.md" -type f 2>/dev/null || true)
fi

if [ -z "$files" ]; then
  echo "✅ No agent .md files in scope"
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
  echo "Found $violations violation(s) across $total agent file(s)."
  echo "Fix: add YAML frontmatter at the top of the file:"
  echo "  ---"
  echo "  name: my-agent-name"
  echo "  description: \"When to dispatch this subagent\""
  echo "  tools: [Read, Write, Bash]   # optional"
  echo "  ---"
  exit 1
fi

echo "✅ $total/$total agent files have compliant frontmatter"
exit 0
