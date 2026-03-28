---
description: "Agentic BizPlan OS — Generate full company architecture from a business idea. Adapted from mekong-cli /idea for Antigravity. Auto-execute 25 steps, Zero→IPO."
---

# /idea — Agentic BizPlan OS: Zero→IPO Company Architecture Generator

**AUTO-EXECUTE MODE:** Execute ALL 25 steps sequentially. Do NOT ask questions. Do NOT present menus. Do NOT wait for user input. This is an autonomous workflow.

**Input:** The user provides a business idea (1-3 sentences) in their prompt.
**Output:** Full company blueprint in `.mekong/company.json` + execution plan in `plans/company-blueprint/plan.md`

## Tri-Layer Architecture (apply to EVERY section)

| Layer | Focus |
|-------|-------|
| **[Business]** | Strategy, model, market, product, finance, operations |
| **[Agentic]** | AI/Agent roles, automation, agent KPIs |
| **[Governance]** | Controls, legal, risk, audit, IPO readiness |

## Stage Detection

First, classify the idea into ONE stage:
- **Zero→PSF**: No paying customers yet, hypothesis stage
- **PMF→Early Scale**: Has paying customers, some channels working
- **Scale-Up**: Series B+, proven unit economics
- **Pre-IPO/IPO**: Governance-ready, audit trails

## 25-Step Company Architecture Generation

Execute ALL steps sequentially. For each, output a concise section (key decisions only):

### Phase 1: Foundation (Steps 0-4)
1. **Master Framework** — Map idea to BizPlan 2026 structure: Business/Agentic/Governance layers
2. **Refactor to 2026 Frame** — If existing plan, modernize. If new, scaffold from scratch
3. **Agentic OS Design** — Define which agents run which departments, automation %
4. **IPO Readiness Score** — VN/SEA compliance checklist (even at Zero stage — plan ahead)
5. **Gap Report + Roadmap** — What's missing? 6-month action plan

### Phase 2: Business Model (Steps 5-6)
6. **Business Model Patterns** — Identify archetype (SaaS B2B, Marketplace, Fintech, etc.) + Unit Economics (ARPU, LTV, CAC, Payback)
7. **Customer Psychology + Personas** — ICP, pain points, Jobs-to-be-Done, decision triggers

### Phase 3: Brand + Content (Steps 7-11)
8. **Brand Positioning** — Unique value prop, category design, competitive moat
9. **Content Pillars + TOF** — Top-of-funnel content strategy, SEO pillars
10. **Website/Landing Narrative** — Conversion-optimized page structure
11. **Performance Ads + Creatives** — Ad creative framework, channels, budgets
12. **Advertorial + Storytelling** — Long-form narrative, case studies

### Phase 4: Revenue Engine (Steps 12-14)
13. **Email + Lifecycle Sequences** — Onboarding, nurture, upsell, win-back
14. **Sales Process + Channels** — Pipeline stages, qualification, closing playbook
15. **GTM Experiments + Bullseye** — Go-to-market experiments, channel testing

### Phase 5: Operations (Steps 15-21)
16. **AARRR + Lean Analytics** — Metrics dashboard, North Star metric
17. **Fundraising + VC Narrative** — Pitch structure, investor targeting
18. **Risk + Scenario OS** — Risk map, downside scenarios, contingency
19. **Talent + Org Design** — Team structure, hiring plan, culture code
20. **Industry Patterns + IPO Archetypes** — Comparable companies, growth benchmarks
21. **Data Room + Investor Materials** — Deck, one-pager, financial model template

### Phase 6: Execution (Steps 22-24)
22. **Agentic Execution + OKR** — OKRs per quarter, agent task assignment
23. **Board Governance** — Board structure, advisory, reporting cadence
24. **ESG + Impact** — Sustainability framework, impact metrics
25. **Crisis + Reputation OS** — Crisis playbook, reputation monitoring

## Output Requirements

After all 25 steps, generate these files:

### 1. `.mekong/company.json`

// turbo
```bash
mkdir -p .mekong
```

Create the file with this structure:
```json
{
  "name": "<company name>",
  "stage": "<zero|pmf|scale|ipo>",
  "model": "<SaaS B2B|Marketplace|...>",
  "target_arr": "$1M",
  "icp": "<ideal customer profile>",
  "moat": "<competitive advantage>",
  "agents": { "<department>": "<agent role>" },
  "okrs": [ "<Q1 OKR>", "<Q2 OKR>" ],
  "next_steps": [
    "Build MVP",
    "Setup sales pipeline",
    "Launch marketing campaign",
    "Deploy to production",
    "Monitor and iterate"
  ]
}
```

### 2. Execution Plan → `plans/company-blueprint/plan.md`

// turbo
```bash
mkdir -p plans/company-blueprint
```

Map each department to actionable tasks:

| Layer | Key Actions | Agent/Owner |
|-------|-------------|-------------|
| Founder | Strategy, fundraising, portfolio | CEO |
| Business | Sales pipeline, marketing, finance | Revenue Team |
| Product | Sprint planning, design, user research | Product Team |
| Engineering | Build MVP, deploy, architecture | CTO/Dev Team |
| Ops | Health monitoring, SRE, analytics | Ops Team |

### 3. First 5 Priority Tasks → `plans/company-blueprint/tasks.md`

Generate 5 immediate action items with priority and owner.

## Follow-up Execution Chain

After blueprint is created, suggest these manual follow-up steps:

```
PHASE 1: INTELLIGENCE
  → SWOT analysis of the business idea
  → 5-factor assessment (market, team, product, traction, timing)
  → Technical audit for readiness

PHASE 2: STRATEGY  
  → Implementation plan for MVP features
  → Market terrain mapping
  → GTM strategy brainstorm

PHASE 3: BUILD
  → Build MVP end-to-end
  → Full test suite
  → Production deployment

PHASE 4: REVENUE
  → Launch marketing campaign
  → Sales pipeline setup
  → Coordinated product launch
  → Monetization/pricing strategy

PHASE 5: SCALE
  → Competitive positioning
  → Growth experiments
  → Financial tracking
```

Each phase should be executed as a separate conversation/task on Antigravity.

## IMPORTANT
- This is the ENTRY POINT for every new project
- If no `.mekong/company.json` exists → run this workflow first
- After completion → user follows the execution chain manually
- Target: $1M ARR per project within GTM 2026
