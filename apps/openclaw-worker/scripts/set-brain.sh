#!/bin/bash
# scripts/set-brain.sh
# Usage: ./scripts/set-brain.sh https://xxxx.serveo.net

URL=$1

if [ -z "$URL" ]; then
  echo "❌ Error: Missing URL."
  echo "Usage: npm run set-brain <url>"
  exit 1
fi

echo "🦞 Connecting to new Brain: $URL..."

# 1. Update .env (Create if missing)
if [ ! -f .env ]; then
  touch .env
fi

# Remove old entry if exists (macOS sed)
sed -i '' '/CLOUD_BRAIN_URL/d' .env
echo "CLOUD_BRAIN_URL=$URL" >> .env

# 2. Kill stale processes (Vitest, Scribe) to forcing reload config
echo "🧹 Cleaning up old thoughts..."
pkill -f "vitest" || true
pkill -f "scribe-daemon" || true

# 3. Verify Connection
echo "📡 Pinging Brain..."
curl -s "$URL/api/tags" > /dev/null

if [ $? -eq 0 ]; then
  echo "✅ Brain Connected Successfully! (200 OK)"
  echo "🧠 Model: Qwen3-Coder-Next (Ready)"
else
  echo "⚠️ Warning: Brain not reachable yet. Check Colab tunnel."
fi
