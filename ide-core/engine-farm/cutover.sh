#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# Engine Farm Cutover — Switch to new models after A/B test
# Usage: bash cutover.sh [--yes]
# ═══════════════════════════════════════════════════════════════
set -euo pipefail

G="\033[32m" R="\033[31m" Y="\033[33m" C="\033[36m" B="\033[1m" D="\033[0m"

OLLAMA_API="${OLLAMA_API:-http://127.0.0.1:11434}"
OLLAMA_BIN="${OLLAMA_BIN:-ollama}"
if ! command -v "$OLLAMA_BIN" &>/dev/null; then
  OLLAMA_BIN="/usr/local/bin/ollama"
fi

echo -e "${B}${C}╔══════════════════════════════════════════════════════╗${D}"
echo -e "${B}${C}║     ENGINE FARM CUTOVER — Go Live                   ║${D}"
echo -e "${B}${C}╚══════════════════════════════════════════════════════╝${D}"
echo ""

# Auto-approve with --yes flag, otherwise prompt
if [[ "${1:-}" != "--yes" ]]; then
  read -p "A/B test passed? Proceed with cutover? (y/N): " confirm
  [[ "$confirm" != "y" && "$confirm" != "Y" ]] && { echo "Aborted."; exit 0; }
fi

# ─── Unload old models from memory ───
echo -e "${Y}Unloading old models from memory...${D}"
OLD_MODELS=("qwen2.5-coder:32b" "deepseek-r1:32b" "nemotron:12b" "qwen2.5:14b" "qwen2.5:7b")
for model in "${OLD_MODELS[@]}"; do
  if "$OLLAMA_BIN" ps 2>/dev/null | grep -q "${model}"; then
    echo -e "  Unloading ${model}..."
    curl -sf "${OLLAMA_API}/api/generate" \
      -d "{\"model\":\"${model}\",\"keep_alive\":0}" \
      >/dev/null 2>&1 || true
  fi
done
echo ""

# ─── Warm new models ───
echo -e "${G}Warming new models into unified memory...${D}"
NEW_MODELS=("qwen2.5-coder:7b" "qwen3:8b" "qwen3:1.7b" "phi4-mini-reasoning" "nomic-embed-text")
for model in "${NEW_MODELS[@]}"; do
  echo -e "  Loading ${model}..."
  curl -sf "${OLLAMA_API}/api/generate" \
    -d "{\"model\":\"${model}\",\"prompt\":\"ping\",\"stream\":false,\"options\":{\"num_predict\":5}}" \
    >/dev/null 2>&1 || echo -e "  ${R}Warning: ${model} failed to load${D}"
done
echo ""

# ─── Verify ───
echo -e "${B}═══ Verification ═══${D}"
echo "Loaded models:"
"$OLLAMA_BIN" ps 2>/dev/null || echo "  (could not check)"
echo ""

# Health check each model
PASS=0
FAIL=0
for model in "${NEW_MODELS[@]}"; do
  result=$(curl -s "${OLLAMA_API}/api/generate" \
    -d "{\"model\":\"${model}\",\"prompt\":\"ping\",\"stream\":false,\"options\":{\"num_predict\":5}}" 2>/dev/null)
  if echo "$result" | grep -q "response"; then
    echo -e "  ${G}✅ ${model}${D}"
    PASS=$((PASS + 1))
  else
    echo -e "  ${R}❌ ${model} — NOT RESPONDING${D}"
    FAIL=$((FAIL + 1))
  fi
done

echo ""
echo -e "${B}Results: ${G}${PASS} passed${D}, ${R}${FAIL} failed${D}"
echo ""

if [[ $FAIL -eq 0 ]]; then
  echo -e "${B}═══ Cleanup (optional) ═══${D}"
  echo "To remove old models and free disk space:"
  for model in "${OLD_MODELS[@]}"; do
    echo "  $OLLAMA_BIN rm ${model}"
  done
  echo ""
  echo -e "${G}✅ Engine Farm v2 live. 兵貴神速!${D}"
else
  echo -e "${R}⚠️ Some models failed. Check Ollama logs before removing old models.${D}"
fi
