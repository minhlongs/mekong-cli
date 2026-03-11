---
description: Public company operations — earnings prep, 10-Q/10-K, guidance, quarterly cadence
allowed-tools: Read, Write, Bash
---

# /founder public-co — Public Company Operating System

## USAGE
```
/founder public-co [--quarter <q1|q2|q3|q4>] [--prep | --earnings | --filing]
```

## WELCOME TO PUBLIC LIFE

```
WHAT CHANGES AFTER IPO:
  Before: → build product, talk to customers, raise money
  After:  → all of above PLUS quarterly earnings machine

THE NEW RHYTHM (every 90 days, forever):
  Day 1-75:  Run the business
  Day 76-85: Prepare earnings
  Day 86:    Earnings call
  Day 87-90: Analyst questions, stock reaction
  Day 91:    Repeat

WHAT INVESTORS NOW EXPECT:
  □ 10-Q filed within 40 days of quarter end (SEC)
  □ 10-K filed within 60-90 days of year end
  □ 8-K for material events (within 4 business days)
  □ Earnings call: results + guidance + Q&A
  □ No surprises (missing guidance = stock -20%)
```

## QUARTERLY EARNINGS CALENDAR

```
FILE: .mekong/ipo/earnings-calendar.md

FISCAL YEAR: {company fiscal year}

EARNINGS SCHEDULE:
  Q1 (Jan-Mar):  Earnings call → ~April 25-30
  Q2 (Apr-Jun):  Earnings call → ~July 25-30
  Q3 (Jul-Sep):  Earnings call → ~October 25-30
  Q4 (Oct-Dec):  Earnings call → ~January 25-30

T-30 DAYS: PREPARATION
  □ CFO begins close process
  □ Revenue recognition review
  □ Non-GAAP reconciliations prepared
  □ Key metric calculations finalized
  □ Comparison to guidance (what we told investors last quarter)

T-15 DAYS: FIRST DRAFT
  □ Earnings press release draft 1
  □ Prepared remarks (CEO + CFO scripts)
  □ 10-Q draft begins
  □ Slide deck draft

T-7 DAYS: FINAL PREP
  □ Guidance for next quarter set
    (conservative: beat and raise is the game)
  □ Q&A prep: anticipate 20+ analyst questions
  □ Board review of results + guidance
  □ Legal review of all disclosures
  □ Quiet period: CEO/CFO no public commentary

T-1 DAY: LOCKDOWN
  □ Press release finalized
  □ 10-Q finalized
  □ All participants on earnings call confirmed
  □ Dial-in / webcast URL distributed

EARNINGS DAY:
  16:00 ET: Market close
  16:05 ET: Press release over wire (BusinessWire/PR Newswire)
  16:30 ET: Earnings call begins
  17:00 ET: Q&A with analysts
  17:30 ET: Call ends, replay available
  Next AM:  10-Q filing with SEC
```

## EARNINGS CALL STRUCTURE

**Agent: CFO + CMO / sonnet + gemini / 5 MCU per quarter**

```
CALL STRUCTURE (45-60 minutes total):

OPERATOR: "Welcome to {Company} Q{n} {year} Earnings Call."

IR DISCLAIMER (2 min):
  Forward-looking statements safe harbor
  GAAP vs non-GAAP reconciliation reminder

CEO REMARKS (10-12 min):
  Business highlights (3-4 wins this quarter)
  Customer stories (1-2 specific examples)
  Product milestones
  Strategic progress on stated priorities
  Looking ahead (qualitative)

CFO REMARKS (8-10 min):
  Revenue: $Xm, up Y% YoY, vs guidance of $Zm
  Gross margin: X%, improvement/decline of Y bps
  Operating income/loss: $Xm non-GAAP
  Key metrics: ARR, NRR, customer count
  Q{n+1} guidance:
    Revenue: $X to $Y million
    (range = conservative to base case)
  Full year guidance: raise/maintain/narrow

Q&A (20-25 min):
  Analyst questions (prepared + live)
  CEO handles strategic, CFO handles financial
  
CALL RULES:
  □ Never say "I don't know" — "We'll follow up on that"
  □ Never react to stock price movement on call
  □ Beat guidance by 2-3% consistently = reliable premium
  □ Never miss on both revenue AND guidance — double miss = -30%
```

## THE GUIDANCE GAME

```
BEAT AND RAISE STRATEGY:
  Analyst expectations = wall street consensus
  Your guidance sets that consensus
  
  PLAYBOOK:
    Set guidance at 90-95% confidence level
    Beat by 3-5% → small upward surprise → stock up
    Then raise next quarter guidance modestly
    Repeat every quarter = "premium quality" multiple
  
  NEVER:
    Set aggressive guidance to excite market
    Then miss = stock craters = analysts downgrade
    Trust broken = 2-3 years to rebuild
  
  MISS TYPES:
    Revenue miss only: -10 to -20% stock reaction
    Guidance cut only: -15 to -25%
    Both: -30 to -50% in one day
    
  "A company that consistently delivers is worth more than
   one that occasionally delights and occasionally disappoints."
   — Every public CFO ever

GUIDANCE FORMULA:
  Q{n+1} guidance = 
    Current run rate × (1 + conservative_growth%) 
    + signed contracts not yet recognized
    - churn at normal rate
    × 0.95 (5% safety margin)
```

## 10-K ANNUAL REPORT

```
ANNUAL REPORT COMPONENTS:
  Business description (updated)
  Risk factors (updated)
  Financial statements (audited)
  MD&A: Management Discussion & Analysis
    → CEO explains the year in narrative form
    → This is your annual letter to shareholders
  
SHAREHOLDER LETTER (most read section):
  Format: Warren Buffett style — honest, personal, long-term
  
  TEMPLATE:
  "To Our Shareholders,
  
  {Year} was {honest assessment — good/hard/transformative}.
  
  [1 paragraph: what we said we'd do last year]
  [1 paragraph: what we actually did — honest on gaps]
  [1 paragraph: what we learned]
  [2 paragraphs: where we're going and why]
  [1 paragraph: thanks to team, customers, shareholders]
  
  —{CEO name}"
  
  AVOID: PR speak, vague promises, "we're excited"
  INCLUDE: Real numbers, honest challenges, specific plans
```

## MATERIAL EVENT REPORTING (8-K)

```
WHAT REQUIRES IMMEDIATE 8-K FILING (4 business days):
  □ Major acquisition or divestiture
  □ Bankruptcy or receivership
  □ Changes to fiscal year
  □ CEO/CFO departure or appointment
  □ Material cybersecurity incident
  □ Auditor resignation
  □ Amendment to articles or bylaws
  □ Regulation FD: any material disclosure to investors

8-K RULE: If in doubt, file. Over-disclosure is never penalized.
Under-disclosure = SEC enforcement + shareholder lawsuits.
```

## QUARTERLY METRICS DASHBOARD (automated)

**Agent: Data / local / 1 MCU**

```
/founder public-co --quarter q3

AUTO-GENERATES from .mekong data:

Q3 {YEAR} KEY METRICS:

  FINANCIAL:
  Revenue:       ${n}M    (+{pct}% YoY, vs guidance ${n}M)
  Gross Margin:  {pct}%   (prev quarter: {pct}%)
  OpEx:          ${n}M    (as % revenue: {pct}%)
  Free Cash Flow:${n}M    (positive/negative)
  Cash:          ${n}M    (runway: {n} months)

  BUSINESS:
  ARR:           ${n}M    (+{pct}% QoQ)
  Customers:     {n}      (+{n} net new)
  NRR:           {pct}%   (prev: {pct}%)
  CAC:           ${n}     (trend: improving/worsening)

  GUIDANCE SET LAST QUARTER: ${range}M
  BEAT/MISS: {BEAT by ${n}M / MISS by ${n}M}
  
  NEXT QUARTER GUIDANCE: ${range}M ({pct}% YoY)
```

## OUTPUT

```
✅ Public Company Q{n} Package Ready
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📁 .mekong/ipo/earnings/q{n}-{year}/
  ✓ earnings-press-release.md
  ✓ ceo-prepared-remarks.md
  ✓ cfo-prepared-remarks.md
  ✓ qa-prep-40-questions.md
  ✓ guidance-model.md
  ✓ 10q-draft.md
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💳 MCU: -5 (balance: {remaining})

NEXT COMMANDS: /founder ir · /founder insider
```
