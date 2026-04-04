---
name: pm-backlog
description: "User story management and sprint grooming"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# /pm:backlog — Backlog Management

**IC super command** — User story management and sprint grooming

## Pipeline

```
SEQUENTIAL: triage-stories → estimate → groom → assign-sprint
```

## Trigger

Runs recipe `recipes/pm/backlog.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/pm:backlog [goal]
```

## Estimated: 2 credits, 8 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
