---
description: "Quarterly access recertification with evidence"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /iam:review — Access Recertification

**IC super command** — Quarterly access recertification with evidence

## Pipeline

```
PARALLEL: extract-entitlements + collect-managers
    |
SEQUENTIAL: certify → remediate-exceptions
    |
OUTPUT: reports/iam/review/
```

## Trigger

Runs recipe `recipes/iam/review.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/iam:review [goal]
```

## Estimated: 3 credits, 10 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
