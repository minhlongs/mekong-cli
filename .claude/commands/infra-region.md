---
description: "Region and edge deployment planning — latency, compliance, cost"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /infra:region — Region Planning

**IC super command** — Region and edge deployment planning — latency, compliance, cost

## Pipeline

```
SEQUENTIAL: latency-analysis → compliance-check → cost-model → recommend
```

## Trigger

Runs recipe `recipes/infra/region.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/infra:region [goal]
```

## Estimated: 3 credits, 10 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
