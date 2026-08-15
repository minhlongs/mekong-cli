#!/bin/bash
# install-codebase-memory.sh — Install codebase-memory-mcp MCP server
# Part of mekong init. Run: bash scripts/install-codebase-memory.sh

set -e

echo "🔌 Installing Codebase Memory MCP..."
echo ""

# Check if already installed
if command -v codebase-memory-mcp &>/dev/null; then
  echo "✅ codebase-memory-mcp already installed"
  codebase-memory-mcp --version 2>/dev/null || true
  exit 0
fi

# Install
echo "Downloading and installing..."
curl -fsSL https://raw.githubusercontent.com/DeusData/codebase-memory-mcp/main/install.sh | bash

# Verify
if command -v codebase-memory-mcp &>/dev/null; then
  echo "✅ Installed successfully"
  echo ""
  echo "To index current project:"
  echo "  codebase-memory-mcp --index ."
  echo ""
  echo "MCP config already in .mcp.json"
else
  echo "⚠️  Install script ran but binary not found in PATH"
  echo "   Try: curl -fsSL https://raw.githubusercontent.com/DeusData/codebase-memory-mcp/main/install.sh | bash"
fi
