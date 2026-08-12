# Mekong Plugin Marketplace — Monetization System

**Task #90, #122, #282** — Design marketplace monetization for Mekong plugin marketplace  
**Status:** Complete | **Owner:** Claude Opus 4.8 | **Date:** 2026-06-21

---

## Executive Summary

The Mekong Plugin Marketplace enables developers to publish, sell, and monetize plugins that extend Mekong IDE's capabilities. This document defines the monetization architecture: revenue sharing, fee structure, payment integration, license management, and developer payouts.

**Core Principles:**
- Fair revenue split (80/20 or 70/30 favoring developers)
- Transparent fee structure with no hidden charges
- Automated license key generation and validation
- Multi-currency support (USD, VND)
- Global payment methods (Stripe, Polar, bank transfers)

---

## 1. Monetization Model Overview

### 1.1 Revenue Streams

| Revenue Stream | Description | Mekong Share | Developer Share |
|----------------|-------------|--------------|-----------------|
| **Plugin Sales** | One-time or subscription plugin purchases | 20-30% | 70-80% |
| **Marketplace Commission** | Transaction fee on all plugin marketplace sales | 20% | 80% |
| **Premium Plugin Subscriptions** | Recurring revenue for SaaS plugins | 20-30% | 70-80% |
| **Plugin Usage Credits** | Credits consumed by plugin commands (optional) | 0% | 100% (developer sets price) |

### 1.2 Pricing Flexibility

Plugin developers can choose their pricing model:

- **Free:** Open source, no cost
- **One-time purchase:** Single payment, perpetual license
- **Subscription:** Monthly/annual recurring revenue
- **Freemium:** Free basic version + paid premium features
- **Usage-based:** Credit consumption per command execution
- **Tiered pricing:** Multiple plans (Basic/Pro/Enterprise)

---

## 2. Fee Structure

### 2.1 Marketplace Fees

| Plugin Type | Transaction Fee | When Applied | Developer Revenue |
|-------------|-----------------|---------------|-------------------|
| **Free Plugin** | $0 | N/A | 100% (no revenue) |
| **Paid Plugin (One-time)** | 20% of sale price | At purchase | 80% |
| **Paid Plugin (Subscription)** | 20% of recurring revenue | Each billing cycle | 80% |
| **Enterprise Plugin** | Negotiable (10-15%) | Custom contract | 90-95% |

**Example:**
- Plugin sold for $100 one-time → Developer receives $80, Mekong $20
- Plugin subscription $20/mo → Developer $16/mo, Mekong $4/mo

### 2.2 Payment Processing Fees

**Additional fees (deducted from developer revenue):**

| Payment Method | Processing Fee | Currency |
|----------------|----------------|----------|
| Stripe (card) | 2.9% + $0.30 | USD |
| Stripe (international) | +1% (if applicable) | USD |
| Polar (card) | 2.9% + $0.30 | USD |
| Bank Transfer (Vietnam) | ~1-2% (bank-dependent) | VND |
| PayPal (future) | 4.4% + $0.30 | USD |

**Fee absorption:** Processing fees are deducted from developer payout, not added on top.

### 2.3 Tiered Commission Structure

**Volume-based discounts for high-grossing developers:**

| Annual Gross | Commission Rate | Developer Share |
|--------------|-----------------|-----------------|
| < $10k | 20% | 80% |
| $10k - $50k | 18% | 82% |
| $50k - $100k | 15% | 85% |
| $100k - $500k | 12% | 88% |
| > $500k | 10% | 90% |

**Trigger:** Automatic recalculation monthly; applies to future revenue, not retroactive.

---

## 3. Payment Integration Architecture

### 3.1 Supported Payment Providers

| Provider | Use Case | Coverage | Fee Structure |
|----------|----------|----------|---------------|
| **Stripe** | Global credit/debit cards | Worldwide | 2.9% + $0.30 |
| **Polar** | Subscription management | Global | 2.9% + $0.30 + $0.10/mo |
| **Bank Transfer** | Vietnam market (VND) | Vietnam only | ~1-2% |
| **PayPal** (planned) | Alternative global | Worldwide | 4.4% + $0.30 |

### 3.2 Multi-Currency Support

| Currency | Pricing Display | Payout Currency | Conversion |
|----------|-----------------|-----------------|------------|
| USD | $ | USD (Stripe/Polar) | N/A |
| VND | ₫ | VND (bank) or USD (Polar) | 1 USD ≈ 25,000₫ |

**Display rules:**
- International users: USD only
- Vietnam users (detected by IP/Zalo OA): Show VND conversion (e.g., $19.99 ≈ 499.000₫)
- Developer dashboard: Show earnings in preferred currency

### 3.3 Payment Flow

```
User purchases plugin:
1. Select plugin → "Buy Now" or "Subscribe"
2. Checkout page shows price in user's currency
3. Payment via Stripe/Polar/bank transfer
4. Webhook from payment provider → Mekong API
5. License key auto-generated and delivered
6. Plugin access granted
7. Revenue allocated: 80% to developer wallet, 20% to Mekong
8. Payout scheduled (see Section 6)
```

---

## 4. License Key Management

### 4.1 License Key Generation

**Format:** `MEKONG-PLUGIN-{PLUGIN_ID}-{USER_ID}-{RANDOM}`

Example: `MEKONG-PLUGIN-xj9dk2s-opc_001_abc123-Ab3dE7fG`

**Generation:**
- Triggered on successful purchase
- Unique per user per plugin (one license per purchase)
- Stored in database with metadata: user_id, plugin_id, purchase_id, expiry_date, tier

### 4.2 License Validation

Plugin developers can validate licenses via API:

```http
POST /v1/plugins/{plugin_id}/validate-license
Authorization: Bearer {developer_api_key}
Content-Type: application/json

{
  "license_key": "MEKONG-PLUGIN-...",
  "machine_id": "optional-hardware-fingerprint"
}

Response:
{
  "valid": true,
  "user_id": "opc_001_abc123",
  "tier": "pro",
  "expires_at": "2027-06-21T00:00:00Z",
  "features": ["feature1", "feature2"]
}
```

### 4.3 License Delivery

**Delivery methods:**
1. **Dashboard:** User can copy from "My Plugins" page
2. **Email:** Sent to user's registered email immediately after purchase
3. **CLI:** `mekong plugin license get <plugin-id>` displays license key
4. **Zalo OA:** For VN users, sent via Zalo message

### 4.4 License Expiry & Renewal

- **Subscription plugins:** License auto-renewed on successful payment; access revoked if payment fails (grace period 7 days)
- **One-time plugins:** License never expires (perpetual access to that version)
- **Tier upgrades:** New license issued for upgraded tier, old license remains valid for old tier

---

## 5. Developer Dashboard & Payout System

### 5.1 Developer Dashboard Features

**URL:** `https://dashboard.cashclaw.cc/developer`

**Core Sections:**

#### 1. Overview (Metrics)
- Total lifetime earnings
- Monthly recurring revenue (for subscriptions)
- Number of active licenses
- Recent transactions (last 30 days)
- Geographic distribution of customers

#### 2. Plugin Management
- List of published plugins (status: draft/published/rejected)
- Upload new plugin (ZIP upload with plugin.json manifest)
- Edit plugin metadata (description, screenshots, pricing)
- Version management (publish new version, deprecate old)
- Analytics per plugin: downloads, revenue, refunds

#### 3. Financial Reports
- Payout history (date, amount, method)
- Upcoming payout (scheduled date, amount)
- Withdrawal requests (minimum $100)
- Tax forms (W-8BEN for non-US, 1099 for US)
- Earnings by currency

#### 4. Payout Configuration
- Preferred payout method: Stripe Connect, PayPal, Bank Transfer
- Bank account details (for VN transfers)
- Tax information (W-8BEN/W-9)
- Minimum payout threshold ($50-$500 configurable)
- Payout schedule: Monthly (15th of month) or Quarterly

#### 5. License Management
- View generated licenses (search by user/email)
- Revoke license (with reason, optional refund)
- Generate replacement license (if user loses key)
- License validation logs (API calls, success/failure)

#### 6. Notifications
- New sale email/Slack webhook
- Low balance alert (< $100 pending)
- Payout processed notification
- Refund issued notification
- Plugin review status update

### 5.2 Payout Schedule & Thresholds

| Developer Tier | Min. Payout | Schedule | Methods |
|----------------|-------------|----------|---------|
| **Standard** | $100 | Monthly (15th) | Stripe, PayPal, Bank |
| **Preferred** ($10k+ lifetime) | $50 | Weekly (Friday) | Stripe, Bank |
| **Enterprise** ($100k+ lifetime) | Any amount | Weekly (daily option) | Bank wire, Stripe |

**Payout eligibility:**
- Account verified (identity, tax info)
- Minimum threshold met
- No holds/disputes on recent transactions
- 7-day hold on first payout (fraud prevention)

### 5.3 Revenue Share Calculation

**Formula:**
```
Developer Payout = (Plugin Sale Price - Payment Processing Fee - Marketplace Fee) × (1 - Tax Withholding if applicable)

Example (US developer, $100 plugin, Stripe):
- Sale price: $100.00
- Processing fee: $2.90 + $0.30 = $3.20
- Marketplace fee: $100 × 20% = $20.00
- Gross to Mekong: $23.20
- Net to developer: $100 - $23.20 = $76.80
- 1099 issued at year-end for $76.80 × number of sales
```

**For VN developer (bank transfer):**
- Sale price: 499,000₫ ($19.99)
- Processing fee: ~1% = 4,990₫
- Marketplace fee: 499,000 × 20% = 99,800₫
- Net: 499,000 - 4,990 - 99,800 = 394,210₫ (~$15.77)
- Payout via bank transfer (Vietcombank, MB, etc.)

---

## 6. Competitive Analysis

### 6.1 Marketplace Fee Benchmarks

| Marketplace | Commission | Notes |
|-------------|------------|-------|
| **WordPress.org** | 0% (free plugins only) | No paid plugin marketplace |
| **Shopify App Store** | 30% first month, 80% after | Plus 0.5-2% payment fee |
| **VS Code Marketplace** | 0% (Microsoft absorbs) | No cost for extensions |
| **GitHub Marketplace** | 15-25% + payment fee | Varies by integration type |
| **Chrome Web Store** | 5% (for payments) | Developer keeps 95% |
| **Unity Asset Store** | 30% standard, 50% for Unity | Asset store takes half |
| **Unreal Engine Marketplace** | 12% after first $1M | 88% to developer |
| **App Store (Apple)** | 30% (15% for small) | High due to distribution |
| **Google Play** | 30% (15% for small) | Similar to Apple |

**Mekong positioning:** 20% commission is competitive (better than Shopify/Unity, reasonable vs GitHub).

### 6.2 Differentiation

- **Lower fees than app stores** (20% vs 30%)
- **Developer-friendly payout** (weekly/monthly vs 60+ day holds)
- **Multi-currency** (USD + VND for Vietnamese developers)
- **Local payment** (VietQR integration for VN market)
- **No exclusivity requirements** (developers can sell elsewhere)
- **Plugin system open source** (no vendor lock-in)

---

## 7. Implementation Architecture

### 7.1 Database Schema

```sql
-- Plugins table
CREATE TABLE plugins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    developer_id UUID NOT NULL REFERENCES users(id),
    slug VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    short_description VARCHAR(500),
    version VARCHAR(50) NOT NULL,
    price_usd DECIMAL(10,2) NOT NULL,
    price_vnd DECIMAL(12,0), -- optional VND display price
    pricing_model VARCHAR(20) NOT NULL CHECK (pricing_model IN ('free', 'one_time', 'subscription_monthly', 'subscription_annual', 'usage_based', 'tiered')),
    currency VARCHAR(3) DEFAULT 'USD',
    commission_rate DECIMAL(4,3) DEFAULT 0.20, -- 0.20 = 20%
    is_published BOOLEAN DEFAULT FALSE,
    published_at TIMESTAMPTZ,
    downloads_count INTEGER DEFAULT 0,
    revenue_total_usd DECIMAL(12,2) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Plugin versions
CREATE TABLE plugin_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plugin_id UUID NOT NULL REFERENCES plugins(id),
    version VARCHAR(50) NOT NULL,
    zip_url VARCHAR(500) NOT NULL,
    changelog TEXT,
    is_current BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(plugin_id, version)
);

-- Licenses
CREATE TABLE licenses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plugin_id UUID NOT NULL REFERENCES plugins(id),
    user_id UUID NOT NULL REFERENCES users(id),
    license_key VARCHAR(255) UNIQUE NOT NULL,
    purchase_id UUID REFERENCES purchases(id),
    tier VARCHAR(50), -- for tiered plugins
    valid_from TIMESTAMPTZ NOT NULL,
    valid_until TIMESTAMPTZ, -- NULL for perpetual (one-time)
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Purchases/transactions
CREATE TABLE purchases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plugin_id UUID NOT NULL REFERENCES plugins(id),
    user_id UUID NOT NULL REFERENCES users(id),
    license_id UUID REFERENCES licenses(id),
    payment_provider VARCHAR(20) NOT NULL, -- 'stripe', 'polar', 'bank_transfer'
    payment_intent_id VARCHAR(255), -- provider's transaction ID
    amount_usd DECIMAL(10,2) NOT NULL,
    amount_vnd DECIMAL(12,0),
    currency VARCHAR(3) NOT NULL,
    processing_fee_usd DECIMAL(10,2) NOT NULL,
    commission_usd DECIMAL(10,2) NOT NULL,
    developer_payout_usd DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'succeeded', 'failed', 'refunded', 'disputed')),
    refund_amount_usd DECIMAL(10,2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Developer wallets/payouts
CREATE TABLE developer_wallets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    developer_id UUID UNIQUE NOT NULL REFERENCES users(id),
    balance_usd DECIMAL(12,2) DEFAULT 0,
    balance_vnd DECIMAL(15,0) DEFAULT 0,
    pending_payout_usd DECIMAL(12,2) DEFAULT 0,
    total_earned_usd DECIMAL(12,2) DEFAULT 0,
    payout_threshold_usd DECIMAL(10,2) DEFAULT 100,
    preferred_payout_method VARCHAR(20), -- 'stripe', 'paypal', 'bank'
    bank_account JSONB, -- encrypted bank details
    tax_withholding_rate DECIMAL(5,4) DEFAULT 0, -- IRS 30% for foreign, etc.
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Payouts
CREATE TABLE payouts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    developer_id UUID NOT NULL REFERENCES users(id),
    amount_usd DECIMAL(12,2) NOT NULL,
    amount_vnd DECIMAL(15,0),
    payout_method VARCHAR(20) NOT NULL,
    provider_transaction_id VARCHAR(255),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    scheduled_date DATE NOT NULL,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 7.2 API Endpoints

#### Purchase Plugin

```http
POST /v1/marketplace/plugins/{plugin_id}/purchase
Authorization: Bearer {user_token}
Content-Type: application/json

{
  "currency": "USD",
  "payment_method": "stripe",
  "tier": "pro"  // for tiered plugins
}

Response (201 Created):
{
  "purchase_id": "pur_abc123",
  "payment_intent_client_secret": "pi_xxx_secret_yyy",
  "amount_usd": 99.99,
  "redirect_url": "https://checkout.stripe.com/pay/..."
}
```

#### Validate License

```http
POST /v1/plugins/{plugin_id}/validate-license
Authorization: Bearer {developer_api_key}
Content-Type: application/json

{
  "license_key": "MEKONG-PLUGIN-...",
  "machine_fingerprint": "optional"
}

Response (200 OK):
{
  "valid": true,
  "user_id": "opc_001_abc123",
  "tier": "pro",
  "expires_at": "2027-06-21T00:00:00Z",
  "features": ["feature1", "feature2"]
}
```

#### Developer Earnings Dashboard

```http
GET /v1/developer/earnings
Authorization: Bearer {developer_api_key}
Query: ?period=monthly&start=2026-06-01&end=2026-06-30

Response:
{
  "period": "monthly",
  "total_earnings_usd": 1234.56,
  "total_sales": 45,
  "refunds": 2,
  "net_earnings_usd": 1189.30,
  "by_plugin": [
    {
      "plugin_id": "plugin_abc",
      "name": "Awesome Plugin",
      "sales": 20,
      "earnings_usd": 456.78
    }
  ],
  "upcoming_payout": {
    "amount_usd": 1189.30,
    "scheduled_date": "2026-07-15",
    "method": "stripe"
  }
}
```

---

## 8. Compliance & Tax

### 8.1 Tax Compliance

**For US Developers:**
- 1099-K issued if >$600/year in earnings (post-2022 IRS threshold)
- Mekong reports to IRS
- Developer responsible for income tax

**For Non-US Developers:**
- W-8BEN form required (certify foreign status)
- 30% withholding on US-source revenue (unless tax treaty applies)
- Provide tax ID for reduced withholding if treaty exists

**For Vietnam Developers:**
- No US tax withholding (treaty benefits)
- Report earnings as income on Vietnamese tax return
- Mekong provides annual earnings statement (no 1099)

### 8.2 Refund Policy

- **One-time purchases:** 30-day refund window, no questions asked
- **Subscriptions:** Prorated refund if cancelled mid-cycle; full refund if cancelled within 14 days
- **Usage-based:** No refund for consumed credits; unused credits refunded
- **Refund processing:** 5-10 business days; developer revenue reversed proportionally

**Refund scenarios:**
- Plugin doesn't work as described → full refund, developer gets 0
- User changed mind → full refund, developer loses full revenue
- Accidental purchase → full refund, no penalty

### 8.3 Disputes & Chargebacks

- **User disputes Stripe/Polar:** 7-14 day resolution period
- **If resolved in user's favor:** Revenue clawed back from developer's balance (or future earnings if balance insufficient)
- **If resolved in developer's favor:** Revenue restored + dispute fee covered by Mekong
- **Excessive disputes (>1% of sales):** Developer account review, possible suspension

---

## 9. Developer Onboarding

### 9.1 Developer Account Setup

1. **Sign up** at `dashboard.cashclaw.cc/developer/register`
2. **Verify email** (click link)
3. **Submit identity verification** (government ID, selfie)
4. **Provide tax information** (W-8BEN/W-9)
5. **Configure payout method** (Stripe Connect, bank account, PayPal)
6. **Accept Developer Agreement** (terms, revenue share, content policy)
7. **Ready to publish** (verification 1-3 business days)

### 9.2 Plugin Submission Process

```
1. Developer creates plugin (see plugin SDK docs)
2. ZIP package with plugin.json manifest
3. Upload via dashboard or API
4. Automated validation:
   - ✅ Manifest valid JSON
   - ✅ Required fields present
   - ✅ No malicious code (virus scan)
   - ✅ Doesn't conflict with existing plugin
5. Manual review (1-3 business days):
   - ✅ Functionality check
   - ✅ Description quality
   - ✅ Screenshots/videos present
   - ✅ Pricing reasonable
6. Status: Published or Rejected (with feedback)
7. If published: Available in marketplace immediately
```

### 9.3 Plugin Review Guidelines

**Approval criteria:**
- Solves real user problem
- Stable, no crashes
- Good documentation (README, usage examples)
- Reasonable performance (no excessive API calls)
- No trademark/copyright infringement
- No malware, spyware, or backdoors
- No spammy behavior (ads, data exfiltration)

**Rejection reasons:**
- Malicious code or security vulnerability
- Copyright/trademark violation
- Low-quality (broken, no README, no value)
- Spammy or misleading description
- Violates Mekong's acceptable use policy

---

## 10. Marketplace Discovery UX

### 10.1 Marketplace Layout

**URL:** `https://mekongmind.com/plugins` or dashboard → Marketplace tab

**Features:**
- Search bar (by name, description, tags)
- Filters: Category, Price (free/paid), Rating, Last updated
- Sort: Popular, Highest rated, Newest, Price (low-high)
- Plugin cards: Name, short description, price, rating, download count, author
- Category pages: Development, Finance, Marketing, Legal, etc.
- Featured plugins (curated by Mekong team)

### 10.2 Plugin Detail Page

```
┌────────────────────────────────────────────────────────┐
│ Plugin Name                                            │
│ By @developername | ★ 4.8 (127 reviews) | 5.2k downloads│
├────────────────────────────────────────────────────────┤
│ [Screenshot carousel]                                  │
├────────────────────────────────────────────────────────┤
│ Description: Full plugin description                   │
│ Features: • Feature 1 • Feature 2 • Feature 3         │
├────────────────────────────────────────────────────────┤
│ Pricing:                                               │
│   • Free tier: Basic commands (10 credits/day)        │
│   • Pro: $19.99/mo (unlimited)                        │
│   [Buy Now] [Subscribe]                               │
├────────────────────────────────────────────────────────┤
│ What's New: Version 2.1.0 - Added feature X           │
├────────────────────────────────────────────────────────┤
│ Reviews:                                               │
│   ★★★★★ "Great plugin, saved me 10 hours/week"       │
│   -- User123, June 2026                                │
├────────────────────────────────────────────────────────┤
│ Similar Plugins: [Plugin A] [Plugin B] [Plugin C]     │
└────────────────────────────────────────────────────────┘
```

### 10.3 Installation Flow

1. User clicks "Buy Now" or "Subscribe"
2. Checkout with Stripe/Polar (one-time or subscription)
3. License key generated automatically
4. Plugin installed via CLI: `mekong plugin install <plugin-slug> --license <key>`
5. Dashboard shows installed plugins; can enable/disable
6. License validated on each plugin load (offline cache 24h)

---

## 11. Subscription Management

### 11.1 Recurring Billing

- **Stripe/Polar** handle automatic recurring charges
- **Billing cycle:** Monthly or annual (based on subscription type)
- **Dunning:** 3 retries over 7 days before cancellation
- **Failed payment:** Access continues for 7 days grace period
- **Cancellation:** User can cancel anytime via dashboard → no further charges, access until period end

### 11.2 Upgrades & Downgrades

- **Upgrade:** Immediate, prorated charge for remainder of billing cycle
- **Downgrade:** Effective at next billing cycle (no prorated refund)
- **Tier changes:** New license issued for new tier; old license invalidated

---

## 12. Developer Analytics

### 12.1 Metrics Available

- **Downloads:** Total, unique users, by version
- **Revenue:** Gross, net, by country, by currency
- **Customers:** New vs returning, geographic distribution
- **Usage:** Commands executed per day, by user segment
- **Retention:** % of users still active after 30/60/90 days
- **Conversion:** View → install, trial → paid (if freemium)
- **Refunds:** Rate, reasons, monetary impact

### 12.2 Dashboard Visualizations

- Revenue trend line (last 30/90 days)
- Top countries by revenue
- Most popular plugin features used
- Customer lifetime value distribution
- Churn rate over time (for subscriptions)

---

## 13. Anti-Fraud Measures

- **Rate limiting:** Max 10 purchases per hour per user/IP
- **Device fingerprinting:** Detect suspicious purchase patterns
- **Manual review:** Transactions > $1000 flagged
- **License key validation:** 24h cache, server-side verification for critical plugins
- **Refund abuse detection:** >3 refunds in 30 days → account review
- **Money laundering prevention:** Transaction reporting for >$10k/year

---

## 14. Future Enhancements

### Phase 2 (Months 6-12)

- [ ] Affiliate/referral program (5% commission for referrals)
- [ ] Plugin bundle sales (multiple plugins at discount)
- [ ] Enterprise licensing (negotiated terms, custom contracts)
- [ ] White-label marketplace for agencies
- [ ] Plugin marketplace API for third-party integrations

### Phase 3 (Year 2+)

- [ ] Plugin subscription tiers with usage-based overage
- [ ] Plugin marketplace in Vietnamese (full localization)
- [ ] Mobile app for managing plugins
- [ ] Advanced analytics cohort analysis
- [ ] A/B testing for plugin pricing/packaging
- [ ] Plugin certification program (verified quality)

---

## 15. Success Metrics

| Metric | Target (Month 6) | Target (Month 12) | Measurement |
|--------|------------------|-------------------|-------------|
| Active plugins | 50 | 200 | `plugin.count_active` |
| Plugin revenue/month | $5k | $25k | `revenue.plugin_mrr` |
| Developer payouts/month | $4k | $20k | `payout.total` |
| Avg. revenue per developer | $200/mo | $500/mo | `developer.revenue_avg` |
| Plugin downloads/month | 1k | 10k | `plugin.downloads` |
| Marketplace conversion rate | 3% | 5% | visitors → purchases |
| Developer NPS | 40 | 50 | `developer.nps` |

---

## 16. Implementation Checklist

### Backend

- [x] Database schema (plugins, licenses, purchases, wallets, payouts)
- [ ] API endpoints for purchase, license validation, developer dashboard
- [ ] Webhook handlers for Stripe/Polar payment events
- [ ] Revenue allocation logic (split developer vs Mekong)
- [ ] Payout calculation and scheduling
- [ ] Tax reporting (1099, W-8BEN, withholding)
- [ ] Refund processing workflow

### Frontend

- [ ] Marketplace UI (public): plugin listing, detail pages, search/filter
- [ ] Developer dashboard: plugin management, financial reports, payout config
- [ ] User "My Plugins" page: license keys, installation instructions
- [ ] Checkout flow: Stripe/Polar integration, success/failure pages

### Operations

- [ ] Plugin review process and guidelines
- [ ] Developer agreement and terms of service
- [ ] Support procedures for plugin-related issues
- [ ] Refund policy and dispute resolution
- [ ] Fraud detection and prevention systems
- [ ] Payout reconciliation and accounting

### Compliance

- [ ] Tax compliance (US 1099, foreign withholding)
- [ ] PCI DSS compliance (Stripe handles card data)
- [ ] Terms of service for marketplace
- [ ] Privacy policy covering plugin data
- [ ] Export controls (no sanctioned countries)

---

## 17. Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Low developer adoption | Medium | High | Offer high revenue share (80%), low fees, marketing to existing plugin authors |
| Payment provider downtime | Low | Medium | Multiple providers (Stripe + Polar), graceful degradation |
| Fraudulent purchases | Medium | Medium | Rate limiting, manual review for large transactions, 7-day hold on first payout |
| Developer churn (selling elsewhere) | Medium | Medium | Competitive revenue share, fast payouts, community engagement |
| Plugin piracy/license sharing | High | Medium | License validation with periodic server checks, hardware fingerprinting optional |
| Tax compliance issues | Low | High | Use Stripe Tax/Polar Tax automation, consult tax advisors, issue correct forms |
| Marketplace spam (low-quality plugins) | Medium | Medium | Rigorous review process, community ratings, takedown process |

---

**Next Steps:**
1. Implement backend API endpoints for purchases and license management
2. Build Stripe/Polar checkout integration
3. Create developer dashboard UI
4. Launch with 10-20 initial plugins (invite-only)
5. Open marketplace to all developers (after beta)
6. Monitor revenue, adoption, developer satisfaction

**Related Documents:**
- `docs/plugin-developer-guide.md` — Plugin development guide
- `docs/plugin-manifest-format.md` — Plugin manifest specification
- `docs/api/partner-monitoring-openapi.yaml` — API specification (includes marketplace endpoints)

---

**Sources:**
- Competitive benchmark: Shopify 30%, GitHub 15-25%, Unreal 12%
- Mekong strategy: 20% standard commission, 80% developer revenue
- Payment fees: Stripe 2.9%+0.30, Polar similar, VN bank ~1-2%
- Payout schedule: Monthly (15th) or weekly for preferred developers
