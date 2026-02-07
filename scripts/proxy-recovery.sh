#!/bin/bash
# 🏯 Mekong-CLI Proxy Recovery Utility
# Purpose: Surgically reset rate-limit flags and restart the Antigravity Proxy.

ACCOUNTS_JSON="$HOME/.config/antigravity-proxy/accounts.json"
PLIST_PATH="$HOME/Library/LaunchAgents/com.antigravity.proxy.plist"

echo "🚀 Starting Autonomous Proxy Recovery..."

if [ ! -f "$ACCOUNTS_JSON" ]; then
    echo "❌ Error: accounts.json not found at $ACCOUNTS_JSON"
    exit 1
fi

# 1. Log quota consumption before reset
echo "📊 Pre-reset quota snapshot ($(date)):"
python3 -c "
import json
with open('$ACCOUNTS_JSON') as f:
    data = json.load(f)
for acc in data['accounts']:
    email = acc['email']
    tier = acc.get('subscription', {}).get('tier', '?')
    limited = [m for m, v in acc.get('modelRateLimits', {}).items() if v.get('isRateLimited')]
    consumed = [(m, q.get('remainingFraction', 1)) for m, q in acc.get('quota', {}).get('models', {}).items() if q.get('remainingFraction', 1) < 1]
    if limited or consumed:
        print(f'  {email} ({tier}):')
        for m in limited: print(f'    🔴 {m} — rate limited')
        for m, f in consumed: print(f'    📉 {m} — {f*100:.0f}% remaining')
    else:
        print(f'  {email} ({tier}): ✅ all clear')
"

# 2. Surgical Reset of flags
echo "⚒️  Surgically resetting rate-limit flags in accounts.json..."
sed -i '' 's/"isRateLimited": true/"isRateLimited": false/g' "$ACCOUNTS_JSON"
sed -i '' 's/"remainingFraction": 0/"remainingFraction": 1/g' "$ACCOUNTS_JSON"

# 3. Restart Service
if [ -f "$PLIST_PATH" ]; then
    echo "🔄 Restarting Antigravity Proxy service..."
    launchctl unload "$PLIST_PATH"
    launchctl load "$PLIST_PATH"
    echo "✅ Service restarted successfully."
else
    echo "⚠️  LaunchAgent plist not found. Please restart the proxy manually."
fi

echo "✨ Recovery complete. CC CLI should resume immediately."
