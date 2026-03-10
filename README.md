<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://img.shields.io/badge/🐉_MEKONG_CLI-0d1117?style=for-the-badge&labelColor=0d1117&color=0d1117">
    <img alt="Mekong CLI" src="https://img.shields.io/badge/🐉_MEKONG_CLI-ffffff?style=for-the-badge&labelColor=ffffff&color=ffffff">
  </picture>
</p>

<h1 align="center">
  Mekong CLI
</h1>

<p align="center">
  <strong>AGI Vibe Coding Factory — Plan, Execute & Verify autonomous engine.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/AGI_Score-benchmarked-green?style=flat-square" alt="AGI Score" />
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-22c55e?style=flat-square" alt="MIT" /></a>
  <a href="https://github.com/longtho638-jpg/mekong-cli/actions"><img src="https://img.shields.io/github/actions/workflow/status/longtho638-jpg/mekong-cli/ci.yml?style=flat-square&label=CI" alt="CI" /></a>
  <img src="https://img.shields.io/badge/Python-3.9+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/LLM-Any_Provider-8B5CF6?style=flat-square" alt="LLM" />
  <img src="https://img.shields.io/badge/v3.0.0-blue?style=flat-square" alt="Version" />
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> •
  <a href="#how-it-works">How It Works</a> •
  <a href="#agents">Agents</a> •
  <a href="#raas">RaaS</a> •
  <a href="CONTRIBUTING.md">Contribute</a>
</p>

---

## Why Mekong?

Most AI tools generate code and hope it works. Mekong **plans**, **executes**, and **verifies** — then rolls back if anything breaks.

```
You: "Create a FastAPI service with JWT auth and tests"

Mekong:
  📋 PLAN     → LLM decomposes into 5 steps with dependency graph
  ⚡ EXECUTE  → Runs each step (shell, code gen, API calls)
  ✅ VERIFY   → Tests pass? Types clean? Builds green?
  🏁 DONE     → All verified. Ship it.

  ❌ FAILED?  → Auto-rollback → Retry with corrected approach.
```

**Zero babysitting. Zero hallucination tolerance.**

## Quick Start

```bash
# 1. Install
git clone https://github.com/longtho638-jpg/mekong-cli.git
cd mekong-cli && pip install -e ".[dev]"

# 2. Configure any OpenAI-compatible LLM
export LLM_BASE_URL="https://api.openai.com/v1"
export LLM_API_KEY="sk-..."

# 3. Go
mekong cook "Create a Python calculator with tests"
```

### Works with every LLM

| Provider | Base URL | Cost |
|----------|----------|------|
| **OpenAI** | `https://api.openai.com/v1` | Pay-per-use |
| **Google Gemini** | `https://generativelanguage.googleapis.com/v1beta/openai` | Free tier |
| **DashScope (Qwen)** | `https://dashscope.aliyuncs.com/compatible-mode/v1` | [Free credits →](https://www.alibabacloud.com/campaign/benefits?referral_code=A9245T) |
| **Ollama (Local)** | `http://localhost:11434/v1` | Free |
| **Any proxy** | Your OpenAI-compatible endpoint | Custom |

## How It Works

### Plan → Execute → Verify (PEV)

```
┌──────────────────────────────────────────────┐
│              🎯 Your Goal                     │
└──────────────┬───────────────────────────────┘
               │
    ┌──────────▼──────────┐
    │  📋 PLAN             │  LLM decomposes goal into
    │  RecipePlanner       │  ordered steps + dependencies
    └──────────┬──────────┘
               │
    ┌──────────▼──────────┐
    │  ⚡ EXECUTE          │  Runs shell, code gen, API
    │  RecipeExecutor      │  calls — parallel where safe
    └──────────┬──────────┘
               │
    ┌──────────▼──────────┐
    │  ✅ VERIFY           │  Exit codes, tests, types,
    │  RecipeVerifier      │  file checks, LLM assessment
    └──────────┬──────────┘
               │
       ┌───────┴───────┐
       │               │
    ✅ Pass         ❌ Fail
       │               │
    🏁 Done        ⏪ Rollback → Retry
```

| Phase | Module | What It Does |
|-------|--------|-------------|
| **Plan** | `src/core/planner.py` | LLM decomposes goal into steps with dependency graph |
| **Execute** | `src/core/executor.py` | Runs shell/code/API tasks, parallel where possible |
| **Verify** | `src/core/verifier.py` | Validates results against success criteria |
| **Orchestrate** | `src/core/orchestrator.py` | Coordinates PEV loop, rollback, self-healing |

## Agents

All agents follow the same `plan() → execute() → verify()` pattern:

```bash
mekong agent git status              # Git operations
mekong agent git commit "feat: ..."  # Smart commits
mekong agent file find "*.py"        # File search & analysis
mekong agent file tree src/          # Directory tree
mekong agent shell "npm test"        # Safe shell execution
mekong agent lead hunt               # Lead generation
mekong agent content write           # SEO content
mekong agent crawler scan            # Recipe discovery
```

[Build your own agent →](CONTRIBUTING.md)

## CLI

```bash
mekong cook  "Build a REST API"      # Full PEV pipeline
mekong plan  "Add OAuth support"     # Plan only (dry run)
mekong run   recipe.md               # Execute recipe file
mekong agent <name> <command>        # Run agent directly
mekong gateway --port 8000           # Start API server
mekong list                          # List available recipes
mekong search "deploy"               # Search recipes
```

| Flag | Effect |
|------|--------|
| `--verbose / -v` | Step-by-step execution details |
| `--dry-run / -n` | Plan only, no execution |
| `--strict` | Fail on first verification error |
| `--json / -j` | Machine-readable JSON output |

## API

Start the gateway: `mekong gateway --port 8000`

```
POST   /v1/tasks              # Submit task (credits deducted)
GET    /v1/tasks/{id}         # Task status
GET    /v1/tasks/{id}/stream  # SSE real-time progress
GET    /v1/agents             # List agents
POST   /v1/agents/{name}/run  # Invoke agent
POST   /v1/license/validate   # Validate license key
GET    /health                # Health check
POST   /billing/webhook       # Polar.sh webhook
```

```bash
curl -X POST http://localhost:8000/v1/tasks \
  -H "Authorization: Bearer mk_your_key" \
  -H "Content-Type: application/json" \
  -d '{"goal": "Create a todo app with tests", "strict": false}'
```

## RaaS

**Revenue as a Service** — Open Core model with built-in credit billing.

| Tier | Credits | Agents |
|------|---------|--------|
| **Free** | 10/month | Core agents |
| **Pro** | 200/month | All agents |
| **Enterprise** | Custom | Custom + API |

| Complexity | Credits | Example |
|-----------|---------|---------|
| Simple | 1 | File edit, git op |
| Standard | 3 | Feature with tests |
| Complex | 5 | Full-stack + deploy |

```python
from src.raas.sdk import MekongClient

client = MekongClient("https://api.mekong.io", "mk_your_key")
result = client.cook("Deploy a landing page")

for event in client.stream_task(result.task_id):
    print(f"Step {event['step']}: {event['title']}")
```

### Premium Agents (License Required)

| Agent | Description |
|-------|-------------|
| `auto-cto-pilot` | Autonomous daily task generation |
| `opus-strategy` | Strategic planning with top-tier LLM |
| `opus-parallel` | Multi-agent parallel orchestration |
| `opus-review` | Security + quality code review |

## Architecture

```
mekong-cli/
├── src/                    # Core engine (Python)
│   ├── core/               # PEV pipeline (planner, executor, verifier, orchestrator)
│   ├── agents/             # Pluggable agent system (git, file, shell, lead, content)
│   ├── raas/               # Credit billing + SDK
│   ├── commands/           # CLI subcommands (monitor, etc.)
│   └── db/                 # Database layer (asyncpg)
├── apps/                   # Monorepo services
│   ├── openclaw-worker/    # Autonomous CTO daemon (Node.js)
│   ├── raas-gateway/       # Cloudflare Worker API
│   ├── algo-trader/        # Trading engine (TypeScript)
│   ├── well/               # Well platform
│   └── ...                 # Other apps
├── packages/               # Shared libraries (vibe-*, core, trading-core)
├── frontend/               # Landing pages
├── tests/                  # Python test suite (62 tests)
├── recipes/                # Built-in task templates
└── docs/                   # Documentation
```

## Development

```bash
# Python core
pip install -e ".[dev]"
python3 -m pytest              # Run 62 tests (~2.5min)

# Node.js monorepo (apps & packages)
pnpm install
pnpm run build                 # Build all workspaces
pnpm run test                  # Test all workspaces
pnpm run lint                  # Lint all workspaces
```

## Mekong vs. Alternatives

| Feature | Mekong | Aider | Cursor | Copilot |
|---------|--------|-------|--------|---------|
| Plan → Execute → Verify | ✅ | ❌ | ❌ | ❌ |
| Auto-rollback on failure | ✅ | ❌ | ❌ | ❌ |
| Multiple agents | ✅ 17+ | ❌ | ❌ | ❌ |
| Any LLM provider | ✅ | ✅ | ❌ | ❌ |
| Built-in billing/RaaS | ✅ | ❌ | ❌ | ❌ |
| REST API + WebSocket | ✅ | ⚠️ | ❌ | ⚠️ |
| Self-hosted | ✅ | ✅ | ❌ | ❌ |

## Contributing

Contributors **share in revenue** generated by AgencyOS usage of their code.

- **Agent submissions** → 10% of credits used
- **Recipe contributions** → 5% of credits used
- **Bug bounties** → $50–$500

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## Roadmap

- [x] PEV Engine (Plan → Execute → Verify)
- [x] Agent System (Git, File, Shell, Database, Lead, Content)
- [x] Credit Billing (SQLite + Polar.sh)
- [x] Multi-provider LLM support
- [x] Python SDK (sync + async)
- [x] FastAPI Gateway + WebSocket streaming
- [ ] Web dashboard
- [ ] Recipe marketplace
- [ ] npm/PyPI packages
- [ ] Plugin system

## Founder OS — Goldman Sachs Playbook as Code

Complete founder lifecycle from Idea to Post-IPO, encoded as 24 executable commands across 11 stages.

### Why This is a Moat

1. **Information Asymmetry** — Institutional knowledge (term sheets, cap tables, S-1 filings) packaged as code. First-time founders get Goldman-grade analysis.
2. **Operating System, Not Tools** — Not a calculator or template. A complete decision engine that connects bootstrapping → fundraising → IPO → public company.
3. **Compounds Over Time** — Each module feeds the next. Cap table feeds term sheet analysis feeds negotiation strategy feeds IPO readiness.

### 11-Stage Lifecycle

```
Idea → Validate → Brand → Pitch → Bootstrap → Raise (VC) → Grow → Secondary → Pre-IPO → IPO → Post-IPO
```

### 24 Commands

| Stage | Command | Description |
|-------|---------|-------------|
| 1. Validate | `/founder:validate` | Market validation, PMF signals, pivot criteria |
| 2. Brand | `/founder:brand` | Brand DNA, positioning, naming, voice |
| 3. Pitch | `/founder:pitch` | Pitch deck, elevator pitch, investor materials |
| 4. Metrics | `/founder:metrics` | KPI dashboard, cohort analysis, benchmarks |
| 5. Hire | `/founder:hire` | Role definition, JD generation, interview scorecards |
| 6. Legal | `/founder:legal` | Entity structure, IP protection, compliance |
| 7. Weekly | `/founder:week` | Weekly review, OKR tracking, team updates |
| 8. Bootstrap | `/founder:vc:bootstrap` | Ramen profitability, alternative funding, raise readiness |
| 9. Term Sheet | `/founder:vc:term-sheet` | Red flag detection, clause analysis, exit simulation |
| 10. Cap Table | `/founder:vc:cap-table` | Dilution modeling, SAFE conversion, exit waterfall |
| 11. Negotiate | `/founder:vc:negotiate` | BATNA assessment, counter scripts, walk-away lines |
| 12. VC Map | `/founder:vc-map` | VC database, warm intro finder, outreach intel |
| 13. Grow | `/founder:grow` | Growth strategy, channel optimization |
| 14. Secondary | `/founder:secondary` | Secondary market, tender offers, tax optimization |
| 15. Pre-IPO | `/founder:ipo:pre-ipo-prep` | IPO readiness audit (5 categories, 100 points) |
| 16. S-1 | `/founder:ipo:s1` | S-1 prospectus framework, risk factors, narrative |
| 17. Roadshow | `/founder:ipo:roadshow` | 20-slide deck, Q&A bank, order book analysis |
| 18. IPO Day | `/founder:ipo:ipo-day` | Pricing scenarios, T-minus timeline, bell ceremony |
| 19. Public Co | `/founder:ipo:public-co` | Quarterly earnings, guidance, 10-Q/10-K filing |
| 20. Insider | `/founder:ipo:insider` | Trading windows, 10b5-1 plans, lockup strategy |
| 21. Succession | `/founder:ipo:succession` | CEO transition, buyback modeling, M&A screening |
| 22. Emergency | `/founder:emergency` | Crisis playbook, board communication |
| 23. Scale | `/founder:scale` | Scaling operations, team growth |
| 24. Budget | `/founder:budget` | Financial planning, runway management |

### Architecture

```
src/core/
├── founder_vc/           # VC Layer (Stage 8-12)
│   ├── founder_vc_bootstrap.py
│   ├── founder_vc_term_sheet.py
│   ├── founder_vc_cap_table.py
│   ├── founder_vc_negotiate.py
│   └── founder_vc_map.py
├── founder_ipo/          # IPO Layer (Stage 15-21)
│   ├── founder_pre_ipo.py
│   ├── founder_s1.py
│   ├── founder_roadshow.py
│   ├── founder_ipo_day.py
│   ├── founder_public_co.py
│   ├── founder_insider.py
│   └── founder_succession.py
├── founder_secondary.py  # Growth Layer (Stage 14)
├── founder_validate.py   # Stage 1
├── founder_brand.py      # Stage 2
├── founder_pitch.py      # Stage 3
├── founder_metrics.py    # Stage 4
├── founder_hire.py       # Stage 5
├── founder_legal.py      # Stage 6
├── founder_week.py       # Stage 7
└── founder_grow.py       # Stage 13
```

## License

[MIT](LICENSE) — Use it, fork it, build on it.

---

<p align="center">
  <sub>Built with 🐉 by <a href="https://binhphap.io">Binh Phap Venture Studio</a></sub><br/>
  <sub><em>"Speed is the essence of war." — Sun Tzu</em></sub>
</p>
