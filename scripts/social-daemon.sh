#!/bin/bash
# Mekong CLI — Social Daemon launcher for M1 Max
# Starts the social auto-poster + LLM reply daemon via PM2 or directly.
# Usage:
#   bash scripts/social-daemon.sh                 # default 60-min interval
#   bash scripts/social-daemon.sh --interval 30   # custom interval

set -euo pipefail

MEKONG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$MEKONG_DIR"

# Load environment variables
if [ -f ".env" ]; then
  # shellcheck disable=SC1091
  set -a && source .env && set +a
fi

INTERVAL="${1:-60}"
if [[ "$1" == "--interval" && -n "${2:-}" ]]; then
  INTERVAL="$2"
fi

echo "[social-daemon] Starting from $MEKONG_DIR (interval=${INTERVAL}m)"
exec python3 -m src.agents.social_daemon --interval "$INTERVAL"
