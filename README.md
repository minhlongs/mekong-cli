<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://img.shields.io/badge/🐉_MEKONG_CLI-0d1117?style=for-the-badge&labelColor=0d1117&color=0d1117">
    <img alt="Mekong CLI" src="https://img.shields.io/badge/🐉_MEKONG_CLI-ffffff?style=for-the-badge&labelColor=ffffff&color=ffffff">
  </picture>
</p>

<h1 align="center">Mekong CLI</h1>

<p align="center"><strong>The terminal OS for AI-native founders.</strong></p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-22c55e?style=flat-square" alt="MIT" /></a>
  <img src="https://img.shields.io/badge/Python-3.9+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.9+" />
  <img src="https://img.shields.io/badge/v3.1.0-8B5CF6?style=flat-square" alt="v3.1.0" />
  <img src="https://img.shields.io/badge/AGI_Score-97.6%2F100-22c55e?style=flat-square" alt="AGI Score 97.6/100" />
  <a href="https://github.com/longtho638-jpg/mekong-cli/actions"><img src="https://img.shields.io/github/actions/workflow/status/longtho638-jpg/mekong-cli/ci.yml?style=flat-square&label=CI" alt="CI" /></a>
</p>

<p align="center">
  <strong>Open-source AI agent framework for autonomous task execution.</strong><br/>
  Plan → Execute → Verify — with built-in credit billing for RaaS.<br/>
  <em>AGI v2: 9 subsystems • 97.6/100 score • Self-healing pipeline</em>
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> •
  <a href="#how-it-works">How It Works</a> •
  <a href="#commands">Commands</a> •
  <a href="#agencyos-raas">AgencyOS</a> •
  <a href="#roadmap">Roadmap</a>
</p>

---

Mekong CLI is an autonomous agent framework that plans, executes, and verifies — then rolls back if anything breaks. 55 commands. From `mekong cook` to `/founder ipo-day`. For founders who run their company from the terminal.

## Quick Start

```bash
pip install mekong-cli              # or: git clone + pip install -e ".[dev]"
export LLM_BASE_URL="https://api.openai.com/v1"
export LLM_API_KEY="sk-..."
mekong cook "Build me a SaaS landing page"
```

### Works with every LLM provider

| Provider | Base URL | Cost |
|----------|----------|------|
| **OpenAI** | `https://api.openai.com/v1` | Pay-per-use |
| **Google Gemini** | `https://generativelanguage.googleapis.com/v1beta/openai` | Free tier |
| **DashScope (Qwen)** | `https://coding-intl.dashscope.aliyuncs.com/v1` | [Free credits →](https://www.alibabacloud.com/campaign/benefits?referral_code=A9245T) |
| **Ollama (local)** | `http://localhost:11434/v1` | Free |
| **Any proxy** | Your OpenAI-compatible endpoint | Custom |

## The Journey

```
IDEA ─── BUILD ─── SEED ─── A ─── B ─── C ─── PRE-IPO ─── IPO ─── PUBLIC
  │        │        │       │     │     │        │          │         │
validate  cook    raise   pitch  grow  scale  pre-ipo    ipo-day  public-co
brand     fix     credits  vc/*  hire         s1          insider  succession
          plan                   legal        roadshow
```

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                    AgencyOS (RaaS Layer)                     │
│  Dashboard · /v1/missions · MCU Billing · Polar.sh Webhooks │
├─────────────────────────────────────────────────────────────┤
│                   OpenClaw (Orchestrator)                    │
├──────────┬──────────┬──────────┬──────────────────────────┤
│  📋 PLAN  │  ⚡ EXEC  │  ✅ VERIFY │     🤖 AGENTS           │
│ planner  │ executor │ verifier │  git·file·shell·db·lead  │
├──────────┴──────────┴──────────┴──────────────────────────┤
│                        LLM Router                           │
│  Claude · Gemini · Qwen · Ollama · Antigravity Proxy:9191  │
└─────────────────────────────────────────────────────────────┘
```

| Phase | Module | What It Does |
|-------|--------|-------------|
| **Plan** | `src/core/planner.py` | LLM decomposes goal into ordered steps with dependency graph |
| **Execute** | `src/core/executor.py` | Runs shell/code/API tasks in parallel where safe |
| **Verify** | `src/core/verifier.py` | Exit codes, tests, types, file checks, LLM assessment |
| **Orchestrate** | `src/core/orchestrator.py` | Coordinates PEV loop, rollback, self-healing |

## Quick Demo

```bash
$ mekong cook "Add Stripe billing to my FastAPI app"
$ /founder validate --product "AI coding assistant for solo devs"
$ /founder pitch --investor yc --rounds 10
$ /founder vc/term-sheet --file term.pdf
$ /founder ipo-day --exchange nasdaq
```

## Commands

### Core (13)

| Command | Description |
|---------|-------------|
| `cook` | Full PEV pipeline — plan, execute, verify |
| `fix` | Debug and fix bugs with auto-rollback |
| `plan` | Create implementation plan (dry run) |
| `review` | Code quality review |
| `status` | System health check |
| `help` | Command reference |
| `deploy` | Deployment orchestration |
| `launch` | Launch copy for PH, HN, Reddit |
| `credits` | Find startup credits and programs |
| `pricing` | Pricing strategy and tier modeling |
| `raise` | Fundraising prep (tactical) |
| `fundraise` | Fundraising playbook (strategic) |
| `cofounder` | Co-founder strategy |

### Company (6)

| Command | Description |
|---------|-------------|
| `company/init` | Initialize agentic company (8 AI agents) |
| `company/agent` | Manage agents — list, ask, train |
| `company/billing` | MCU balance and billing |
| `company/report` | Business intelligence reports |
| `company/run` | Universal task runner |
| `company/workflow` | Automated workflows |

### Founder (9)

| Command | Description |
|---------|-------------|
| `founder/validate` | Customer discovery and PMF |
| `founder/brand` | Brand identity and positioning |
| `founder/pitch` | Pitch deck practice with AI investor |
| `founder/metrics` | KPI dashboard and anomaly detection |
| `founder/hire` | Agentic recruiting and interview kits |
| `founder/legal` | Legal checklist and IP protection |
| `founder/week` | Weekly CEO rhythm |
| `founder/grow` | GTM playbook execution |
| `founder/secondary` | Founder liquidity mechanics |

### VC (5)

| Command | Description |
|---------|-------------|
| `founder/vc/bootstrap` | Path to $1M ARR without VC |
| `founder/vc/cap-table` | Dilution modeling and exit waterfall |
| `founder/vc/negotiate` | BATNA tactics and counter-offers |
| `founder/vc/term-sheet` | Term sheet red flag detection |
| `founder/vc-map` | VC landscape mapping |

### IPO (7)

| Command | Description |
|---------|-------------|
| `founder/ipo/pre-ipo-prep` | 18-month IPO readiness audit |
| `founder/ipo/s1` | S-1 prospectus framework |
| `founder/ipo/roadshow` | 2-week roadshow sprint |
| `founder/ipo/ipo-day` | IPO Day execution playbook |
| `founder/ipo/public-co` | Public company quarterly rhythm |
| `founder/ipo/insider` | Insider compliance and IR |
| `founder/ipo/succession` | Post-IPO: buybacks, M&A, CEO transition |

### RaaS (5)

| Command | Description |
|---------|-------------|
| `raas/billing` | Billing integration (Polar.sh) |
| `raas/bootstrap` | Bootstrap RaaS service |
| `raas/deploy` | Deploy RaaS to production |
| `raas/mission` | Dispatch AGI mission |
| `raas/status` | RaaS health check |

### Bootstrap (3)

| Command | Description |
|---------|-------------|
| `bootstrap/auto` | Auto bootstrap project |
| `bootstrap/auto/fast` | Quick bootstrap |
| `bootstrap/auto/parallel` | Parallel bootstrap |

## CLI Flags

| Flag | Effect |
|------|--------|
| `--verbose / -v` | Step-by-step execution details |
| `--dry-run / -n` | Plan only, no execution |
| `--strict` | Fail on first verification error |
| `--json / -j` | Machine-readable JSON output |

## AgencyOS RaaS

AgencyOS is the hosted platform built on Mekong CLI — a Revenue as a Service layer with MCU credit billing and multi-tenant orchestration.

### Credit Tiers

| Tier | Price | MCU Credits |
|------|-------|-------------|
| **Starter** | $29/mo | 500 MCU |
| **Growth** | $99/mo | 2,000 MCU |
| **Premium** | $299/mo | Unlimited MCU + white-label |

| Complexity | MCU Cost | Example |
|-----------|----------|---------|
| `simple` | 1 MCU | File edit, git op, single command |
| `standard` | 3 MCU | Feature with tests, multi-step |
| `complex` | 5 MCU | Full-stack + deploy, multi-agent |

### API

```
POST   /v1/tasks              # Submit task
GET    /v1/tasks/{id}         # Task status
GET    /v1/tasks/{id}/stream  # SSE real-time progress
GET    /v1/agents             # List agents
POST   /v1/agents/{name}/run  # Invoke agent
POST   /v1/license/validate   # Validate license key
GET    /health                # Health check
POST   /billing/webhook       # Polar.sh webhook
```

### Python SDK

```python
from src.raas.sdk import MekongClient

client = MekongClient("https://api.agencyos.network", "mk_your_key")
result = client.cook("Deploy a landing page")

for event in client.stream_task(result.task_id):
    print(f"Step {event['step']}: {event['title']}")
```

## Mekong vs. Alternatives

| Feature | Mekong | Aider | Cursor | Copilot |
|---------|--------|-------|--------|---------|
| Plan → Execute → Verify | ✅ | ❌ | ❌ | ❌ |
| Auto-rollback on failure | ✅ | ❌ | ❌ | ❌ |
| 17+ specialized agents | ✅ | ❌ | ❌ | ❌ |
| Any LLM provider | ✅ | ✅ | ❌ | ❌ |
| Built-in billing/RaaS | ✅ | ❌ | ❌ | ❌ |
| Founder OS (idea → IPO) | ✅ | ❌ | ❌ | ❌ |
| Self-hosted | ✅ | ✅ | ❌ | ❌ |

| Complexity | Credits | Example |
|-----------|---------|---------|
| Simple | 1 | Single file edit, git operation |
| Standard | 3 | Multi-step feature implementation |
| Complex | 5 | Full-stack feature with tests |

## CLI Commands

```bash
mekong cook "<goal>"           # Full PEV pipeline
mekong cook "<goal>" --agi-dash # With AGI v2 dashboard
mekong plan "<goal>"           # Plan only (dry run)
mekong run <recipe.md>         # Execute existing recipe
mekong agent <name> <cmd>      # Run agent directly
mekong list                    # List available recipes
mekong search <query>          # Search recipes
mekong version                 # Show version + AGI health
mekong agi status              # AGI score dashboard (0-100)
mekong collab debate "<topic>" # Multi-agent debate
mekong collab review <file>    # Peer code review
mekong memory search "<query>" # Vector semantic search
```

### Flags

| Flag | Description |
|------|------------|
| `--verbose` | Show step-by-step execution details |
| `--dry-run` | Plan only, no execution |
| `--strict` | Fail on first verification error |
| `--no-rollback` | Skip rollback on failure |
| `--agi-dash` | Show 9-subsystem AGI dashboard after cook |

## Architecture

```
mekong-cli/
├── src/
│   ├── core/                      # PEV Engine + AGI v2
│   │   ├── planner.py             # LLM task decomposition (5 step types)
│   │   ├── executor.py            # Multi-mode runner (shell/llm/tool/browse/evolve)
│   │   ├── verifier.py            # Result validation
│   │   ├── orchestrator.py        # PEV coordination + self-healing + auto-recipe
│   │   ├── nlu.py                 # 📡 Intent classification (NLU)
│   │   ├── memory.py              # 💾 Persistent execution memory
│   │   ├── reflection.py          # 🪞 Past failure analysis
│   │   ├── world_model.py         # 🌍 Environment state tracking
│   │   ├── tool_registry.py       # 🔧 Dynamic tool management
│   │   ├── browser_agent.py       # 🌐 Web content extraction
│   │   ├── collaboration.py       # 🤝 Multi-agent coordination
│   │   ├── code_evolution.py      # 🧬 Code quality evolution
│   │   ├── vector_memory_store.py # 🧠 Semantic vector search
│   │   ├── agi_score.py           # 🏆 Real-time score engine (0-100)
│   │   ├── event_bus.py           # ⚡ Reactive event system (22 events)
│   │   ├── telemetry.py           # 📊 Tiered telemetry (T0/T1/T2)
│   │   ├── smart_router.py        # Intent → recipe/tool/evolve router
│   │   ├── llm_client.py          # OpenAI-compatible client
│   │   └── gateway.py             # FastAPI server + WebSocket
│   ├── agents/                    # Pluggable agent system
│   └── raas/                      # Credit billing (RaaS)
├── tests/                         # Test suite (197+ tests)
├── recipes/                       # Built-in + auto-generated recipes
│   └── auto/                      # Auto-saved from successful runs
└── docs/                          # Documentation
```

## AGI v2 — 9-Subsystem Intelligence

Mekong CLI integrates **9 AGI subsystems** into the core pipeline, scored in real-time via `mekong agi status`:

```
╭── 🧠 AGI v2 Score Dashboard ──╮
│ Grade: S    Score: 97.6/100    │
│ ███████████████████░           │
│                                │
│ Modules: 45/45  Wiring: 25/25 │
│ Runtime: 13/15  Improve: 15/15│
╰────────────────────────────────╯
```

### 17 Pipeline Touchpoints

```
PRE-EXEC (5):   World → Reflection → Tools → VecMem → Collab
PLAN (3):       NLU classify → Decompose (5 types) → SmartRouter
EXEC (3):       Execute → Self-heal (reflection+LLM) → Verify
POST-EXEC (6):  Reflect → WorldDiff → CodeEvo → VecMem → Collab → AutoRecipe+Telemetry
```

### Key AGI Features

| Feature | Description |
|---------|-------------|
| **Self-Healing** | Failed steps → reflection hint → LLM retry → auto-correct |
| **Auto-Recipes** | Successful runs auto-save to `recipes/auto/` for future reuse |
| **Score Engine** | 4-dimension scoring: modules (45) + wiring (25) + runtime (15) + improve (15) |
| **EventBus** | 22 event types for reactive module communication |
| **Tiered Telemetry** | T0 (full trace) → T1 (daily summary) → T2 (monthly archive) |

## API Server

```bash
# Start the gateway
uvicorn src.core.gateway:app --host 0.0.0.0 --port 8000
```

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/cmd` | POST | Execute PEV pipeline |
| `/missions` | POST | Create mission (credits deducted) |
| `/missions` | GET | List missions |
| `/missions/{id}` | GET | Get mission status |
| `/missions/{id}/cancel` | POST | Cancel + refund credits |
| `/billing/webhook` | POST | Polar.sh webhook receiver |
| `/dashboard/summary` | GET | Tenant dashboard data |

## RaaS Integration

Mekong CLI is the open-source engine behind **Agency OS** — a managed platform where non-technical users submit tasks in natural language and pay per execution via credits.

### How it works

```
Non-tech User → "Build me a landing page"
    ↓
Agency OS Dashboard (commercial)
    ↓
Mekong CLI API → Plan → Execute → Verify
    ↓
Credits deducted → Result delivered
```

### Build your own RaaS

```python
# 1. Create a tenant
from src.raas.tenant import TenantStore
store = TenantStore()
tenant = store.create_tenant("Acme Corp")
print(f"API Key: {tenant.api_key}")  # mk_... (shown once)

# 2. Add credits
from src.raas.credits import CreditStore
credits = CreditStore()
credits.add(tenant.id, 100, "initial_grant")

# 3. Submit missions via API
# POST /missions with Bearer token
# Body: {"goal": "Create a REST API for users"}
```

## Configuration

Copy `.env.example` and set:

```bash
# LLM Provider (any OpenAI-compatible API)
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-...

# Billing (optional, for RaaS)
POLAR_WEBHOOK_SECRET=whsec_...

# Database (default: ~/.mekong/raas/tenants.db)
RAAS_DB_PATH=~/.mekong/raas/tenants.db
```

## Development

```bash
# Python core
pip install -e ".[dev]"
python3 -m pytest              # 62 tests (~2.5 min)

# Node.js monorepo
pnpm install && pnpm run build
```

## Roadmap

**v3.1.0 (current)** — 55 commands, Founder OS complete, AGI Score 97.6/100

- [x] PEV Engine (Plan-Execute-Verify)
- [x] Agent System (Git, File, Shell)
- [x] Credit Billing (SQLite, Polar.sh)
- [x] Multi-tenant isolation
- [x] Python SDK
- [x] AGI v2: 9 subsystems (NLU, Memory, Reflection, WorldModel, Tools, Browser, Collab, Evo, VecMem)
- [x] Self-healing pipeline with reflection-guided retries
- [x] Auto-recipe generation from successful runs
- [x] AGI Score Engine (0-100) with agi status dashboard
- [x] EventBus reactive module communication (22 events)
- [x] Tiered telemetry (T0/T1/T2)

- [ ] v4.0: Web dashboard + Recipe marketplace
- [ ] Plugin system (custom agents)
- [ ] npm/PyPI public packages
- [ ] Multi-tenant team mode

## Contributing

Contributors share in revenue generated by AgencyOS usage of their code.

- **Agent submissions** → 10% of credits used
- **Recipe contributions** → 5% of credits used
- **Bug bounties** → $50–$500

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

---

[MIT License](LICENSE) · Built by [Binh Phap Venture Studio](https://binhphap.io) · [GitHub](https://github.com/longtho638-jpg/mekong-cli)
