#!/bin/bash
# ============================================================
# 🦞 Tôm Hùm Telegram Bot — Persistent Launcher
# Auto-restart on crash. Run via launchctl or directly.
# ============================================================

set -euo pipefail

export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

cd /Users/macbookprom1/mekong-cli

# Load tokens
TELEGRAM_BOT_TOKEN="8405197398:AAHuuykECSxEGZaBZVhtvwyIWM84LtGLO5I"
TELEGRAM_CHAT_ID="5503922921"
GOOGLE_API_KEY="AIzaSyC79sMC-4fLacJDpDpGmFZKxvsvwZMC2IQ"

export MEKONG_TELEGRAM_TOKEN="$TELEGRAM_BOT_TOKEN"
export GOOGLE_API_KEY

LOG_FILE="$HOME/.mekong/logs/telegram-bot.log"
PID_FILE="$HOME/.mekong/telegram-bot.pid"
mkdir -p "$HOME/.mekong/logs"

# Kill any existing bot instances to prevent Conflict error
pkill -f "MekongBot" 2>/dev/null || true
pkill -f "start-telegram-bot" 2>/dev/null || true
sleep 2

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🦞 Starting Tôm Hùm Bot..." >> "$LOG_FILE"

# Auto-restart loop
MAX_RETRIES=100
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Attempt $((RETRY_COUNT+1))/$MAX_RETRIES" >> "$LOG_FILE"
    
    python3 -c "
import asyncio, signal, sys, os, traceback
os.environ['MEKONG_TELEGRAM_TOKEN'] = '$TELEGRAM_BOT_TOKEN'
os.environ['GOOGLE_API_KEY'] = '$GOOGLE_API_KEY'

from src.core.telegram_bot import MekongBot

async def main():
    bot = MekongBot()
    await bot.start()
    print(f'✅ Tôm Hùm Bot polling (PID {os.getpid()})', flush=True)
    
    # Write PID
    with open('$PID_FILE', 'w') as f:
        f.write(str(os.getpid()))
    
    # Notify user
    try:
        from telegram import Bot
        tg = Bot('$TELEGRAM_BOT_TOKEN')
        await tg.send_message(chat_id=$TELEGRAM_CHAT_ID, text='🦞 Tôm Hùm Bot online! Send /help for commands.')
    except: pass
    
    # Keep alive
    stop = asyncio.Event()
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, stop.set)
    await stop.wait()
    await bot.stop()

try:
    asyncio.run(main())
except KeyboardInterrupt:
    sys.exit(0)
except Exception as e:
    traceback.print_exc()
    sys.exit(1)
" >> "$LOG_FILE" 2>&1
    
    EXIT_CODE=$?
    RETRY_COUNT=$((RETRY_COUNT + 1))
    
    if [ $EXIT_CODE -eq 0 ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Bot stopped gracefully" >> "$LOG_FILE"
        break
    fi
    
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️ Bot crashed (exit $EXIT_CODE). Restarting in 5s..." >> "$LOG_FILE"
    sleep 5
done

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Bot launcher exiting" >> "$LOG_FILE"
