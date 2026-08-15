#!/bin/bash
# project-idea.sh — Run /project-idea in Claude Code from shell
# Usage: bash scripts/project-idea.sh "Build SaaS cho freelancer VN"
#        bash scripts/project-idea.sh "Build SaaS" --plan (optional flags)

cd "$(dirname "$0")/.."
CMD="/project-idea $*"
echo "$CMD" | mekong --print 2>/dev/null || echo "$CMD" | claude --print 2>/dev/null || {
  echo "⚠️  Neither 'mekong' nor 'claude' CLI found."
  echo "   Run 'mekong' first, then type: /project-idea $*"
}
