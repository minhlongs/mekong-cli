---
description: "Generate compliance evidence packages"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /sec:compliance-report — Compliance Report

**IC super command** — Generate compliance evidence packages

## Pipeline

```
PARALLEL: collect-soc2 + collect-iso27001 + collect-sox
    |
SEQUENTIAL: package-evidence
    |
OUTPUT: reports/sec/compliance-report/
```

## Trigger

Runs recipe `recipes/sec/compliance-report.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/sec:compliance-report [goal]
```

## Estimated: 5 credits, 15 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
