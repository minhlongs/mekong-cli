---
name: data-metric
description: "Semantic layer for consistent KPI definitions"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

description: "Semantic layer for consistent KPI definitions"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /data:metric — Semantic Layer

**IC super command** — Semantic layer for consistent KPI definitions

## Pipeline

```
SEQUENTIAL: define-metrics → validate-calculations → publish-layer
OUTPUT: reports/data/metric/
```

## Trigger

Runs recipe `recipes/data/metric.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/data:metric [goal]
```

## Estimated: 2 credits, 8 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
