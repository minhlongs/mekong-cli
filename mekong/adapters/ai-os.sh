#!/bin/bash
# ==============================================================================
# ai-os.sh — Mekong AI OS MCP Server Wrapper
# Calls the Python MCP server module from the mekong-cli project root.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT" || exit 1

exec python3 -m src.core.mcp_server "$@"
