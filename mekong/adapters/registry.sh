#!/bin/bash
# ADAPTER REGISTRY — Detect available AI CLI tools + select best one
# Usage: source mekong/adapters/registry.sh
#        TOOL=$(select_tool "auto")  # or "claude" or "gemini" etc.

MEKONG_ROOT="${MEKONG_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"

# ─── TOOL DATABASE ───
# Format: name|binary|check_cmd|idle_pattern|launch_cmd|has_slash_commands
declare -A TOOL_DB
TOOL_DB=(
  [claude]="claude|claude --version|❯|claude --dangerously-skip-permissions|yes"
  [gemini]="gemini|gemini --version|Type your message|gemini|yes"
  [opencode]="opencode|opencode --version|>|opencode|yes"
  [aider]="aider|aider --version|aider>|aider --yes-always|no"
  [codex]="codex|codex --version|codex>|codex --full-auto|no"
  [bb]="bb|bb --version|bb>|bb|no"
)

# Priority order for auto-selection (best → fallback)
TOOL_PRIORITY=(claude gemini opencode aider codex bb)

# ─── DETECTION ───

is_tool_available() {
  local tool=$1
  local entry="${TOOL_DB[$tool]:-}"
  if [ -z "$entry" ]; then return 1; fi
  local binary
  binary=$(echo "$entry" | cut -d'|' -f1)
  command -v "$binary" &>/dev/null
}

list_available_tools() {
  local available=()
  for tool in "${TOOL_PRIORITY[@]}"; do
    if is_tool_available "$tool"; then
      available+=("$tool")
    fi
  done
  echo "${available[@]}"
}

get_tool_field() {
  local tool=$1 field=$2
  local entry="${TOOL_DB[$tool]:-}"
  case "$field" in
    binary)    echo "$entry" | cut -d'|' -f1 ;;
    check)     echo "$entry" | cut -d'|' -f2 ;;
    idle)      echo "$entry" | cut -d'|' -f3 ;;
    launch)    echo "$entry" | cut -d'|' -f4 ;;
    has_slash) echo "$entry" | cut -d'|' -f5 ;;
  esac
}

# ─── SELECTION ───

select_tool() {
  local requested="${1:-auto}"

  if [ "$requested" != "auto" ]; then
    if is_tool_available "$requested"; then
      echo "$requested"
      return 0
    else
      echo "ERROR: $requested not installed" >&2
      return 1
    fi
  fi

  # Auto-select from env var first
  if [ -n "${MEKONG_TOOL:-}" ] && [ "${MEKONG_TOOL}" != "auto" ]; then
    if is_tool_available "$MEKONG_TOOL"; then
      echo "$MEKONG_TOOL"
      return 0
    fi
  fi

  # Auto-select best available
  for tool in "${TOOL_PRIORITY[@]}"; do
    if is_tool_available "$tool"; then
      echo "$tool"
      return 0
    fi
  done

  echo "ERROR: No AI CLI tool found. Install: npm i -g @anthropic-ai/claude-code" >&2
  return 1
}

# ─── IDLE DETECTION (tool-agnostic) ───

is_pane_idle() {
  local pane=$1 session=$2
  local output
  output=$(tmux capture-pane -t "${session}:0.${pane}" -p 2>/dev/null | tail -5)

  if echo "$output" | grep -qE "❯|bypass"; then echo "claude:idle"; return 0; fi
  if echo "$output" | grep -qE "Type your message"; then echo "gemini:idle"; return 0; fi
  if echo "$output" | grep -qE "^>"; then echo "opencode:idle"; return 0; fi
  if echo "$output" | grep -qE "aider>"; then echo "aider:idle"; return 0; fi
  if echo "$output" | grep -qE "codex>"; then echo "codex:idle"; return 0; fi

  if echo "$output" | grep -qE "Running|thinking|Cooking|Baking|Stewing|Generating|Creating|Brewing"; then
    echo "working"
    return 1
  fi

  if echo "$output" | grep -qE "bash-5|% $|\\$  $"; then
    echo "shell:crashed"
    return 2
  fi

  echo "unknown:busy"
  return 1
}

# ─── LAUNCH ───

get_launch_cmd() {
  local tool=$1
  local model="${2:-}"
  local cwd="${3:-.}"

  local adapter="${MEKONG_ROOT}/mekong/adapters/${tool}-cli.sh"
  if [ -f "$adapter" ]; then
    echo "bash $adapter --interactive --cwd $cwd ${model:+--model $model}"
    return 0
  fi

  local launch
  launch=$(get_tool_field "$tool" "launch")
  echo "cd $cwd && $launch"
}

respawn_in_pane() {
  local pane=$1 session=$2 tool=$3 cwd="${4:-$HOME/mekong-cli}"
  local launch_cmd
  launch_cmd=$(get_launch_cmd "$tool" "" "$cwd")
  tmux send-keys -t "${session}:0.${pane}" C-c "" 2>/dev/null || true
  sleep 0.5
  tmux send-keys -t "${session}:0.${pane}" "$launch_cmd" Enter 2>/dev/null || true
}
