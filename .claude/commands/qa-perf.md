---
description: "Performance and load testing with k6"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /qa:perf — Performance Testing

**IC super command** — Performance and load testing with k6

## Pipeline

```
PARALLEL: configure-k6 + warm-up
    |
SEQUENTIAL: execute-load-test → analyze-results
    |
OUTPUT: reports/qa/perf/
```

## Trigger

Runs recipe `recipes/qa/perf.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/qa:perf [goal]
```

## Estimated: 3 credits, 12 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
