---
description: "MANDATORY first step — Generate full company architecture from a business idea before OpenClaw runs the 5-layer command system. Zero→IPO Agentic BizPlan OS."
argument-hint: "<your business idea in 1-3 sentences>"
---

# /project-idea — Agentic BizPlan OS: Zero→IPO Company Architecture Generator

**MANDATORY GATE:** OpenClaw will NOT run 5-layer commands until this step completes.
**Input:** A business idea (1-3 sentences)
**Output:** Full company blueprint in `.mekong/company.json` + 5-layer execution plan

**CRITICAL: AUTO-EXECUTE MODE. Do NOT ask questions. Do NOT present menus. Do NOT wait for user input. Execute ALL 25 steps sequentially and generate ALL output files immediately. This is an autonomous command — treat it as `--auto` mode.**

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

## 25-Step Company Architecture → 25 Files (Parallel)

Execute ALL phases in batch. **Each phase generates ALL its files in ONE response** — do NOT write files one by one.

```bash
mkdir -p plans/company-blueprint/
```

### Phase 1: Foundation — L1 Founder · Đạo (Steps 0-4) — WRITE ALL 5 FILES NOW
Generate ALL 5 files in batch:
- `00-framework.md` — **L1 Founder · Đạo** — Master Framework: Tri-Layer architecture, mission, stage detection
- `01-agency-os.md` — **L1 Founder · Đạo** — Agentic OS Design: AI governance, constitution
- `02-ipo-readiness.md` — **L2 CEO · Tướng** — IPO Readiness Score: VN/SEA compliance checklist
- `03-gap-report.md` — **L3 COO · Pháp** — Gap Report + 6-month Roadmap
- `04-refactor-frame.md` — **L1 Founder · Đạo** — Refactor to 2026 Frame

### Phase 2: Business Model — L5 CSO · Thiên — WRITE ALL FILES NOW
- `05-business-model.md` — **L5 CSO · Thiên** — Business Model Patterns: archetype, unit economics
- `06-customer-psychology.md` — **L5 CSO · Thiên** — Customer Psychology + Personas

### Phase 3: Brand + Content — L5 CMO · Thiên — WRITE ALL FILES NOW
- `07-brand-positioning.md` — **L5 CMO · Thiên** — Brand Positioning, category design
- `08-content-pillars.md` — **L5 CMO · Thiên** — Content Pillars + TOF strategy
- `09-landing-narrative.md` — **L5 CMO · Thiên** — Website/Landing Narrative
- `10-performance-ads.md` — **L5 CMO · Thiên** — Performance Ads + Creatives
- `11-advertorial.md` — **L5 CMO · Thiên** — Advertorial + Storytelling

### Phase 4: Revenue Engine — L5 CSO · Thiên — WRITE ALL FILES NOW
- `12-email-lifecycle.md` — **L5 CSO · Thiên** — Email + Lifecycle Sequences
- `13-sales-process.md` — **L5 CSO · Thiên** — Sales Process + Channels
- `14-gtm-experiments.md` — **L5 CSO · Thiên** — GTM Experiments + Bullseye

### Phase 5: Operations — L2 CEO + L3 COO + L2 CFO + L3 CHRO — WRITE ALL FILES NOW
- `15-aarrr-analytics.md` — **L3 COO · Pháp** — AARRR + Lean Analytics
- `16-fundraising.md` — **L2 CFO · Tướng** — Fundraising + VC Narrative
- `17-risk-scenario.md` — **L2 CEO · Tướng** — Risk + Scenario OS
- `18-talent-org.md` — **L3 CHRO · Pháp** — Talent + Org Design
- `19-industry-patterns.md` — **L2 CEO · Tướng** — Industry Patterns + IPO Archetypes
- `20-data-room.md` — **L3 COO · Pháp** — Data Room + Investor Materials

### Phase 6: Execution — L3 COO + L2 CEO + L2 CFO — WRITE ALL FILES NOW
- `21-okr-execution.md` — **L3 COO · Pháp** — Agentic Execution + OKR
- `22-board-governance.md` — **L2 CEO · Tướng** — Board Governance
- `23-esg-impact.md` — **L2 CFO · Tướng** — ESG + Impact
- `24-crisis-os.md` — **L3 COO · Pháp** — Crisis + Reputation OS

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
  ],
  "distribution": [
    { "file": "00-framework.md", "layer": "L1", "owner": "Founder", "sequence": 1, "binh_phap": "dao" },
    { "file": "01-agency-os.md", "layer": "L1", "owner": "Founder", "sequence": 1, "binh_phap": "dao" },
    { "file": "02-ipo-readiness.md", "layer": "L2", "owner": "CEO", "sequence": 4, "binh_phap": "tuong" },
    { "file": "03-gap-report.md", "layer": "L3", "owner": "COO", "sequence": 5, "binh_phap": "phap" },
    { "file": "04-refactor-frame.md", "layer": "L1", "owner": "Founder", "sequence": 1, "binh_phap": "dao" },
    { "file": "05-business-model.md", "layer": "L5", "owner": "CSO", "sequence": 2, "binh_phap": "thien" },
    { "file": "06-customer-psychology.md", "layer": "L5", "owner": "CSO", "sequence": 2, "binh_phap": "thien" },
    { "file": "07-brand-positioning.md", "layer": "L5", "owner": "CMO", "sequence": 2, "binh_phap": "thien" },
    { "file": "08-content-pillars.md", "layer": "L5", "owner": "CMO", "sequence": 2, "binh_phap": "thien" },
    { "file": "09-landing-narrative.md", "layer": "L5", "owner": "CMO", "sequence": 2, "binh_phap": "thien" },
    { "file": "10-performance-ads.md", "layer": "L5", "owner": "CMO", "sequence": 2, "binh_phap": "thien" },
    { "file": "11-advertorial.md", "layer": "L5", "owner": "CMO", "sequence": 2, "binh_phap": "thien" },
    { "file": "12-email-lifecycle.md", "layer": "L5", "owner": "CSO", "sequence": 2, "binh_phap": "thien" },
    { "file": "13-sales-process.md", "layer": "L5", "owner": "CSO", "sequence": 2, "binh_phap": "thien" },
    { "file": "14-gtm-experiments.md", "layer": "L5", "owner": "CSO", "sequence": 2, "binh_phap": "thien" },
    { "file": "15-aarrr-analytics.md", "layer": "L3", "owner": "COO", "sequence": 5, "binh_phap": "phap" },
    { "file": "16-fundraising.md", "layer": "L2", "owner": "CFO", "sequence": 4, "binh_phap": "tuong" },
    { "file": "17-risk-scenario.md", "layer": "L2", "owner": "CEO", "sequence": 4, "binh_phap": "tuong" },
    { "file": "18-talent-org.md", "layer": "L3", "owner": "CHRO", "sequence": 5, "binh_phap": "phap" },
    { "file": "19-industry-patterns.md", "layer": "L2", "owner": "CEO", "sequence": 4, "binh_phap": "tuong" },
    { "file": "20-data-room.md", "layer": "L3", "owner": "COO", "sequence": 5, "binh_phap": "phap" },
    { "file": "21-okr-execution.md", "layer": "L3", "owner": "COO", "sequence": 5, "binh_phap": "phap" },
    { "file": "22-board-governance.md", "layer": "L2", "owner": "CEO", "sequence": 4, "binh_phap": "tuong" },
    { "file": "23-esg-impact.md", "layer": "L2", "owner": "CFO", "sequence": 4, "binh_phap": "tuong" },
    { "file": "24-crisis-os.md", "layer": "L3", "owner": "COO", "sequence": 5, "binh_phap": "phap" }
  ],
  "distribution_state": {
    "status": "pending",
    "current_layer": 0,
    "completed_layers": [],
    "dispatched_agents": [],
    "gates_passed": []
  }
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

## Binh Phap Auto-Chain (NEW)

After generating company.json + blueprint, OpenClaw MUST auto-dispatch the **Binh Phap 13-Chapter Liên Hoàn Lệnh** — a chained sequence of commands that takes the project from idea to revenue.

Reference: `docs/BINH_PHAP_MASTER.md` for chapter→command mapping.
Reference: `docs/BINH_PHAP_1M_BATTLE_PLAN.md` for campaign strategy.

### Chain Sequence (auto-execute after blueprint)

```
PHASE 1: INTELLIGENCE (Chapters 1, 13)
  /swot "$ARGUMENTS"                    → SWOT analysis
  /venture:five-factors "$ARGUMENTS"    → 5-factor assessment
  /audit "project readiness"            → Technical audit

PHASE 2: STRATEGY (Chapters 3, 10)
  /plan "MVP features for $ARGUMENTS"   → Implementation plan
  /venture:terrain "market analysis"    → Market terrain mapping
  /brainstorm "GTM strategy"            → Go-to-market options

PHASE 3: BUILD (Chapters 4, 7, 9)
  /cook "Build MVP per plan"            → End-to-end implementation
  /test "Full test suite"               → Quality verification
  /deploy "Production deployment"       → Ship it

PHASE 4: REVENUE (Chapters 5, 12, 2)
  /marketing "Launch campaign"          → Marketing push
  /sales "Pipeline setup"              → Sales outreach
  /launch "Product launch"             → Coordinated launch
  /pricing "Monetization strategy"      → Revenue optimization

PHASE 5: SCALE (Chapters 6, 8, 11)
  /competitive "Market positioning"     → Competitive intel
  /growth:experiment "Growth loops"     → Growth experiments
  /finance "Financial tracking"         → Revenue monitoring
```

### Dispatch Rules
- Each phase MUST complete before the next begins
- If any command fails → Chapter 8 (Nine Variations): adapt and retry
- After Phase 4 → enter Growth Loop (Chapter 9: The March)
- Growth Loop runs indefinitely: `/standup` → `/sprint` → `/market` → `/growth` → `/audit`

### company.json Enhancement

Add `binh_phap_state` to track chain progress:
```json
{
  "binh_phap_state": {
    "current_chapter": 1,
    "current_phase": "intelligence",
    "completed_chapters": [],
    "chain_status": "active",
    "next_command": "/swot",
    "campaign": "first_blood",
    "target_mrr": 1000
  }
}
```

## Step 25: Bootstrap Economic Particle (Node.js — NO Python backend)

After all 24 steps complete, bootstrap the project as a ZenOS Economic Particle.
**IMPORTANT: Use Node.js mekong init, NOT Python mekong company init.**

```bash
# Derive project name from the business idea
PROJECT_NAME=$(echo "$ARGUMENTS" | sed 's/[^a-zA-Z0-9]/–/g' | tr '[:upper:]' '[:lower:]' | cut -c1-30)

# Create particle with Node.js init (NO Python backend needed)
mekong init "$PROJECT_NAME"

# Update ZENOS.md with the company mission from this plan
sed -i "s/Mission: _/Mission: $(echo "$ARGUMENTS" | head -c 80)/" "$PROJECT_NAME/ZENOS.md"
```

The result: a fully bootstrapped Economic Particle with:
- CK init harness (.claude/ + hooks)
- 39 AI agents (7 C-Level + 31 Dept Heads)
- 2-Guard deploy pipeline (.github/workflows/)
- ZENOS.md constitution populated with the business mission
- Git init with initial commit
- Ready for: `cd $PROJECT_NAME && mekong audit . --fix`

# Auto-Dispatch Trigger 🔄
After `mekong init` completes, RUN `/dispatch --project "$PROJECT_NAME"` to auto-route the 25 files to C-Level agents following the Binh Phap sequence (Đạo→Thiên→Địa→Tướng→Pháp).


## IMPORTANT
- This is the ENTRY POINT for every new project
- Step 25 auto-bootstraps as a ZenOS Economic Particle
- After /project-idea completes → `cd <project>` → COO dispatch workflows
- OpenClaw reads `.mekong/company.json` on boot
- Each campaign cycle = 1 GTM sprint toward $1M ARR
- Target: $1M ARR per project within GTM 2026
