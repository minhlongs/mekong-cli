---
description: "Carbon footprint tracking for Scope 1-3"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /esg:carbon — Carbon Tracking

**IC super command** — Carbon footprint tracking for Scope 1-3

## Pipeline

```
SEQUENTIAL: measure-scope1 → measure-scope2 → estimate-scope3 → offset-plan
```

## Trigger

Runs recipe `recipes/esg/carbon.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/esg:carbon [goal]
```

## Estimated: 3 credits, 10 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
