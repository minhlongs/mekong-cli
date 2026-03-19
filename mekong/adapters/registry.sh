#!/bin/bash
# ADAPTER REGISTRY — Detect + select AI CLI tools (bash 3.2 compatible)
# Source this file: source mekong/adapters/registry.sh

MEKONG_ROOT="${MEKONG_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/../.." 2>/dev/null && pwd || echo "$HOME/mekong-cli")}"

# Tool priority order
TOOL_PRIORITY="claude gemini opencode aider codex amp"

# ─── TOOL DATABASE (bash 3.2 compatible — no declare -A) ───
_tool_binary() {
  case "$1" in
    claude)   echo "claude";;
    gemini)   echo "gemini";;
    opencode) echo "opencode";;
    aider)    echo "aider";;
    codex)    echo "codex";;
    amp)      echo "amp";;
    *)        echo "";;
  esac
}

_tool_idle() {
  case "$1" in
    claude)   echo "❯|bypass";;
    gemini)   echo "Type your message";;
    opencode) echo "^>";;
    aider)    echo "aider>";;
    codex)    echo "codex>";;
    amp)      echo "amp>";;
    *)        echo "";;
  esac
}

_tool_launch() {
  case "$1" in
    claude)   echo "claude --dangerously-skip-permissions";;
    gemini)   echo "gemini";;
    opencode) echo "opencode";;
    aider)    echo "aider --yes-always";;
    codex)    echo "codex --full-auto";;
    amp)      echo "amp";;
    *)        echo "";;
  esac
}

# ─── DETECTION ───
is_tool_available() { command -v "$(_tool_binary "$1")" >/dev/null 2>&1; }

list_available_tools() {
  local out=""
  for t in $TOOL_PRIORITY; do
    is_tool_available "$t" && out="$out$t "
  done
  echo "$out"
}

# ─── SELECTION ───
select_tool() {
  local req="${1:-auto}"
  if [ "$req" != "auto" ]; then
    is_tool_available "$req" && echo "$req" && return 0
    echo "ERROR: $req not installed" >&2; return 1
  fi
  if [ -n "${MEKONG_TOOL:-}" ]; then
    is_tool_available "$MEKONG_TOOL" && echo "$MEKONG_TOOL" && return 0
  fi
  for t in $TOOL_PRIORITY; do
    is_tool_available "$t" && echo "$t" && return 0
  done
  echo "ERROR: No AI CLI found" >&2; return 1
}

# ─── IDLE DETECTION (multi-tool) ───
is_pane_idle() {
  local pane="$1" session="$2"
  local tail5
  tail5=$(tmux capture-pane -t "${session}:0.${pane}" -p 2>/dev/null | tail -5)
  
  # Check all known idle patterns
  for t in $TOOL_PRIORITY; do
    local pattern="$(_tool_idle "$t")"
    if [ -n "$pattern" ] && echo "$tail5" | grep -qE "$pattern"; then
      echo "${t}:idle"; return 0
    fi
  done
  
  # Working patterns
  if echo "$tail5" | grep -qE "Bash\(|Read [0-9]|Write\(|Edit\(|Running|thinking|Hashing|Blanching|Creating|Generating|Brewing|Cooking|Baking|Stewing|Sautéed|Cogitated|Crunching|Pondering|Crystallizing|Sublimating|Boondoggling"; then
    echo "working"; return 1
  fi
  
  # Shell crashed
  if echo "$tail5" | grep -qE "bash-5|% $|\\$  $"; then
    echo "shell:crashed"; return 2
  fi
  
  echo "unknown:busy"; return 1
}

# ─── LAUNCH ───
get_launch_cmd() {
  local tool="$1" cwd="${2:-.}"
  local adapter="$MEKONG_ROOT/mekong/adapters/${tool}-cli.sh"
  if [ -f "$adapter" ]; then
    echo "bash $adapter --interactive --cwd $cwd"
  else
    echo "cd $cwd && $(_tool_launch "$tool")"
  fi
}

# Respawn tool in tmux pane
respawn_in_pane() {
  local pane="$1" session="$2" tool="$3" cwd="${4:-$HOME/mekong-cli}"
  local cmd
  cmd=$(get_launch_cmd "$tool" "$cwd")
  tmux send-keys -t "${session}:0.${pane}" -l "$cmd" 2>/dev/null || true
  sleep 0.5
  tmux send-keys -t "${session}:0.${pane}" Enter 2>/dev/null || true
}
