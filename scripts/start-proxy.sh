#!/bin/bash
# 🏯 Antigravity Proxy Starter
# Auto-start wrapper for LaunchAgent daemon

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"
export NODE_ENV="production"

# Fix for missing 'python' command (common in macOS Sonoma/Sequoia)
if ! command -v python &> /dev/null && command -v python3 &> /dev/null; then
  mkdir -p "$HOME/.antigravity/bin"
  ln -sf "$(which python3)" "$HOME/.antigravity/bin/python"
  export PATH="$HOME/.antigravity/bin:$PATH"
fi

# Log location
LOG_DIR="$HOME/.mekong/logs"
mkdir -p "$LOG_DIR"

echo "[$(date)] Starting Antigravity Proxy..." >> "$LOG_DIR/proxy.log"

# Start proxy (blocking - LaunchAgent will manage lifecycle)
exec antigravity-claude-proxy start --fallback 2>&1 | tee -a "$LOG_DIR/proxy.log"
