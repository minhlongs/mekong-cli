---
description: "Sales forecast — pipeline analysis, conversion rates, revenue projection, risk factors. 3 steps, ~15 min."
argument-hint: [quarter or time period]
allowed-tools: Read, Write, Bash, Task
---

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
