---
description: "Design and measure viral loops — K-factor, cycle time"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /momentum:viral-loop — Viral Loop Design

**IC super command** — Design and measure viral loops — K-factor, cycle time

## Pipeline

```
SEQUENTIAL: map-loop → measure-k-factor → optimize
```

## Trigger

Runs recipe `recipes/momentum/viral-loop.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/momentum:viral-loop [goal]
```

## Estimated: 3 credits, 10 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
