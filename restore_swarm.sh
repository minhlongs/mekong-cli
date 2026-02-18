#!/bin/bash
# 🦞 Tôm Hùm Brain — Restore Swarm (2-Tab Layout)
# CTO (Window 0) + Worker (Window 1)

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Kill existing session
tmux kill-session -t tom_hum_brain 2>/dev/null || true
pkill -9 -f "claude" 2>/dev/null || true
sleep 2

# Ensure Antigravity Proxy is running on port 9191
if ! curl -sf http://localhost:9191/health > /dev/null 2>&1; then
    echo "⚡ Starting Antigravity Proxy on port 9191..."
    PORT=9191 antigravity-claude-proxy &
    sleep 3
fi

# Ensure Adapter is running on port 11436
if ! curl -sf http://localhost:11436/health > /dev/null 2>&1; then
    echo "⚡ Starting Anthropic Adapter on port 11436..."
    PORT=11436 node scripts/anthropic-adapter.js &
    sleep 3
fi

# === PROXY CONFIG ===
PROXY_URL="http://localhost:11436"
PROXY_PORT="11436"
CLAUDE_CONFIG_DIR="/Users/macbookprom1/.claude_antigravity_${PROXY_PORT}"
MODEL="claude-sonnet-4-5-20250514"

# Ensure Claude config dir exists
mkdir -p "$CLAUDE_CONFIG_DIR"

ENV_VARS="unset ANTHROPIC_AUTH_TOKEN && export ANTHROPIC_API_KEY=\"ollama\" && export ANTHROPIC_BASE_URL=\"${PROXY_URL}\" && export CLAUDE_BASE_URL=\"${PROXY_URL}\" && export CLAUDE_CONFIG_DIR=\"${CLAUDE_CONFIG_DIR}\""
CLAUDE_CMD="${ENV_VARS} && claude --model ${MODEL} --dangerously-skip-permissions"

# === CREATE 2-TAB TMUX SESSION ===
echo "🦞 Creating 2-tab tmux session..."

# Window 0: CTO (Brain + Task Watcher)
tmux new-session -d -s tom_hum_brain -n "CTO" -x 200 -y 50

# Start brain/CTO using task-watcher.js (actual entry point)
tmux send-keys -t tom_hum_brain:CTO.0 "cd ${SCRIPT_DIR}/apps/openclaw-worker && node task-watcher.js 2>&1 | tee ~/tom_hum_cto.log" Enter

# Window 1: Worker (CC CLI)
tmux new-window -t tom_hum_brain -n "Worker"
tmux send-keys -t tom_hum_brain:Worker.0 "cd ${SCRIPT_DIR} && ${CLAUDE_CMD}" Enter

# Wait for CC CLI to boot
sleep 8

# NOTE: Do NOT send Enter here — brain's spawnBrain() handles bypass permissions
# Sending extra Enter causes "queued messages" in CC CLI

# Switch to Worker tab
tmux select-window -t tom_hum_brain:Worker

echo "✅ Swarm ready! 2 tabs: CTO + Worker"
echo "   📋 tmux attach -t tom_hum_brain"
