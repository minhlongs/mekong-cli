---
description: "Logistics, investor targeting, and presentation versioning"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /ir:roadshow — IR Roadshow

**IC super command** — Logistics, investor targeting, and presentation versioning

## Pipeline

```
SEQUENTIAL: target-investors → schedule-meetings → version-deck
OUTPUT: reports/governance/ir-roadshow/
```

## Trigger

Runs recipe `recipes/ir/roadshow.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/ir:roadshow [goal]
```

## Estimated: 3 credits, 10 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
