#!/usr/bin/env bash
# Mekong CLI — Install dept-finance
set -euo pipefail

DEPT_ID="dept-finance"
DEPT_NAME="finance"
MEKONG_HOME="${MEKONG_HOME:-$HOME/mekong-cli}"
ENV_FILE="$MEKONG_HOME/.mekong/.env.$DEPT_ID"

check_mekong() {
  if ! command -v mekong &>/dev/null && [ ! -f "$MEKONG_HOME/scripts/shell-init.sh" ]; then
    echo "ERROR: mekong-cli not found. Install: https://mekongmind.com"
    exit 1
  fi
  echo "mekong-cli found at $MEKONG_HOME"
}

validate_manifest() {
  local manifest="$(dirname "$0")/manifest.json"
  if command -v python3 &>/dev/null; then
    python3 -c "import json; json.load(open('$manifest'))" && echo "manifest.json: valid JSON"
  fi
}

setup_env() {
  mkdir -p "$MEKONG_HOME/.mekong"
  if [ ! -f "$ENV_FILE" ]; then
    echo "# $DEPT_ID configuration" > "$ENV_FILE"
    echo "# Edit this file to configure your department" >> "$ENV_FILE"
    echo "Created $ENV_FILE — edit with your credentials"
  else
    echo "Config exists: $ENV_FILE"
  fi
}

dry_run() {
  echo ""
  echo "=== DRY RUN: $DEPT_ID ==="
  echo "Commands available: finance-budget-plan,finance-monthly-close,finance-collections"
  echo "Skills available: finance-accounting,finance-agent"
  echo 'Pricing: $10.00 per finance_deliverable (floor $49/mo)'
  echo "Config file: $ENV_FILE"
  echo ""
  echo "To start: source $MEKONG_HOME/scripts/shell-init.sh"
  echo "First command: mekong $(echo 'finance-budget-plan,finance-monthly-close,finance-collections' | cut -d',' -f1)"
  echo "=== DRY RUN COMPLETE ==="
}

main() {
  local mode="${1:-install}"
  local dry_mode="${2:-}"
  echo "Mekong CLI — Installing $DEPT_ID"
  check_mekong
  validate_manifest
  setup_env
  if [ "$mode" = "--dry-run" ]; then
    dry_run
  else
    echo ""
    echo "$DEPT_ID installed successfully."
    echo "Config: $ENV_FILE"
    echo "Docs: $(dirname "$0")/README.md"
    echo ""
    echo "Next: edit $ENV_FILE then run:"
    echo "  mekong $(echo 'finance-budget-plan,finance-monthly-close,finance-collections' | cut -d',' -f1)"
  fi
}

main "$@"
