# Sync & Integration Operations — Mekong CLI v5.0.0
**Date:** 2026-03-11 | **Commands covered:** sync-all, sync-tasks, sync-artifacts, sync-agent, sync-editor, sync-mcp, sync-providers, sync-browser, integration

---

## Overview

Mekong CLI sync operations span 5 domains: task state, LLM provider config, agent artifacts, MCP tooling, and editor (CC CLI) integration.

---

## 1. Task Sync (`sync-tasks`)

### Storage Location
- Active tasks: `.mekong/tasks/` (per CLAUDE.md session bootstrap)
- Company state: `.mekong/company.json`
- CI task tracking: GitHub Issues + `daily-repo-status` workflow

### Session Bootstrap Sync
Every session init reads:
```
1. .mekong/company.json  → company context
2. .mekong/tasks/        → active task queue
3. Output: "OpenClaw online. [N] pending tasks. Ready."
```

### CI Task Sync
- `.github/workflows/daily-repo-status.md` — daily GH issue with repo activity
- `.github/workflows/issue-triage.yml` — auto-label/triage new issues
- `.github/workflows/stale-cleanup.yml` — stale issue/PR cleanup
- `.github/workflows/pr-auto-review.yml` — auto-review triggers

### Nightly Billing Sync
- `scripts/nightly-reconciliation.sh` — cron `0 2 * * *`
- `.github/workflows/nightly-reconciliation.yml` — GH Actions version
- Syncs local DB ↔ Stripe billing records

---

## 2. Provider Sync (`sync-providers`)

### LLM Provider Registry
**File:** `mekong/adapters/llm-providers.yaml`

Supported providers (full list):
| Provider | Base URL | Notes |
|----------|----------|-------|
| qwen-coding-plan | dashscope.aliyuncs.com | ~$10/mo unlimited |
| qwen-international | dashscope-intl.aliyuncs.com | International endpoint |
| deepseek | api.deepseek.com | $0.27/100K tokens |
| openrouter | openrouter.ai/api/v1 | 300+ models, $5 free |
| agentrouter | agentrouter.org/v1 | $200 free credits |
| openai | api.openai.com/v1 | GPT-4o |
| anthropic | api.anthropic.com/v1 | Claude direct |
| deepinfra | api.deepinfra.com | EU hosting |
| fireworks | api.fireworks.ai | Qwen hosted |
| together | api.together.xyz/v1 | DeepSeek-V3 |
| local/ollama | localhost:11434/v1 | Free, offline |

### Provider Switch Scripts
```bash
scripts/switch-to-max.sh      # Switch to Claude Max
scripts/switch-to-qwen.sh     # Switch to Qwen coding plan
scripts/api-switch.sh         # Generic provider switch
```

### Fallback Chain (automatic, `src/core/llm_client.py`)
```
OPENROUTER_API_KEY
→ DASHSCOPE_API_KEY
→ DEEPSEEK_API_KEY
→ ANTHROPIC_API_KEY
→ OPENAI_API_KEY
→ GOOGLE_API_KEY
→ OLLAMA_BASE_URL
→ OfflineProvider
```

### Runtime Provider Detection (`src/core/api_adapter.py`)
```python
detect_provider(model_id: str) → "anthropic" | "google" | "openai" | "ollama"
```
Routes to correct SDK per model prefix.

---

## 3. MCP Sync (`sync-mcp`)

### MCP Configuration
**Template:** `scripts/claude-settings.json.example`
```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "https://coding-intl.dashscope.aliyuncs.com/...",
    "ENABLE_EXPERIMENTAL_MCP_CLI": "true"
  }
}
```
- `ENABLE_EXPERIMENTAL_MCP_CLI: true` — MCP CLI feature flag enabled
- Deployed to `~/.claude/settings.json` via `setup-dev.sh`
- `setup-dev.sh --quick` — non-interactive setup for CI/AI agents

### MCP Tool Registry
`src/core/tool_registry.py` — references MCP tool definitions (found via grep)

### Setup MCP
```bash
# Full setup (interactive):
bash scripts/setup-dev.sh

# Quick setup (CI / agents):
bash scripts/setup-dev.sh --quick

# Manual MCP config:
cp scripts/claude-settings.json.example ~/.claude/settings.json
# Edit: add real DashScope/Anthropic API key
```

---

## 4. Editor Sync (`sync-editor`)

### CC CLI Integration
- **Mode:** `claude -p` (non-interactive print mode) — per MEMORY.md
- CC CLI spawned via Node.js child_process with `stdin: 'ignore'`
- `mekong/adapters/cc-cli.sh` — CC CLI adapter script
- Bypass flag: `claude --dangerously-skip-permissions`

### Tôm Hùm Daemon → CC CLI
`apps/openclaw-worker/` daemon (Tôm Hùm v23.0):
- `brain-process-manager.js` → `runMission()` → `claude -p` per mission
- No expect, no file IPC
- Daemon control: `make start-daemon` / `make stop-daemon` / `make daemon-status`

### Editor Environment Variables (`.claude/.env` hierarchy)
Priority (highest → lowest):
1. `process.env` — runtime
2. `.claude/skills/<skill>/.env` — skill-specific
3. `.claude/skills/.env` — shared skills
4. `.claude/.env` — global defaults

---

## 5. Artifact Sync (`sync-artifacts`)

### Build Artifacts
- Python: `dist/`, `build/`, `*.egg-info/` — local, not committed
- Node: `.next/`, `dist/`, `out/` — not committed
- Binary: `mekong.spec` present (PyInstaller spec for binary build)
- Build binary script: `scripts/build-binary.sh`

### Published Packages
- **NPM:** `@agencyos/core`, `@agencyos/agents` — published on GitHub release
- **PyPI:** `mekong-cli` — published via Poetry on GitHub release
- Guard: `publish-packages.yml` explicitly blocks proprietary packages (`openclaw-worker`, `antigravity-proxy`)

### Factory Contracts (`factory/`)
- 176 JSON machine contracts
- Sync commands: `make generate-contracts` → `make validate-contracts` → `make self-test`
- Full regeneration: `make regenerate`

---

## 6. Agent Sync (`sync-agent`)

### Agent Registry (`src/agents/__init__.py`)
`AGENT_REGISTRY` dict — CLI lookup map for all agents:
- `LeadHunter`, `ContentWriter`, `RecipeCrawler`
- `GitAgent`, `FileAgent`, `ShellAgent`

### IPC Message Bus
`src/core/ipc_agent_message_bus.py` — inter-agent communication

### Activation Sync
`src/core/activation_sync.py` — agent activation state synchronization

---

## 7. Browser Sync (`sync-browser`)

- `src/agents/` contains `browser_agent` (referenced in test `test_browser_agent.py`)
- Used for web research tasks (LeadHunter, content scraping)
- M1 protection rule: browser agent limited — ~2GB RAM per instance

---

## Integration Status Matrix

| Integration | Status | Config |
|-------------|--------|--------|
| GitHub Actions | ACTIVE | 24 workflows |
| Cloudflare Pages | ACTIVE | `deploy-landing.yml` |
| Cloudflare Workers | ACTIVE | `deploy-cloudflare.yml` |
| Fly.io | ACTIVE | `fly.toml` |
| Stripe | ACTIVE | Nightly reconciliation |
| Polar.sh | ACTIVE | Webhook-based billing |
| Telegram | CONFIGURED | `TELEGRAM_API_TOKEN` |
| LLM providers | ACTIVE | 10+ providers via fallback chain |
| PyPI | ON-RELEASE | `publish-pypi.yml` |
| NPM | ON-RELEASE | `publish-packages.yml` |
| Langfuse | PARTIAL | Tests exist, prod unconfirmed |
| Qdrant | PARTIAL | `test_memory_qdrant.py` exists |
| Supabase | IN-APPS | `apps/` only, not core |

---

## Sync Health Check Commands

```bash
# Provider connectivity
python3 -c "from src.core.llm_client import LLMClient; print('LLM OK')"

# Task state
ls .mekong/tasks/ 2>/dev/null && cat .mekong/company.json 2>/dev/null

# Factory contracts
make validate-contracts

# Agent registry
python3 -c "from src.agents import AGENT_REGISTRY; print(list(AGENT_REGISTRY.keys()))"

# Nightly sync status
tail -50 /var/log/mekong/reconciliation-$(date +%Y-%m-%d).log 2>/dev/null
```
