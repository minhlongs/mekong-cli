---
description: 18-month IPO readiness audit — financials, governance, legal, ops, narrative
allowed-tools: Read, Write, Bash
---

# /founder pre-ipo-prep — IPO Readiness Engine

## USAGE
```
/founder pre-ipo-prep [--timeline <months>] [--exchange nasdaq|nyse|hose|hkex] [--audit]
```

## BƯỚC 0 — SCAN
```
□ Đọc .mekong/company.json       → all company data
□ Đọc .mekong/reports/ (latest)  → MRR, growth, metrics
□ Đọc .mekong/raise/cap-table.json → current ownership structure
□ Đọc .mekong/legal/              → legal structure
```

## IPO READINESS SCORE (1-100)

**Agent: CFO + COO + CTO / sonnet + local / 5 MCU**

```
CATEGORY 1: FINANCIAL READINESS (30 points)
  □ 2+ years audited financial statements (PCAOB audit)     [0-10]
  □ Revenue recognition compliant (ASC 606 / IFRS 15)      [0-5]
  □ Internal controls (SOX 404 readiness)                   [0-10]
  □ CFO with public company experience                      [0-5]
  Score: ___/30

CATEGORY 2: BUSINESS METRICS (25 points)
  □ Revenue growth > 30% YoY                               [0-10]
  □ Gross margin > 60% (SaaS) / > 40% (other)             [0-5]
  □ Rule of 40 > 40 (growth% + profit%)                    [0-5]
  □ NRR > 110% (Net Revenue Retention)                     [0-5]
  Score: ___/25

CATEGORY 3: GOVERNANCE (20 points)
  □ Board: majority independent directors                   [0-8]
  □ Audit committee (3 independent, 1 financial expert)    [0-4]
  □ Comp committee (2+ independent)                        [0-4]
  □ D&O insurance in place                                 [0-4]
  Score: ___/20

CATEGORY 4: LEGAL + COMPLIANCE (15 points)
  □ Delaware C-corp (or equivalent)                        [0-3]
  □ Clean cap table (no messy convertibles)                [0-3]
  □ IP ownership clean (all assignments done)              [0-3]
  □ No material litigation                                 [0-3]
  □ Data privacy compliance (GDPR, etc.)                   [0-3]
  Score: ___/15

CATEGORY 5: OPERATIONS (10 points)
  □ Financial close < 10 business days                     [0-5]
  □ Reporting systems scalable for quarterly requirements  [0-3]
  □ IR function or readiness                               [0-2]
  Score: ___/10

TOTAL: ___/100

VERDICT:
  80-100: IPO-ready, proceed to banker selection
  60-79:  6-12 months to ready
  40-59:  12-18 months to ready
  < 40:   18+ months, major gaps to address
```

## 18-MONTH IPO PREPARATION TIMELINE

```
MONTH T-18 TO T-12: FOUNDATION

  Finance:
  □ Hire CFO with public company experience
  □ Engage Big 4 auditor (E&Y, KPMG, Deloitte, PwC)
  □ Begin historical financial statement audit
  □ Implement ERP system (NetSuite, SAP) if not done
  □ Revenue recognition review + restatement if needed

  Legal:
  □ Convert to Delaware C-Corp if not already
  □ Clean cap table: resolve all convertible notes
  □ IP audit: ensure all code/IP owned by company
  □ Litigation review + clean up

  Governance:
  □ Recruit 2-3 independent board directors
    (look for: CFO of public co, CEO of public co, subject expert)
  □ Form audit committee, comp committee, nominating committee
  □ Implement D&O insurance (start before going public)
  □ Draft committee charters

MONTH T-12 TO T-6: READINESS

  Finance:
  □ Audited financials: years 1, 2, 3 (or YTD)
  □ Quarterly financials audited (or reviewed)
  □ SOX readiness assessment (internal controls)
  □ Financial close process: target < 10 business days

  Business:
  □ Define and validate key metrics for S-1
    (ARR, NRR, DAU, cohort retention — whatever tells your story)
  □ Unit economics fully documented
  □ Customer concentration analysis
    (no single customer > 10% revenue for clean IPO)

  IR Preparation:
  □ Hire IR firm or VP IR
  □ Develop investor story + key messages
  □ Start analyst outreach (buy-side + sell-side)
  □ Competitive positioning document

MONTH T-6 TO T-3: SELECTION

  □ Select investment bankers (/founder banker)
  □ Select securities counsel (IPO-specialist)
  □ Select accounting firm (if switching)
  □ File confidential S-1 (Testing the Waters — US)
  □ Pre-IPO institutional investor meetings (testing narrative)
  □ Determine exchange: NASDAQ vs NYSE vs HoSE vs HKEX

MONTH T-3 TO T-0: EXECUTION

  □ Finalize S-1 / prospectus (/founder s1)
  □ File public S-1
  □ SEC/regulatory comment period
  □ Roadshow (/founder roadshow)
  □ IPO pricing (/founder pricing-ipo)
  □ LISTING (/founder ipo-day)
```

## EXCHANGE SELECTION GUIDE

```
NASDAQ:
  Requirements: $5M net income OR $750M revenue OR $110M revenue + cash
  Listing fee: ~$150K-$300K
  Best for: Tech companies, AI, SaaS
  Tier: NASDAQ Global Select Market (top tier)
  Prestige: Where Apple, Google, Microsoft, Meta listed
  
NYSE:
  Requirements: $10M net income or $750M revenue
  Listing fee: ~$250K-$500K
  Best for: Traditional, financial, large cap
  Prestige: Older brand, NYSE bell = iconic

HoSE (Vietnam Stock Exchange):
  Requirements: VND 300B charter capital, 2yr profitable
  Listing fee: much lower
  Best for: Vietnam-focused businesses, domestic investors
  Consideration: Limited liquidity vs US markets
  
HNX (Hanoi Stock Exchange):
  Requirements: Lower than HoSE
  Best for: SME, startup friendly path
  UpCOM → HNX → HoSE migration path

HKEX (Hong Kong):
  Requirements: Market cap HK$200M+ 
  Best for: SEA companies wanting Asia liquidity
  Consideration: Post-2021 regulatory risk

RECOMMENDATION LOGIC:
  Global AI/SaaS + US customers → NASDAQ
  Vietnam-focused + domestic → HoSE after 3yr profitability
  SEA + Asian investors → HKEX
  Dual listing: possible after 2yr as public company
```

## READINESS GAP ANALYSIS

```
FILE: .mekong/ipo/readiness-gaps.md

Generated from score assessment:

CRITICAL GAPS (fix before IPO):
  ❌ No audited financials → Engage Big 4 immediately
     Timeline: 6-9 months | Cost: $500K-$2M/year
  
  ❌ No independent board → Recruit 2-3 directors
     Timeline: 3-6 months | Cost: $100K-$300K in equity/cash
  
  ❌ Revenue recognition issues → Hire technical accounting
     Timeline: 3-6 months | Risk: restatement if IPO reveals

MODERATE GAPS (fix before S-1 filing):
  ⚠️  SOX compliance → Internal audit function
  ⚠️  Customer concentration → Diversify before IPO
  ⚠️  IP gaps → Clean up before legal review

MINOR GAPS (fix before roadshow):
  ~ D&O insurance → Get immediately
  ~ IR readiness → Hire VP IR or agency
```

## OUTPUT

```
✅ IPO Readiness Assessment Complete
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
IPO Readiness Score: {score}/100
Status: {READY / {n} MONTHS TO READY}

Critical gaps: {n}
Months to address: {n}
Estimated prep cost: ${range}

📁 .mekong/ipo/
  ✓ readiness-score.md
  ✓ readiness-gaps.md
  ✓ 18-month-timeline.md
  ✓ exchange-analysis.md
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💳 MCU: -5 (balance: {remaining})

NEXT: /founder banker (when score > 70)
```
