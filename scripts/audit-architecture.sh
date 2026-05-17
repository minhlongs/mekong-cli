#!/usr/bin/env bash
# audit-architecture.sh — ClaudeKit Layer Contract Guard
#
# Validates Layer 1 (global ~/.claude/) vs Layer 2 (mekong .claude/) boundary.
# Run on demand or wire to .husky/pre-commit.
#
# Exit 0 = pass | Exit 1 = layer violation detected

set -euo pipefail

GLOBAL_DIR="$HOME/.claude"
PROJECT_DIR="$(git rev-parse --show-toplevel)/.claude"
ARCH_DOC="$(git rev-parse --show-toplevel)/ARCHITECTURE.md"

if [ ! -d "$PROJECT_DIR" ]; then
  echo "audit-architecture: not in mekong-cli — skip"
  exit 0
fi

# Live counts
G_SKILLS=$(ls "$GLOBAL_DIR/skills" 2>/dev/null | wc -l | tr -d ' ')
M_SKILLS=$(ls "$PROJECT_DIR/skills" 2>/dev/null | wc -l | tr -d ' ')
G_CMDS=$(ls "$GLOBAL_DIR/commands" 2>/dev/null | wc -l | tr -d ' ')
M_CMDS=$(ls "$PROJECT_DIR/commands" 2>/dev/null | wc -l | tr -d ' ')
G_AGENTS=$(ls "$GLOBAL_DIR/agents" 2>/dev/null | wc -l | tr -d ' ')
M_AGENTS=$(ls "$PROJECT_DIR/agents" 2>/dev/null | wc -l | tr -d ' ')

# Overlap counts
SKILL_OVERLAP=$(comm -12 <(ls "$GLOBAL_DIR/skills" 2>/dev/null | sort) <(ls "$PROJECT_DIR/skills" 2>/dev/null | sort) | wc -l | tr -d ' ')
CMD_OVERLAP=$(comm -12 <(ls "$GLOBAL_DIR/commands" 2>/dev/null | sort) <(ls "$PROJECT_DIR/commands" 2>/dev/null | sort) | wc -l | tr -d ' ')
AGENT_OVERLAP=$(comm -12 <(ls "$GLOBAL_DIR/agents" 2>/dev/null | sort) <(ls "$PROJECT_DIR/agents" 2>/dev/null | sort) | wc -l | tr -d ' ')

echo "Layer Contract Audit"
echo "===================="
echo "Skills:   L1=$G_SKILLS  L2=$M_SKILLS  overlap=$SKILL_OVERLAP"
echo "Commands: L1=$G_CMDS  L2=$M_CMDS  overlap=$CMD_OVERLAP"
echo "Agents:   L1=$G_AGENTS  L2=$M_AGENTS  overlap=$AGENT_OVERLAP"

# Thresholds (post-cleanup baseline 2026-04-29)
MAX_SKILL_OVERLAP=40   # 38 actual + 2 buffer (incomplete + 1 mekong-newer-divergent)
MAX_CMD_OVERLAP=2      # 2 divergent kept (idea, marketing-seo)
MAX_AGENT_OVERLAP=0    # main is clean

VIOLATIONS=0

if [ "$SKILL_OVERLAP" -gt "$MAX_SKILL_OVERLAP" ]; then
  echo "❌ Skill overlap $SKILL_OVERLAP > threshold $MAX_SKILL_OVERLAP"
  comm -12 <(ls "$GLOBAL_DIR/skills" 2>/dev/null | sort) <(ls "$PROJECT_DIR/skills" 2>/dev/null | sort) | head -10
  VIOLATIONS=$((VIOLATIONS+1))
fi

if [ "$CMD_OVERLAP" -gt "$MAX_CMD_OVERLAP" ]; then
  echo "❌ Command overlap $CMD_OVERLAP > threshold $MAX_CMD_OVERLAP"
  comm -12 <(ls "$GLOBAL_DIR/commands" 2>/dev/null | sort) <(ls "$PROJECT_DIR/commands" 2>/dev/null | sort)
  VIOLATIONS=$((VIOLATIONS+1))
fi

if [ "$AGENT_OVERLAP" -gt "$MAX_AGENT_OVERLAP" ]; then
  echo "❌ Agent overlap $AGENT_OVERLAP > threshold $MAX_AGENT_OVERLAP"
  echo "   Layer-1 canonical agents must NOT live in Layer-2"
  comm -12 <(ls "$GLOBAL_DIR/agents" 2>/dev/null | sort) <(ls "$PROJECT_DIR/agents" 2>/dev/null | sort)
  VIOLATIONS=$((VIOLATIONS+1))
fi

# ARCHITECTURE.md count drift check (warn only, don't fail)
if [ -f "$ARCH_DOC" ]; then
  if ! grep -q "L2=$M_SKILLS\|skills=$M_SKILLS\|$M_SKILLS skills\|skills.*$M_SKILLS" "$ARCH_DOC" 2>/dev/null; then
    echo "⚠️  ARCHITECTURE.md may be out of sync (skill count $M_SKILLS not found)"
  fi
fi

if [ "$VIOLATIONS" -gt 0 ]; then
  echo ""
  echo "❌ $VIOLATIONS layer contract violation(s)"
  echo "Fix or run: bash scripts/audit-architecture.sh --baseline (to update thresholds)"
  exit 1
fi

echo "✅ Layer contract OK"
exit 0
