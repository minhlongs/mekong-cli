# Content Strategy — Mekong CLI

## Overview
Content is the primary acquisition channel for a developer-focused CLI tool. Mekong CLI's content strategy targets technical and business audiences through educational, demo-driven content that converts readers into CLI installers and paying RaaS customers.

---

## Content Mission
**"Show, don't tell — every piece of content demonstrates Mekong CLI running a real business task."**

The content engine itself runs on Mekong CLI:
- Blog posts drafted via `mekong writer-blog`
- Social batches via `mekong writer-social-batch`
- Newsletter via `mekong writer-newsletter`
- Content calendar managed via `mekong marketing-content-engine`

---

## Content Pillars

### Pillar 1: Technical Tutorials (40% of output)
**Audience:** Developers, DevOps engineers
**Goal:** Drive GitHub stars and pip installs
**Format:** Long-form blog post (1,500-3,000 words) + code snippets

Topics:
- "Build a full REST API from scratch with `mekong cook`"
- "Replace your CI/CD setup with 3 Mekong CLI commands"
- "Universal LLM routing: DeepSeek to Claude with one env var swap"
- "Mekong CLI + Ollama: Run your entire dev workflow offline, free"
- "PEV engine explained: How AI plans, executes, and self-heals"

### Pillar 2: Business Automation (30% of output)
**Audience:** Founders, operators, agency owners
**Goal:** Convert to Starter $49 tier
**Format:** Case study + demo video

Topics:
- "How I replaced a $2,000/mo VA with `mekong sales` + `mekong finance`"
- "Quarterly business review in 10 minutes with `mekong quarterly`"
- "From zero to pitch deck: `mekong fundraise` in action"
- "Agency ops on autopilot: 289 commands for client delivery"
- "Non-technical founder survival guide: Mekong CLI for business ops"

### Pillar 3: Comparisons & Positioning (15% of output)
**Audience:** Decision makers evaluating tools
**Goal:** Capture high-intent comparison searches
**Format:** SEO-optimized comparison pages

Topics:
- "Mekong CLI vs GitHub Copilot: Beyond code completion"
- "Mekong CLI vs Cursor: When you need more than an IDE"
- "Replace 10 SaaS tools with one CLI: Notion + Linear + Slack + more"
- "OpenRouter vs DeepSeek vs Ollama: LLM provider cost comparison"

### Pillar 4: Community & Ecosystem (15% of output)
**Audience:** Open source community, contributors
**Goal:** Drive GitHub engagement and contributions
**Format:** Short posts, changelogs, community updates

Topics:
- Monthly changelog posts (via `mekong docs-changelog`)
- "Week in Mekong" community digest
- Contributor spotlights
- Command deep-dives (one command per week)

---

## Content Production Process (command: `mekong marketing-content-engine`)

```
Weekly content workflow:
1. mekong marketing-content-engine  → Generate topic ideas + calendar
2. mekong writer-blog "Topic"       → Draft long-form post (1,500+ words)
3. mekong content/enhance           → Polish, SEO optimize
4. mekong writer-social-batch       → 5 social posts per blog
5. mekong writer-newsletter         → Weekly digest email
6. Publish: GitHub, Dev.to, personal blog, Twitter, LinkedIn
```

**Cadence:**
- 2 blog posts/week
- 5 social posts/day (batched weekly via `mekong writer-social-batch`)
- 1 newsletter/week
- 1 YouTube/Loom demo video/2 weeks

---

## Blog Content Calendar (Q2 2026)

| Week | Blog Topic | Pillar | Command Featured |
|------|-----------|--------|-----------------|
| W1 Apr | "Mekong CLI: Build your AI company in 10 minutes" | Tutorial | `cook`, `company/init` |
| W2 Apr | "Replace your sales team with 5 commands" | Business | `sales`, `sdr-prospect` |
| W3 Apr | "Universal LLM: 7 providers, zero lock-in" | Tutorial | LLM config |
| W4 Apr | "Quarterly review in 10 min" | Business | `quarterly` |
| W1 May | "Mekong vs GitHub Copilot" | Comparison | Full suite |
| W2 May | "HR automation: hire to offboard" | Business | `hr-recruit`, `people-offboard` |
| W3 May | "Deploy to Cloudflare in one command" | Tutorial | `deploy` |
| W4 May | "Finance ops for non-finance founders" | Business | `finance`, `invoice` |

---

## Social Media Strategy (command: `mekong writer-social-batch`)

### Twitter/X
- **Frequency:** 2 posts/day
- **Format:** Demo GIFs of CLI running commands, code snippets, one-liner insights
- **Hook:** "I just [ran quarterly review/closed a sales deal/deployed an app] in 30 seconds. Here's the command:"

### LinkedIn
- **Frequency:** 1 post/day
- **Format:** Founder stories, business automation case studies
- **Audience:** Founders, agency owners, CTOs

### GitHub
- Repo README with animated terminal GIF
- Detailed CHANGELOG via `mekong docs-changelog`
- Issues as community engagement touchpoints

---

## Newsletter Strategy (command: `mekong writer-newsletter`)

**Name:** "OpenClaw Weekly"
**Audience:** Developers and founders in Mekong CLI ecosystem
**Frequency:** Weekly (Friday)

**Sections:**
1. Command of the week: deep dive on one command
2. Community highlight: user story or use case
3. Changelog: new features/commands added
4. Resource: external tool or tutorial relevant to readers
5. CTA: Upgrade prompt or partner offer

**Growth targets:**
- Month 1: 200 subscribers (from GitHub readme + Product Hunt)
- Month 3: 1,000 subscribers
- Month 6: 5,000 subscribers
- Conversion: 2% of subscribers → paid (100 customers from email by month 6)

---

## SEO Content Plan (command: `mekong seo`)

### Primary landing pages to create:
1. `/ai-cli-tool` — "AI CLI Tool for Developers and Founders"
2. `/replace-saas` — "Replace Your SaaS Stack with AI"
3. `/pricing` — Clear tier comparison with MCU calculator
4. `/comparisons/github-copilot` — Comparison page
5. `/use-cases/agencies` — Agency-specific landing page

### Internal linking structure:
- Blog posts → Feature pages → Pricing → Sign up
- Command docs → Tutorial posts → Blog → Sign up

---

## Content Metrics

| Metric | Month 3 Target | Month 6 Target |
|--------|---------------|----------------|
| Blog posts published | 24 | 48 |
| Organic visitors/mo | 2,000 | 10,000 |
| Newsletter subscribers | 500 | 3,000 |
| Twitter followers | 500 | 2,000 |
| GitHub stars from content | 300 | 1,000 |
| Content-attributed signups | 50 | 200 |
| Content-attributed MRR | $2,450 | $10,000 |

---

## Tools & Stack

All content production uses Mekong CLI itself (dogfooding):
- `mekong writer-blog` — Blog drafts
- `mekong writer-social-batch` — Social queue
- `mekong writer-newsletter` — Email drafts
- `mekong marketing-content-engine` — Calendar and strategy
- `mekong seo` — Keyword research and optimization
- `mekong content/enhance` — Quality polish

External tools: none required for content production (zero extra cost).
