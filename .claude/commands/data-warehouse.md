---
description: "Warehouse administration and cost monitoring"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /data:warehouse — Warehouse Admin

**IC super command** — Warehouse administration and cost monitoring

## Pipeline

```
SEQUENTIAL: usage-stats → cost-analysis → optimization-recs
OUTPUT: reports/data/warehouse/
```

## Trigger

Runs recipe `recipes/data/warehouse.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/data:warehouse [goal]
```

## Estimated: 2 credits, 8 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
