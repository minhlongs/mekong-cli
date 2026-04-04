---
description: "Daily cash position across all accounts"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /treasury:position — Cash Position

**IC super command** — Daily cash position across all accounts

## Pipeline

```
SEQUENTIAL: aggregate-accounts → reconcile → dashboard
```

## Trigger

Runs recipe `recipes/treasury/position.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/treasury:position [goal]
```

## Estimated: 2 credits, 5 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
