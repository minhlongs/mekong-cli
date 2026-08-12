#!/usr/bin/env bash
set -euo pipefail

MODEL_PATH="${LLAMA_MODEL_PATH:-$(pwd)/models/qwen3.6-35b-instruct-q4_k_m.gguf}"

if [[ ! -f "$MODEL_PATH" ]]; then
  echo "Error: Model file not detected at $MODEL_PATH"
  exit 1
fi

exec llama-server \
  --model "$MODEL_PATH" \
  --host 127.0.0.1 \
  --port 8080 \
  --threads 8 \
  --ctx-size 40960 \
  --n-gpu-layers 99 \
  --no-mmap \
  --flash-attn
