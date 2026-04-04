---
name: studio-portfolio
description: "Portfolio dashboard — P&L, MRR, runway. 5 credits, ~15 min."
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# /studio:portfolio — Portfolio Dashboard

**VC Studio super command** — portfolio-level orchestration.

## Pipeline

```
DELEGATION: studio:portfolio → cto:* → dev:* → worker:*
OUTPUT: reports/studio/portfolio/
```

## Estimated: 5 credits, ~15 minutes

## Execution

Load recipe: `recipes/studio/portfolio.json`

Execute DAG groups in dependency order:
- If mode = "parallel": spawn multiple subagents simultaneously via Task tool
- If mode = "sequential": run commands one after another
- Wait for group completion before starting dependent groups

## Goal context

<goal>$ARGUMENTS</goal>

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
