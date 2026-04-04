---
description: "Changelog generation and stakeholder communication"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /pm:release-note — Release Notes

**IC super command** — Changelog generation and stakeholder communication

## Pipeline

```
SEQUENTIAL: generate-changelog → format-notes → distribute
```

## Trigger

Runs recipe `recipes/pm/release-note.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/pm:release-note [goal]
```

## Estimated: 2 credits, 5 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
