---
name: sre-incident
description: "SRE incident — triage, mitigate, verify, report in 10 min"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# /sre:incident — Incident Response

**IC super command** — chains 3 commands via DAG pipeline.

## Pipeline

```
SEQUENTIAL: /debug → /fix --hotfix → /smoke                     (~10 min)
    |
OUTPUT: reports/sre/incident/
```

## Estimated: 5 credits, 10 minutes

## Execution

Load recipe: `recipes/sre/sre-incident.json`

Execute DAG groups in dependency order:
- If mode = "parallel": spawn multiple subagents simultaneously via Task tool
- If mode = "sequential": run commands one after another
- Wait for group completion before starting dependent groups

## Goal context

<goal>$ARGUMENTS</goal>

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
