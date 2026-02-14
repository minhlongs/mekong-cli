#!/bin/bash
# 🦞 TOM HUM DEEP SUPERVISOR - Hardened Infinite Loop (v31.0 - SERVEO EDITION)
# Chạy: nohup ./scripts/tom-hum-deep-loop.sh &
# Dừng: kill $(cat /tmp/tom-hum-deep.pid)

set -euo pipefail

# --- CONFIGURATION ---
MEKONG_DIR="/Users/macbookprom1/mekong-cli"
APP_DIR="$MEKONG_DIR/apps/openclaw-worker"
LOG_FILE="/tmp/tom-hum-deep.log"
PID_FILE="/tmp/tom-hum-deep.pid"
HEALTH_URL="http://localhost:8765/health"
INTERVAL=60 # Check every 60s
GIT_PULL_INTERVAL=3600 # Chỉ pull mỗi 1 tiếng để tránh náo động

# Load environment variables
export CLOUDFLARE_API_TOKEN="ZGmz0rgZp4l8q8YYp8Qo9nDpu-rJbbg0QnxCkWVu"
export TELEGRAM_BOT_TOKEN="8405197398:AAHuuykECSxEGZaBZVhtvwyIWM84LtGLO5I"
export TELEGRAM_CHAT_ID="5503922921"
export TOM_HUM_PANE_COUNT="4"
export TOM_HUM_HOURLY_BUDGET="30"

echo $$ > "$PID_FILE"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

notify() {
  log "📣 Notify: $1"
  curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
    -H "Content-Type: application/json" \
    -d "{\"chat_id\":\"${TELEGRAM_CHAT_ID}\",\"text\":\"🦞 OpenClaw Deep Loop\n\n$1\"}" > /dev/null || true
}

# --- PROCESS MANAGEMENT ---

check_process() {
  pgrep -f "$1" > /dev/null
}

start_bridge() {
  log "🌉 Starting bridge-server.js..."
  cd "$APP_DIR"
  pkill -f "bridge-server.js" || true
  nohup node bridge-server.js >> /tmp/bridge.log 2>&1 &
  sleep 3 # Đợi bridge lên hẳn
}

start_watcher() {
  log "👀 Starting task-watcher.js..."
  cd "$APP_DIR"
  pkill -f "task-watcher.js" || true
  nohup node task-watcher.js >> /tmp/watcher.log 2>&1 &
  sleep 2
}

start_tunnel() {
  log "📡 Starting Serveo Tunnel (SSH)..."
  pkill -f "ssh.*serveo.net" || true
  
  # Start SSH Tunnel
  nohup ssh -o StrictHostKeyChecking=no -R 80:localhost:8765 serveo.net > /tmp/tunnel_serveo.log 2>&1 &
  
  # Đợi 5s lấy URL
  sleep 5
  local tunnel_url=$(grep -o 'https://[a-z0-9-]*\.serveo\.net' /tmp/tunnel_serveo.log | head -n 1)
  
  if [ -n "$tunnel_url" ]; then
    log "✅ Tunnel Online: $tunnel_url"
    echo "$tunnel_url" | CLOUDFLARE_API_TOKEN="$CLOUDFLARE_API_TOKEN" \
      /opt/homebrew/bin/wrangler secret put BRIDGE_URL --force > /dev/null 2>&1 && \
      log "🔑 Secret updated"
    notify "Bridge is ONLINE (Serveo)!\n$tunnel_url"
  else
    log "⚠️ Tunnel URL not found yet (check /tmp/tunnel_serveo.log)"
  fi
}

# --- MAIN LOOP ---

log "🚀 TOM HUM DEEP SUPERVISOR ONLINE (v31.0 - NO PROXY)"

# Check Bridge Health
if ! curl -s -m 5 "$HEALTH_URL" > /dev/null; then
  start_bridge
  start_tunnel
fi

if ! check_process "task-watcher.js"; then
  start_watcher
fi

LAST_GIT_PULL=$(date +%s)

while true; do
  NOW=$(date +%s)

  # 1. Check Bridge Health (HTTP)
  if ! curl -s -m 5 "$HEALTH_URL" > /dev/null; then
    log "❌ Bridge unresponsive at $HEALTH_URL"
    start_bridge
    start_tunnel
  fi

  # 2. Check Task Watcher (Process)
  if ! check_process "task-watcher.js"; then
    log "❌ task-watcher.js died"
    start_watcher
  fi

  # 3. Check SSH Tunnel (Process)
  if ! check_process "ssh.*serveo.net"; then
    log "❌ Serveo SSH died"
    start_tunnel
  fi

  # 4. Periodic Git Pull
  if [ $((NOW - LAST_GIT_PULL)) -ge $GIT_PULL_INTERVAL ]; then
    log "📦 Checking for updates..."
    cd "$MEKONG_DIR"
    git fetch origin main > /dev/null 2>&1
    LOCAL=$(git rev-parse HEAD)
    REMOTE=$(git rev-parse @{u})
    if [ "$LOCAL" != "$REMOTE" ]; then
      log "✨ Updates found! Re-basing and restarting..."
      git pull --rebase > /dev/null 2>&1
      notify "Updates applied. Restarting for deep-sync."
      start_bridge
      start_watcher
      start_tunnel
    fi
    LAST_GIT_PULL=$NOW
  fi

  sleep "$INTERVAL"
done
