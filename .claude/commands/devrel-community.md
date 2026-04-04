---
description: "Discord/forum management and engagement metrics"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /devrel:community — Community Management

**IC super command** — Discord/forum management and engagement metrics

## Pipeline

```
PARALLEL: discord-stats + forum-stats\n    |\nSEQUENTIAL: engagement-report
```

## Trigger

Runs recipe `recipes/devrel/community.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/devrel:community [goal]
```

## Estimated: 2 credits, 8 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
