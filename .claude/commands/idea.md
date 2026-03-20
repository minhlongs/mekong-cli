---
description: "MANDATORY first step — Generate full company architecture from a business idea before OpenClaw runs the 5-layer command system. Zero→IPO Agentic BizPlan OS."
argument-hint: "<your business idea in 1-3 sentences>"
---

# /idea — Agentic BizPlan OS: Zero→IPO Company Architecture Generator

**MANDATORY GATE:** OpenClaw will NOT run 5-layer commands until this step completes.
**Input:** A business idea (1-3 sentences)
**Output:** Full company blueprint in `.mekong/company.json` + 5-layer execution plan

## Your Business Idea
$ARGUMENTS

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

Execute ALL steps sequentially. For each, output a concise section (not full skill — key decisions only):

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

After all 25 steps, generate:

### 1. `.mekong/company.json`
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
  "next_commands": [
    "/studio-strategy",
    "/product-sprint-plan",
    "/sales-pipeline-build",
    "/marketing-campaign-run",
    "/release-ship"
  ]
}
```

### 2. Execution Plan → `plans/company-blueprint/plan.md`
Map each department to mekong-cli 5-layer commands:

| Layer | Key Commands | Agent |
|-------|-------------|-------|
| Founder | /studio-strategy, /founder-raise, /studio-portfolio | CEO Agent |
| Business | /sales-pipeline-build, /marketing-campaign-run, /finance-budget-plan | Revenue Agent |
| Product | /product-sprint-plan, /pm-sprint, /design-sprint | Product Agent |
| Engineering | /cook, /dev-feature, /cto-architect, /release-ship | CTO Agent |
| Ops | /ops-health-sweep, /sre-morning-check, /analyst-report | Ops Agent |

### 3. First 5 Tasks for CTO Daemon
Generate 5 mission files in `tasks/` that OpenClaw will execute immediately:
- `HIGH_mission_<project>_gtm_strategy.txt`
- `HIGH_mission_<project>_build_mvp.txt`
- `HIGH_mission_<project>_sales_pipeline.txt`
- `HIGH_mission_<project>_marketing_launch.txt`
- `HIGH_mission_<project>_deploy_production.txt`

## IMPORTANT
- This is the ENTRY POINT for every new project
- OpenClaw reads `.mekong/company.json` on boot
- If no company.json → suggest running `/idea` first
- After /idea completes → CTO daemon auto-executes the 5-layer flow
- Target: $1M ARR per project within GTM 2026
