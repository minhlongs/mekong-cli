---
description: "M&A target identification"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /corpdev:scout — M&A Scout

**IC super command** — M&A target identification

## Pipeline

```
SEQUENTIAL: define-criteria → scan-market → shortlist
```

## Trigger

Runs recipe `recipes/corpdev/scout.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/corpdev:scout [goal]
```

## Estimated: 3 credits, 10 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
