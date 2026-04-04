---
name: dev-bug-sprint
description: "Bug sprint — debug, fix, test. Batch bug fixes in 15 min"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# /dev:bug-sprint — Bug Sprint

**IC super command** — chains 3 commands via DAG pipeline.

## Pipeline

```
SEQUENTIAL: /debug → /fix → /test --all                         (~15 min)
    |
OUTPUT: reports/dev/bug-sprint/
```

## Estimated: 8 credits, 15 minutes

## Execution

Load recipe: `recipes/dev/dev-bug-sprint.json`

Execute DAG groups in dependency order:
- If mode = "parallel": spawn multiple subagents simultaneously via Task tool
- If mode = "sequential": run commands one after another
- Wait for group completion before starting dependent groups

## Goal context

<goal>$ARGUMENTS</goal>

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
