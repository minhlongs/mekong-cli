---
description: "Content calendar and event management"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /devrel:advocate — Developer Advocacy

**IC super command** — Content calendar and event management

## Pipeline

```
PARALLEL: plan-content + plan-events\n    |\nSEQUENTIAL: calendar-publish
```

## Trigger

Runs recipe `recipes/devrel/advocate.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/devrel:advocate [goal]
```

## Estimated: 2 credits, 8 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
