---
description: "Earnings calendar, quiet periods, Reg FD windows"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /ir:calendar — IR Calendar

**IC super command** — Earnings calendar, quiet periods, Reg FD windows

## Pipeline

```
SEQUENTIAL: set-dates → enforce-quiet-periods → notify-stakeholders
OUTPUT: reports/governance/ir-calendar/
```

## Trigger

Runs recipe `recipes/ir/calendar.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/ir:calendar [goal]
```

## Estimated: 2 credits, 5 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
