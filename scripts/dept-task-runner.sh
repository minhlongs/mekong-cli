#!/opt/homebrew/bin/bash
# ═══════════════════════════════════════════════════════════════
# Department Task Runner — uses Ollama qwen3:32b directly
# NO CC CLI = NO API burn. For content generation tasks only.
# Usage: bash scripts/dept-task-runner.sh <dept> <task_description>
# Output saved to: .mekong/output/<dept>/<timestamp>.md
# ═══════════════════════════════════════════════════════════════
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
MEKONG_DIR="${PROJECT_ROOT}/.mekong"
OLLAMA_URL="${OLLAMA_BASE_URL:-http://127.0.0.1:11434}"
OLLAMA_MODEL="${OPENCLAW_WORKER_MODEL:-qwen3:32b}"

DEPT="${1:-general}"
TASK="${2:-Write a brief status update}"
TIMESTAMP=$(date '+%Y%m%d-%H%M%S')
OUTPUT_DIR="${MEKONG_DIR}/output/${DEPT}"
OUTPUT_FILE="${OUTPUT_DIR}/${TIMESTAMP}.md"

mkdir -p "$OUTPUT_DIR"

# Build prompt with project context
PROMPT="/no_think
You are a ${DEPT} specialist for RaaS (ROI-as-a-Service) platform.
Project: mekong-cli — AI-operated business platform.
Packages: raas-landing (Astro), mekong-engine (Hono/D1), raas-dashboard (React).
Pricing: Starter \$49/mo, Pro \$149/mo, Enterprise \$499/mo.

TASK: ${TASK}

Write professional output. Use markdown formatting. Be specific and actionable.
If writing code snippets, use real file paths from the project."

# Call Ollama directly — no CC CLI, no API burn
RESPONSE=$(python3 -c "
import json, urllib.request, sys
data = json.dumps({
    'model': '${OLLAMA_MODEL}',
    'prompt': sys.stdin.read(),
    'stream': False,
    'keep_alive': '24h',
    'options': {'temperature': 0.7, 'num_predict': 4000, 'num_ctx': 8192}
}).encode()
try:
    req = urllib.request.Request('${OLLAMA_URL}/api/generate', data=data,
        headers={'Content-Type': 'application/json'})
    resp = urllib.request.urlopen(req, timeout=120)
    d = json.loads(resp.read())
    print(d.get('response', ''))
except Exception as e:
    print(f'ERROR: {e}', file=sys.stderr)
    sys.exit(1)
" <<< "$PROMPT" 2>>"${MEKONG_DIR}/brain-errors.log")

if [[ -n "$RESPONSE" ]]; then
  # Save output with metadata header
  cat > "$OUTPUT_FILE" << EOF
---
department: ${DEPT}
task: ${TASK}
model: ${OLLAMA_MODEL}
generated: $(date -u '+%Y-%m-%dT%H:%M:%SZ')
---

${RESPONSE}
EOF
  echo "$OUTPUT_FILE"
else
  echo "ERROR: Empty response from Ollama" >&2
  exit 1
fi
