---
name: terrain-entry
description: "Market entry strategy per terrain classification"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

description: "Market entry strategy per terrain classification"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /terrain:entry — Market Entry

**IC super command** — Market entry strategy per terrain classification

## Pipeline

```
SEQUENTIAL: assess-terrain → choose-entry-mode → execution-plan
```

## Trigger

Runs recipe `recipes/terrain/entry.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/terrain:entry [goal]
```

## Estimated: 3 credits, 10 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
