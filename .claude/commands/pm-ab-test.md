---
description: "Experiment design, statistical analysis, auto-rollback"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /pm:ab-test — A/B Testing

**IC super command** — Experiment design, statistical analysis, auto-rollback

## Pipeline

```
SEQUENTIAL: design-experiment → launch → analyze-stats → decide-rollback
```

## Trigger

Runs recipe `recipes/pm/ab-test.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/pm:ab-test [goal]
```

## Estimated: 3 credits, 10 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
