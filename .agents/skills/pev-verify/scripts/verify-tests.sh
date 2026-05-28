#!/bin/bash
# Run test suite and verify exit code 0
# Usage: ./verify-tests.sh [test-command]
# Default: auto-detects pytest or npm test

set -e

CMD="${1:-}"

if [ -z "$CMD" ]; then
    if [ -f "pytest.ini" ] || [ -f "pyproject.toml" ] || [ -d "tests" ]; then
        CMD="python3 -m pytest tests/ -x -q"
    elif [ -f "package.json" ]; then
        CMD="npm test"
    else
        echo "[ERROR] Cannot auto-detect test framework" >&2
        exit 1
    fi
fi

echo "[verify] Running: $CMD"
eval "$CMD"
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "[verify] Tests PASSED (exit code 0)"
else
    echo "[verify] Tests FAILED (exit code $EXIT_CODE)" >&2
fi

exit $EXIT_CODE
