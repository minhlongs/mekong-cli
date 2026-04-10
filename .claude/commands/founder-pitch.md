---
description: "Pitch deck creation — problem, solution, market, traction, financials, ask. 6 steps, ~35 min."
argument-hint: [company name and stage]
allowed-tools: Read, Write, Bash, Task
---

# /venture:founder-pitch — Founder Pitch Deck

**Super command** — chains steps via DAG pipeline.

## Pipeline

```
SEQUENTIAL:
  ├── problem-statement       → problem.md
  ├── solution-design         → solution.md
  ├── market-sizing           → market.md
  ├── traction-metrics        → traction.md
  ├── financial-model         → financials.md
  └── ask-structure           → pitch-deck.md
```

## Output directory: reports/venture/founder-pitch/
