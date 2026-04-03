#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.env"

all_healthy=true

check_server() {
  local name="$1"
  local port="$2"
  local url="http://${FARM_HOST}:${port}/v1/models"

  if curl -sf --max-time 5 "$url" > /dev/null 2>&1; then
    echo "[health] $name (port $port): OK"
  else
    echo "[health] $name (port $port): UNREACHABLE"
    all_healthy=false
  fi
}

echo "[health] === Mekong Engine Farm — Health Check ==="

check_server "router"    "$ROUTER_PORT"
check_server "reasoning" "$REASONING_PORT"
check_server "audit"     "$AUDIT_PORT"

if $all_healthy; then
  echo "[health] === All servers healthy ==="
  exit 0
else
  echo "[health] === One or more servers unreachable ==="
  exit 1
fi
