---
description: "Prioritize what stays in context window under pressure"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /context:priority — Context Priority

**IC super command** — Prioritize what stays in context window under pressure

## Pipeline

```
SEQUENTIAL: rank-messages → score-relevance → evict-lowest
```

## Trigger

Runs recipe `recipes/context/priority.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/context:priority [goal]
```

## Estimated: 2 credits, 5 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
