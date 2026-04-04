---
name: context-compress
description: "Auto-compact and compress context to fit window"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

description: "Auto-compact and compress context to fit window"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /context:compress — Context Compress

**IC super command** — Auto-compact and compress context to fit window

## Pipeline

```
SEQUENTIAL: summarize-history → prune-stale → verify-coherence
```

## Trigger

Runs recipe `recipes/context/compress.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/context:compress [goal]
```

## Estimated: 2 credits, 5 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
