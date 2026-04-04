---
name: cto-incident
description: "Incident response orchestration. 8 credits, ~20 min."
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# /cto:incident — Incident Response

**CTO strategic command** — architecture and team orchestration.

## Pipeline

```
DELEGATION: cto:incident → pm:* / dev:* → worker:*
OUTPUT: reports/cto/incident/
```

## Estimated: 8 credits, ~20 minutes

## Execution

Load recipe: `recipes/cto/incident.json`

Execute DAG groups in dependency order:
- If mode = "parallel": spawn multiple subagents simultaneously via Task tool
- If mode = "sequential": run commands one after another
- Wait for group completion before starting dependent groups

## Goal context

<goal>$ARGUMENTS</goal>

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
