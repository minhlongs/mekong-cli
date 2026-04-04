---
description: "Centralized repository and SLA tracking"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /vendor:contract — Vendor Contracts

**IC super command** — Centralized repository and SLA tracking

## Pipeline

```
SEQUENTIAL: import-contract → extract-terms → track-slas
```

## Trigger

Runs recipe `recipes/vendor/contract.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/vendor:contract [goal]
```

## Estimated: 2 credits, 8 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
