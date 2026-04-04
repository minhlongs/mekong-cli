---
description: "Freshness, volume, and schema monitoring"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /data:quality — Data Quality

**IC super command** — Freshness, volume, and schema monitoring

## Pipeline

```
PARALLEL: freshness-check + volume-check + schema-check
    |
SEQUENTIAL: alert-report
OUTPUT: reports/data/quality/
```

## Trigger

Runs recipe `recipes/data/quality.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/data:quality [goal]
```

## Estimated: 2 credits, 8 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
