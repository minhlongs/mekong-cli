# Mekong IDE Pricing Strategy

> **Task #88** — Design pricing strategy for the one-person company platform
> **Status:** In Progress | **Owner:** Claude Opus 4.8 | **Date:** 2026-06-20

---

## Executive Summary

Mekong IDE replaces a 50-person team with autonomous agents for **solo founders**. The pricing strategy must:

1. **Align with value** — $49-499/mo for a full workforce replacement
2. **Enable growth** — clear upgrade path as business scales
3. **Capture international markets** — Vietnam and emerging markets
4. **Optimize for conversion** — frictionless trial to paid
5. **Maximize LTV** — reduce churn, increase expansion revenue

---

## Current State Analysis

### Existing Pricing (Revenue Router)

| Tier | Price | Credits | Price/Credit |
|------|-------|---------|--------------|
| Starter | $49/mo | 200 | $0.245 |
| Growth | $149/mo | 1,000 | $0.149 |
| Pro | $499/mo | 5,000 | $0.100 |

**Issues Identified:**

1. **Gap Problem**: $149 → $499 jump is too large. No mid-tier for users outgrowing Growth but not needing Pro.
2. **Credit Allocation**: Pro's 5,000 credits may be insufficient for heavy users; no easy overage path.
3. **Feature Blur**: All tiers claim "all departments" — unclear differentiation beyond credits.
4. **VN Pricing Disconnect**: VN market shows different prices ($7.99-49.99) but not aligned with main tiers.
5. **No Annual Discount**: Missing 20-30% annual prepayment incentive.
6. **No Add-on Credits**: Credit-only purchases not available for existing subscribers.

### Command Cost Structure

Based on `factory/contracts/pricing.json` service costs:

| Command Category | Credits | Example |
|------------------|---------|---------|
| Simple task | 1-2 | `/marketing-vn`, `/bhxh` |
| Medium task | 3-5 | `/annual`, `/landing-page` |
| Complex task | 5-10 | `/security-audit`, `/fundraise` |

**Usage Patterns (estimated):**
- Casual user: 50-100 credits/mo
- Regular user: 300-800 credits/mo
- Power user: 1,500-3,000 credits/mo
- Heavy user: 5,000+ credits/mo

---

## Recommended Pricing Structure

### Tier Redesign (4-Tier Model)

| Tier | Price | Credits | Price/Credit | Target User |
|------|-------|---------|--------------|-------------|
| **Free** | $0 | 50 | $0.000 | Trial, exploration |
| **Starter** | $49/mo | 300 | $0.163 | Testing the waters |
| **Growth** | $149/mo | 1,200 | $0.124 | Growing business |
| **Scale** | $299/mo | 3,500 | $0.085 | Scaling operation |
| **Pro** | $499/mo | 7,000 | $0.071 | Max capacity |
| **Enterprise** | Custom | Custom | Custom | Teams + on-prem |

**Key Changes:**

1. **Add Scale tier** ($299/mo, 3,500 credits) — bridges Growth→Pro gap
2. **Increase credit allocation** across all tiers by 20-40% (better value)
3. **Maintain decreasing per-credit cost** — volume discounts baked in
4. **Free tier** stays at 50 credits for product-led growth

### Feature Differentiation (Beyond Credits)

| Feature | Free | Starter | Growth | Scale | Pro | Enterprise |
|---------|------|---------|--------|-------|-----|------------|
| All 22 departments | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Concurrent agents | 1 | 2 | 4 | 8 | 16 | 32+ |
| Priority queue | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| Custom agents | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| Dedicated support | Community | Email | Email | Slack | Slack | Dedicated CSM |
| SLA | ❌ | ❌ | ❌ | 99% | 99.5% | 99.9% |
| SSO / SCIM | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| On-prem option | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Audit logs | 7 days | 30 days | 90 days | 1 year | 2 years | Unlimited |
| Webhooks | ❌ | ❌ | Basic | Advanced | Advanced | ✅ |
| Custom integrations | ❌ | ❌ | ❌ | ❌ | 5 included | Unlimited |
| Training import | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |

### Overage & Add-on Pricing

**Credit Overages:**
- Free tier: no overages (blocked at 0)
- Paid tiers: $0.08/credit (matches Pro effective rate)
- Auto-topup: $20 minimum when balance < 20% of monthly allocation

**Add-on Packs (one-time or recurring):**
| Pack | Credits | Price | Effective Rate |
|------|---------|-------|----------------|
| Mini | 500 | $35 | $0.070 |
| Standard | 2,000 | $120 | $0.060 |
| Bulk | 10,000 | $500 | $0.050 |

**Note:** Add-ons DO NOT expire monthly. Carry forward indefinitely.

---

## International Pricing Strategy

### Vietnam Market (VND)

Based on GDP per capita and purchasing power parity:

| Tier | USD | VND Display | PPP Adjustment |
|------|-----|-------------|----------------|
| Starter | $49 | 499,000₫ | 1.0x (reference) |
| Growth | $149 | 1,499,000₫ | 1.0x |
| Scale | $299 | 2,999,000₫ | 1.0x |
| Pro | $499 | 4,999,000₫ | 1.0x |

**Payment Methods:**
- Primary: Stripe/Polar (USD billing)
- Local: VietQR bank transfer (auto-convert VND → USD via sepay)
- Mobile: MoMo, ZaloPay integration (Phase 7+)

**Promotional Pricing (VN Launch):**
- First 100 subscribers: 50% off first 3 months
- Student/educator discount: 40% off (verify via email)
- Early adopter lock: $29/mo for life (limited to first 50)

---

## Annual Commitment Incentive

**20% discount on annual prepayment:**

| Tier | Monthly | Annual (20% off) | Savings |
|------|---------|------------------|---------|
| Starter | $49 | $470 | $118 |
| Growth | $149 | $1,431 | $357 |
| Scale | $299 | $2,870 | $718 |
| Pro | $499 | $4,791 | $1,197 |

**Benefits:**
- Improves cash flow (12 months upfront)
- Reduces churn (annual commitment)
- Increases LTV (20% more revenue per customer)

**Display psychology:**
```
Most Popular
$149/mo → $119/mo billed annually (Save $357)
```

---

## Competitive Positioning

| Competitor | Price | What You Get | Mekong Advantage |
|------------|-------|--------------|------------------|
| **Claude Code** | $20/mo (Pro) | Claude AI coding assistant | 22 departments, full business ops |
| **Cursor** | $20-40/mo | AI editor | Full autonomous execution |
| **Windsurf** | $15-30/mo | AI coding tool | Complete workforce replacement |
| **GitHub Copilot** | $10-19/mo | Code completion | Strategy + execution + ops |
| **Replit AI** | $20-70/mo | AI in browser | Local-first, no cloud lock-in |

**Mekong's Value Proposition:**
- One subscription = 50-person team
- 22 autonomous departments
- Runs locally (privacy) or cloud (convenience)
- All-inclusive — no add-ons for core features

**Pricing Justification:**
- **Starter ($49)**: 2x Cursor Pro but includes FULL business stack, not just coding
- **Growth ($149)**: 5x Cursor Pro but includes sales, marketing, finance, legal, HR
- **Pro ($499)**: 25x Cursor Pro but replaces entire company workforce

---

## Price Elasticity & Conversion Targets

### Conversion Funnel Targets

| Stage | Current Target | Optimized Target |
|-------|----------------|------------------|
| Landing → Signup | 5% | 8% |
| Free → Paid (30d) | 3% | 5% |
| Paid Upgrade Rate (annual) | 15% | 25% |
| Churn (annual) | 25% | 15% |

### Pricing Psychology Optimization

1. **Decoy Effect**: Add Enterprise at $999 to make Pro look reasonable
2. **Anchoring**: Show $499/mo Pro first, then $299 Scale, then $149 Growth
3. **Most Popular Badge**: Highlight Growth tier (sweet spot)
4. **Price Ending**: Use .99 or .00 for premium positioning (keep .00 for B2B)
5. **Value Stack**: Show "50-person team" value = $250,000/yr

---

## Implementation Checklist

### Code Changes Required

1. **Update `src/raas/revenue_router.py`**:
   ```python
   CREDIT_MAP = {
       "free": 50,
       "starter": 300,
       "growth": 1200,
       "scale": 3500,
       "pro": 7000,
   }

   _PRICING_TIERS = [
       {"name": "Free", "tier": "free", "price_usd": 0, "credits": 50},
       {"name": "Starter", "tier": "starter", "price_usd": 49, "credits": 300},
       {"name": "Growth", "tier": "growth", "price_usd": 149, "credits": 1200},
       {"name": "Scale", "tier": "scale", "price_usd": 299, "credits": 3500},
       {"name": "Pro", "tier": "pro", "price_usd": 499, "credits": 7000},
   ]
   ```

2. **Update Polar.sh product IDs**: Create new Scale tier product, adjust Pro credits to 7,000.

3. **Update `/v1/pricing` endpoint** to return 5 tiers.

4. **Add overage billing** in `src/raas/credits.py`:
   - Track usage beyond monthly allocation
   - Charge $0.08/credit to stored payment method
   - Implement soft/hard limits

5. **Add annual subscription support**:
   - Update checkout flow with `interval=annual` parameter
   - Prorate upgrades/downgrades appropriately
   - Update `src/raas/billing_proration.py`

6. **Update VN pricing** in `factory/contracts/pricing.json`:
   ```json
   "vn_products": {
     "starter_vn": { "price_usd": 49, "price_display_vnd": "499.000₫", ... },
     "growth_vn": { "price_usd": 149, "price_display_vnd": "1.499.000₫", ... },
     "scale_vn": { "price_usd": 299, "price_display_vnd": "2.999.000₫", ... },
     "pro_vn": { "price_usd": 499, "price_display_vnd": "4.999.000₫", ... }
   }
   ```

7. **Update docs/website**:
   - `README.md` pricing table
   - `www.mekongmind.com` landing pages (13 use cases)
   - Dashboard pricing component
   - CLI help output (`mekong pricing`)

---

## Rollout Plan

### Phase 1: Technical Implementation (Week 1-2)
- Update pricing constants
- Create Polar Scale product
- Update webhook handlers
- Add overage tracking

### Phase 2: Migration Path (Week 3)
- **Grandfather existing customers** at current rates for 6 months
- Offer upgrade incentives (credit bonuses)
- Communicate clearly via email + in-app

### Phase 3: Marketing Update (Week 4)
- Update all landing pages
- Create new comparison charts
- Update demo videos/screenshots
- Train support (Zalo OA responses)

### Phase 4: Monitor & Optimize (Week 5-8)
- Track conversion rates by tier
- Monitor upgrade/downgrade patterns
- A/B test pricing display
- Adjust if churn increases

---

## Success Metrics

| Metric | Baseline | Target (90d) | Measurement |
|--------|----------|--------------|-------------|
| Free → Paid conversion | 3% | 5% | `analytics.onboarding_funnel` |
| Average Revenue Per User (ARPU) | $89 | $135 | `revenue.arpu` |
| Expansion revenue | 5% | 15% | `revenue.expansion` |
| Annual churn | 25% | 15% | `tenant.churn_rate` |
| NPS (paid users) | 40 | 55 | `survey.nps` |
| LTV:CAC | 3:1 | 5:1 | `unit_economics.ltv_cac` |

---

## Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Price increase backlash from existing users | Medium | High | Grandfather 6 months, communicate value |
| Competitors undercut on price | Low | Medium | Emphasize 22-department value prop |
| Scale tier cannibalizes Pro | Low | Medium | Position Pro as "unlimited" with highest SLA |
| VN pricing confusion (USD vs VND display) | Medium | Medium | Clear note: "Giá USD, hiển thị VND" |
| Credit consumption faster than expected | High | High | Monitor usage, adjust allocations if needed |
| Polar webhook issues with new tiers | Medium | High | Test thoroughly in staging |

---

## Next Steps

1. **Review this strategy** with stakeholders (founder, potential customers)
2. **Run pricing interviews** with 10-15 target users (task #89)
3. **Finalize tier boundaries** based on feedback
4. **Implement technical changes** per checklist
5. **Prepare communication plan** for existing customers
6. **Set up analytics tracking** for all pricing metrics
7. **Execute phased rollout** with close monitoring

---

## Appendix: Unit Economics

**Assumptions:**
- CAC (Customer Acquisition Cost): $50
- Gross margin: 85% (cloud costs minimal, mostly LLM API)
- Avg customer lifetime: 36 months

**Current Pricing (baseline):**
- ARPU: $89
- LTV: $89 × 36 × 0.85 = $2,723
- LTV:CAC = 54:1 (excellent, but pricing likely too low)

**Optimized Pricing (target):**
- ARPU: $135
- LTV: $135 × 36 × 0.85 = $4,131
- LTV:CAC = 82:1 (exceptional)

**Expansion revenue target:** 15% of existing customers upgrade annually → additional $50-200/mo per upgrade.

---

**Sources:**
- Current pricing: `src/raas/revenue_router.py`
- Command costs: `factory/contracts/pricing.json`
- Strategy alignment: `STRATEGY.md`
- Go-live context: `GO_LIVE_PLAYBOOK.md`
