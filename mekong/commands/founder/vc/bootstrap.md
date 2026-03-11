---
description: Bootstrap vs raise decision — ramen profitability calculator, bootstrap playbook
allowed-tools: Read, Write, Bash
---

# /founder bootstrap — Independence Calculator

## USAGE
```
/founder bootstrap [--target <mrr>] [--runway <months>] [--model]
```

## PHILOSOPHY

```
Tại sao bootstrap trước?
  
  Với traction: raise từ thế mạnh, không từ thế yếu
  Không cần raise: best leverage = "we don't need your money"
  
  Indie Hackers case studies:
    Basecamp: $100M+ ARR, 0 VC, 57 employees
    Mailchimp: $700M exit, 0 VC (acquired by Intuit for $12B later)
    Notion: raised but only AFTER $1M ARR
    Linear: $35M ARR before raising
    
  Vietnam case:
    Bootstrapped to $100K ARR → raise at $10M pre
    vs
    Raised $500K at $2M pre → give away 20% for cheap
```

## BƯỚC 0 — SCAN
```
□ Đọc .mekong/company.json      → product_type, stage
□ Đọc .mekong/reports/ (latest) → current MRR, costs
□ Đọc .mekong/mcu_balance.json  → operational costs
```

## BƯỚC 1 — RAMEN PROFITABILITY CALCULATOR

**Agent: CFO / local / 1 MCU**

```
RAMEN PROFITABLE = MRR covers founder's minimum survival costs

INPUTS (ask if not in company.json):
  Monthly personal expenses: $___
    (rent + food + utilities + insurance minimum)
  
  Monthly business expenses: $___
    (server, tools, API costs — AgencyOS example: ~$65/mo)
  
  Founder salary needed: $___/mo minimum

CALCULATE:
  ramen_mrr_target = personal_expenses + business_expenses + founder_salary
  
  At AgencyOS pricing ($49 starter):
    Users needed for ramen: {ramen_mrr / 49} users
    
  At AgencyOS growth tier ($149):
    Users needed: {ramen_mrr / 149} users
    
  Breakeven timeline at current growth: {months}
  
  RAMEN MRR TARGET: ${ramen_mrr}/mo
  USERS NEEDED: {n} paying customers
  TIME TO RAMEN: {weeks} at current growth rate

┌─────────────────────────────────────────────┐
│  RAMEN CALCULATOR — {company_name}         │
├──────────────────┬──────────────────────────┤
│  Personal costs  │  ${personal}/mo          │
│  Business costs  │  ${business}/mo          │
│  Buffer (20%)    │  ${buffer}/mo            │
├──────────────────┼──────────────────────────┤
│  RAMEN TARGET    │  ${total}/mo MRR         │
│  Users needed    │  {n} at ${avg_price}/mo  │
│  Time estimate   │  {n} weeks               │
└──────────────────┴──────────────────────────┘
```

## BƯỚC 2 — BOOTSTRAP PATH TO $1M ARR

```
FILE: .mekong/founder/bootstrap-plan.md

$1M ARR = $83K MRR
Let's reverse-engineer this without VC:

MONTH-BY-MONTH TARGETS:
  M1:  $1K MRR  → 20 users  → focus: product + 1 channel
  M3:  $5K MRR  → 100 users → focus: retention + 1 growth channel
  M6:  $15K MRR → 300 users → focus: word of mouth kicks in
  M9:  $35K MRR → 700 users → focus: sales + content compound
  M12: $83K MRR → 1,700 users → $1M ARR

BOOTSTRAP-SPECIFIC STRATEGIES:

1. CHARGE FROM DAY 1
   Never "free until we figure it out"
   Even $1 validates willingness to pay
   AgencyOS: MCU credits = pay-as-you-go = low friction to start
   
2. ANNUAL PLANS EARLY
   Annual = 1 month free = 17% discount
   Annual plan collected upfront = instant cash flow boost
   10 annual customers × $588 ($49 × 12) = $5,880 upfront
   
3. SERVICES BRIDGE
   If product slow to monetize → sell consulting using your tool
   "I'll setup and run AgencyOS for your company for $2K/mo"
   Revenue now + product validation + case study
   
4. LIFETIME DEALS (one-time)
   LTD AppSumo: $89-249 one-time, 1-3K buyers typical
   AgencyOS LTD at $149: 1,000 buyers = $149K upfront
   Tradeoff: give away future sub revenue but get cash now
   Rule: do LTD only if < 6 months runway
   
5. CONTENT COMPOUNDING
   Blog post ranks → free users → some convert → MRR
   Takes 6-12 months but then runs forever
   Most bootstrapped companies built on SEO + word of mouth
   
6. NICHE THEN EXPAND
   AgencyOS: start with "solo AI developers" → expand to "solo founders"
   Niche = easier to reach, better conversion, lower CAC
   Expand after $10K MRR

BOOTSTRAP UNIT ECONOMICS TARGET:
  CAC: < $50 (1-month payback)
  LTV: > $500 (10+ months average subscription)
  LTV:CAC ratio: > 10:1
  Gross margin: > 70%
  
  AgencyOS target:
    CAC (content/organic): $20-30
    LTV (6mo avg at $49): $294
    LTV:CAC: ~12:1 ✓
```

## BƯỚC 3 — WHEN TO RAISE (if ever)

```
RAISE IF AND ONLY IF all of these are true:
  □ MRR > $25K (have real product-market fit)
  □ Growth rate > 15% MoM (momentum to show)
  □ Specific use case for capital (hiring, paid acquisition that works)
  □ Valuation > $10M pre (you're not giving away too much)
  □ You've tried to grow organically and hit a real ceiling
  □ You have BATNA (another offer or can stay bootstrapped)

DO NOT RAISE IF:
  ✗ "We'll figure out monetization after"
  ✗ MRR < $10K (pre-PMF money is expensive)
  ✗ You just want validation (that's therapy, not fundraising)
  ✗ Runway > 18 months (you don't need it yet)
  ✗ No competing term sheet (negotiate blind = lose)

ALTERNATIVE FUNDING SOURCES (not VC):
  Revenue-based financing: Capchase, Clearco (repay from revenue %)
  Startup grants: Innovate UK, NSF SBIR (US), DOST (PH), Vintech (VN)
  Strategic angels: customers who invest = aligned incentives
  Accelerators: YC, Techstars = money + network, better than blind VC
  Founder debt: bootstrap with personal savings, repay from MRR
```

## BƯỚC 4 — ALTERNATIVES DATABASE

```
/founder bootstrap --model (shows cost to stay independent)

REVENUE-BASED FINANCING:
  Capchase.com: advance 6-12mo of ARR at 6-8% fee
    Example: $100K ARR → $50-80K now → repay from monthly revenue
    Requirement: $50K+ ARR, positive growth
  
  Clearco.com: same model, focus on e-commerce/SaaS
  
  Pipe.com: trade annual contracts for upfront cash
    Example: 10 annual customers @ $588 = $5,880/yr
    Pipe advances you $5,500 now, takes monthly payments

GRANTS (free money, no dilution):
  Vietnam:
    Quỹ Đổi mới sáng tạo (NATIF): up to $100K for tech
    Vietnam Innovation Challenge: grants for AI/tech
    VINTECH: VinGroup startup program
  
  US (if incorporated):
    SBIR/STTR: up to $1.5M for tech/AI, non-dilutive
    NSF Grants: research-based tech
  
  Global:
    Google for Startups: $100K cloud credits
    AWS Activate: $100K credits
    Anthropic Startup: $10K API credits
    (see /credits for full list)

ACCELERATORS (smart money):
  YC: $125K for 7% — best network in world
  Pioneer: $8K-$50K — good for early solo founders
  Antler: $100K, 10% — hiring co-founder focus
  
  Vietnam/SEA:
    VIISA: local market, VND funding
    Do Ventures portfolio programs
    Grab Ventures Velocity

STRATEGIC INVESTORS (aligned > financial):
  Customers who invest = product advocates + revenue
  Partners who invest = distribution built in
  Angels who were founders = actual advice
```

## OUTPUT

```
✅ Bootstrap Intelligence Ready
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 RAMEN TARGET: ${ramen_mrr}/mo ({n} users)
📈 $1M ARR PATH: {n} months at current growth
💪 RAISE THRESHOLD: ${raise_mrr}MRR (you're at ${current_mrr})

📁 .mekong/founder/
  ✓ bootstrap-plan.md
  ✓ alternatives.md
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💳 MCU: -1 (balance: {remaining})

BOTTOM LINE:
  Bootstrap to ${raise_threshold} MRR first.
  Then raise with BATNA.
  Every dollar of revenue = $3-10 off valuation they're negotiating.
```
