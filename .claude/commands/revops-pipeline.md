---
description: "Unified pipeline visibility across sales stages"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /revops:pipeline — Pipeline Visibility

**IC super command** — Unified pipeline visibility across sales stages

## Pipeline

```
SEQUENTIAL: aggregate-stages → clean-data → dashboard
```

## Trigger

Runs recipe `recipes/revops/pipeline.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/revops:pipeline [goal]
```

## Estimated: 2 credits, 8 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
