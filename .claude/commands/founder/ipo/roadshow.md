---
description: Roadshow preparation — 2-week sprint, Q&A simulation, pricing signal tracking
allowed-tools: Read, Write
---

# /founder roadshow — IPO Roadshow Engine

## USAGE
```
/founder roadshow [--simulate | --schedule | --track-orders]
```

## ROADSHOW OVERVIEW

```
WHAT IS ROADSHOW:
  2 weeks. 50-100 investor meetings. 8-10 meetings/day.
  Goal: build order book > 5-10x oversubscribed
  
  Day 1-2:   Major cities (NYC, SF, Boston, London)
  Day 3-10:  Secondary cities + large institutions
  Day 11-12: Final push, pricing decision
  Day 13:    IPO pricing set (night before listing)
  Day 14:    YOU RING THE BELL

TYPES OF MEETINGS:
  1-on-1:      Top 20 institutions (CEO + CFO attend)
  Small group: 5-10 investors (CEO + CFO)
  Large group: 20-50 (CFO + IR)
  Analyst:     Sell-side analyst briefings (sets price targets)

YOUR TEAM:
  CEO: all 1-on-1s, keynote large groups
  CFO: financial Q&A, 50% of meetings
  IR: logistics, order tracking, banker coordination
  Bankers: roadshow masters, manage schedule
```

## BƯỚC 1 — ROADSHOW DECK (20 slides MAX)

```
Investor attention span: 45 minutes total
20 slides × 2 min = 40 min talk + 5 min Q&A buffer

SLIDE STRUCTURE:
  1.  Cover: Company name, tagline, offering details
  2.  Executive summary: Why invest (3 bullets)
  3.  The problem: Market pain, quantified
  4.  Our solution: What we do, demo screenshot
  5.  Why now: Market timing, tailwinds
  6.  Business model: How we make money
  7.  Go-to-market: How we reach customers
  8.  Metrics page 1: Revenue growth, ARR
  9.  Metrics page 2: NRR, cohorts, LTV:CAC
  10. Competitive moat: Why we win, defensibility
  11. Customer logos + quotes: Social proof
  12. International expansion: Markets we're entering
  13. Product roadmap: What's coming (high level)
  14. Team: CEO, CFO, key executives
  15. Board: Independent directors, credibility
  16. Financial model: Revenue bridge, margins
  17. Path to profitability: When and how
  18. Use of proceeds: What IPO money buys
  19. Summary investment thesis: 3 reasons to buy
  20. Appendix: Additional data (backup slides)

DESIGN RULES:
  □ Max 3 data points per slide
  □ No bullet soup — visual storytelling
  □ Every slide answers: "Why does this make the stock go up?"
  □ Consistent color/brand throughout
  □ "We built this for {persona}" = most memorable framing
```

## BƯỚC 2 — Q&A SIMULATION

**Agent: Opus (investor simulation) / 5 MCU per session**

```
/founder roadshow --simulate

Simulate Institutional Investor Meeting — 45 minutes

OPENING (5 min):
  "Tell me the story of why you started this company."
  CEO presents deck (accelerated — 20 min)

Q&A (20 min) — all the hard questions:

FINANCIAL QUESTIONS:
  "Walk me through your revenue recognition policy."
  → Test: CFO must explain ASC 606 clearly in 2 minutes

  "Your growth decelerated from 120% to 80% YoY. Why?"
  → Test: Have a crisp, honest answer ready
  
  "What's your payback period on CAC by cohort?"
  → Test: Know your unit economics cold
  
  "When do you expect to be GAAP profitable?"
  → Never say "never." Have a credible path.
  
  "Your stock-based comp is very high. Adjust that out —
   what's your real profitability?"
  → Have adjusted metrics + GAAP reconciliation ready

BUSINESS QUESTIONS:
  "Who is your biggest competitive threat in 3 years?"
  → Test: Intellectual honesty + conviction in your moat
  
  "Why hasn't [Big Tech] built this?"
  → Good answer: "They have / tried / here's why we win anyway"
  
  "Customer X is X% of your revenue. What happens if they leave?"
  → Have diversification plan + contract terms ready
  
  "Your NRR is 115%. What would it take to get to 130%?"
  → Shows growth roadmap + product thinking

FOUNDER QUESTIONS:
  "You've been CEO for {n} years. As you scale, do you see
   yourself still in this role?"
  → Never be uncertain. "I'm building for the long term."
  
  "You own {pct}% after this offering. How do you stay
   motivated given dilution?"
  → "{Dollar value} of {pct}% of a $5B company = real motivation.
    We're building to be worth $20B."
  
  "Your co-founder left 2 years ago. What happened?"
  → Have honest, forward-looking answer. Investors will find out.

MARKET QUESTIONS:
  "Your TAM of $X billion — walk me through that calculation."
  → Test: Bottom-up AND top-down methodology ready
  
  "How does macro environment affect your business?"
  → Show: counter-cyclical elements, recession resilience
  
  "With AI advancing rapidly, is your product moat durable?"
  → Core question for AI era companies. Have strong answer.

VALUATION QUESTIONS:
  "At $X per share, you're trading at {multiple}x revenue.
   How do you justify that vs {comparable}?"
  → Have comp set. Know why you're premium.
  → "We trade at premium because NRR {pct}% vs comp {pct}%"
```

## BƯỚC 3 — ORDER BOOK TRACKING

```
/founder roadshow --track-orders

DAILY DEMAND DASHBOARD:
  Day {n} of 14

  ┌──────────────────────────────────────────────────┐
  │  ORDER BOOK STATUS — {date}                     │
  ├──────────────────┬───────────────────────────────┤
  │  Shares offered  │  {n}M shares                  │
  │  Orders in       │  {n}M shares                  │
  │  Coverage        │  {n}x oversubscribed          │
  │  Price signal    │  ${range} (vs $X-Y range)     │
  ├──────────────────┼───────────────────────────────┤
  │  QUALITY DEMAND  │                               │
  │  Long-only funds │  {pct}% of book               │
  │  Hedge funds     │  {pct}%                       │
  │  Retail          │  {pct}%                       │
  ├──────────────────┼───────────────────────────────┤
  │  TOP 10 ACCOUNTS │  {names} (tracked by bankers) │
  └──────────────────┴───────────────────────────────┘

ORDER QUALITY ANALYSIS:
  HIGH QUALITY: Long-only, large institutions, 3yr+ hold
  MED QUALITY: Long/short hedge funds, momentum players
  LOW QUALITY: Retail flippers, day traders

  Target: >60% high-quality demand at pricing
  
PRICING RECOMMENDATION:
  Current demand → suggested pricing range
  
  If 10x+ oversubscribed at top of range:
    Price at top or above range
    Upside to founders: {$delta per share × shares}
  
  If 3-5x at midpoint:
    Price at midpoint
    Conservative but stable post-IPO
  
  If < 2x:
    Delay or reprice
    NEVER price an undersubscribed IPO
```

## BƯỚC 4 — INVESTOR ALLOCATION STRATEGY

```
HOW TO ALLOCATE SHARES (with bankers):

RULES FOR FOUNDER-OPTIMAL ALLOCATION:
  □ 50-60% to long-term institutional investors
    (Fidelity, Vanguard, T. Rowe Price, BlackRock)
  □ 15-20% to growth/crossover funds
    (Tiger, Coatue, D1 — will add post-IPO too)
  □ 10-15% index funds (guaranteed buy on inclusion)
  □ 5-10% to strategic partners (customers, partners)
  □ 5% retail (goodwill, broader shareholder base)
  
  AVOID: Allocating too much to hedge funds
         → They flip = stock drops day 1 = bad headline

CORNER INVESTOR STRATEGY:
  Find 2-3 "anchor" investors pre-roadshow
  They commit early → signals quality → attracts others
  In exchange: larger allocation, slight price preference
```

## OUTPUT

```
✅ Roadshow Package Ready
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📁 .mekong/ipo/roadshow/
  ✓ deck-outline.md (20 slides)
  ✓ qa-simulation-session.md
  ✓ order-tracker-template.md
  ✓ allocation-strategy.md
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💳 MCU: -5 (balance: {remaining})

NEXT: /founder ipo-day (after pricing set)

RULE: First-day pop of 10-20% = good IPO.
      Pop > 50% = you left money on table.
      Drop day 1 = badly managed roadshow.
```
