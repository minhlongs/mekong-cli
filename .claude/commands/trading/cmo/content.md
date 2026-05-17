---
description: ⚡⚡⚡ CMO Content Strategy — calendar planning, content creation, pillar balance, SEO optimization
argument-hint: [action: calendar|create|audit] [topic: "content topic"]
---

**Ultrathink** CMO content strategy: <args>$ARGUMENTS</args>

**CWD:** `apps/algo-trader` | **REF:** `docs/cmo-sops.md` SOP-M02

## Pipeline (5 steps)

### 1. CONTENT INVENTORY
- Scan existing content: blog posts, threads, tutorials, docs
- Categorize by pillar: 70% educational / 20% showcase / 10% community
- Identify gaps and overrepresented topics

### 2. KEYWORD RESEARCH
```
Primary targets:
├── "crypto trading bot cli" — competition: low
├── "algorithmic trading open source" — competition: medium
├── "automated crypto trading" — competition: high
├── "stealth crypto trading" — competition: low
└── "cli trading bot tutorial" — competition: low
```
Match keywords → content gaps → calendar slots

### 3. WEEKLY CALENDAR GENERATION
```
Monday:    Technical deep-dive (blog)     — Pillar: Educational
Tuesday:   Strategy spotlight (thread)    — Pillar: Showcase
Wednesday: Community Q&A (Discord/Reddit) — Pillar: Community
Thursday:  Tutorial/how-to (video/blog)   — Pillar: Educational
Friday:    Performance report (data viz)  — Pillar: Showcase
Weekend:   Market analysis (short-form)   — Pillar: Educational
```

### 4. CONTENT BRIEF CREATION
For each calendar slot, generate brief:
```markdown
## Content Brief — {title}
- **Type:** Blog / Thread / Tutorial / Report
- **Pillar:** Educational / Showcase / Community
- **Target keyword:** {keyword}
- **Audience:** {beginner/intermediate/advanced}
- **Outline:** {3-5 sections}
- **CTA:** {install / star / join Discord / subscribe}
- **Assets needed:** {screenshots / diagrams / code snippets}
- **Distribution:** {channels}
```

### 5. OUTPUT
Save: `plans/reports/cmo-content-calendar-{date}.md`

## Content Ideas (Algo-Trader Specific)

| # | Title | Type | Keyword |
|---|-------|------|---------|
| 1 | "Building a Stealth Crypto Arb Bot with CLI" | Blog | stealth crypto trading |
| 2 | "4-Tier Autonomy: From Observer to AGI Trader" | Thread | automated crypto trading |
| 3 | "Backtest Results: MACD+Bollinger+RSI Strategy" | Report | crypto backtest results |
| 4 | "Why CLI > GUI for Algo Trading" | Blog | cli trading bot |
| 5 | "Art of War Applied to Crypto Trading" | Blog | trading strategy |
| 6 | "1216 Tests: How We Build Reliable Trading Bots" | Blog | reliable trading bot |
| 7 | "Cross-Exchange Arbitrage Tutorial" | Tutorial | crypto arbitrage tutorial |
| 8 | "Circuit Breakers: Safety-First Trading" | Thread | safe algo trading |

## USAGE
```bash
/trading:cmo:content calendar           # Generate weekly calendar
/trading:cmo:content create "topic"     # Create content brief
/trading:cmo:content audit              # Audit existing content
```
