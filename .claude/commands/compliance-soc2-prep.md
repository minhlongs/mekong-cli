---
description: "SOC2 prep — audit, policy, IAM review, compliance report"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /compliance:soc2-prep — SOC2 Preparation

**Super command** — chains multiple commands via DAG pipeline.

## Pipeline

```
PARALLEL: /sec:audit + /sec:policy + /iam:review
    |
SEQUENTIAL: /sec:compliance-report
    |
OUTPUT: reports/compliance/soc2-prep/
```

## Trigger

Runs recipe `recipes/compliance/soc2-prep.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Spawn parallel subagents via Task tool
3. Wait for all groups to complete
4. Compile into summary report

## Usage

```
/compliance:soc2-prep [goal]
```

## Estimated: 13 credits, 25 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
