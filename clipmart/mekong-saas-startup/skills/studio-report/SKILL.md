---
name: studio-report
description: "Generate investor report (weekly/monthly). 5 credits, ~20 min."
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# /studio:report — Investor Report

**VC Studio super command** — portfolio-level orchestration.

## Pipeline

```
DELEGATION: studio:report → cto:* → dev:* → worker:*
OUTPUT: reports/studio/report/
```

## Estimated: 5 credits, ~20 minutes

## Execution

Load recipe: `recipes/studio/report.json`

Execute DAG groups in dependency order:
- If mode = "parallel": spawn multiple subagents simultaneously via Task tool
- If mode = "sequential": run commands one after another
- Wait for group completion before starting dependent groups

## Goal context

<goal>$ARGUMENTS</goal>

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
