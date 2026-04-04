---
name: pm-competitor
description: "Competitive intelligence tracking"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# /pm:competitor — Competitive Intel

**IC super command** — Competitive intelligence tracking

## Pipeline

```
SEQUENTIAL: scan-competitors → analyze-features → gap-report
```

## Trigger

Runs recipe `recipes/pm/competitor.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/pm:competitor [goal]
```

## Estimated: 2 credits, 8 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
