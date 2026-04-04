---
description: "Post-acquisition integration playbook"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /corpdev:integrate — Post-Acquisition

**IC super command** — Post-acquisition integration playbook

## Pipeline

```
SEQUENTIAL: day-1-plan → 30-day-milestones → 90-day-milestones → track
```

## Trigger

Runs recipe `recipes/corpdev/integrate.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/corpdev:integrate [goal]
```

## Estimated: 3 credits, 12 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
