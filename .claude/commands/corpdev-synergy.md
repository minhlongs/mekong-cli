---
description: "Synergy tracking and integration milestones"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /corpdev:synergy — Synergy Tracking

**IC super command** — Synergy tracking and integration milestones

## Pipeline

```
SEQUENTIAL: identify-synergies → track-realization → report
```

## Trigger

Runs recipe `recipes/corpdev/synergy.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/corpdev:synergy [goal]
```

## Estimated: 2 credits, 8 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
