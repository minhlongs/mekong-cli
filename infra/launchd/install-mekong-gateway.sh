#!/usr/bin/env bash
# Install Mekong Gateway as macOS LaunchDaemon (boot-resilient, system-level).
#
# Usage:
#   ./install-mekong-gateway.sh                # auto-detect project dir, reuse/generate token
#   ./install-mekong-gateway.sh /path/to/mekong-cli
#
# Token handling:
#   - If ~/.mekong/admin-token.txt exists → reuse it (rotation requires manual delete first).
#   - Else → generate fresh 32-byte URL-safe token via python3 secrets, save to ~/.mekong/admin-token.txt (mode 600).
#
# Requires: sudo (writes to /Library/LaunchDaemons/), .venv/bin/uvicorn in project dir.

set -euo pipefail

PLIST_TARGET="/Library/LaunchDaemons/com.mekong.gateway.plist"
PLIST_TEMPLATE="$(cd "$(dirname "$0")" && pwd)/com.mekong.gateway.plist"

# 1. Resolve project dir (arg > template parent's grandparent > cwd)
PROJECT_DIR="${1:-}"
if [ -z "$PROJECT_DIR" ]; then
  # template lives in <project>/infra/launchd/, so grandparent = project root
  PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
fi
if [ ! -d "$PROJECT_DIR" ]; then
  echo "❌ Project dir not found: $PROJECT_DIR"
  exit 1
fi

# 2. Validate uvicorn binary
UVICORN_BIN="$PROJECT_DIR/.venv/bin/uvicorn"
if [ ! -x "$UVICORN_BIN" ]; then
  echo "❌ uvicorn not found at $UVICORN_BIN"
  echo "   Install: cd $PROJECT_DIR && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
  exit 1
fi

# 3. Resolve / generate admin token
TOKEN_DIR="$HOME/.mekong"
TOKEN_FILE="$TOKEN_DIR/admin-token.txt"
mkdir -p "$TOKEN_DIR"
chmod 700 "$TOKEN_DIR"
if [ -f "$TOKEN_FILE" ]; then
  echo "🔑 Reusing existing token: $TOKEN_FILE"
  TOKEN=$(cat "$TOKEN_FILE")
else
  echo "🆕 Generating new admin token → $TOKEN_FILE"
  TOKEN=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
  printf '%s' "$TOKEN" > "$TOKEN_FILE"
  chmod 600 "$TOKEN_FILE"
fi
if [ -z "$TOKEN" ] || [ "${#TOKEN}" -lt 32 ]; then
  echo "❌ Admin token invalid (length=${#TOKEN}, need ≥32)"
  exit 1
fi

# 4. Interpolate template → temp file
TMP=$(mktemp)
# Use # delimiter for sed because TOKEN may contain / or _ (URL-safe base64)
sed -e "s#__USER_HOME__#$HOME#g" \
    -e "s#__PROJECT_DIR__#$PROJECT_DIR#g" \
    -e "s#__MEKONG_ADMIN_TOKEN__#$TOKEN#g" \
    "$PLIST_TEMPLATE" > "$TMP"

# 5. Validate XML before install
if ! plutil -lint "$TMP" >/dev/null; then
  echo "❌ Generated plist failed XML validation"
  rm "$TMP"
  exit 1
fi

# 6. Backup existing plist (if any)
if [ -f "$PLIST_TARGET" ]; then
  BACKUP="${PLIST_TARGET}.bak-$(date +%y%m%d-%H%M%S)"
  echo "📦 Backing up existing plist → $BACKUP"
  sudo cp "$PLIST_TARGET" "$BACKUP"
fi

# 7. Install
echo "📥 Installing $PLIST_TARGET (project: $PROJECT_DIR)"
sudo cp "$TMP" "$PLIST_TARGET"
sudo chown root:wheel "$PLIST_TARGET"
sudo chmod 644 "$PLIST_TARGET"
rm "$TMP"

# 8. (Re)load service
sudo launchctl bootout system "$PLIST_TARGET" 2>/dev/null || true
sudo launchctl bootstrap system "$PLIST_TARGET"
sudo launchctl kickstart -k system/com.mekong.gateway

# 9. Verify
sleep 2
if sudo launchctl list | grep -q com.mekong.gateway; then
  echo "✅ Mekong Gateway LaunchDaemon active"
  echo "   Logs: /var/log/mekong-gateway.log, /var/log/mekong-gateway-err.log"
  echo "   Health: curl -s http://localhost:8000/healthz"
  echo "   Status: sudo launchctl list | grep mekong"
else
  echo "⚠️  Service started but not found in launchctl list. Check /var/log/mekong-gateway-err.log"
  exit 1
fi
