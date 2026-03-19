#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# SYNC COMMANDS — Convert .claude/commands/*.md to other tool formats
#
# Claude Code: .claude/commands/cook.md ($ARGUMENTS)
# Gemini CLI:  .gemini/commands/cook.toml ({{args}})
# OpenCode:    .opencode/commands/cook.md ($INPUT)
#
# Usage: bash scripts/sync-commands.sh [--all|--gemini|--opencode|--agents]
# ═══════════════════════════════════════════════════════════════
set -uo pipefail

MEKONG_ROOT="${MEKONG_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
SRC="$MEKONG_ROOT/.claude/commands"
TOTAL=0 SYNCED=0

echo "🔄 Syncing commands from .claude/commands/..."

# ─── GEMINI CLI (.toml format) ───
sync_gemini() {
  local DEST="$MEKONG_ROOT/.gemini/commands"
  mkdir -p "$DEST"
  local count=0

  for md in "$SRC"/*.md; do
    [ -f "$md" ] || continue
    local base=$(basename "$md" .md)
    local toml="$DEST/${base}.toml"

    # Extract description from frontmatter
    local desc=$(sed -n 's/^description: *"\(.*\)"/\1/p' "$md" | head -1)
    [ -z "$desc" ] && desc="Mekong command: $base"

    cat > "$toml" << TOML
description = "$desc"

[steps]
[steps.run]
command = "mekong $base {{args}}"
TOML
    count=$((count + 1))
  done
  echo "  ✅ Gemini: $count commands → .gemini/commands/"
}

# ─── OPENCODE (.md format, $INPUT vars) ───
sync_opencode() {
  local DEST="$MEKONG_ROOT/.opencode/commands"
  mkdir -p "$DEST"
  local count=0

  for md in "$SRC"/*.md; do
    [ -f "$md" ] || continue
    local base=$(basename "$md")
    local target="$DEST/$base"

    # Copy and replace $ARGUMENTS with $INPUT
    sed 's/\$ARGUMENTS/\$INPUT/g' "$md" > "$target"
    count=$((count + 1))
  done
  echo "  ✅ OpenCode: $count commands → .opencode/commands/"
}

# ─── AGENTS.md (universal — all tools read this) ───
sync_agents_md() {
  local AGENTS_FILE="$MEKONG_ROOT/AGENTS.md"
  local CMD_COUNT=$(ls "$SRC"/*.md 2>/dev/null | wc -l | tr -d ' ')

  cat > "$AGENTS_FILE" << 'AGENTSMD'
# AGENTS.md — Mekong CLI Universal Configuration
# Read by: Claude Code, Gemini CLI, OpenCode, Cursor, Codex, Amp
# Ref: https://agents.md

## Project Overview
Mekong CLI — AI-operated business platform. 6 layers, 300+ commands.
Open source (BSL 1.1). Universal LLM (3 vars, any provider).

## Commands
All mekong commands are in `.claude/commands/*.md` format.
To execute any command: `mekong <command-name> <arguments>`
Engine routes to Python CLI → PEV orchestrator → LLM.

## Code Style
- Python: snake_case, type hints required, < 200 lines per file
- TypeScript: camelCase, strict mode, ESM imports
- Commits: conventional format (feat/fix/refactor/docs/test)
- Tests: pytest (Python), vitest (TypeScript)

## Build & Test
```bash
pip install -e .          # Python CLI
pnpm install              # TypeScript packages
python3 -m pytest tests/  # Run tests
mekong doctor check       # Health check
```

## Architecture
```
CLI (mekong cook/fix/plan) → API Gateway → PEV Engine → Agent Layer → LLM Router
```
6 Layers: Studio → Founder → Business → Product → Engineering → Ops
AGENTSMD

  echo "  ✅ AGENTS.md: generated ($CMD_COUNT commands referenced)"
}

# Parse args
TARGET="${1:---all}"
case "$TARGET" in
  --gemini)   sync_gemini ;;
  --opencode) sync_opencode ;;
  --agents)   sync_agents_md ;;
  --all)      sync_gemini; sync_opencode; sync_agents_md ;;
  *)          echo "Usage: $0 [--all|--gemini|--opencode|--agents]"; exit 1 ;;
esac

echo "✅ Command sync complete."
