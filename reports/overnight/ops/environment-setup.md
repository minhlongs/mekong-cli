# Environment & Platform Setup — Mekong CLI v5.0.0
**Date:** 2026-03-11 | **Commands covered:** env, platform-environment-setup, install, setup-mcp

---

## Local Dev Requirements

### Runtime Prerequisites

| Tool | Minimum | CI Version | Check |
|------|---------|-----------|-------|
| Python | 3.9+ | 3.12 | `python3 --version` |
| Node.js | 18+ | 22 | `node -v` |
| pnpm | any | latest | `pnpm -v` |
| Git | any | latest | `git --version` |
| CC CLI | any | N/A | `claude --version` |
| mekong CLI | installed | N/A | `mekong --help` |

> Note: Local machine runs Python 3.9.6 (system); CI uses 3.12. Recommend aligning to 3.12 locally to avoid behavior differences.

### Optional Tools

| Tool | Purpose | Install |
|------|---------|---------|
| `ruff` | Linting + formatting | `pip install ruff` |
| `mypy` | Type checking | `pip install mypy` |
| `wrangler` | CF Workers deploy | `npm install -g wrangler` |
| `fly` / `flyctl` | Fly.io operations | `brew install flyctl` |
| `bandit` | Python SAST | `pip install bandit` |
| `safety` | Dependency audit | `pip install safety` |
| `truffleHog` | Secret scanning | `pip install truffleHog` |
| `ollama` | Local LLM | `brew install ollama` |

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/agencyos/mekong-cli
cd mekong-cli

# 2. Setup (interactive)
bash scripts/setup-dev.sh

# OR: non-interactive (for CI / AI agents)
bash scripts/setup-dev.sh --quick

# 3. Verify
make health
```

### What `setup-dev.sh` Does
1. Copies `.env.example` → `.env` (if missing)
2. `pip install -e ".[dev]"` — installs Python deps in editable mode
3. `pnpm install` — installs Node deps
4. Copies `scripts/claude-settings.json.example` → `~/.claude/settings.json` (if missing)
5. Optionally prompts for DashScope API key
6. Runs `scripts/health-check.sh`

---

## Environment Variable Configuration

### Hierarchy (highest → lowest priority)
```
process.env                        ← Runtime / shell export
.claude/skills/<skill>/.env        ← Skill-specific overrides
.claude/skills/.env                ← Shared across all skills
.claude/.env                       ← Project global defaults
.env                               ← Root project env (dotenv loaded)
```

Resolver script: `~/.claude/scripts/resolve_env.py`
Debug: `python ~/.claude/scripts/resolve_env.py --show-hierarchy`

### Root `.env` (from `.env.example`)

```bash
# LLM Provider — 3-var universal config
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_API_KEY=sk-or-v1-yourkey
LLM_MODEL=anthropic/claude-sonnet-4

# Provider-specific keys (auto-detect fallback chain)
OPENROUTER_API_KEY=
DASHSCOPE_API_KEY=
DEEPSEEK_API_KEY=
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
GOOGLE_API_KEY=
OLLAMA_BASE_URL=http://localhost:11434/v1

# RaaS billing
POLAR_WEBHOOK_SECRET=
RAAS_LICENSE_KEY=

# Telegram bot
TELEGRAM_API_TOKEN=

# Backend services
DATABASE_URL=/data/tenants.db
TELEMETRY_BACKEND_URL=https://api.mekong.dev/api/v1/telemetry/events
```

### Fly.io Production Secrets (set via `fly secrets set`)

```bash
fly secrets set \
  LLM_API_KEY=... \
  DATABASE_URL=... \
  STRIPE_SECRET_KEY=... \
  POLAR_WEBHOOK_SECRET=... \
  TELEGRAM_API_TOKEN=... \
  RAAS_LICENSE_KEY=... \
  -a agencyos-gateway
```

### GitHub Actions Secrets Required

| Secret | Used By |
|--------|---------|
| `CLOUDFLARE_API_TOKEN` | `deploy-cloudflare.yml`, `deploy-landing.yml` |
| `CLOUDFLARE_ACCOUNT_ID` | `deploy-cloudflare.yml` |
| `NPM_TOKEN` | `publish-packages.yml` |
| `PYPI_TOKEN` | `publish-pypi.yml` |
| `DATABASE_URL` | `nightly-reconciliation.yml` |
| `STRIPE_SECRET_KEY` | `nightly-reconciliation.yml` |
| `FLY_API_TOKEN` | Fly deployments |

---

## MCP Server Configuration

### Template Location
`scripts/claude-settings.json.example` → deployed to `~/.claude/settings.json`

### Default MCP Config (DashScope / Qwen)
```json
{
  "env": {
    "ANTHROPIC_API_KEY": "YOUR_DASHSCOPE_KEY",
    "ANTHROPIC_AUTH_TOKEN": "YOUR_DASHSCOPE_KEY",
    "ANTHROPIC_BASE_URL": "https://coding-intl.dashscope.aliyuncs.com/apps/anthropic",
    "ANTHROPIC_MODEL": "qwen3.5-plus",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "qwen3.5-plus",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "qwen3.5-plus",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "qwen3-coder-next",
    "ENABLE_EXPERIMENTAL_MCP_CLI": "true"
  },
  "includeCoAuthoredBy": false,
  "model": "qwen3.5-plus"
}
```

### MCP Feature Flag
`ENABLE_EXPERIMENTAL_MCP_CLI: "true"` — enables MCP CLI integration in CC CLI.

### ClaudeKit Environment (`.claude/.env`)
```bash
CLAUDEKIT_API_KEY=        # claudekit.cc/api-keys
CONTEXT7_API_KEY=         # context7.com/dashboard
DISCORD_WEBHOOK_URL=      # notifications
TELEGRAM_BOT_TOKEN=       # notifications
```

---

## Platform-Specific Notes

### macOS M1 (Primary Dev Machine)
- Python 3.9.6 system default — recommend `pyenv install 3.12` or `brew install python@3.12`
- M1 cooling scripts: `scripts/m1-cooler.sh`, `scripts/m1-survival.sh`
- Browser agent: limited to 1 instance (~2GB RAM), per Rule 13
- `logs/m1-cooler.log` — temperature monitoring log

### CI (Ubuntu Latest / ubuntu-latest)
- Python 3.12 (pinned in all workflows)
- Node 22 (frontend), Node 20 (mekong-engine)
- pnpm via `pnpm/action-setup@v4`

### Production (Fly.io)
- Docker image: `python:3.12-slim`
- Region: `sin` (Singapore)
- Memory: 512MB shared CPU
- Auto-start/stop machines enabled
- Persistent volume: `agencyos_data` → `/data`

### Cloudflare Workers (mekong-engine)
- Node 20, pnpm
- Wrangler deploy via `cloudflare/wrangler-action@v3`
- No persistent storage (stateless Workers)

---

## Makefile Targets (Dev Ops)

```bash
make setup          # Full dev setup
make setup-quick    # Non-interactive setup
make health         # Health check
make install        # pip install -e .
make dev            # pip install -e ".[dev]"
make test           # pytest tests/ -v
make lint           # ruff + mypy
make format         # ruff format
make server         # uvicorn dev server (port 8000)
make build          # pnpm build (monorepo)
make clean          # Remove build artifacts
make start-daemon   # Start Tôm Hùm daemon
make stop-daemon    # Stop daemon
make daemon-status  # Check daemon status
make start-gateway  # Start API gateway
make regenerate     # Regenerate + validate factory contracts
```

---

## Environment Health Check

```bash
# Run full health check
make health
# OR
bash scripts/health-check.sh

# Expected output (all green):
# ✅ Python 3.9+          3.9.6
# ✅ Node.js 18+          v22.x.x
# ✅ pnpm                 9.x.x
# ✅ Git                  2.x.x
# ✅ .env file            exists
# ✅ CC CLI (claude)      installed
# ✅ mekong command       available
# ✅ pytest               7.x.x
# ✅ ~/.claude/settings   configured
```
