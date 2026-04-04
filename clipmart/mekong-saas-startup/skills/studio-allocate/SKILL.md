---
name: studio-allocate
description: "Reallocate MCU budget across projects. 3 credits, ~10 min."
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

description: "Reallocate MCU budget across projects. 3 credits, ~10 min."
argument-hint: [context or goal]
allowed-tools: Read, Write, Bash, Task
---

# /studio:allocate — Budget Allocation

**VC Studio super command** — portfolio-level orchestration.

## Pipeline

```
DELEGATION: studio:allocate → cto:* → dev:* → worker:*
OUTPUT: reports/studio/allocate/
```

## Estimated: 3 credits, ~10 minutes

## Execution

Load recipe: `recipes/studio/allocate.json`

Execute DAG groups in dependency order:
- If mode = "parallel": spawn multiple subagents simultaneously via Task tool
- If mode = "sequential": run commands one after another
- Wait for group completion before starting dependent groups

## Goal context

<goal>$ARGUMENTS</goal>

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
