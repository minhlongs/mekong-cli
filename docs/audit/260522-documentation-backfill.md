# Documentation Backfill — Mekong CLI v6.0.0

**Date:** 2026-05-22 | **Auditor:** Claude Opus 4.6

This document identifies documentation gaps and provides backfill content for each.

---

## 1. Quick Start Guide (MISSING → BACKFILLED)

### Prerequisites

- macOS (M1/M2/M3) or Linux
- Python 3.9–3.12
- Node.js 18+ with pnpm 9+
- Poetry (Python package manager)
- Git

### Install

```bash
# Clone
git clone https://github.com/mekong-cli/mekong-cli.git ~/mekong-cli
cd ~/mekong-cli

# Python deps
poetry install

# TypeScript deps
pnpm install

# Shell init (add to ~/.zshrc)
source ~/mekong-cli/scripts/shell-init.sh
```

### First Run

```bash
# Interactive mode (CC CLI with all mekong commands)
mekong

# Run a command
mekong cook "build a landing page"

# Check health
curl http://localhost:8000/healthz
```

### Provider Setup

Set at least one LLM provider:

```bash
# Option A: OpenRouter (recommended — aggregates all providers)
export LLM_BASE_URL=https://openrouter.ai/api/v1
export LLM_API_KEY=sk-or-v1-yourkey
export LLM_MODEL=anthropic/claude-sonnet-4

# Option B: Direct Anthropic
export ANTHROPIC_API_KEY=sk-ant-yourkey

# Option C: Local (free, requires Ollama)
brew install ollama
ollama pull qwen3:32b
# No env vars needed — auto-detected at localhost:11434
```

---

## 2. Local Development Guide (INCOMPLETE → BACKFILLED)

### Start API Gateway

```bash
uvicorn src.gateway:app --port 8000 --reload
# Health check: http://localhost:8000/healthz
```

### Start Frontend (any app)

```bash
pnpm dev                    # All apps via Turbo
pnpm dev --filter=well      # Single app (WellNexus)
pnpm dev --filter=dashboard # Dashboard only
```

### Run Tests

```bash
# Python
python3 -m pytest tests/ -v              # All tests
python3 -m pytest tests/vn/ -v           # VN Hub tests only
python3 -m pytest tests/core/ -v         # Core engine tests

# TypeScript
pnpm test                                # All packages via vitest
pnpm test --filter=openclaw-engine       # Single package
```

### Build

```bash
pnpm build                  # All packages (Turbo, concurrency=4)
pnpm build --filter=well    # Single app
```

### Common Aliases (from shell-init.sh)

| Alias | Command | Purpose |
|-------|---------|---------|
| `mekong` | CC CLI with mekong commands | Interactive CLI |
| `mekong-opus` | CC CLI with Opus model | Premium AI |
| `mekong-sonnet` | CC CLI with Sonnet model | Standard AI |
| `mekong-qwen` | CC CLI with Qwen model | Free/cheap AI |
| `mekong-cto` | CTO daemon mode | Autonomous execution |
| `mekong-continue` | Resume last session | Session recovery |
| `mekong-status` | Show API config | Debug provider |

---

## 3. Environment Variables Documentation (PARTIAL → BACKFILLED)

133 variables in `.env.example`. Key groups:

### LLM Providers (REQUIRED: at least one)

| Variable | Example | Purpose |
|----------|---------|---------|
| `LLM_BASE_URL` | `https://openrouter.ai/api/v1` | Primary LLM endpoint |
| `LLM_API_KEY` | `sk-or-v1-...` | Primary LLM key |
| `LLM_MODEL` | `anthropic/claude-sonnet-4` | Default model |
| `OPENROUTER_API_KEY` | `sk-or-v1-...` | Fallback #1 |
| `DASHSCOPE_API_KEY` | `sk-...` | Fallback #2 (Qwen) |
| `DEEPSEEK_API_KEY` | `sk-...` | Fallback #3 |
| `ANTHROPIC_API_KEY` | `sk-ant-...` | Fallback #4 |
| `OPENAI_API_KEY` | `sk-...` | Fallback #5 |
| `GOOGLE_API_KEY` | `AI...` | Fallback #6 (Gemini) |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Fallback #7 (local) |

### Billing (REQUIRED for production)

| Variable | Example | Purpose |
|----------|---------|---------|
| `POLAR_ACCESS_TOKEN` | `pat_...` | Polar.sh API access |
| `STRIPE_SECRET_KEY` | `sk_...` | Legacy Stripe (migration in progress) |
| `STRIPE_WEBHOOK_SECRET` | `whsec_...` | Stripe webhook verification |

### Auth

| Variable | Example | Purpose |
|----------|---------|---------|
| `JWT_SECRET=REDACTED_KEY` | (random 64 chars) | JWT signing |
| `MEKONG_ADMIN_TOKEN` | (token_urlsafe 32) | Admin API access |
| `SUPABASE_URL` | `https://xxx.supabase.co` | Frontend auth |
| `SUPABASE_ANON_KEY` | `eyJ...` | Frontend auth |

### VN Hub

| Variable | Example | Purpose |
|----------|---------|---------|
| `MEKONG_USER_ID` | `opc_001_abc123` | Pilot user identity |
| `MEKONG_VIETQR_PROVIDER` | `sepay` | Bank transfer provider |
| `MEKONG_VIETQR_WEBHOOK_SECRET` | (HMAC secret) | Webhook verification |
| `MEKONG_SIGNUP_WEBHOOK_URL` | `https://hooks.zapier.com/...` | Signup notifications |

### Infrastructure

| Variable | Example | Purpose |
|----------|---------|---------|
| `DATABASE_URL` | `postgresql://...` | PostgreSQL connection |
| `SENTRY_DSN` | `https://...@sentry.io/...` | Error tracking |
| `CF_ACCOUNT_ID` | (Cloudflare account) | CF deployment |
| `CF_API_TOKEN` | (Cloudflare token) | CF API access |

---

## 4. Testing Guide (MISSING → BACKFILLED)

### Test Frameworks

| Framework | Language | Config | Command |
|-----------|----------|--------|---------|
| pytest | Python | pyproject.toml `[tool.pytest]` | `python3 -m pytest` |
| vitest | TypeScript | vitest.config.ts | `pnpm test` |

### Test Structure

```
tests/
├── vn/          # VN Hub pilot (100+ tests)
├── seed/        # Seed layer unit tests
├── raas/        # RaaS billing/credit tests
├── core/        # PEV engine tests
├── api/         # Gateway API tests
└── ...          # 258 total pytest files

apps/*/tests/    # App-specific tests (vitest)
packages/*/tests/# Package-specific tests (vitest)
```

### Running Tests

```bash
# Full Python suite (6,160 tests)
python3 -m pytest tests/ -v

# With coverage
python3 -m pytest tests/ --cov=src --cov-report=html

# Specific subsystem
python3 -m pytest tests/vn/ -v -k "test_pilot"
python3 -m pytest tests/core/ -v -k "test_planner"

# TypeScript (5,843 tests)
pnpm test
pnpm test --filter=openclaw-engine
pnpm test --filter=vibe-auth
```

### Coverage Gaps (Known)

The following paths are EXCLUDED from coverage in `pyproject.toml`:
- `src/raas/` — Billing engine (20K LOC, revenue-critical)
- `src/core/llm_client.py` — LLM provider chain
- `src/commands/`, `src/cli/` — CLI commands
- `src/config.py`, `src/main.py` — Config and entry point

These exclusions mean coverage percentage overstates actual coverage of business-critical code.

### CI/CD Test Integration

Tests run automatically via GitHub Actions:
- `ci.yml` — Python 3.11 + 3.12 matrix on push to main/master
- `gates.yml` — Lint, typecheck, tests, coverage gates
- `test.yml` — PR validation

---

## 5. Deployment Guide (PARTIAL → BACKFILLED)

### Cloudflare Pages (Frontend)

```bash
# Auto-deploy: push to main → GitHub Actions → CF Pages
git push origin main

# Manual deploy (if CI bypassed)
cd apps/well && npx wrangler pages deploy dist
```

### Cloudflare Workers (Edge API)

```bash
# Scaffold new worker
bash mekong/infra/scaffold.sh myproject startup

# Deploy
npx wrangler deploy

# Verify
curl https://your-worker.workers.dev/healthz
```

### FastAPI Gateway (Self-hosted)

```bash
# Production (macOS LaunchDaemon)
# Plist: /Library/LaunchDaemons/com.mekong.gateway.plist
sudo launchctl load /Library/LaunchDaemons/com.mekong.gateway.plist

# Development
uvicorn src.gateway:app --port 8000 --reload

# Verify
curl http://localhost:8000/health
```

### 3-Layer Architecture

| Layer | Platform | Deploy Method | Cost |
|-------|----------|---------------|------|
| Frontend | CF Pages | git push → CI | $0 |
| Edge API | CF Workers | wrangler deploy | $0 |
| Backend | Self-hosted (FastAPI) | LaunchDaemon | Server cost |
| Data | CF D1 + KV + R2 | wrangler migrations | $0 (free tier) |

---

## 6. Architecture Overview (EXISTS → UPDATED POINTERS)

Existing: `docs/system-architecture.md` (2026-04-16, stale)
New: `docs/audit/260522-architecture-understanding.md` (2026-05-22, current)

The new architecture document covers:
- 5 system entry points (CLI, Gateway, Daemon, IDE, Seed)
- 5 request/data flows (CLI, API Mission, VN Pilot, VietQR, Polar)
- Background jobs and schedulers
- 18 external integrations
- State management across 3 layers
- Full persistence schema
- Auth/AuthZ flow (5 auth systems)
- Deployment topology diagram
- Feature flags and env handling

---

## 7. Glossary (MISSING → BACKFILLED)

| Term | Definition |
|------|-----------|
| **PEV** | Plan-Execute-Verify — core orchestration loop in src/core/ |
| **MCU** | Mission Credit Unit — billing unit. 1 MCU = 1 credit |
| **RaaS** | Robot-as-a-Service — billing engine in src/raas/ |
| **OpenClaw** | The AI agent identity ("I am OpenClaw. I run this company.") |
| **Tôm Hùm** | "Lobster" — codename for the daemon autonomous dispatch system |
| **Binh Pháp** | Art of War (孫子兵法) — quality framework mapped to software delivery |
| **Clipmart** | Marketplace for installable agent company department templates |
| **Factory Contract** | JSON machine contract in factory/contracts/ consumed by PEV classifier |
| **VN Hub** | Vietnamese one-person business platform (ke_toan, thue, zalo_oa) |
| **Seed** | Phase 01 minimal runtime (stdlib-only Python, Ollama) |
| **Tree** | Phase 02 full Python backend (FastAPI, PEV engine) |
| **Forest** | Phase 03 TypeScript monorepo (38 apps, 58 packages) |
| **Land** | Phase 04 deployed production infrastructure |
| **CC CLI** | Claude Code CLI — the inner engine invoked by mekong wrapper |
| **Mekong Wrapper** | scripts/mekong-wrapper.sh — universal CLI entry point |
| **Vibe** | TypeScript package namespace for business domain libraries |
| **Jidoka** | Toyota "stop the line" — daemon quality check that halts on failures |
| **DLQ** | Dead Letter Queue — failed daemon tasks stored for retry/inspection |
| **Circuit Breaker** | Pattern in LLM client: 3 failures → 15s cooldown per provider |
| **DAG Recipe** | Directed Acyclic Graph workflow definition in recipes/ |

---

## 8. Onboarding Notes (MISSING → BACKFILLED)

### For New Developers

1. **Start here:** Read `CLAUDE.md` (project root) — it's the constitution
2. **Understand the layers:** CLI → Gateway → PEV → Agents → LLM
3. **Pick your plane:**
   - Python backend? → `src/`, `tests/`, `pyproject.toml`
   - TypeScript frontend? → `apps/`, `packages/`, `pnpm`
   - AI config? → `.claude/`, `.agent/`, `factory/`

4. **Don't be overwhelmed by size:**
   - Only ~5-8 apps are actively developed (well, dashboard, mekong-ide, algo-trader, admin)
   - Only ~10 packages are actively maintained
   - 28+ apps and 20+ packages are scaffolds

5. **Key files to read first:**
   - `CLAUDE.md` — Architecture and conventions
   - `src/gateway.py` — API entry point (210 lines)
   - `src/core/orchestrator.py` — PEV loop
   - `src/core/llm_client.py` — LLM provider chain
   - `.claude/commands/cook.md` — Most-used command

6. **Running things:**
   ```bash
   source ~/mekong-cli/scripts/shell-init.sh  # Aliases
   mekong                                       # Interactive CLI
   uvicorn src.gateway:app --port 8000          # API server
   python3 -m pytest tests/ -v                  # Tests
   ```

### For AI Agents

1. Read `CLAUDE.md` for constitution and command namespace
2. Commands are in `.claude/commands/` (342+ files)
3. Skills are in `.claude/skills/` (542 files)
4. Factory contracts in `factory/contracts/` (567 JSON files)
5. Always use `mekong` wrapper, never bare `claude`
6. PEV engine is in `src/core/` — plan, execute, verify
7. MCU billing checks run before every mission

---

## 9. Documentation Inventory & Status

| Document | Path | Last Updated | Status |
|----------|------|-------------|--------|
| README.md | / | 2026-05 | Current |
| CLAUDE.md | / | 2026-05 | Current (constitution) |
| ARCHITECTURE.md | / | 2026-05 | Current |
| STRATEGY.md | / | 2026-05 | Current |
| codebase-summary.md | docs/ | 2026-04-25 | Slightly stale |
| system-architecture.md | docs/ | 2026-04-16 | **Stale** — superseded by audit |
| code-standards.md | docs/ | Unknown | Needs review |
| deployment-guide.md | docs/ | Unknown | **Incomplete** — backfilled above |
| CLI_REFERENCE.md | docs/ | Unknown | Needs review |
| api-reference.md | docs/ | Unknown | Needs review |
| getting-started.md | docs/ | Unknown | **Incomplete** — backfilled above |
| ONBOARDING.md | docs/ | Unknown | **Missing** — backfilled above |
| Repository Audit | docs/audit/ | 2026-05-22 | **NEW** |
| Architecture Understanding | docs/audit/ | 2026-05-22 | **NEW** |
| Knowledge Extraction | docs/audit/ | 2026-05-22 | **NEW** |
| Gap & Risk Report | docs/audit/ | 2026-05-22 | **NEW** |
| Documentation Backfill | docs/audit/ | 2026-05-22 | **NEW** (this file) |

### Recommended Doc Updates

1. **system-architecture.md** — Replace with pointer to `docs/audit/260522-architecture-understanding.md`
2. **getting-started.md** — Incorporate Quick Start from Section 1 above
3. **ONBOARDING.md** — Create standalone file from Section 8 above
4. **deployment-guide.md** — Incorporate Deployment Guide from Section 5 above
5. **Create testing-guide.md** — From Section 4 above

---

## Unresolved Questions

1. Should scaffold apps (28+) be archived to a separate repo or deleted?
2. Should `docs/system-architecture.md` be updated in-place or replaced with the audit version?
3. Is there an internal wiki or Notion with additional documentation not in the repo?
