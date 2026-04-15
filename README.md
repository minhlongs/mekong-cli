# Mekong IDE — The One-Person Company Platform

> **One person. 22 departments. $49/mo.** Replace a 50-person team with autonomous agents.

[![Website](https://img.shields.io/badge/Website-mekongmind.com-blue)](https://www.mekongmind.com)
[![Subscribe](https://img.shields.io/badge/Subscribe-$49%2Fmo-green)](https://buy.polar.sh/polar_cl_apvIt00Pf7vw2GGX0PW7tWfNjSiwaTRUl0YzO3YqVhA)

## What is Mekong IDE?

The platform that enables the **one-person billion-dollar company**. 22 autonomous departments — engineering, marketing, sales, finance, legal, compliance, HR — all operated by agents. You make the decisions, agents do the work.

**Built for solo founders:**
- 385 pre-built workflow templates across 22 departments
- Runs locally on your Mac with Ollama — zero cloud cost
  - M1/M2/M3/M4: 7B-14B models | M1 Ultra/M2 Ultra: 32B-70B models
- Your data never leaves your machine
- Autonomous operations engine (OpenClaw) runs 24/7 while you sleep
- One subscription = your entire workforce

## Quick Start

```bash
curl -fsSL https://www.mekongmind.com/install.sh | bash
```

## Pricing

| Plan | Price | Credits |
|------|-------|---------|
| [Starter](https://buy.polar.sh/polar_cl_apvIt00Pf7vw2GGX0PW7tWfNjSiwaTRUl0YzO3YqVhA) | $49/mo | 200 |
| [Growth](https://buy.polar.sh/polar_cl_TDhelBvQfsZq3Rayqf9to4tl0UD6D04OBFqXm1zJDVC) | $149/mo | 1,000 |
| [Pro](https://buy.polar.sh/polar_cl_zi7LHdaPk93V0xbNVQZgqum96gWCFDTVzpDNR2kfN3j) | $499/mo | 5,000 |

## Links

- **Website:** [mekongmind.com](https://www.mekongmind.com)
- **IDE:** [ide.mekongmind.com](https://ide.mekongmind.com)
- **Guides:** [mekongmind.com/guides](https://www.mekongmind.com/guides/)
- **API:** [api.cashclaw.cc](https://api.cashclaw.cc/health)


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
