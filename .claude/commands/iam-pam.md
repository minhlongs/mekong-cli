---
description: "Privileged access management with JIT elevation"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /iam:pam — Privileged Access

**IC super command** — Privileged access management with JIT elevation

## Pipeline

```
SEQUENTIAL: scan-privileged → enforce-jit → audit-log
    |
OUTPUT: reports/iam/pam/
```

## Trigger

Runs recipe `recipes/iam/pam.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/iam:pam [goal]
```

## Estimated: 2 credits, 8 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
