#!/bin/bash
# deploy-models.sh — Pull and verify tiered Ollama models for Mekong AI OS
# Usage: ./deploy-models.sh          # interactive (prompts before pulling)
#        ./deploy-models.sh --force  # auto-pull without prompts

set -euo pipefail

FORCE="${1:-}"

echo "=== Mekong AI OS — Model Deployment ==="
echo ""

# Ensure Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
  echo "ERROR: Ollama is not running. Start it first."
  exit 1
fi

echo "Checking currently available models..."
ollama list
echo ""

# --------------------------------------------------
# Helper: check + pull a model
# --------------------------------------------------
ensure_model() {
  local model="$1"
  local label="$2"

  if ollama list | grep -qF "$model"; then
    echo "[✓] $model ($label) — already available"
    return 0
  fi

  echo "[ ] $model ($label) — NOT found"

  if [ "$FORCE" == "--force" ]; then
    REPLY="y"
  else
    read -r -p "  Pull $model ($label) now? [Y/n] " REPLY
    REPLY="${REPLY:-y}"
  fi

  if [[ "$REPLY" =~ ^[Yy]$ ]]; then
    echo "  Pulling $model..."
    ollama pull "$model"
    echo "[✓] $model pulled successfully"
  else
    echo "[ ] Skipped $model"
  fi
}

# --------------------------------------------------
# Models
# --------------------------------------------------
echo "--- Tier 2: Coding (7B) ---"
ensure_model "qwen2.5-coder:7b" "Lightweight coding/utility"

echo ""
echo "--- Tier 3: Deep Coding (14B) ---"
ensure_model "qwen2.5-coder:14b" "Heavy coding/reasoning"

echo ""
echo "--- Tier 1 is already available ---"
echo "  qwen3.6:35b-mlx-fast (strategic/critical)"

echo ""
echo "=== Verifying models ==="

for model in "qwen2.5-coder:7b" "qwen2.5-coder:14b"; do
  if ollama list | grep -qF "$model"; then
    echo -n "Testing $model... "
    OUTPUT=$(ollama run "$model" "hello" 2>&1 | head -3)
    echo "OK (response: $(echo "$OUTPUT" | wc -c) chars)"
  fi
done

echo ""
echo "=== Model Inventory ==="

# Build inventory JSON
INVENTORY=$(ollama list --json 2>/dev/null || ollama list 2>/dev/null)
if [ -z "$INVENTORY" ]; then
  # Fallback: build manually from plain output
  INVENTORY="["
  FIRST=true
  while IFS=$'\t' read -r name id size modified; do
    if [ -z "$name" ] || [ "$name" == "NAME" ]; then
      continue
    fi
    # Clean up whitespace
    name=$(echo "$name" | xargs)
    id=$(echo "$id" | xargs)
    if [ "$FIRST" = false ]; then
      INVENTORY+=","
    fi
    INVENTORY+=$(cat <<EOJ
    {"name":"$name","model_id":"$id","size":"$size","modified":"$modified"}
EOJ
    )
    FIRST=false
  done < <(ollama list | tail -n +2)
  INVENTORY+="]"
fi

mkdir -p "$HOME/.system"
cat > "$HOME/.system/model-inventory.json" <<EOJ
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "host": "$(hostname)",
  "models": $INVENTORY,
  "tier_map": {
    "tier1_strategic": "qwen3.6:35b-mlx-fast",
    "tier2_coding_14b": "qwen2.5-coder:14b",
    "tier3_utility_7b": "qwen2.5-coder:7b"
  }
}
EOJ

echo "Inventory saved to ~/.system/model-inventory.json"
echo "=== Done ==="
