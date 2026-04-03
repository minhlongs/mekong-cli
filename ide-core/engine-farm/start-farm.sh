#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.env"

# Timeout in seconds to wait for each server to become healthy
HEALTH_TIMEOUT=120
HEALTH_INTERVAL=5

# --- Helpers ---

pid_file() {
  echo "${PID_DIR}/mekong-farm-${1}.pid"
}

start_server() {
  local name="$1"
  local model="$2"
  local port="$3"
  local max_tokens="$4"
  local context="$5"

  local pidfile
  pidfile="$(pid_file "$port")"

  # Kill stale process if pid file exists
  if [[ -f "$pidfile" ]]; then
    local old_pid
    old_pid="$(cat "$pidfile")"
    if kill -0 "$old_pid" 2>/dev/null; then
      echo "[farm] $name already running (pid $old_pid), skipping."
      return
    else
      rm -f "$pidfile"
    fi
  fi

  echo "[farm] Starting $name on port $port (model: $model)..."

  python3.11 -m mlx_lm server \
      --model "$model" \
      --max-tokens "$max_tokens" \
      --host "$FARM_HOST" \
      --port "$port" \
    > "/tmp/mekong-farm-${port}.log" 2>&1 &

  echo $! > "$pidfile"
  echo "[farm] $name started (pid $!, log: /tmp/mekong-farm-${port}.log)"
}

wait_healthy() {
  local name="$1"
  local port="$2"
  local url="http://${FARM_HOST}:${port}/v1/models"
  local elapsed=0

  echo "[farm] Waiting for $name health check at $url..."

  while [[ $elapsed -lt $HEALTH_TIMEOUT ]]; do
    if curl -sf "$url" > /dev/null 2>&1; then
      echo "[farm] $name is healthy (${elapsed}s)"
      return 0
    fi

    # Check process is still alive
    local pidfile
    pidfile="$(pid_file "$port")"
    if [[ -f "$pidfile" ]]; then
      local pid
      pid="$(cat "$pidfile")"
      if ! kill -0 "$pid" 2>/dev/null; then
        echo "[farm] ERROR: $name process (pid $pid) died. Check /tmp/mekong-farm-${port}.log"
        return 1
      fi
    fi

    sleep "$HEALTH_INTERVAL"
    elapsed=$((elapsed + HEALTH_INTERVAL))
  done

  echo "[farm] ERROR: $name did not become healthy within ${HEALTH_TIMEOUT}s"
  return 1
}

# --- Start all servers ---

echo "[farm] === Mekong Engine Farm — Starting ==="

start_server "router"    "$ROUTER_MODEL"    "$ROUTER_PORT"    "$ROUTER_MAX_TOKENS"    "$ROUTER_CONTEXT"
start_server "reasoning" "$REASONING_MODEL" "$REASONING_PORT" "$REASONING_MAX_TOKENS" "$REASONING_CONTEXT"
start_server "audit"     "$AUDIT_MODEL"     "$AUDIT_PORT"     "$AUDIT_MAX_TOKENS"     "$AUDIT_CONTEXT"

# --- Health checks (sequential — each model loads large weights) ---

wait_healthy "router"    "$ROUTER_PORT"    || exit 1
wait_healthy "reasoning" "$REASONING_PORT" || exit 1
wait_healthy "audit"     "$AUDIT_PORT"     || exit 1

echo "[farm] === All servers healthy ==="
echo "[farm]   router    http://${FARM_HOST}:${ROUTER_PORT}"
echo "[farm]   reasoning http://${FARM_HOST}:${REASONING_PORT}"
echo "[farm]   audit     http://${FARM_HOST}:${AUDIT_PORT}"
