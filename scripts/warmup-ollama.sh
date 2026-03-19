#!/bin/bash
# Warmup Ollama — load model into VRAM before daemon starts
# Usage: bash scripts/warmup-ollama.sh
set -uo pipefail

OLLAMA_URL="${OLLAMA_BASE_URL:-http://127.0.0.1:11434}"
MODEL="${OPENCLAW_WORKER_MODEL:-qwen3:32b}"

echo "Warming up Ollama ${MODEL}..."

# Check if Ollama is running
if ! curl -s "${OLLAMA_URL}/api/tags" >/dev/null 2>&1; then
  echo "Ollama not running at ${OLLAMA_URL}. Starting..."
  ollama serve &>/dev/null &
  sleep 3
fi

# Send minimal request to load model into VRAM
RESP=$(curl -s --max-time 120 "${OLLAMA_URL}/api/generate" \
  -d "{\"model\":\"${MODEL}\",\"prompt\":\"hello\",\"stream\":false,\"keep_alive\":\"24h\",\"options\":{\"num_predict\":1}}" 2>/dev/null)

if echo "$RESP" | grep -q "response"; then
  echo "✅ ${MODEL} loaded and warm (keep_alive=24h)"
else
  echo "⚠️  ${MODEL} warmup failed. Brain dispatch will use fallback tasks."
  # Try to pull model if not found
  if echo "$RESP" | grep -qi "not found"; then
    echo "Pulling ${MODEL}..."
    ollama pull "$MODEL" &
  fi
fi
