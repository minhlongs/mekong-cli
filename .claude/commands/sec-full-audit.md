---
description: "Complete security audit — scan, vuln, access review, compliance report"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /sec:full-audit — Full Security Audit

**Super command** — chains multiple commands via DAG pipeline.

## Pipeline

```
PARALLEL: /sec:scan + /sec:vuln + /sec:access-review
    |
SEQUENTIAL: /sec:compliance-report
    |
OUTPUT: reports/sec/full-audit/
```

## Trigger

Runs recipe `recipes/sec/full-audit.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Spawn parallel subagents via Task tool
3. Wait for all groups to complete
4. Compile into summary report

## Usage

```
/sec:full-audit [goal]
```

## Estimated: 14 credits, 25 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
