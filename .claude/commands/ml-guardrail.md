---
description: "Content safety, output validation, fallback mechanisms"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /ml:guardrail — AI Guardrails

**IC super command** — Content safety, output validation, fallback mechanisms

## Pipeline

```
SEQUENTIAL: define-rules → test-guardrails → deploy-filters
```

## Trigger

Runs recipe `recipes/ml/guardrail.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/ml:guardrail [goal]
```

## Estimated: 2 credits, 8 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
