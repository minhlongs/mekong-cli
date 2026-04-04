---
description: "Competitive intelligence tracking"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /pm:competitor — Competitive Intel

**IC super command** — Competitive intelligence tracking

## Pipeline

```
SEQUENTIAL: scan-competitors → analyze-features → gap-report
```

## Trigger

Runs recipe `recipes/pm/competitor.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/pm:competitor [goal]
```

## Estimated: 2 credits, 8 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
