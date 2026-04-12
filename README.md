# Mekong IDE — Business Automation Platform

> 22 operational modules. 290 commands. 1 subscription. Run your entire business with automation workflows.

[![CI](https://github.com/longtho638-jpg/mekong-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/longtho638-jpg/mekong-cli/actions/workflows/ci.yml)
[![npm openclaw-engine](https://img.shields.io/npm/v/@mekongcli/openclaw-engine?label=openclaw-engine)](https://www.npmjs.com/package/@mekongcli/openclaw-engine)
[![npm cli-core](https://img.shields.io/npm/v/@mekongcli/cli-core?label=cli-core)](https://www.npmjs.com/package/@mekongcli/cli-core)
[![Tests](https://img.shields.io/badge/tests-5713%20passing-brightgreen)]()
[![License: BSL 1.1](https://img.shields.io/badge/License-BSL%201.1-blue.svg)](LICENSE)

**Describe your goal. automation plans, executes, verifies, delivers.**

Mekong CLI is an automation-powered business platform. One natural-language command triggers multi-agent workflows that build software, run marketing campaigns, manage finances, and ship products. Works with any LLM provider -- cloud or local.

```
$ mekong cook "Create a SaaS landing page with Polar.sh checkout"

  ◐ Planning...   3 phases identified
  ✓ Phase 1/3:    Scaffold Next.js + Tailwind        (12 files created)
  ✓ Phase 2/3:    Wire Polar.sh checkout + webhook handler
  ✓ Phase 3/3:    Deploy to Cloudflare Pages
  ✓ Verify:       Build OK ─ 14 tests pass ─ live at https://app.example.com

  ✅ Done in 4m 23s.  3 MCU credits used.

$ mekong founder:raise "Series A for automation platform"

  ◐ Dispatching 8 agents in parallel...
  ✓ Group 1:  Unit Economics + TAM + Moat Audit      (3 parallel)
  ✓ Group 2:  Financial Model + Data Room            (2 parallel)
  ✓ Group 3:  Cap Table → Pitch Deck → VC Map        (3 sequential)

  ✅ Raise-ready kit at reports/raise-ready-kit/

$ mekong status

  OpenClaw ─ 348 commands ─ 5 layers ─ CI: GREEN
  LLM:     anthropic/claude-sonnet-4  via OpenRouter
  Credits: 847 / 1000 MCU remaining
```

## Get Started

### Quick Start

**Option 1 — Self-hosted (open source)**

```bash
git clone --depth 1 https://github.com/longtho638-jpg/mekong-cli.git
source ~/mekong-cli/scripts/shell-init.sh && mekong
```

**Option 2 — Managed API**

Sign up at [mekongmind.pages.dev](https://mekongmind.pages.dev) to get an API key, then onboard:

```bash
curl -X POST https://api.cashclaw.cc/v1/onboard \
  -H 'Content-Type: application/json' \
  -d '{"name":"Your Name","email":"you@example.com"}'
```

**Option 3 — Free tier**

50 credits/month. No credit card required. Start at [mekongmind.pages.dev](https://mekongmind.pages.dev).

### Pricing

| Tier | Price | Credits/mo | Access |
|------|-------|-----------|--------|
| Starter | $49/mo | 200 | All 22 departments |
| Growth | $149/mo | 1,000 | + priority + webhooks |
| Pro | $499/mo | 5,000 | + support + custom agents |

### Links

- Landing: [mekongmind.pages.dev](https://mekongmind.pages.dev)
- API: [api.cashclaw.cc](https://api.cashclaw.cc)
- Subscribe: [Starter $49/mo](https://buy.polar.sh/a09a5fa0-63db-42a4-a547-3b1523ffc263) · [Growth $149/mo](https://buy.polar.sh/c06a03a3-25cd-4cd3-a13d-e795ee592a4e) · [Pro $499/mo](https://buy.polar.sh/52b7404c-b420-48cc-a382-ab4b5979f766)

---

## Install

### SDK (npm)

```bash
npm install @mekongcli/openclaw-engine    # Mission orchestration SDK
npm install @mekongcli/cli-core           # Full CLI with 300+ commands
```

### Full Platform

```bash
git clone --depth 1 https://github.com/longtho638-jpg/mekong-cli.git
cd mekong-cli && source scripts/shell-init.sh

# Set any OpenAI-compatible LLM (3 env vars)
export LLM_BASE_URL=https://openrouter.ai/api/v1
export LLM_API_KEY=sk-or-v1-yourkey
export LLM_MODEL=anthropic/claude-sonnet-4

mekong cook "Create a REST API with auth"
```

### Free with Local LLM

```bash
ollama pull qwen2.5-coder
export LLM_BASE_URL=http://localhost:11434/v1
mekong cook "Build a Python CLI calculator"
```

### Dashboard (IDE)

```bash
cd apps/dashboard
cp .env.local.example .env.local
# Edit .env.local — only SUPABASE vars are required
npm run dev
# Open http://localhost:3000
```

The dashboard runs without payment env vars — Polar and Stripe
features degrade gracefully when not configured.

## How It Works

**Plan-Execute-Verify (PEV)** -- the core loop:

1. **Plan** -- LLM decomposes your goal into concrete steps
2. **Execute** -- Agents run each step (code, shell, API calls)
3. **Verify** -- Quality gates check output; self-heals on failure

```
CLI Input: "Create a REST API with auth and deploy"
    |
    v
PEV Engine -----> Planner: 4 steps identified
    |               |
    |          +----+----+----+
    |          v    v    v    v
    |       Schema  Routes  Auth  Tests
    |          |    |    |    |
    v          +----+----+----+
Verifier: build OK, 12 tests pass, deployed
```

Commands compose into **DAG workflows** -- parallel where possible, sequential where required. The `founder:raise` demo above shows 8 agents dispatched across 3 dependency groups, finishing in one command.

## 5 Business Layers, 300+ Commands

| Layer | Examples | Purpose |
|-------|----------|---------|
| **Founder** | `/annual` `/okr` `/fundraise` `/swot` | Strategy and governance |
| **Business** | `/sales` `/marketing` `/finance` `/hr` | Revenue and operations |
| **Product** | `/plan` `/sprint` `/roadmap` `/brainstorm` | Product management |
| **Engineering** | `/cook` `/code` `/test` `/deploy` `/review` | Build and ship |
| **Ops** | `/audit` `/health` `/security` `/status` | Monitor and maintain |

Every command has a typed JSON contract (388 total) specifying input schema, output schema, agent assignments, and cascade triggers.

## Architecture

```
mekong cook "your goal"
    |
    v
+-------------------+
|  Mekong Wrapper    |  shell-init.sh: aliases for every provider
+-------------------+
    |
    v
+-------------------+
|  CC CLI Engine     |  claude / gemini / qwen / ollama
+-------------------+
    |
    v
+-------------------+
|  PEV Orchestrator  |  src/core/orchestrator.py
|  Plan -> Execute   |  planner.py -> executor.py
|  -> Verify         |  verifier.py (quality gates)
+-------------------+
    |
    v
+-------------------+
|  Agent Layer       |  GitAgent, FileAgent, ShellAgent
|  248 Skills        |  .claude/skills/
|  206 Commands      |  .claude/commands/
+-------------------+
    |
    v
+-------------------+
|  LLM Router        |  3 env vars -> any provider
|  OpenRouter        |  Anthropic, OpenAI, DeepSeek,
|  Ollama, MLX       |  DashScope, or any compatible API
+-------------------+
```

## LLM Provider Support

Mekong works with **any OpenAI-compatible API**. Three environment variables, zero vendor lock-in:

```bash
export LLM_BASE_URL=...   # API endpoint
export LLM_API_KEY=...    # Your key
export LLM_MODEL=...      # Model name
```

| Provider | Example |
|----------|---------|
| OpenRouter | `https://openrouter.ai/api/v1` + any model |
| Anthropic | `https://api.anthropic.com/v1` + `claude-sonnet-4` |
| OpenAI | `https://api.openai.com/v1` + `gpt-4o` |
| DeepSeek | `https://api.deepseek.com/v1` + `deepseek-chat` |
| Ollama (local) | `http://localhost:11434/v1` + `qwen2.5-coder` |
| MLX (Apple Silicon) | `http://localhost:8080/v1` + local model |

**Fallback chain:** OpenRouter -> DashScope -> DeepSeek -> Anthropic -> OpenAI -> Google -> Ollama -> Offline

## OpenClaw Engine (SDK)

The orchestration core is published as a standalone TypeScript SDK:

```typescript
import { OpenClawEngine } from '@mekongcli/openclaw-engine';

const engine = new OpenClawEngine();

// Classify task complexity
const complexity = engine.classifyComplexity("Deploy a microservice");
// => "standard" | "complex" | "critical"

// Submit a mission
const result = await engine.submitMission({
  goal: "Create user authentication",
  layer: "engineering",
  commands: ["code", "test", "deploy"],
});
```

## Infrastructure ($0)

Deploys on Cloudflare free tier:

| Layer | Service | Cost |
|-------|---------|------|
| Frontend | Cloudflare Pages | $0 |
| API | Cloudflare Workers | $0 |
| Database | Cloudflare D1 | $0 |
| Storage | Cloudflare R2 | $0 |
| KV Cache | Cloudflare KV | $0 |

```bash
bash mekong/infra/scaffold.sh myproject startup   # Frontend + API
bash mekong/infra/scaffold.sh myproject scale      # All layers
```

## Project Stats

| Metric | Count |
|--------|-------|
| Commands | 300+ across 5 layers |
| Machine Contracts | 388 (typed JSON I/O) |
| Skills | 248 |
| Tests | 5,713 passing (1,263 TS + 4,450 Python) |
| npm Packages | 2 published |

## Contributing

```bash
# Setup
git clone https://github.com/longtho638-jpg/mekong-cli.git
cd mekong-cli && pnpm install

# Run tests
cd packages/mekong-cli-core && pnpm test     # 1,263 tests
cd packages/openclaw-engine && pnpm test      # Engine tests

# Lint
pnpm --filter @mekongcli/cli-core lint
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

[BSL 1.1](LICENSE) -- source-available, converts to MIT on 2028-03-13.

SDK packages (`@mekongcli/openclaw-engine`, `@mekongcli/cli-core`) are MIT licensed.
