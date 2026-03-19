# Tasks API — Mission Management

> **Purpose**: Tạo và quản lý AI missions với credit metering. Credits được trừ trước khi thực hiện và refund khi cancel.

---

## Endpoints Overview

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/v1/tasks` | ✅ | Create new mission |
| GET | `/v1/tasks` | ✅ | List missions |
| GET | `/v1/tasks/:id` | ✅ | Get mission details |
| GET | `/v1/tasks/:id/stream` | ✅ | SSE progress stream |
| POST | `/v1/tasks/:id/cancel` | ✅ | Cancel pending mission |

---

## POST /v1/tasks — Create Mission

### Request

```bash
curl -X POST https://agencyos.network/v1/tasks \
  -H "Authorization: Bearer $RAAS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "goal": "Write a blog post about coffee brewing techniques"
  }'
```

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `goal` | string | ✅ | Mission goal (1-2000 chars) |
| `priority` | string | ❌ | `low`, `medium`, `high`, `critical` (default: `medium`) |
| `estimated_credits` | integer | ❌ | Override auto-estimate |
| `metadata` | object | ❌ | Additional metadata |

### Response (201 Created)

```json
{
  "id": "mission_xyz789",
  "tenant_id": "tenant_abc123",
  "goal": "Write a blog post about coffee brewing techniques",
  "status": "pending",
  "credits_used": 3,
  "created_at": "2026-03-19T10:30:00Z",
  "message": "Mission created. Use /v1/tasks/:id/stream to track progress."
}
```

### Credit Deduction Flow

```
1. Check tenant credit balance
2. Deduct estimated credits (3 for standard complexity)
3. Create mission with status "pending"
4. Agent executes mission
5. On completion: status → "completed"
6. On cancel: refund credits
```

### Error Responses

**402 Insufficient Credits:**
```json
{
  "error": "INSUFFICIENT_CREDITS",
  "message": "Insufficient balance",
  "details": [{"balance": 2}]
}
```

**400 Validation Error:**
```json
{
  "error": "VALIDATION_ERROR",
  "message": "Goal is required"
}
```

---

## GET /v1/tasks — List Missions

### Request

```bash
curl -X GET "https://agencyos.network/v1/tasks?status=pending&limit=20" \
  -H "Authorization: Bearer $RAAS_API_KEY"
```

### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `status` | string | — | Filter: `pending`, `running`, `completed`, `failed`, `cancelled` |
| `limit` | integer | 50 | Max results (1-100) |
| `offset` | integer | 0 | Pagination offset |

### Response

```json
{
  "missions": [
    {
      "id": "mission_xyz789",
      "tenant_id": "tenant_abc123",
      "goal": "Write a blog post about coffee brewing techniques",
      "status": "pending",
      "credits_used": 3,
      "created_at": "2026-03-19T10:30:00Z"
    }
  ],
  "total": 1
}
```

---

## GET /v1/tasks/:id — Get Mission Details

### Request

```bash
curl -X GET https://agencyos.network/v1/tasks/mission_xyz789 \
  -H "Authorization: Bearer $RAAS_API_KEY"
```

### Response

```json
{
  "id": "mission_xyz789",
  "tenant_id": "tenant_abc123",
  "goal": "Write a blog post about coffee brewing techniques",
  "status": "completed",
  "result": {
    "output": "blog_post.md",
    "url": "https://storage.agencyos.network/outputs/mission_xyz789/blog_post.md"
  },
  "credits_used": 3,
  "created_at": "2026-03-19T10:30:00Z",
  "completed_at": "2026-03-19T10:32:15Z"
}
```

---

## GET /v1/tasks/:id/stream — SSE Progress

### Purpose

Real-time progress tracking via Server-Sent Events.

### Request

```bash
curl -X GET https://agencyos.network/v1/tasks/mission_xyz789/stream \
  -H "Authorization: Bearer $RAAS_API_KEY"
```

### SSE Event Stream

```
event: status
data: {"id":"mission_xyz789","status":"planning","result":null}

event: status
data: {"id":"mission_xyz789","status":"executing","result":{"step":"generating_content"}}

event: status
data: {"id":"mission_xyz789","status":"verifying","result":{"checks_passed":3}}

event: status
data: {"id":"mission_xyz789","status":"completed","result":{"output":"blog_post.md"}}
```

### JavaScript Example

```javascript
const eventSource = new EventSource(
  'https://agencyos.network/v1/tasks/mission_xyz789/stream',
  {
    headers: { 'Authorization': `Bearer ${RAAS_API_KEY}` }
  }
);

eventSource.addEventListener('status', (event) => {
  const { status, result } = JSON.parse(event.data);
  console.log(`Mission ${status}:`, result);

  if (status === 'completed' || status === 'failed') {
    eventSource.close();
  }
});
```

### Event Types

| Event | Data | Description |
|-------|------|-------------|
| `status` | `{id, status, result}` | Progress update |
| `log` | `{level, message}` | Log output |
| `complete` | `{status, result}` | Mission completed |
| `error` | `{error, message}` | Error occurred |

---

## POST /v1/tasks/:id/cancel — Cancel Mission

### Request

```bash
curl -X POST https://agencyos.network/v1/tasks/mission_xyz789/cancel \
  -H "Authorization: Bearer $RAAS_API_KEY"
```

### Response (200 OK)

```json
{
  "id": "mission_xyz789",
  "status": "cancelled",
  "refunded": 3
}
```

### Constraints

- Only `pending` missions can be cancelled
- `running` missions must complete or fail
- Full credit refund on successful cancel

### Error Responses

**404 Not Found:**
```json
{
  "error": "NOT_FOUND",
  "message": "Mission not found"
}
```

**409 Conflict:**
```json
{
  "error": "CONFLICT",
  "message": "Only pending missions can be cancelled"
}
```

---

## Credit Estimation

### Complexity Rules

| Complexity | Words in Goal | Credits |
|------------|---------------|---------|
| Simple | < 10 | 1 |
| Standard | 10-30 | 3 |
| Complex | > 30 | 5 |

### Example Goals

```
Simple (1 credit):
- "Summarize this document"
- "Fix typo in file"

Standard (3 credits):
- "Write a blog post about coffee"
- "Analyze sales data for Q1"

Complex (5 credits):
- "Build a landing page with React"
- "Refactor authentication module"
```

---

## Mission Status Lifecycle

```
pending → running → verifying → completed
                    ↓
                    failed

pending → cancelled (refund)
```

| Status | Description | Can Cancel? |
|--------|-------------|-------------|
| `pending` | Waiting in queue | ✅ Yes |
| `running` | Agent executing | ❌ No |
| `verifying` | Quality check | ❌ No |
| `completed` | Success | ❌ No |
| `failed` | Error occurred | ❌ No |
| `cancelled` | Cancelled by user | ❌ No |

---

## Related Endpoints

- [GET /billing/credits](./billing.md) — Check credit balance
- [POST /agents/:name/run](./agents.md) — Run specific agent
- [GET /reports/weekly](./reports.md) — Weekly mission summary

---

## Next Steps

- [Agents API](./agents.md) — Run git, file, shell agents
- [Billing API](./billing.md) — Manage credits
- [SSE Stream Guide](../guides/sse-streaming.md) — Real-time progress tracking
