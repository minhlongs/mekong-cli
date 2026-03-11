---
description: Cap table modeling — dilution across rounds, ownership %, ESOP impact
allowed-tools: Read, Write, Bash
---

# /founder cap-table — Dilution Intelligence Engine

## USAGE
```
/founder cap-table [--setup | --model-round | --scenario | --exit <amount>]
```

## BƯỚC 0 — LOAD CAP TABLE
```
IF .mekong/raise/cap-table.json tồn tại:
  Đọc current cap table
ELSE (--setup):
  Wizard thu thập:
    - Founders: name, shares, vesting status
    - Existing investors (nếu có): name, shares/%, round
    - Option pool: size, issued, available
    - Convertible notes (nếu có): amount, cap, discount
```

## SETUP WIZARD

```
Q1: Số founder và shares hiện tại?
    Founder 1: {name} — {shares} shares (___% vested)
    Founder 2: {name} — {shares} shares (___% vested)

Q2: Có convertible notes không?
    SAFE/Note amount: $___
    Valuation cap: $___M
    Discount: ___%
    MFN: yes/no

Q3: Option pool hiện tại?
    Total: ___%
    Issued: ___%
    Available: ___%

Q4: Có investors nào chưa?
    IF yes: name, amount, round, %

GENERATE: .mekong/raise/cap-table.json
```

## MODEL: --model-round

Mô phỏng một round mới:

```
INPUT:
  round_name     : Seed | Series A | Series B
  investment_amt : $___M
  pre_money_val  : $___M
  option_pool    : ___% (pre or post-money?)
  liquidation    : 1x non-part | 1x part | 2x
  
CALCULATE:

Step 1: Effective pre-money (option pool shuffle)
  IF option_pool == "pre-money":
    effective_pre = stated_pre - (new_pool_size × post_money_val)
    print: "⚠️ Option pool pre-money: your effective pre = ${effective_pre}M"
    print: "  (not ${stated_pre}M they're claiming)"

Step 2: Post-money valuation
  post_money = pre_money + investment

Step 3: New investor ownership
  investor_pct = investment / post_money

Step 4: Dilution of existing holders
  dilution_factor = 1 - investor_pct - new_option_pool_pct
  
  Everyone diluted by: {dilution_factor}%

Step 5: New cap table
  Founder 1: {old_pct} × dilution_factor = {new_pct}%
  Founder 2: {old_pct} × dilution_factor = {new_pct}%
  Prev investors: diluted proportionally
  New investor: {investor_pct}%
  Option pool: {pool_pct}%

OUTPUT TABLE:
  ╔═══════════════════════════════════════════════════╗
  ║ CAP TABLE — Post {round_name}                    ║
  ╠══════════════════╦════════╦════════╦═════════════╣
  ║ Holder           ║ Shares ║ Before ║ After       ║
  ╠══════════════════╬════════╬════════╬═════════════╣
  ║ Founder 1        ║ {n}    ║ 70%    ║ 52.5%       ║
  ║ Founder 2        ║ {n}    ║ 20%    ║ 15%         ║
  ║ Option Pool      ║ {n}    ║ 10%    ║ 17.5%       ║
  ║ New Investor     ║ {n}    ║ 0%     ║ 15%         ║
  ╠══════════════════╬════════╬════════╬═════════════╣
  ║ TOTAL            ║ {n}    ║ 100%   ║ 100%        ║
  ╚══════════════════╩════════╩════════╩═════════════╝
  
  Founder 1 dilution: 70% → 52.5% (-17.5pp)
  Implied value of Founder 1's stake: ${n}M
```

## SCENARIO: --scenario

Mô phỏng toàn bộ hành trình từ now → Series B:

```
FULL DILUTION JOURNEY — {company_name}

Stage        Round $   Pre $   Founder%  Founder Value
──────────────────────────────────────────────────────
Today        -         -       70.0%     ${current_val}M
Post-Seed    $2M       $8M     52.5%     ${n}M
Post-A       $8M       $20M    36.8%     ${n}M
Post-B       $20M      $60M    26.2%     ${n}M

If company sells at $100M:
  Founder gets: ${100M × 26.2% − liquidation_prefs}M

⚠️  WARNING THRESHOLDS:
  < 20%  after Series A = founder becoming minority
  < 10%  total = Zuckerberg territory (great if you're Zuckerberg)
  < 5%   = you're basically an employee with upside
  
FOUNDER DILUTION ACCELERATORS (watch these):
  □ Large option pool creations
  □ Bridge rounds (convert at discount = extra dilution)
  □ Anti-dilution triggers
  □ Employee equity grants from pool
```

## CONVERTIBLE NOTE ANALYSIS

```
IF SAFEs or notes exist, model conversion:

SAFE with $5M cap, 20% discount, $3M raise at $15M pre:

Scenario A: $15M pre > $5M cap → cap triggers
  SAFE converts at $5M pre (lower = better for SAFE holder)
  SAFE ownership: $500K / $5M = 10% 
  Founders think they raised at $15M, but SAFE converts at $5M
  → Surprise dilution

Scenario B: No cap, 20% discount
  SAFE converts at $15M × 80% = $12M effective pre
  SAFE ownership: $500K / ($12M + round) = {pct}%

MULTIPLE SAFEs MODEL:
  Show all SAFEs converting simultaneously at Series A
  Many founders surprised by how much multiple SAFEs dilute

RULE: Model all SAFE conversions BEFORE signing any priced round.
```

## EXIT: --exit <amount>

```
/founder cap-table --exit 50

Who gets what at $50M exit:

WATERFALL ANALYSIS:
  Step 1: Pay liquidation preferences (senior first)
    Series A: 1x pref = $2M → remaining: $48M
    Series Seed: 1x pref = $500K → remaining: $47.5M
  
  Step 2: Participating or convert?
    Series A (participating): takes another 15% × $47.5M = $7.1M
    Total Series A: $2M + $7.1M = $9.1M
    
  Step 3: Remaining to common
    $47.5M - $7.1M = $40.4M
    Founders (60% of common): $40.4M × 60% = $24.2M
    ESOP: $40.4M × 15% = $6.1M
  
  ╔═══════════════════════════════════╗
  ║ WHO GETS WHAT AT $50M EXIT       ║
  ╠══════════════════╦═══════════════╣
  ║ Series A VC      ║ $9.1M (18.2%) ║
  ║ Seed VC          ║ $2.8M (5.6%)  ║
  ║ Founder 1        ║ $18.2M        ║
  ║ Founder 2        ║ $6.0M         ║
  ║ ESOP             ║ $6.1M         ║
  ╚══════════════════╩═══════════════╝
  
  vs CLEAN TERMS (no participation):
  ║ Series A VC      ║ $7.5M         ║
  ║ Founder 1        ║ $20.6M  ← $2.4M more
  
  Difference: Participating preferred costs founders $2.4M at $50M exit
```

## OUTPUT

```
✅ Cap Table Model Ready
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📁 .mekong/raise/
  ✓ cap-table.json      ← current state
  ✓ round-model.md      ← dilution per round
  ✓ full-journey.md     ← seed → B journey
  ✓ exit-waterfall.md   ← who gets what
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💳 MCU: -3 (balance: {remaining})

BEFORE SIGNING:
  □ Run /founder term-sheet on actual document
  □ Run /founder cap-table --exit {expected_exit_val}
  □ Run /founder negotiate for counter-terms
  □ Show to startup lawyer
  
KEY INSIGHT: VCs model this for every deal.
Now you have the same model.
```
