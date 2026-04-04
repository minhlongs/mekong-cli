#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.env"

HEALTH_TIMEOUT=120
HEALTH_INTERVAL=3

# --- Helpers ---

check_ollama() {
  if ! command -v ollama &>/dev/null; then
    echo "[farm] ERROR: Ollama not installed."
    echo "[farm] Install: curl -fsSL https://ollama.com/install.sh | sh"
    echo "[farm] macOS: brew install ollama"
    exit 1
  fi
  echo "[farm] Ollama $(ollama --version 2>&1 | head -1)"
}

ensure_ollama_serving() {
  if curl -sf "${OLLAMA_API}/api/tags" >/dev/null 2>&1; then
    echo "[farm] Ollama already serving at ${OLLAMA_API}"
    return
  fi

  echo "[farm] Starting Ollama server..."
  OLLAMA_HOST="${OLLAMA_HOST}" ollama serve >/tmp/mekong-ollama.log 2>&1 &
  echo $! >/tmp/mekong-ollama.pid

  local elapsed=0
  while [[ $elapsed -lt 30 ]]; do
    if curl -sf "${OLLAMA_API}/api/tags" >/dev/null 2>&1; then
      echo "[farm] Ollama serving at ${OLLAMA_API} (${elapsed}s)"
      return
    fi
    sleep 1
    elapsed=$((elapsed + 1))
  done

  echo "[farm] ERROR: Ollama failed to start within 30s"
  exit 1
}

pull_model() {
  local model="$1"
  if ollama list 2>/dev/null | grep -q "^${model}"; then
    echo "[farm] Model $model already pulled"
    return
  fi
  echo "[farm] Pulling $model (this may take a while)..."
  ollama pull "$model"
}

warm_model() {
  local model="$1"
  if ollama ps 2>/dev/null | grep -q "${model}"; then
    echo "[farm] Model $model already loaded in memory"
    return
  fi
  echo "[farm] Warming $model into unified memory..."
  curl -sf "${OLLAMA_API}/api/generate" \
    -d "{\"model\":\"${model}\",\"prompt\":\"hi\",\"stream\":false}" \
    >/dev/null 2>&1 || true
  echo "[farm] Model $model warmed"
}

# --- Resolve models based on MEKONG_ENV ---

resolve_models() {
  if [[ "${MEKONG_ENV}" == "production" ]]; then
    ROUTER_MODEL="$PROD_ROUTER_MODEL"
    REASONING_MODEL="$PROD_REASONING_MODEL"
    AUDIT_MODEL="$PROD_AUDIT_MODEL"
    echo "[farm] Mode: PRODUCTION (lightweight models for B2B)"
  else
    ROUTER_MODEL="$DEV_ROUTER_MODEL"
    REASONING_MODEL="$DEV_REASONING_MODEL"
    AUDIT_MODEL="$DEV_AUDIT_MODEL"
    echo "[farm] Mode: DEVELOPMENT (full-power models)"
  fi
}

# --- Main ---

echo "[farm] === Mekong Engine Farm — Ollama MLX ==="
echo "[farm] MEKONG_ENV=${MEKONG_ENV}"

check_ollama
ensure_ollama_serving
resolve_models

echo ""
echo "[farm] --- Pulling models ---"
pull_model "$ROUTER_MODEL"
pull_model "$REASONING_MODEL"
pull_model "$AUDIT_MODEL"

echo ""
echo "[farm] --- Warming models into unified memory ---"
warm_model "$ROUTER_MODEL"
warm_model "$REASONING_MODEL"

echo ""
echo "[farm] === Engine Farm Ready ==="
echo "[farm]   API:       ${OLLAMA_API}/v1"
echo "[farm]   Router:    ${ROUTER_MODEL}"
echo "[farm]   Reasoning: ${REASONING_MODEL}"
echo "[farm]   Audit:     ${AUDIT_MODEL}"
echo "[farm]   Env:       ${MEKONG_ENV}"
echo ""
echo "[farm] OpenAI-compatible endpoint: ${OLLAMA_API}/v1/chat/completions"
