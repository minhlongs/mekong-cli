#!/bin/bash
# Format review findings as markdown table
# Usage: echo '{"severity":"HIGH","file":"foo.ts","issue":"..."}' | ./format-review.sh
# Reads JSONL from stdin, outputs markdown table

echo "| Severity | File | Issue |"
echo "|----------|------|-------|"

while IFS= read -r line; do
    severity=$(echo "$line" | python3 -c "import sys,json; print(json.load(sys.stdin).get('severity','?'))" 2>/dev/null || echo "?")
    file=$(echo "$line" | python3 -c "import sys,json; print(json.load(sys.stdin).get('file','?'))" 2>/dev/null || echo "?")
    issue=$(echo "$line" | python3 -c "import sys,json; print(json.load(sys.stdin).get('issue','?'))" 2>/dev/null || echo "?")
    echo "| $severity | $file | $issue |"
done
