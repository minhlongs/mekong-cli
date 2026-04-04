---
name: devrel-community
description: "Discord/forum management and engagement metrics"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# /devrel:community — Community Management

**IC super command** — Discord/forum management and engagement metrics

## Pipeline

```
PARALLEL: discord-stats + forum-stats\n    |\nSEQUENTIAL: engagement-report
```

## Trigger

Runs recipe `recipes/devrel/community.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/devrel:community [goal]
```

## Estimated: 2 credits, 8 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
