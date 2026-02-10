#!/usr/bin/env bash
# Start Qwen Bridge Proxy on port 8081
# Converts Anthropic Messages API → DashScope OpenAI Chat Completions API
# Used by Tôm Hùm when TOM_HUM_ENGINE=qwen

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BRIDGE_PY="$SCRIPT_DIR/qwen_bridge.py"

if [ ! -f "$BRIDGE_PY" ]; then
  echo "ERROR: $BRIDGE_PY not found"
  exit 1
fi

# Check dependencies
if ! python3 -c "import flask, requests" 2>/dev/null; then
  echo "Installing dependencies: flask requests..."
  pip3 install flask requests
fi

echo "Starting Qwen Bridge on port 8081..."
exec python3 "$BRIDGE_PY"
