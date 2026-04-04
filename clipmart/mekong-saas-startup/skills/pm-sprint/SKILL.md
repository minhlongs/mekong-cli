---
name: pm-sprint
description: "Sprint planning — backlog to sprint tasks. 3 credits, ~15 min."
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# /pm:sprint — Sprint Planning

**PM tactical command** — sprint and task management.

## Pipeline

```
DELEGATION: pm:sprint → dev:* → worker:*
OUTPUT: reports/pm/sprint/
```

## Estimated: 3 credits, ~15 minutes

## Execution

Load recipe: `recipes/pm/sprint.json`

Execute DAG groups in dependency order:
- If mode = "parallel": spawn multiple subagents simultaneously via Task tool
- If mode = "sequential": run commands one after another
- Wait for group completion before starting dependent groups

## Goal context

<goal>$ARGUMENTS</goal>

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
