#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# Engine Farm A/B Test — Old vs New Models
# Tests: Code Gen, Reasoning, Tool Use, Trading, Embeddings
# Usage: bash ab-test.sh
# ═══════════════════════════════════════════════════════════════
set -euo pipefail

G="\033[32m" R="\033[31m" Y="\033[33m" C="\033[36m" B="\033[1m" D="\033[0m"

OLLAMA_API="${OLLAMA_API:-http://127.0.0.1:11434}"
OLLAMA_BIN="${OLLAMA_BIN:-ollama}"
if ! command -v "$OLLAMA_BIN" &>/dev/null; then
  OLLAMA_BIN="/usr/local/bin/ollama"
fi

RESULTS_DIR="ab-test-results-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$RESULTS_DIR"

echo -e "${B}${C}╔══════════════════════════════════════════════════════╗${D}"
echo -e "${B}${C}║          A/B TEST — Old vs New Engine Farm           ║${D}"
echo -e "${B}${C}╚══════════════════════════════════════════════════════╝${D}"
echo ""

# ─── Helper: query model and measure ───
query_model() {
  local model="$1"
  local prompt="$2"
  local label="$3"
  local output_file="$RESULTS_DIR/${label}.txt"

  local start_time=$(python3 -c "import time; print(time.time())")

  local response=$(curl -s "${OLLAMA_API}/api/generate" \
    -d "{\"model\":\"${model}\",\"prompt\":\"${prompt}\",\"stream\":false,\"options\":{\"temperature\":0.3,\"num_predict\":500}}" \
    2>/dev/null)

  local end_time=$(python3 -c "import time; print(time.time())")
  local duration=$(python3 -c "print(f'{${end_time} - ${start_time}:.2f}')")
  local tokens=$(echo "$response" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('eval_count',0))" 2>/dev/null || echo "0")
  local tok_per_sec=$(python3 -c "t=${tokens}; d=${duration}; print(f'{t/d:.1f}' if d>0 else '0')")

  echo "$response" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('response','')[:300])" 2>/dev/null > "$output_file"

  echo -e "  ${model}: ${G}${duration}s${D} | ${tokens} tokens | ${C}${tok_per_sec} tok/s${D}"
  echo "${model}|${duration}|${tokens}|${tok_per_sec}" >> "$RESULTS_DIR/metrics.csv"
}

# ═══════════════════════════════════════════════════════════════
# TEST 1: CODE GENERATION
# ═══════════════════════════════════════════════════════════════
echo -e "${B}═══ TEST 1: Code Generation ═══${D}"
CODE_PROMPT="Write a TypeScript function that implements a circuit breaker pattern with 3 states (closed, open, half-open), configurable failure threshold, and automatic reset timeout. Include proper error handling and type definitions."

echo "Prompt: Circuit breaker pattern in TypeScript"
echo ""

if "$OLLAMA_BIN" list 2>/dev/null | grep -q "qwen2.5-coder:32b"; then
  echo -e "${Y}OLD: Qwen2.5-Coder-32B${D}"
  query_model "qwen2.5-coder:32b" "$CODE_PROMPT" "code-old-qwen25coder32b"
fi

echo -e "${G}NEW: Qwen2.5-Coder-7B${D}"
query_model "qwen2.5-coder:7b" "$CODE_PROMPT" "code-new-qwen25coder7b"
echo ""

# ═══════════════════════════════════════════════════════════════
# TEST 2: REASONING
# ═══════════════════════════════════════════════════════════════
echo -e "${B}═══ TEST 2: Reasoning (Fair Value Estimation) ═══${D}"
REASON_PROMPT="A prediction market has a contract for 'Will Bitcoin exceed 150000 USD by December 2026?' currently trading at 0.42 (42% implied probability). Recent data: BTC is at 98000 USD, 3-month trend is +18%, institutional adoption increasing, but Fed signaling rate pause. Estimate the fair value probability and explain your reasoning step by step. Output as JSON: {fair_value: 0.XX, confidence: 0.XX, reasoning: '...'}"

echo "Prompt: BTC prediction market fair value estimation"
echo ""

if "$OLLAMA_BIN" list 2>/dev/null | grep -q "deepseek-r1:32b"; then
  echo -e "${Y}OLD: DeepSeek R1 32B${D}"
  query_model "deepseek-r1:32b" "$REASON_PROMPT" "reason-old-deepseek32b"
fi

echo -e "${G}NEW: Qwen3-8B (thinking mode)${D}"
query_model "qwen3:8b" "$REASON_PROMPT" "reason-new-qwen3-8b"
echo ""

# ═══════════════════════════════════════════════════════════════
# TEST 3: TOOL CALLING
# ═══════════════════════════════════════════════════════════════
echo -e "${B}═══ TEST 3: Tool Use / Function Calling ═══${D}"
TOOL_PROMPT="You have access to these tools: get_market_data(market_id: string) -> {price, volume, spread}, place_order(market_id: string, side: buy|sell, amount: number) -> {order_id}, get_balance() -> {usd: number, positions: array}. User request: Check the current price of market btc-dec-150k, and if the price is below 0.40, buy 50 USD worth. Respond with the sequence of tool calls needed as JSON array."

echo "Prompt: Multi-step tool calling for trading"
echo ""

if "$OLLAMA_BIN" list 2>/dev/null | grep -q "qwen2.5:7b\|qwen2.5:14b"; then
  echo -e "${Y}OLD: Qwen 2.5 14B${D}"
  query_model "qwen2.5:14b" "$TOOL_PROMPT" "tool-old-qwen25-14b"
fi

echo -e "${G}NEW: Qwen3-1.7B${D}"
query_model "qwen3:1.7b" "$TOOL_PROMPT" "tool-new-qwen3-1.7b"
echo ""

# ═══════════════════════════════════════════════════════════════
# TEST 4: TRADING / MATH REASONING
# ═══════════════════════════════════════════════════════════════
echo -e "${B}═══ TEST 4: Trading / Mathematical Reasoning ═══${D}"
TRADE_PROMPT="Calculate the optimal position size using Kelly Criterion: Win probability: 0.58, Win/loss ratio: 1.4 (avg win 140 USD, avg loss 100 USD), Current bankroll: 10000 USD, Apply quarter-Kelly for safety. Show the full calculation and output JSON: {full_kelly_pct: X, quarter_kelly_pct: X, position_size_usd: X, max_loss_usd: X}"

echo "Prompt: Kelly Criterion position sizing"
echo ""

if "$OLLAMA_BIN" list 2>/dev/null | grep -q "nemotron"; then
  echo -e "${Y}OLD: Nemotron 12B${D}"
  query_model "nemotron:12b" "$TRADE_PROMPT" "trade-old-nemotron12b"
fi

echo -e "${G}NEW: Phi-4-mini-reasoning${D}"
query_model "phi4-mini-reasoning" "$TRADE_PROMPT" "trade-new-phi4mini"
echo ""

# ═══════════════════════════════════════════════════════════════
# TEST 5: EMBEDDINGS (NEW capability)
# ═══════════════════════════════════════════════════════════════
echo -e "${B}═══ TEST 5: Embeddings (NEW capability) ═══${D}"
EMBED_RESULT=$(curl -s "${OLLAMA_API}/api/embed" \
  -d '{"model":"nomic-embed-text","input":"prediction market trading bot with fair value estimation"}' 2>/dev/null)
EMBED_DIM=$(echo "$EMBED_RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('embeddings',[[]])[0]))" 2>/dev/null || echo "0")
echo -e "  nomic-embed-text: ${G}${EMBED_DIM} dimensions${D} — embedding generated"
echo ""

# ═══════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════
echo -e "${B}${C}╔══════════════════════════════════════════════════════╗${D}"
echo -e "${B}${C}║              A/B TEST RESULTS SUMMARY                ║${D}"
echo -e "${B}${C}╚══════════════════════════════════════════════════════╝${D}"
echo ""

if [ -f "$RESULTS_DIR/metrics.csv" ]; then
  echo -e "${B}Performance Metrics:${D}"
  printf "  %-30s %8s %8s %10s\n" "Model" "Time(s)" "Tokens" "Tok/s"
  echo "  ────────────────────────────────────────────────────"
  while IFS='|' read -r model duration tokens tps; do
    printf "  %-30s %8s %8s %10s\n" "$model" "$duration" "$tokens" "$tps"
  done < "$RESULTS_DIR/metrics.csv"
fi

echo ""
echo -e "Full responses saved in: ${C}${RESULTS_DIR}/${D}"
echo ""
echo -e "${B}Memory comparison:${D}"
echo "  OLD: ~22 GB (4 models, no embeddings)"
echo "  NEW: ~14.7 GB (5 models + embeddings)"
echo "  SAVINGS: ~7.3 GB freed"
echo ""
echo -e "${B}Next steps:${D}"
echo "  1. Review responses in ${RESULTS_DIR}/*.txt"
echo "  2. Compare quality side-by-side"
echo "  3. If satisfied: bash cutover.sh"
echo "  4. If not: keep old models, tune prompts"
