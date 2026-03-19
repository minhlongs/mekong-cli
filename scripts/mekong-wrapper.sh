#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# MEKONG WRAPPER — Universal AI CLI Dispatcher
#
# Wraps ANY AI CLI tool (claude/gemini/opencode/aider/codex/bb)
# Detects available tools, routes to best one, normalizes interface.
#
# Usage:
#   mekong-wrapper [--tool claude|gemini|opencode|aider|auto] [--model MODEL] [PROMPT]
#   mekong-wrapper --interactive          # Open interactive session
#   mekong-wrapper --list-tools           # Show available tools
#   mekong-wrapper --status               # Show current config
#
# Environment:
#   MEKONG_TOOL=claude|gemini|opencode|aider|auto  (default: auto)
#   MEKONG_MODEL=model-name                         (tool-specific)
#   MEKONG_ROOT=/path/to/mekong-cli                 (auto-detected)
# ═══════════════════════════════════════════════════════════════
set -uo pipefail

# Auto-detect project root
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export MEKONG_ROOT="${MEKONG_ROOT:-$(dirname "$SCRIPT_DIR")}"

# Source registry
REGISTRY="$MEKONG_ROOT/mekong/adapters/registry.sh"
if [ -f "$REGISTRY" ]; then
  source "$REGISTRY"
else
  echo "❌ Registry not found: $REGISTRY"
  echo "   Falling back to claude"
  FALLBACK=true
fi

# Defaults
TOOL="${MEKONG_TOOL:-auto}"
MODEL="${MEKONG_MODEL:-}"
CWD="${MEKONG_CWD:-$MEKONG_ROOT}"
PROMPT=""
INTERACTIVE=false
ACTION="run"
QUIET=false

# Parse args
while [[ $# -gt 0 ]]; do
  case $1 in
    --tool|-t)        TOOL="$2"; shift 2;;
    --model|-m)       MODEL="$2"; shift 2;;
    --cwd)            CWD="$2"; shift 2;;
    --interactive|-i) INTERACTIVE=true; shift;;
    --list-tools)     ACTION="list"; shift;;
    --status)         ACTION="status"; shift;;
    --quiet|-q)       QUIET=true; shift;;
    --help|-h)        ACTION="help"; shift;;
    --)               shift; PROMPT="$*"; break;;
    -*)               echo "Unknown flag: $1" >&2; exit 1;;
    *)                PROMPT="$*"; break;;
  esac
done

# ─── FALLBACK MODE (no registry) ───
if [ "${FALLBACK:-}" = true ]; then
  cd "$CWD"
  exec claude --dangerously-skip-permissions "$@"
fi

case "$ACTION" in
  list)
    echo "Available AI CLI tools:"
    for t in "${TOOL_PRIORITY[@]}"; do
      if is_tool_available "$t"; then
        local_ver=$($(get_tool_field "$t" "binary") --version 2>/dev/null | head -1 || echo "?")
        echo "  ✅ $t ($local_ver)"
      else
        echo "  ❌ $t (not installed)"
      fi
    done
    echo ""
    echo "Commands: $(find "$MEKONG_ROOT/.claude/commands" -name '*.md' 2>/dev/null | wc -l | tr -d ' ')"
    echo "Skills: $(find "$MEKONG_ROOT/.claude/skills" -name 'SKILL.md' 2>/dev/null | wc -l | tr -d ' ')"
    exit 0;;

  status)
    SELECTED=$(select_tool "$TOOL")
    echo "🌊 Mekong Wrapper Status:"
    echo "  Active tool: $SELECTED"
    echo "  Model: ${MODEL:-default}"
    echo "  Project root: $MEKONG_ROOT"
    echo "  CWD: $CWD"
    echo "  Available: $(list_available_tools)"
    echo "  Commands: $(find "$MEKONG_ROOT/.claude/commands" -name '*.md' 2>/dev/null | wc -l | tr -d ' ')"
    echo "  Skills: $(find "$MEKONG_ROOT/.claude/skills" -name 'SKILL.md' 2>/dev/null | wc -l | tr -d ' ')"
    exit 0;;

  help)
    head -20 "$0" | grep "^#" | sed 's/^# //'
    exit 0;;
esac

# Select tool
SELECTED=$(select_tool "$TOOL")
if [ $? -ne 0 ]; then exit 1; fi

# Banner
if [ "$QUIET" = false ]; then
  echo "🌊 MEKONG CLI → $SELECTED"
fi

# Get adapter
ADAPTER="$MEKONG_ROOT/mekong/adapters/${SELECTED}-cli.sh"

if [ ! -f "$ADAPTER" ]; then
  # No adapter — use raw launch command from registry
  LAUNCH=$(get_tool_field "$SELECTED" "launch")
  if [ "$INTERACTIVE" = true ] || [ -z "$PROMPT" ]; then
    cd "$CWD" && exec $LAUNCH
  elif [ -n "$PROMPT" ]; then
    cd "$CWD" && exec $LAUNCH -p "$PROMPT"
  fi
  exit $?
fi

# Dispatch through adapter
ADAPTER_ARGS=()
[ "$INTERACTIVE" = true ] && ADAPTER_ARGS+=(--interactive)
[ -n "$MODEL" ] && ADAPTER_ARGS+=(--model "$MODEL")
[ -n "$CWD" ] && ADAPTER_ARGS+=(--cwd "$CWD")
[ -n "$PROMPT" ] && ADAPTER_ARGS+=(--prompt "$PROMPT")

exec bash "$ADAPTER" "${ADAPTER_ARGS[@]}"
