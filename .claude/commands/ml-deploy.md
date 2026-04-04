---
description: "Model deployment with A/B serving and canary rollouts"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /ml:deploy — Model Deploy

**IC super command** — Model deployment with A/B serving and canary rollouts

## Pipeline

```
SEQUENTIAL: package-model → deploy-canary → monitor-metrics → promote
```

## Trigger

Runs recipe `recipes/ml/deploy.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/ml:deploy [goal]
```

## Estimated: 3 credits, 12 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
