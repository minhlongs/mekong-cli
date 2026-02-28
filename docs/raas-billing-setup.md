# RaaS Billing Setup (Polar.sh)

How to connect Polar.sh subscriptions and credit packs to your RaaS deployment.

---

## 1. Create Products in Polar.sh

Log in to [polar.sh](https://polar.sh) and create products matching the IDs in `POLAR_PRODUCT_MAP`:

| Polar Product ID | Credits Granted | Suggested Price |
|-----------------|----------------|-----------------|
| `starter_monthly` | 50 | $29/mo |
| `growth_monthly` | 200 | $99/mo |
| `pro_monthly` | 500 | $199/mo |
| `enterprise_monthly` | 2000 | $599/mo |
| `credits_10` | 10 | $5 one-time |
| `credits_50` | 50 | $20 one-time |
| `credits_100` | 100 | $35 one-time |

Set each product's **ID** to exactly match the `POLAR_PRODUCT_MAP` key in `src/raas/billing.py`.

---

## 2. Configure Webhook URL

In the Polar dashboard, go to **Settings → Webhooks → Add Endpoint**:

| Field | Value |
|-------|-------|
| URL | `https://your-domain.com/raas/billing/webhook` |
| Events | `order.created`, `subscription.created` |
| Format | Standard Webhooks (SHA-256) |

Copy the generated **webhook secret** — you will need it in step 3.

---

## 3. Set Environment Variable

```bash
export POLAR_WEBHOOK_SECRET="whsec_your_secret_here"
```

Add to `.env` or your deployment config. The gateway reads this at startup.
If the variable is empty, signature verification is **skipped** (dev only).

---

## 4. Map Tenant IDs to Polar Customers

When creating a Polar checkout session or customer, set the `external_id` field
to your tenant's UUID from `TenantStore`:

```python
# Example: create tenant and pass ID to Polar checkout metadata
from src.raas.tenant import TenantStore

store = TenantStore()
tenant = store.create_tenant("Acme Corp")
print(tenant.id)   # pass this as external_id in Polar customer object
print(tenant.api_key)  # give to the customer for API access
```

The webhook handler extracts tenant ID from:
1. `data.customer.external_id` (preferred)
2. `data.metadata.tenant_id` (fallback)
3. `data.customer_id` (last resort)

---

## 5. Test Locally with curl

Simulate a `credits_10` purchase for a tenant (no signature check in dev):

```bash
curl -X POST http://localhost:8000/raas/billing/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "id": "evt_test_001",
    "type": "order.created",
    "data": {
      "customer": { "external_id": "<your-tenant-uuid>" },
      "product": { "id": "credits_10" }
    }
  }'
```

Expected response:
```json
{
  "status": "ok",
  "event_id": "evt_test_001",
  "type": "order.created",
  "tenant_id": "<your-tenant-uuid>",
  "product_id": "credits_10",
  "new_balance": 10
}
```

Posting the same `event_id` again returns `{"status": "duplicate"}` — credits are **not** added twice.
