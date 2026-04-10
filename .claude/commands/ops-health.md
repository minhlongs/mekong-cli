---
description: "Operations health check — system status, capacity planning, bottleneck analysis. 3 steps, ~15 min."
argument-hint: [system or service name]
allowed-tools: Read, Write, Bash, Task
---

# /ops:ops-health — Operations Health Check

**Super command** — chains steps via DAG pipeline.

## Pipeline

```
SEQUENTIAL:
  ├── status-check            → system-status.md
  ├── capacity-analysis       → capacity.md
  └── bottleneck-report       → health-report.md
```

## Output directory: reports/ops/ops-health/
