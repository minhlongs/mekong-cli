#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.env"

echo "[farm] === Mekong Engine Farm — Stopping ==="

# Unload all models from memory
if command -v ollama &>/dev/null; then
  running=$(ollama ps 2>/dev/null | tail -n +2 | awk '{print $1}')
  if [[ -n "$running" ]]; then
    while IFS= read -r model; do
      echo "[farm] Unloading $model..."
      curl -sf "${OLLAMA_API}/api/generate" \
        -d "{\"model\":\"${model}\",\"keep_alive\":0}" \
        >/dev/null 2>&1 || true
    done <<< "$running"
  fi
fi

# Stop Ollama server if we started it
if [[ -f /tmp/mekong-ollama.pid ]]; then
  pid=$(cat /tmp/mekong-ollama.pid)
  if kill -0 "$pid" 2>/dev/null; then
    echo "[farm] Stopping Ollama server (pid $pid)..."
    kill -TERM "$pid" 2>/dev/null || true
    sleep 2
    kill -0 "$pid" 2>/dev/null && kill -KILL "$pid" 2>/dev/null || true
  fi
  rm -f /tmp/mekong-ollama.pid
fi

echo "[farm] === Engine Farm Stopped ==="
