# License Management UI

**ROIaaS Phase 2** — Admin Dashboard for license CRUD, analytics, and audit trails.

**Route:** `/admin/licenses`

---

## UI Sections

| Tab | Purpose |
|-----|---------|
| **Licenses** | List, filter, sort, create, revoke, delete licenses |
| **Audit Logs** | Timeline view of license events with filtering |
| **Analytics** | Usage metrics, quota gauges, recent activity |

---

## API Endpoints (`/api/v1/licenses`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | List licenses (pagination: `take`, `skip`, `status`, `tier`) |
| `GET` | `/:id` | Get single license |
| `POST` | `/` | Create license |
| `PATCH` | `/:id/revoke` | Revoke license |
| `DELETE` | `/:id` | Delete license |
| `GET` | `/:id/audit` | Get audit logs |
| `GET` | `/analytics` | Aggregate analytics |

### Create License Example

```bash
curl -X POST https://api.algo-trader.com/api/v1/licenses \
  -H "X-API-Key: admin-key" \
  -H "Content-Type: application/json" \
  -d '{"name": "Prod License", "tier": "PRO", "tenantId": "t123"}'
```

**Response:** License with auto-generated key like `raas-rpp-abc123DEF456XYZ7`

---

## License Key Format

| Tier | Prefix | Example |
|------|--------|---------|
| FREE | `free` | `raas-free-ABCD1234-WXYZ7890` |
| PRO | `rpp` | `raas-rpp-ABCD1234-WXYZ7890` |
| ENTERPRISE | `rep` | `raas-rep-ABCD1234-WXYZ7890` |

---

## Admin Workflow

1. **Create** - Click "Create License" → Fill name/tier/expiration/tenant → Copy generated key
2. **View Usage** - Actions menu (dots) → "View Audit Log"
3. **Revoke** - Actions menu → "Revoke License"
4. **Delete** - Actions menu → "Delete License"

---

## Features

- **Sorting**: Click column headers to sort by name, key, tier, status, usage, dates
- **Filtering**: By status (Active/Expired/Revoked) and tier (FREE/PRO/ENTERPRISE)
- **Audit Events**: Created, Activated, Revoked, API Call, ML Feature, Rate Limit
- **Analytics**: License distribution by tier, usage breakdown, quota gauges

---

## Phase 3: Polar.sh Webhook Integration

**ROIaaS Phase 3** — Automated license management via Polar.sh payment webhooks.

### Webhook Endpoint

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/webhooks/polar` | Polar.sh webhook handler |

### Supported Webhook Events

| Event | Action | License Impact |
|-------|--------|----------------|
| `subscription.created` | Create subscription record | Activate PRO/ENTERPRISE license |
| `subscription.active` | Update subscription status | Set/upgrade license tier |
| `subscription.updated` | Update tier/period | Update license tier |
| `subscription.cancelled` | Mark as cancelled | Downgrade to FREE license |
| `checkout.created` | Track checkout session | No license change (pending) |
| `payment.success` | Record payment | Maintain current tier |
| `payment.failed` | Record failed payment | Flag for review |

### Webhook Payload Example

```json
{
  "type": "subscription.active",
  "data": {
    "object": {
      "id": "sub_2JZ9X8Y7W6V5U4T3",
      "product_id": "pro-monthly",
      "customer_email": "user@example.com",
      "status": "active",
      "current_period_start": "2026-03-01T00:00:00Z",
      "current_period_end": "2026-04-01T00:00:00Z"
    }
  }
}
```

### Webhook Signature Verification

Polar.sh webhooks are signed using HMAC-SHA256. Verify signatures using:

```typescript
import { PolarService } from '../payment/polar-service';

const polarService = PolarService.getInstance();
const isValid = await polarService.verifyWebhook(payload, signature);
```

### Configuration

Add to `.env`:

```bash
# Polar.sh Configuration
POLAR_API_KEY=sk_polar_...
POLAR_WEBHOOK_SECRET=whsec_...
POLAR_SUCCESS_URL=https://algo-trader.com/upgrade/success
```

### Payment-License Sync

The `LicensePaymentSync` service tracks:

- **Payment records**: Order ID, amount, currency, status
- **Subscription records**: Subscription ID, tier, interval, period dates
- **Revenue metrics**: MRR, total revenue, average license value
- **Payment status distribution**: Success/failed/pending/refunded counts

### Revenue Analytics

Dashboard analytics include:

| Metric | Description |
|--------|-------------|
| **MRR** | Monthly Recurring Revenue from active subscriptions |
| **Total Revenue** | Sum of all successful payments |
| **Avg License Value** | Total revenue / active licenses |
| **Payment Success Rate** | Successful payments / total payments |

---

## Related Docs

| File | Purpose |
|------|---------|
| `docs/RAAS_API_ENDPOINTS.md` | RaaS gate API reference |
| `docs/raas-license-integration.md` | License key integration |
| `docs/LICENSE_GATING.md` | License enforcement |

---

*Last updated: 2026-03-12*
