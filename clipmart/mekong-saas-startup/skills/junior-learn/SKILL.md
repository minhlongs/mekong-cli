---
name: junior-learn
description: "Junior learn — architecture overview, module deep dive, key patterns in 10 min"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# /junior:learn — Learn Codebase

**IC super command** — chains 2 commands via DAG pipeline.

## Pipeline

```
SEQUENTIAL: /arch --explain → /docs                             (~10 min)
    |
OUTPUT: reports/junior/learn/
```

## Estimated: 3 credits, 10 minutes

## Execution

Load recipe: `recipes/junior/junior-learn.json`

Execute DAG groups in dependency order:
- If mode = "parallel": spawn multiple subagents simultaneously via Task tool
- If mode = "sequential": run commands one after another
- Wait for group completion before starting dependent groups

## Goal context

<goal>$ARGUMENTS</goal>

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
