---
description: Insider trading compliance + investor relations + lockup expiry — post-IPO protection
allowed-tools: Read, Write
---

# /founder insider — Trading Compliance System

## USAGE
```
/founder insider [--setup | --window | --plan | --check]
```

## WHY THIS COMMAND COULD SAVE YOUR FREEDOM

```
Martha Stewart went to prison for insider trading.
Countless founders have faced SEC enforcement.
The rules are NOT intuitive. The mistakes are NOT obvious.

RULE 1: As a public company insider, you CANNOT trade on
        material non-public information (MNPI).

WHAT IS MNPI:
  □ Upcoming earnings (better or worse than expected)
  □ A major deal about to be signed
  □ A regulatory approval coming
  □ A data breach not yet disclosed
  □ A CEO departure being planned
  □ ANY information not yet in a press release

WHAT YOU CANNOT DO:
  ✗ Sell shares before a bad earnings announcement
  ✗ Buy shares before a positive announcement
  ✗ Tell family members to trade based on your knowledge
  ✗ Text friends about upcoming news even casually
  
WHAT HAPPENS IF CAUGHT:
  Civil: SEC fine (disgorgement + 3x penalty)
  Criminal: up to 20 years prison, $5M fine
  Company: SEC enforcement = massive distraction
```

## BƯỚC 1 — TRADING WINDOWS

```
CLOSED WINDOW PERIODS (cannot trade):
  □ 30 days before quarterly earnings + 24h after
  □ Any time you have MNPI
  □ Reg FD: after any material disclosure to investors
  
OPEN WINDOW PERIODS (safe to trade):
  □ Typically: day 2-30 after earnings release
  □ Exact window set by General Counsel quarterly
  
COMPANY TRADING POLICY (generate template):
FILE: .mekong/ipo/insider-trading-policy.md

  "All employees and officers must:
   1. Pre-clear trades with General Counsel
   2. Trade only during open windows
   3. Sign attestation form before each trade
   4. No hedging or pledging of company stock"
```

## BƯỚC 2 — 10b5-1 PLAN (your best friend)

```
WHAT IS A 10b5-1 PLAN:
  Pre-planned trading schedule, set up DURING open window
  Trades execute automatically on schedule
  Because planned in advance = no MNPI at time of trade
  = Legal safe harbor = you can sleep at night

HOW TO SET UP:
  1. During open trading window, with GC and broker
  2. Specify: dates, amounts, price ranges to sell
  3. File notice (SEC)
  4. Wait 90-120 days before first trade executes
     (cooling-off period under new 2023 SEC rules)

EXAMPLE PLAN:
  "Sell 50,000 shares on the 1st of each month
   if stock price > $X, for 12 months"
  
  This runs automatically — no decision at time of trade
  No MNPI issue even if you know earnings are coming

FOUNDER LIQUIDITY PLAN:
  Set up 10b5-1 immediately after IPO lockup expiry
  Don't wait until you "need" the money
  Planned, systematic selling = signals confidence
  Panic selling = signals fear
```

## BƯỚC 3 — LOCKUP EXPIRY MANAGEMENT

```
/founder lockup-expiry

LOCKUP = 180 days after IPO. Then:
  All insiders can sell. Stock often drops on expiry.

STRATEGY:

30 DAYS BEFORE EXPIRY:
  □ Calculate: how many shares you want to sell
  □ Set up 10b5-1 plan NOW (before you "know" Q results)
  □ Coordinate with other insiders (signal, not collusion)
  □ IR team: prepare for analyst questions about lockup

ON EXPIRY DAY:
  □ Your 10b5-1 plan executes automatically
  □ You are NOT available for comment on stock
  □ Pre-drafted response ready: "We have systematic
    trading plan in place, have no further comment"

AFTER EXPIRY:
  □ Stock typically drops 5-15% on expiry day (supply increase)
  □ This is NORMAL — don't panic, don't buy back publicly
  □ Recovery usually happens within 2-4 weeks if fundamentals strong

SECONDARY OFFERING (alternative):
  Instead of open market sale, company can do "registered
  direct" or secondary offering
  Pros: organized, larger block, institutional buyers
  Cons: cost (~4% fee), dilution signal if primary shares included
```

## /founder ir — Investor Relations Engine

```
/founder ir [--init | --communicate | --analyst]

IR MISSION:
  Tell your story consistently. To the right people.
  So your stock reflects true value. Not manipulation.

IR CALENDAR (setup):
  □ Earnings calls: 4x/year
  □ Investor conferences: 3-5/year (Goldman, JPMorgan, etc.)
  □ Non-deal roadshows: 2-4/year (just meetings, no capital raise)
  □ Analyst days: 1/year (deep dive, multi-hour event)
  □ Annual meeting: 1/year (proxy vote)

ANALYST COVERAGE MANAGEMENT:
  □ Initiation research: 1-2 weeks post-quiet period
  □ Target: 8-12 analysts covering you
  □ Sell-side vs buy-side: different relationships
  □ Never: trade favors for favorable coverage
  □ Reg FD: same info to all, no selective disclosure

INVESTOR TARGETING:
  Types of shareholders you want:
    Long-only growth: buy and hold 3-5 years (BEST)
    Index funds: guaranteed buy when index-eligible
    Value: come in after growth narrative matures
    Activist: avoid until you're large enough
  
  Targeting strategy:
    Map: current shareholder base
    Gap: who should own you but doesn't?
    Outreach: non-deal roadshow to target accounts

COMMUNICATION PRINCIPLES:
  □ Under-promise, over-deliver (every quarter)
  □ One voice: CEO + CFO only, IR filters everything else
  □ Bad news: disclose immediately, contextualize, show plan
  □ Good news: let results speak, don't hype
  □ Consistency: same story quarter to quarter
  □ Authenticity: institutional investors can smell BS

CRISIS COMMUNICATION:
  IF stock drops > 15% in one day:
    □ Do NOT immediately issue statement (looks panic)
    □ Assess: market-wide move or company-specific?
    □ If company-specific: determine cause
    □ Schedule analyst calls if needed
    □ 8-K if material information exists
    □ CEO available for top 10 shareholders
```

## OUTPUT

```
✅ Post-IPO Compliance Layer Active
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📁 .mekong/ipo/compliance/
  ✓ insider-trading-policy.md
  ✓ trading-windows-calendar.md
  ✓ 10b5-1-plan-template.md
  ✓ lockup-expiry-strategy.md
  ✓ ir-calendar.md
  ✓ analyst-coverage-map.md
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💳 MCU: -3 (balance: {remaining})

⚠️  CRITICAL: Every trade by insiders requires GC pre-clearance.
    When in doubt: don't trade. Ask counsel.
    One mistake here has no good outcome.
```
