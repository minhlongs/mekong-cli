---
description: "Growth metrics dashboard — acquisition, activation, retention, revenue, referral. 2 steps, ~12 min."
argument-hint: [product or time period]
allowed-tools: Read, Write, Bash, Task
---

# /growth:growth-metrics — Growth Metrics

**Super command** — chains steps via DAG pipeline.

## Pipeline

```
SEQUENTIAL:
  ├── metrics-collection      → raw-metrics.md
  └── dashboard-assembly      → growth-dashboard.md
```

## Output directory: reports/growth/growth-metrics/
