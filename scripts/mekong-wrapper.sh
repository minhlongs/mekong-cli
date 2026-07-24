#!/bin/bash
# MEKONG WRAPPER — Universal AI CLI dispatcher (bash 3.2 compat)
# Usage: mekong-wrapper [--tool X] [--model M] [--list-tools] [PROMPT]
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export MEKONG_ROOT="${MEKONG_ROOT:-$(dirname "$SCRIPT_DIR")}"
export MEKONG_TOOL="${MEKONG_TOOL:-auto}"
export MEKONG_MODEL="${MEKONG_MODEL:-}"
export MEKONG_CWD="${MEKONG_CWD:-$MEKONG_ROOT}"

# Require mekong-cli checkout location to be resolvable.
if [ ! -d "$MEKONG_ROOT/src" ]; then
  rc=1
  echo "[mekong-wrapper] ERROR: MEKONG_ROOT=$MEKONG_ROOT is not a mekong-cli checkout. (rc=$rc)"
  exit $rc
fi

# Adapter registry is optional; fall back to base cli when missing.
if [ -f "$MEKONG_ROOT/mekong/adapters/registry.sh" ]; then
  set +u
  # shellcheck source=/dev/null
  . "$MEKONG_ROOT/mekong/adapters/registry.sh" || true
  set -u
else
  echo "[mekong-wrapper] WARN: missing mekong/adapters/registry.sh; base cli fallback active."
fi

PROMPT=""
INTERACTIVE=false
ACTION="run"
PIPELINE_STAGES=""
TOOL="${TOOL:-auto}"
MODEL="${MODEL:-}"
CWD="${CWD:-$MEKONG_CWD}"

while [ $# -gt 0 ]; do
  case "$1" in
    --tool|-t) TOOL="${2:-auto}"; shift 2 ;;
    --model|-m) MODEL="${2:-}"; shift 2 ;;
    --cwd) CWD="${2:-}"; shift 2 ;;
    --interactive|-i) INTERACTIVE=true; shift ;;
    --list-tools) ACTION="list"; shift ;;
    --status) ACTION="status"; shift ;;
    --help|-h|help) ACTION="help"; shift ;;
    --quiet|-q) shift ;;
    --pipeline) ACTION="pipeline"; PIPELINE_STAGES="${2:-}"; shift 2 ;;
    --) shift; PROMPT="$*"; break ;;
    -*) echo "Unknown: $1" >&2; exit 1 ;;
    *) PROMPT="$*"; break ;;
  esac
done

case "$ACTION" in
  help)
    printf '%s\n' '#!/bin/bash MEKONG WRAPPER — Universal AI CLI dispatcher (bash 3.2 compat)' \
      'Usage: mekong-wrapper [--tool X] [--model M] [--list-tools] [PROMPT]' \
      'Flags: --tool, --model, --cwd, --interactive, --list-tools, --status, --help, --pipeline, --'
    exit 0
    ;;
  list|status) cd "$MEKONG_ROOT" && exec python3 "$MEKONG_ROOT/src/main.py" "$ACTION" ;;
  pipeline) cd "$MEKONG_ROOT" && exec python3 "$MEKONG_ROOT/src/main.py" --pipeline "$PIPELINE_STAGES" "$PROMPT" ;;
esac

SEL="$(select_tool "$TOOL")" || exit $?
DEFAULT_MODEL=""
case "$SEL" in
  claude) DEFAULT_MODEL="claude-sonnet-4-6-20250514" ;;
esac
MODEL="${MODEL:-$DEFAULT_MODEL}"

LAUNCH="command claude --dangerously-skip-permissions"
if [ -z "$PROMPT" ] || [ "$INTERACTIVE" = true ]; then
  cd "$MEKONG_CWD" && exec $LAUNCH
fi
cd "$MEKONG_CWD" && exec $LAUNCH -p "$PROMPT"
