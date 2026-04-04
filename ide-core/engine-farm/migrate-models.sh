#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# Engine Farm Migration — Pull new optimized model stack
# Old (22GB, 4 models) → New (14.9GB, 7 models)
# Usage: bash migrate-models.sh
#   or SSH: ssh <user>@<host> 'bash -s' < migrate-models.sh
# ═══════════════════════════════════════════════════════════════
set -euo pipefail

G="\033[32m" R="\033[31m" Y="\033[33m" C="\033[36m" B="\033[1m" D="\033[0m"

echo -e "${B}${C}╔══════════════════════════════════════════════════════╗${D}"
echo -e "${B}${C}║     ENGINE FARM MIGRATION — M1 Max 64GB             ║${D}"
echo -e "${B}${C}║     Old (22GB, 4 models) → New (14.9GB, 7 models)  ║${D}"
echo -e "${B}${C}╚══════════════════════════════════════════════════════╝${D}"
echo ""

OLLAMA_BIN="${OLLAMA_BIN:-ollama}"
if ! command -v "$OLLAMA_BIN" &>/dev/null; then
  OLLAMA_BIN="/usr/local/bin/ollama"
fi

# ─── PHASE 1: Verify Ollama 0.19+ (MLX backend) ───
echo -e "${B}═══ PHASE 1: Verify Ollama ═══${D}"
OLLAMA_VERSION=$("$OLLAMA_BIN" --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+' | head -1 || echo "0.0")
echo -e "Current Ollama: ${Y}${OLLAMA_VERSION}${D}"

if [[ "$OLLAMA_VERSION" < "0.19" ]]; then
  echo -e "${Y}Updating Ollama to 0.19+ (MLX backend)...${D}"
  curl -fsSL https://ollama.com/install.sh | sh
  echo -e "${G}✅ Ollama updated${D}"
else
  echo -e "${G}✅ Ollama ${OLLAMA_VERSION} — MLX backend ready${D}"
fi
echo ""

# ─── PHASE 2: Pull new models ───
echo -e "${B}═══ PHASE 2: Pull New Models ═══${D}"

MODELS=(
  "qwen2.5-coder:7b"       # Code gen — replaces Gemma 26B / qwen2.5-coder:32b
  "qwen3:8b"               # Reasoning — replaces DeepSeek R1 32B
  "qwen3:1.7b"             # Tool use — replaces Qwen 2.5 7B
  "phi4-mini-reasoning"    # Trading — replaces Nemotron 30B
  "nomic-embed-text"       # Embeddings — NEW capability
)

for model in "${MODELS[@]}"; do
  if "$OLLAMA_BIN" list 2>/dev/null | grep -q "^${model}"; then
    echo -e "${G}✅ ${model} already pulled${D}"
  else
    echo -e "${C}Pulling ${model}...${D}"
    "$OLLAMA_BIN" pull "$model"
    echo -e "${G}✅ ${model} ready${D}"
  fi
  echo ""
done

# ─── PHASE 3: Model Inventory ───
echo -e "${B}═══ PHASE 3: Model Inventory ═══${D}"
echo "All models:"
"$OLLAMA_BIN" list 2>/dev/null || echo "  (could not list)"
echo ""

# ─── Memory Budget ───
echo -e "${B}═══ Memory Budget ═══${D}"
echo "New stack (always loaded):"
echo "  Qwen2.5-Coder-7B  Q4_K_M  ~5.5 GB  Code gen"
echo "  Qwen3-8B           Q4_K_M  ~5.2 GB  Reasoning"
echo "  Qwen3-1.7B         Q4_K_M  ~1.2 GB  Tool use"
echo "  Phi-4-mini-reason  Q4_K_M  ~2.5 GB  Trading"
echo "  nomic-embed-text   FP16    ~0.3 GB  Embeddings"
echo "  ─────────────────────────────────────────────"
echo "  TOTAL                      ~14.7 GB"
echo "  Available (64GB)           ~49.3 GB headroom"
echo ""
echo -e "${G}✅ Migration complete. Ready for A/B testing.${D}"
echo -e "Run: ${C}bash engine-farm-ab-test.sh${D}"
