# Algo-Trader — /idea 25-Step Company Architecture

**Date:** 2026-03-19
**Stage:** Zero→PSF (No paying customers, hypothesis stage)
**Target:** $1M ARR by GTM 2026

---

## Executive Summary

**Algo-Trader** is an AI-powered multi-exchange crypto arbitrage engine targeting institutional traders and DeFi funds in Asia. Revenue model: SaaS subscription + performance fees.

---

## Phase 1: Foundation (Steps 0-4)

### 1. Master Framework

| Layer | Algo-Trader Application |
|-------|------------------------|
| **[Business]** | SaaS B2B targeting institutional crypto traders, DeFi funds, family offices in SEA |
| **[Agentic]** | Trading agents (arb detection, execution, risk), P&L analytics, auto-rebalancing |
| **[Governance]** | Compliance (SEC, CFTC, MAS), audit trails, risk controls, AML/KYC integration |

### 2. Refactor to 2026 Frame

Existing codebase: Modular arbitrage engine with CCXT integration, backtesting, RSI/SMA strategies.
Modernization needed: Multi-tenant SaaS, MCU metering, Polar.sh billing, compliance layer.

### 3. Agentic OS Design

| Agent | Role | Automation % |
|-------|------|--------------|
| Trading Agent | Spread detection, execution across Binance/OKX/Bybit | 80% |
| Risk Agent | Position limits, drawdown stops, exposure monitoring | 90% |
| P&L Agent | Real-time performance tracking, reporting | 95% |
| Compliance Agent | Trade validation, regulatory checks | 70% |
| Ops Agent | Infrastructure monitoring, alerting | 85% |

**Target Automation:** 85% by Q4 2026

### 4. IPO Readiness Score (VN/SEA Compliance)

| Requirement | Status | Timeline |
|-------------|--------|----------|
| Corporate Structure (SG/Cayman) | Missing | Month 3 |
| AML/KYC Integration | Missing | Month 4 |
| Audit Trail (Trade Logs) | Partial | Month 2 |
| Regulatory Licenses (MAS) | Missing | Month 12 |
| Financial Reporting | Missing | Month 6 |

**Current Score:** 2/10 → **Target Month 12:** 8/10

### 5. Gap Report + Roadmap

**6-Month Action Plan:**

| Month | Focus | Deliverables |
|-------|-------|--------------|
| 1-2 | MVP Hardening | Multi-exchange live trading, basic P&L dashboard |
| 3-4 | SaaS Layer | Auth, billing, multi-tenant architecture |
| 5-6 | Compliance | AML/KYC, audit logging, risk reporting |

---

## Phase 2: Business Model (Steps 5-6)

### 6. Business Model Patterns

**Archetype:** SaaS B2B + Performance Fee (2/20 model adapted for crypto)

**Unit Economics:**

| Metric | Target |
|--------|--------|
| ARPU | $2,000/mo (Pro), $10,000/mo (Institutional) |
| LTV | $72,000 (36 mo retention) |
| CAC | $5,000 (enterprise sales cycle) |
| Payback | 3-4 months |
| Gross Margin | 85% (cloud infra ~15%) |

**Revenue Streams:**
1. SaaS Subscription: $499-$10,000/mo tiers
2. Performance Fee: 10-20% of profits above benchmark
3. Enterprise License: Custom pricing for funds

### 7. Customer Psychology + Personas

**ICP (Ideal Customer Profile):**

| Segment | Profile | Pain Points |
|---------|---------|-------------|
| **Crypto Funds** | $10M-100M AUM, 5-20 person teams | Manual arb tracking, missed opportunities, no unified P&L |
| **DeFi Protocols** | Treasury management teams | Yield optimization across CEX/DEX, slippage control |
| **Family Offices** | Asia-based, crypto-allocated | Institutional-grade execution, compliance reporting |
| **Prop Trading Firms** | Existing infra, seeking alpha | Low-latency execution, risk controls |

**Jobs-to-be-Done:**
- "Capture spread opportunities across exchanges automatically"
- "Know my real P&L across all positions 24/7"
- "Stay compliant with trade reporting requirements"

**Decision Triggers:**
- ROI proof (backtest results, paper trading)
- Security audit (SOC2, custody solution)
- Integration with existing stack (custodians, prime brokers)

---

## Phase 3: Brand + Content (Steps 7-11)

### 8. Brand Positioning

**Unique Value Proposition:** "Institutional-grade crypto arbitrage, automated."

**Category Design:** AI Trading Infrastructure (not just a bot — a platform)

**Competitive Moat:**
- Multi-exchange execution (Binance, OKX, Bybit, future: DEXs)
- Sub-100ms latency arbitrage detection
- Compliance-first architecture (audit trails, reporting)
- AI-driven strategy optimization

### 9. Content Pillars + TOF

**SEO Pillars:**
1. "Crypto Arbitrage Strategies" (high-volume, educational)
2. "Institutional Crypto Trading" (buyer intent)
3. "Multi-Exchange Trading Bots" (solution-aware)
4. "Crypto P&L Tracking" (pain-point)

**Content Cadence:** 2 posts/week (technical deep dives + case studies)

### 10. Website/Landing Narrative

**Conversion Structure:**
```
Hero: "Capture crypto arbitrage opportunities 24/7"
  ↓
Problem: "Manual trading misses spreads. Single-exchange bots leave alpha on table."
  ↓
Solution: "AI-powered multi-exchange arbitrage with institutional P&L tracking"
  ↓
Proof: Backtest results, paper trading stats, security audits
  ↓
CTA: "Start Paper Trading →" (free) | "Book Demo" (enterprise)
```

### 11. Performance Ads + Creatives

**Channels:**
- LinkedIn (CFOs, fund managers, family offices)
- Twitter/X (crypto trader community)
- Google Search (high-intent: "crypto arbitrage bot")

**Ad Framework:**
| Angle | Creative | CTA |
|-------|----------|-----|
| ROI Proof | "Our arb bot captured 47% APY last quarter" | "See Backtest →" |
| FOMO | "While you sleep, our AI finds 12 arb opportunities/night" | "Start Free Trial →" |
| Security | "SOC2-ready, audit-logged, institutional custody" | "Book Security Review →" |

**Budget:** $10K/mo months 3-6, scale to $30K/mo by month 9

### 12. Advertorial + Storytelling

**Case Study Template:**
```
Title: "How [Fund X] Captured 34% APY with Multi-Exchange Arbitrage"
Hook: Fund was missing spread opportunities across 3 exchanges
Solution: Deployed Algo-Trader with custom risk params
Result: +34% APY, 2hr/day time savings, automated compliance
```

---

## Phase 4: Revenue Engine (Steps 12-14)

### 13. Email + Lifecycle Sequences

| Sequence | Trigger | Emails | Goal |
|----------|---------|--------|------|
| Onboarding | Sign up | Day 0, 2, 5, 10 | First paper trade |
| Activation | First trade | Day 0, 3, 7 | Fund account, go live |
| Nurture | Inactive 7d | Day 7, 14, 21 | Re-engage with new features |
| Upsell | 80% usage | Day 0, 5 | Upgrade to Pro/Enterprise |
| Win-back | Churned 30d | Day 30, 45 | Special offer, feature update |

### 14. Sales Process + Channels

**Pipeline Stages:**

| Stage | Criteria | Close Rate | Duration |
|-------|----------|------------|----------|
| Lead Inbound | Demo request, pricing page | 20% | - |
| Qualified | Fund >$10M AUM, active trading | 40% | 1 week |
| Demo Completed | Live walkthrough, Q&A | 50% | 2 weeks |
| Pilot | Paper trading or small live | 70% | 4 weeks |
| Closed Won | Contract signed, integration | - | 8-12 weeks total |

**Channels:**
- Inbound (content, SEO, ads)
- Outbound (LinkedIn, crypto conferences)
- Partnerships (custodians, prime brokers)

### 15. GTM Experiments + Bullseye

**Bullseye Framework:**

| Channel | Test Budget | Success Metric | Scale? |
|---------|-------------|----------------|--------|
| LinkedIn Ads | $5K | 5 demos/booked | Yes → $20K |
| Twitter/X | $2K | 50 signups | Yes → $10K |
| Crypto Conf (sponsorship) | $15K/event | 20 qualified leads | Maybe |
| Content/SEO | $10K/mo (team) | 500 organic visits/mo | Long-term |
| Partnerships | $0 (BD time) | 2 partner referrals/qtr | Yes |

---

## Phase 5: Operations (Steps 15-21)

### 16. AARRR + Lean Analytics

**North Star Metric:** "Daily Active Trading Volume" (DATV)

| Metric | Target M6 | Target M12 |
|--------|-----------|------------|
| Acquisition | 500 signups/mo | 2,000 signups/mo |
| Activation | 30% paper trade D1 | 40% paper trade D1 |
| Retention | 50% D7 active | 60% D7 active |
| Revenue | $10K MRR | $83K MRR ($1M ARR) |
| Referral | 5% invite rate | 15% invite rate |

**Dashboard:** Daily tracking in Grafana/Looker

### 17. Fundraising + VC Narrative

**Pitch Structure:**
```
Problem: Institutional traders miss arb opportunities across fragmented exchanges
Solution: AI-powered multi-exchange arbitrage engine
Market: $2.3T crypto daily volume, 2-5% arb opportunity = $46-115B TAM
Traction: [X] funds piloting, $[Y] MRR, [Z]% MoM growth
Ask: $3M Seed at $15M pre (18mo runway to $10M ARR)
```

**Target Investors:**
- Crypto-native VCs (a16z crypto, Paradigm, Pantera)
- SEA-focused funds (Golden Gate Ventures, Sequoia SEA)
- Angel: Ex-traders, fund managers

### 18. Risk + Scenario OS

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Exchange API downtime | High | Medium | Multi-exchange redundancy, circuit breakers |
| Regulatory crackdown | Medium | High | SG entity, MAS compliance, legal counsel |
| Smart contract exploit | Low | Critical | Third-party audits, insurance fund |
| Competitor undercutting | Medium | Medium | Feature velocity, customer lock-in (data) |
| Key person risk | Low | High | Documentation, bus factor >2 |

### 19. Talent + Org Design

**6-Month Hiring Plan:**

| Month | Role | Type | Focus |
|-------|------|------|-------|
| 1-2 | CTO (cofounder) | Founder | Architecture, trading infra |
| 3 | Backend Engineer | FT | API, billing, multi-tenant |
| 4 | Compliance Officer | FT/Contractor | MAS licensing, AML/KYC |
| 6 | Sales Lead | FT | Enterprise pipeline, partnerships |

**Culture Code:**
- "Alpha first" — Every feature must prove ROI
- "Compliance is a feature" — Not an afterthought
- "Ship daily" — Rapid iteration, data-driven

### 20. Industry Patterns + IPO Archetypes

**Comparable Companies:**

| Company | Model | Valuation | Multiple |
|---------|-------|-----------|----------|
| TradeSanta | Crypto bot SaaS | ~$50M | 5x ARR |
| Cryptohopper | Trading platform | ~$100M | 8x ARR |
| HaasOnline | Enterprise trading | ~$80M | 6x ARR |
| **Algo-Trader (Target)** | Institutional arb | $1M ARR → $10M valuation (10x) |

**IPO Path:**
- Year 1-2: Grow to $10M ARR, MAS license
- Year 3: $30M ARR, Series B, expand to US/EU
- Year 4-5: $100M ARR, IPO on SGX/Nasdaq

### 21. Data Room + Investor Materials

**Required Documents:**
- Pitch Deck (12 slides)
- One-pager (teaser)
- Financial Model (3-yr projections)
- Technical Architecture Doc
- Security Audit Report
- Legal Opinion (regulatory status)
- Customer LOIs (pilot commitments)

---

## Phase 6: Execution (Steps 22-24)

### 22. Agentic Execution + OKR

**Q2 2026 OKRs:**

| Objective | Key Results | Owner |
|-----------|-------------|-------|
| Ship MVP | 3 exchanges live, <100ms latency, 99.9% uptime | CTO |
| First Revenue | $10K MRR, 5 paying customers | Sales |
| Compliance Ready | AML/KYC integrated, audit logs complete | Compliance |

**Q3 2026 OKRs:**

| Objective | Key Results | Owner |
|-----------|-------------|-------|
| Scale Infrastructure | 10x throughput, DEX integration | CTO |
| Growth | $50K MRR, 20 customers | Sales |
| Fundraising | Close $3M Seed | CEO |

### 23. Board Governance

**Board Structure (Post-Seed):**
- 2 Founder Seats (CEO, CTO)
- 1 Investor Seat (Lead VC)
- 1 Independent (ex-trader, advisor)

**Reporting Cadence:**
- Monthly: Board update (metrics, risks, asks)
- Quarterly: Board meeting (strategy, budget, hiring)
- Ad-hoc: Material events (regulatory, M&A)

### 24. ESG + Impact

**Sustainability Framework:**
- Carbon offset for trading compute (Cloudflare, renewable providers)
- Energy-efficient consensus (avoid PoW chains for settlements)
- Transparency: Publish quarterly impact report

**Impact Metrics:**
- "Alpha democratized" — Retail access to institutional strategies
- "Market efficiency" — Arb reduces price fragmentation
- "Jobs created" — Local hiring in SEA

### 25. Crisis + Reputation OS

**Crisis Playbook:**

| Scenario | Response | Owner |
|----------|----------|-------|
| Exchange hack | Pause trading, assess exposure, comms within 1hr | CTO |
| Regulatory action | Legal review, pause affected markets, investor notify | CEO |
| Major bug/loss | Incident report, user reimbursement, post-mortem | CTO |
| PR negative | Comms response, fact-check, proactive outreach | CMO |

**Reputation Monitoring:**
- Brand mentions (Twitter, Reddit, Telegram)
- Review sites (Trustpilot, G2)
- Customer health scores (NPS, churn risk)

---

## Output Files Generated

### 1. `.mekong/company.json`
Location: `apps/algo-trader/.mekong/company.json`

### 2. Execution Plan
Location: `plans/algo-trader-blueprint/plan.md`

### 3. First 5 Mission Tasks
Location: `apps/algo-trader/tasks/`

---

## Unresolved Questions

1. **Entity Structure:** SG (MAS) vs Cayman (crypto-friendly) vs BVI?
2. **Custody:** Self-custody vs third-party (Fireblocks, Copper)?
3. **Performance Fee Legal:** Can we charge 2/20 without fund license?
4. **DEX Integration:** Which chains? (Ethereum, Solana, Cosmos?)
5. **Insurance:** Should we carry crime insurance for user funds?

---

**Analysis Status:** COMPLETE
**Next Step:** OpenClaw CTO daemon executes 5 missions from `tasks/`
