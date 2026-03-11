---
description: VC landscape mapping — tier, sector focus, check size, founder-friendliness score
allowed-tools: Read, Write
---

# /founder vc-map — Investor Intelligence System

## USAGE
```
/founder vc-map [--stage seed|a|b|c|late] [--sector <type>] [--region <geo>] [--score]
```

## BƯỚC 0 — SCAN
```
□ Đọc .mekong/company.json          → stage, product_type, region
□ Đọc .mekong/raise/ (nếu có)       → previous investor context
□ Đọc .mekong/founder/persona.json  → company positioning
```

## BƯỚC 1 — INVESTOR DATABASE + SCORING

**Agent: Data / local / 1 MCU**

```python
# Founder-Friendliness Score (FFS): 1-10
# Based on: board control, liquidation terms, support quality,
#           founder references, portfolio outcomes

VC_DATABASE = {

  # ═══ GLOBAL TIER 1 — SEED ═══
  "YC": {
    "stage": ["pre-seed", "seed"],
    "check": "$125K-$500K",
    "equity": "7%",
    "ffs": 9,  # legendary founder-friendly
    "pros": "Best network on earth, brand lifts valuation",
    "cons": "Batch dilution, competitive cohort",
    "apply": "ycombinator.com/apply",
    "signal": "high acceptance bar, but worth 10x applying",
    "notable_portfolio": "Airbnb, Stripe, Coinbase, Dropbox",
    "vietnam_portfolio": "Giải pháp Việt if any"
  },
  "Pioneer": {
    "stage": ["pre-seed"],
    "check": "$8K-$50K",
    "equity": "1-2%",
    "ffs": 8,
    "pros": "Solo founder friendly, global, small equity",
    "cons": "Small check",
    "apply": "pioneer.app",
    "signal": "Good first check if pre-revenue"
  },
  "Sequoia": {
    "stage": ["seed", "a", "b", "c"],
    "check": "$1M-$100M+",
    "equity": "15-25%",
    "ffs": 7,
    "pros": "Best brand, deep operator network",
    "cons": "High expectations, fast-paced portfolio",
    "apply": "sequoiacap.com",
    "signal": "Warm intro only"
  },
  "a16z": {
    "stage": ["seed", "a", "b", "c"],
    "check": "$500K-$100M+",
    "equity": "15-20%",
    "ffs": 7,
    "pros": "Deep media + network, strong AI thesis",
    "cons": "Big fund = need big outcomes only",
    "apply": "a16z.com",
    "focus": "AI, crypto, bio, consumer"
  },

  # ═══ SEA / VIETNAM FOCUSED ═══
  "Do Ventures": {
    "stage": ["seed", "a"],
    "check": "$500K-$5M",
    "equity": "10-20%",
    "ffs": 8,
    "pros": "Vietnam deep network, founder-operator team",
    "cons": "Vietnam-first focus",
    "apply": "doventures.vc",
    "region": "Vietnam, SEA",
    "portfolio": "Timo, Dat Bike, GoBear"
  },
  "Wavemaker Partners": {
    "stage": ["seed", "a"],
    "check": "$500K-$5M",
    "equity": "10-20%",
    "ffs": 7,
    "region": "SEA, Vietnam",
    "apply": "wavemaker.vc"
  },
  "Golden Gate Ventures": {
    "stage": ["seed", "a", "b"],
    "check": "$1M-$15M",
    "ffs": 7,
    "region": "SEA",
    "apply": "goldengate.vc"
  },
  "500 SEA": {
    "stage": ["pre-seed", "seed"],
    "check": "$150K-$500K",
    "ffs": 8,
    "pros": "Network access, global SEA focus",
    "apply": "500.co/startups/sea",
    "region": "SEA"
  },
  "Monk's Hill Ventures": {
    "stage": ["seed", "a"],
    "check": "$1M-$10M",
    "ffs": 8,
    "region": "SEA, Vietnam",
    "apply": "monkshill.com"
  },

  # ═══ AI/DEV TOOL FOCUSED ═══
  "Gradient Ventures (Google)": {
    "stage": ["seed", "a"],
    "check": "$1M-$10M",
    "ffs": 7,
    "focus": "AI, developer tools",
    "pros": "Google integration + infra credits",
    "apply": "gradient.google"
  },
  "Boldstart Ventures": {
    "stage": ["seed"],
    "check": "$1M-$5M",
    "ffs": 9,
    "focus": "Developer tools, infrastructure",
    "pros": "Deep enterprise + PLG expertise",
    "notable": "Snyk, BigID, StepSecurity"
  },
  "Heavybit": {
    "stage": ["seed", "a"],
    "check": "$500K-$5M",
    "ffs": 9,
    "focus": "Developer tools exclusively",
    "pros": "Community, program, networks",
    "apply": "heavybit.com/apply"
  },

  # ═══ BOOTSTRAPPED / INDIE FRIENDLY ═══
  "Tiny.vc": {
    "stage": ["seed"],
    "check": "$250K-$2M",
    "equity": "5-10%",
    "ffs": 10,
    "focus": "Calm, profitable businesses",
    "pros": "No board, no pressure to scale at all costs",
    "apply": "tiny.vc"
  },
  "Calm Fund": {
    "stage": ["seed"],
    "check": "$20K-$200K",
    "equity": "revenue share or small equity",
    "ffs": 10,
    "focus": "Sustainable, founder-owned",
    "apply": "calmfund.com"
  },
  "Indie.vc": {
    "stage": ["seed"],
    "check": "$100K-$1M",
    "model": "revenue-based repayment",
    "ffs": 10,
    "focus": "Revenue-generating from day 1"
  },

  # ═══ SERIES A/B ═══
  "Accel": {
    "stage": ["a", "b"],
    "check": "$5M-$50M",
    "ffs": 7,
    "notable": "Atlassian, Dropbox, Slack, Facebook early"
  },
  "Bessemer": {
    "stage": ["a", "b", "c"],
    "check": "$5M-$100M",
    "ffs": 7,
    "cloud_laws": "10 laws of cloud",
    "notable": "LinkedIn, Pinterest, Shopify"
  },
  "Index Ventures": {
    "stage": ["a", "b", "c"],
    "check": "$5M-$100M",
    "ffs": 8,
    "notable": "Adyen, Figma, Notion"
  },

  # ═══ LATE STAGE / PRE-IPO ═══
  "Tiger Global": {
    "stage": ["c", "d", "pre-ipo"],
    "check": "$50M-$500M",
    "ffs": 5,
    "pros": "Fast, no board involvement",
    "cons": "Pure financial, no value-add",
    "signal": "Good for pre-IPO check, not strategic"
  },
  "SoftBank Vision Fund": {
    "stage": ["c", "d", "pre-ipo"],
    "check": "$100M-$5B",
    "ffs": 3,
    "warning": "Read WeWork case study before taking"
  },
  "Coatue": {
    "stage": ["b", "c", "d", "pre-ipo"],
    "check": "$20M-$500M",
    "ffs": 6
  }
}
```

## BƯỚC 2 — FILTER + RANK

```
Filter by: stage + sector + region + ffs_minimum
Sort by: founder-friendliness score DESC

Output table:
╔═══════════════════════════════════════════════════════════════════╗
║  INVESTOR MAP — {company_name} · Stage: {stage} · Sector: {type} ║
╠═══════════════════╦═══════╦══════════╦═══════╦═══════════════════╣
║ Fund              ║ Check ║ Equity   ║ FFS   ║ Why               ║
╠═══════════════════╬═══════╬══════════╬═══════╬═══════════════════╣
║ YC                ║ $500K ║ 7%       ║ ★★★★★ ║ Best network      ║
║ Do Ventures       ║ $1M   ║ 15%      ║ ★★★★☆ ║ Vietnam depth     ║
║ Heavybit          ║ $2M   ║ 10%      ║ ★★★★★ ║ Dev tool expert   ║
║ 500 SEA           ║ $300K ║ 6%       ║ ★★★★☆ ║ SEA network       ║
╚═══════════════════╩═══════╩══════════╩═══════╩═══════════════════╝

FOUNDER-FRIENDLINESS SCORE BREAKDOWN:
  10 = Tiny.vc, Calm Fund (no pressure, no board)
  9  = YC, Pioneer, Heavybit (network + support)
  8  = Do Ventures, 500 SEA, Boldstart (active help)
  7  = Sequoia, Accel, Index (brand but less flexible)
  6  = Coatue (check + connections, limited help)
  3-5 = SoftBank, Tiger (money, be careful with control)
```

## BƯỚC 3 — OUTREACH INTEL

**Agent: Sales / haiku / 2 MCU**

For top 10 matched investors:
```
Generate outreach package per investor:

VC NAME: {name}
Partner to target: {most active partner for our sector}
Best warm intro path: {LinkedIn 2nd connection / portfolio founder / mutual}
Cold email angle: {what their investment thesis says we should pitch}
Their recent portfolio: {2-3 recent investments = signal of thesis}

PERSONALIZED EMAIL:
  Subject: {specific hook based on their portfolio/thesis}
  "I saw you invested in {portfolio_company} — we're building
   something adjacent but for {different angle}..."
```

## OUTPUT

```
✅ VC Intelligence Map Ready
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{n} investors matched for stage: {stage}
Top 3 founder-friendly: YC, Heavybit, Do Ventures

📁 .mekong/raise/vc-map/
  ✓ matched-investors.md
  ✓ outreach-intel.md
  ✓ warm-intro-map.md
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💳 MCU: -1 (balance: {remaining})

RULE: Always approach founder-friendly funds first.
High FFS score = better terms + better relationship.
```
