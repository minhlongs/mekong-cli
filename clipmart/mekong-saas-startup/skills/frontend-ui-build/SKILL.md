---
name: frontend-ui-build
description: "Frontend UI build — component, styling, responsive, test in 12 min"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# /frontend:ui-build — UI Build

**IC super command** — chains 3 commands via DAG pipeline.

## Pipeline

```
SEQUENTIAL: /component → /cook --frontend → /e2e-test           (~12 min)
    |
OUTPUT: reports/frontend/ui-build/
```

## Estimated: 8 credits, 12 minutes

## Execution

Load recipe: `recipes/frontend/frontend-ui-build.json`

Execute DAG groups in dependency order:
- If mode = "parallel": spawn multiple subagents simultaneously via Task tool
- If mode = "sequential": run commands one after another
- Wait for group completion before starting dependent groups

## Goal context

<goal>$ARGUMENTS</goal>

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
