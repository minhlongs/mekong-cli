#!/bin/bash
# 🏦 Setup Polar Balance Checker Cron Job
# 
# This script sets up automatic balance checking every 6 hours
# and sends Telegram notification when balance is ready for withdrawal

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CHECKER_SCRIPT="$SCRIPT_DIR/polar-balance-checker.ts"

echo "🏦 Polar Balance Checker - Cron Setup"
echo "======================================"
echo ""

# Check if script exists
if [ ! -f "$CHECKER_SCRIPT" ]; then
    echo "❌ Error: polar-balance-checker.ts not found"
    exit 1
fi

echo "📋 Current crontab:"
crontab -l 2>/dev/null || echo "(empty)"
echo ""

# Create cron job entry
CRON_CMD="0 */6 * * * cd $SCRIPT_DIR/.. && /usr/local/bin/npx ts-node $CHECKER_SCRIPT >> /tmp/polar-balance.log 2>&1"

# Check if already exists
if crontab -l 2>/dev/null | grep -q "polar-balance-checker"; then
    echo "⚠️ Cron job already exists"
    echo ""
    echo "To remove: crontab -e"
else
    echo "➕ Adding cron job (every 6 hours)..."
    (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
    echo "✅ Cron job added!"
fi

echo ""
echo "📊 Schedule: Every 6 hours (0:00, 6:00, 12:00, 18:00)"
echo "📁 Log file: /tmp/polar-balance.log"
echo ""
echo "🔧 Environment variables needed:"
echo "   POLAR_ACCESS_TOKEN     - Your Polar.sh access token"
echo "   TELEGRAM_BOT_TOKEN     - (Optional) Telegram bot token"
echo "   TELEGRAM_CHAT_ID       - (Optional) Your Telegram chat ID"
echo ""
echo "🧪 Test manually:"
echo "   npx ts-node $CHECKER_SCRIPT"
echo ""
