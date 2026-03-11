#!/bin/bash
# Send message from Antigravity to Telegram
# Usage: ./telegram-notify.sh "Your message here"

TELEGRAM_BOT_TOKEN="8405197398:AAHuuykECSxEGZaBZVhtvwyIWM84LtGLO5I"
TELEGRAM_CHAT_ID="5503922921"

MESSAGE="$1"

if [ -z "$MESSAGE" ]; then
  echo "Usage: ./telegram-notify.sh \"message\""
  exit 1
fi

curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  -H "Content-Type: application/json" \
  -d "{
    \"chat_id\": \"${TELEGRAM_CHAT_ID}\",
    \"text\": \"${MESSAGE}\",
    \"parse_mode\": \"Markdown\"
  }" > /dev/null

echo "✅ Sent to Telegram"
