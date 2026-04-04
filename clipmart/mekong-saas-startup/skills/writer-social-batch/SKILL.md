---
name: writer-social-batch
description: "Social batch — 7-day posts + posting schedule in parallel. 2 commands, ~10 min."
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# /writer:social-batch — Social Batch

**IC super command** — chains 2 commands via DAG pipeline.

## Pipeline

```
PARALLEL: /social --batch 7 + /schedule --social
    |
OUTPUT: reports/writer/social/
        7-day-posts.md
        posting-schedule.md
        SOCIAL-BATCH-SUMMARY.md
```

## Trigger

Runs recipe `recipes/writer/writer-social-batch.json` through DAGScheduler.

## Execution

1. Read recipe DAG definition
2. Spawn both subagents simultaneously via Task tool (mode: parallel)
3. Wait for both to complete
4. Compile into SOCIAL-BATCH-SUMMARY.md as content calendar with copy and optimal send times

## Usage

```
/writer:social-batch [brand-or-content-theme]
```

## Estimated: 5 credits, 10 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
