#!/bin/bash
# ==============================================================================
# mekong-ai-os.sh — Unified entry point for Mekong AI OS operational scripts
# Source this file to expose all shell functions:
#   source mekong/adapters/mekong-ai-os.sh
# ==============================================================================

set -euo pipefail

MEKONG_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Banner ─────────────────────────────────────────────────
echo "  ╔══════════════════════════════════════════════╗"
echo "  ║     Mekong AI OS — Operational Scripts       ║"
echo "  ╚══════════════════════════════════════════════╝"
echo "  Scripts dir: ${MEKONG_SCRIPT_DIR}"
echo ""

# ── Aliases ────────────────────────────────────────────────

# Model routing
mekong-route() {
  bash "${MEKONG_SCRIPT_DIR}/model-router.sh" "$@"
}

# System health
mekong-health() {
  bash "${MEKONG_SCRIPT_DIR}/health-check.sh" "$@"
}

# Intent classification
mekong-classify() {
  node "${MEKONG_SCRIPT_DIR}/intent-router.cjs" "$@"
}

# Deploy models
mekong-deploy-models() {
  bash "${MEKONG_SCRIPT_DIR}/deploy-models.sh" "$@"
}

# Memory inspection
mekong-memory() {
  node "${MEKONG_SCRIPT_DIR}/memory-inspector.js" "$@"
}

# Observability reports
mekong-observe() {
  node "${MEKONG_SCRIPT_DIR}/observability-report.js" "$@"
}

# Error logging
mekong-log-error() {
  node "${MEKONG_SCRIPT_DIR}/log-error.js" "$@"
}

# Token usage logging
mekong-log-tokens() {
  node "${MEKONG_SCRIPT_DIR}/log-token-usage.js" "$@"
}

# Agent tracing
mekong-trace() {
  node "${MEKONG_SCRIPT_DIR}/trace-agent.js" "$@"
}

# AI OS MCP server
mekong-ai-os() {
  python3 -m src.core.mcp_server "$@"
}

# ── Composite commands ──────────────────────────────────────

# Full health report (all checks + observability summary)
mekong-status() {
  echo ""
  echo "═══ Mekong AI OS — Full Status ═══"
  echo ""

  echo "── Health Check ──"
  bash "${MEKONG_SCRIPT_DIR}/health-check.sh" || true
  echo ""

  echo "── Token Usage Today ──"
  node "${MEKONG_SCRIPT_DIR}/observability-report.js" today 2>/dev/null || echo "  (no data)"
  echo ""

  echo "── Recent Errors ──"
  node "${MEKONG_SCRIPT_DIR}/observability-report.js" errors --recent 2>/dev/null || echo "  (no errors)"
  echo ""
}

# Quick classify + route
mekong-go() {
  if [ $# -eq 0 ]; then
    echo "Usage: mekong-go <request>"
    echo "Classifies and routes a request in one step."
    return 1
  fi

  local result
  result=$(node "${MEKONG_SCRIPT_DIR}/intent-router.cjs" "$*" 2>/dev/null)

  echo "Intent: $(echo "$result" | python3 -c "import sys,json; r=json.load(sys.stdin); print(r.get('domain','?')+'/'+r.get('mode','?')+'/'+r.get('complexity','?'))" 2>/dev/null || echo 'parse error')"
  echo "Agent:  $(echo "$result" | python3 -c "import sys,json; r=json.load(sys.stdin); print(r.get('agent','?'))" 2>/dev/null || echo 'parse error')"

  local mode
  mode=$(echo "$result" | python3 -c "import sys,json; r=json.load(sys.stdin); print(r.get('mode','cook'))" 2>/dev/null || echo 'cook')

  # Route to appropriate model tier
  case "$mode" in
    fix|debug)
      echo "→ Routing to: utility tier (7B)"
      bash "${MEKONG_SCRIPT_DIR}/model-router.sh" utility "$*"
      ;;
    test|review)
      echo "→ Routing to: coding tier (14B)"
      bash "${MEKONG_SCRIPT_DIR}/model-router.sh" coding "$*"
      ;;
    plan|deploy)
      echo "→ Routing to: strategic tier (35B)"
      bash "${MEKONG_SCRIPT_DIR}/model-router.sh" strategic "$*"
      ;;
    *)
      echo "→ Routing to: coding tier (14B)"
      bash "${MEKONG_SCRIPT_DIR}/model-router.sh" coding "$*"
      ;;
  esac
}

echo "  Commands loaded: mekong-route, mekong-health, mekong-classify,"
echo "                    mekong-deploy-models, mekong-memory, mekong-observe,"
echo "                    mekong-log-error, mekong-log-tokens, mekong-trace,"
echo "                    mekong-ai-os, mekong-status, mekong-go"
echo ""
