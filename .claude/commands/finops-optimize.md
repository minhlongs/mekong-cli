---
description: "Reserved instance management and rightsizing"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /finops:optimize — Cloud Optimize

**IC super command** — Reserved instance management and rightsizing

## Pipeline

```
PARALLEL: ri-analysis + rightsizing-scan\n    |\nSEQUENTIAL: recommendations
```

## Trigger

Runs recipe `recipes/finops/optimize.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/finops:optimize [goal]
```

## Estimated: 3 credits, 10 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
