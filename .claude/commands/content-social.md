---
description: "Social media content — platform-specific posts, hashtags, scheduling. 3 steps, ~15 min."
argument-hint: [topic or campaign]
allowed-tools: Read, Write, Bash, Task
---

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
