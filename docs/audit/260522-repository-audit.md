# Repository Audit — Mekong CLI v6.0.0

**Date:** 2026-05-22 | **Auditor:** Claude Opus 4.6 | **Confidence:** High (code-verified)

---

## Executive Summary

Mekong CLI is a **16GB monorepo** containing an AI-operated business platform ("one-person company"). It has two distinct execution planes:

1. **Python backend** (`src/`) — FastAPI gateway + Typer CLI + PEV engine + 30+ subsystems (~134K LOC)
2. **TypeScript frontend** (`apps/` + `packages/`) — 38 apps + 58 packages, pnpm monorepo with Turbo

Additionally, ~16K markdown files define **commands, skills, agents** consumed by Claude Code and Gemini as system prompts.

**Key stats:** 16K .py files | 74K .ts/.tsx files | 16K .md files | 305 test files | pnpm + poetry dual package managers

---

## 1. Top-Level Directory Map

### Core Application Code

| Directory | Purpose | Tech | Runtime Role | Risk |
|-----------|---------|------|-------------|------|
| `src/` | Python backend — API gateway, CLI, PEV engine, billing, auth, agents | Python 3.11, FastAPI, Typer | **PRIMARY** — runs `api.cashclaw.cc` gateway + CLI | **HIGH** — core business logic |
| `apps/` | 38 frontend/fullstack apps (dashboard, IDE, landing, trading, etc.) | Next.js, React, Vite | Web UIs, deployed to CF Pages | MEDIUM — user-facing |
| `packages/` | 58 shared TS packages (SDKs, engines, UI, billing types) | TypeScript, ESM | Libraries consumed by apps | MEDIUM — shared deps |
| `seed/` | Standalone Python CLI runtime (stdlib-only, Phase 01) | Python, Ollama | Local agent execution | LOW — self-contained |

### Agent/AI Configuration

| Directory | Purpose | Consumer | Risk |
|-----------|---------|----------|------|
| `.claude/` | 24 commands + 39 skills + 22 agents + hooks for Claude Code | Claude Code CLI | LOW — config only |
| `.agent/` | 106 subagents + 40 workflows + skills for Gemini/Antigravity | Gemini CLI | LOW — config only |
| `factory/contracts/` | 567 JSON machine contracts (command specs) | PEV engine classifier | LOW — data |
| `clipmart/` | "Paperclip Agent Companies" — installable dept templates | `mekong install` CLI | LOW — templates |

### Infrastructure & Operations

| Directory | Purpose | Tech | Risk |
|-----------|---------|------|------|
| `scripts/` | 100+ shell scripts — wrapper, init, deploy, health, dev setup | Bash | **HIGH** — operational glue |
| `infra/` | CF Workers deploy templates (3-layer) | Wrangler, TOML | MEDIUM |
| `.github/workflows/` | 15 CI/CD workflows | GitHub Actions | **HIGH** — deploy pipeline |
| `docker/` | Docker configs + compose files | Docker | LOW — optional |
| `.husky/` | Git pre-commit hooks | Husky | LOW |
| `bin/` | CLI entry points | Shell | MEDIUM |
| `ide-core/` | TS CLI compiler + engine-farm (multi-model A/B testing) | TypeScript, Bun | MEDIUM |

### Supporting

| Directory | Purpose | Risk |
|-----------|---------|------|
| `docs/` | 88 documentation files | LOW |
| `tests/` | 177 test directories + files (Python + TS) | LOW |
| `plans/` | 83 implementation plan directories (gitignored content) | LOW |
| `mekong/` | Python adapters, infra templates, daemon configs | MEDIUM |
| `recipes/` | 82 DAG recipe definitions (multi-step workflows) | LOW |
| `models/` | Data models/schemas | LOW |
| `tools/` | Capability tools (file_system, browser) | LOW |

---

## 2. apps/ — 38 Applications

### Tier 1: Active & Deployed

| App | Purpose | Stack | Deploy Target |
|-----|---------|-------|--------------|
| `well` | WellNexus RaaS portal (v3.0.0) | React 19, Vite, Zustand, i18next | CF Pages |
| `dashboard` | Central management dashboard | Next.js 16, React 19, Polar/Stripe | Self-hosted |
| `mekong-ide` | Web IDE interface | Next.js 15, React 19 | CF Pages |
| `algo-trader-remote` | Algo trading bot + dashboard | Fastify 5, Prisma, CCXT, TensorFlow.js | Cloud |
| `admin` | Admin control panel | Next.js 16 | CF Pages |

### Tier 2: Scaffolded / Early Stage

| App | Purpose | Status |
|-----|---------|--------|
| `agencyos-web`, `agencyos-landing` | Agency marketing/platform | Scaffolded |
| `ide-ui` | IDE UI components (port 3010) | Early |
| `landing` | Main marketing landing page | Active |
| `tauri-shell` | Desktop app shell | Scaffolded |
| `agi-sops` | AGI SOP execution (Node→Python bridge) | Active/scaffolded |

### Tier 3: Projects / Templates / Legacy

28 additional apps including: `crm`, `saas-dashboard`, `roi-calculator`, `raas-demo`, `raas-gateway`, `openclaw-worker`, `starter-template`, `vibe-coding-cafe`, `sa-dec-flower-hunt`, `com-anh-duong-10x`, etc.

**Observation:** Many apps appear to be scaffolded placeholders or customer-specific projects. Only ~5-8 apps show active development.

---

## 3. packages/ — 58 Packages

### Core SDK (Published to npm)

| Package | Version | Purpose | Consumers |
|---------|---------|---------|-----------|
| `mekong-cli-core` | 0.3.0 | Main CLI entry point (319+ commands) | End users |
| `openclaw-engine` | 1.0.0 | Mission orchestration SDK | CLI, gateway |
| `mekong-engine` | 3.2.0 | CF Workers PEV engine (Hono + D1) | Edge runtime |
| `cli-adapter` | 1.0.0 | CLI ↔ OpenClaw bridge | CLI |
| `raas-sdk` | 1.0.0 | RaaS Gateway TS SDK | Frontend apps |

### Business Domain (Vibe Ecosystem) — 32 packages

`vibe`, `vibe-ui`, `vibe-auth`, `vibe-payment`, `vibe-stripe`, `vibe-subscription`, `vibe-supabase`, `vibe-crm`, `vibe-money`, `vibe-embedded-finance`, `vibe-analytics`, `vibe-agents`, `vibe-arbitrage-engine`, `vibe-payos-billing-types`, etc.

**Status:** Mix of active and placeholder. Many are `0.0.1` scaffolds.

### Specialized

| Package | Purpose | Status |
|---------|---------|--------|
| `cleo-new` | CleoCode agent framework (v2026.5.87, 30+ internal packages) | Very active |
| `i18n` | Shared i18n (React hooks, Astro integration, locale extraction) | Active |
| `ui` | React component library (shadcn/Tailwind) | Active |
| `tokens` | CSS design tokens | Active |
| `observability` | Structured logging, health checks | Active |
| `agi-evolution` | Self-improving agent framework | Published |
| `vc-governance` | ISO compliance, data room, exit engine | Published |
| `license-sdk` | License key generation/verification | Active |
| `zalo-parser` | Zalo OA message parser (CF Worker) | Active |

---

## 4. src/ — Python Backend (30+ Subsystems)

### Entry Points

| File | Role | How to Run |
|------|------|-----------|
| `src/gateway.py` | FastAPI API server (v3.3.0) | `uvicorn src.gateway:app --port 8000` |
| `src/main.py` | Typer CLI entry | `python3 src/main.py` or `mekong` |
| `src/daemon/__main__.py` | Heartbeat scheduler daemon | `python3 -m src.daemon` |

### Subsystem Map

| Module | Files | Purpose | Confidence |
|--------|-------|---------|-----------|
| `src/core/` | 60+ | PEV engine, LLM client, agents, billing, auth, telemetry, DAG scheduler | High |
| `src/api/` | 33 | FastAPI routes — missions, webhooks, VN pilot, billing, orgs | High |
| `src/raas/` | 65 | RaaS billing engine — credits, checkout, marketplace, webhooks, tenants | High |
| `src/cli/` | 15+ | Typer CLI command groups — cook, workflow, recipe, SDLC, system | High |
| `src/commands/` | 40+ | CLI command implementations (ke_toan, zalo_oa, analytics, etc.) | High |
| `src/agents/` | ~10 | Agent implementations (Git, File, Shell, LeadHunter, ContentWriter) | High |
| `src/daemon/` | 34 | Autonomous dispatch — worker pool, DLQ, circuit breaker, heartbeat | High |
| `src/billing/` | ~5 | Billing integration layer | Medium |
| `src/auth/` | ~5 | Auth middleware, JWT, sessions | High |
| `src/db/` | 10+ | PostgreSQL schema, migrations, repository pattern | High |
| `src/models/` | ~10 | Pydantic models | Medium |
| `src/security/` | ~5 | Security utilities | Medium |
| `src/telemetry/` | ~5 | OpenTelemetry + Sentry init | Medium |
| `src/metering/` | ~3 | Usage metering | Medium |
| `src/usage/` | 3 | Usage tracker + decorators | High |
| `src/studio/` | 2 | Venture studio models | Low |
| `src/polymarket/` | ~3 | Polymarket prediction market integration | Low |
| `src/strategies/` | ~5 | Trading strategies (polymarket) | Low |
| `src/jobs/` | ~3 | Background job definitions | Medium |
| `src/i18n/` | ~2 | Internationalization | Low |
| `src/a2ui/` | ~3 | Agent-to-UI bridge | Low |
| `src/sops/` | ~5 | Standard Operating Procedures | Low |
| `src/binh_phap/` | ~3 | Strategy framework | Low |
| `src/pages/` | ~3 | Page renderers | Low |
| `src/services/` | ~5 | Service layer | Medium |
| `src/analytics/` | 3 | ROI dashboard, analytics service | Medium |
| `src/config/` | ~3 | Configuration management | Medium |
| `src/middleware/` | 3 | Auth middleware, license gate | High |
| `src/lib/` | ~5 | Shared utilities + RaaS gate | Medium |
| `src/components/` | ~8 | Network, robot-interface, withdrawal components | Low |

---

## 5. scripts/ — Operational Glue (100+ Scripts)

### Critical Scripts

| Script | Purpose | Risk |
|--------|---------|------|
| `mekong-wrapper.sh` | Universal CLI dispatcher (routes to claude/gemini/qwen) | **HIGH** |
| `shell-init.sh` | Shell initialization (aliases, PATH, env) | **HIGH** |
| `health-check.sh` | Production health verification | HIGH |
| `setup-dev.sh` | Developer environment setup | MEDIUM |

### Categories (estimated)

- **CLI wrappers:** ~10 scripts (mekong-*, provider routing)
- **Deploy:** ~15 scripts (CF Workers, Pages, gateway)
- **Dev tools:** ~20 scripts (setup, lint, format, seed)
- **VN Hub:** ~10 scripts (pilot onboard, metrics, polls)
- **Daemon/ops:** ~15 scripts (health, monitor, backup)
- **Build:** ~10 scripts (compile, bundle, sign)
- **Misc/legacy:** ~20+ scripts

---

## 6. CI/CD — 15 GitHub Actions Workflows

| Workflow | Trigger | Purpose | Status |
|----------|---------|---------|--------|
| `ci.yml` | push main/master, PR | Backend (Python 3.11/3.12) + TS packages build | Active |
| `gates.yml` | (imported by ci) | Lint, type-check, tests, coverage | Active |
| `security-hardening.yml` | scheduled/manual | Security scans | Active |
| `deploy.yml` | push main | Full deployment pipeline | Active |
| `deploy-ide.yml` | push main | IDE app deployment | Active |
| `deploy-landing.yml` | push main | Landing page deployment | Active |
| `deploy-site.yml` | push main | Site deployment | Active |
| `test.yml` | PR/push | Test suite | Active |
| `ai-native-ci.yml` | (conditional) | AI-native CI checks | Active |
| `agent-core.yml` | (conditional) | Agent core tests | Active |
| `agent-forest.yml` | (conditional) | Agent forest tests | Active |
| `claude-code-guards.yml` | (conditional) | Claude Code guard rails | Active |
| `mekongd.yml` | (conditional) | Daemon service | Active |
| `docsops.yml` | (conditional) | Documentation operations | Active |
| `factory-validate.yml` | (conditional) | Factory contract validation | Active |

---

## 7. tests/ — Testing Infrastructure

**Framework:** pytest (Python) + vitest (TypeScript)

**Config:** `pyproject.toml` (pytest section) + `vitest.config.ts`

**Test paths:** `tests/` (main) — excludes `node_modules`, `apps/`, `packages/` (they have own tests)

**Test count:** 305 test files total (across all languages)

**Notable test directories:**
- `tests/vn/` — 100+ tests for VN Hub pilot features
- `tests/seed/` — Seed layer unit tests
- `tests/raas/` — RaaS billing/credit tests
- `tests/core/` — PEV engine tests
- `tests/api/` — Gateway API tests

**Coverage config:** Covers `src/` but excludes: raas/, main.py, nlp_commander.py, telegram_bot.py, memory_client.py, pages/, exceptions.py, binh_phap/, commands/, cli/, agi_loop.py, cc_spawner.py, llm_client.py, config.py

**Observation:** Coverage exclusion list is extensive — many critical paths (llm_client, commands, cli) are excluded. This is a testing gap.

---

## 8. docs/ — 88 Documentation Files

### Key Documents

| File | Purpose | Last Updated |
|------|---------|-------------|
| `codebase-summary.md` | Architecture overview | 2026-04-25 |
| `system-architecture.md` | Detailed system architecture | 2026-04-16 |
| `deployment-guide.md` | Deployment instructions | Unknown |
| `code-standards.md` | Coding standards | Unknown |
| `CLI_REFERENCE.md` | CLI command reference | Unknown |
| `api-reference.md` | API endpoint docs | Unknown |
| `getting-started.md` | Quick start guide | Unknown |
| `ONBOARDING.md` | New developer onboarding | Unknown |

**Observation:** Many docs reference pre-v6.0 architecture. `codebase-summary.md` (2026-04-25) is the most current. Several docs may be stale.

---

## Unresolved Questions

1. How many of the 38 apps are actually deployed and receiving traffic?
2. What's the actual test pass rate? (305 files exist but coverage exclusions are broad)
3. How many of the 58 packages have been published to npm vs are workspace-only?
4. Is `cleo-new` (nested monorepo in packages/) intentionally embedded or should it be extracted?
5. What's the relationship between `src/raas/` (Python) and `packages/raas-sdk/` (TS)?
6. Are the 567 factory contracts still in sync with the current command definitions?
