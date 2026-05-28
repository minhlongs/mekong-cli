#!/usr/bin/env bash
# ============================================================
# Launch CC CLI pane via MEKONG WRAPPER (unified entry point)
#
# All CC CLI-like tools go through mekong-wrapper.sh which handles:
# - Provider routing (claude/opus/sonnet/qwen/gemini/opencode)
# - cd to mekong-cli root (so .claude/commands/ loads)
# - --dangerously-skip-permissions
#
# USAGE:
#   ./scripts/launch-pane-cc.sh <pane_idx> <project_dir> [session_name] [provider]
#   ./scripts/launch-pane-cc.sh 1 apps/algo-trader tom_hum qwen
#   ./scripts/launch-pane-cc.sh 2 apps/well tom_hum claude
#   ./scripts/launch-pane-cc.sh 3 apps/sophia-proposal tom_hum opus
#
# PROVIDER OPTIONS: agy|claude|opus|sonnet|qwen|gemini|opencode
# ============================================================
set -euo pipefail

PANE_IDX="${1:?Usage: $0 <pane_idx> <project_dir> [session_name] [provider]}"
PROJECT_DIR="${2:?Usage: $0 <pane_idx> <project_dir> [session_name] [provider]}"
SESSION="${3:-tom_hum}"
PROVIDER="${4:-qwen}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MEKONG_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🚀 Launching CC CLI pane P${PANE_IDX}"
echo "   Project: ${PROJECT_DIR}"
echo "   Provider: ${PROVIDER}"
echo "   Via: mekong-wrapper.sh"

# Detect first window and get the N-th pane ID (supports both base-index 0/1 and pane-base-index 0/1)
WINDOW_ID=$(tmux list-windows -t "${SESSION}" -F '#{window_index}' 2>/dev/null | head -n 1 || echo "0")
PANE_IDS=($(tmux list-panes -t "${SESSION}:${WINDOW_ID}" -F '#{pane_id}' 2>/dev/null))
TARGET_PANE="${PANE_IDS[$PANE_IDX]:-}"
if [[ -z "$TARGET_PANE" ]]; then
  echo "❌ Error: Could not find pane index $PANE_IDX in session $SESSION window $WINDOW_ID" >&2
  exit 1
fi

# Kill any existing process in the pane first (safe respawn)
tmux send-keys -t "${TARGET_PANE}" C-c "" 2>/dev/null || true
sleep 0.5

# CD to mekong-cli root FIRST — ensures .claude/commands/ discovery
# Then launch via mekong-wrapper (unified entry point)
LAUNCH_CMD="cd '${MEKONG_ROOT}' && MEKONG_ROOT='${MEKONG_ROOT}' bash '${MEKONG_ROOT}/scripts/mekong-wrapper.sh' --provider '${PROVIDER}' --quiet"

# Send to existing tmux pane
tmux send-keys -t "${TARGET_PANE}" "$LAUNCH_CMD" Enter

echo "✅ P${PANE_IDX} launched — cd mekong-cli → mekong-wrapper → ${PROVIDER}"
