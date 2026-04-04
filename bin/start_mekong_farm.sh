#!/bin/bash
# Mekong CLI — Ollama Engine Farm Launcher
# Usage: bin/start_mekong_farm.sh [--dev|--prod]
#
# Starts Ollama with the right models for the current environment.
# Dev:  qwen3:30b-a3b + deepseek-r1:32b (M1 Max 64GB, max reasoning)
# Prod: qwen2.5:14b + nemotron:12b (customer B2B, low RAM)
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Parse flags
case "${1:-}" in
  --prod|--production) export MEKONG_ENV=production ;;
  --dev|--development) export MEKONG_ENV=development ;;
esac

exec bash "$ROOT_DIR/ide-core/engine-farm/start-farm.sh"
