---
description: Founder liquidity mechanics — secondary sales, tender offers, SPV, tax optimization
allowed-tools: Read, Write
---

# /founder secondary — Founder Liquidity Intelligence

## USAGE
```
/founder secondary [--amount <usd>] [--stage <round>] [--tax-optimize]
```

## PHILOSOPHY

```
"Taking money off the table" bị VC stigmatize — sai hoàn toàn.

Tại sao founder SHOULD take some liquidity:
  1. Concentration risk: 100% net worth trong 1 startup = gambling
  2. Cognitive load: "Nhà sắp mất" founder không make good decisions
  3. Long game: founder có $2M bank takes bigger product swings
  4. Family: spouse/parents pressure disappears = founder focus
  5. Alignment signal: founder who "proved it" with own liquidity
     still running shows conviction, not desperation

Industry standard:
  Series B+: founder 10-20% of round as secondary is normal
  Pre-IPO: founder 15-30% as tender offer is standard
  
VC who says "no secondary ever" = bad partner, misaligned incentive
```

## MECHANISMS

### 1. SECONDARY IN FINANCING ROUND (most common)

```
How: New investor buys existing shares from founder
     alongside primary (new shares) investment

WHEN: Series B+ is the typical earliest
AMOUNT: Standard = 10-20% of total round size

Example:
  Series B: $30M total round
  Primary: $25M (new shares, goes to company)
  Secondary: $5M (founder sells existing shares)
  
  VC preference: primary only (money to company)
  Founder preference: some secondary
  
  NEGOTIATION SCRIPT (add to /founder negotiate):
  "We're excited about this partnership. One element important
   to us is a small secondary component — $3-5M — which lets
   us focus completely on building without personal financial
   pressure. This is standard at Series B and aligns our
   long-term incentives to build a category-defining company."
  
  Common VC objections + counters:
  "Sending wrong signal" →
    "Less than 10% of round is standard. LinkedIn, Facebook,
     Airbnb founders all did this. It removes distraction."
  
  "We want all capital to company" →
    "We can structure it as separate secondary transaction.
     Or we can bring in a secondary buyer alongside."

MODELING SECONDARY IMPACT:
  IF founder sells $5M of shares at Series B ($200M valuation):
    Founder sells: $5M / $200M = 2.5% of company
    Remaining stake: {current%} - 2.5% = {new%}
    BUT: $5M in bank = massive BATNA for all future rounds
    
  TAX (US - consult accountant):
    Shares held > 1 year = long-term capital gains (15-20%)
    Shares held < 1 year = ordinary income (37%+)
    QSBS: if eligible, up to $10M gain tax-free federally
```

### 2. TENDER OFFER

```
HOW: Company (with VC backing) offers to buy shares from
     all shareholders including founders + early employees

TYPICAL STAGE: Pre-IPO, late Series C/D

EXAMPLE:
  Company at $1B valuation
  Tender offer at $500M valuation (50% discount) OR
  Tender offer at $800M (20% discount)
  
  Why discount: liquidity premium — employees/founders
    accept lower price for certainty
    
FOUNDER STRATEGY:
  □ Sell minimum needed to derisk personal finances
  □ Keep maximum for IPO upside
  □ Calculate: what amount in bank lets me sleep well?
    That's the secondary target.
  
TENDER OFFER CHECKLIST:
  □ 10b5-1 plan (US): pre-planned trading = legal safe harbor
  □ Board approval required
  □ Securities counsel review
  □ Employee communications (are employees included too?)
  □ Price negotiation (tender price vs last round price)
```

### 3. SPV SECONDARY (Special Purpose Vehicle)

```
HOW: Third party creates SPV, raises money from LPs,
     SPV buys shares from founder

TYPICAL: When VC doesn't want secondary in round
         but market exists for founder shares

PLATFORMS:
  Forge Global: forge.com (pre-IPO marketplace)
  CartaX: carta.com/secondary
  EquityZen: equityzen.com
  Nasdaq Private Market

PROCESS:
  1. Check ROFR (right of first refusal) in shareholder agreement
     - Company or existing investors typically have ROFR
     - Must offer to them first at same price
  2. If ROFR waived → find buyer (platform or direct)
  3. Transfer approval from company
  4. Close transaction

PRICING:
  Secondary market price = function of:
    Last round price × discount (10-40%) for:
      - Illiquidity premium
      - Uncertainty of exit timing
      - Deal size (larger = more discount)
```

### 4. PERSONAL LIQUIDITY OPTIMIZATION

**Agent: CFO / local / 1 MCU**

```
TAX OPTIMIZATION STRATEGIES:

QSBS (US Qualified Small Business Stock):
  IF: C-corp + < $50M assets at issuance + hold > 5 years
  BENEFIT: $10M gain excluded from federal tax
  ACTION: Ensure 83(b) election filed within 30 days of grant
  
  Example: Founder sells $10M of shares with QSBS = $0 federal tax
           vs normal = $2M+ tax. HUGE.

83(b) ELECTION (US):
  File within 30 days of receiving restricted shares
  Pays tax on CURRENT value (likely $0 or minimal)
  ALL future appreciation = capital gains, not income
  
  Missing 83(b) = one of the most expensive founder mistakes ever

INSTALLMENT SALE:
  Spread large secondary gain over multiple years
  = lower effective tax rate

CHARITABLE GIVING:
  Give appreciated shares to DAF (donor-advised fund)
  = deduct full market value, avoid capital gains
  = charity wins, founder wins, VC can't complain

GEOGRAPHY (for non-US founders):
  Singapore: 0% capital gains tax
  Vietnam: 20% capital gains on stock sales (ưu đãi startup)
  Check: residency at time of sale determines tax home
```

## CALCULATOR

```
/founder secondary --amount 3000000 --tax-optimize

SECONDARY ANALYSIS — $3M

At Series B ($150M pre-money):
  Shares to sell: $3M / ($150M / total_shares) = {n} shares
  % sold: {n}%
  Remaining stake: {current%} - {sold%} = {remaining%}

TAX SCENARIOS (US):
  Standard (LT capital gains): $3M × 20% = $600K tax
                                Net proceeds: $2.4M
  
  QSBS eligible:               $3M × 0% = $0 tax
                                Net proceeds: $3M
  
  Missing 83(b):               $3M × 37% = $1.11M tax
                                Net proceeds: $1.89M
  
  Delta QSBS vs no-83b: $1.11M saved by filing 1 form

NET WORTH DIVERSIFICATION AFTER:
  Before: 95% startup equity, 5% cash
  After:  {n}% startup equity, {n}% liquid
  
  RECOMMENDATION: {agent assessment of optimal amount}
```

## OUTPUT

```
✅ Liquidity Analysis Ready
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📁 .mekong/raise/liquidity/
  ✓ secondary-options.md
  ✓ tax-scenarios.md
  ✓ negotiation-script.md
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💳 MCU: -2 (balance: {remaining})

⚠️  Tax advice requires CPA + securities attorney.
    Mekong provides framework, professionals execute.
```
