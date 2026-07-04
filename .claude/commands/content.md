---
description: "Content marketing — generate posts, manage calendar, track channels"
argument-hint: "[generate|calendar|channels] [args]"
---

# /content — Content Marketing

## Usage
```
/content generate --pillar one-person-company --format blog
/content generate --pillar ai-agents --format twitter
/content calendar               # Show content calendar
/content channels               # Show channel stats
```

## Content Pillars
| Pillar | Frequency | Channels |
|--------|-----------|----------|
| One-Person Company | Weekly | Blog, IH, Twitter |
| AI Agents in Practice | Weekly | Blog, Twitter, YouTube |
| Solo Founder Life | Biweekly | Twitter, IH |
| Binh Phap for Business | Monthly | Blog, Twitter |
| ZenOS Philosophy | Monthly | Blog, IH |

## Implementation
Generate: `node scripts/content-gen.cjs --pillar <name> --format <format>`
