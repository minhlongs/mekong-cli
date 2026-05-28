---
name: "source-command-marketing-seo"
description: "SEO analysis — keyword research, competitor analysis, on-page audit, content gaps. 3 steps, ~20 min."
---

# source-command-marketing-seo

Use this skill when the user asks to run the migrated source command `marketing-seo`.

## Command Template

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
