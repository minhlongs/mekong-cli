---
description: "Daily pipeline — ingest, transform, quality check"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /data:daily-pipeline — Daily Data Pipeline

**Super command** — chains multiple commands via DAG pipeline.

## Pipeline

```
SEQUENTIAL: /data:ingest → /data:transform → /data:quality
    |
OUTPUT: reports/data/daily-pipeline/
```

## Trigger

Runs recipe `recipes/data/daily-pipeline.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Spawn parallel subagents via Task tool
3. Wait for all groups to complete
4. Compile into summary report

## Usage

```
/data:daily-pipeline [goal]
```

## Estimated: 8 credits, 15 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
