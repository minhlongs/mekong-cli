---
name: eng-tech-debt
description: "Audit → prioritize → refactor → test → verify tech debt"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

description: "Audit → prioritize → refactor → test → verify tech debt"
argument-hint: [focus area or module]
allowed-tools: Read, Write, Bash, Task
---

# /eng:tech-debt — Tech Debt Sprint

**Super command** — chains 5 commands via DAG pipeline.

## Pipeline

```
[audit] ══╗
[coverage] ╣ (parallel)
[lint]  ══╝
           ▼
      [refactor $ARGUMENTS]
           │
           ▼
       [test --all]
```

## Estimated: 20 credits, 40 minutes

## Execution

Load recipe: `recipes/eng/tech-debt.json`

Execute DAG groups in dependency order:
- If mode = "parallel": spawn multiple subagents simultaneously via Task tool
- If mode = "sequential": run commands one after another
- Wait for group completion before starting dependent groups

## Goal context

<goal>$ARGUMENTS</goal>

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
