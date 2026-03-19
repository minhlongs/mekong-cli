#!/bin/bash
# ═══════════════════════════════════════════════════════════
# MEKONG-CLI WRAPPER — CC CLI runs INSIDE mekong-cli
# All 300+ commands loaded via .claude/commands/
# ═══════════════════════════════════════════════════════════
set -euo pipefail

MEKONG_ROOT="${MEKONG_ROOT:-$HOME/mekong-cli}"
PROVIDER="${MEKONG_PROVIDER:-claude}"    # claude|gemini|qwen|bb
MODE="${MEKONG_MODE:-interactive}"        # interactive|print|cto|continue

# ═══ Provider Config ═══
setup_provider() {
  case "$PROVIDER" in
    opus)
      # Anthropic Opus — Claude Max Auth (unset DashScope)
      unset ANTHROPIC_BASE_URL ANTHROPIC_API_KEY ANTHROPIC_MODEL 2>/dev/null
      unset ANTHROPIC_DEFAULT_OPUS_MODEL ANTHROPIC_DEFAULT_SONNET_MODEL 2>/dev/null
      unset ANTHROPIC_DEFAULT_HAIKU_MODEL ANTHROPIC_AUTH_TOKEN 2>/dev/null
      unset DASHSCOPE_API_KEY DASHSCOPE_API_KEYS 2>/dev/null
      BINARY="claude"
      EXTRA_ARGS="--model claude-opus-4-0520"
      ;;
    sonnet)
      # Anthropic Sonnet — Claude Max Auth
      unset ANTHROPIC_BASE_URL ANTHROPIC_API_KEY ANTHROPIC_MODEL 2>/dev/null
      unset ANTHROPIC_DEFAULT_OPUS_MODEL ANTHROPIC_DEFAULT_SONNET_MODEL 2>/dev/null
      unset ANTHROPIC_DEFAULT_HAIKU_MODEL ANTHROPIC_AUTH_TOKEN 2>/dev/null
      unset DASHSCOPE_API_KEY DASHSCOPE_API_KEYS 2>/dev/null
      BINARY="claude"
      EXTRA_ARGS="--model claude-sonnet-4-20250514"
      ;;
    qwen)
      # DashScope Qwen
      export ANTHROPIC_BASE_URL="https://coding-intl.dashscope.aliyuncs.com/apps/anthropic"
      export ANTHROPIC_API_KEY="${DASHSCOPE_API_KEY:-}"
      export ANTHROPIC_MODEL="qwen3.5-plus"
      export ANTHROPIC_DEFAULT_OPUS_MODEL="qwen3.5-plus"
      export ANTHROPIC_DEFAULT_SONNET_MODEL="qwen3.5-plus"
      export ANTHROPIC_DEFAULT_HAIKU_MODEL="qwen-turbo"
      BINARY="claude"
      EXTRA_ARGS=""
      ;;
    gemini)
      BINARY="gemini"
      EXTRA_ARGS=""
      ;;
    opencode)
      BINARY="opencode"
      EXTRA_ARGS=""
      ;;
    claude|*)
      # Default — use whatever auth is configured
      BINARY="claude"
      EXTRA_ARGS=""
      ;;
  esac
}

# ═══ Verify mekong-cli workspace ═══
verify_workspace() {
  if [[ ! -d "$MEKONG_ROOT/.claude/commands" ]]; then
    echo "❌ ERROR: .claude/commands/ not found in $MEKONG_ROOT"
    echo "   Run this from mekong-cli root or set MEKONG_ROOT"
    exit 1
  fi
  local cmd_count=$(find "$MEKONG_ROOT/.claude/commands" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
  local skill_count=$(find "$MEKONG_ROOT/.claude/skills" -name "SKILL.md" 2>/dev/null | wc -l | tr -d ' ')
  echo "🌊 MEKONG CLI v5.0 — OpenClaw"
  echo "   📂 $MEKONG_ROOT"
  echo "   ⚡ $cmd_count commands | 🧠 $skill_count skills"
  echo "   🔗 Provider: $PROVIDER → $BINARY"
  echo ""
}

# ═══ Launch CC CLI ═══
launch() {
  cd "$MEKONG_ROOT"
  
  case "$MODE" in
    print)
      # Non-interactive: pipe output
      case "$BINARY" in
        gemini)
          echo "$TASK" | $BINARY $EXTRA_ARGS 2>&1
          ;;
        opencode)
          $BINARY $EXTRA_ARGS -m "$TASK" 2>&1
          ;;
        *)
          $BINARY --dangerously-skip-permissions -p "$TASK" $EXTRA_ARGS 2>&1
          ;;
      esac
      ;;
    continue)
      # Resume last session
      $BINARY --dangerously-skip-permissions --continue $EXTRA_ARGS
      ;;
    cto)
      # CTO daemon mode
      export OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://127.0.0.1:11434}"
      bash "$MEKONG_ROOT/cto-daemon.sh" --session "${CTO_SESSION:-tom_hum}" --interval "${CTO_INTERVAL:-90}" "$@"
      ;;
    interactive|*)
      # Interactive mode with all commands loaded
      case "$BINARY" in
        gemini|opencode)
          # Non-CC CLI binaries don't support --dangerously-skip-permissions
          $BINARY $EXTRA_ARGS "$@"
          ;;
        *)
          $BINARY --dangerously-skip-permissions $EXTRA_ARGS "$@"
          ;;
      esac
      ;;
  esac
}

# ═══ Parse args ═══
TASK=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --provider) PROVIDER="$2"; shift 2 ;;
    --mode)     MODE="$2"; shift 2 ;;
    --print|-p) MODE="print"; TASK="$2"; shift 2 ;;
    --continue) MODE="continue"; shift ;;
    --cto)      MODE="cto"; shift ;;
    --quiet|-q) QUIET=1; shift ;;
    *) break ;;
  esac
done

# ═══ Run ═══
setup_provider
[[ -z "${QUIET:-}" ]] && verify_workspace
launch "$@"
