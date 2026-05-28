---
name: "source-command-sales-forecast"
description: "Sales forecast — pipeline analysis, conversion rates, revenue projection, risk factors. 3 steps, ~15 min."
---

# source-command-sales-forecast

Use this skill when the user asks to run the migrated source command `sales-forecast`.

## Command Template

# /sales:sales-forecast — Sales Forecast

**Super command** — chains steps via DAG pipeline.

## Pipeline

```
SEQUENTIAL:
  ├── pipeline-analysis       → pipeline-health.md
  ├── conversion-rates        → conversion.md
  └── revenue-projection      → forecast.md
```

## Output directory: reports/sales/sales-forecast/
