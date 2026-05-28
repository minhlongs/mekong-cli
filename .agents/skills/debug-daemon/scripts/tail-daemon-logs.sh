#!/bin/bash
# Tail last 50 lines of daemon + tmux worker logs
# Usage: ./tail-daemon-logs.sh [session-name]

SESSION="${1:-cto}"

echo "[daemon] Last 50 lines from tmux session '$SESSION':"
echo "=================================================="

if tmux has-session -t "$SESSION" 2>/dev/null; then
    tmux capture-pane -t "$SESSION" -p -S -50
else
    echo "[daemon] tmux session '$SESSION' not found" >&2
    echo "[daemon] Available sessions:"
    tmux ls 2>/dev/null || echo "  (no tmux sessions)"
fi
