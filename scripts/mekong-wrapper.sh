#!/bin/bash
# MEKONG WRAPPER — Universal AI CLI dispatcher
# Usage: mekong-wrapper [--tool X] [--model M] [--list-tools] [PROMPT]
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export MEKONG_ROOT="${MEKONG_ROOT:-$(dirname "$SCRIPT_DIR")}"

# Source registry (with fallback)
REGISTRY="$MEKONG_ROOT/mekong/adapters/registry.sh"
if [ -f "$REGISTRY" ]; then
  source "$REGISTRY"
else
  echo "❌ Registry not found: $REGISTRY — falling back to claude"
  FALLBACK=true
fi

TOOL="${MEKONG_TOOL:-auto}" MODEL="${MEKONG_MODEL:-}" CWD="${MEKONG_CWD:-$MEKONG_ROOT}"
PROMPT="" INTERACTIVE=false ACTION="run" QUIET=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --tool|-t) TOOL="$2"; shift 2;; --model|-m) MODEL="$2"; shift 2;;
    --cwd) CWD="$2"; shift 2;; --interactive|-i) INTERACTIVE=true; shift;;
    --list-tools) ACTION="list"; shift;; --status) ACTION="status"; shift;;
    --quiet|-q) QUIET=true; shift;; --help|-h) ACTION="help"; shift;;
    --) shift; PROMPT="$*"; break;;
    -*) echo "Unknown: $1" >&2; exit 1;; *) PROMPT="$*"; break;;
  esac
done

# Fallback mode (no registry)
if [ "${FALLBACK:-}" = true ]; then
  cd "$CWD"
  exec claude --dangerously-skip-permissions "$@"
fi

case "$ACTION" in
  list)
    echo "AI CLI tools:"
    for t in "${TOOL_PRIORITY[@]}"; do
      if is_tool_available "$t"; then echo "  ✅ $t"
      else echo "  ❌ $t"; fi
    done
    echo ""
    echo "Commands: $(find "$MEKONG_ROOT/.claude/commands" -name '*.md' 2>/dev/null | wc -l | tr -d ' ')"
    echo "Skills: $(find "$MEKONG_ROOT/.claude/skills" -name 'SKILL.md' 2>/dev/null | wc -l | tr -d ' ')"
    exit 0;;
  status)
    SEL=$(select_tool "$TOOL")
    echo "Tool: $SEL | Model: ${MODEL:-default} | Root: $MEKONG_ROOT"
    echo "Available: $(list_available_tools)"
    echo "Commands: $(find "$MEKONG_ROOT/.claude/commands" -name '*.md' 2>/dev/null | wc -l | tr -d ' ')"
    exit 0;;
  help) head -5 "$0" | sed 's/^# //'; exit 0;;
esac

SEL=$(select_tool "$TOOL") || exit 1

# Banner
if [ "$QUIET" = false ]; then
  echo "🌊 MEKONG CLI → $SEL"
fi

ADAPTER="$MEKONG_ROOT/mekong/adapters/${SEL}-cli.sh"
if [ ! -f "$ADAPTER" ]; then
  # No adapter — use raw launch command from registry
  if [ "$INTERACTIVE" = true ] || [ -z "$PROMPT" ]; then
    CMD=$(get_launch_cmd "$SEL" "$CWD")
    exec $CMD
  elif [ -n "$PROMPT" ]; then
    cd "$CWD" && exec ${TOOL_LAUNCH[$SEL]} -p "$PROMPT"
  fi
  exit $?
fi

# Dispatch through adapter
ARGS=()
[ "$INTERACTIVE" = true ] && ARGS+=(--interactive)
[ -n "$MODEL" ] && ARGS+=(--model "$MODEL")
[ -n "$CWD" ] && ARGS+=(--cwd "$CWD")
[ -n "$PROMPT" ] && ARGS+=(--prompt "$PROMPT")
exec bash "$ADAPTER" "${ARGS[@]}"
