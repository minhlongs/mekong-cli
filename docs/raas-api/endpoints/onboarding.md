# Onboarding API — Tenant Setup Flow

> **Purpose**: Hướng dẫn tenants qua 4 bước setup: Profile → Channel → Menu → Activate.

---

## Endpoints Overview

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/v1/onboarding/status` | ✅ | Get onboarding progress |
| POST | `/v1/onboarding/profile` | ✅ | Step 1: Business profile |
| POST | `/v1/onboarding/channel` | ✅ | Step 2: Connect channels |
| POST | `/v1/onboarding/menu` | ✅ | Step 3: Setup menu/products |
| POST | `/v1/onboarding/activate` | ✅ | Step 4: Activate account |

---

## Onboarding Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Step 1    │ →   │   Step 2    │ →   │   Step 3    │ →   │   Step 4    │
│   Profile   │     │   Channel   │     │    Menu     │     │   Activate  │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
     ↓                   ↓                   ↓                   ↓
  Business info     Connect Zalo/      Add products/     Account ready
  & preferences      Facebook          services          for missions
```

---

## GET /v1/onboarding/status — Check Progress

### Request

```bash
curl -X GET https://agencyos.network/v1/onboarding/status \
  -H "Authorization: Bearer $RAAS_API_KEY"
```

### Response

```json
{
  "tenant_id": "tenant_abc123",
  "current_step": 2,
  "total_steps": 4,
  "progress_percentage": 50,
  "steps": {
    "profile": {
      "status": "completed",
      "completed_at": "2026-03-19T10:00:00Z"
    },
    "channel": {
      "status": "in_progress",
      "started_at": "2026-03-19T10:05:00Z"
    },
    "menu": {
      "status": "pending"
    },
    "activate": {
      "status": "pending"
    }
  },
  "next_step": {
    "step": 2,
    "name": "channel",
    "description": "Connect your communication channels (Zalo OA, Facebook Page)"
  }
}
```

### Status Values

| Status | Description |
|--------|-------------|
| `pending` | Not started |
| `in_progress` | Currently working on |
| `completed` | Finished |
| `skipped` | Optional step skipped |

---

## POST /v1/onboarding/profile — Step 1: Business Profile

### Request

```bash
curl -X POST https://agencyos.network/v1/onboarding/profile \
  -H "Authorization: Bearer $RAAS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "business_name": "The Coffee House",
    "industry": "F&B",
    "business_type": "coffee_shop",
    "address": "123 Nguyen Hue, District 1, Ho Chi Minh City",
    "phone": "+84 90 123 4567",
    "email": "hello@thecoffeehouse.vn",
    "website": "https://thecoffeehouse.vn",
    "description": "Premium Vietnamese coffee chain",
    "tax_code": "0123456789",
    "preferences": {
      "language": "vi",
      "currency": "VND",
      "timezone": "Asia/Ho_Chi_Minh"
    }
  }'
```

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `business_name` | string | ✅ | Legal business name |
| `industry` | string | ✅ | Industry: `F&B`, `retail`, `ecommerce`, `services`, `other` |
| `business_type` | string | ✅ | Specific type (e.g., `coffee_shop`, `restaurant`) |
| `address` | string | ❌ | Business address |
| `phone` | string | ❌ | Contact phone |
| `email` | string | ❌ | Contact email |
| `website` | string | ❌ | Business website |
| `description` | string | ❌ | Business description |
| `tax_code` | string | ❌ | Tax identification number |
| `preferences` | object | ❌ | Default preferences |

### Preferences Object

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `language` | string | `vi` | `vi` or `en` |
| `currency` | string | `VND` | `VND` or `USD` |
| `timezone` | string | `Asia/Ho_Chi_Minh` | Timezone |

### Response (200 OK)

```json
{
  "step": 1,
  "status": "completed",
  "next_step": {
    "step": 2,
    "name": "channel",
    "description": "Connect your communication channels"
  },
  "message": "Business profile saved successfully"
}
```

### Error Responses

**400 Missing Required Fields:**
```json
{
  "error": "VALIDATION_ERROR",
  "message": "Business name and industry are required"
}
```

---

## POST /v1/onboarding/channel — Step 2: Connect Channels

### Request

```bash
curl -X POST https://agencyos.network/v1/onboarding/channel \
  -H "Authorization: Bearer $RAAS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "channels": [
      {
        "type": "zalo_oa",
        "oa_id": "1234567890",
        "oa_name": "The Coffee House",
        "verified": true
      },
      {
        "type": "facebook_page",
        "page_id": "987654321",
        "page_name": "The Coffee House",
        "access_token": "EAAB..."
      }
    ]
  }'
```

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `channels` | array | ✅ | List of channels to connect |

### Channel Objects

**Zalo OA:**
```json
{
  "type": "zalo_oa",
  "oa_id": "1234567890",
  "oa_name": "The Coffee House",
  "verified": true
}
```

**Facebook Page:**
```json
{
  "type": "facebook_page",
  "page_id": "987654321",
  "page_name": "The Coffee House",
  "access_token": "EAAB..."
}
```

### Supported Channels

| Channel | Type ID | Required Fields |
|---------|---------|-----------------|
| Zalo OA | `zalo_oa` | `oa_id`, `oa_name` |
| Facebook Page | `facebook_page` | `page_id`, `access_token` |
| Instagram | `instagram` | `account_id`, `access_token` |
| TikTok | `tiktok` | `account_id`, `access_token` |
| Website Widget | `website` | `website_url` |

### Response (200 OK)

```json
{
  "step": 2,
  "status": "completed",
  "channels_connected": 2,
  "next_step": {
    "step": 3,
    "name": "menu",
    "description": "Setup your product menu"
  },
  "message": "Channels connected successfully"
}
```

### Error Responses

**400 Invalid Channel:**
```json
{
  "error": "VALIDATION_ERROR",
  "message": "Invalid channel type: 'unknown_channel'"
}
```

**401 Authentication Failed:**
```json
{
  "error": "UNAUTHORIZED",
  "message": "Facebook access token is invalid or expired"
}
```

---

## POST /v1/onboarding/menu — Step 3: Setup Menu

### Request

```bash
curl -X POST https://agencyos.network/v1/onboarding/menu \
  -H "Authorization: Bearer $RAAS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "categories": [
      {
        "name": "Cà Phê",
        "name_en": "Coffee",
        "items": [
          {
            "name": "Cà Phê Sữa Đá",
            "name_en": "Vietnamese Iced Coffee",
            "price": 29000,
            "description": "Cà phê rang xay pha phin truyền thống",
            "image_url": "https://storage.../ca-phe-sua-da.jpg"
          },
          {
            "name": "Bạc Xỉu",
            "name_en": "White Coffee",
            "price": 32000,
            "description": "Cà phê với nhiều sữa",
            "image_url": "https://storage.../bac-siu.jpg"
          }
        ]
      },
      {
        "name": "Đá Xay",
        "name_en": "Frozen",
        "items": [
          {
            "name": "Trà Xanh Đá Xay",
            "name_en": "Matcha Frozen",
            "price": 45000,
            "description": "Trà xanh Nhật Bản xay đá",
            "image_url": "https://storage.../matcha-frozen.jpg"
          }
        ]
      }
    ]
  }'
```

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `categories` | array | ✅ | Product categories |

### Category Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | ✅ | Category name (Vietnamese) |
| `name_en` | string | ❌ | Category name (English) |
| `items` | array | ✅ | Products in category |

### Item Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | ✅ | Item name (Vietnamese) |
| `name_en` | string | ❌ | Item name (English) |
| `price` | integer | ✅ | Price in VND |
| `description` | string | ❌ | Item description |
| `image_url` | string | ❌ | Product image URL |

### Response (200 OK)

```json
{
  "step": 3,
  "status": "completed",
  "categories_count": 2,
  "items_count": 3,
  "next_step": {
    "step": 4,
    "name": "activate",
    "description": "Activate your account"
  },
  "message": "Menu setup completed"
}
```

### Error Responses

**400 Invalid Price:**
```json
{
  "error": "VALIDATION_ERROR",
  "message": "Price must be a positive integer"
}
```

---

## POST /v1/onboarding/activate — Step 4: Activate Account

### Request

```bash
curl -X POST https://agencyos.network/v1/onboarding/activate \
  -H "Authorization: Bearer $RAAS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "confirm": true,
    "terms_accepted": true,
    "privacy_accepted": true
  }'
```

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `confirm` | boolean | ✅ | Confirmation to activate |
| `terms_accepted` | boolean | ✅ | Accept terms of service |
| `privacy_accepted` | boolean | ✅ | Accept privacy policy |

### Response (200 OK)

```json
{
  "step": 4,
  "status": "completed",
  "account_status": "active",
  "activated_at": "2026-03-19T10:30:00Z",
  "welcome_bonus": {
    "credits": 10,
    "description": "Welcome bonus for completing onboarding"
  },
  "message": "Account activated! You can now create missions."
}
```

### What Happens on Activation

1. Account status changed to `active`
2. Welcome bonus (10 credits) added
3. First mission can be created
4. Onboarding flow marked complete
5. Welcome email sent

### Error Responses

**400 Not Completed:**
```json
{
  "error": "VALIDATION_ERROR",
  "message": "Please complete previous steps first"
}
```

---

## Skip Optional Steps

Steps 2-3 are optional but recommended:

```bash
# Skip channel connection (not recommended)
curl -X POST https://agencyos.network/v1/onboarding/skip \
  -H "Authorization: Bearer $RAAS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "step": "channel",
    "reason": "Will configure later"
  }'
```

### Skippable Steps

| Step | Skippable? | Recommendation |
|------|------------|----------------|
| Profile | ❌ No | Required for billing |
| Channel | ✅ Yes | Recommended for omnichannel |
| Menu | ✅ Yes | Recommended for F&B/retail |
| Activate | ❌ No | Required to use platform |

---

## Onboarding Completion Checklist

```
✅ Step 1: Profile
   - Business name registered
   - Industry classified
   - Preferences set (language, currency, timezone)

✅ Step 2: Channels (optional)
   - Zalo OA connected
   - Facebook Page connected

✅ Step 3: Menu (optional)
   - Product categories created
   - Items with prices added

✅ Step 4: Activate
   - Terms accepted
   - Account activated
   - Welcome bonus received
```

---

## Related Endpoints

- [POST /billing/tenants](./billing.md) — Create tenant (prerequisite)
- [POST /v1/tasks](./tasks.md) — Create first mission
- [GET /v1/onboarding/status](#) — Check progress

---

## Next Steps

- [Tasks API](./tasks.md) — Create your first AI mission
- [Billing API](./billing.md) — Manage credits and subscriptions
- [Chat API](./chat.md) — Configure communication channels
