# VC & Cap Table Strategy — Mekong CLI

**Date:** March 2026
**Covers:** vc-map, cap-table, term-sheet, negotiate, dilution-sim

---

## Founding Cap Table (Pre-Raise)

| Shareholder | Shares | % Ownership | Notes |
|-------------|--------|-------------|-------|
| Founder | 10,000,000 | 100% | Common stock |
| Option pool | 0 | 0% | Create before raise |
| **Total** | **10,000,000** | **100%** | |

**Recommended pre-raise setup:**
- Create 1,000,000 share option pool (10%) BEFORE raise → dilutes founder pre-money → better for future hires
- Incorporate as Delaware C-Corp or Singapore HoldCo (required for US/SEA VC investment)

---

## Seed Round Dilution Simulation

### Scenario A: $500K at $3M post-money SAFE

| Shareholder | Shares (est.) | % Post-money |
|-------------|---------------|--------------|
| Founder | 10,000,000 | 75.0% |
| Option pool (10%) | 1,333,333 | 10.0% |
| Seed investors | 2,000,000 | 15.0% |
| **Total** | **13,333,333** | **100%** |

Founder dilution: 100% → 75% (25% given up for $500K + option pool)

### Scenario B: $750K at $4.5M post-money SAFE

| Shareholder | Shares (est.) | % Post-money |
|-------------|---------------|--------------|
| Founder | 10,000,000 | 74.1% |
| Option pool (10%) | 1,351,351 | 10.0% |
| Seed investors | 2,162,162 | 16.0% |
| **Total** | **13,513,513** | **100%** |

Founder dilution: 100% → 74.1%

### Scenario C: $1M at $6M post-money SAFE

| Shareholder | Shares (est.) | % Post-money |
|-------------|---------------|--------------|
| Founder | 10,000,000 | 73.5% |
| Option pool (10%) | 1,360,544 | 10.0% |
| Seed investors | 2,244,898 | 16.5% |
| **Total** | **13,605,442** | **100%** |

Founder dilution: 100% → 73.5%

**Recommendation:** Scenario B ($750K at $4.5M). Sufficient capital for 18 months, founder retains >74%, valuation defensible at $10K+ MRR.

---

## Post-Series A Dilution (Projected 2027–2028)

Assuming Series A: $3M at $15M post-money (after $900K ARR)

| Shareholder | Pre-A % | A Dilution | Post-A % |
|-------------|---------|------------|----------|
| Founder | 74.1% | 20% | 59.3% |
| Seed investors | 16.0% | 20% | 12.8% |
| Series A investors | — | — | 20.0% |
| Option pool (expanded) | 10.0% | — | 7.9% |
| **Total** | **100%** | | **100%** |

**Founder at Series A: ~59% ownership** — still control position, no dual-class needed at this stage.

---

## VC Target Map

### Tier 1: Lead Investors (Southeast Asia + OSS focus)

| Fund | Focus | Check Size | Why Mekong |
|------|-------|------------|------------|
| Iterative.vc | SEA B2B SaaS | $100K–$500K | SEA-first, dev tools thesis |
| Golden Gate Ventures | SEA early-stage | $250K–$1M | Vietnam presence |
| Antler Vietnam | Pre-seed/seed | $100K–$300K | Vietnam market |
| OSS Capital | Open source | $500K–$2M | MIT license, community moat |
| 500 Global | SEA/global | $150K–$500K | Large Vietnam portfolio |

### Tier 2: US Micro-VCs (Dev Tools)

| Fund | Focus | Check Size | Notes |
|------|-------|------------|-------|
| Boldstart Ventures | Dev infra | $500K–$2M | Strong dev tools portfolio |
| Uncorrelated | Dev tools | $250K–$1M | OSS-friendly |
| Heavybit | Dev-focused | $500K–$2M | Community-built products |
| Backend Capital | B2B SaaS | $250K–$500K | CLI/terminal tools fit |

### Tier 3: Strategic Angels

| Profile | Why Valuable |
|---------|-------------|
| Cloudflare employees | Technical credibility + distribution |
| OpenRouter / DeepSeek team | LLM partnership alignment |
| Polar.sh founders | Existing billing integration |
| Vietnamese tech founders (exits) | Local network + credibility |
| Former GitHub/Atlassian PMs | Dev tools distribution knowledge |

---

## Term Sheet Negotiation Guide

### Non-negotiables (protect these)

| Term | Our Position | Why |
|------|-------------|-----|
| Pro-rata rights | Only for checks >$100K | Prevent small investors clogging future rounds |
| Information rights | Quarterly updates only | Monthly investor updates are overhead |
| Board seats | None at seed (SAFE) | Preserve founder control pre-Series A |
| Anti-dilution | Broad-based weighted avg | Industry standard, not full ratchet |
| Liquidation preference | 1x non-participating | Prevent 2x or participating preferred |

### Acceptable concessions

| Term | Acceptable | Avoid |
|------|-----------|-------|
| Valuation cap | $3M–$5M (SAFE) | Below $3M is punitive |
| Discount | 15–20% | Above 25% |
| MFN clause | Yes (standard) | — |
| ROFR | Yes on secondary sales | First refusal on primary is ok |
| Drag-along | Yes, majority threshold | Super-majority drag-along |

### Red flags — walk away if investor insists on:

- Full ratchet anti-dilution
- Participating preferred with >1x cap
- Board seat at seed round
- Exclusivity period >30 days
- Redemption rights
- Pay-to-play provisions at seed

---

## Valuation Justification

**Comparable seed valuations (2025–2026 dev tools):**

| Company | Stage | Valuation | ARR at raise |
|---------|-------|-----------|-------------|
| Aider (comparable OSS) | Seed | $8M | $0 (pure OSS) |
| Warp terminal | Seed | $15M | Pre-revenue |
| Typical B2B SaaS seed | Seed | $5–15M | $100K–$500K ARR |

**Mekong CLI at $10K MRR ($120K ARR):**
- Revenue multiple: $4.5M / $120K = 37.5x ARR (aggressive but justifiable for 92% GM + 136:1 LTV:CAC)
- Comparable OSS tools: $8M+ seed valuations at zero revenue
- **Target: $4–5M post-money is defensible**

---

## SAFE vs. Priced Round Analysis

| Factor | SAFE | Priced Round |
|--------|------|--------------|
| Legal cost | $5K–$15K | $50K–$100K |
| Time to close | 2–4 weeks | 3–6 months |
| Valuation set now | No (cap only) | Yes |
| Investor rights | Minimal | Full preferred rights |
| Board complexity | None | Often 1 board seat |
| **Recommended** | **YES at seed** | Wait for Series A |

---

## Cap Table Hygiene Rules

1. Never issue shares without a 4-year vesting / 1-year cliff (even to co-founders added later)
2. All advisor shares: 2-year vesting, no cliff, max 0.25% each
3. Option pool: replenish to 10–15% before each priced round
4. Track all SAFEs in a cap table model — conversion math gets complex fast
5. Use Carta or Pulley for cap table management (not spreadsheets) post-raise
6. Get a 409A valuation before issuing any options (required for US entities)

---

## Key Milestones to Maximize Valuation

| Milestone | Valuation Impact |
|-----------|-----------------|
| $10K MRR | +$1M on cap (proves PMF) |
| 100 paying customers | +$500K (proves repeatability) |
| Enterprise pilot (3 accounts) | +$1M (proves upmarket motion) |
| Agent marketplace live | +$1M (network effect moat) |
| YC application accepted | +$2–3M (signal value) |
| LLM provider partnership signed | +$500K (distribution moat) |
