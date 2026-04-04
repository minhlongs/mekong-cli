#!/bin/bash
# Shared Inference Health Check — IDE-Core + CashClaw
set -uo pipefail

check() {
  local name="$1" port="$2"
  if curl -sf --max-time 3 "http://localhost:${port}/v1/models" > /dev/null 2>&1; then
    echo "  $name :$port — OK"
  else
    echo "  $name :$port — OFFLINE"
  fi
}

echo "═══ Shared Inference Health ═══"
echo ""
echo "IDE-Core Engine Farm:"
check "Gemma 4 (Router)"     4001
check "DeepSeek R1 (Reason)" 4002
check "Qwen 2.5 (Audit)"    4003

echo ""
echo "CashClaw Engines:"
check "DeepSeek R1 (Trading)" 11435
check "Nemotron 30B (Triage)" 11436

echo ""
echo "Memory Usage:"
ps aux | grep -E "mlx_lm|ollama" | grep -v grep | awk '{printf "  %-40s %dMB\n", $11, $6/1024}' 2>/dev/null || echo "  No MLX/Ollama processes found"

echo ""
if [ -n "${REASONING_PORT:-}" ]; then
  echo "Sharing Mode: ACTIVE (REASONING_PORT=$REASONING_PORT)"
else
  echo "Sharing Mode: DISABLED (default port 4002)"
fi

echo ""
echo "To enable sharing: export REASONING_PORT=11435"
echo "Or start farm with: ./ide-core/engine-farm/start-farm.sh --share-reasoning"
