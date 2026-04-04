---
description: "End-to-end test execution with Playwright"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /qa:e2e — E2E Tests

**IC super command** — End-to-end test execution with Playwright

## Pipeline

```
SEQUENTIAL: run-playwright → collect-results → report
    |
OUTPUT: reports/qa/e2e/
```

## Trigger

Runs recipe `recipes/qa/e2e.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/qa:e2e [goal]
```

## Estimated: 3 credits, 12 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
