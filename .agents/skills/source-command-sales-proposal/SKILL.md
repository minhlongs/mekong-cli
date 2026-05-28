---
name: "source-command-sales-proposal"
description: "Sales proposal — client needs analysis, solution design, pricing, ROI calculation. 4 steps, ~25 min."
---

# source-command-sales-proposal

Use this skill when the user asks to run the migrated source command `sales-proposal`.

## Command Template

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
