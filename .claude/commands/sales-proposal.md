---
description: "Sales proposal — client needs analysis, solution design, pricing, ROI calculation. 4 steps, ~25 min."
argument-hint: [client name and opportunity]
allowed-tools: Read, Write, Bash, Task
---

# /sales:sales-proposal — Sales Proposal

**Super command** — chains steps via DAG pipeline.

## Pipeline

```
SEQUENTIAL:
  ├── needs-analysis          → client-needs.md
  ├── solution-design         → solution.md
  ├── pricing-structure       → pricing.md
  └── roi-calculation         → proposal.md
```

## Output directory: reports/sales/sales-proposal/
