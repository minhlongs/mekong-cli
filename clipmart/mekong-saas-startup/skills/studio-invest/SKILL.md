---
name: studio-invest
description: "Add new project to portfolio. 8 credits, ~30 min."
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

description: "Add new project to portfolio. 8 credits, ~30 min."
argument-hint: [context or goal]
allowed-tools: Read, Write, Bash, Task
---

# /studio:invest — New Investment

**VC Studio super command** — portfolio-level orchestration.

## Pipeline

```
DELEGATION: studio:invest → cto:* → dev:* → worker:*
OUTPUT: reports/studio/invest/
```

## Estimated: 8 credits, ~30 minutes

## Execution

Load recipe: `recipes/studio/invest.json`

Execute DAG groups in dependency order:
- If mode = "parallel": spawn multiple subagents simultaneously via Task tool
- If mode = "sequential": run commands one after another
- Wait for group completion before starting dependent groups

## Goal context

<goal>$ARGUMENTS</goal>

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
