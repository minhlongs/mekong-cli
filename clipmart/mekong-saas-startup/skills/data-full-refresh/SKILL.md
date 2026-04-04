---
name: data-full-refresh
description: "Full refresh — ingest, transform, quality, catalog in parallel, then metrics"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

description: "Full refresh — ingest, transform, quality, catalog in parallel, then metrics"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /data:full-refresh — Full Data Refresh

**Super command** — chains multiple commands via DAG pipeline.

## Pipeline

```
PARALLEL: /data:ingest + /data:transform + /data:quality + /data:catalog
    |
SEQUENTIAL: /data:metric
    |
OUTPUT: reports/data/full-refresh/
```

## Trigger

Runs recipe `recipes/data/full-refresh.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Spawn parallel subagents via Task tool
3. Wait for all groups to complete
4. Compile into summary report

## Usage

```
/data:full-refresh [goal]
```

## Estimated: 13 credits, 30 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
