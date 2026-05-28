---
name: "source-command-business-report"
description: "Business performance report — revenue, growth, operational metrics, recommendations. 3 steps, ~20 min."
---

# source-command-business-report

Use this skill when the user asks to run the migrated source command `business-report`.

## Command Template

# /analytics:business-report — Business Performance Report

**Super command** — chains steps via DAG pipeline.

## Pipeline

```
SEQUENTIAL:
  ├── data-collection         → raw-metrics.md
  ├── analysis                → insights.md
  └── report-assembly         → business-report.md
```

## Output directory: reports/analytics/business-report/
