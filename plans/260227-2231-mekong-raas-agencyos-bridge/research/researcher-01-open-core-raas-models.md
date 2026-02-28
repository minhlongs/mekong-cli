# Open Core Business Models for AI CLI Tools & RaaS Platforms

**Date:** 2026-02-27 | **Researcher:** researcher-01 | **Max lines:** 150

---

## 1. How Successful AI CLI Tools Monetize

### Supabase (Open Core, $70M ARR, $5B valuation 2025)
- Core: fully open-source Postgres backend (self-host forever free)
- Paid: managed hosting, scaling, support SLAs, enterprise SSO
- Free tier: 50K MAU + 500MB DB — generous enough to hook devs
- Trigger for upgrade: app scales → compute/storage costs kick in
- Key insight: **community adoption → enterprise revenue**, not vice versa

### Cursor ($500M ARR est. 2025)
- Core: VS Code fork — proprietary from day one (NOT open core)
- Model: flat subscription ($20/mo Hobby, $40/mo Business)
- Paid unlocks: GPT-4/Claude access, unlimited completions, team features
- Key insight: **DevX moat** — switching cost is learned muscle memory

### Continue.dev (open-core, VC-backed)
- Core: IDE extension — fully open source (Apache 2.0)
- Paid: Continue Hub (managed model routing, team config sync, audit logs)
- Monetizes team coordination, NOT the core AI functionality
- Key insight: **keep the tool free, sell the orchestration layer**

### Vercel/Next.js Pattern
- Next.js: 100% MIT open source, millions of users
- Vercel: paid hosting/CI/CDN on top — the "batteries included" cloud
- Free tier generous → upgrade trigger is bandwidth/team size
- Key insight: **framework as top-of-funnel**, cloud as revenue engine

---

## 2. Open Source → Commercial Bridge Patterns

| Layer | Open (Free) | Closed (Paid) |
|-------|------------|---------------|
| Core engine | Plan-Execute-Verify, agent SDK | Managed orchestration, SLA |
| Storage | Local file IPC | Cloud sync, vector DB, team memory |
| Auth | None / DIY | SSO, RBAC, audit trail |
| Scale | Single machine | Multi-tenant, auto-scaling |
| Support | Community Discord | Dedicated CSM, SLA response |
| Analytics | None | Usage dashboards, cost reports |
| Compliance | N/A | SOC2, HIPAA, GDPR docs |

**Rule of thumb:** Open everything that creates adoption; close everything that reduces churn.

LangChain/LangGraph: open framework → paid LangSmith (observability), LangGraph Cloud (deployment).
CrewAI: open framework → paid CrewAI Studio (no-code builder for non-devs).

---

## 3. RaaS for Non-Tech Agency Owners — Selling Outcomes Not Tools

### Definition
Results-as-a-Service (RaaS): customer pays for measurable business outcome, NOT software access.
- NOT "you get 10K AI agent calls/month"
- YES "you get 50 qualified leads/month" or "95% support tickets auto-resolved"

### Market Size
Global AI agencies: $7.63B in 2025, growing 45.8% YoY. Margins 70–90%.

### Pricing Benchmarks for Agency Owners
| Model | Structure | Range |
|-------|-----------|-------|
| Monthly retainer | Fixed, outcome-guaranteed | $2K–$20K/mo |
| Value share | % of value delivered | 10–25% of savings |
| Per-task | Unit of work completed | $5–$50/task |
| Credit pack | Prepaid, rollover | $500–$5K packs |

### Key Selling Points for Non-Tech Buyers
1. Show ROI dashboard, not API docs
2. Guarantee SLA on outcome (X leads, Y tickets resolved)
3. Offer "done for you" onboarding — eliminate setup friction
4. Provide human escalation fallback — reduces fear of "AI mistakes"
5. Monthly business review (MBR) — prove value, upsell naturally

### Example: Bairong RaaS (Dec 2025)
Launched "Results Cloud" — enterprises pay per verified business outcome (fraud prevented, loan approved, ticket resolved). No seat licenses.

---

## 4. Maintaining OSS Community While Building Commercial Layer

### Best Practices (verified from Supabase, LangChain, CrewAI)
1. **License clearly**: MIT/Apache for core; commercial add-ons proprietary or BSL
2. **Never close what's already open** — community backlash kills adoption (HashiCorp BSL mistake)
3. **Commercial ≠ features users need daily** — gate enterprise-specific needs (SSO, audit)
4. **Contribute upstream visibly** — community sees your team as stewards, not extractors
5. **Discord/GitHub as first-class** — fast response to issues builds trust
6. **Paid team = 80% OSS features, 20% infra/ops** — correct ratio

### Anti-patterns
- Gating debugging/logging behind paywall → community forks
- Closing SDK after adoption → trust collapse (see Elasticsearch)
- "Open source" as marketing label only → detected instantly, backlash fatal

---

## 5. AI Agent Platform Pricing Models

### Token-Based (Anthropic/OpenAI style)
| Tier | Input/M tokens | Output/M tokens | Use case |
|------|---------------|-----------------|----------|
| Haiku 4.5 | $1 | $5 | High-volume, cheap |
| Sonnet 4.5 | $3 | $15 | Balanced (default) |
| Opus 4.5 | $5 | $25 | Complex reasoning |

Batch API: 50% discount. Prompt caching: 90% savings on repeated context.

### Seat-Based (SaaS agents)
- Microsoft Copilot: $30/user/mo + $4/hour compute for agent tasks
- Claude Team: $30/user/mo (min 5 seats)
- Cursor Business: $40/user/mo

### Task/Credit-Based (Agency reseller sweet spot)
- Sell credit packs to clients (e.g., 1,000 "tasks" = $500)
- Markup: buy API at $0.015/task, sell at $0.50/task = 33x margin
- Works for non-tech buyers who can't reason about tokens

### Hybrid Tiers (Recommended for Mekong/AgencyOS)
```
Tier 0 - Starter (Free):   OSS self-hosted, community support
Tier 1 - Growth ($299/mo): Managed, 5K tasks/mo, basic dashboard
Tier 2 - Scale ($999/mo):  20K tasks, custom agents, SLA, MBR
Tier 3 - Enterprise:       Custom pricing, white-label, dedicated infra
```

---

## Synthesis for Mekong-CLI / AgencyOS Bridge

1. **OSS core** (Plan-Execute-Verify engine, agent SDK) = top-of-funnel, MIT licensed
2. **Managed cloud layer** = revenue engine (multi-tenant, analytics, team sync)
3. **RaaS wrapping** = non-tech agency owners pay per outcome (leads, tasks, reports)
4. **White-label tier** = highest margin, resellers brand it as their own
5. **Credit packs** = best fit for Vietnamese SME market (predictable spend, no seat complexity)

---

## Unresolved Questions

1. What specific outcomes can Mekong/AgencyOS guarantee? (leads/mo? tasks/mo? cost savings?)
2. Target segment: dev-facing (CLI) vs. non-tech agency owner — requires different packaging
3. Vietnamese market price sensitivity vs. USD pricing benchmarks above — needs local research
4. Open-source license choice: MIT vs. BSL vs. AGPL tradeoffs for Mekong's competitive context
5. How to handle LLM cost volatility in fixed-price outcome contracts?

---

**Sources:**
- [Supabase $5B Valuation / $70M ARR](https://articles.uvnetware.com/software-engineering/supabase-backend-platform-architecture/)
- [Inside Supabase's Breakout Growth](https://medium.com/craft-ventures/inside-supabases-breakout-growth-lessons-scaling-to-4-5m-devs-powering-ai-vibe-coding-dc574acfafaa)
- [Open-core model - Wikipedia](https://en.wikipedia.org/wiki/Open-core_model)
- [Why RaaS is the Future of SaaS - TwinsAI](https://www.twinsai.com/blog/why-raas-results-as-a-service-is-the-future-of-saas)
- [Agentic AI Breaking SaaS Pricing - Zenskar](https://www.zenskar.com/blog/agentic-saas-pricing)
- [The Rise of Results-as-a-Service - LBZ Advisory](https://liatbenzur.com/2024/12/05/ai-agents-saas-to-raas-business-transformation/)
- [AI Agency Pricing Guide 2025](https://digitalagencynetwork.com/ai-agency-pricing/)
- [How to Price AI Products 2026 - Aakash G](https://www.news.aakashg.com/p/how-to-price-ai-products)
- [Anthropic Claude API Pricing](https://platform.claude.com/docs/en/about-claude/pricing)
- [The Real Cost of AI Coding Agents 2026](https://www.gauraw.com/real-cost-ai-coding-agents-2026/)
- [Bairong RaaS Strategy Launch](https://www.morningstar.com/news/pr-newswire/20251219cn51630/ai-agent-paradigm-shift-bairong-launches-raas-strategy-and-results-cloud-platform)
