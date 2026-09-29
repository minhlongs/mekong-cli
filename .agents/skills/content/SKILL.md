---
name: content
description: >-
  Content marketing — generate posts, manage calendar, track channels
---

# /content — Autonomous Content Marketing & Editorial Publishing Suite

Multi-format generation, editorial calendar management, multi-channel distribution, and content pipeline tracking for the Mekong RaaS Agency OS.

---

## Content Pillars & Distribution Cadence

| Pillar | Frequency | Target Channels | Theme |
|---|---|---|---|
| **One-Person Company (`one-person-company`)** | Weekly | Blog, Indie Hackers, Twitter | Solo founder scaling, automation, AI leverage |
| **AI Agents in Practice (`ai-agents`)** | Weekly | Blog, Twitter, YouTube | Agent harness architecture, PEV loops, resilience |
| **Solo Founder Life (`solo-founder`)** | Biweekly | Twitter, Indie Hackers, Substack | Transparent bootstrapping, mental models, discipline |
| **Binh Pháp for Business (`binh-phap`)** | Monthly | Blog, Twitter, Substack | Sun Tzu Art of War applied to software strategy |
| **ZenOS Philosophy (`zenos`)** | Monthly | Blog, Indie Hackers | Decentralized commons, particles, agent governance |

---

## Typer CLI Commands

```bash
# Editorial operations & content pipeline overview
mekong content [--json]

# Generate structured, ready-to-publish content for any pillar and format
mekong content generate --pillar one-person-company --format blog [--topic <topic>] [--channel blog] [--save] [--file] [--output-dir <path>] [--json]
mekong content generate --pillar ai-agents --format twitter [--topic "Why PEV loops beat prompt chains"] [--json]
mekong content generate --pillar binh-phap --format linkedin [--json]

# Show editorial calendar schedule, publication frequencies, and due dates
mekong content calendar [--json]

# Show distribution channel statistics, followers, and post counts
mekong content channels [--json]

# List tracked content items with status filtering
mekong content list [--status draft|scheduled|published|all] [--pillar <name>] [--json]

# Mark a drafted/scheduled content item as published
mekong content publish <content_id> [--channel <channel>] [--json]

# Display registered content pillars and guidelines
mekong content pillars [--json]
```

---

## Native MCP Tools

| MCP Tool | Description | Arguments |
|---|---|---|
| `mekong_content_generate` | Generate structured, ready-to-publish content for any pillar and format | `pillar: str, format_type: str = "blog", topic: str = "", channel: str = ""` |
| `mekong_content_calendar` | Query editorial publication calendar, frequencies, and deadlines | `()` |
| `mekong_content_channels` | Query distribution channels, audience size, and post metrics | `()` |
