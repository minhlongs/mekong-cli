# Mekong CLI v5.0 — Launch Newsletter
**Subject:** v5.0 shipped: 273 commands, $0 infra, your terminal runs your company
**List:** Early access subscribers + waitlist
**Send date:** 2026-03-12

---

## Preview text
OpenClaw is live. 273 AI workflows. Any LLM. $0/month infrastructure. Read time: 3min.

---

## Header

```
MEKONG CLI v5.0 — OPENCLAW
━━━━━━━━━━━━━━━━━━━━━━━━━━
The terminal that runs your company.
```

---

## Opening

Hi,

We shipped v5.0 this week.

If you've been on the waitlist since v4.x, here's what changed: everything.

v5.0 isn't an incremental update. It's a complete rethinking of what a developer CLI should cover — not just code, but the entire business that code is part of.

Here's what's new.

---

## What Shipped

### 273 Commands Across 5 Business Layers

We organized every workflow into five layers that mirror how a real company operates:

**👑 Founder** — OKRs, annual planning, SWOT, fundraising, VC cap tables, IPO prep
**🏢 Business** — Sales pipelines, marketing campaigns, finance models, HR, pricing
**📦 Product** — Sprint planning, roadmaps, brainstorming, scope definition
**⚙️ Engineering** — Cook, fix, code, test, deploy, review (the familiar layer)
**🔧 Ops** — Audit, health, security, status, cleanup

Run `mekong help` to see all 273. Most take under 60 seconds from invocation to output.

---

### The PEV Engine — Plan, Execute, Verify

Every command runs through three phases:

1. **Plan** — LLM decomposes your goal into discrete, reversible steps with a DAG
2. **Execute** — Steps run via shell, file system, or LLM API
3. **Verify** — Each step validates output before proceeding to the next

If anything fails, the orchestrator rolls back completed steps in reverse order. You never end up in a half-deployed, broken state.

For multi-command operations, the DAG scheduler runs steps in parallel where possible. A 6-command ops sweep that would take 41 seconds sequentially finishes in 8.3 seconds.

---

### Universal LLM — 3 Environment Variables

```bash
export LLM_BASE_URL=https://openrouter.ai/api/v1
export LLM_API_KEY=your-key
export LLM_MODEL=anthropic/claude-sonnet-4
```

That's the entire LLM configuration. Switch to any OpenAI-compatible provider by changing one variable. We support and test against:

- OpenRouter (300+ models, $5 free signup)
- DeepSeek ($0.27/100K tokens — cheapest serious option)
- Qwen Coder (~$10/month unlimited coding plan)
- Ollama (local, $0)
- OpenAI, Anthropic, Google (direct)

If your primary provider goes down, Mekong falls back through a 7-provider chain automatically. Tasks don't fail because of a provider outage.

---

### $0/Month Infrastructure

The entire platform runs on Cloudflare's free tier:

| Layer | Service | Cost |
|-------|---------|------|
| Frontend | CF Pages | $0 |
| Edge API | CF Workers | $0 |
| Database | CF D1 (SQLite) | $0 |
| Cache | CF KV | $0 |
| Storage | CF R2 | $0 |

No AWS. No Vercel. No infrastructure bill. The scaffold script (`mekong/infra/scaffold.sh`) sets up all five layers for any project in under 2 minutes.

---

### MCU Billing — Pay for Results

Mission Credit Units are consumed only after successful task delivery.

| Task type | MCU cost |
|-----------|---------|
| Simple (status, list, check) | 1 MCU |
| Standard (plan, review, deploy) | 3 MCU |
| Complex (full pipeline, multi-agent) | 5 MCU |

Failed tasks cost 0 MCU. The orchestrator rolls back and you keep your credits.

**Pricing:**
- Starter: 50 credits / $49/month (solo founder)
- Growth: 200 credits / $149/month (small team)
- Premium: 1,000 credits / $499/month (agency)

Payment via Polar.sh. Cancel anytime. No contracts.

---

## What's Next (v5.1)

Honest gaps we're fixing:

1. **Test coverage** — currently 26% line coverage across 3,638 tests. Target: 60% by v5.1
2. **SAST scanning** — adding semgrep to CI pipeline
3. **Sentry integration** — error tracking currently missing from monitoring stack
4. **CF WAF rules** — custom WAF rules for raas-gateway hardening

v5.1 target: Q2 2026.

---

## Get Started

```bash
# Install
pip install mekong-cli

# Configure
export LLM_BASE_URL=https://openrouter.ai/api/v1
export LLM_API_KEY=your-key
export LLM_MODEL=anthropic/claude-sonnet-4

# Verify
mekong health

# Run first command
mekong cook "write a Python hello world"
```

Full docs: docs.mekong-cli.dev
GitHub (MIT): github.com/mekong-cli/mekong-cli
Pricing: mekong-cli.dev/pricing

---

## Closing

Thank you for being on the waitlist. v5.0 is the platform we set out to build.

The terminal is the most powerful interface ever built. We're just bringing it up to 2026.

— The OpenClaw team

---

*You're receiving this because you signed up for Mekong CLI early access.*
*Unsubscribe: mekong-cli.dev/unsubscribe*
