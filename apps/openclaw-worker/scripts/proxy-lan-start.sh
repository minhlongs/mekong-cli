#!/bin/bash
# 🦞 PROXY LAN AUTO-CONNECT (Antigravity Ecosystem)
# Forces clean startup of Proxy Router (20128) + Backends (9191, 9192)
# Ensures LAN-like connectivity for CC CLI, CTO, and Antigravity IDE
# Prevents "Sock-hopping" deadlocks and overheating loops.

set -e

LOG="/tmp/tomcat_proxy_lan.log"
timestamp() { date '+%Y-%m-%d %H:%M:%S'; }
log() { echo "[$(timestamp)] $1" | tee -a "$LOG"; }

log "🦞 INIT: Starting Proxy LAN Auto-Connect Sequence..."

# 1. Stop existing service cleanly via launchctl
log "💥 NUKE: Unloading com.antigravity.proxy via launchctl..."
launchctl unload -w ~/Library/LaunchAgents/com.antigravity.proxy.plist 2>/dev/null || true
pkill -9 -f "antigravity-claude-proxy" 2>/dev/null || true
pkill -9 -f "node.*20128|node.*9191|node.*9192" 2>/dev/null || true
sleep 1

# Force free ports if still stuck
for port in 20128 9191 9192; do
  pid=$(lsof -t -i :$port 2>/dev/null || true)
  if [ -n "$pid" ]; then
    log "⚠️ FORCE FREE: Killing PID $pid stuck on port $port"
    kill -9 $pid 2>/dev/null || true
  fi
done
sleep 1

# 2. Start Proxy Hub via launchctl
log "🚀 LAUNCH: Starting com.antigravity.proxy via launchd..."
launchctl load -w ~/Library/LaunchAgents/com.antigravity.proxy.plist
log "✅ PROXY Hub restarted by macOS launchd"

# 3. Health Checks
log "🩺 HEALTH: Verifying LAN connectivity..."
MAX_WAIT=15
WAIT_COUNT=0
HEALTHY=0

while [ $WAIT_COUNT -lt $MAX_WAIT ]; do
  if curl -sf --connect-timeout 2 http://localhost:20128/health >/dev/null; then
    log "✅ ALIVE: Router Port 20128 online"
    HEALTHY=1
    break
  fi
  sleep 1
  WAIT_COUNT=$((WAIT_COUNT + 1))
done

if [ $HEALTHY -eq 1 ]; then
  log "🦞 SUCCESS: Proxy LAN is Fully Operational (Port 20128)"
  exit 0
else
  log "❌ FAILURE: Proxy Router 20128 failed to respond within 15s"
  exit 1
fi
