---
description: "Fieldwork tracking and evidence collection"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /audit:execute — Audit Execution

**IC super command** — Fieldwork tracking and evidence collection

## Pipeline

```
SEQUENTIAL: assign-fieldwork → collect-evidence → document-findings
    |
OUTPUT: reports/audit/execute/
```

## Trigger

Runs recipe `recipes/audit/execute.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/audit:execute [goal]
```

## Estimated: 3 credits, 12 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
