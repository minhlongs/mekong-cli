---
description: "Funnel analysis and feature adoption tracking"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /pm:analytics — Product Analytics

**IC super command** — Funnel analysis and feature adoption tracking

## Pipeline

```
PARALLEL: funnel-analysis + adoption-tracking\n    
```

## Trigger

Runs recipe `recipes/pm/analytics.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/pm:analytics [goal]
```

## Estimated: \nSEQUENTIAL: insights-report credits, 2 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
