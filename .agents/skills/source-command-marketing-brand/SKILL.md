---
name: "source-command-marketing-brand"
description: "Brand strategy — positioning, voice, visual identity guidelines, messaging framework. 4 steps, ~30 min."
---

# source-command-marketing-brand

Use this skill when the user asks to run the migrated source command `marketing-brand`.

## Command Template

# /marketing:marketing-brand — Brand Strategy

**Super command** — chains steps via DAG pipeline.

## Pipeline

```
SEQUENTIAL:
  ├── brand-positioning       → positioning.md
  ├── voice-guidelines        → voice.md
  ├── visual-identity         → visual-guide.md
  └── messaging-framework     → messaging.md
```

## Output directory: reports/marketing/marketing-brand/
