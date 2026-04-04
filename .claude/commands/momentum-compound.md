---
description: "Compound growth calculator — retention curves, expansion revenue"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /momentum:compound — Compound Growth

**IC super command** — Compound growth calculator — retention curves, expansion revenue

## Pipeline

```
PARALLEL: retention-curve + expansion-analysis\nSEQUENTIAL: compound-model
```

## Trigger

Runs recipe `recipes/momentum/compound.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/momentum:compound [goal]
```

## Estimated: 2 credits, 8 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
