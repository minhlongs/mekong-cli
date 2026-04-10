---
description: "Blog post creation — research, outline, draft, SEO optimization. 4 steps, ~25 min."
argument-hint: [topic or keyword]
allowed-tools: Read, Write, Bash, Task
---

# /content:content-blog — Blog Post Creator

**Super command** — chains steps via DAG pipeline.

## Pipeline

```
SEQUENTIAL:
  ├── topic-research          → research.md
  ├── outline                 → outline.md
  ├── draft                   → blog-post.md
  └── seo-optimize            → final-post.md
```

## Output directory: reports/content/content-blog/
