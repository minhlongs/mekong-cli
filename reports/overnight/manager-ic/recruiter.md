# Recruiter Report — Mekong CLI
*Role: Recruiter | Date: 2026-03-11*

---

## Hiring Philosophy

Mekong CLI operates on an "AI-first workforce" model — the OpenClaw agent system
handles execution, humans handle judgment. This means we hire fewer people but need
each hire to be exceptional. Quality > quantity, always.

Core hiring principle: **Every candidate must dogfood Mekong CLI before their first interview.**
"Run `mekong cook 'Build a todo API'` and tell us what happened" = first screen question.

---

## Talent Market Analysis

### Python Backend Developer Market
- Demand: Very high (AI/ML tooling boom)
- Supply: Moderate for senior level
- Salary range (remote, mid-senior): $70-120K USD
- Competitive advantage for Mekong CLI: open source fame, AI-first culture, autonomy
- Competing with: Anthropic, Cursor, LangChain, Replicate for same talent

### TypeScript/Cloudflare Workers Developer Market
- Demand: High (CF ecosystem growing rapidly)
- Supply: Low — CF Workers expertise is rare
- Salary range (remote, mid-senior): $80-130K USD
- Competitive advantage: We're 100% CF stack — rare greenfield opportunity
- Competing with: Cloudflare itself, Vercel, Netlify

### Developer Relations Market
- Demand: High (every AI tool needs DevRel)
- Supply: Moderate
- Salary range: $65-95K USD
- Key differentiator: Must genuinely love CLIs and open source culture
- Red flag: DevRel candidates who can't write code

---

## Job Descriptions

### JD-001: Full-Stack Developer (Python + TypeScript)

**Mekong CLI — Full-Stack Developer (Remote)**

We're building an AI-operated business platform. 289 commands. 5 business layers.
Any LLM. The PEV engine (Plan→Execute→Verify) runs goals autonomously with rollback.

You'll own:
- `src/core/` PEV engine improvements
- `apps/openclaw-worker/` Tôm Hùm daemon (CF Workers + Queues)
- New agent types in `src/agents/`
- CF D1/KV/R2 data layer patterns

You are:
- 3+ years Python (async, type hints, pytest — non-negotiable)
- Cloudflare Workers experience (or strong Node.js + eager to learn CF)
- TypeScript comfortable (we have TS in the CF layer)
- Open source contributor (show us your GitHub)
- Uses LLMs daily in your workflow

Interview process:
1. `mekong cook "Build a REST API"` — async, 30 min, send us the output
2. 45-min technical conversation (architecture + PEV engine walkthrough)
3. Paid trial task (1 week, $500 — add one new agent to the registry)

Compensation: $70-90K base + equity in Binh Phap Venture Studio

---

### JD-002: Developer Relations Engineer

**Mekong CLI — Developer Relations Engineer (Remote)**

You'll be the bridge between Mekong CLI and the developer community.

You'll own:
- Tutorial content and "Cook Like a Pro" series
- Discord community management
- GitHub Discussions + issue triage
- Conference talks and HN/Reddit presence
- PostHog funnel analysis (growth metrics)

You are:
- Can write and run Python + TypeScript code
- Active open source community participant
- Technical writer with portfolio (blog posts, tutorials, docs)
- Data-curious: comfortable querying PostHog or SQL for insights
- LLM enthusiast — uses Ollama or OpenRouter daily

Compensation: $65-80K base + equity

---

### JD-003: Customer Success (Part-time → Full-time)

**Mekong CLI — Customer Success (Remote, Part-time)**

You'll help Enterprise customers get maximum value from Mekong CLI.

You'll own:
- Enterprise onboarding and first-week activation
- Polar.sh billing questions and credit management
- Churn prevention — identify at-risk accounts from D1 data
- Feature request synthesis → product team feedback

You are:
- Technical enough to run CLI tools and read error messages
- Excellent async communicator (Discord, email, Loom)
- Customer-obsessed: tracks every open issue until resolved

Compensation: $30-40/hr part-time, path to $45-60K full-time at $50K MRR

---

## Hiring Timeline

| Role | Trigger | Target Start |
|------|---------|-------------|
| Full-Stack Dev | MRR > $10K | Month 5-6 |
| Developer Relations | MRR > $25K | Month 8-9 |
| Customer Success (PT) | MRR > $15K | Month 6-7 |
| Head of Product | MRR > $50K | Month 12+ |

---

## Sourcing Channels

| Channel | Best For | Expected Yield |
|---------|----------|---------------|
| GitHub repo stargazers | Technical roles | High quality, low volume |
| r/LocalLLaMA contributors | Python devs with LLM interest | Medium |
| HN "Who's hiring?" thread | All technical roles | High quality |
| IndieHackers community | DevRel, CS roles | Medium |
| Twitter/X dev community | All roles | High volume, mixed quality |
| Wellfound (AngelList) | All roles | Standard startup talent |

**Best source:** People who already starred the repo and filed issues.
They're already qualified — they just need an invitation.

---

## Interview Scorecard (Technical Roles)

| Dimension | Weight | How to Assess |
|-----------|--------|--------------|
| Technical depth | 30% | Paid trial task output |
| LLM fluency | 25% | How they use Mekong CLI in trial |
| Communication | 20% | Written async communication quality |
| Culture fit | 15% | Binh Pháp principles alignment |
| Open source ethos | 10% | GitHub history review |

---

## Q2 Recruiting Actions

- [ ] Post JD-001 (Full-Stack Dev) to HN "Who's hiring?" thread
- [ ] Set up Wellfound company page for Binh Phap Venture Studio
- [ ] Create `CONTRIBUTING.md` — pipeline for open source → paid contributor
- [ ] Build GitHub stargazer outreach list (top contributors first)
- [ ] Define equity pool and vesting schedule before first offer
