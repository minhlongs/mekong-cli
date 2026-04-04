---
description: "S-1 narrative development — investment thesis and MD&A"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /ir:narrative — S-1 Narrative

**IC super command** — S-1 narrative development — investment thesis and MD&A

## Pipeline

```
SEQUENTIAL: draft-thesis → write-mda → legal-review
OUTPUT: reports/governance/ir-narrative/
```

## Trigger

Runs recipe `recipes/ir/narrative.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/ir:narrative [goal]
```

## Estimated: 5 credits, 20 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
