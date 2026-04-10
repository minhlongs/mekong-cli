---
description: "Continuous compliance monitoring — drift detection, policy violations, alert rules. 2 steps, ~10 min."
argument-hint: [system or compliance domain]
allowed-tools: Read, Write, Bash, Task
---

# /compliance:compliance-monitor — Compliance Monitor

**Super command** — chains steps via DAG pipeline.

## Pipeline

```
SEQUENTIAL:
  ├── drift-detection         → drift-report.md
  └── alert-configuration     → monitor-rules.md
```

## Output directory: reports/compliance/compliance-monitor/
