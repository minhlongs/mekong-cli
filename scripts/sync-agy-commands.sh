#!/usr/bin/env bash
set -euo pipefail

MEKONG_ROOT="${MEKONG_ROOT:-$(pwd)}"
OPENCODE_DIR="${OPENCODE_DIR:-$MEKONG_ROOT/.opencode/commands}"
GEMINI_DIR="${GEMINI_DIR:-$MEKONG_ROOT/.gemini/commands}"

SOURCE="$OPENCODE_DIR/cook-auto.md"
TARGET="$GEMINI_DIR/cook-auto.toml"

if [[ ! -f "$SOURCE" ]]; then
  echo "missing source command: $SOURCE" >&2
  exit 1
fi

mkdir -p "$GEMINI_DIR"
cat > "$TARGET" <<'EOF'
description = "Durable autonomous goal runner"

output = """
Returns status_command, resume_command, verify_command, status_json_command,
resume_json_command, verify_json_command, and accepts --auto for AGY mode.
"""

[steps.run]
command = "mekong mk-cook-auto {{args}} --profile smoke --auto"
EOF

echo "synced cook-auto -> $TARGET"
