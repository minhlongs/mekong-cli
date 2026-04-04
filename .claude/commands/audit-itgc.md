---
description: "IT General Controls testing"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /audit:itgc — ITGC Testing

**IC super command** — IT General Controls testing

## Pipeline

```
PARALLEL: access-controls + change-mgmt + operations
    |
SEQUENTIAL: findings-report
    |
OUTPUT: reports/audit/itgc/
```

## Trigger

Runs recipe `recipes/audit/itgc.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/audit:itgc [goal]
```

## Estimated: 3 credits, 12 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
