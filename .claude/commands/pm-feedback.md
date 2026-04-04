---
description: "User feedback collection routed to backlog"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /pm:feedback — User Feedback

**IC super command** — User feedback collection routed to backlog

## Pipeline

```
SEQUENTIAL: collect-feedback → categorize → route-to-backlog
```

## Trigger

Runs recipe `recipes/pm/feedback.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/pm:feedback [goal]
```

## Estimated: 2 credits, 8 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
