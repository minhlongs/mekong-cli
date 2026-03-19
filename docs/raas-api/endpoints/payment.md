# Payment API — Vietnam Payment Gateways

> **Purpose**: Tích hợp cổng thanh toán Việt Nam MoMo và VNPAY để nạp credits.

---

## Endpoints Overview

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/v1/payment/pricing-vn` | ❌ | Get pricing tiers in VND |
| POST | `/v1/payment/create` | ✅ | Create payment request |
| POST | `/v1/payment/webhook/momo` | ❌ | MoMo webhook handler |
| POST | `/v1/payment/webhook/vnpay` | ❌ | VNPAY webhook handler |

---

## GET /v1/payment/pricing-vn — Pricing Tiers

### Request

```bash
curl -X GET https://agencyos.network/v1/payment/pricing-vn
```

### Response (200 OK)

```json
{
  "tiers": [
    {
      "id": "tier_free",
      "name": "Free",
      "name_vi": "Miễn Phí",
      "credits": 10,
      "price_vnd": 0,
      "price_usd": 0,
      "description": "Dùng thử miễn phí với 10 credits",
      "popular": false
    },
    {
      "id": "tier_starter",
      "name": "Starter",
      "name_vi": "Khởi Đầu",
      "credits": 50,
      "price_vnd": 199000,
      "price_usd": 8,
      "description": "Dành cho cá nhân mới bắt đầu",
      "popular": true
    },
    {
      "id": "tier_pro",
      "name": "Pro",
      "name_vi": "Chuyên Nghiệp",
      "credits": 200,
      "price_vnd": 499000,
      "price_usd": 20,
      "description": "Dành cho đội nhóm nhỏ",
      "popular": false
    },
    {
      "id": "tier_enterprise",
      "name": "Enterprise",
      "name_vi": "Doanh Nghiệp",
      "credits": 1000,
      "price_vnd": 2990000,
      "price_usd": 120,
      "description": "Dành cho tổ chức quy mô lớn",
      "popular": false
    }
  ],
  "currency": "VND",
  "updated_at": "2026-03-19T10:00:00Z"
}
```

### Pricing Tier Object

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique tier identifier |
| `name` | string | English tier name |
| `name_vi` | string | Vietnamese tier name |
| `credits` | integer | Credits included |
| `price_vnd` | integer | Price in Vietnamese Dong |
| `price_usd` | integer | Price in USD (reference) |
| `description` | string | Tier description |
| `popular` | boolean | Featured/most popular tier |

### Pricing Comparison

| Tier | Credits | Price (VND) | Price/credit | Best For |
|------|---------|-------------|--------------|----------|
| Free | 10 | 0 | 0đ | Trial |
| Starter | 50 | 199,000 | 3,980đ | Individuals |
| Pro | 200 | 499,000 | 2,495đ | Small teams |
| Enterprise | 1000 | 2,990,000 | 2,990đ | Large orgs |

---

## POST /v1/payment/create — Create Payment

### Request

```bash
curl -X POST https://agencyos.network/v1/payment/create \
  -H "Authorization: Bearer $RAAS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "gateway": "momo",
    "tier_id": "tier_starter",
    "return_url": "https://agencyos.network/billing/success"
  }'
```

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `gateway` | string | ✅ | Payment gateway: `momo` or `vnpay` |
| `tier_id` | string | ✅ | Pricing tier ID to purchase |
| `return_url` | string | ❌ | Redirect URL after payment |

### Payment Gateway Options

| Gateway | Type | Processing Fee | Settlement |
|---------|------|----------------|------------|
| MoMo | e-Wallet | 1.5% | T+1 |
| VNPAY | Bank Transfer | 1.2% | T+2 |

### Response (201 Created)

**For MoMo:**
```json
{
  "payment_id": "pay_abc123",
  "gateway": "momo",
  "status": "pending",
  "amount": 199000,
  "currency": "VND",
  "credits_to_add": 50,
  "momo_url": "https://payment.momo.vn/v2/gateway?order_id=pay_abc123&signature=xyz789",
  "qr_code_url": "https://storage.../qr/pay_abc123.png",
  "expires_at": "2026-03-19T11:00:00Z",
  "created_at": "2026-03-19T10:00:00Z"
}
```

**For VNPAY:**
```json
{
  "payment_id": "pay_def456",
  "gateway": "vnpay",
  "status": "pending",
  "amount": 499000,
  "currency": "VND",
  "credits_to_add": 200,
  "vnpay_url": "https://sandbox.vnpayment.vn/paymentv2/vpcpay.html?vnp_Amount=499000&vnp_OrderInfo=pay_def456&vnp_SecureHash=abc123",
  "expires_at": "2026-03-19T11:00:00Z",
  "created_at": "2026-03-19T10:00:00Z"
}
```

### Payment Response Object

| Field | Type | Description |
|-------|------|-------------|
| `payment_id` | string | Unique payment request ID |
| `gateway` | string | Selected payment gateway |
| `status` | string | `pending`, `completed`, `failed`, `expired` |
| `amount` | integer | Amount in VND |
| `currency` | string | `VND` |
| `credits_to_add` | integer | Credits to be added on success |
| `momo_url` | string | MoMo payment URL (if MoMo) |
| `qr_code_url` | string | QR code image URL (if MoMo) |
| `vnpay_url` | string | VNPAY payment URL (if VNPAY) |
| `expires_at` | string | Payment link expiry time |
| `created_at` | string | Payment request creation time |

### Payment Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  User       │     │  RaaS       │     │  MoMo/      │     │  RaaS       │
│  selects    │ →   │  creates    │ →   │  VNPAY      │ →   │  webhook    │
│  tier       │     │  payment    │     │  payment    │     │  receives   │
│             │     │  request    │     │  processed  │     │  confirm    │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                                                                   │
                                                                   ↓
                                                          ┌─────────────┐
                                                          │  Credits    │
                                                          │  added to   │
                                                          │  tenant     │
                                                          └─────────────┘
```

### Error Responses

**400 Invalid Tier:**
```json
{
  "error": "VALIDATION_ERROR",
  "message": "Invalid tier_id: 'invalid-tier'"
}
```

**400 Invalid Gateway:**
```json
{
  "error": "VALIDATION_ERROR",
  "message": "Invalid gateway. Must be 'momo' or 'vnpay'"
}
```

**402 Insufficient Credits:**
```json
{
  "error": "INSUFFICIENT_CREDITS",
  "message": "Current balance is 0 credits",
  "details": {
    "balance": 0,
    "required_for_operation": 1
  }
}
```

---

## POST /v1/payment/webhook/momo — MoMo Webhook

### Purpose

Nhận payment confirmation từ MoMo và tự động cộng credits.

### Request

```http
POST /v1/payment/webhook/momo
Content-Type: application/json

{
  "partner_code": "MOMO",
  "order_id": "pay_abc123",
  "request_id": "req_xyz789",
  "amount": 199000,
  "order_info": "Payment for tier_starter",
  "message": "Successful",
  "result_code": 0,
  "resp_code": "00",
  "signature": "abc123xyz789..."
}
```

### Request Body

| Field | Type | Description |
|-------|------|-------------|
| `partner_code` | string | MoMo partner code |
| `order_id` | string | Payment ID from RaaS |
| `request_id` | string | MoMo request ID |
| `amount` | integer | Amount in VND |
| `order_info` | string | Order description |
| `message` | string | Status message |
| `result_code` | integer | 0 = success, non-zero = failure |
| `resp_code` | string | Response code |
| `signature` | string | HMAC-SHA256 signature |

### Response (200 OK)

**Success:**
```json
{
  "status": "success",
  "payment_id": "pay_abc123",
  "credits_added": 50,
  "new_balance": 60
}
```

**Failure:**
```json
{
  "status": "failed",
  "payment_id": "pay_abc123",
  "reason": "Invalid signature"
}
```

### Signature Verification

```typescript
const secret = c.env.MOMO_WEBHOOK_SECRET;
const payload = `${order_id}${request_id}${amount}`;
const cryptoKey = await crypto.subtle.importKey(
  'raw',
  new TextEncoder().encode(secret),
  { name: 'HMAC', hash: 'SHA-256' },
  false,
  ['sign']
);
const sigBuffer = await crypto.subtle.sign('HMAC', cryptoKey, new TextEncoder().encode(payload));
const expectedSig = Array.from(new Uint8Array(sigBuffer))
  .map(b => b.toString(16).padStart(2, '0')).join('');

if (signature !== expectedSig) {
  return c.json({ status: 'failed', reason: 'Invalid signature' }, 401);
}
```

---

## POST /v1/payment/webhook/vnpay — VNPAY Webhook

### Purpose

Nhận payment confirmation từ VNPAY và tự động cộng credits.

### Request

```http
POST /v1/payment/webhook/vnpay
Content-Type: application/x-www-form-urlencoded

vnp_Amount=199000&
vnp_BankCode=VCB&
vnp_BankTranNo=VNPAY123456&
vnp_OrderInfo=pay_abc123&
vnp_PayDate=20260319100000&
vnp_ResponseCode=00&
vnp_TmnCode=MERCHANT123&
vnp_TransactionNo=789012&
vnp_TransactionStatus=00&
vnp_SecureHash=abc123xyz789...
```

### Request Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `vnp_Amount` | integer | Amount in VND |
| `vnp_BankCode` | string | Bank code |
| `vnp_BankTranNo` | string | Bank transaction number |
| `vnp_OrderInfo` | string | Payment ID from RaaS |
| `vnp_PayDate` | string | Payment datetime |
| `vnp_ResponseCode` | string | 00 = success |
| `vnp_TmnCode` | string | Merchant code |
| `vnp_TransactionNo` | string | Transaction number |
| `vnp_TransactionStatus` | string | 00 = success |
| `vnp_SecureHash` | string | SHA256 signature |

### Response (200 OK)

```
RSPCODE=00&MESSAGE=Success
```

### Credit Auto-Add Flow

```typescript
// On successful webhook verification:
const payment = await db.payments.get({ order_id: orderInfo });
if (payment) {
  await db.runTransaction(async (tx) => {
    // Update payment status
    await tx.payments.update(payment.id, {
      status: 'completed',
      completed_at: new Date().toISOString()
    });

    // Add credits to tenant
    const tenant = await tx.tenants.get(payment.tenant_id);
    await tx.tenants.update(tenant.id, {
      credit_balance: (tenant.credit_balance || 0) + payment.credits_to_add
    });

    // Create audit trail
    await tx.credit_transactions.create({
      tenant_id: tenant.id,
      type: 'purchase',
      amount: payment.credits_to_add,
      payment_id: payment.id,
      created_at: new Date().toISOString()
    });
  });
}
```

---

## Use Cases

### Individual Developer

```bash
# Purchase Starter tier via MoMo
curl -X POST https://agencyos.network/v1/payment/create \
  -H "Authorization: Bearer sk_test_abc123" \
  -H "Content-Type: application/json" \
  -d '{
    "gateway": "momo",
    "tier_id": "tier_starter"
  }'

# Response: MoMo QR code URL
# User scans QR → Pays 199kđ → 50 credits added instantly
```

### Small Agency

```bash
# Purchase Pro tier via VNPAY
curl -X POST https://agencyos.network/v1/payment/create \
  -H "Authorization: Bearer sk_live_xyz789" \
  -H "Content-Type: application/json" \
  -d '{
    "gateway": "vnpay",
    "tier_id": "tier_pro",
    "return_url": "https://agency.com/billing/success"
  }'

# Response: VNPAY payment URL
# User redirected → Bank login → Confirm → Redirected back → 200 credits added
```

### Enterprise

```bash
# Purchase Enterprise tier
curl -X POST https://agencyos.network/v1/payment/create \
  -H "Authorization: Bearer sk_live_enterprise" \
  -H "Content-Type: application/json" \
  -d '{
    "gateway": "vnpay",
    "tier_id": "tier_enterprise"
  }'

# 1000 credits added after 2.99M VND payment confirmed
```

---

## Credit System

### Credit Usage

| Agent Type | Complexity | Credits per Use |
|------------|------------|-----------------|
| Git Agent | Simple | 1 |
| File Agent | Simple | 1 |
| Shell Agent | Simple | 1 |
| Content Writer | Standard | 3 |
| Lead Hunter | Standard | 3 |
| Recipe Crawler | Complex | 5 |

### Credit Balance Check

```bash
curl -X GET https://agencyos.network/v1/billing/credits \
  -H "Authorization: Bearer $RAAS_API_KEY"
```

### Low Balance Alert

When credit balance < 10:
- Dashboard warning displayed
- Email notification sent
- API responses include `X-Credit-Balance: N` header

---

## Related Endpoints

- [GET /v1/billing/credits](./billing.md) — Check credit balance
- [GET /v1/billing/history](./billing.md) — Transaction history
- [POST /v1/billing/webhook](./billing.md) — Polar webhook handler
- [GET /v1/onboarding/status](./onboarding.md) — Tenant setup progress

---

## Next Steps

- [Governance API](./governance.md) — Quadratic voting and proposals
- [Ledger API](./ledger.md) — Double-entry accounting
- [Revenue API](./revenue.md) — 6-way revenue split
