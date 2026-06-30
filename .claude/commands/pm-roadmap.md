---
description: "Roadmap visibility and prioritization with RICE/ICE scoring"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /pm:roadmap — Roadmap Planning

**IC super command** — Roadmap visibility and prioritization with RICE/ICE scoring

## Pipeline

```
SEQUENTIAL: gather-inputs → score-rice → prioritize → publish-roadmap
```

## Trigger

Runs recipe `recipes/pm/roadmap.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/pm:roadmap [goal]
```

## Estimated: 3 credits, 10 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
