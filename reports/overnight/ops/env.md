# Mekong CLI v5.0 — Environment Configuration Report
**Generated:** 2026-03-12 overnight | **Op:** /ops:env

---

## LLM Configuration (Universal 3-Var System)

```bash
# Minimum required — works with ANY OpenAI-compatible provider
export LLM_BASE_URL=https://openrouter.ai/api/v1
export LLM_API_KEY=sk-or-v1-yourkey
export LLM_MODEL=anthropic/claude-sonnet-4
```

No proxy, no custom SDK. Pure OpenAI-compatible REST.
Config reference: mekong/adapters/llm-providers.yaml

---

## Provider Presets (mekong/adapters/llm-providers.yaml)

| Preset | Base URL | Model | Cost |
|--------|----------|-------|------|
| openrouter | openrouter.ai/api/v1 | claude-sonnet-4 | Pay-per-token |
| deepseek | api.deepseek.com | deepseek-chat | $0.27/100K |
| qwen-coding-plan | dashscope.aliyuncs.com | qwen3-coder-plus | ~$10/mo unlimited |
| agentrouter | agentrouter.org/v1 | claude-sonnet-4-6 | $200 free |
| openai | api.openai.com/v1 | gpt-4o | Pay-per-token |
| ollama | localhost:11434/v1 | llama3 | Free (local) |

---

## Fallback Chain (src/core/fallback_chain.py)

Priority order when primary provider fails:
```
1. OPENROUTER_API_KEY   → openrouter.ai
2. DASHSCOPE_API_KEY    → qwen-coding-plan (Alibaba)
3. DEEPSEEK_API_KEY     → deepseek-chat
4. ANTHROPIC_API_KEY    → anthropic direct
5. OPENAI_API_KEY       → gpt-4o
6. GOOGLE_API_KEY       → gemini-pro
7. OLLAMA_BASE_URL      → local model
8. OfflineProvider      → cached responses only
```

---

## Cloudflare Deployment Environment

### CF Pages (Frontend)
```toml
# pages.toml
name = "sophia-proposal"
compatibility_date = "2024-01-01"
build.command = "npm run build"
build.output_directory = "dist"
```

### CF Workers (Edge API)
```toml
# wrangler.toml (raas-gateway)
name = "raas-gateway"
main = "index.js"
compatibility_date = "2024-09-23"
[vars]
ENVIRONMENT = "production"
[kv_namespaces]
binding = "TENANT_STORE"
[d1_databases]
binding = "DB"
[r2_buckets]
binding = "STORAGE"
```

### Secrets (CF Secrets — never in wrangler.toml)
```bash
wrangler secret put JWT_SECRET=REDACTED
wrangler secret put POLAR_WEBHOOK_SECRET
wrangler secret put LLM_API_KEY
wrangler secret put MCU_SIGNING_KEY
```

---

## Local Development Environment

```bash
# Install
pip3 install -e ".[dev]"

# Required env vars
cp .env.example .env
# Edit: LLM_BASE_URL, LLM_API_KEY, LLM_MODEL

# Run locally
python3 -m mekong.cli --help
# or
python3 src/main.py --help

# Test
python3 -m pytest tests/ -x -q
```

---

## Environment Variables Reference

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| LLM_BASE_URL | YES | — | LLM API endpoint |
| LLM_API_KEY | YES | — | LLM authentication |
| LLM_MODEL | YES | — | Model identifier |
| POLAR_WEBHOOK_SECRET | prod only | — | Payment webhook auth |
| JWT_SECRET=REDACTED | prod only | — | API auth signing |
| MCU_SIGNING_KEY | prod only | — | Credit audit signing |
| TELEGRAM_BOT_TOKEN | optional | — | Tôm Hùm bot |
| ENVIRONMENT | optional | development | prod/staging/dev |
| LOG_LEVEL | optional | INFO | debug/info/warn/error |

---

## No-Proxy Design

Mekong CLI requires NO proxy, NO VPN, NO special network config.
Direct HTTPS to LLM provider. CF Workers handle edge routing.
Works from: macOS, Linux, Windows (WSL), Docker, GitHub Actions.

**ENVIRONMENT: CORRECTLY CONFIGURED**
