---
description: "Chaos engineering — fault injection and resilience testing"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /qa:chaos — Chaos Engineering

**IC super command** — Chaos engineering — fault injection and resilience testing

## Pipeline

```
SEQUENTIAL: define-experiments → inject-faults → observe-recovery → report
    |
OUTPUT: reports/qa/chaos/
```

## Trigger

Runs recipe `recipes/qa/chaos.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/qa:chaos [goal]
```

## Estimated: 3 credits, 10 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
