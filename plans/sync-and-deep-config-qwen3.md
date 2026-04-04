# PLAN: Sync Upstream & Deep Config Qwen3.0 32B

**Priority:** 🔴 HIGH
**Assignee:** CTO Daemon
**Created:** 2026-03-20T14:56:00+07:00

---

## Phase 1: Sync Upstream → Local

### Step 1: Fetch upstream
```bash
cd /Users/mac/mekong-cli && git fetch upstream
```

### Step 2: Merge upstream/main
```bash
cd /Users/mac/mekong-cli && git merge upstream/main --no-edit
```

### Step 3: Verify sync (10 commits behind)
```bash
cd /Users/mac/mekong-cli && git log --oneline -5
```

**Expected:** Thấy commits mới nhất từ upstream:
- `8a1d107` fix: remove any types and console.log
- `bc16a9e` fix(cto-daemon): send_to_pane Escape-first
- `1fbb33e` fix(cto-daemon): company.json path fallback
- `8aa0694` feat(cto-daemon): PRIORITY 0 dispatch
- `f551a45` fix(cto-daemon): GATE 1 race condition

---

## Phase 2: Pull Qwen3.0 32B vào Ollama

### Step 4: Pull model
```bash
ollama pull qwen3:32b
```

### Step 5: Verify model available
```bash
ollama list | grep qwen3
```

**Expected:** `qwen3:32b` xuất hiện trong danh sách.

---

## Phase 3: Deep Config .env cho Qwen3.0 32B

### Step 6: Update .env
```bash
cd /Users/mac/mekong-cli && cat > .env << 'EOF'
# =============================================================================
# Mekong CLI v5.0 — Qwen3.0 32B Local Config
# =============================================================================

# PRIMARY: Ollama Local (Qwen3.0 32B - FREE, OFFLINE)
LLM_BASE_URL=http://localhost:11434/v1
LLM_API_KEY=ollama
LLM_MODEL=qwen3:32b

# Ollama explicit config
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=qwen3:32b

# Mode: BYOK (default — key hits provider directly)
LLM_MODE=byok

# RaaS (optional)
# POLAR_WEBHOOK_SECRET=whsec_...
# RAAS_LICENSE_KEY=your-license-key

# Telegram (optional)
# MEKONG_TELEGRAM_TOKEN=bot-token-here
EOF
```

### Step 7: Verify .env loaded correctly
```bash
cd /Users/mac/mekong-cli && grep -E "^(LLM_|OLLAMA_)" .env
```

**Expected output:**
```
LLM_BASE_URL=http://localhost:11434/v1
LLM_API_KEY=ollama
LLM_MODEL=qwen3:32b
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=qwen3:32b
LLM_MODE=byok
```

---

## Phase 4: Verify LLM Client Connectivity

### Step 8: Test Ollama health
```bash
curl -s http://localhost:11434/api/tags | python3 -c "import sys,json; d=json.load(sys.stdin); [print(m['name']) for m in d.get('models',[])]" 2>/dev/null || echo "Ollama not running"
```

### Step 9: Test Qwen3 chat completion
```bash
curl -s http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen3:32b","messages":[{"role":"user","content":"Hello, respond with OK"}],"max_tokens":10}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

**Expected:** Qwen3.0 32B responds "OK" hoặc tương tự.

### Step 10: Test Mekong CLI integration
```bash
cd /Users/mac/mekong-cli && python3 -c "
from src.core.llm_client import get_client
client = get_client()
print(f'Mode: {client.mode}')
print(f'Available: {client.is_available}')
print(f'Providers: {[p.name for p in client.providers]}')
print(f'Model: {client.model}')
"
```

**Expected:**
```
Mode: proxy
Available: True
Providers: ['primary', 'ollama-local', 'offline']
Model: qwen3:32b
```

---

## Phase 5: Deep Config — Adapter & Provider YAML

### Step 11: Create/update provider config
```bash
mkdir -p /Users/mac/mekong-cli/mekong/adapters
cat > /Users/mac/mekong-cli/mekong/adapters/llm-providers.yaml << 'EOF'
# Mekong CLI — LLM Provider Configuration
# Qwen3.0 32B Local (Ollama) — Primary

providers:
  - name: qwen3-local
    type: openai_compatible
    base_url: http://localhost:11434/v1
    api_key_env: LLM_API_KEY
    model: qwen3:32b
    timeout: 120
    priority: 0

  - name: ollama-fallback
    type: openai_compatible
    base_url: http://localhost:11434/v1
    api_key_env: LLM_API_KEY
    model: qwen3:32b
    timeout: 60
    priority: 1

defaults:
  model: qwen3:32b
  temperature: 0.7
  max_tokens: 4096
  timeout: 120

circuit_breaker:
  max_failures: 3
  cooldown_secs: 15
EOF
```

### Step 12: Verify config
```bash
cd /Users/mac/mekong-cli && python3 -c "
import yaml
with open('mekong/adapters/llm-providers.yaml') as f:
    cfg = yaml.safe_load(f)
print(f'Providers: {len(cfg[\"providers\"])}')
for p in cfg['providers']:
    print(f'  - {p[\"name\"]}: {p[\"model\"]} @ {p[\"base_url\"]}')
print(f'Default model: {cfg[\"defaults\"][\"model\"]}')
"
```

---

## ✅ Done Criteria

- [ ] `git log` shows upstream commits synced
- [ ] `ollama list` shows `qwen3:32b`
- [ ] `.env` has `LLM_MODEL=qwen3:32b`
- [ ] `curl localhost:11434/v1/chat/completions` returns response
- [ ] Mekong CLI `get_client()` detects Qwen3 provider
- [ ] `llm-providers.yaml` configured with Qwen3 as primary
