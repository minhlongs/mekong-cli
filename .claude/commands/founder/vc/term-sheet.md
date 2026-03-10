---
description: Phân tích term sheet — tìm mọi trap, tính impact thực, so sánh với market standard
allowed-tools: Read, Write
---

# /founder term-sheet — Term Sheet Analyzer

## USAGE
```
/founder term-sheet --file <termsheet.pdf|.md> [--compare] [--simulate-exit]
```

**⚠️ Không phải tư vấn pháp lý. Thuê luật sư startup trước khi ký.**

## BƯỚC 0 — LOAD TERM SHEET
```
IF --file provided:
  Đọc file (PDF hoặc markdown)
ELSE:
  "Paste nội dung term sheet hoặc các điều khoản chính:"
  Đọc input

Đọc .mekong/raise/cap-table.json (nếu có) → current ownership
```

## BƯỚC 1 — EXTRACT KEY TERMS

**Agent: CFO / claude-sonnet-4-6 / 5 MCU** (dùng Sonnet vì độ chính xác quan trọng)

Parse và extract:

```
ECONOMIC TERMS:
  Valuation       : pre-money $___M | post-money $___M
  Investment      : $___M
  Ownership (new) : ___%
  
  Liquidation pref: ___x non-participating | ___x participating
  Anti-dilution   : broad-based WA | narrow-based WA | full ratchet
  Dividends       : ___% cumulative | non-cumulative | none
  
CONTROL TERMS:
  Board seats     : Founder ___ | Investor ___ | Independent ___
  Protective provisions: [list]
  Drag-along      : threshold ___% | who triggers
  Right of first refusal: yes/no | terms
  Co-sale rights  : yes/no | terms
  
FOUNDER TERMS:
  Vesting         : ___ years, ___ cliff
  Acceleration    : single trigger | double trigger | none
  Non-compete     : duration ___ | geography ___
  No-shop         : duration ___
  
OPTION POOL:
  Size            : ___%
  Pre or post-money: (critical — see analysis)
```

## BƯỚC 2 — TRAP DETECTION

**Each clause rated: 🟢 STANDARD | 🟡 WATCH | 🔴 DANGER**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CLAUSE ANALYSIS — {company_name} Term Sheet
VC: {vc_name} | Date: {date}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. VALUATION + OPTION POOL SHUFFLE
   Term: Pre-money $8M, $2M investment, 15% option pool
   
   Surface math: You think you're selling at $8M pre
   ACTUAL math:
     Option pool created BEFORE investment = dilutes founder
     Real pre-money (founder's perspective) = $8M - $1.2M pool = $6.8M
     Founder actual dilution: {calculated}%
   
   🔴 DANGER: Option pool pre-money shuffle
   Market standard: Negotiate option pool POST-money
   Impact: Founder gives up extra {n}% they didn't price in
   Counter: "Option pool to be created post-closing"

2. LIQUIDATION PREFERENCE
   Term: 1x participating preferred
   
   Non-participating (STANDARD): VC gets 1x back OR converts to common.
     They can't double dip.
   Participating (TRAP): VC gets 1x back AND participates in remaining.
   
   🔴 DANGER: "Participating preferred" = VC eats twice
   
   SIMULATION at $10M exit:
     Non-participating: VC=$2M, Founder=$8M × ownership
     Participating:     VC=$2M + ($8M × 20%) = $3.6M, Founder gets less
   
   Counter: "Non-participating preferred, or cap at 3x"
   
   IF 2x or higher liquidation pref:
   🔴🔴 EXTREME DANGER
     At 2x: VC needs $4M back before founder sees anything
     If company sells for $6M: VC=$4M, everyone else=$2M
     Common scenario: Founder works 5 years, exits $20M, VC takes $8M first

3. ANTI-DILUTION
   Broad-based weighted average: 🟢 STANDARD
     Only slightly adjusts VC price if down round
   
   Narrow-based weighted average: 🟡 WATCH
     More aggressive adjustment, can dilute founder more
   
   Full ratchet: 🔴🔴 EXTREME DANGER
     If next round price < this round → VC gets repriced to new price
     Founder gets massively diluted
     Example: Raise $2M at $10M pre. Next round $8M pre.
     Full ratchet: VC's $2M now acts like invested at $8M pre.
     Founder dilution: catastrophic
   
   Counter: "Broad-based weighted average anti-dilution only"

4. BOARD CONTROL
   Term: 2 investor seats, 1 founder seat, 1 independent
   
   🔴 DANGER: Investor majority on board
   
   Board 2-1-1: VC controls 2 votes + independent (often VC-friendly)
   = VC can fire founder, block M&A, force decisions
   
   Market standard at Seed: 2 founders, 1 investor
   Market standard at Series A: 2 founders, 2 investors, 1 independent
   
   Counter: "Equal board until Series B. Founder + VC + neutral party."
   Counter: "Independent director selected by mutual agreement"

5. DRAG-ALONG
   Term: Drag-along at majority of preferred
   
   🟡 WATCH: Who triggers drag-along matters enormously
   
   Bad: "Majority of preferred can drag common" 
     = VC can sell company, drag founder along
   Better: "Majority of preferred AND majority of common"
     = Both sides must agree to sell
   Best: "Including majority of common" + minimum price threshold
   
   Counter: "Drag-along requires majority of common shareholders"
   Counter: "Minimum return threshold of 2x for drag to trigger"

6. FOUNDER VESTING RESET
   Term: Founders re-vest from closing
   
   🔴 DANGER if: Founder has been building 2 years, then re-vests from zero
   
   Market standard: Founders get credit for time worked
   Example: 2 years worked = 50% already vested immediately at close
   
   Counter: "Founders credit for {n} months of prior service"

7. PAY-TO-PLAY
   Term: Pay-to-play provision
   
   🟢 STANDARD (actually founder-friendly when used correctly)
   Forces VC to participate in future rounds or lose anti-dilution/preferences
   
   But check: Does it apply to founders' shares too?
   If yes: 🟡 WATCH

8. NO-SHOP
   Term: 45-day exclusivity
   
   🟡 WATCH
   Standard: 30 days is plenty
   45+ days = VC can string you along, kill other deals
   
   Counter: "30 days maximum with good faith milestones"

9. INFORMATION RIGHTS
   Term: Monthly financials, annual audit
   
   🟢 STANDARD
   Watch for: "Board observer rights" given to too many people
   = Confidentiality risk if strategic info gets out

10. NON-COMPETE
    Term: 2-year non-compete in same industry
    
    🟡 WATCH
    Market standard: 1 year, narrowly defined
    2+ years in broad industry = founder trapped
    
    Counter: "1 year, limited to direct competitive products"
    Note: Non-compete enforceability varies by country
```

## BƯỚC 3 — EXIT SIMULATION

```
/founder term-sheet --simulate-exit

Input: valuation scenarios (pessimistic | base | optimistic)

For each scenario, calculate who gets what:

SCENARIO: $5M exit (below expectations)
  VC investment: $2M at 20% ownership, 1x non-participating pref
  
  VC gets: max(1x pref, 20% × $5M) = max($2M, $1M) = $2M (takes pref)
  Founders get: $5M - $2M = $3M × founder% of common = ${n}

SCENARIO: $5M exit with PARTICIPATING preferred
  VC gets: $2M (pref) + 20% × ($5M - $2M) = $2M + $600K = $2.6M
  Founders get: $5M - $2.6M = $2.4M × founder% = ${n}
  DIFFERENCE: ${delta} less for founder vs non-participating

SCENARIO: $20M exit
  Non-participating:
    VC: max($2M, 20% × $20M) = max($2M, $4M) = $4M (converts)
    Founders: $16M × founder%
  
  Participating:
    VC: $2M + 20% × $18M = $2M + $3.6M = $5.6M
    Founders: $20M - $5.6M = $14.4M × founder%

SCENARIO: $100M exit (success case)
  (participation becomes less impactful at high exits)

TABLE:
  Exit Value   Non-Part VC  Part VC   Founder Δ
  $5M          $2.0M        $2.6M     -$0.6M
  $20M         $4.0M        $5.6M     -$1.6M
  $50M         $10M         $13.6M    -$3.6M
  $100M        $20M         $26M      -$6M
```

## BƯỚC 4 — NEGOTIATION BRIEF

```
FILE: .mekong/raise/term-sheet-negotiation.md

MUST FIX (walk away if not changed):
  🔴 {clause}: "{current}" → demand "{counter}"
  🔴 {clause}: ...

SHOULD FIX (negotiate hard):
  🟡 {clause}: "{current}" → propose "{counter}"

CAN LIVE WITH:
  🟢 {clause}: standard, accept

NEGOTIATION SEQUENCE:
  1. Fix option pool timing first (highest economic impact)
  2. Fix liquidation preference (non-participating)
  3. Fix board composition (founder-friendly)
  4. Fix drag-along trigger
  5. Relax non-compete scope

LEVERAGE YOU HAVE:
  □ {other investors interested? use as leverage}
  □ {current revenue/traction = less need for money}
  □ {alternative financing available?}

WHAT VC WANTS (use against them):
  □ VCs need to deploy capital — empty fund = no carry
  □ Competitive deals = fear of missing out
  □ Your traction = they need you more than you need them
  
LINES TO USE IN NEGOTIATION:
  "We spoke to {n} lawyers and this participation clause
   isn't standard for a seed round at our stage."
  
  "We have another term sheet. We'd prefer to work with you
   but need this term to match."
  
  "I've modeled the exit scenarios. With participation,
   my incentive to grow past $20M drops significantly.
   That's not aligned with your fund returns either."
```

## OUTPUT

```
✅ Term Sheet Analysis Complete
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OVERALL VERDICT: {FOUNDER-FRIENDLY / STANDARD / CONCERNING / PREDATORY}

🔴 MUST FIX: {n} clauses
🟡 SHOULD FIX: {n} clauses  
🟢 ACCEPTABLE: {n} clauses

Economic impact of traps found:
  At $20M exit: you lose ${n} vs clean term sheet
  At $50M exit: you lose ${n} vs clean term sheet

📁 .mekong/raise/
  ✓ term-sheet-analysis.md
  ✓ term-sheet-negotiation.md
  ✓ exit-simulation.md
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💳 MCU: -5 (balance: {remaining})

⚠️  MANDATORY: Share analysis with startup lawyer before responding to VC.
    Vietnam: LNT & Partners, VILAF, Vision & Associates
    US: Gunderson, Cooley, Wilson Sonsini
    Singapore: Rajah & Tann, WongPartnership
```
