---
description: "COO auto-dispatch — route /idea 25 files to C-Level agents per Inverted Triangle layer mapping"
argument-hint: "[--project <name> | --status | --reset]"
---

# /dispatch — Auto-Dispatch Pipeline

**COO Agent:** Routes 25 blueprint files to correct C-Level agents.
**Sequence:** L1 Founder (Đạo) → L5 CSO/CMO (Thiên) → L4 CTO (Địa) → L2 CEO/CFO (Tướng) → L3 COO/CHRO (Pháp)
**Prerequisite:** Run `/idea <business idea>` first to generate 25 files and `company.json`

## Usage

```
/dispatch                          # Auto-detect project, show pending dispatch
/dispatch --project MyStartup      # Dispatch for specific project
/dispatch --status                 # Show current distribution state
/dispatch --reset                  # Reset distribution_state to pending
```

## Pipeline

### Step 1: Read distribution

Read `plans/company-blueprint/.mekong/company.json` (or `<project>/.mekong/company.json`), extract `distribution` array.

If no `company.json` found → error: "No company.json found. Run /idea first."

### Step 2: Group by layer

Group distribution entries by `layer`:

| Layer | Binh Phap | Files | Owner |
|-------|-----------|-------|-------|
| L1 | Đạo | 00-framework, 01-agency-os, 04-refactor-frame | Founder |
| L5 | Thiên | 05→14 (10 files) | CSO + CMO |
| L4 | Địa | (receives specs from L5) | CTO |
| L2 | Tướng | 02, 16, 17, 19, 22, 23 (6 files) | CEO + CFO |
| L3 | Pháp | 03, 15, 18, 20, 21, 24 (6 files) | COO + CHRO |

### Step 3: Dispatch by Binh Phap Sequence

Execute in order. Each layer requires WIN-WIN-WIN gate before proceeding.

#### Gate 1: L1 Founder · Đạo
Founder reads 3 files:
- `00-framework.md` — Tri-Layer architecture, mission
- `01-agency-os.md` — AI governance, constitution
- `04-refactor-frame.md` — Refactor direction

**Action:** Confirm mission alignment
**Gate:** WIN-WIN-WIN — "Founder win? Platform win? Customer win?"
**Pass →** update `distribution_state.completed_layers: ["L1"]`
**Fail →** STOP. Fix mission before proceeding.

#### Gate 2: L5 Mặt Trận · Thiên
**CSO** receives:
- `05-business-model.md`, `06-customer-psychology.md`
- `12-email-lifecycle.md`, `13-sales-process.md`, `14-gtm-experiments.md`

**CMO** receives:
- `07-brand-positioning.md`, `08-content-pillars.md`, `09-landing-narrative.md`
- `10-performance-ads.md`, `11-advertorial.md`

**Action:** Market analysis → Generate GTM spec for CTO (L4)
**Gate:** WIN-WIN-WIN
**Pass →** `completed_layers: ["L1", "L5"]`
**Fail →** Fall back to defense (Chapter 7: Competition)

#### Gate 3: L4 Sản Xuất · Địa
**CTO** receives specs from L5 (CSO/CMO output).

**Action:** Feasibility check → Architecture plan → Build schedule
**Gate:** WIN-WIN-WIN
**Pass →** `completed_layers: ["L1", "L5", "L4"]`
**Fail →** Chapter 4: Position adjustment

#### Gate 4: L2 Chiến Lược · Tướng
**CEO** receives:
- `02-ipo-readiness.md`, `17-risk-scenario.md`
- `19-industry-patterns.md`, `22-board-governance.md`

**CFO** receives:
- `16-fundraising.md`, `23-esg-impact.md`

**Action:** Resource allocation → Fundraising strategy
**Gate:** WIN-WIN-WIN
**Pass →** `completed_layers: ["L1", "L5", "L4", "L2"]`
**Fail →** Chapter 6: Anti-dilution

#### Gate 5: L3 Vận Hành · Pháp
**COO** receives:
- `03-gap-report.md`, `15-aarrr-analytics.md`
- `20-data-room.md`, `21-okr-execution.md`, `24-crisis-os.md`

**CHRO** receives:
- `18-talent-org.md`

**Action:** OKR creation → Workflow automation → Monitoring setup
**Gate:** WIN-WIN-WIN
**Pass →** `distribution_state.status: "completed"`
**Fail →** Chapter 9: Movement adjustment

### Step 4: Update distribution_state

After each gate, update `company.json.distribution_state`:

```
status: pending | in_progress | completed | failed
current_layer: 0-5
completed_layers: ["L1"] → ["L1","L5"] → etc.
dispatched_agents: ["founder-agent", ...]
gates_passed: ["L1", ...]
```

### Step 5: Final status

When all 5 layers complete:
- `status: "completed"`
- Ready for: `mekong first-ship` or layer-specific commands
- Message: "✅ All 25 files dispatched. 8 agents activated. Ready to execute."

## Implementation Notes

- This is a **command definition** (.md) — LLM reads this and executes dispatch logic directly
- Each layer spawns subagents via Agent tool for file reading + planning
- WIN-WIN-WIN gate uses `AskUserQuestion` for Founder approval
- Ship the plan file: update plan.md current phase, generate report
- Commit and push after pipeline completes
