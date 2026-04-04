---
name: cto-deploy
description: "Production deployment decision + execution. 5 credits, ~15 min."
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# /cto:deploy — Production Deploy

**CTO strategic command** — architecture and team orchestration.

## Pipeline

```
DELEGATION: cto:deploy → pm:* / dev:* → worker:*
OUTPUT: reports/cto/deploy/
```

## Estimated: 5 credits, ~15 minutes

## Execution

Load recipe: `recipes/cto/deploy.json`

Execute DAG groups in dependency order:
- If mode = "parallel": spawn multiple subagents simultaneously via Task tool
- If mode = "sequential": run commands one after another
- Wait for group completion before starting dependent groups

## Goal context

<goal>$ARGUMENTS</goal>

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
