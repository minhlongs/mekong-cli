---
description: "Regression test suite management"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /qa:regression — Regression Tests

**IC super command** — Regression test suite management

## Pipeline

```
SEQUENTIAL: select-suite → run-regression → diff-report
    |
OUTPUT: reports/qa/regression/
```

## Trigger

Runs recipe `recipes/qa/regression.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/qa:regression [goal]
```

## Estimated: 2 credits, 10 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
