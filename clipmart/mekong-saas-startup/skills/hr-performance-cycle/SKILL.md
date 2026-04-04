---
name: hr-performance-cycle
description: "Performance review cycle — self-assessment → manager review → calibration → feedback delivery"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# /hr:performance-cycle — Performance Review Cycle

**Super command** — chains 3 commands via DAG pipeline.

## Pipeline

```
[assess] ──────────────────────────────────────── PARALLEL
  ├── performance-review        → review-templates.md
  └── kpi --team                → team-metrics.md
         │
         ▼
[deliver] ─────────────────────────────────────── SEQUENTIAL
  └── feedback                  → feedback-guides.md
```

## Estimated: 10 credits, 15 minutes

## Execution

Load recipe: `recipes/hr/performance-cycle.json`

Execute DAG groups in dependency order:
- If mode = "parallel": spawn multiple subagents simultaneously via Task tool
- If mode = "sequential": run commands one after another
- Wait for group completion before starting dependent groups

## Goal context

<goal>$ARGUMENTS</goal>

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
