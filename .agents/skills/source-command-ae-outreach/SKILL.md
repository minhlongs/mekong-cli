---
name: "source-command-ae-outreach"
description: "Sales outreach sequences — prospect research, email drafts, follow-up cadence. 3 steps, ~15 min."
---

# source-command-ae-outreach

Use this skill when the user asks to run the migrated source command `ae-outreach`.

## Command Template

# /sales:ae-outreach — Sales Outreach Sequences

**Super command** — chains steps via DAG pipeline.

## Pipeline

```
SEQUENTIAL:
  ├── prospect-research       → prospect-profile.md
  ├── outreach-draft          → email-sequences.md
  └── follow-up-cadence       → cadence-schedule.md
```

## Output directory: reports/sales/ae-outreach/
