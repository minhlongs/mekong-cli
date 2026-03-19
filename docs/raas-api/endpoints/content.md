# Content API — AI Content Generation

> **Purpose**: Tạo nội dung social media tự động với AI cho 7-14 ngày.

---

## Endpoints Overview

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/v1/content/generate` | ✅ | Generate 7-14 days of content |
| GET | `/v1/content` | ✅ | List content with filters |
| PATCH | `/v1/content/:id` | ✅ | Update content status |

---

## POST /v1/content/generate — Generate Content

### Request

```bash
curl -X POST https://agencyos.network/v1/content/generate \
  -H "Authorization: Bearer $RAAS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Coffee brewing techniques for beginners",
    "days": 7,
    "tone": "friendly"
  }'
```

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `topic` | string | ✅ | Content topic/theme |
| `days` | integer | ❌ | Number of days (7-14, default: 7) |
| `tone` | string | ❌ | `professional`, `friendly`, `humorous`, `inspirational` |

### Tone Options

| Tone | Description | Example |
|------|-------------|---------|
| `professional` | Formal, authoritative | "Discover our premium coffee selection" |
| `friendly` | Casual, conversational | "Hey coffee lovers! ☕" |
| `humorous` | Playful, witty | "But first, coffee... always coffee" |
| `inspirational` | Motivational, uplifting | "Start your day with purpose and caffeine" |

### Response (201 Created)

```json
{
  "generated_at": "2026-03-19T10:30:00Z",
  "topic": "Coffee brewing techniques for beginners",
  "days": 7,
  "posts": [
    {
      "id": "post_001",
      "day": 1,
      "platform": "facebook",
      "content": "☕ New to coffee brewing? Start with the French Press! It's forgiving, affordable, and produces rich, full-bodied coffee. Tip: Use a 1:15 coffee-to-water ratio and steep for 4 minutes. #CoffeeTips #BrewingGuide",
      "hashtags": ["#CoffeeTips", "#BrewingGuide", "#FrenchPress"],
      "status": "draft",
      "scheduled_for": null
    },
    {
      "id": "post_002",
      "day": 1,
      "platform": "instagram",
      "content": "French Press Friday ☕✨\n\nThe secret to perfect French Press coffee:\n• Coarse grind (like sea salt)\n• 200°F water (not boiling!)\n• 4 minute steep time\n• Gentle plunge\n\nTag a coffee newbie who needs this! 👇\n\n#CoffeeLovers #BrewingTips #FrenchPress #CoffeeGuide #BaristaLife",
      "hashtags": ["#CoffeeLovers", "#BrewingTips", "#FrenchPress", "#CoffeeGuide", "#BaristaLife"],
      "status": "draft",
      "scheduled_for": null
    },
    {
      "id": "post_003",
      "day": 2,
      "platform": "facebook",
      "content": "Pour-over vs. French Press — which team are you? 🤔\n\nPour-over: Clean, bright flavors, precise control\nFrench Press: Rich body, bold taste, easy to use\n\nBoth are perfect for beginners! Start with what fits your style.\n\n#CoffeeDebate #BrewingMethods",
      "hashtags": ["#CoffeeDebate", "#BrewingMethods"],
      "status": "draft",
      "scheduled_for": null
    }
  ],
  "total_posts": 21,
  "credits_used": 5
}
```

### Response Object

| Field | Type | Description |
|-------|------|-------------|
| `generated_at` | string | ISO 8601 timestamp |
| `topic` | string | Generated topic |
| `days` | integer | Number of days generated |
| `posts` | array | Array of content posts |
| `total_posts` | integer | Total posts generated |
| `credits_used` | integer | Credits consumed |

### Post Object

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique post ID |
| `day` | integer | Day number (1-14) |
| `platform` | string | `facebook`, `instagram`, `linkedin`, `twitter` |
| `content` | string | Post content text |
| `hashtags` | array | Array of hashtags |
| `status` | string | `draft`, `scheduled`, `published` |
| `scheduled_for` | string | Scheduled publish time (ISO 8601) |

### Error Responses

**400 Invalid Days:**
```json
{
  "error": "VALIDATION_ERROR",
  "message": "Days must be between 7 and 14"
}
```

**400 Invalid Tone:**
```json
{
  "error": "VALIDATION_ERROR",
  "message": "Invalid tone. Must be one of: professional, friendly, humorous, inspirational"
}
```

**402 Insufficient Credits:**
```json
{
  "error": "INSUFFICIENT_CREDITS",
  "message": "Insufficient balance",
  "details": [{"balance": 1, "required": 5}]
}
```

---

## GET /v1/content — List Content

### Request

```bash
curl -X GET "https://agencyos.network/v1/content?status=draft&limit=20" \
  -H "Authorization: Bearer $RAAS_API_KEY"
```

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `status` | string | ❌ | Filter by status: `draft`, `scheduled`, `published` |
| `limit` | integer | ❌ | Max results (default: 50, max: 100) |
| `offset` | integer | ❌ | Pagination offset (default: 0) |

### Response (200 OK)

```json
{
  "posts": [
    {
      "id": "post_001",
      "topic": "Coffee brewing techniques for beginners",
      "platform": "facebook",
      "content": "☕ New to coffee brewing? Start with the French Press!...",
      "hashtags": ["#CoffeeTips", "#BrewingGuide"],
      "status": "draft",
      "created_at": "2026-03-19T10:30:00Z",
      "scheduled_for": null,
      "published_at": null
    },
    {
      "id": "post_002",
      "topic": "Coffee brewing techniques for beginners",
      "platform": "instagram",
      "content": "French Press Friday ☕✨...",
      "hashtags": ["#CoffeeLovers", "#BrewingTips"],
      "status": "scheduled",
      "created_at": "2026-03-19T10:30:00Z",
      "scheduled_for": "2026-03-20T08:00:00Z",
      "published_at": null
    },
    {
      "id": "post_003",
      "topic": "Coffee brewing techniques for beginners",
      "platform": "linkedin",
      "content": "Mastering the art of coffee brewing...",
      "hashtags": ["#Coffee", "#Professional"],
      "status": "published",
      "created_at": "2026-03-18T10:30:00Z",
      "scheduled_for": "2026-03-19T08:00:00Z",
      "published_at": "2026-03-19T08:00:00Z"
    }
  ],
  "total": 21,
  "limit": 20,
  "offset": 0
}
```

### Content Status Workflow

```
┌─────────┐     ┌──────────┐     ┌───────────┐
│  draft  │ →   │scheduled │ →   │ published │
└─────────┘     └──────────┘     └───────────┘
     ↓                ↓                ↓
  Created        Scheduled        Published
  by AI          for time         to platform
```

### Status Values

| Status | Description | Actions Available |
|--------|-------------|-------------------|
| `draft` | AI-generated, not scheduled | Edit, schedule, delete |
| `scheduled` | Queued for publishing | Edit, reschedule, cancel |
| `published` | Posted to platform | View analytics, delete |

---

## PATCH /v1/content/:id — Update Content

### Request

```bash
curl -X PATCH https://agencyos.network/v1/content/post_001 \
  -H "Authorization: Bearer $RAAS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "scheduled",
    "scheduled_for": "2026-03-20T08:00:00Z"
  }'
```

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | Content post ID |

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `status` | string | ❌ | `draft`, `scheduled`, `published` |
| `scheduled_for` | string | ❌ | ISO 8601 timestamp (required if status=scheduled) |
| `content` | string | ❌ | Edit post content |
| `hashtags` | array | ❌ | Edit hashtags |

### Response (200 OK)

```json
{
  "id": "post_001",
  "topic": "Coffee brewing techniques for beginners",
  "platform": "facebook",
  "content": "☕ New to coffee brewing? Start with the French Press!...",
  "hashtags": ["#CoffeeTips", "#BrewingGuide"],
  "status": "scheduled",
  "created_at": "2026-03-19T10:30:00Z",
  "scheduled_for": "2026-03-20T08:00:00Z",
  "published_at": null,
  "updated_at": "2026-03-19T10:35:00Z"
}
```

### Error Responses

**400 Invalid Status Transition:**
```json
{
  "error": "VALIDATION_ERROR",
  "message": "Cannot transition from 'published' to 'draft'"
}
```

**400 Missing Scheduled Time:**
```json
{
  "error": "VALIDATION_ERROR",
  "message": "scheduled_for is required when status is 'scheduled'"
}
```

**404 Not Found:**
```json
{
  "error": "NOT_FOUND",
  "message": "Content post not found"
}
```

---

## Content Generation Flow

```
1. User submits topic + tone + days
2. AI generates 7-14 days of content
   - 3 posts/day (Facebook, Instagram, LinkedIn)
   - Platform-optimized formatting
   - Relevant hashtags included
3. Posts saved as drafts
4. User reviews and schedules
5. Auto-publish at scheduled times
```

### Platform Optimization

| Platform | Content Length | Hashtag Strategy | Best Time |
|----------|----------------|------------------|-----------|
| Facebook | 40-80 chars | 2-3 hashtags | 8-9 AM |
| Instagram | 150-200 chars | 5-10 hashtags | 11 AM-1 PM |
| LinkedIn | 100-150 chars | 3-5 hashtags | 7-8 AM |
| Twitter | 280 chars | 1-2 hashtags | 12-1 PM |

---

## Use Cases

### E-commerce Product Launch

```json
{
  "topic": "New organic coffee bean collection launch",
  "days": 14,
  "tone": "exciting"
}
```

### Educational Content Series

```json
{
  "topic": "Coffee origin stories: Ethiopia, Colombia, Vietnam",
  "days": 7,
  "tone": "professional"
}
```

### Community Engagement

```json
{
  "topic": "Customer coffee moments and testimonials",
  "days": 7,
  "tone": "friendly"
}
```

---

## Credit Costs

| Operation | Credits |
|-----------|---------|
| Generate 7 days (21 posts) | 5 |
| Generate 14 days (42 posts) | 8 |
| List content | 0 |
| Update content | 0 |

---

## Related Endpoints

- [POST /v1/agents/content-writer/run](./agents.md) — Run content writer agent
- [POST /v1/chat/webhook/zalo](./chat.md) — Social media engagement
- [GET /v1/reports/analytics](./reports.md) — Content performance analytics

---

## Next Steps

- [CRM API](./crm.md) — Manage contacts and leads
- [Reports API](./reports.md) — Track content performance
- [Billing API](./billing.md) — Credit management
