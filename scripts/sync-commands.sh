#!/bin/bash
# SYNC: .claude/commands/*.md → .gemini/commands/*.toml + .opencode/commands/*.md + AGENTS.md
set -uo pipefail
MEKONG_ROOT="${MEKONG_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
SRC="$MEKONG_ROOT/.claude/commands"

echo "🔄 Syncing commands from .claude/commands/..."

# Gemini CLI (.toml format)
sync_gemini() {
  local DEST="$MEKONG_ROOT/.gemini/commands" count=0
  mkdir -p "$DEST"
  for md in "$SRC"/*.md; do
    [ -f "$md" ] || continue
    local base
    base=$(basename "$md" .md)
    local desc
    desc=$(sed -n 's/^description: *"\(.*\)"/\1/p' "$md" | head -1)
    [ -z "$desc" ] && desc="Mekong: $base"
    cat > "$DEST/${base}.toml" << TOML
description = "$desc"
[steps]
[steps.run]
command = "mekong $base {{args}}"
TOML
    count=$((count + 1))
  done
  echo "  ✅ Gemini: $count → .gemini/commands/"
}

# OpenCode (.md, $INPUT instead of $ARGUMENTS)
sync_opencode() {
  local DEST="$MEKONG_ROOT/.opencode/commands" count=0
  mkdir -p "$DEST"
  for md in "$SRC"/*.md; do
    [ -f "$md" ] || continue
    sed 's/\$ARGUMENTS/\$INPUT/g' "$md" > "$DEST/$(basename "$md")"
    count=$((count + 1))
  done
  echo "  ✅ OpenCode: $count → .opencode/commands/"
}

# AGENTS.md (universal — all tools read)
sync_agents() {
  local CMD_COUNT
  CMD_COUNT=$(find "$SRC" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
  cat > "$MEKONG_ROOT/AGENTS.md" << 'EOF'
# AGENTS.md — Mekong CLI
# Read by: Claude Code, Gemini CLI, OpenCode, Cursor, Codex, Amp

## Project
AI-operated business platform. 6 layers, 300+ commands. BSL 1.1.
Universal LLM: 3 env vars (LLM_BASE_URL, LLM_API_KEY, LLM_MODEL), any provider.

## Commands
Commands live in `.claude/commands/*.md`. Execute via: `mekong <name> <args>`
Engine: Python CLI (Typer) → PEV orchestrator → LLM Router → Agent Layer

## Build & Test
```bash
pip install -e .           # Python CLI
pnpm install               # TypeScript packages
python3 -m pytest tests/   # Tests
mekong doctor check        # Health
```

## Style
Python: snake_case, type hints, < 200 lines. TypeScript: strict, ESM.
Commits: conventional (feat/fix/refactor/docs/test). No AI refs in messages.

## Architecture
Studio → Founder → Business → Product → Engineering → Ops
Water Protocol 水: multi-agent context flow between layers.
EOF
  echo "  ✅ AGENTS.md generated ($CMD_COUNT commands)"
}

case "${1:---all}" in
  --gemini) sync_gemini;; --opencode) sync_opencode;; --agents) sync_agents;;
  --all) sync_gemini; sync_opencode; sync_agents;; *) echo "Usage: $0 [--all|--gemini|--opencode|--agents]";;
esac
echo "✅ Sync complete."
