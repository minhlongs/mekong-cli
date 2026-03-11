# Mekong CLI — User Personas

## Research Basis
Synthesized from: README use-case segments (founder non-tech, developer, company operator),
command layer architecture (5 layers), MCU billing tiers, RaaS positioning.

---

## Persona 1: The Non-Technical Founder
**Name:** Minh Duc
**Role:** Solo founder / micro-SaaS operator
**Location:** Ho Chi Minh City / Southeast Asia
**Age:** 28-38

### Profile
Minh has a business idea but limited coding ability. He understands the domain (education SaaS, e-commerce, fintech) but can't hire engineers yet. He needs to validate, launch, and iterate fast with AI doing the heavy lifting.

### Goals
- Validate product idea before writing any code
- Get a pitch deck ready for investor meeting
- Understand unit economics and pricing before launch
- Run marketing campaigns without a marketing team

### Pain Points
- Cursor/Cline require coding knowledge to be useful
- ChatGPT gives advice but doesn't execute tasks
- Hiring costs: $3,000–5,000/mo for junior developer
- LangGraph/AutoGPT too complex to configure

### How Mekong Solves It
```bash
mekong founder/validate "EdTech platform for rural Vietnam"
mekong founder/pitch --market SEA --stage pre-seed
mekong annual "Business plan 2026 — EdTech startup"
mekong pricing "Freemium B2C vs B2B enterprise"
```

### Key Commands Used
- `founder/validate` — Customer discovery & PMF scoring
- `founder/pitch` — Pitch deck practice + VC Q&A simulation
- `annual` — Annual business planning
- `swot` — Strategic analysis
- `marketing` — Campaign brief generation
- `okr` — Objectives & key results

### Tier
**Starter $49/200cr** — 5-10 missions/month typical usage

### Aha Moment
Running `mekong annual "My startup plan"` and getting a structured 12-page business plan in 90 seconds.

---

## Persona 2: The Solo Developer
**Name:** Linh Nguyen
**Role:** Freelance fullstack developer / indie hacker
**Location:** Remote (Vietnam, Thailand, or Europe)
**Age:** 24-32

### Profile
Linh builds products alone. She knows React, FastAPI, PostgreSQL. Her bottleneck is the volume of work — she can build but needs 2x speed. She uses AI for code but wants it to actually run, verify, and commit — not just suggest.

### Goals
- Ship features 3x faster without cutting quality
- Automate the boring: tests, review, deploy
- Reduce cognitive load: let AI handle the plan, she approves or adjusts
- Build and monetize CLI tools herself using Mekong as template

### Pain Points
- Aider is good but no verification — needs manual check after every run
- Cline works but VS Code only — can't run in CI
- No rollback when AI makes wrong edits to production files
- Can't easily automate `cook → test → deploy` chain

### How Mekong Solves It
```bash
mekong cook "Add rate limiting middleware to FastAPI" --dry-run  # preview plan
mekong cook "Add rate limiting middleware to FastAPI"             # execute + verify
mekong fix "Login returns 500 on Safari" --verbose               # debug + patch
mekong review                                                     # quality gate
mekong deploy                                                     # Cloudflare push
```

### Key Commands Used
- `cook` — Full PEV pipeline (3 MCU) — most-used command
- `fix` — Debug + patch loop
- `review` — Code quality gate before PR
- `test` — Run + report test suite
- `deploy` — Cloudflare Workers/Pages push
- `plan --dry-run` — See plan before execution

### Tier
**Pro $149/1000cr** — 20-50 cook sessions/month

### Aha Moment
`mekong cook "Migrate SQLite to PostgreSQL"` executes a 12-step migration, runs tests, rollbacks one step that failed, re-attempts — without human intervention.

---

## Persona 3: The Engineering Team Lead
**Name:** Tuan Pham
**Role:** CTO / Tech Lead at 5-20 person startup
**Location:** Hanoi / Singapore
**Age:** 30-42

### Profile
Tuan leads a small engineering team. He needs to multiply team output, enforce code quality, and handle DevOps without a dedicated ops engineer. He evaluates tools carefully — security, cost, reliability matter.

### Goals
- Automate PR review and quality gates in CI
- Reduce time from ticket to deployment
- Universal LLM to avoid vendor lock-in (can use Qwen/DeepSeek for cost)
- Plugin system to add company-specific commands

### Pain Points
- GitHub Copilot: $39/seat × 10 devs = $390/mo, closed source
- Cursor: no CI/CD integration, IDE-only
- Building custom scripts for every workflow repetitive (DRY violation)
- LLM costs with OpenAI are high at scale

### How Mekong Solves It
```bash
# In CI pipeline:
mekong review --strict                                # Gate on PR quality
mekong test                                           # Run + report
mekong deploy --env staging                          # Cloudflare deploy

# Cost control:
export LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
export LLM_MODEL=qwen2.5-coder-32b-instruct          # $10/mo unlimited

# Custom commands:
mekong plugin install company-security-audit         # Team plugin
```

### Key Commands Used
- `review` — Automated PR review
- `audit` — Security + debt audit
- `health` — System health check
- `deploy` — Multi-env Cloudflare deploy
- `cook` — Feature implementation delegation
- Plugin system for company-specific workflows

### Tier
**Enterprise $499/unlimited** — CI/CD automation = unlimited call volume

### Aha Moment
Dropping GitHub Copilot Enterprise ($390/mo) and running `mekong review` in CI using Qwen at $10/mo with equivalent output quality.

---

## Persona 4: The Agency Operator
**Name:** Duc Ha
**Role:** Digital agency owner / AI agency founder
**Location:** Ho Chi Minh City / Southeast Asia
**Age:** 32-45

### Profile
Duc runs a 3-10 person agency building web products for clients. He wants to sell AI-powered delivery at premium margins, using Mekong as the backbone. He's interested in RaaS — reselling Mekong's capabilities under his own brand.

### Goals
- White-label Mekong CLI as "AgencyOS" for clients
- Automate client deliverables: landing pages, content, campaigns
- Use `company/init` to spin up new client company contexts fast
- Monetize via MCU credits at markup to end clients

### Pain Points
- Manual delivery is not scalable — 1 person = 1 project
- Client wants "AI-powered" but existing tools require technical clients
- No turnkey white-label AI agency platform exists
- RaaS pricing model ($49-499/mo) needs reseller margin

### How Mekong Solves It
```bash
mekong company/init "Hanoi Craft Coffee — D2C brand"
mekong marketing "Launch campaign for new espresso blend"
mekong brand "Brand identity guide — minimalist Vietnamese aesthetic"
mekong finance "Monthly P&L report Q1 2026"
```

### Key Commands Used
- `company/init` — Client company context initialization
- `company/report` — Automated client reporting
- `marketing` — Campaign briefs and copy
- `sales` — Outreach sequences
- `finance` — Budget tracking
- `hr` — Job description generation

### Tier
**Enterprise $499/unlimited** — Multiple client contexts, high volume

### Aha Moment
Running `mekong company/init` for a new client, then immediately generating a 30-day marketing calendar with `mekong marketing "30-day launch plan"` — 2 hours of agency work done in 8 minutes.

---

## Persona 5: The OSS Contributor / Power User
**Name:** Alex (Vietnam or international)
**Role:** Open-source developer, AI tooling enthusiast
**Age:** 20-30

### Profile
Alex found Mekong on GitHub. Interested in the PEV architecture, wants to extend it — build plugins, contribute new agent types, fork for personal workflows. Motivated by technical depth and open-source philosophy.

### Goals
- Understand and extend `src/core/orchestrator.py` PEV loop
- Build a custom agent (e.g., `mekong recipe/scrape` using `recipe_crawler.py`)
- Contribute factory contracts (`factory/contracts/*.json`)
- Use `--dry-run` and `--verbose` to understand execution graph

### Pain Points
- Aider and Cline are not extensible at the architecture level
- AutoGPT is too complex; LangGraph requires deep Python graph knowledge
- No CLI tool exposes planning phase as a first-class feature

### How Mekong Solves It
```bash
make self-test                                  # Understand factory contracts
mekong cook "hello world" --dry-run --verbose  # Trace PEV loop
# Fork → add custom agent to src/agents/
# Write factory/contracts/my-command.json
# PR to main
```

### Key Commands Used
- `cook --dry-run --verbose` — Trace execution for learning
- `plan` — Standalone plan generation
- Direct Python API: `from src.core.orchestrator import Orchestrator`

### Tier
**Free (Ollama)** — OSS contributors, local models

### Aha Moment
Reading `src/core/orchestrator.py` and seeing the clean Plan→Execute→Verify→Rollback loop — recognizing it as a proper architecture, not a hack. Filing first PR within a day.

---

## Persona Summary Table

| Persona | Primary Value | Tier | Top Commands |
|---------|--------------|------|-------------|
| Non-Tech Founder | Business automation | Starter $49 | annual, pitch, swot, founder/validate |
| Solo Developer | Coding 3x speed + verified | Pro $149 | cook, fix, review, deploy |
| Engineering Lead | CI/CD automation, cost | Enterprise $499 | review, audit, deploy, plugin |
| Agency Operator | White-label delivery | Enterprise $499 | company/init, marketing, sales |
| OSS Power User | Architecture extension | Free (Ollama) | cook --dry-run, plan |

---

## UX Interview Questions (Next Research Round)

1. "When you ran `mekong cook` for the first time, what surprised you?"
2. "Which commands do you run most — and which ones are confusing?"
3. "What would make you upgrade from Starter to Pro?"
4. "Have you ever been surprised by rollback behavior? Was it correct?"
5. "What business problem do you wish there was a `mekong` command for?"

---

_Personas v1.0 — Update after first 100 RaaS customers_
_Owner: Product / OpenClaw CTO_
