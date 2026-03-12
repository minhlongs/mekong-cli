# Mekong CLI v5.0 — Content Marketing Strategy
**Generated:** 2026-03-12 overnight | **Horizon:** Q2 2026

---

## Strategic Position

**Core message:** The AI CLI that runs your entire company, not just your code.
**Audience:** AI-forward founders, dev agencies, full-stack developers
**Differentiator:** Business-complete (5 layers) + universal LLM + $0 infra
**Tone:** Technical credibility + founder pragmatism. No hype. Show, don't tell.

---

## Content Pillars

### Pillar 1: Technical Deep Dives (40% of output)
Target: developers, CTOs, senior engineers
Formats: blog posts, Reddit technical threads, GitHub discussions
Topics:
- PEV engine internals — how Plan-Execute-Verify works
- DAG scheduler — parallel command execution at 4.9x speedup
- Universal LLM config — why 3 env vars beats SDKs
- CF Workers architecture — 42ms cold start breakdown
- MCU billing — deduct-on-success incentive design
- Rollback mechanics — reversible step execution

### Pillar 2: Founder Workflow Stories (30% of output)
Target: founders, product managers, agency owners
Formats: LinkedIn posts, case studies, newsletter issues
Topics:
- Morning routine automation (daily + sprint = 4min)
- OKR planning with `mekong okr`
- Investor pitch generation with `mekong pitch`
- Sprint planning from backlog to execution plan
- Financial modeling from raw data to forecast

### Pillar 3: Open Source Community (20% of output)
Target: open source contributors, CLI enthusiasts
Formats: GitHub READMEs, changelogs, contributor guides, Twitter threads
Topics:
- How to add a skill (SKILL.md pattern)
- How to add a command (.md in .claude/commands/)
- Agent architecture — extending AgentBase
- Binh Pháp quality system explained
- v5.1 roadmap and contribution opportunities

### Pillar 4: Comparison and Positioning (10% of output)
Target: buyers evaluating AI tools
Formats: comparison tables, landing page copy, Reddit comments
Topics:
- Mekong vs GitHub Copilot CLI (breadth)
- Mekong vs Cursor (terminal vs IDE)
- Mekong vs LangChain (user-facing vs framework)
- $0 CF infra vs Vercel/AWS cost comparison

---

## SEO Strategy

### Target Keywords

| Keyword | Volume | Difficulty | Pillar |
|---------|--------|------------|--------|
| AI CLI for developers | Medium | Medium | 1 |
| business automation CLI | Low | Low | 2 |
| open source AI terminal | Medium | Medium | 3 |
| cloudflare workers AI | Medium | High | 1 |
| mekong CLI | Low | Low | all |
| AI business operating system | Low | Low | 2 |
| plan execute verify AI | Very low | Very low | 1 |
| universal LLM CLI | Very low | Very low | 1 |

### Content Calendar — Q2 2026

**April (Launch momentum)**
- Week 1: PEV engine deep dive (blog + Reddit r/programming)
- Week 2: Morning founder routine story (LinkedIn + newsletter)
- Week 3: CF Workers architecture breakdown (blog + Hacker News)
- Week 4: Open source contribution guide (GitHub + Twitter)

**May (Case studies)**
- Week 1: Agency use case — 10 client projects, $0 infra (LinkedIn)
- Week 2: Solo founder use case — from okr to deploy in one terminal
- Week 3: Technical comparison — Mekong vs LangChain (blog)
- Week 4: v5.1 preview — coverage improvements (newsletter)

**June (Community)**
- Week 1: Contributor spotlight (GitHub + Twitter)
- Week 2: Binh Pháp quality system explained (blog)
- Week 3: MCU billing model deep dive (LinkedIn)
- Week 4: Q2 recap + v5.1 release (newsletter + all channels)

---

## Distribution Channels

| Channel | Cadence | Content type | Owner |
|---------|---------|--------------|-------|
| GitHub README | On release | Feature overview | Engineering |
| Blog (dev.to/Hashnode) | 2x/month | Technical deep dives | ContentWriter agent |
| LinkedIn | 3x/week | Founder stories + positioning | CMO |
| Twitter/X | Daily | Quick tips, metrics, threads | CMO |
| Reddit | 2x/week | Technical threads, AMA | CTO |
| Newsletter | 2x/month | Curated digest | CMO |
| Hacker News | Monthly | Show HN posts | Founder |
| Discord | Weekly | Community Q&A | Ops |

---

## Content Production Workflow

```
mekong content "topic: PEV engine internals"
  → ContentWriter agent drafts 800-word post
  → LeadHunter agent finds relevant subreddits
  → CMO agent reviews tone and positioning
  → Output: draft.md + distribution plan

mekong social "topic: morning routine"
  → generates Twitter thread + LinkedIn post
  → schedules via Buffer/Typefully API
  → tracks engagement via PostHog

Cadence: 2 blog posts + 15 social posts + 1 newsletter per month
MCU cost: ~40 MCU/month for content ops
```

---

## Success Metrics

| Metric | 30-day target | 90-day target |
|--------|--------------|---------------|
| GitHub stars | 500 | 2,000 |
| pip installs/week | 200 | 1,000 |
| Newsletter subscribers | 1,000 | 5,000 |
| Paid tenants | 20 | 100 |
| Blog post views | 5,000 | 25,000 |
| Reddit karma (r/commandline) | 500 | 2,000 |

**CONTENT ENGINE: STRATEGY DEFINED — READY TO EXECUTE**
