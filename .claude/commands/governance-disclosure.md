---
description: "SEC disclosure requirements tracking"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /governance:disclosure — SEC Disclosure

**IC super command** — SEC disclosure requirements tracking

## Pipeline

```
SEQUENTIAL: identify-requirements → track-deadlines → prepare-filings
OUTPUT: reports/governance/disclosure/
```

## Trigger

Runs recipe `recipes/governance/disclosure.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/governance:disclosure [goal]
```

## Estimated: 3 credits, 10 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
