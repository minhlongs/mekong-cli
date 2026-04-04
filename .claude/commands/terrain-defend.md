---
description: "Maintain and strengthen defensive market position"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /terrain:defend — Defensive Position

**IC super command** — Maintain and strengthen defensive market position

## Pipeline

```
SEQUENTIAL: audit-moat → identify-threats → reinforce-defenses
```

## Trigger

Runs recipe `recipes/terrain/defend.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/terrain:defend [goal]
```

## Estimated: 3 credits, 10 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
