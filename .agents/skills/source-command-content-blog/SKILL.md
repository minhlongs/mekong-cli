---
name: "source-command-content-blog"
description: "Blog post creation — research, outline, draft, SEO optimization. 4 steps, ~25 min."
---

# source-command-content-blog

Use this skill when the user asks to run the migrated source command `content-blog`.

## Command Template

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
