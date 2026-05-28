---
name: "source-command-venture-due-diligence"
description: "Due diligence report — market analysis, team assessment, financial review, risk factors. 4 steps, ~30 min."
---

# source-command-venture-due-diligence

Use this skill when the user asks to run the migrated source command `venture-due-diligence`.

## Command Template

# /venture:venture-due-diligence — Venture Due Diligence

**Super command** — chains steps via DAG pipeline.

## Pipeline

```
SEQUENTIAL:
  ├── market-analysis         → market.md
  ├── team-assessment         → team.md
  ├── financial-review        → financials.md
  └── risk-analysis           → due-diligence.md
```

## Output directory: reports/venture/venture-due-diligence/
