#!/usr/bin/env bash
# Install cloudflared as macOS LaunchDaemon (boot-resilient, system-level).
#
# Usage:
#   ./install-cloudflared.sh                       # auto-detect tunnel ID from ~/.cloudflared/config.yml
#   ./install-cloudflared.sh <TUNNEL_UUID>         # specify tunnel ID explicitly
#
# Requires: sudo (writes to /Library/LaunchDaemons/), cloudflared binary.

set -euo pipefail

PLIST_TARGET="/Library/LaunchDaemons/com.cloudflare.cloudflared.plist"
PLIST_TEMPLATE="$(cd "$(dirname "$0")" && pwd)/com.cloudflare.cloudflared.plist"

# 1. Validate cloudflared binary
CLOUDFLARED_BIN="${CLOUDFLARED_BIN:-/opt/homebrew/bin/cloudflared}"
if [ ! -x "$CLOUDFLARED_BIN" ]; then
  echo "❌ cloudflared not found at $CLOUDFLARED_BIN"
  echo "   Install: brew install cloudflared"
  exit 1
fi

# 2. Resolve tunnel ID (arg > config.yml)
TUNNEL_ID="${1:-}"
if [ -z "$TUNNEL_ID" ] && [ -f "$HOME/.cloudflared/config.yml" ]; then
  TUNNEL_ID=$(awk '/^tunnel:/ {print $2; exit}' "$HOME/.cloudflared/config.yml" | tr -d '"')
fi
if [ -z "$TUNNEL_ID" ]; then
  echo "❌ Tunnel ID required."
  echo "   Usage: $0 <TUNNEL_UUID>"
  echo "   Or set 'tunnel: <UUID>' in ~/.cloudflared/config.yml"
  exit 1
fi

# 3. Validate config.yml exists
CONFIG_FILE="$HOME/.cloudflared/config.yml"
if [ ! -f "$CONFIG_FILE" ]; then
  echo "❌ Missing $CONFIG_FILE"
  exit 1
fi

# 4. Interpolate template → temp file
TMP=$(mktemp)
sed -e "s|__USER_HOME__|$HOME|g" \
    -e "s|__TUNNEL_ID__|$TUNNEL_ID|g" \
    "$PLIST_TEMPLATE" > "$TMP"

# 5. Backup existing plist (if any)
if [ -f "$PLIST_TARGET" ]; then
  BACKUP="${PLIST_TARGET}.bak-$(date +%y%m%d-%H%M%S)"
  echo "📦 Backing up existing plist → $BACKUP"
  sudo cp "$PLIST_TARGET" "$BACKUP"
fi

# 6. Install
echo "📥 Installing $PLIST_TARGET (tunnel: $TUNNEL_ID)"
sudo cp "$TMP" "$PLIST_TARGET"
sudo chown root:wheel "$PLIST_TARGET"
sudo chmod 644 "$PLIST_TARGET"
rm "$TMP"

# 7. (Re)load service
sudo launchctl bootout system "$PLIST_TARGET" 2>/dev/null || true
sudo launchctl bootstrap system "$PLIST_TARGET"
sudo launchctl kickstart -k system/com.cloudflare.cloudflared

# 8. Verify
sleep 2
if sudo launchctl list | grep -q com.cloudflare.cloudflared; then
  echo "✅ cloudflared LaunchDaemon active"
  echo "   Logs: /Library/Logs/com.cloudflare.cloudflared.{out,err}.log"
  echo "   Status: sudo launchctl list | grep cloudflared"
else
  echo "⚠️  Service started but not found in launchctl list. Check logs."
  exit 1
fi
