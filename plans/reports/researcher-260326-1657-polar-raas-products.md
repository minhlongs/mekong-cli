# Polar.sh RaaS 5-Tier Product Listings Research Report

**Date:** 2026-03-26
**Task:** Create Polar.sh product listings for OpenClaw Robot-as-a-Service
**Status:** Research Complete — Ready for Implementation

---

## Executive Summary

OpenClaw (AI-operated business platform) requires 5 subscription tiers on Polar.sh. This report documents:
1. Polar API endpoints for product creation
2. Safe product descriptions (avoiding prohibited terms from incident 2026-03-23)
3. JSON payloads for each tier
4. Webhook setup for MCU credit provisioning
5. Existing Polar integration in codebase

**CRITICAL:** Polar account flagged in March for "wellness/health" terminology. All descriptions use safe B2B SaaS language.

---

## Part 1: Polar API Overview

### API Access
- **Base URL:** `https://api.polar.sh`
- **Authentication:** Bearer token (`Authorization: Bearer sk_live_YOUR_API_KEY`)
- **Rate Limit:** Standard rate limiting with `Retry-After` header on 429 responses
- **Timeout:** 10 seconds recommended (with exponential backoff)

### Endpoints
- **Create Product:** `POST /v1/products`
- **List Products:** `GET /v1/products`
- **Get Product:** `GET /v1/products/{id}`
- **Update Product:** `PATCH /v1/products/{id}`
- **Create Price/Subscription:** `POST /v1/products/{id}/prices` (or via product creation)
- **List Subscriptions:** `GET /v1/subscriptions`
- **Webhooks:** `POST /webhooks/` + signature verification (Standard Webhooks spec)

### SDK Available
- **npm:** `@polar-sh/sdk@0.41.5` (installed in mekong-cli)
- **Features:** Type-safe, built-in retry/backoff, webhook verification
- **Key Classes:**
  - `PolarClient` — Fetch products, subscriptions
  - `PolarWebhookVerifier` — HMAC-SHA256 verification
  - `BenefitGrants`, `CustomerMeters` — Metered billing

---

## Part 2: Polar Acceptable Use Policy — COMPLIANCE CRITICAL

### Incident (2026-03-23)
- **Account:** "Wellneusraas" (for Well project)
- **Reason for flag:** Product description contained "wellness/health" keywords
- **Result:** Payments DENIED until remediation

### PROHIBITED Words (NEVER use)
```
health, wellness, medical, therapeutic, diagnosis, treatment
prescription, clinical, patient, healthcare, fitness, tracking
doctor, nurse, therapist, consultant (implies medical service)
```

### SAFE Words (USE THESE)
```
B2B SaaS, business operations, automation platform
team management, task orchestration, workflow automation
AI-powered, mission credits, agent-based, dashboard
business intelligence, analytics, performance monitoring
operations management, mission execution platform
```

### Compliance Strategy
- Describe OpenClaw as **"AI-operated business automation platform"**
- Focus on **workflow execution, task coordination, mission planning**
- Highlight **MCU credits, agent teams, dashboard analytics**
- Zero mention of any health/wellness/medical use cases
- Product descriptions < 200 chars, clear business focus

---

## Part 3: 5-Tier Products — Safe Descriptions

### Product Definition Structure (Polar API)

```json
{
  "name": "OpenClaw — Tier Name",
  "description": "...",  // Max 200 chars, NO prohibited words
  "prices": [{
    "type": "recurring",
    "currency": "usd",
    "recurring_interval": "month",
    "price_amount": CENTS,  // $49.00 = 4900 cents
    "billing_cycle_anchor": null
  }],
  "metadata": {
    "tier": "starter|pro|growth|scale|enterprise",
    "mcu_credits": 200,
    "target_audience": "Solo founders"
  }
}
```

---

### Tier 1: Starter — $49/month

**Purpose:** Solo founders, indie developers, single operator

**Safe Product Description (Polar):**
```
AI-operated business automation. 200 MCU credits/month for workflow
orchestration, task execution, team coordination. Best for solo teams.
```

**JSON Payload:**
```json
{
  "name": "OpenClaw Starter — $49/month",
  "description": "AI-operated business automation. 200 MCU credits/month for workflow orchestration, task execution, team coordination. Best for solo teams.",
  "prices": [{
    "type": "recurring",
    "currency": "usd",
    "recurring_interval": "month",
    "price_amount": 4900,
    "billing_cycle_anchor": null
  }],
  "metadata": {
    "tier": "starter",
    "mcu_credits": 200,
    "target_audience": "Solo founders / Indie developers",
    "features": [
      "200 MCU credits/month",
      "AI mission planning & execution",
      "Basic dashboard access",
      "Email support"
    ]
  }
}
```

**Product ID (set after creation):** `POLAR_STARTER_PRODUCT_ID` → store in .env

---

### Tier 2: Pro — $99/month

**Purpose:** Small teams, growing businesses, power users

**Safe Product Description (Polar):**
```
500 MCU credits/month. Full team access, advanced mission features,
API integration, priority support. Scale operations across 3-5 operators.
```

**JSON Payload:**
```json
{
  "name": "OpenClaw Pro — $99/month",
  "description": "500 MCU credits/month. Full team access, advanced mission features, API integration, priority support. Scale operations across 3-5 operators.",
  "prices": [{
    "type": "recurring",
    "currency": "usd",
    "recurring_interval": "month",
    "price_amount": 9900,
    "billing_cycle_anchor": null
  }],
  "metadata": {
    "tier": "pro",
    "mcu_credits": 500,
    "target_audience": "Small teams (3-5 people)",
    "features": [
      "500 MCU credits/month",
      "Team collaboration (5 users)",
      "API access for integrations",
      "Advanced analytics dashboard",
      "Priority email support (4-hour response)",
      "Webhook events for custom workflows"
    ]
  }
}
```

**Product ID:** `POLAR_PRO_PRODUCT_ID` → store in .env

---

### Tier 3: Growth — $199/month

**Purpose:** Growing businesses, multi-team operations

**Safe Product Description (Polar):**
```
1,500 MCU credits/month. Multi-team coordination, custom agents,
advanced automation. For operations across 5-20+ team members.
```

**JSON Payload:**
```json
{
  "name": "OpenClaw Growth — $199/month",
  "description": "1,500 MCU credits/month. Multi-team coordination, custom agents, advanced automation. For operations across 5-20+ team members.",
  "prices": [{
    "type": "recurring",
    "currency": "usd",
    "recurring_interval": "month",
    "price_amount": 19900,
    "billing_cycle_anchor": null
  }],
  "metadata": {
    "tier": "growth",
    "mcu_credits": 1500,
    "target_audience": "Growing businesses (5-20 people)",
    "features": [
      "1,500 MCU credits/month",
      "Team collaboration (20 users)",
      "Custom agent deployment",
      "Advanced mission templates",
      "Real-time execution dashboard",
      "API + webhook premium support",
      "Slack integration"
    ]
  }
}
```

**Product ID:** `POLAR_GROWTH_PRODUCT_ID` → store in .env

---

### Tier 4: Scale — $299/month

**Purpose:** Scaling companies, enterprise operations, high-volume automation

**Safe Product Description (Polar):**
```
3,000 MCU credits/month. Unlimited agent teams, production automation,
SLA support. For mission-critical operations at scale (20-100+ people).
```

**JSON Payload:**
```json
{
  "name": "OpenClaw Scale — $299/month",
  "description": "3,000 MCU credits/month. Unlimited agent teams, production automation, SLA support. For mission-critical operations at scale (20-100+ people).",
  "prices": [{
    "type": "recurring",
    "currency": "usd",
    "recurring_interval": "month",
    "price_amount": 29900,
    "billing_cycle_anchor": null
  }],
  "metadata": {
    "tier": "scale",
    "mcu_credits": 3000,
    "target_audience": "Scaling companies (20-100+ people)",
    "features": [
      "3,000 MCU credits/month",
      "Unlimited team members",
      "Unlimited custom agents",
      "Production automation suite",
      "99% uptime SLA",
      "Dedicated support + Slack channel",
      "Advanced monitoring & alerting",
      "White-label options"
    ]
  }
}
```

**Product ID:** `POLAR_SCALE_PRODUCT_ID` → store in .env

---

### Tier 5: Enterprise — $499/month

**Purpose:** Large organizations, mission-critical operations, custom requirements

**Safe Product Description (Polar):**
```
Unlimited MCU credits. Enterprise automation, dedicated infrastructure,
custom integrations, 24/7 support. For large-scale mission-critical ops.
```

**JSON Payload:**
```json
{
  "name": "OpenClaw Enterprise — $499/month",
  "description": "Unlimited MCU credits. Enterprise automation, dedicated infrastructure, custom integrations, 24/7 support. For large-scale mission-critical ops.",
  "prices": [{
    "type": "recurring",
    "currency": "usd",
    "recurring_interval": "month",
    "price_amount": 49900,
    "billing_cycle_anchor": null
  }],
  "metadata": {
    "tier": "enterprise",
    "mcu_credits": null,
    "mcu_limit": "unlimited",
    "target_audience": "Large organizations / Mission-critical operations",
    "features": [
      "Unlimited MCU credits",
      "Unlimited users & agents",
      "Dedicated infrastructure",
      "Custom agent development",
      "Enterprise SSO (SAML2)",
      "99.95% uptime SLA + support",
      "24/7 phone + email support",
      "Custom integrations",
      "On-premises deployment option",
      "Audit logging & compliance"
    ]
  }
}
```

**Product ID:** `POLAR_ENTERPRISE_PRODUCT_ID` → store in .env

---

## Part 4: Webhook Setup for MCU Credit Provisioning

### Polar Webhook Events (Standard Webhooks Spec)

When customer subscribes → Polar fires webhook to your endpoint:

```
Webhook Event: subscription.created
├─ customer_id (e.g., "customer_abc123")
├─ subscription_id (e.g., "sub_def456")
├─ product_id (e.g., "prod_starter")
├─ status: "active"
├─ started_at: "2026-03-26T10:00:00Z"
└─ current_period_end: "2026-04-26T10:00:00Z"
```

### Implementation Flow (from codebase)

**1. Webhook Verification** (`polar-webhook-verify.js` — already in codebase)

```javascript
const PolarWebhookVerifier = require('./polar-webhook-verify.js');

app.post('/raas/billing/webhook', (req, res) => {
  const verifier = new PolarWebhookVerifier(process.env.POLAR_WEBHOOK_SECRET);

  try {
    const result = verifier.process(
      JSON.stringify(req.body),
      {
        'webhook-id': req.headers['webhook-id'],
        'webhook-timestamp': req.headers['webhook-timestamp'],
        'webhook-signature': req.headers['webhook-signature']
      }
    );

    if (!result.success) {
      return res.status(401).json({ error: 'Invalid signature' });
    }

    // Process event
    const event = result.event;
    return res.json({ received: true });
  } catch (e) {
    return res.status(400).json({ error: e.message });
  }
});
```

**2. Credit Provisioning** (create in `src/raas/billing.py`)

```python
# Pseudocode for webhook handler
async def handle_subscription_created(event: dict):
    """
    Webhook payload structure:
    {
      "type": "subscription.created",
      "data": {
        "id": "sub_abc123",
        "customer_id": "cust_xyz789",
        "product_id": "prod_starter",
        "status": "active",
        "started_at": "2026-03-26T10:00:00Z",
        "current_period_end": "2026-04-26T10:00:00Z"
      }
    }
    """

    event_data = event.get('data', {})
    subscription_id = event_data['id']
    customer_id = event_data['customer_id']
    product_id = event_data['product_id']

    # Map product_id to MCU credits
    CREDITS_MAP = {
        os.getenv('POLAR_STARTER_PRODUCT_ID'): 200,
        os.getenv('POLAR_PRO_PRODUCT_ID'): 500,
        os.getenv('POLAR_GROWTH_PRODUCT_ID'): 1500,
        os.getenv('POLAR_SCALE_PRODUCT_ID'): 3000,
        os.getenv('POLAR_ENTERPRISE_PRODUCT_ID'): 0,  # Unlimited
    }

    credits = CREDITS_MAP.get(product_id, 0)

    # Store subscription + provision credits
    db = get_database()

    await db.execute("""
        INSERT INTO subscriptions (
            subscription_id, customer_id, product_id,
            status, period_end, created_at
        ) VALUES (?, ?, ?, ?, ?, datetime('now'))
    """, (subscription_id, customer_id, product_id, 'active', event_data['current_period_end']))

    await db.execute("""
        INSERT INTO credits (
            customer_id, amount, reason, period_end
        ) VALUES (?, ?, ?, ?)
    """, (customer_id, credits, 'subscription_created', event_data['current_period_end']))

    await db.commit()

    # Log for audit
    await log_billing_event(
        customer_id=customer_id,
        event_type='subscription.created',
        subscription_id=subscription_id,
        credits_granted=credits
    )
```

**3. Webhook Endpoint Configuration**

```bash
# In Polar Dashboard → Settings → Webhooks:

Endpoint URL: https://api.agencyos.network/raas/billing/webhook
Events to subscribe:
  ✓ subscription.created
  ✓ subscription.updated
  ✓ subscription.canceled
  ✓ order.created (for one-time charges)

Secret: (Polar generates) → Store as POLAR_WEBHOOK_SECRET in .env
```

---

## Part 5: Existing Polar Integration in Codebase

### Files Found

| Path | Purpose | Status |
|------|---------|--------|
| `packages/mekong-cli-core/src/payments/polar-client.ts` | TypeScript SDK wrapper | ✓ Implemented |
| `.claude/skills/payment-integration/scripts/polar-webhook-verify.js` | Webhook verification | ✓ Implemented |
| `.env.example` | Config template | ✓ Has POLAR_* vars |
| `docs/pricing.md` | Pricing doc (internal) | ✓ Current |
| `docs/raas-revenue-architecture.md` | RaaS architecture | ✓ Current |

### PolarClient API (TypeScript)

**Location:** `/Users/macbookprom1/mekong-cli/packages/mekong-cli-core/src/payments/polar-client.ts`

**Key Methods:**
- `checkSubscription(customerId)` — Verify active subscription
- `listProducts()` — Get all products
- `getSubscription(subscriptionId)` — Get subscription details
- Built-in retry with exponential backoff (3 retries, base 500ms)
- Timeout: 10 seconds

**Usage Example:**
```typescript
const client = new PolarClient({ apiKey: process.env.POLAR_API_KEY! });

// List products
const result = await client.listProducts();
if (result.ok) {
  console.log(result.value); // PolarProduct[]
}

// Check subscription
const subResult = await client.checkSubscription('cust_abc123');
if (subResult.ok) {
  console.log(subResult.value.active); // boolean
  console.log(subResult.value.subscription); // PolarSubscription
}
```

### Environment Variables (Current)

```bash
# From .env.example
POLAR_API_KEY=sk_live_YOUR_POLAR_API_KEY
POLAR_WEBHOOK_SECRET=whsec_YOUR_WEBHOOK_SECRET
POLAR_SUCCESS_URL=https://agencyos.network/success
POLAR_CANCEL_URL=https://agencyos.network/pricing

# Product IDs (to be populated after creation)
POLAR_STARTER_PRODUCT_ID=prod_starter
POLAR_PRO_PRODUCT_ID=prod_pro
POLAR_GROWTH_PRODUCT_ID=prod_growth
POLAR_SCALE_PRODUCT_ID=prod_scale
POLAR_ENTERPRISE_PRODUCT_ID=prod_enterprise
```

### Webhook Verification Implementation (Existing)

**Location:** `.claude/skills/payment-integration/scripts/polar-webhook-verify.js`

**Algorithm:** HMAC-SHA256 verification following Standard Webhooks spec
```javascript
// Signature = base64(HMAC-SHA256(timestamp.payload, secret))
crypto
  .createHmac('sha256', Buffer.from(secret, 'base64'))
  .update(`${timestamp}.${payload}`)
  .digest('base64')
```

**Timestamp Protection:** Rejects webhooks > 5 minutes old

---

## Part 6: Implementation Roadmap

### Step 1: Create Products in Polar Dashboard (Manual)
1. Visit `https://polar.sh/mekong-cli` (organization dashboard)
2. Create 5 products using JSON payloads from Part 3
3. Copy Product IDs → `.env` file (POLAR_*_PRODUCT_ID)

**OR programmatically via API:**
```bash
curl -X POST https://api.polar.sh/v1/products \
  -H "Authorization: Bearer sk_live_..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "OpenClaw Starter...",
    "description": "...",
    ...
  }'
```

### Step 2: Configure Webhook Endpoint
1. Polar Dashboard → Settings → Webhooks
2. Add endpoint: `https://api.agencyos.network/raas/billing/webhook`
3. Subscribe to: `subscription.created`, `subscription.updated`, `subscription.canceled`
4. Store secret in `.env` as `POLAR_WEBHOOK_SECRET`

### Step 3: Implement Webhook Handler (Python)
Create `src/raas/billing.py`:
- Verify webhook signature using existing JS verifier (call via subprocess or port to Python)
- Parse event → map product_id → credits
- Insert into SQLite (subscriptions + credits tables)
- Log for audit trail

### Step 4: Update Marketing Copy
- Landing page: Pricing tiers with safe descriptions (no health/wellness terms)
- Dashboard: Show MCU balance + tier info
- Email: Subscription confirmation with credits info

### Step 5: Testing
- Mock webhook event → verify credit provisioning
- Upgrade/downgrade → ensure credits update correctly
- Cancellation → stop credit provisioning

---

## Part 7: Compliance Checklist

- [ ] **CRITICAL:** All product descriptions reviewed for prohibited words
- [ ] No "health", "wellness", "medical", "therapy", "treatment" terms
- [ ] Descriptions focus on: "business automation", "workflow orchestration", "task execution"
- [ ] Product names generic: "OpenClaw — Tier Name"
- [ ] Metadata in JSON safe (no medical use cases in features list)
- [ ] Webhook secret securely stored in .env (not in git)
- [ ] API key in .env (not in code)
- [ ] Product IDs stored in .env after creation

---

## Unresolved Questions

1. **Checkout flow:** Should pricing page link directly to Polar checkout or custom flow through agencyos.network dashboard?
2. **Free tier:** Not included in current 5 tiers. Should we add "Free — $0/10 MCU" for trials?
3. **Overage pricing:** Enterprise tier has unlimited, but what's cost for overages in Scale tier?
4. **Annual billing:** Polar supports yearly subscriptions. Should we offer "10 months = 2 months free" discount?
5. **Metered billing:** Should "Pay-per-use overage" use Polar's metered credits API (`POST /v1/customer_meters`) for per-credit charges?

---

## Sources

- [Polar.sh GitHub Repository](https://github.com/polarsource/polar)
- [Polar.sh Documentation](https://polar.sh/docs/)
- [Medium: Polar Integration Guide](https://medium.com/@paudelronish/how-to-integrate-polar-payments-for-subscriptions-and-one-time-payments-in-next-js-fc79da765379)
- Existing codebase: `packages/mekong-cli-core/src/payments/polar-client.ts`
- Existing codebase: `.claude/skills/payment-integration/scripts/polar-webhook-verify.js`
- Incident note: Polar account flagged 2026-03-23 for "wellness" terminology

