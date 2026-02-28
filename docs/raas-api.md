# RaaS API Reference

**Base URL:** `http://localhost:8000/raas`
**Version:** 1.0

---

## Authentication

All endpoints (except `/raas/billing/webhook`) require a Bearer token.

```
Authorization: Bearer mk_<your_api_key>
```

Keys are issued by `TenantStore.create_tenant()` and begin with `mk_`.

---

## Endpoints

### Missions

#### POST /raas/missions

Create a new mission. Deducts credits from the tenant account.

**Request**
```json
{
  "goal": "Automate weekly sales report to Slack",
  "complexity": "standard"
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `goal` | string | yes | Min 3 chars. Shell metacharacters stripped. |
| `complexity` | string | no | `simple`, `standard`, `complex`. Auto-detected from goal length if omitted. |

**Auto-detection thresholds:**
- `simple` — goal < 50 chars (1 credit)
- `standard` — goal 50–149 chars (3 credits)
- `complex` — goal ≥ 150 chars (5 credits)

**Response `201 Created`**
```json
{
  "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "status": "queued",
  "goal": "Automate weekly sales report to Slack",
  "complexity": "standard",
  "credits_cost": 3,
  "created_at": "2026-02-28T10:00:00+00:00",
  "started_at": null,
  "completed_at": null,
  "error_message": null,
  "logs_url": "/missions/f47ac10b.../logs"
}
```

**curl example**
```bash
curl -X POST http://localhost:8000/raas/missions \
  -H "Authorization: Bearer mk_abc123" \
  -H "Content-Type: application/json" \
  -d '{"goal": "Generate Q1 revenue report"}'
```

---

#### GET /raas/missions

List missions for the authenticated tenant (newest first).

**Query params:** `limit` (default 20), `offset` (default 0)

**Response `200 OK`**
```json
[
  {
    "id": "f47ac10b-...",
    "status": "completed",
    "goal": "Generate Q1 revenue report",
    "complexity": "simple",
    "credits_cost": 1,
    "created_at": "2026-02-28T09:00:00+00:00",
    "started_at": "2026-02-28T09:00:05+00:00",
    "completed_at": "2026-02-28T09:02:15+00:00",
    "error_message": null,
    "logs_url": "/missions/f47ac10b-.../logs"
  }
]
```

**curl example**
```bash
curl http://localhost:8000/raas/missions?limit=10 \
  -H "Authorization: Bearer mk_abc123"
```

---

#### GET /raas/missions/{mission_id}

Retrieve a single mission by ID (tenant-scoped).

**Response `200 OK`** — same shape as a single item from the list endpoint.

**curl example**
```bash
curl http://localhost:8000/raas/missions/f47ac10b-58cc-4372-a567-0e02b2c3d479 \
  -H "Authorization: Bearer mk_abc123"
```

---

#### POST /raas/missions/{mission_id}/cancel

Cancel a queued mission. Credits are refunded to the tenant account.

**Response `200 OK`**
```json
{
  "id": "f47ac10b-...",
  "status": "cancelled",
  "credits_cost": 3,
  ...
}
```

**curl example**
```bash
curl -X POST http://localhost:8000/raas/missions/f47ac10b-.../cancel \
  -H "Authorization: Bearer mk_abc123"
```

---

#### GET /raas/missions/{mission_id}/logs

Return execution log content for a mission.

**Response `200 OK`**
```json
{
  "mission_id": "f47ac10b-...",
  "logs": "Step 1: Planning...\nStep 2: Executing...\n"
}
```

**curl example**
```bash
curl http://localhost:8000/raas/missions/f47ac10b-.../logs \
  -H "Authorization: Bearer mk_abc123"
```

---

### Dashboard

#### GET /raas/dashboard/summary

Aggregated view of missions, credits, and platform health for the tenant.

**Response `200 OK`**
```json
{
  "missions": {
    "total": 42,
    "queued": 1,
    "running": 2,
    "completed": 38,
    "failed": 1,
    "cancelled": 0
  },
  "credits": {
    "balance": 95,
    "total_earned": 500,
    "total_spent": 405
  },
  "health": "ok"
}
```

---

#### GET /raas/dashboard/stream

Server-Sent Events stream of real-time mission status updates.

**curl example**
```bash
curl -N http://localhost:8000/raas/dashboard/stream \
  -H "Authorization: Bearer mk_abc123" \
  -H "Accept: text/event-stream"
```

---

#### GET /raas/dashboard/costs

Credit cost breakdown by complexity tier.

**Response `200 OK`**
```json
{
  "simple": 1,
  "standard": 3,
  "complex": 5
}
```

---

### Billing

#### POST /raas/billing/webhook

Receive Polar.sh webhook events. Provisions credits on purchase.

**Headers**
```
webhook-signature: sha256=<hmac_hex>
Content-Type: application/json
```

**Request body (Polar `order.created` event)**
```json
{
  "id": "evt_polar_001",
  "type": "order.created",
  "data": {
    "customer": { "external_id": "<tenant_id>" },
    "product": { "id": "growth_monthly" }
  }
}
```

**Response `200 OK`**
```json
{
  "status": "ok",
  "event_id": "evt_polar_001",
  "type": "order.created",
  "tenant_id": "<tenant_id>",
  "product_id": "growth_monthly",
  "new_balance": 295
}
```

**Idempotent:** Duplicate `event_id` returns `{"status": "duplicate"}` without crediting again.

---

### Registry

#### GET /raas/registry/recipes

List available recipes in the registry.

---

## Error Codes

| Code | Meaning | Common cause |
|------|---------|--------------|
| 401 | Unauthorized | Missing/invalid `Authorization` header or unknown API key |
| 402 | Payment Required | Insufficient credits for mission (ValueError from credit store) |
| 403 | Forbidden | Tenant account is deactivated |
| 404 | Not Found | Mission ID not found, or belongs to different tenant |
| 409 | Conflict | Cannot cancel a mission not in `queued` state |
| 422 | Unprocessable Entity | Goal is empty after sanitisation, or invalid request body |
| 500 | Internal Server Error | Database or store failure |

---

## Mission Statuses

| Status | Description |
|--------|-------------|
| `queued` | Waiting for daemon pickup |
| `running` | Actively executing |
| `completed` | Successfully finished |
| `failed` | Execution error (see `error_message`) |
| `cancelled` | Cancelled by tenant; credits refunded |
