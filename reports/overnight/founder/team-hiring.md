# Team Building Plan — Mekong CLI

**Date:** March 2026
**Covers:** hire, recruiter-screen, recruiter-source, people-onboard
**Context:** Solo founder + AI agents today. First human hires post-seed (Q4 2026).

---

## Current "Team" Composition

| Member | Type | Role | Capacity |
|--------|------|------|----------|
| Founder | Human | CTO / CEO / Product | 1 FTE |
| Tôm Hùm daemon | AI | Autonomous task dispatch | ~3 FTE equivalent |
| PEV engine agents | AI | cook/fix/review/deploy | ~5 FTE equivalent |
| LeadHunter | AI agent | Sales prospecting | 0.5 FTE equivalent |
| ContentWriter | AI agent | Blog/docs content | 0.5 FTE equivalent |
| GitAgent / FileAgent / ShellAgent | AI agents | Engineering execution | 2 FTE equivalent |

**Effective capacity:** 1 human + ~12 FTE AI equivalents for structured tasks.

AI agents cannot replace: strategic decisions, investor relationships, enterprise sales calls, user empathy research, hiring judgment.

---

## Hiring Philosophy

1. **Hire humans only for what AI cannot do** — judgment, relationships, creativity in ambiguous spaces
2. **First hires are multipliers, not executors** — they amplify founder output, not replace it
3. **Culture fit > skill fit at seed** — wrong culture hire at 3-person company is fatal
4. **Hire slow, fire fast** — 2-week paid trial before full offer
5. **Vietnamese talent first** — lower cost, cultural alignment, home market advantage

---

## Hiring Roadmap 2026–2027

### Phase 1: Post-Seed (Q4 2026 — after $750K close)

**Hire 1: Senior Python Engineer**
- Start: Month 1 post-close
- Salary: $2,500–$4,000/mo (Vietnam) or $8,000–$12,000/mo (Singapore remote)
- Focus: PEV engine hardening, test coverage >80%, enterprise reliability

**Hire 2: Growth Marketer**
- Start: Month 3 post-close
- Salary: $1,500–$2,500/mo (Vietnam) or $5,000–$8,000/mo (global remote)
- Focus: dev community, content, ProductHunt/HN launches, Vietnamese market

### Phase 2: Series A (2027 — $3M ARR target)

**Hire 3: Enterprise Account Executive**
- Targets $499/mo Enterprise tier
- Commission-heavy comp: base $3,000/mo + 15% of closed ARR

**Hire 4: Developer Advocate**
- Owns agent marketplace community
- Conference presence, YouTube, OSS contributions

**Hire 5: Full-Stack Engineer**
- AgencyOS web dashboard
- VS Code extension maintenance

### Phase 3: Scale (2028)

- Head of Sales (VP-level)
- 2 additional engineers
- Customer Success Manager
- Finance/Ops (part-time or contractor)

---

## Hire 1: Senior Python Engineer — Full Job Spec

### Role
Build the production-grade infrastructure that makes Mekong CLI reliable enough for Enterprise customers.

### Responsibilities
- Harden PEV engine (`src/core/`) for 99.5% success rate SLA
- Expand test coverage from 62 tests to >80% coverage
- Performance optimization: `mekong cook` cold start < 3 seconds
- RaaS billing engine maintenance (`src/raas/` — 35+ modules)
- Agent development: new agents for agent marketplace
- Code review for community PRs

### Requirements
**Must have:**
- 3+ years Python, production systems
- Async Python (asyncio, aiohttp)
- CLI tool development experience (Click, Typer, Rich)
- Git, GitHub Actions CI/CD
- Understanding of LLM APIs (OpenAI SDK or compatible)

**Nice to have:**
- Cloudflare Workers / D1 experience
- OSS contribution history
- FastAPI / Pydantic
- Experience with RaaS / billing systems

### Sourcing Channels
1. Vietnamese dev communities: Viblo.asia job board, TopDev.vn
2. GitHub: search contributors to Typer, Rich, Aider repos
3. LinkedIn: "Python developer Vietnam" + "CLI tools"
4. Discord: Python Vietnam server, Cloudflare Workers community
5. Referral: ask first 50 GitHub stargazers

### Screening Process

**Round 1: Async code review (2 hours)**
- Send 3 files from `src/core/` with known issues
- Ask: "What would you improve? Identify any bugs."
- Looking for: specificity, depth, Python idioms, async understanding

**Round 2: Technical interview (60 min)**
- Live coding: extend `executor.py` with a new execution mode
- Architecture discussion: how would you make PEV engine distributed?
- Questions about `src/raas/billing_engine.py` — do they understand it?

**Round 3: Paid trial (2 weeks, $500)**
- Real task: increase test coverage on `src/core/verifier.py` from X% to 80%
- Ship via PR, full review process
- Evaluate: code quality, communication, initiative, speed

**Offer:** Full-time, 4-year vest / 1-year cliff, 0.5–1.0% equity (pre-Series A)

---

## Hire 2: Growth Marketer — Full Job Spec

### Role
Turn Mekong CLI's technical depth into developer community dominance.

### Responsibilities
- Own dev community presence: HN, Reddit, Dev.to, Viblo, Twitter/X
- Run ProductHunt and Hacker News launches
- Content calendar: 2 blog posts/month, 4 tweets/week
- Vietnamese market: Viblo articles, TopDev, FB groups, meetups
- YouTube channel: demo videos, tutorials
- SEO: docs site optimization
- Track acquisition metrics: stars, installs, trial signups by channel

### Requirements
**Must have:**
- Proven dev tools or OSS marketing experience
- Written English (blog posts, HN comments) — fluent
- Vietnamese (for local market)
- Data-driven: comfortable with analytics, A/B testing
- Self-starter: no hand-holding, moves fast

**Nice to have:**
- Technical background (can read Python code, understand CLI tools)
- Built a personal developer brand (blog, YouTube, Twitter)
- ProductHunt top launch experience

### Sourcing Channels
1. Twitter/X: follow dev tools marketers, look at who's driving OSS launches
2. Indie Hackers community: many solo marketers for dev tools
3. ProductHunt: connect with makers of successful dev tool launches
4. Viblo.asia: Vietnamese tech writers with marketing background
5. Referral from dev tool founders (Warp, Raycast, etc. alumni)

---

## Onboarding Protocol (New Hires)

### Week 1: Orientation
- [ ] Read CLAUDE.md — understand OpenClaw philosophy and 5-layer architecture
- [ ] Run `mekong cook "hello world"` — experience the product as user
- [ ] Read `src/core/` — understand PEV engine (engineer) or analytics dashboard (marketer)
- [ ] Shadow founder for 3 customer conversations
- [ ] Set up dev environment, run full test suite (`python3 -m pytest tests/`)
- [ ] Review `docs/` — codebase-summary, system-architecture, code-standards

### Week 2: Shallow end
- [ ] First real task assigned (scoped to 1-2 days)
- [ ] PR submitted and reviewed
- [ ] Join all community channels
- [ ] Meet 5 active users (async, via GitHub or Discord)

### Month 1: Full ownership
- [ ] Own one feature or channel end-to-end
- [ ] Weekly 1:1 with founder (30 min)
- [ ] Retrospective: what's working, what's not

### 90-day success criteria

| Role | 90-day Goal |
|------|-------------|
| Engineer | PEV engine test coverage >80%, 0 P1 bugs in their area |
| Marketer | 1,000 new GitHub stars, 1 successful HN/PH post |

---

## Compensation Philosophy

**Pre-Series A:**
- Pay fairly for Vietnam market (not below market)
- Equity is real — 0.25–1.0% vest over 4 years
- Remote-first, async-first
- No perks theater — pay cash, let people spend it

**Vietnam engineer market rates (2026):**
- Junior (2yr): $800–$1,500/mo
- Mid (3–5yr): $1,500–$3,000/mo
- Senior (5yr+): $3,000–$5,000/mo

**Equity grants (pre-Series A, $4M valuation):**
- 0.5% = $20,000 paper value (grows with company)
- 1.0% = $40,000 paper value
- Vest over 4 years, 1-year cliff, standard

---

## What AI Agents Cannot Replace (Never Automate These)

| Task | Why Human Needed |
|------|-----------------|
| User empathy interviews | Emotional intelligence, follow-up questions |
| Investor relationship building | Trust is human-to-human |
| Enterprise sales calls | Buying decisions require human authority |
| Hiring judgment (final call) | Culture fit assessment |
| Strategic pivots | Requires synthesis of ambiguous signals |
| Crisis management | Speed + judgment + stakeholder management |
| Community trust-building | Authenticity cannot be automated |
