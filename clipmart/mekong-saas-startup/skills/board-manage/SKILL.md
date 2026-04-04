---
name: board-manage
description: "Meeting scheduling, agenda, and materials preparation"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

description: "Meeting scheduling, agenda, and materials preparation"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /board:manage — Board Management

**IC super command** — Meeting scheduling, agenda, and materials preparation

## Pipeline

```
SEQUENTIAL: schedule-meeting → prepare-agenda → distribute-materials
OUTPUT: reports/governance/board-manage/
```

## Trigger

Runs recipe `recipes/board/manage.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/board:manage [goal]
```

## Estimated: 3 credits, 10 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
