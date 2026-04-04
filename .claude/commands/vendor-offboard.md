---
description: "Vendor decommissioning and data deletion"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /vendor:offboard — Vendor Offboard

**IC super command** — Vendor decommissioning and data deletion

## Pipeline

```
SEQUENTIAL: revoke-access → delete-data → generate-evidence
```

## Trigger

Runs recipe `recipes/vendor/offboard.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/vendor:offboard [goal]
```

## Estimated: 2 credits, 5 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
