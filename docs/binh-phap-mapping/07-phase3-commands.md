# Phase 3: Command Migration — MK Namespace Expansion

> Status: DRAFT
> Prerequisite: Phase 1 (routing) and Phase 2 (structure) complete

## 1. Objective

Create 3 new mk commands:
- `cfo` — Ch2 financial oversight (budget, pricing, MRR)
- `cmo` — Ch11/12 marketing/growth (campaign, outreach, growth:experiment)
- `cso` — Ch6 research/intel (scout, competitive, venture:void-substance)

## 2. Command Skeleton Pattern

Template from existing mk-* commands:
```yaml
description: "Mekong CFO — Binh Pháp Ch2: Tình Hình (Situation)"
argument-hint: "[budget|pricing|mrr|finance]"
allowed-tools: Bash, Read
---
cfo "budget review Q3"
  -> python3 -m src.main mk binh-phap --chapter 2 --command finance
  -> LLM: Fable 5 (via escalation.py)
```

## 3. Per-Command Spec

### 3.1 cfo.md
description: "CFO Brain — Binh Pháp Ch2: Tình Hình + Ch5: Căn Cứ"
commands: [finance, budget, pricing, venture:five-factors, founder:validate]
model: fable (strategic)
output: budget_analysis.md + pricing_recommendation.md

### 3.2 cmo.md
description: "CMO Brain — Binh Pháp Ch11: Hỏa Công + Ch12: Xâm Phạm"
commands: [marketing, campaign, outreach, launch, growth:experiment]
model: fable (strategic)
output: campaign_plan.md + growth_experiment_log.md

### 3.3 cso.md
description: "CSO Brain — Binh Pháp Ch6: Trống Hư + Ch1: Tính Địa"
commands: [research, competitive, scout, venture:terrain, positioning]
model: fable (strategic)
output: competitive_intel.md + terrain_analysis.md

## 4. Integration Points

app_setup.py:
 from src.cli.csuite_commands import register_csuite_commands
  register_csuite_commands(root)  # adds cfo, cmo, cso directly to root

binh_phap_escalation.py:
  # Already routes strategic -> claude-fable-5
  # No changes needed

settings.json modelRouting rules:
  ADD:
  - match: [cfo, cmo, cso]
    provider: anthropic  # or zunef if ZUNEF env set
    model: claude-fable-5
    reason: Strategic C-suite commands use Fable

## 5. Migration Checklist
- [x] Register cfo/cmo/cso via register_csuite_commands() in app_setup.py
- [x] Add modelRouting rules to .claude/settings.json
- [ ] Test: cfo "budget review" -> routes to Fable 5
- [ ] Test: cmo "campaign plan" -> routes to Fable 5
- [ ] Test: cso "competitive intel" -> routes to Fable 5

## 6. Acceptance Criteria
- 3 commands appear in `mekong --help`
- Each command produces output via Binh Phap dispatcher
- LLM routing verified in logs (provider_name = "fable")
- Backward compatible: existing mk-* commands unchanged
