# Mekong CLI

[![CI](https://github.com/longtho638-jpg/mekong-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/longtho638-jpg/mekong-cli/actions/workflows/ci.yml)
[![npm openclaw-engine](https://img.shields.io/npm/v/@mekongcli/openclaw-engine?label=openclaw-engine)](https://www.npmjs.com/package/@mekongcli/openclaw-engine)
[![npm cli-core](https://img.shields.io/npm/v/@mekongcli/cli-core?label=cli-core)](https://www.npmjs.com/package/@mekongcli/cli-core)
[![Tests](https://img.shields.io/badge/tests-1263%20passing-brightgreen)]()
[![License: BSL 1.1](https://img.shields.io/badge/License-BSL%201.1-blue.svg)](LICENSE)

**Describe your goal. AI plans, executes, verifies, delivers.**

Mekong CLI is an AI-operated business platform. One natural-language command triggers multi-agent workflows that build software, run marketing campaigns, manage finances, and ship products. Works with any LLM provider -- cloud or local.

```
$ mekong cook "Create a SaaS landing page with Stripe checkout"

  Planning...  3 phases identified
  Phase 1/3:   Scaffold Next.js + Tailwind (12 files)
  Phase 2/3:   Wire Stripe checkout + webhook handler
  Phase 3/3:   Deploy to Cloudflare Pages
  Verify:      Build OK, tests pass, live at https://...

  Done. 3 MCU credits used.
```

## Install

### SDK (npm)

```bash
npm install @mekongcli/openclaw-engine    # Mission orchestration SDK
npm install @mekongcli/cli-core           # Full CLI with 300+ commands
```

### Full Platform

```bash
git clone https://github.com/longtho638-jpg/mekong-cli.git
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

Commands compose into **DAG workflows** -- parallel where possible, sequential where required:

```bash
$ mekong founder:raise "Series A for AI platform"
  Group 1 (parallel): /unit-economics + /tam + /moat-audit
  Group 2 (parallel): /financial-model + /data-room
  Group 3 (sequential): /cap-table -> /pitch -> /vc-map
  Output: reports/raise-ready-kit/
```

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
| Tests | 1,263 passing |
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
