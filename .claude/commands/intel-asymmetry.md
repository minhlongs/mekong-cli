---
description: "Exploit information asymmetry for competitive advantage"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /intel:asymmetry — Info Asymmetry

**IC super command** — Exploit information asymmetry for competitive advantage

## Pipeline

```
SEQUENTIAL: assess-advantage → identify-levers → action-plan
```

## Trigger

Runs recipe `recipes/intel/asymmetry.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/intel:asymmetry [goal]
```

## Estimated: 3 credits, 10 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
