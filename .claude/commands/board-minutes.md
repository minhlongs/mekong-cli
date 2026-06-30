---
description: "Meeting minutes and action item tracking"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /board:minutes — Board Minutes

**IC super command** — Meeting minutes and action item tracking

## Pipeline

```
SEQUENTIAL: draft-minutes → track-action-items → distribute
OUTPUT: reports/governance/board-minutes/
```

## Trigger

Runs recipe `recipes/board/minutes.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/board:minutes [goal]
```

## Estimated: 2 credits, 8 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
