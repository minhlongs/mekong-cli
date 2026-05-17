---
description: "SEO analysis — keyword research, competitor analysis, on-page audit, content gaps. 3 steps, ~20 min."
argument-hint: [domain or target keywords]
allowed-tools: Read, Write, Bash, Task
why-override: "Mekong's recipe is the actionable 3-step audit; the global /marketing-seo at ~/.claude/commands is a Binh-Phap-style strategy doc. Both serve different intents."
---

# /marketing:marketing-seo — SEO Analysis

**Super command** — chains steps via DAG pipeline.

## Pipeline

```
SEQUENTIAL:
  ├── keyword-research        → keywords.md
  ├── competitor-audit        → competitor-analysis.md
  └── content-gaps            → seo-action-plan.md
```

## Output directory: reports/marketing/marketing-seo/
