#!/bin/bash
# OpenClaw Service - Bridge + Tunnel combined
# Run at boot: launchctl load ~/Library/LaunchAgents/com.openclaw.bridge.plist

export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

cd /Users/macbookprom1/mekong-cli/apps/openclaw-worker

CLOUDFLARE_API_TOKEN="ZGmz0rgZp4l8q8YYp8Qo9nDpu-rJbbg0QnxCkWVu"
TELEGRAM_BOT_TOKEN="8405197398:AAHuuykECSxEGZaBZVhtvwyIWM84LtGLO5I"
TELEGRAM_CHAT_ID="5503922921"
CLOUDFLARED="/opt/homebrew/bin/cloudflared"
WRANGLER="/opt/homebrew/bin/wrangler"
NODE="/opt/homebrew/bin/node"

# Start bridge server in background
$NODE bridge-server.js &
BRIDGE_PID=$!
echo "🌉 Bridge started (PID: $BRIDGE_PID)"

# Start task watcher in background
$NODE task-watcher.js &
WATCHER_PID=$!
echo "👀 Task Watcher started (PID: $WATCHER_PID)"

sleep 2

# Start tunnel and auto-update secret
$CLOUDFLARED tunnel --url http://localhost:8765 2>&1 | while read line; do
  echo "$line"
  
  if echo "$line" | grep -q "trycloudflare.com"; then
    TUNNEL_URL=$(echo "$line" | grep -o 'https://[a-z-]*\.trycloudflare\.com')
    
    if [ -n "$TUNNEL_URL" ]; then
      echo "📡 Tunnel: $TUNNEL_URL"
      
      # Update secret
      echo "$TUNNEL_URL" | CLOUDFLARE_API_TOKEN="$CLOUDFLARE_API_TOKEN" \
        wrangler secret put BRIDGE_URL --force 2>/dev/null && \
        echo "✅ Secret updated"
      
      # Notify
      curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
        -H "Content-Type: application/json" \
        -d "{\"chat_id\":\"${TELEGRAM_CHAT_ID}\",\"text\":\"🌉 OpenClaw Bridge Online!\n\n${TUNNEL_URL}\"}" > /dev/null
    fi
  fi
done

# Cleanup on exit
trap "kill $BRIDGE_PID $WATCHER_PID 2>/dev/null" EXIT
