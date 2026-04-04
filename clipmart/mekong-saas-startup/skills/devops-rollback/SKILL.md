---
name: devops-rollback
description: "Emergency rollback → smoke test → health check → incident report"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# /devops:rollback — Emergency Rollback

**Super command** — chains 3 commands via DAG pipeline.

## Pipeline

```
[rollback $ARGUMENTS]
          │
          ▼
  [smoke] ══╗
  [health] ══╝ (parallel)
```

## Estimated: 5 credits, 10 minutes

## Execution

Load recipe: `recipes/devops/rollback.json`

Execute DAG groups in dependency order:
- If mode = "parallel": spawn multiple subagents simultaneously via Task tool
- If mode = "sequential": run commands one after another
- Wait for group completion before starting dependent groups

## Goal context

<goal>$ARGUMENTS</goal>

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
