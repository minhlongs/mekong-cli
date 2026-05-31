# Mekong IDE — The One-Person Company Platform

> **One person. 10 business layers. $49/mo.** Replace a 50-person team with autonomous agents.

[![Website](https://img.shields.io/badge/Website-mekongmind.com-blue)](https://www.mekongmind.com)
[![Subscribe](https://img.shields.io/badge/Subscribe-$49%2Fmo-green)](https://buy.polar.sh/polar_cl_apvIt00Pf7vw2GGX0PW7tWfNjSiwaTRUl0YzO3YqVhA)

## What is Mekong IDE?

The platform that enables the **one-person billion-dollar company**. 10 business layers — Founder, Business, Product, Engineering, Ops, Studio, CTO, PM, Dev, Worker — all operated by agents. You make the decisions, agents do the work.

**Built for solo founders (status as of latest commit):**
- ~490 command definitions across 10 business layers (markdown specs;
  ~43 are wired through to executable Python in `src/commands/`).
- Runs locally on your Mac with Ollama — zero cloud cost (smoke-tested
  with Qwen 2.5-coder; performance benchmarks not yet published).
- Your data never leaves your machine when running locally.
- Autonomous operations engine (OpenClaw) — **scaffolded**; orchestration
  daemon and runbook are on the roadmap, not shipped (see
  [`GO_LIVE_PLAYBOOK.md`](./GO_LIVE_PLAYBOOK.md)).
- One subscription = your entire workforce.

**What's actually live today:**

| | Status | Notes |
| --- | --- | --- |
| `api.cashclaw.cc` (gateway) | ✅ live | CF Tunnel → M1 Max:8000 |
| `www.mekongmind.com` (landing) | ✅ live | 13 pages |
| Polar.sh checkout (Starter / Growth / Pro) | ✅ wired | URLs return 302 |
| `ide.mekongmind.com` (dashboard) | ⚠️ deploying | see [`GO_LIVE_PLAYBOOK.md`](./GO_LIVE_PLAYBOOK.md) |
| OpenClaw daemon orchestration | ❌ not yet | scaffolded only |
| First paying customer | ❌ not yet | tracked in [`STRATEGY.md`](./STRATEGY.md) |

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

## Harness Engineering

Mekong is built on **harness engineering** principles: shaping the environment around AI agents for reliability, not just writing better prompts.

> Inspired by [walkinglabs/awesome-harness-engineering](https://github.com/walkinglabs/awesome-harness-engineering)

### The 6 Harness Principles

| Principle | Mekong Implementation |
|-----------|----------------------|
| **Context Engineering** | `HARNESS.md` — context budget rules, layer-specific allowlists, CEO override clauses |
| **Constraints & Guardrails** | `.claude/settings.json` — deny list for destructive actions, ask list for high-risk, SOP hard gates |
| **Specs & Workflow Design** | `sops/` — Standard Operating Procedures as executable specs with acceptance criteria |
| **Evals & Observability** | `observability/` — OpenTelemetry traces, Grafana dashboards, `evals/solo-ceo-eval.md` |
| **Orchestration** | `agents/registry.yaml` — declarative agent definitions, `/cook-auto-parallel` for concurrent execution |
| **Safe Autonomy** | CEO override available at any point, high-risk actions always require approval, all-fail halt |

### Quick Links

- **Harness Config:** [`HARNESS.md`](./HARNESS.md)
- **Architecture:** [`docs/harness-engineering.md`](./docs/harness-engineering.md)
- **SOPs:** [`sops/`](./sops/)
- **Agent Registry:** [`agents/registry.yaml`](./agents/registry.yaml)
- **Eval Suite:** [`evals/solo-ceo-eval.md`](./evals/solo-ceo-eval.md)
- **Observability:** [`observability/`](./observability/)

---

## Links

- **Website:** [mekongmind.com](https://www.mekongmind.com)
- **IDE:** [ide.mekongmind.com](https://ide.mekongmind.com)
- **Guides:** [mekongmind.com/guides](https://www.mekongmind.com/guides/)
- **API:** [api.cashclaw.cc](https://api.cashclaw.cc/health)


## Install

### SDK (npm)

```bash
npm install @mekongcli/openclaw-engine    # Mission orchestration SDK
npm install @mekongcli/cli-core           # Full CLI with 443 command definitions
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

## 10 Business Layers, 443 Commands

| Layer | Examples | Purpose |
|-------|----------|---------|
| **Founder** | `/annual` `/okr` `/fundraise` `/swot` | Strategy and governance |
| **Business** | `/sales` `/marketing` `/finance` `/hr` | Revenue and operations |
| **Product** | `/plan` `/sprint` `/roadmap` `/brainstorm` | Product management |
| **Engineering** | `/cook` `/code` `/test` `/deploy` `/review` | Build and ship |
| **Ops** | `/audit` `/health` `/security` `/status` | Monitor and maintain |
| **Studio** | `/studio-audit` `/studio-portfolio` `/studio-roi` | VC studio / portfolio ops |
| **CTO** | `/cto-review` `/cto-roadmap` `/cto-architect` | Architecture and tech leadership |
| **PM** | `/pm-plan` `/pm-sprint` `/pm-okr` | Tactical product management |
| **Dev** | `/dev-feature` `/dev-fix` `/dev-test` | Developer execution |
| **Worker** | `/worker-code` `/worker-build` `/worker-push` | Atomic task execution |

Every command has a typed JSON contract (567 total) specifying input schema, output schema, agent assignments, and cascade triggers. Evidence: `factory/contracts/commands/`.

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
|  197 Skills        |  .claude/skills/ (SKILL.md definitions)
|  443 Commands      |  .claude/commands/ (command definitions)
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

*Verified counts as of 2026-04-17. Evidence: [`docs/claims-audit.md`](docs/claims-audit.md)*

| Metric | Count | Evidence |
|--------|-------|----------|
| Command definitions | 443 across 10 layers | `find .claude/commands -name '*.md' \| wc -l` |
| Live command modules (Python) | 43 | `find src/commands -name '*.py' -not -name '_*' \| wc -l` |
| Machine contracts (JSON) | 567 (typed I/O) | `ls factory/contracts/commands/ \| wc -l` |
| Skill definitions | 197 | `find .claude/skills -name 'SKILL.md' \| wc -l` |
| Python tests passing | 7,007 (34 skipped) | `python3 -m pytest -q --tb=no` |
| npm Packages | 2 published | `@mekongcli/openclaw-engine`, `@mekongcli/cli-core` |

## Roadmap — Binh Pháp 13 Verticals

Mekong IDE is the AI kernel. 13 vertical products are built on top of it.
1 shipped (CashClaw). 12 remaining are post-D-Day targets.

| Status | Vertical | Chapter |
|--------|----------|---------|
| **SHIPPED** | CashClaw (trading) | 2 作戰 |
| PARTIAL | MekongPay, MekongMind, MekongEye | 6, 8, 13 |
| SCAFFOLD | MekongHQ, MekongCounsel, MekongVault, MekongStudio, MekongBridge, MekongPulse, MekongMap, MekongForce, MekongLaunch | 1,3,4,5,7,9,10,11,12 |

Full roadmap: [`docs/BINH_PHAP_ROADMAP.md`](docs/BINH_PHAP_ROADMAP.md) · Scaffold plans: [`verticals/scaffold/`](verticals/scaffold/)

> XONG = $ in bank. Not PR merged. Not scaffold created.

---

## Contributing

```bash
# Setup
git clone https://github.com/longtho638-jpg/mekong-cli.git
cd mekong-cli && pnpm install

# Run Python tests (7,007 passing as of 2026-04-17)
python3 -m pytest -q --tb=short

# Run TS tests
cd packages/mekong-cli-core && pnpm test
cd packages/openclaw-engine && pnpm test

# Lint
pnpm --filter @mekongcli/cli-core lint
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

[BSL 1.1](LICENSE) -- source-available, converts to MIT on 2028-03-13.

SDK packages (`@mekongcli/openclaw-engine`, `@mekongcli/cli-core`) are MIT licensed.
