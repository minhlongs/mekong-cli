---
description: "Generate audit report from findings — executive summary, detailed findings, risk ratings. 2 steps, ~12 min."
argument-hint: [audit scope or prior findings file]
allowed-tools: Read, Write, Bash, Task
---

# /compliance:audit-report — Audit Report Generator

**Super command** — chains steps via DAG pipeline.

## Pipeline

```
SEQUENTIAL:
  ├── findings-analysis       → risk-matrix.md
  └── report-generation       → audit-report.md
```

## Output directory: reports/compliance/audit-report/
