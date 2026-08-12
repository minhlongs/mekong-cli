# Revenue Sharing & Fee Structure — Mekong Plugin Marketplace

**Task #283** — Design revenue sharing and fee structure model  
**Status:** Complete | **Owner:** Claude Opus 4.8 | **Date:** 2026-06-21

---

## Executive Summary

This document defines the revenue sharing model for the Mekong Plugin Marketplace, specifying how revenue from plugin sales is distributed between Mekong IDE and plugin developers. The model incentivizes developer participation while ensuring sustainable marketplace operations.

**Key Principles:**
- Developer-first revenue split (80% standard)
- Volume-based tiered commissions (decrease Mekong share as developer grows)
- Transparent calculations with no hidden fees
- Competitive with industry benchmarks
- Multi-currency support (USD, VND)

---

## 1. Revenue Sharing Model

### 1.1 Standard Commission Structure

| Plugin Type | Developer Share | Mekong Share | Notes |
|-------------|-----------------|--------------|-------|
| **Free Plugin** | 100% (no revenue) | 0% | No monetary revenue |
| **Paid Plugin (One-time)** | 80% | 20% | Per sale |
| **Paid Plugin (Subscription)** | 80% | 20% | Per billing cycle |
| **Enterprise Plugin** | 85-95% | 5-15% | Negotiated, usually 90/10 |

**Baseline:** 80/20 split favors developers to incentivize marketplace participation.

### 1.2 Volume-Based Tiered Discounts

**Developers earn better rates as they sell more:**

| Annual Gross Revenue | Mekong Commission | Developer Revenue | Tier Name |
|----------------------|-------------------|-------------------|-----------|
| $0 - $10,000 | 20% | 80% | Standard |
| $10,001 - $50,000 | 18% | 82% | Bronze |
| $50,001 - $100,000 | 15% | 85% | Silver |
| $100,001 - $500,000 | 12% | 88% | Gold |
| $500,000+ | 10% | 90% | Platinum |

**Example calculation:**
- Developer sells $60k worth of plugins in year 1 → 20% commission = $48k earned
- Same $60k in year 2 (after crossing $50k threshold) → 15% commission = $51k earned
- **Extra $3k from volume discount** (6.25% increase)

**Important:** Commission rates apply to revenue **after** payment processing fees but **before** tax withholding.

---

## 2. Payment Processing Fees

### 2.1 Fee Schedule

| Payment Method | Fee Structure | Currency | Who Bears Cost |
|----------------|---------------|----------|----------------|
| **Stripe (card)** | 2.9% + $0.30 per transaction | USD | Deducted from developer revenue |
| **Stripe (international cards)** | +1% surcharge | USD | Deducted from developer revenue |
| **Polar (card)** | 2.9% + $0.30 + $0.10/mo | USD | Deducted from developer revenue |
| **Bank Transfer (Vietnam)** | ~1-2% (bank-dependent) | VND | Deducted from developer revenue |
| **PayPal (future)** | 4.4% + $0.30 | USD | Deducted from developer revenue |

### 2.2 Fee Calculation Examples

**Example 1: $100 Plugin Sale (Stripe, US Developer)**

```
Sale price: $100.00
Payment fee: $100 × 2.9% + $0.30 = $2.90 + $0.30 = $3.20
Mekong commission: $100 × 20% = $20.00
Total deductions: $3.20 + $20.00 = $23.20
Developer receives: $100 - $23.20 = $76.80
Developer net %: 76.8%
```

**Example 2: 499,000₫ Plugin Sale (Vietcombank, VN Developer)**

```
Sale price: 499,000₫ ($19.99 at 25,000₫/USD)
Payment fee: 499,000 × 1.5% = 7,485₫
Mekong commission: 499,000 × 20% = 99,800₫
Total deductions: 7,485 + 99,800 = 107,285₫
Developer receives: 499,000 - 107,285 = 391,715₫ (~$15.67)
Developer net %: 78.5% (bank fee lower, so net higher)
```

**Example 3: Subscription $20/mo (Stripe)**

```
Monthly sale: $20.00
Payment fee (recurring): $20 × 2.9% + $0.30 = $0.58 + $0.30 = $0.88
Mekong commission: $20 × 20% = $4.00
Developer receives monthly: $20 - $0.88 - $4.00 = $15.12
Annual developer revenue: $15.12 × 12 = $181.44
```

---

## 3. Revenue Sharing Formulas

### 3.1 General Formula

```
NetDeveloperRevenue = GrossSalePrice - ProcessingFee - MekongCommission
NetDeveloperPercentage = (NetDeveloperRevenue / GrossSalePrice) × 100%

Where:
ProcessingFee = min(ProcessingRate × GrossSalePrice + FixedFee, MaxFee)
MekongCommission = GrossSalePrice × CommissionRate(developerTier)
```

### 3.2 Tier-Based Commission Lookup

Commission rate is determined by developer's **annual gross revenue to date** (cumulative):

```python
def get_commission_rate(annual_gross_usd: float) -> float:
    """
    Returns Mekong commission rate based on developer's annual gross revenue.
    Rate decreases as developer sells more (incentive for high performers).
    """
    if annual_gross_usd < 10000:
        return 0.20  # Standard: 20%
    elif annual_gross_usd < 50000:
        return 0.18  # Bronze: 18%
    elif annual_gross_usd < 100000:
        return 0.15  # Silver: 15%
    elif annual_gross_usd < 500000:
        return 0.12  # Gold: 12%
    else:
        return 0.10  # Platinum: 10%
```

**Note:** Commission rate is evaluated at time of sale based on developer's current annual gross (YTD). If developer crosses tier threshold mid-year, future sales use new rate; past sales not adjusted.

---

## 4. Developer Wallet & Payouts

### 4.1 Wallet Structure

Developers have separate balances per currency:

```sql
developer_wallets:
- developer_id (FK)
- balance_usd (available for withdrawal)
- balance_vnd (available for withdrawal)
- pending_payout_usd (scheduled but not yet sent)
- total_earned_usd (lifetime cumulative)
- payout_threshold_usd (min before auto-payout, default $100)
- preferred_payout_method (stripe|paypal|bank)
```

### 4.2 Payout Schedule

| Developer Tier | Min. Threshold | Schedule | Processing Time |
|----------------|----------------|----------|-----------------|
| Standard | $100 | Monthly (15th) | 3-5 business days |
| Preferred (lifetime >$10k) | $50 | Weekly (Friday) | 1-3 business days |
| Enterprise (lifetime >$100k) | $0 | Weekly (daily option) | Same-day (wire) |

**Payout Trigger:**
- Automatic: When `balance_usd >= threshold` on payout calculation date
- Manual: Developer can request immediate payout (if balance > threshold)
- Hold: New developers (first 30 days) have 7-day hold on first payout

### 4.3 Payout Methods

**USD Wallets:**
- **Stripe Connect:** Fastest (2-3 days), lowest fee (1-2%), requires Stripe account
- **PayPal:** Global, 4-5 days, higher fee (if any)
- **Bank Wire:** $15-30 fee, 3-5 business days, for large amounts ($1k+)

**VND Wallets:**
- **Vietcombank/MB/ACB:** Direct transfer to Vietnamese bank account
- **MoMo/Timo:** E-wallet integration (future)
- **Processing time:** 1-2 business days
- **Fee:** 0-1% (bank-dependent, often free for inbound)

---

## 5. Tax & Compliance

### 5.1 US Tax Withholding

**For US Developers (W-9 on file):**
- No withholding
- 1099-K issued if annual earnings > $600 (per IRS)
- Developer reports as business income on Schedule C

**For Non-US Developers (W-8BEN on file):**
- 30% statutory withholding on US-source revenue
- **BUT:** If developer's country has tax treaty with US, reduced rate may apply (e.g., 0% for many countries)
- Treaty benefits claimed via W-8BEN (provide foreign tax ID)
- Withheld amount may be creditable against home country taxes

**Example (Non-US with treaty 0%):**
- Developer in Germany (tax treaty 0% on business profits)
- W-8BEN on file → no US withholding
- Developer pays German income tax on worldwide income

**Example (Non-US without treaty):**
- Developer in country without treaty
- 30% withheld on US-source revenue (from Stripe/Polar payments)
- Developer may claim foreign tax credit on home country return

### 5.2 VAT/GST

- **EU:** Mekong (as platform operator) may need to collect/remit VAT depending on EU OSS regime
- **Vietnam:** 10% VAT on digital services to Vietnamese consumers (B2B exempt if valid tax ID)
- **Other countries:** Follow local digital services tax rules

**Implementation:** Stripe/Polar can auto-collect VAT if configured; otherwise Mekong handles.

### 5.3 Tax Reporting

**Year-End Documents:**
- **US developers:** 1099-K (if >$600)
- **Non-US developers:** 1042-S (if US withholding applied)
- **All developers:** Annual earnings statement (for tax return)

---

## 6. Refunds & Adjustments

### 6.1 Refund Policy

| Plugin Type | Refund Window | Refund Amount | Developer Impact |
|-------------|---------------|---------------|------------------|
| **One-time purchase** | 30 days | 100% | Revenue reversed fully |
| **Subscription** | 14 days (first period) or pro-rated | Pro-rated | Reversed for unearned portion |
| **Usage-based** | 30 days on unused credits | Unused portion only | Only unused revenue reversed |
| **Enterprise (custom)** | As per contract | Negotiated | Contract-specific |

**Refund Processing:**
- User requests refund via support@ or dashboard
- Stripe/Polar processes refund (original payment method)
- Mekong API updates purchase status → "refunded"
- Developer wallet debited (if sufficient balance) or future earnings reduced
- If developer balance insufficient, Mekong absorbs loss (fraud protection)

### 6.2 Disputes & Chargebacks

**Dispute Lifecycle:**
1. User disputes charge with bank/card issuer (via Stripe/Polar)
2. Stripe/Polar notifies Mekong via webhook
3. Purchase status → "disputed"
4. Developer has 7 days to submit evidence (via dashboard)
5. Stripe/Polar reviews evidence; resolves in 5-30 days
6. If won: dispute dismissed, revenue restored to developer
7. If lost: revenue clawed back + $15-25 dispute fee

**Developer Responsibilities:**
- Respond to disputes within 7 days
- Provide evidence: proof of delivery, terms accepted, usage logs
- Maintain good dispute response rate (>70% win rate)

**Excessive Disputes:**
- >1% dispute rate triggers review
- >3% dispute rate → account suspension
- Repeated abuse → termination

---

## 7. Marketplace Fee Alternatives Considered

### Option A: Flat 20% Commission (SELECTED)

**Pros:**
- Simple, predictable
- Competitive with industry (Shopify 30%, GitHub 15-25%)
- Easy to understand for developers
- Scales fairly (volume discounts applied on top)

**Cons:**
- Doesn't account for plugin complexity differences
- May discourage high-priced plugins (developer keeps less)

### Option B: Tiered by Plugin Price

- Plugins < $20: 15% commission
- Plugins $20-100: 20% commission
- Plugins $100-500: 25% commission
- Plugins > $500: 30% commission

**Rejected:** Too complex, discourages premium plugins

### Option C: Subscription vs One-time Differentiated

- One-time: 25% commission
- Subscription: 15% commission (encourage recurring)

**Rejected:** Overly complex; current 20% flat is fair enough

### Option D: Freemium with Marketplace Fee on Upgrades

- Free plugin: 0% commission
- Upgrades: 30% commission (like mobile app stores)

**Rejected:** Would discourage free+paid model; 20% on all is simpler

---

## 8. Volume Incentives Program

### 8.1 Developer Tiers & Benefits

| Tier | Annual Gross | Commission | Additional Benefits |
|------|--------------|------------|---------------------|
| **Standard** | <$10k | 20% | Basic support, community access |
| **Bronze** | $10k-$50k | 18% | Priority support, featured placement |
| **Silver** | $50k-$100k | 15% | Dedicated CSM, early API access |
| **Gold** | $100k-$500k | 12% | Custom analytics, co-marketing |
| **Platinum** | >$500k | 10% | Custom contracts, white-glove support |

### 8.2 Tier Qualification

- **Evaluation:** Monthly recalculation based on YTD gross revenue
- **Grace period:** 30 days at new tier before rate applies (prevents churn from threshold crossing)
- **Appeals:** Developer can request review if believes tier assignment incorrect

---

## 9. Affiliate & Referral Program (Future)

### 9.1 Proposed Structure

- **Referrer:** 5% of revenue from referred developer (lifetime)
- **Capped at 20% of developer's revenue** (so developer still gets at least 80%)
- **Example:** Developer A refers Developer B. B sells $100k worth of plugins. A receives $5k (5% of $100k). B receives $80k (80% of $100k).

**Not implemented yet** (Phase 2, Months 6-12)

---

## 10. Implementation Checklist

### Database

- [x] `plugins` table with commission_rate field
- [x] `developer_wallets` table with balance fields
- [x] `purchases` table with processing_fee, commission, developer_payout
- [x] `payouts` table with scheduled/completed status
- [x] Commission rate lookup function/query
- [ ] Trigger to update developer annual gross on each sale

### API

- [x] Purchase endpoint calculates fees correctly
- [x] Webhook handlers for payment providers (Stripe/Polar)
- [x] Developer earnings dashboard API
- [x] Payout scheduling endpoint
- [ ] Tax withholding calculation endpoint
- [ ] Refund reversal logic

### Dashboard

- [ ] Developer wallet page (balance, pending, history)
- [ ] Earnings breakdown by plugin
- [ ] Payout configuration (threshold, method)
- [ ] Tax forms upload/download (W-8BEN/W-9/1099)
- [ ] Tier status display (current tier, progress to next)

### Operations

- [ ] Monthly payout calculation script
- [ ] Stripe Connect payouts batch processing
- [ ] Bank transfer processing for VN developers
- [ ] Tax form generation (year-end)
- [ ] Dispute management interface

---

## 11. Monitoring & Metrics

### Financial Metrics to Track

| Metric | Calculation | Target |
|--------|-------------|--------|
| **Developer net revenue %** | (Revenue - fees - commission) / Revenue | >75% |
| **Developer retention rate** | Developers with >$0 earnings MoM | >80% |
| **Payout latency** | Days from eligible → actual payout | <3 days |
| **Payout success rate** | % of payouts completed without error | >99% |
| **Dispute rate** | Disputed purchases / total purchases | <1% |
| **Refund rate** | Refunded purchases / total purchases | <5% |

### Alerting

- Payout failures (bank rejected, Stripe error) → alert engineering
- Developer balance > $10k pending for >30 days → investigate
- Dispute rate > 2% → review
- Refund rate > 10% for any developer → review for fraud

---

## 12. Success Criteria

**By Month 6:**
- 20+ active developers earning money
- Total plugin revenue $5k/month
- Average developer net % > 75%
- Payout success rate > 99%
- Developer NPS > 40

**By Month 12:**
- 100+ active developers
- Total plugin revenue $25k/month
- 5 developers in Gold/Platinum tiers
- Payouts processed on time 100%
- Developer NPS > 50

---

**Related Documents:**
- `docs/marketplace-monetization-system.md` — Full marketplace monetization architecture
- `docs/plugin-developer-guide.md` — Developer onboarding and plugin development
- `docs/partners/partner-api-spec.md` — Partner monitoring API (related but separate)

---

**Sources:**
- Industry benchmarks: Shopify 30%, GitHub 15-25%, Unreal 12%
- Mekong strategy: 20% standard, volume discount to 10% at $500k+
- Payment processing: Stripe 2.9%+0.30, Polar similar, VN bank ~1-2%
- Developer-first positioning: 80% revenue share competitive with best platforms
