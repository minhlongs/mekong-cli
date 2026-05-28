#!/bin/bash
# Verify files exist and have content
# Usage: ./verify-files.sh file1.ts file2.py ...
# Exit 0 if ALL files exist and are non-empty, exit 1 otherwise

set -e
FAILED=0

if [ $# -eq 0 ]; then
    echo "Usage: $0 <file1> [file2] ..." >&2
    exit 1
fi

for f in "$@"; do
    if [ ! -f "$f" ]; then
        echo "[FAIL] $f does not exist" >&2
        FAILED=1
    elif [ ! -s "$f" ]; then
        echo "[FAIL] $f is empty" >&2
        FAILED=1
    else
        LINES=$(wc -l < "$f")
        echo "[OK] $f ($LINES lines)"
    fi
done

exit $FAILED
