# How Mekong CLI Runs Your Business with 261 AI Workflows
**Blog post draft — v5.0 launch | Target: dev.to, Hashnode, Medium**

---

## Introduction

What if your terminal could run your company?

Not just generate code. Not just answer questions. Actually run your business — sales outreach, financial forecasts, sprint planning, investor pitch decks — all from a single CLI, powered by any LLM you choose.

That's Mekong CLI v5.0. We call it OpenClaw.

---

## The Problem with AI Tools Today

Most AI tools fall into one of two traps:

**Trap 1: Too narrow.** GitHub Copilot writes code. ChatGPT answers questions. Cursor autocompletes. Each tool lives in its own silo, solving one slice of one problem.

**Trap 2: Too expensive.** Enterprise AI platforms charge $500+/month per seat, lock you into a single LLM provider, and still require you to stitch everything together manually.

Founders, agencies, and dev teams need something different. They need a platform that spans the entire business — from investor pitch to production deploy — without vendor lock-in and without a $10,000 monthly AI bill.

---

## What Mekong CLI Does Differently

### 1. Five Business Layers, One CLI

Mekong CLI organizes 273 commands across five layers that mirror how a real company operates:

**Founder Layer** — Annual planning, OKRs, SWOT analysis, fundraising, VC cap tables, IPO preparation. Run `mekong okr` and get a structured OKR framework for your quarter in under 60 seconds.

**Business Layer** — Sales pipelines, marketing campaigns, financial modeling, HR workflows, pricing strategy. `mekong sales` kicks off a lead generation workflow using your LeadHunter agent.

**Product Layer** — Sprint planning, roadmaps, brainstorming, scope definition. `mekong sprint` decomposes your backlog into a two-week execution plan with clear acceptance criteria.

**Engineering Layer** — The familiar territory: cook, fix, code, test, deploy, review. `mekong cook "add OAuth to the API"` runs a full Plan-Execute-Verify cycle with automatic rollback on failure.

**Ops Layer** — Audit, health, security, status, cleanup. `mekong health` runs 36 checks across your entire stack in 4.2 seconds using parallel DAG execution.

### 2. Universal LLM — Three Environment Variables

```bash
export LLM_BASE_URL=https://openrouter.ai/api/v1
export LLM_API_KEY=your-key
export LLM_MODEL=anthropic/claude-sonnet-4
```

That's it. Switch to DeepSeek for $0.27/100K tokens. Use Qwen for an unlimited coding plan at ~$10/month. Run Llama3 locally via Ollama at zero cost. If your primary provider goes down, Mekong automatically falls back through a chain of seven providers without dropping your task.

### 3. Plan-Execute-Verify Engine

Every command runs through the PEV engine:

- **Plan**: The LLM decomposes your goal into discrete, reversible steps
- **Execute**: Steps run via shell, file system, or LLM API calls
- **Verify**: Each step validates its output before proceeding

If a step fails, the orchestrator rolls back completed steps in reverse order. No half-finished deployments. No corrupted state.

### 4. $0/Month Infrastructure

The entire platform runs on Cloudflare's free tier:
- Frontend: Cloudflare Pages
- Edge API: Cloudflare Workers
- Database: Cloudflare D1 (SQLite at the edge)
- Cache: Cloudflare KV
- Storage: Cloudflare R2

For an agency running 10 client projects, this is the difference between $0 and $2,000/month in infrastructure.

### 5. MCU Billing — Pay for Results

Mission Credit Units (MCU) are consumed only after successful task delivery. A simple task costs 1 MCU. A complex multi-step deployment costs 5 MCU. If the task fails, you pay nothing.

Tiers start at $49/month for 50 credits — enough for a solo founder running daily operations. Agencies on the Premium tier get 1,000 credits for $499, with Polar.sh handling all payments via webhook.

---

## Real Workflows in Action

### Morning Standup in 30 Seconds

```bash
mekong daily
# → pulls tasks from .mekong/tasks/
# → checks CI status
# → summarizes overnight agent activity
# → prints prioritized todo for today
```

### Investor Pitch in 5 Minutes

```bash
mekong pitch --deck --market-size SaaS --stage seed
# → generates executive summary
# → builds TAM/SAM/SOM analysis
# → creates problem/solution/traction narrative
# → outputs pitch.md ready for Keynote/Slides
```

### Full Deploy Pipeline

```bash
mekong deploy --env production
# → lint + typecheck
# → 3638 tests
# → staging deploy + smoke test
# → production deploy + smoke test
# → health check
# → done in 4.4 minutes
```

---

## The Binh Pháp Quality System

Mekong CLI enforces six quality fronts inspired by Sun Tzu's Art of War:

1. **始計 Tech Debt** — Zero TODO/FIXME in core. Zero console.log in production.
2. **作戰 Type Safety** — Type hints on every public function. mypy strict mode.
3. **謀攻 Performance** — CLI starts in 1.2s. Commands route in 18ms.
4. **軍形 Security** — JWT RS256, tenant isolation, command sanitization.
5. **兵勢 UX** — Rich terminal output, streaming LLM responses.
6. **虛實 Documentation** — 542 skills documented. Self-documenting codebase.

---

## Getting Started

```bash
# Install
pip install mekong-cli

# Configure LLM (use any OpenAI-compatible provider)
export LLM_BASE_URL=https://openrouter.ai/api/v1
export LLM_API_KEY=your-key
export LLM_MODEL=anthropic/claude-sonnet-4

# Verify
mekong health

# Run your first command
mekong cook "build a REST API with FastAPI"
```

GitHub: github.com/mekong-cli/mekong-cli
Docs: docs.mekong-cli.dev
Pricing: mekong-cli.dev/pricing

---

## Conclusion

Mekong CLI v5.0 is the first AI platform that treats your entire business as a deployable system. Five layers. 273 commands. 542 skills. 14 agents. Any LLM. $0 infrastructure.

The terminal is the new C-suite.

*OpenClaw. I run this company.*
