#!/bin/bash
# MEKONG WRAPPER — Universal AI CLI dispatcher (bash 3.2 compat)
# Usage: mekong-wrapper [--tool X] [--model M] [--list-tools] [PROMPT]
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export MEKONG_ROOT="${MEKONG_ROOT:-$(dirname "$SCRIPT_DIR")}"
source "$MEKONG_ROOT/mekong/adapters/registry.sh"

TOOL="${MEKONG_TOOL:-auto}" MODEL="${MEKONG_MODEL:-}" CWD="${MEKONG_CWD:-$MEKONG_ROOT}"
PROMPT="" INTERACTIVE=false ACTION="run"

# Provider→Tool+Model mapping (provider names that aren't CLI binaries)
_resolve_provider() {
  case "$1" in
    qwen)    TOOL="claude"; MODEL="${MODEL:-qwen3.5-plus}";;
    opus)    TOOL="claude"; MODEL="${MODEL:-claude-opus-4-6-20250901}";;
    sonnet)  TOOL="claude"; MODEL="${MODEL:-claude-sonnet-4-6-20250514}";;
    haiku)   TOOL="claude"; MODEL="${MODEL:-claude-haiku-4-5-20251001}";;
    *)       TOOL="$1";;  # Direct tool name (claude, gemini, etc.)
  esac
}

while [[ $# -gt 0 ]]; do
  case $1 in
    --tool|-t) TOOL="$2"; shift 2;; --provider) _resolve_provider "$2"; shift 2;; --model|-m) MODEL="$2"; shift 2;;
    --cwd) CWD="$2"; shift 2;; --interactive|-i) INTERACTIVE=true; shift;;
    --list-tools) ACTION="list"; shift;; --status) ACTION="status"; shift;;
    --help|-h) ACTION="help"; shift;; --quiet|-q) shift;; --) shift; PROMPT="$*"; break;;
    -*) echo "Unknown: $1" >&2; exit 1;; *) PROMPT="$*"; break;;
  esac
done

case "$ACTION" in
  list)
    echo "AI CLI tools:"
    for t in $TOOL_PRIORITY; do
      if is_tool_available "$t"; then echo "  ✅ $t"
      else echo "  ❌ $t"; fi
    done
    echo ""
    echo "Commands: $(find "$MEKONG_ROOT/.claude/commands" -name '*.md' 2>/dev/null | wc -l | tr -d ' ')"
    echo "Skills: $(find "$MEKONG_ROOT/.claude/skills" -name 'SKILL.md' 2>/dev/null | wc -l | tr -d ' ')"
    exit 0;;
  status)
    SEL=$(select_tool "$TOOL")
    echo "🌊 Mekong Wrapper Status:"
    echo "  Tool: $SEL | Model: ${MODEL:-default} | Root: $MEKONG_ROOT"
    echo "  Available: $(list_available_tools)"
    echo "  Commands: $(find "$MEKONG_ROOT/.claude/commands" -name '*.md' 2>/dev/null | wc -l | tr -d ' ')"
    echo "  Skills: $(find "$MEKONG_ROOT/.claude/skills" -name 'SKILL.md' 2>/dev/null | wc -l | tr -d ' ')"
    exit 0;;
  help) head -5 "$0" | sed 's/^# //'; exit 0;;
esac

SEL=$(select_tool "$TOOL") || exit 1
ADAPTER="$MEKONG_ROOT/mekong/adapters/${SEL}-cli.sh"

if [ ! -f "$ADAPTER" ]; then
  LAUNCH=$(_tool_launch "$SEL")
  if [ "$INTERACTIVE" = true ] || [ -z "$PROMPT" ]; then
    cd "$CWD" && exec $LAUNCH
  elif [ -n "$PROMPT" ]; then
    cd "$CWD" && exec $LAUNCH -p "$PROMPT"
  fi
  exit $?
fi

ARGS=""
[ "$INTERACTIVE" = true ] && ARGS="$ARGS --interactive"
[ -n "$MODEL" ] && ARGS="$ARGS --model $MODEL"
[ -n "$CWD" ] && ARGS="$ARGS --cwd $CWD"
[ -n "$PROMPT" ] && ARGS="$ARGS --prompt \"$PROMPT\""

exec bash "$ADAPTER" $ARGS
