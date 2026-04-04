---
description: "Board prep — meeting management, metrics, risk report in parallel, then minutes"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /ipo:board-prep — IPO Board Prep

**Super command** — chains multiple commands via DAG pipeline.

## Pipeline

```
PARALLEL: /board:manage + /ir:metrics + /risk:report
    |
SEQUENTIAL: /board:minutes
    |
OUTPUT: reports/ipo/board-prep/
```

## Trigger

Runs recipe `recipes/ipo/board-prep.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Spawn parallel subagents via Task tool
3. Wait for all groups to complete
4. Compile into summary report

## Usage

```
/ipo:board-prep [goal]
```

## Estimated: 11 credits, 30 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
