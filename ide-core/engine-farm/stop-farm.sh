#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.env"

WAIT_TIMEOUT=15

stop_server() {
  local name="$1"
  local port="$2"
  local pidfile="${PID_DIR}/mekong-farm-${port}.pid"

  if [[ ! -f "$pidfile" ]]; then
    echo "[farm] $name: no pid file at $pidfile, skipping."
    return
  fi

  local pid
  pid="$(cat "$pidfile")"

  if ! kill -0 "$pid" 2>/dev/null; then
    echo "[farm] $name: process $pid already stopped."
    rm -f "$pidfile"
    return
  fi

  echo "[farm] Stopping $name (pid $pid)..."
  kill -TERM "$pid"

  local elapsed=0
  while kill -0 "$pid" 2>/dev/null && [[ $elapsed -lt $WAIT_TIMEOUT ]]; do
    sleep 1
    elapsed=$((elapsed + 1))
  done

  if kill -0 "$pid" 2>/dev/null; then
    echo "[farm] WARNING: $name (pid $pid) did not stop after ${WAIT_TIMEOUT}s, sending SIGKILL."
    kill -KILL "$pid" 2>/dev/null || true
  else
    echo "[farm] $name stopped (${elapsed}s)."
  fi

  rm -f "$pidfile"
}

echo "[farm] === Mekong Engine Farm — Stopping ==="

stop_server "audit"     "$AUDIT_PORT"
stop_server "reasoning" "$REASONING_PORT"
stop_server "router"    "$ROUTER_PORT"

echo "[farm] === All servers stopped ==="
