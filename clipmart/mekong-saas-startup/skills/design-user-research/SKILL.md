---
name: design-user-research
description: "UX research sprint — personas → user journeys → pain points → opportunity map"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

description: "UX research sprint — personas → user journeys → pain points → opportunity map"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /design:user-research — UX Research Sprint

**Super command** — chains 3 commands via DAG pipeline.

## Pipeline

```
[discover] ─────────────────────────────────────── PARALLEL
  ├── persona                   → personas.md
  └── feedback                  → user-feedback.md
         │
         ▼
[synthesize] ───────────────────────────────────── SEQUENTIAL
  └── brainstorm                → opportunity-map.md
```

## Estimated: 12 credits, 20 minutes

## Execution

Load recipe: `recipes/design/user-research.json`

Execute DAG groups in dependency order:
- If mode = "parallel": spawn multiple subagents simultaneously via Task tool
- If mode = "sequential": run commands one after another
- Wait for group completion before starting dependent groups

## Goal context

<goal>$ARGUMENTS</goal>

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
