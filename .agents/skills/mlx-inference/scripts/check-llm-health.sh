#!/bin/bash
# Check health of both MLX LLM servers on M1 Max
# Usage: ./check-llm-health.sh

DEEPSEEK_URL="${LLM_DEEPSEEK_URL:-http://127.0.0.1:11435/v1}"
NEMOTRON_URL="${LLM_NEMOTRON_URL:-http://127.0.0.1:11436/v1}"

echo "[mlx] Checking LLM server health..."

if curl -sf "$DEEPSEEK_URL/models" > /dev/null 2>&1; then
    echo "[mlx] DeepSeek R1 (:11435) — healthy"
else
    echo "[mlx] DeepSeek R1 (:11435) — UNREACHABLE" >&2
fi

if curl -sf "$NEMOTRON_URL/models" > /dev/null 2>&1; then
    echo "[mlx] Nemotron Nano (:11436) — healthy"
else
    echo "[mlx] Nemotron Nano (:11436) — UNREACHABLE" >&2
fi
