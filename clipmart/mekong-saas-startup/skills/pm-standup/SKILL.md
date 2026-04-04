---
name: pm-standup
description: "Daily standup report. 1 credit, ~5 min."
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# /pm:standup — Daily Standup

**PM tactical command** — sprint and task management.

## Pipeline

```
DELEGATION: pm:standup → dev:* → worker:*
OUTPUT: reports/pm/standup/
```

## Estimated: 1 credits, ~5 minutes

## Execution

Load recipe: `recipes/pm/standup.json`

Execute DAG groups in dependency order:
- If mode = "parallel": spawn multiple subagents simultaneously via Task tool
- If mode = "sequential": run commands one after another
- Wait for group completion before starting dependent groups

## Goal context

<goal>$ARGUMENTS</goal>

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
