---
description: "Secrets management and rotation"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /sec:secrets — Secrets Management

**IC super command** — Secrets management and rotation

## Pipeline

```
PARALLEL: vault-check + leak-scan
    |
SEQUENTIAL: rotate-expired
    |
OUTPUT: reports/sec/secrets/
```

## Trigger

Runs recipe `recipes/sec/secrets.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/sec:secrets [goal]
```

## Estimated: 2 credits, 8 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
