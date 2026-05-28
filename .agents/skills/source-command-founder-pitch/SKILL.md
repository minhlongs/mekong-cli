---
name: "source-command-founder-pitch"
description: "Pitch deck creation — problem, solution, market, traction, financials, ask. 6 steps, ~35 min."
---

# source-command-founder-pitch

Use this skill when the user asks to run the migrated source command `founder-pitch`.

## Command Template

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
