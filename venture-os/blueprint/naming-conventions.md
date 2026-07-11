# Naming Conventions — VentureOS

> **Source:** foundation.md §12
> **Status:** IMMUTABLE | **Version:** 0.1.0 | **Date:** 2026-07-11

---

## Tổng quan / Overview

Mọi naming convention dưới đây là BẮT BUỘC. Không exception. Mục đích: predictability — AI agents có thể nhìn vào tên file/folder/biến và biết chính xác nó là gì.

---

## Naming by Context

| Entity | Convention | Example | Context |
|---|---|---|---|
| Venture ID | `{type}-{YYYY}-{slug}` | `saas-2026-ai-chatbot-platform` | TOML identifies; entropy là wallet-biến |
| Venture directory | Same as ID | `ventures/saas-2026-ai-chatbot-platform/` | File tree |
| Workflow ID | `{namespace}/{slug}` | `research/market-research` | YAML + CLI |
| Compiler ID | `{slug}` | `business-plan` | YAML + CLI |
| Decision file | `{YYYYMMDD}-{slug}.md` | `20260710-mvp-scope.md` | Filesystem |
| Decision ID field | `decision-{slug}-{YYYYMM}` | `decision-mvp-scope-chatbot-202607` | TOML/JSON metadata |
| WAL file | `run-{YYYYMMDD}.jsonl` | `run-20260710.jsonl` | Filesystem |
| Plan directory | `{YYYYMMDD}-{slug}/` | `260711-0255-ventureos-next/` | Plans |
| ADR file | `{NNN}-{slug}.md` | `001-filesystem-as-db.md` | ADR registry |
| Extension ID | `{slug}` | `custom-research-agent` | Extension manifest |
| Knowledge domain | `{domain}` | `legal`, `market`, `technology` | Knowledge tree |

---

## Core Rules

### 1. Slugs — Kebab Case (lowercase + hyphens)

```
GOOD:  ai-chatbot-platform, market-research, business-plan
BAD:   AI_Chatbot, market_research, businessPlan, ai chatbot
```

- All lowercase
- Hyphens as separators (không underscores, không spaces)
- Max 60 characters per slug
- Alphanumeric + hyphens only (no accents, no emoji)
- Readable khi đọc nhanh: `ai-chatbot` rõ hơn `aicb`

### 2. Dates — Two Formats

| Use | Format | Example |
|---|---|---|
| Filename dates | `YYYYMMDD` | `20260710` |
| Timestamps in content | ISO-8601 | `2026-07-10T20:22:14.616Z` |
| Directory dates | `YYYYMMDD-HHMM` | `260711-0255` |

**Không mixed formats trong cùng một context.** Nếu filename dùng `YYYYMMDD`, không dùng `MM-DD-YYYY`.

### 3. IDs — Prefix + Entity + Date

Pattern: `{prefix}-{entity}-{YYYYMM}`

```
decision-mvp-scope-chatbot-202607
entity-market-ai-202607
rel-venture-depends-on-202607
```

Prefixes: `decision-`, `entity-`, `rel-`, `venture-`, `workflow-`, `compile-`, `wal-`

### 4. No Version Numbers in IDs

```
GOOD:  saas-2026-chatbot
BAD:   saas-v2-2026-chatbot
BAD:   saas-v2.1-2026-chatbot
```

Reasoning: Versioning happens in git. Filename versioning is stale the moment you commit.

### 5. Directory Names Match IDs

```
Venture ID: saas-2026-chatbot
Directory:  ventures/saas-2026-chatbot/
```

Never: `ventures/chatbot/` when ID is `saas-2026-chatbot`.

---

## CLI Command Conventions

### Verb Pattern

| Verb | Meaning | Example |
|---|---|---|
| `init` | Create new entity | `venture init "My SaaS" --type startup` |
| `new` | Append new record | `venture decision new "Pivot?" --type strategic` |
| `run` | Execute pipeline | `venture workflow run research/market-research` |
| `compile` | Transform outputs | `venture compile business-plan` |
| `show` | Display state | `venture show` |
| `list` | Enumerate | `venture list` |
| `compact` | Maintenance | `venture wal compact --policy events:1000` |

### Command Arguments

- Venture ID: passed as positional arg `venture-id`
- File paths: relative to venture directory
- Flags: kebab-case `--output-dir`, not `--outputDir`

---

## Content Conventions (Markdown)

### Decision Document Template

```markdown
# {EN Title} / {Tiếng Việt}

> **ID:** {decision-id-field}
> **Type:** {type} | **Date:** {YYYY-MM-DD} | **Status:** {pending\|approved\|rejected}

---

## Context / Bối cảnh

English context...

/Bối cảnh tiếng Việt...

---

## Options / Lựa chọn

### Option A
- Pros
- Cons

### Option B
- Pros
- Cons

---

## Decision / Quyết định

{chosen option}

---

## Rationale / Lý do

```text
## Core Thread (English)
## Luồng suy nghĩ chính (Tiếng Việt)
```

---
```

### Section Heading Format

```
## 1. Section Title / Tiêu đề

English content...

/Bản tiếng Việt...
```

Rules:
- Numbered headings (`## 1.`, `## 2.`) for sequential content
- Bilingual headings: `## EN / VI`
- Never single language only in human-facing docs

---

## To-Do vs Done

- `[ ]` = pending task
- `[x]` = completed (lowercase x)
- `[WIP]` = in progress (only in comments/notes, not in committed docs)

---

## Anti-patterns

| Pattern | Problem | Fix |
|---|---|---|
| `my_venture` in path | Underscore ≠ kebab | `my-venture` |
| `venture_v2` | Version in ID | Use git tags |
| `ChatBot` in slug | PascalCase | `chat-bot` |
| `2026-07-10` in filename | Wrong date format | `20260710` |
| `research.market` | Dot separator | `research/market-research` |
| `entity123` | No semantic prefix | `entity-{slug}-{YYYYMM}` |
