---
description: "Risk tiering and SOC 2 verification"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /vendor:assess — Vendor Assessment

**IC super command** — Risk tiering and SOC 2 verification

## Pipeline

```
SEQUENTIAL: collect-questionnaire → risk-tier → verify-soc2
```

## Trigger

Runs recipe `recipes/vendor/assess.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/vendor:assess [goal]
```

## Estimated: 3 credits, 10 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
