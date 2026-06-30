---
description: "Context window management — what to keep, compress, or drop"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /context:strategy — Context Strategy

**IC super command** — Context window management — what to keep, compress, or drop

## Pipeline

```
SEQUENTIAL: analyze-usage → classify-priority → optimize-allocation
```

## Trigger

Runs recipe `recipes/context/strategy.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/context:strategy [goal]
```

## Estimated: 2 credits, 8 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
