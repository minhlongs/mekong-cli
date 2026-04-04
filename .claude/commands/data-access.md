---
description: "Row-level security and audit logging"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /data:access — Data Access Control

**IC super command** — Row-level security and audit logging

## Pipeline

```
SEQUENTIAL: scan-policies → enforce-rls → audit-log-report
OUTPUT: reports/data/access/
```

## Trigger

Runs recipe `recipes/data/access.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/data:access [goal]
```

## Estimated: 2 credits, 8 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
