# CRM API — Contact & Campaign Management

> **Purpose**: Quản lý contacts, leads và campaigns remarketing tự động.

---

## Endpoints Overview

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/v1/crm/contacts` | ✅ | List contacts with filters |
| POST | `/v1/crm/contacts` | ✅ | Create new contact |
| POST | `/v1/crm/contacts/auto` | ✅ | Auto-create from chat event |
| GET | `/v1/crm/contacts/:id` | ✅ | Get contact details |
| PATCH | `/v1/crm/contacts/:id` | ✅ | Update contact |
| DELETE | `/v1/crm/contacts/:id` | ✅ | Delete contact |
| GET | `/v1/crm/lists` | ✅ | List remarketing segments |
| POST | `/v1/crm/lists` | ✅ | Create contact list |
| GET | `/v1/crm/campaigns` | ✅ | List campaigns |
| POST | `/v1/crm/campaigns` | ✅ | Create remarketing campaign |

---

## GET /v1/crm/contacts — List Contacts

### Request

```bash
curl -X GET "https://agencyos.network/v1/crm/contacts?tag=premium&limit=50" \
  -H "Authorization: Bearer $RAAS_API_KEY"
```

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tag` | string | ❌ | Filter by tag (e.g., `premium`, `lead`, `customer`) |
| `limit` | integer | ❌ | Max results (default: 50, max: 100) |
| `offset` | integer | ❌ | Pagination offset (default: 0) |
| `platform` | string | ❌ | Filter by platform: `zalo`, `facebook`, `web` |

### Response (200 OK)

```json
{
  "contacts": [
    {
      "id": "contact_abc123",
      "external_id": "zalo_user_789",
      "platform": "zalo",
      "name": "Nguyen Van A",
      "phone": "+84 90 123 4567",
      "tags": ["premium", "coffee-lover"],
      "metadata": {
        "last_visit": "2026-03-18T10:30:00Z",
        "total_orders": 15,
        "lifetime_value": 2500000
      },
      "created_at": "2026-03-01T08:00:00Z",
      "updated_at": "2026-03-18T10:30:00Z"
    },
    {
      "id": "contact_def456",
      "external_id": "fb_user_456",
      "platform": "facebook",
      "name": "Tran Thi B",
      "phone": null,
      "tags": ["lead"],
      "metadata": {
        "last_visit": "2026-03-17T14:20:00Z",
        "total_orders": 0,
        "lifetime_value": 0
      },
      "created_at": "2026-03-15T12:00:00Z",
      "updated_at": "2026-03-17T14:20:00Z"
    }
  ],
  "total": 127,
  "limit": 50,
  "offset": 0
}
```

### Contact Object

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique contact ID |
| `external_id` | string | Platform-specific user ID |
| `platform` | string | `zalo`, `facebook`, `web`, `instagram`, `tiktok` |
| `name` | string | Contact display name |
| `phone` | string | Phone number (optional) |
| `tags` | array | Array of tags for segmentation |
| `metadata` | object | Custom data (orders, visits, LTV) |
| `created_at` | string | ISO 8601 timestamp |
| `updated_at` | string | ISO 8601 timestamp |

---

## POST /v1/crm/contacts — Create Contact

### Request

```bash
curl -X POST https://agencyos.network/v1/crm/contacts \
  -H "Authorization: Bearer $RAAS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "external_id": "zalo_user_999",
    "platform": "zalo",
    "name": "Le Van C",
    "phone": "+84 91 234 5678",
    "tags": ["vip", "birthday-march"],
    "metadata": {
      "referral_source": "facebook-ads",
      "preferences": {
        "language": "vi",
        "contact_time": "morning"
      }
    }
  }'
```

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `external_id` | string | ✅ | Platform-specific user ID |
| `platform` | string | ✅ | `zalo`, `facebook`, `web`, `instagram`, `tiktok` |
| `name` | string | ❌ | Contact display name |
| `phone` | string | ❌ | Phone number |
| `tags` | array | ❌ | Array of tags for segmentation |
| `metadata` | object | ❌ | Custom data object |

### Response (201 Created)

```json
{
  "id": "contact_ghi789",
  "external_id": "zalo_user_999",
  "platform": "zalo",
  "name": "Le Van C",
  "phone": "+84 91 234 5678",
  "tags": ["vip", "birthday-march"],
  "metadata": {
    "referral_source": "facebook-ads",
    "preferences": {
      "language": "vi",
      "contact_time": "morning"
    }
  },
  "created_at": "2026-03-19T10:30:00Z",
  "updated_at": "2026-03-19T10:30:00Z"
}
```

### Error Responses

**400 Missing Required Fields:**
```json
{
  "error": "VALIDATION_ERROR",
  "message": "external_id and platform are required"
}
```

**409 Duplicate Contact:**
```json
{
  "error": "CONFLICT",
  "message": "Contact with this external_id already exists for platform 'zalo'"
}
```

---

## POST /v1/crm/contacts/auto — Auto-Create from Chat

### Purpose

Tự động tạo hoặc cập nhật contact từ chat events (Zalo OA, Facebook Messenger).

### Request

```bash
curl -X POST https://agencyos.network/v1/crm/contacts/auto \
  -H "Authorization: Bearer $RAAS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "zalo",
    "external_id": "zalo_user_888",
    "name": "Pham Thi D",
    "metadata": {
      "last_message": "2026-03-19T10:30:00Z",
      "message_count": 5
    }
  }'
```

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `platform` | string | ✅ | `zalo`, `facebook`, `web` |
| `external_id` | string | ✅ | Platform user ID |
| `name` | string | ❌ | Contact name (if available) |
| `metadata` | object | ❌ | Additional data |

### Behavior

- **Upsert**: Creates new contact or updates existing one
- **Key**: `platform` + `external_id` combination
- **Auto-tags**: Adds `chat-user`, `active-now` tags automatically

### Response (200 OK)

```json
{
  "id": "contact_jkl012",
  "external_id": "zalo_user_888",
  "platform": "zalo",
  "name": "Pham Thi D",
  "tags": ["chat-user", "active-now"],
  "metadata": {
    "last_message": "2026-03-19T10:30:00Z",
    "message_count": 5
  },
  "created_at": "2026-03-19T10:30:00Z",
  "updated_at": "2026-03-19T10:30:00Z",
  "action": "created"
}
```

**Response for existing contact:**
```json
{
  "id": "contact_jkl012",
  "action": "updated",
  "updated_at": "2026-03-19T10:30:00Z"
}
```

---

## GET /v1/crm/contacts/:id — Get Contact

### Request

```bash
curl -X GET https://agencyos.network/v1/crm/contacts/contact_abc123 \
  -H "Authorization: Bearer $RAAS_API_KEY"
```

### Response (200 OK)

```json
{
  "id": "contact_abc123",
  "external_id": "zalo_user_789",
  "platform": "zalo",
  "name": "Nguyen Van A",
  "phone": "+84 90 123 4567",
  "tags": ["premium", "coffee-lover"],
  "metadata": {
    "last_visit": "2026-03-18T10:30:00Z",
    "total_orders": 15,
    "lifetime_value": 2500000,
    "favorite_products": ["Ca Phe Sua Da", "Bac Xiu"],
    "notes": "Prefers less sweet, extra ice"
  },
  "interactions": [
    {
      "type": "message",
      "timestamp": "2026-03-18T10:30:00Z",
      "channel": "zalo",
      "direction": "inbound"
    },
    {
      "type": "purchase",
      "timestamp": "2026-03-17T09:15:00Z",
      "amount": 150000,
      "items": 3
    }
  ],
  "created_at": "2026-03-01T08:00:00Z",
  "updated_at": "2026-03-18T10:30:00Z"
}
```

### Interaction History

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | `message`, `purchase`, `visit`, `campaign_response` |
| `timestamp` | string | ISO 8601 timestamp |
| `channel` | string | Platform where interaction occurred |
| `direction` | string | `inbound` or `outbound` (for messages) |
| `amount` | integer | Purchase amount in VND (for purchases) |

### Error Responses

**404 Not Found:**
```json
{
  "error": "NOT_FOUND",
  "message": "Contact not found"
}
```

---

## PATCH /v1/crm/contacts/:id — Update Contact

### Request

```bash
curl -X PATCH https://agencyos.network/v1/crm/contacts/contact_abc123 \
  -H "Authorization: Bearer $RAAS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Nguyen Van A (VIP)",
    "tags": ["premium", "vip", "coffee-lover"],
    "metadata": {
      "lifetime_value": 3000000,
      "notes": "Upgraded to VIP tier"
    }
  }'
```

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | ❌ | Updated display name |
| `phone` | string | ❌ | Updated phone number |
| `tags` | array | ❌ | Replace all tags |
| `metadata` | object | ❌ | Merge with existing metadata |

### Response (200 OK)

```json
{
  "id": "contact_abc123",
  "external_id": "zalo_user_789",
  "platform": "zalo",
  "name": "Nguyen Van A (VIP)",
  "phone": "+84 90 123 4567",
  "tags": ["premium", "vip", "coffee-lover"],
  "metadata": {
    "last_visit": "2026-03-18T10:30:00Z",
    "total_orders": 15,
    "lifetime_value": 3000000,
    "notes": "Upgraded to VIP tier"
  },
  "updated_at": "2026-03-19T10:35:00Z"
}
```

---

## DELETE /v1/crm/contacts/:id — Delete Contact

### Request

```bash
curl -X DELETE https://agencyos.network/v1/crm/contacts/contact_abc123 \
  -H "Authorization: Bearer $RAAS_API_KEY"
```

### Response (200 OK)

```json
{
  "id": "contact_abc123",
  "status": "deleted",
  "message": "Contact deleted successfully"
}
```

### GDPR Compliance

- Soft delete by default (contact marked as `inactive`)
- Hard delete available on request (data permanently removed)
- Audit trail retained for compliance

---

## GET /v1/crm/lists — List Segments

### Request

```bash
curl -X GET https://agencyos.network/v1/crm/lists \
  -H "Authorization: Bearer $RAAS_API_KEY"
```

### Response (200 OK)

```json
{
  "lists": [
    {
      "id": "list_abc123",
      "name": "Premium Customers",
      "description": "Customers with LTV > 1,000,000 VND",
      "criteria": {
        "tags": ["premium"],
        "metadata.lifetime_value": {
          "gte": 1000000
        }
      },
      "contact_count": 45,
      "created_at": "2026-03-01T08:00:00Z"
    },
    {
      "id": "list_def456",
      "name": "Inactive 30 Days",
      "description": "No visits in last 30 days",
      "criteria": {
        "metadata.last_visit": {
          "lte": "2026-02-17T00:00:00Z"
        }
      },
      "contact_count": 128,
      "created_at": "2026-03-10T12:00:00Z"
    }
  ]
}
```

### List Object

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique list ID |
| `name` | string | Display name |
| `description` | string | List purpose |
| `criteria` | object | Filter conditions |
| `contact_count` | integer | Current matching contacts |
| `created_at` | string | ISO 8601 timestamp |

---

## POST /v1/crm/lists — Create Segment

### Request

```bash
curl -X POST https://agencyos.network/v1/crm/lists \
  -H "Authorization: Bearer $RAAS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Birthday March 2026",
    "description": "Contacts with birthday in March",
    "criteria": {
      "tags": ["birthday-march"],
      "platform": "zalo"
    }
  }'
```

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | ✅ | List display name |
| `description` | string | ❌ | List purpose |
| `criteria` | object | ✅ | Filter conditions |

### Criteria Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `tags` | Array contains | `["premium", "vip"]` |
| `platform` | Exact match | `"zalo"` |
| `metadata.lifetime_value.gte` | Greater than or equal | `1000000` |
| `metadata.last_visit.lte` | Less than or equal (date) | `"2026-02-17"` |
| `metadata.total_orders.gte` | Minimum orders | `5` |

### Response (201 Created)

```json
{
  "id": "list_ghi789",
  "name": "Birthday March 2026",
  "description": "Contacts with birthday in March",
  "criteria": {
    "tags": ["birthday-march"],
    "platform": "zalo"
  },
  "contact_count": 23,
  "created_at": "2026-03-19T10:40:00Z"
}
```

---

## GET /v1/crm/campaigns — List Campaigns

### Request

```bash
curl -X GET https://agencyos.network/v1/crm/campaigns \
  -H "Authorization: Bearer $RAAS_API_KEY"
```

### Response (200 OK)

```json
{
  "campaigns": [
    {
      "id": "campaign_abc123",
      "name": "Re-engagement: 30 Days Inactive",
      "trigger": "days_since_visit",
      "trigger_value": 30,
      "target_lists": ["list_def456"],
      "message_template": "Chào bạn! Đã lâu không thấy bạn ghé quán. Ghé ngay hôm nay để nhận ưu đãi 20% nhé!",
      "status": "active",
      "sent_count": 128,
      "response_rate": 0.35,
      "created_at": "2026-03-10T12:00:00Z"
    },
    {
      "id": "campaign_def456",
      "name": "Birthday Wishes",
      "trigger": "birthday",
      "trigger_value": 0,
      "target_lists": ["list_ghi789"],
      "message_template": "🎉 Chúc mừng sinh nhật! Tặng bạn voucher 50k từ The Coffee House!",
      "status": "active",
      "sent_count": 23,
      "response_rate": 0.78,
      "created_at": "2026-03-01T08:00:00Z"
    }
  ]
}
```

### Campaign Object

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique campaign ID |
| `name` | string | Campaign name |
| `trigger` | string | Trigger type (see below) |
| `trigger_value` | integer | Trigger threshold (days) |
| `target_lists` | array | List IDs to target |
| `message_template` | string | Message to send |
| `status` | string | `active`, `paused`, `completed` |
| `sent_count` | integer | Messages sent |
| `response_rate` | float | Response rate (0-1) |

### Trigger Types

| Trigger | Description | `trigger_value` |
|---------|-------------|-----------------|
| `days_since_visit` | Days since last visit | Number of days (e.g., 30) |
| `birthday` | Days before/after birthday | 0 = on birthday, -7 = week before |
| `manual` | Manual trigger | — |
| `tag_match` | Contact tagged | — (uses `target_tags`) |

---

## POST /v1/crm/campaigns — Create Campaign

### Request

```bash
curl -X POST https://agencyos.network/v1/crm/campaigns \
  -H "Authorization: Bearer $RAAS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Welcome New Leads",
    "trigger": "tag_match",
    "target_tags": ["lead"],
    "message_template": "Chào mừng bạn đến với The Coffee House! Ghé quán hôm nay để trải nghiệm cà phê tuyệt hảo.",
    "status": "active"
  }'
```

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | ✅ | Campaign name |
| `trigger` | string | ✅ | `days_since_visit`, `birthday`, `manual`, `tag_match` |
| `trigger_value` | integer | ❌ | Threshold for time-based triggers |
| `target_lists` | array | ❌ | List IDs to target |
| `target_tags` | array | ❌ | Tags to match (for `tag_match` trigger) |
| `message_template` | string | ✅ | Message content |
| `status` | string | ❌ | `active` (default), `paused` |

### Response (201 Created)

```json
{
  "id": "campaign_jkl012",
  "name": "Welcome New Leads",
  "trigger": "tag_match",
  "target_tags": ["lead"],
  "message_template": "Chào mừng bạn đến với The Coffee House! Ghé quán hôm nay để trải nghiệm cà phê tuyệt hảo.",
  "status": "active",
  "sent_count": 0,
  "response_rate": 0,
  "created_at": "2026-03-19T10:45:00Z"
}
```

### Error Responses

**400 Invalid Trigger:**
```json
{
  "error": "VALIDATION_ERROR",
  "message": "Invalid trigger type: 'invalid-trigger'"
}
```

**400 Missing Trigger Value:**
```json
{
  "error": "VALIDATION_ERROR",
  "message": "trigger_value is required for 'days_since_visit' trigger"
}
```

---

## CRM Data Flow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Chat Webhook   │ →   │  Auto-Create    │ →   │  Contact        │
│  (Zalo/FB)      │     │  /v1/crm/contacts/auto │  Database       │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                     │
                                                     ↓
                                          ┌─────────────────┐
                                          │  Campaign       │
                                          │  Trigger Check  │
                                          └─────────────────┘
                                                     │
                                        ┌────────────┴────────────┐
                                        ↓                         ↓
                               ┌─────────────────┐     ┌─────────────────┐
                               │  Send Message   │     │  Update Tags    │
                               │  via Chat API   │     │  (converted)    │
                               └─────────────────┘     └─────────────────┘
```

---

## Use Cases

### E-commerce Lead Nurturing

```json
{
  "name": "Abandoned Cart Recovery",
  "trigger": "days_since_visit",
  "trigger_value": 1,
  "target_tags": ["cart-abandoned"],
  "message_template": "Bạn ơi, giỏ hàng của bạn đang chờ! Hoàn thành đơn hàng ngay để nhận freeship."
}
```

### Birthday Campaign

```json
{
  "name": "Birthday Special Offer",
  "trigger": "birthday",
  "trigger_value": 0,
  "target_lists": ["list_birthday_today"],
  "message_template": "🎂 Chúc mừng sinh nhật! Tặng bạn bánh mì miễn phí hôm nay!"
}
```

### VIP Reactivation

```json
{
  "name": "VIP Comeback",
  "trigger": "days_since_visit",
  "trigger_value": 60,
  "target_tags": ["vip"],
  "message_template": "Chào anh/chị VIP! Đã lâu không thấy anh/chị ghé quán. Ghé ngay để nhận phần quà đặc biệt!"
}
```

---

## Related Endpoints

- [POST /v1/chat/webhook/zalo](./chat.md) — Zalo OA webhooks
- [POST /v1/chat/webhook/facebook](./chat.md) — Facebook Messenger webhooks
- [POST /v1/content/generate](./content.md) — AI content generation
- [GET /v1/reports/weekly](./reports.md) — Weekly analytics

---

## Next Steps

- [Reports API](./reports.md) — Weekly analytics and AI summaries
- [Payment API](./payment.md) — Vietnam payment gateways (MoMo, VNPAY)
- [Governance API](./governance.md) — Quadratic voting and proposals
