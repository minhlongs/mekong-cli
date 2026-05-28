---
name: "source-command-content-social"
description: "Social media content — platform-specific posts, hashtags, scheduling. 3 steps, ~15 min."
---

# source-command-content-social

Use this skill when the user asks to run the migrated source command `content-social`.

## Command Template

# /content:content-social — Social Media Content

**Super command** — chains steps via DAG pipeline.

## Pipeline

```
PARALLEL:
  ├── twitter-posts           → twitter.md
  ├── linkedin-posts          → linkedin.md
  └── scheduling              → content-calendar.md
```

## Output directory: reports/content/content-social/
