#!/bin/bash
# ADAPTER REGISTRY — Detect + select AI CLI tools
# Source this file: source mekong/adapters/registry.sh

MEKONG_ROOT="${MEKONG_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"

# Tool database: binary|idle_pattern|launch_cmd
declare -A TOOL_BINARY TOOL_IDLE TOOL_LAUNCH
TOOL_BINARY=([claude]="claude" [gemini]="gemini" [opencode]="opencode" [aider]="aider" [codex]="codex" [amp]="amp")
TOOL_IDLE=([claude]="❯|bypass" [gemini]="Type your message" [opencode]="^>" [aider]="aider>" [codex]="codex>" [amp]="amp>")
TOOL_LAUNCH=([claude]="claude --dangerously-skip-permissions" [gemini]="gemini" [opencode]="opencode" [aider]="aider --yes-always" [codex]="codex --full-auto" [amp]="amp")

TOOL_PRIORITY=(claude gemini opencode aider codex amp)

is_tool_available() { command -v "${TOOL_BINARY[$1]}" &>/dev/null; }

list_available_tools() {
  local out=""
  for t in "${TOOL_PRIORITY[@]}"; do
    is_tool_available "$t" && out+="$t "
  done
  echo "$out"
}

select_tool() {
  local req="${1:-auto}"
  if [ "$req" != "auto" ]; then
    is_tool_available "$req" && echo "$req" && return 0
    echo "ERROR: $req not installed" >&2; return 1
  fi
  [ -n "${MEKONG_TOOL:-}" ] && is_tool_available "$MEKONG_TOOL" && echo "$MEKONG_TOOL" && return 0
  for t in "${TOOL_PRIORITY[@]}"; do
    is_tool_available "$t" && echo "$t" && return 0
  done
  echo "ERROR: No AI CLI found" >&2; return 1
}

# Idle detection — works for ANY tool
is_pane_idle() {
  local pane=$1 session=$2
  local tail5
  tail5=$(tmux capture-pane -t "${session}:0.${pane}" -p 2>/dev/null | tail -5)
  # Check all known idle patterns
  for t in "${TOOL_PRIORITY[@]}"; do
    if echo "$tail5" | grep -qE "${TOOL_IDLE[$t]}"; then echo "${t}:idle"; return 0; fi
  done
  # Working?
  if echo "$tail5" | grep -qE "Bash\(|Read [0-9]|Write\(|Edit\(|Running|thinking|Hashing|Blanching|Creating|Generating|Brewing|Cooking|Baking|Stewing|Sautéed|Cogitated|Crunching|Pondering|Crystallizing"; then
    echo "working"; return 1
  fi
  # Shell crashed?
  if echo "$tail5" | grep -qE "bash-5|% $|\\$  $"; then echo "shell:crashed"; return 2; fi
  echo "unknown:busy"; return 1
}

# Get launch command for tool
get_launch_cmd() {
  local tool=$1 cwd="${2:-.}"
  local adapter="$MEKONG_ROOT/mekong/adapters/${tool}-cli.sh"
  if [ -f "$adapter" ]; then
    echo "bash $adapter --interactive --cwd $cwd"
  else
    echo "cd $cwd && ${TOOL_LAUNCH[$tool]}"
  fi
}

# Respawn tool in tmux pane
respawn_in_pane() {
  local pane=$1 session=$2 tool=$3 cwd="${4:-$HOME/mekong-cli}"
  local cmd=$(get_launch_cmd "$tool" "$cwd")
  tmux send-keys -t "${session}:0.${pane}" -l "$cmd" 2>/dev/null || true
  sleep 0.5
  tmux send-keys -t "${session}:0.${pane}" Enter 2>/dev/null || true
}
