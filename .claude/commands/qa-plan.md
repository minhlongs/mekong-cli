---
description: "Test plan generation from requirements"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /qa:plan — Test Plan

**IC super command** — Test plan generation from requirements

## Pipeline

```
SEQUENTIAL: analyze-requirements → generate-test-cases → review-plan
    |
OUTPUT: reports/qa/plan/
```

## Trigger

Runs recipe `recipes/qa/plan.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/qa:plan [goal]
```

## Estimated: 2 credits, 8 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
