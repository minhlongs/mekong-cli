# HR Manager Report — Mekong CLI
*Role: HR Manager | Date: 2026-03-11*

---

## Current Team Structure

Mekong CLI is a founder-led project operating under Binh Phap Venture Studio.
The AI agent layer (OpenClaw / Tôm Hùm daemon) effectively acts as a parallel
workforce — 17+ agent types covering coding, reviewing, testing, planning, and ops.
Human headcount is minimal by design.

**Current human roles (estimated):**
- 1 Founder/CTO (architecture, strategy, product)
- 1-2 Contributors (open source, ad hoc)

---

## Hiring Plan by Milestone

### Milestone 1: $10K MRR (Months 1-4)
No new hires needed. OpenClaw handles execution. Founder owns sales + eng.

### Milestone 2: $25K MRR (Months 5-8)
**First hire: Full-Stack Developer (Python + TypeScript)**
- Owns `src/core/` PEV engine improvements
- Cloudflare Workers/D1 backend patterns
- Salary range: $70-90K remote

### Milestone 3: $50K MRR (Months 9-14)
**Second hire: Developer Relations / Growth Engineer**
- Community (Discord, GitHub Discussions, HN)
- Tutorial content, integration guides
- Metrics instrumentation (PostHog/Mixpanel)
- Salary range: $65-80K remote

**Third hire: Customer Success (part-time → full-time)**
- Enterprise onboarding, credit management support
- Polar.sh billing questions, churn prevention
- Salary range: $45-60K remote

### Milestone 4: $100K MRR
- Head of Product (PM background, developer tools experience)
- Second backend engineer (agent framework, new commands)
- Consider Vietnam-based team for cost efficiency (Binh Phap studio origin)

---

## Key Skills Matrix

| Role | Must Have | Nice to Have |
|------|-----------|-------------|
| Backend Dev | Python 3.9+, async patterns, REST API | Cloudflare Workers, Typer, pytest |
| Full-Stack Dev | TypeScript, Next.js, Tailwind | CF Pages, MD3, Polar.sh SDK |
| DevRel | Technical writing, open source culture | LLM/AI tooling experience |
| DevOps/SRE | Cloudflare ecosystem, CI/CD | GitHub Actions, Wrangler CLI |

---

## Culture Principles

Derived from CLAUDE.md and Binh Pháp philosophy:

1. **Mission first** — "OpenClaw runs this company." Humans approve, AI executes.
2. **YAGNI / KISS / DRY** — No over-engineering. Files < 200 lines.
3. **Binh Pháp quality** — 0 tech debt, 0 `any` types, tests always pass.
4. **Async-first** — Remote, timezone-flexible, written communication preferred.
5. **Vietnamese roots, global reach** — ĐIỀU 55: Vietnamese language in internal comms,
   English for code and external-facing content.

---

## Compensation Philosophy

- Below-market base + meaningful equity (MIT open source = equity in the studio entity)
- Remote-first, no office overhead
- Learning budget: $1,000/yr per engineer for LLM API credits + conferences
- "Use the product daily" requirement — dogfooding is non-negotiable

---

## AI Workforce Policy

The Tôm Hùm daemon and CC CLI agents are treated as productive workforce members:
- Agent "hours" tracked via MCU consumption
- No HR overhead for AI agents (no benefits, no onboarding)
- Humans focus on judgment, approval, and novel problem-solving
- Policy: any task doable by `mekong cook` MUST be delegated to it first

---

## Retention Risks

| Risk | Mitigation |
|------|-----------|
| Engineer boredom (AI does the work) | Focus humans on architecture + novel agents |
| Underpay vs FAANG | Offset with autonomy + equity + mission alignment |
| Burnout from small team | Clear scope via agent delegation |

---

## Onboarding Checklist (New Dev Hire)

- [ ] Clone repo, run `make setup`, run `make self-test` (must show 100/100)
- [ ] Set up LLM env vars, run `mekong cook "hello world"`
- [ ] Read `src/core/` — understand PEV engine
- [ ] Read `CLAUDE.md` — understand OpenClaw constitution
- [ ] Read `.claude/skills/` catalog — understand 245 skills
- [ ] First task: add one new command to `.agencyos/commands/`
- [ ] First PR: must pass `python3 -m pytest tests/` locally

---

## Next HR Actions

- [ ] Draft job description for Full-Stack Developer (target: $25K MRR trigger)
- [ ] Set up async hiring process (Loom video submissions over live interviews)
- [ ] Create contributor guide in `CONTRIBUTING.md` for open source pipeline
- [ ] Define equity pool in studio entity (target: 10-15% for first 3 hires)
