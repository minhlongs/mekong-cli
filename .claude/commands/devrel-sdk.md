---
description: "SDK publishing and compatibility matrix"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /devrel:sdk — SDK Publishing

**IC super command** — SDK publishing and compatibility matrix

## Pipeline

```
SEQUENTIAL: build-sdks → test-compat → publish
```

## Trigger

Runs recipe `recipes/devrel/sdk.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/devrel:sdk [goal]
```

## Estimated: 3 credits, 10 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
