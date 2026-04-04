---
description: "Acqui-hire and acquisition evaluation"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /corpdev:evaluate — Acquisition Eval

**IC super command** — Acqui-hire and acquisition evaluation

## Pipeline

```
PARALLEL: financial-model + team-assess + tech-assess\n    |\nSEQUENTIAL: recommendation
```

## Trigger

Runs recipe `recipes/corpdev/evaluate.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/corpdev:evaluate [goal]
```

## Estimated: 5 credits, 20 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
