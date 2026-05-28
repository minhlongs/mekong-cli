---
name: "source-command-marketing-campaign"
description: "Campaign planning — audience, channels, content, budget, timeline, KPIs. 4 steps, ~25 min."
---

# source-command-marketing-campaign

Use this skill when the user asks to run the migrated source command `marketing-campaign`.

## Command Template

# /marketing:marketing-campaign — Marketing Campaign

**Super command** — chains steps via DAG pipeline.

## Pipeline

```
SEQUENTIAL:
  ├── audience-research       → personas.md
  ├── channel-strategy        → channels.md
  ├── content-plan            → content-calendar.md
  └── budget-kpis             → campaign-plan.md
```

## Output directory: reports/marketing/marketing-campaign/
