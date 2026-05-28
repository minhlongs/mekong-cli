#!/bin/bash
# MEKONG WRAPPER — Universal AI CLI dispatcher (bash 3.2 compat)
# Usage: mekong-wrapper [--tool X] [--model M] [--list-tools] [PROMPT]
#        mekong-wrapper install dept-<name>   # Install a Clipmart department
#        mekong-wrapper install <name>        # Alias (dept- prefix optional)
set -uo pipefail

# Load API keys from macOS Keychain
source "$HOME/scripts/load-keychain-secrets.sh" 2>/dev/null || true

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export MEKONG_ROOT="${MEKONG_ROOT:-$(dirname "$SCRIPT_DIR")}"

# ── dept install subcommand (must run before adapter registry) ──────────────
# Usage: mekong install dept-<name> [args...]
#        mekong install <name> [args...]       (dept- prefix optional)
_dept_install() {
  local raw_name="${1:-}"
  shift || true
  local extra_args=("$@")

  # Strip optional "dept-" prefix to get canonical name
  local name="${raw_name#dept-}"

  local dept_dir="$MEKONG_ROOT/clipmart/departments/$name"
  local install_script="$dept_dir/install.sh"

  if [ -n "$name" ] && [ -f "$install_script" ]; then
    echo "🌊 Mekong — installing department: $name"
    bash "$install_script" "${extra_args[@]+"${extra_args[@]}"}"
    exit $?
  fi

  # install.sh not found — show available departments
  echo "❌  Department '${raw_name}' not found." >&2
  echo "" >&2
  echo "Available departments:" >&2
  local found=0
  for mf in "$MEKONG_ROOT/clipmart/departments"/*/manifest.json; do
    [ -f "$mf" ] || continue
    found=1
    local dept_name; dept_name="$(basename "$(dirname "$mf")")"
    # Extract "name" field with minimal tooling (bash 3.2 compat, no jq required)
    local label; label="$(grep '"name"' "$mf" | head -1 | sed 's/.*"name"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/')"
    echo "  mekong install $dept_name  — $label" >&2
  done
  [ "$found" -eq 0 ] && echo "  (none — no departments found in clipmart/departments/)" >&2
  exit 1
}

# Intercept: mekong install [dept-]<name>
if [ "${1:-}" = "install" ]; then
  shift
  _dept_install "${1:-}" "${@:2}"
fi

# Direct Typer-backed durable goal commands. These must not be treated as
# free-form AI prompts when called from AGY/Gemini command descriptors.
case "${1:-}" in
  cook-auto|cook-auto-parallel|goal|match|studio|portfolio|dealflow|expert|venture)
    cd "$MEKONG_ROOT" && exec python3 -m src.main "$@"
    ;;
esac
# ─────────────────────────────────────────────────────────────────────────────

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
SANDBOX=false
DANGEROUSLY_SKIP_PERMISSIONS=false

_dispatch_typer_command() {
  case "${1:-}" in
    cook-auto|cook-auto-parallel)
      if [ "$DANGEROUSLY_SKIP_PERMISSIONS" = true ]; then
        cd "$MEKONG_ROOT" && exec python3 -m src.main "$@" --auto
      fi
      cd "$MEKONG_ROOT" && exec python3 -m src.main "$@"
      ;;
    goal|match|studio|portfolio|dealflow|expert|venture)
      cd "$MEKONG_ROOT" && exec python3 -m src.main "$@"
      ;;
  esac
}

while [[ $# -gt 0 ]]; do
  case $1 in
    --tool|-t) TOOL="$2"; shift 2;; --provider) _resolve_provider "$2"; shift 2;; --model|-m) MODEL="$2"; shift 2;;
    --cwd) CWD="$2"; shift 2;; --interactive|-i) INTERACTIVE=true; shift;;
    --list-tools) ACTION="list"; shift;; --status) ACTION="status"; shift;;
    --sandbox) SANDBOX=true; export MEKONG_PERMISSION_MODE=ask; shift;;
    --dangerously-skip-permissions|--auto) DANGEROUSLY_SKIP_PERMISSIONS=true; export MEKONG_PERMISSION_MODE=bypass; shift;;
    --parallel) PARALLEL=true; shift;;
    --help|-h) ACTION="help"; shift;; --quiet|-q) shift;; --) shift; _dispatch_typer_command "$@"; PROMPT="$*"; break;;
    -*) echo "Unknown: $1" >&2; exit 1;; *) _dispatch_typer_command "$@"; PROMPT="$*"; break;;
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
  help)
    head -6 "$0" | sed 's/^#[[:space:]]*//'
    echo ""
    echo "Dept install:"
    echo "  mekong install dept-<name>   Install a Clipmart department"
    echo "  mekong install <name>        Same (dept- prefix optional)"
    echo "  (run with no name to list available departments)"
    exit 0;;
esac

SEL=$(select_tool "$TOOL") || exit 1
ADAPTER_NAME="$SEL"
[ "$SEL" = "claude" ] && ADAPTER_NAME="cc"
ADAPTER="$MEKONG_ROOT/mekong/adapters/${ADAPTER_NAME}-cli.sh"

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
[ "$SANDBOX" = true ] && ARGS="$ARGS --sandbox"
[ "$DANGEROUSLY_SKIP_PERMISSIONS" = true ] && ARGS="$ARGS --dangerously-skip-permissions"

exec bash "$ADAPTER" $ARGS
