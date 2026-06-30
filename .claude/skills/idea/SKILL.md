---
name: ck:idea
description: "Business ideation pipeline — GO/NO-GO validation, BMC, PRD generation, and plan output. Entrypoint for /goal pipeline. Integrates with Mekong SDLC (spec/design) + ClaudeKit /cook-auto for execution."
user-invocable: true
when_to_use: "Invoke when starting a new business idea, validating product-market fit, generating a business model canvas, or producing a PRD before implementation."
category: planning
keywords: [idea, validation, bmc, prd, business-model, go-nogo, bizplan]
license: MIT
argument-hint: "<business idea in 1-3 sentences>"
metadata:
  author: claudekit
  version: "1.0.0"
  mekong_origin: mekong-cli/.claude/skills/idea/SKILL.md
---

# /ck:idea — Business Ideation Pipeline: Idea → Validated Plan

**GATE COMMAND:** Must run before implementation begins. Produces a validated business case with GO/NO-GO verdict.

Read command spec at `.claude/commands/idea.md` (if present in project).
Consolidated reference: `references/bizplan-os-consolidated.json` (24 skills, 10KB)

## Pipeline Overview

```
/ck:idea "My business idea"
  → Stage Detection (Zero/PMF/Scale/IPO)
  → GO/NO-GO Validation
  → Business Model Canvas (BMC)
  → PRD Generation
  → Plan Output (./plans/)
  → ClaudeKit /cook-auto handoff
```

## Stage Detection

First, classify the idea into ONE stage:

| Stage | Signals |
|-------|---------|
| **Zero→PSF** | No paying customers, hypothesis stage, experimenting |
| **PMF→Early Scale** | Paying customers, some channels working, improving unit economics |
| **Scale-Up** | Series B+, proven unit economics, structured org |
| **Pre-IPO/IPO** | Governance-ready, audit trails, board structure |

## Tri-Layer Analysis (apply to EVERY section)

| Layer | Focus |
|-------|-------|
| **[Business]** | Strategy, model, market, product, finance, operations |
| **[Agentic]** | AI/Agent roles, automation %, agent KPIs |
| **[Governance]** | Controls, legal, risk, audit, IPO readiness |

## Pipeline Steps

### Step 1: GO/NO-GO Validation

Score the idea across these dimensions (1-5 each):

| Dimension | Questions |
|-----------|-----------|
| Market Size | TAM/SAM/SOM realistic? |
| Problem Clarity | Pain point specific and validated? |
| Differentiation | Sustainable moat vs competitors? |
| Unit Economics | Path to LTV > 3x CAC? |
| Execution Feasibility | Can this be built with available resources? |
| Agentic Fit | Where can AI/agents reduce cost or improve delivery? |

**Verdict:**
- **GO** (score >= 20): Proceed to BMC
- **CONDITIONAL GO** (score 15-19): Proceed with risk mitigation plan
- **NO-GO** (score < 15): Document why, suggest pivot angles

### Step 2: Business Model Canvas (BMC)

Generate a complete BMC:

| Block | Content |
|-------|---------|
| Value Propositions | What pain points are we solving? |
| Customer Segments | ICP, personas, Jobs-to-be-Done |
| Channels | How do we reach and deliver? |
| Revenue Streams | Pricing model, monetization |
| Cost Structure | Fixed + variable costs, agentic savings |
| Key Resources | Tech, talent, data, agents |
| Key Activities | Build, market, sell, support |
| Key Partnerships | Vendors, integrations, platforms |
| Customer Relationships | Self-serve, high-touch, community |

### Step 3: PRD Generation

Produce a Product Requirements Document with:

- **Vision**: One-paragraph product vision
- **Target Users**: ICP with demographics, psychographics, triggers
- **Core Features**: MVP feature list (YAGNI — minimum viable)
- **Success Metrics**: North Star metric + 3 supporting KPIs
- **Agentic Architecture**: Which agents automate which workflows
- **Tech Stack**: Recommended stack with rationale
- **Risks & Mitigations**: Top 3 risks + contingency plans

### Step 4: Plan Output

Write outputs to `./plans/` directory:

```
plans/
├── <date>-<slug>-ideation/
│   ├── plan.md              # Overview + verdict + BMC summary
│   ├── go-nogo-report.md    # Validation scores + verdict
│   ├── bmc.md               # Full Business Model Canvas
│   ├── prd.md               # Product Requirements Document
│   └── reports/
│       └── researcher-report.md  # Research findings (if any)
```

**Plan naming:** Use pattern `YYYYMMDD-HHMM-<slug>-ideation`

### Step 5: ClaudeKit Execution Handoff

After ideation completes, hand off to ClaudeKit execution:

```bash
# Option A: Direct plan execution
/ck:cook --auto ./plans/<date>-<slug>-ideation/plan.md

# Option B: Full bootstrap (if greenfield project)
/ck:bootstrap "<idea summary>" --auto
```

## Mekong SDLC Integration

This skill preserves Mekong SDLC hooks for projects that use the Mekong engine:

| Mekong Concept | ClaudeKit Equivalent | Notes |
|---------------|---------------------|-------|
| `mekong spec new` | PRD in `plans/` | Same artifact, different path |
| `mekong cook-auto` | `/ck:cook --auto` | Direct plan → implementation |
| `.mekong/company.json` | `plans/*/plan.md` | Company context in plan header |
| Binh Phap Chain | `/ck:plan` → `/ck:cook` | Sequential plan→cook pipeline |

**When Mekong is available:** After generating the plan, suggest:
```
mekong spec new <project-name>    # Create Mekong spec from PRD
mekong cook-auto                  # Auto-implement the plan
```

**When Mekong is NOT available:** Use pure ClaudeKit flow:
```
/ck:plan --hard <requirements>    # Detailed implementation plan
/ck:cook --auto <plan-path>       # Auto-implement
```

## Skill→Command Mapping (BizPlan OS)

| BizPlan Skill | Mekong Command | ClaudeKit Equivalent |
|---------------|----------------|---------------------|
| Business Model | /business-revenue-engine | BMC section in this skill |
| Customer Psychology | /design-user-research | PRD: Target Users section |
| Brand Positioning | /marketing-content-engine | PRD: Vision section |
| Content Pillars | /writer-blog | Post-ideation content plan |
| Website/Landing | /frontend-ui-build | PRD: Core Features |
| Performance Ads | /marketing-campaign-run | Post-ideation GTM plan |
| Sales Process | /sales-pipeline-build | BMC: Channels + Revenue |
| GTM Experiments | /growth-experiment | Post-ideation execution |
| AARRR Analytics | /analyst-report | PRD: Success Metrics |
| Fundraising | /founder-raise | Post-ideation (Scale+ stage) |
| Risk/Scenario | /ops-disaster-recovery | PRD: Risks & Mitigations |
| Talent/Org | /hr-recruit | Post-ideation (Scale+ stage) |
| Industry Patterns | /studio-strategy | GO/NO-GO: Market Size |
| Data Room | /studio-audit | Post-ideation (Pre-IPO stage) |
| OKR Execution | /pm-okr | PRD: Success Metrics |
| Governance | /legal-compliance-check | Tri-Layer: Governance |
| ESG/Impact | /ops-health-sweep | Tri-Layer: Governance |
| Crisis | /ops-security-audit | PRD: Risks & Mitigations |
| Agentic Design | /cto-architect | PRD: Agentic Architecture |
| IPO Readiness | /founder-ipo | Stage-specific (Pre-IPO only) |
| Gap Report | /analyst-report | GO/NO-GO: score gaps |

## Quick Flow

```bash
/ck:idea "AI-powered customer support SaaS for Vietnamese SMBs"
  → Stage: Zero→PSF
  → GO/NO-GO: Score 22/30 → GO
  → BMC: SaaS B2B, subscription, self-serve + onboarding
  → PRD: MVP = chat widget + admin dashboard + billing
  → Plan: ./plans/20260630-1105-ai-support-saas-ideation/
  → Handoff: /ck:cook --auto ./plans/20260630-1105-ai-support-saas-ideation/plan.md
```

## Critical Rules

- **NO implementation code** — output plans only, delegate to `/ck:cook`
- **Bilingual where relevant** — Vietnamese context for VN/SEA markets
- **YAGNI/KISS/DRY** — MVP features only, no gold-plating
- **Plans to `./plans/`** — never to `.mekong/` (ClaudeKit convention)
- **List unresolved questions** at end of each report
- **Zero console.log** — use structured markdown output

## References

- `references/bizplan-os-consolidated.json` — Full BizPlan OS skill catalog (24 skills)
