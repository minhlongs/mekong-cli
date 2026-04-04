---
name: cto-team
description: "Team capacity planning and task routing. 3 credits, ~10 min."
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# /cto:team — Team Planning

**CTO strategic command** — architecture and team orchestration.

## Pipeline

```
DELEGATION: cto:team → pm:* / dev:* → worker:*
OUTPUT: reports/cto/team/
```

## Estimated: 3 credits, ~10 minutes

## Execution

Load recipe: `recipes/cto/team.json`

Execute DAG groups in dependency order:
- If mode = "parallel": spawn multiple subagents simultaneously via Task tool
- If mode = "sequential": run commands one after another
- Wait for group completion before starting dependent groups

## Goal context

<goal>$ARGUMENTS</goal>

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
