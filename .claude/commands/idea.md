---
description: "MANDATORY first step — Generate full company architecture from a business idea before OpenClaw runs the 5-layer command system. Zero→IPO Agentic BizPlan OS."
argument-hint: "<your business idea in 1-3 sentences>"
why-override: "Mekong-specific OpenClaw 5-layer integration; supersedes the older stock /idea at ~/.claude/commands/idea.md."
---

# /idea — Agentic BizPlan OS: Zero→IPO Company Architecture Generator

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

## IMPORTANT
- This is the ENTRY POINT for every new project
- OpenClaw reads `.mekong/company.json` on boot
- If no company.json → suggest running `/idea` first
- After /idea completes → auto-dispatch Binh Phap Chain (5 phases, 15+ commands)
- Each chain execution = 1 campaign cycle toward $1M ARR
- User can interrupt at any phase gate: "pause" stops, "continue" resumes
- Target: $1M ARR per project within GTM 2026

## PHASE 7 — AUTOPILOT HAND-OFF (NEW)

After all blueprint phases finish, automatically hand control to the
autonomous code-generation loop. This is the "không gõ lại" guarantee:
the user typed `/idea` once; everything from blueprint through shipping
code happens without further input.

### Dispatch (auto-execute, no confirmation)

```bash
# 1. Verify blueprint files exist
test -f .mekong/company.json || { echo "blueprint missing — abort"; exit 1; }

# 2. Hand off to the autopilot. It runs Plan→Execute→Verify→Reflect using
#    DeepSeek (or whatever LLM_BASE_URL is configured) with up to 1M
#    context. Worktree mode is on so the main repo is never touched.
mekong idea run "$ARGUMENTS — implement per blueprint at .mekong/company.json and tasks/" \
  --max-iter 24 \
  --max-tokens 800000 \
  --max-mcu 100 \
  --worktree \
  --yes
```

### What the autopilot does
1. Reads `.mekong/company.json` and the 5 mission files in `tasks/`.
2. Indexes the repo (~10k tokens) so the 1M window stays healthy.
3. Plans → writes code → runs typecheck → runs tests → claudekit
   checkpoints → reflects → repeats until DONE or budget exhausted.
4. Persists every turn to `.mekong/idea/<run-id>/audit.jsonl` so the
   founder can replay the whole run after the fact.
5. Drops the founder onto branch `idea/<slug>` in worktree
   `../mekong-idea-<slug>` for review.

### Stopping conditions
- LLM emits `<tool>DONE …</tool>` → success.
- Iteration cap (24) / token cap (800k) / MCU cap (100) → graceful stop.
- 3 consecutive tool failures → graceful stop.
- `Ctrl-C` → cooperative abort, state persisted, can be resumed later.

### After the autopilot exits
Tell the user EXACTLY this, no more, no less:

```
Autopilot finished. Next steps:
  cd ../mekong-idea-<slug>             # review the worktree
  git diff main..idea/<slug>           # full diff
  mekong idea show <run-id>            # plan + audit tail
  # when satisfied:
  cd ../mekong-cli && git merge idea/<slug>
```

The user is in `idea/<slug>` worktree. Do NOT continue editing files — the
autopilot already ran. Hand control back.
