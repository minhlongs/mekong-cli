---
description: "Network effect analysis — density, clustering, value curves"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /momentum:network — Network Effects

**IC super command** — Network effect analysis — density, clustering, value curves

## Pipeline

```
SEQUENTIAL: graph-analysis → value-curve → defensibility-score
```

## Trigger

Runs recipe `recipes/momentum/network.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/momentum:network [goal]
```

## Estimated: 3 credits, 10 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
