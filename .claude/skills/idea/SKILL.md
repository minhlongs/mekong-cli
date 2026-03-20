---
name: ck:idea
description: "MANDATORY first step — Agentic BizPlan OS: Generate full company architecture (25 steps, Zero→IPO) from a business idea. Outputs .mekong/company.json + 5-layer execution plan + CTO missions."
argument-hint: "<business idea in 1-3 sentences>"
license: MIT
---

# /idea — Agentic BizPlan OS: Zero→IPO

**GATE COMMAND:** Must run before OpenClaw 5-layer system activates.

Read command spec at `.claude/commands/idea.md`.
Consolidated reference: `references/bizplan-os-consolidated.json` (24 skills, 10KB)

## Skill→Command Mapping

| BizPlan Skill | Mekong Command | Layer |
|---------------|----------------|-------|
| Business Model | /business-revenue-engine | Business |
| Customer Psychology | /design-user-research | Product |
| Brand Positioning | /marketing-content-engine | Business |
| Content Pillars | /writer-blog | Business |
| Website/Landing | /frontend-ui-build | Product |
| Performance Ads | /marketing-campaign-run | Business |
| Sales Process | /sales-pipeline-build | Business |
| GTM Experiments | /growth-experiment | Business |
| AARRR Analytics | /analyst-report | Ops |
| Fundraising | /founder-raise | Founder |
| Risk/Scenario | /ops-disaster-recovery | Ops |
| Talent/Org | /hr-recruit | Business |
| Industry Patterns | /studio-strategy | Founder |
| Data Room | /studio-audit | Founder |
| OKR Execution | /pm-okr | Product |
| Governance | /legal-compliance-check | Business |
| ESG/Impact | /ops-health-sweep | Ops |
| Crisis | /ops-security-audit | Ops |
| Agentic Design | /cto-architect | Engineering |
| IPO Readiness | /founder-ipo | Founder |
| Gap Report | /analyst-report | Ops |

## Quick Flow
```
/idea "My SaaS idea" → 25-step analysis → company.json → 5 tasks → CTO daemon
```
