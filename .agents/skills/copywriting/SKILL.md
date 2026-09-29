---
name: copywriting
description: >-
  Conversion copywriting formulas, headline templates, email copy patterns, landing page structures, and CTA optimization
---

# /copywriting — Autonomous Conversion Copywriting & Persuasion Engine

Conversion copywriting formulas, headline templates, email copy patterns, landing page structural frameworks, and CTA optimization for the Mekong RaaS Agency OS.

---

## Psychological Conversion Frameworks

| Formula | Full Name | Primary Strength & Use Case |
|---|---|---|
| **PAS** | Problem - Agitation - Solution | Exposes deep customer pain, agitates consequences, presents undeniable solution |
| **AIDA** | Attention - Interest - Desire - Action | Grabs attention, builds interest, fuels desire, triggers immediate conversion |
| **BAB** | Before - After - Bridge | Contrasts chaotic before-state with dream after-state; positions product as bridge |
| **FAB** | Features - Advantages - Benefits | Translates technical architecture into unfair competitive benefits |
| **4Us** | Urgent - Unique - Useful - Ultra-specific | Scores and crafts high-conversion headlines and subject lines |

---

## Typer CLI Commands

```bash
# Copywriting operations overview & formulas catalog
mekong copywriting [--json]

# Synthesize high-converting copy using proven direct-response frameworks
mekong copywriting generate "Mekong CLI" --audience "Founders & Engineers" [--formula pas|aida|bab|fab|4us] [--type landing_page|email|headline|cta] [--benefit <text>] [--style direct_response|technical_founder|punchy_minimalist|storytelling] [--save] [--json]

# Generate high-impact headline variations categorized by psychological angle
mekong copywriting headline "Mekong CLI" --value "ship autonomous startups" [--count 5] [--json]

# Generate optimized call-to-action button copy with risk-reversal microcopy
mekong copywriting cta "start free trial" [--reversal "No credit card required • Cancel anytime"] [--json]

# Show registered copywriting formulas and steps
mekong copywriting formulas [--json]

# Show brand voice and writing style guides
mekong copywriting styles [--json]

# List saved copywriting projects from the database
mekong copywriting list [--limit 50] [--json]
```

---

## Native MCP Tools

| MCP Tool | Description | Arguments |
|---|---|---|
| `mekong_copywriting_generate` | Synthesize high-converting copy using direct-response frameworks | `product_name: str, target_audience: str, formula: str = "pas", copy_type: str = "landing_page"` |
| `mekong_copywriting_headline` | Generate headline variations categorized by psychological angle | `product_name: str, value_prop: str, count: int = 5` |
| `mekong_copywriting_cta` | Generate optimized call-to-action buttons with risk-reversal microcopy | `action_goal: str, risk_reversal: str = ""` |
