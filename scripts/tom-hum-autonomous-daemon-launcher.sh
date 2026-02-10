#!/bin/bash
# ============================================================================
# 🦞 TÔM HÙM — Autonomous Daemon Launcher
#
# Runs task-watcher.js inside a detached tmux session "tom-hum".
# Designed to run from a REAL terminal (not inside CC CLI sandbox).
#
# Usage:
#   bash scripts/tom-hum-autonomous-daemon-launcher.sh        # start
#   tmux attach -t tom-hum                                     # watch daemon
#   tmux attach -t tom-hum-brain                               # watch CC CLI
#   tail -f ~/tom_hum_cto.log                                  # watch logs
#   tmux kill-session -t tom-hum                                # stop
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MEKONG_DIR="$(dirname "$SCRIPT_DIR")"
OPENCLAW_DIR="$MEKONG_DIR/apps/openclaw-worker"
LOG_FILE="${TOM_HUM_LOG:-$HOME/tom_hum_cto.log}"
TMUX_DAEMON="tom-hum"

# --- Prereq checks ---
for cmd in expect tmux claude node; do
  if ! command -v "$cmd" &>/dev/null; then
    echo "❌ $cmd not found in PATH"
    exit 1
  fi
done

if [ ! -f "$OPENCLAW_DIR/task-watcher.js" ]; then
  echo "❌ task-watcher.js not found at $OPENCLAW_DIR"
  exit 1
fi

# --- Cleanup stale state ---
tmux kill-session -t "$TMUX_DAEMON" 2>/dev/null || true
tmux kill-session -t tom-hum-brain 2>/dev/null || true
rm -f /tmp/tom_hum_next_mission.txt /tmp/tom_hum_mission_done
mkdir -p "$MEKONG_DIR/tasks/processed"

# --- Launch in detached tmux ---
tmux new-session -d -s "$TMUX_DAEMON" -x 200 -y 50 \
  "TOM_HUM_BRAIN_MODE=interactive MEKONG_DIR=$MEKONG_DIR node $OPENCLAW_DIR/task-watcher.js 2>&1 | tee -a $LOG_FILE"

echo ""
echo "  🦞 ═══════════════════════════════════════════════"
echo "  🦞  TÔM HÙM AUTONOMOUS DAEMON STARTED"
echo "  🦞  Tmux session: $TMUX_DAEMON"
echo "  🦞  Engine: ${TOM_HUM_ENGINE:-antigravity}"
echo "  🦞  Log: $LOG_FILE"
echo "  🦞 ═══════════════════════════════════════════════"
echo ""
echo "  Commands:"
echo "    tmux attach -t $TMUX_DAEMON          # watch daemon"
echo "    tmux attach -t tom-hum-brain         # watch CC CLI"
echo "    tail -f $LOG_FILE                    # watch logs"
echo "    tmux kill-session -t $TMUX_DAEMON     # stop"
echo ""
