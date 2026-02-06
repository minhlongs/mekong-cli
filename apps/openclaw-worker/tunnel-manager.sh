#!/bin/bash
# Tunnel Manager - Creates tunnel and auto-updates BRIDGE_URL secret
# Runs under PM2 for auto-restart

CLOUDFLARE_API_TOKEN="ZGmz0rgZp4l8q8YYp8Qo9nDpu-rJbbg0QnxCkWVu"
TELEGRAM_BOT_TOKEN="8405197398:AAHuuykECSxEGZaBZVhtvwyIWM84LtGLO5I"
TELEGRAM_CHAT_ID="5503922921"

cd /Users/macbookprom1/mekong-cli/apps/openclaw-worker

echo "🚀 Starting Cloudflare Tunnel..."

# Create tunnel and capture URL
cloudflared tunnel --url http://localhost:8765 2>&1 | while read line; do
  echo "$line"
  
  # Extract tunnel URL
  if echo "$line" | grep -q "trycloudflare.com"; then
    TUNNEL_URL=$(echo "$line" | grep -o 'https://[a-z-]*\.trycloudflare\.com')
    
    if [ -n "$TUNNEL_URL" ]; then
      echo "📡 Tunnel URL: $TUNNEL_URL"
      
      # Update Cloudflare secret
      echo "$TUNNEL_URL" | CLOUDFLARE_API_TOKEN="$CLOUDFLARE_API_TOKEN" wrangler secret put BRIDGE_URL --force 2>/dev/null
      
      # Notify via Telegram
      curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
        -H "Content-Type: application/json" \
        -d "{\"chat_id\": \"${TELEGRAM_CHAT_ID}\", \"text\": \"🌉 Bridge tunnel started!\n\n${TUNNEL_URL}\", \"parse_mode\": \"Markdown\"}" > /dev/null
      
      echo "✅ BRIDGE_URL secret updated!"
    fi
  fi
done
