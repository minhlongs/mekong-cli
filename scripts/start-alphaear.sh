#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ALPHAEAR_DIR="$SCRIPT_DIR/../packages/alphaear"

echo "═══ AlphaEar — Financial ML Sidecar ═══"

# Check Python
python3 --version || { echo "ERROR: python3 not found"; exit 1; }

# Install deps if needed
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install -r "$ALPHAEAR_DIR/requirements.txt"
fi

echo "Starting on port 8100..."
cd "$ALPHAEAR_DIR"
exec uvicorn main:app --host 127.0.0.1 --port 8100 --reload
