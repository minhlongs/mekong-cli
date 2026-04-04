---
name: pm-delegate
description: "Break task and delegate to dev level. 3 credits, ~10 min."
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# /pm:delegate — Task Delegation

**PM tactical command** — sprint and task management.

## Pipeline

```
DELEGATION: pm:delegate → dev:* → worker:*
OUTPUT: reports/pm/delegate/
```

## Estimated: 3 credits, ~10 minutes

## Execution

Load recipe: `recipes/pm/delegate.json`

Execute DAG groups in dependency order:
- If mode = "parallel": spawn multiple subagents simultaneously via Task tool
- If mode = "sequential": run commands one after another
- Wait for group completion before starting dependent groups

## Goal context

<goal>$ARGUMENTS</goal>

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
