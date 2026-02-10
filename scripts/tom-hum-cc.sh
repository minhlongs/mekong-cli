#!/bin/bash
# ============================================================================
# 🦞 TÔM HÙM CC CLI GATEWAY — Stream JSON Mode
# 
# Run this in VS Code terminal to see CC CLI running live ("xe xịn").
# Tôm Hùm task-watcher sẽ feed missions qua /tmp/tom_hum_stream_in.jsonl
#
# Usage: bash /Users/macbookprom1/mekong-cli/scripts/tom-hum-cc.sh [project_dir]
# ============================================================================

set -e

PROJECT_DIR="${1:-/Users/macbookprom1/mekong-cli}"
INPUT_FILE="/tmp/tom_hum_stream_in.jsonl"
OUTPUT_LOG="/tmp/tom_hum_stream_out.jsonl"
PROXY_PORT=8080
MODEL="claude-opus-4-6-thinking"
API_KEY="sk-6219c93290f14b32b047342ca8b0bea9"

# Clean previous session
> "$INPUT_FILE"
> "$OUTPUT_LOG"

echo ""
echo "  🦞 ═══════════════════════════════════════════════"
echo "  🦞  TÔM HÙM CC CLI GATEWAY v17.0"
echo "  🦞  Model: $MODEL"
echo "  🦞  Proxy: http://127.0.0.1:$PROXY_PORT"
echo "  🦞  Project: $PROJECT_DIR"
echo "  🦞  Input: $INPUT_FILE"
echo "  🦞 ═══════════════════════════════════════════════"
echo ""
echo "  📡 Waiting for missions from task-watcher..."
echo "  📋 Format: {\"type\":\"user\",\"message\":{\"role\":\"user\",\"content\":\"...\"}}"
echo ""

cd "$PROJECT_DIR"

# tail -f keeps stdin open; claude -p processes each JSON line as a new turn
# tee logs all output to file while displaying in terminal
tail -f "$INPUT_FILE" | \
  ANTHROPIC_BASE_URL="http://127.0.0.1:$PROXY_PORT" \
  ANTHROPIC_API_KEY="$API_KEY" \
  claude -p \
  --model "$MODEL" \
  --dangerously-skip-permissions \
  --input-format stream-json \
  --output-format stream-json \
  --verbose \
  2>&1 | tee "$OUTPUT_LOG"
