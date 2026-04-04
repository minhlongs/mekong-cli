---
description: "SAST/DAST/SCA scanning pipeline"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /sec:scan — Security Scan

**IC super command** — SAST/DAST/SCA scanning pipeline

## Pipeline

```
PARALLEL: sast-scan + dast-scan + sca-scan
    |
SEQUENTIAL: compile-report
    |
OUTPUT: reports/sec/scan/
```

## Trigger

Runs recipe `recipes/sec/scan.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/sec:scan [goal]
```

## Estimated: 3 credits, 12 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
