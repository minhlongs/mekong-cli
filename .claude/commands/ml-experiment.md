---
description: "Experiment tracking and model versioning"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /ml:experiment — ML Experiment

**IC super command** — Experiment tracking and model versioning

## Pipeline

```
SEQUENTIAL: setup-tracking → log-run → compare-models
```

## Trigger

Runs recipe `recipes/ml/experiment.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/ml:experiment [goal]
```

## Estimated: 2 credits, 8 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
