---
description: "International entity setup and tax structuring"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /intl:entity — International Entity

**IC super command** — International entity setup and tax structuring

## Pipeline

```
SEQUENTIAL: select-structure → register-entity → setup-banking → tax-plan
```

## Trigger

Runs recipe `recipes/intl/entity.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/intl:entity [goal]
```

## Estimated: 3 credits, 12 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
