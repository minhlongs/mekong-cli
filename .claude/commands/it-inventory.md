---
description: "SaaS discovery, license tracking, shadow IT detection"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /it:inventory — IT Inventory

**IC super command** — SaaS discovery, license tracking, shadow IT detection

## Pipeline

```
PARALLEL: scan-saas + scan-endpoints
    |
SEQUENTIAL: reconcile-licenses
    |
OUTPUT: reports/it/inventory/
```

## Trigger

Runs recipe `recipes/it/inventory.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/it:inventory [goal]
```

## Estimated: 2 credits, 8 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
