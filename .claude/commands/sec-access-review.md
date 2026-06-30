---
description: "SOX quarterly access recertification"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /sec:access-review — Access Review

**IC super command** — SOX quarterly access recertification

## Pipeline

```
SEQUENTIAL: extract-access → send-review → collect-attestation → remediate
    |
OUTPUT: reports/sec/access-review/
```

## Trigger

Runs recipe `recipes/sec/access-review.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/sec:access-review [goal]
```

## Estimated: 3 credits, 10 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
