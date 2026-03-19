# Reports API — Analytics & AI Summaries

> **Purpose**: Báo cáo hiệu suất hàng tuần với AI-generated insights.

---

## Endpoints Overview

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/v1/reports/weekly` | ✅ | Weekly report with AI summary |

---

## GET /v1/reports/weekly — Weekly Report

### Request

```bash
curl -X GET "https://agencyos.network/v1/reports/weekly?days=7" \
  -H "Authorization: Bearer $RAAS_API_KEY"
```

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `days` | integer | ❌ | Number of days (default: 7, max: 30) |

### Response (200 OK)

```json
{
  "period": {
    "start": "2026-03-12T00:00:00Z",
    "end": "2026-03-19T00:00:00Z",
    "days": 7
  },
  "metrics": {
    "messages_handled": 1247,
    "new_contacts": 89,
    "active_conversations": 156,
    "content_posts": {
      "draft": 12,
      "scheduled": 8,
      "published": 21
    },
    "campaigns_sent": 342,
    "campaign_responses": 118
  },
  "trends": {
    "messages_handled": 0.23,
    "new_contacts": 0.15,
    "conversations": -0.08,
    "content_published": 0.45
  },
  "ai_summary": {
    "overview": "Tuần này đạt hiệu suất cao với 1,247 messages được xử lý, tăng 23% so với tuần trước. Campaign 'VIP Comeback' đạt response rate 35%, vượt mức trung bình 28%.",
    "highlights": [
      "Content generation tăng 45% — 21 posts được publish",
      "89 contacts mới được thêm vào CRM từ Zalo OA và Facebook",
      "Campaign response rate cải thiện từ 28% lên 34%"
    ],
    "recommendations": [
      "Tăng frequency cho campaign 'VIP Comeback' do response rate cao",
      "Xem xét mở rộng content sang LinkedIn do engagement tốt",
      "Optimize chatbot responses cho câu hỏi về pricing (30% volume)"
    ],
    "alerts": [
      "Conversation volume giảm 8% — có thể do seasonal effect"
    ]
  },
  "generated_at": "2026-03-19T10:30:00Z"
}
```

### Metrics Object

| Field | Type | Description |
|-------|------|-------------|
| `messages_handled` | integer | Total messages processed across all channels |
| `new_contacts` | integer | New contacts added to CRM |
| `active_conversations` | integer | Active conversation threads |
| `content_posts` | object | Content posts by status |
| `campaigns_sent` | integer | Total campaign messages sent |
| `campaign_responses` | integer | User responses to campaigns |

### Content Posts Object

| Field | Type | Description |
|-------|------|-------------|
| `draft` | integer | AI-generated posts not yet scheduled |
| `scheduled` | integer | Posts queued for publishing |
| `published` | integer | Posts published to platforms |

### Trends Object

| Field | Type | Description |
|-------|------|-------------|
| `messages_handled` | float | Week-over-week change (0.23 = +23%) |
| `new_contacts` | float | Week-over-week change |
| `conversations` | float | Week-over-week change |
| `content_published` | float | Week-over-week change |

### AI Summary Object

| Field | Type | Description |
|-------|------|-------------|
| `overview` | string | Executive summary paragraph |
| `highlights` | array | Key achievements this period |
| `recommendations` | array | Actionable suggestions |
| `alerts` | array | Items requiring attention |

### Error Responses

**400 Invalid Days:**
```json
{
  "error": "VALIDATION_ERROR",
  "message": "Days must be between 1 and 30"
}
```

---

## AI Summary Generation

### Prompt Template

```
You are a business intelligence analyst for a RaaS (Revenue-as-a-Service) platform.

Generate a weekly performance summary based on these metrics:
- Messages handled: {messages_handled} ({messages_trend}% vs last week)
- New contacts: {new_contacts} ({new_contacts_trend}%)
- Active conversations: {conversations} ({conversations_trend}%)
- Content posts: {draft} drafts, {scheduled} scheduled, {published} published
- Campaigns: {campaigns_sent} sent, {campaign_responses} responses ({response_rate}% rate)

Business context:
- Industry: {industry}
- Primary channels: {channels}
- Current campaigns: {campaign_names}

Output format:
{{
  "overview": "2-3 sentence executive summary",
  "highlights": ["achievement 1", "achievement 2", ...],
  "recommendations": ["suggestion 1", "suggestion 2", ...],
  "alerts": ["concern 1", ...]
}}

Tone: Professional, actionable, Vietnamese language.
Focus on revenue-impacting metrics and growth opportunities.
```

### Example AI Output

```json
{
  "overview": "Tuần này đạt hiệu suất cao với 1,247 messages được xử lý, tăng 23% so với tuần trước. Campaign 'VIP Comeback' đạt response rate 35%, vượt mức trung bình 28%. Content generation tăng mạnh với 21 posts được publish.",
  "highlights": [
    "Content generation tăng 45% — 21 posts được publish trên Facebook, Instagram, LinkedIn",
    "89 contacts mới được thêm vào CRM từ Zalo OA và Facebook Messenger",
    "Campaign response rate cải thiện từ 28% lên 34% (+6 điểm phần trăm)",
    "Zalo OA channel chiếm 67% total messages, vượt Facebook (28%) và Web (5%)"
  ],
  "recommendations": [
    "Tăng frequency cho campaign 'VIP Comeback' do response rate cao (35%) — xem xét gửi 2x/tuần",
    "Xem xét mở rộng content sang LinkedIn do engagement rate tốt (4.2% vs 2.8% average)",
    "Optimize chatbot responses cho câu hỏi về pricing (chiếm 30% total messages volume)",
    "Setup A/B test cho message templates — hiện tại chỉ dùng 1 template duy nhất"
  ],
  "alerts": [
    "Conversation volume giảm 8% — có thể do seasonal effect (holiday weekend)",
    "Credit balance còn 45 credits — cần recharge trong 5-7 ngày tới"
  ]
}
```

---

## Metrics Calculation

### Messages Handled

```sql
SELECT COUNT(*)
FROM messages
WHERE tenant_id = ?
  AND created_at >= NOW() - INTERVAL '{days} DAYS'
```

### New Contacts

```sql
SELECT COUNT(*)
FROM contacts
WHERE tenant_id = ?
  AND created_at >= NOW() - INTERVAL '{days} DAYS'
```

### Active Conversations

```sql
SELECT COUNT(DISTINCT thread_id)
FROM messages
WHERE tenant_id = ?
  AND created_at >= NOW() - INTERVAL '{days} DAYS'
```

### Content Posts by Status

```sql
SELECT status, COUNT(*) as count
FROM content_posts
WHERE tenant_id = ?
  AND created_at >= NOW() - INTERVAL '{days} DAYS'
GROUP BY status
```

### Campaign Response Rate

```sql
SELECT
  COUNT(DISTINCT response_id) * 100.0 / COUNT(DISTINCT sent_id) as response_rate
FROM campaign_events
WHERE tenant_id = ?
  AND event_type IN ('sent', 'response')
  AND created_at >= NOW() - INTERVAL '{days} DAYS'
```

---

## Trend Calculation

Week-over-week percentage change:

```typescript
function calculateTrend(current: number, previous: number): number {
  if (previous === 0) return current > 0 ? 1.0 : 0.0;
  return ((current - previous) / previous);
}

// Example:
// Current: 1247, Previous: 1014
// Trend: (1247 - 1014) / 1014 = 0.23 (+23%)
```

---

## Use Cases

### Weekly Performance Review

```bash
# Every Monday, generate last week's report
curl -X GET "https://agencyos.network/v1/reports/weekly?days=7" \
  -H "Authorization: Bearer $RAAS_API_KEY"
```

**Use for:**
- Monday team standup
- Investor updates
- Performance bonus calculations

### Monthly Executive Summary

```bash
# End of month report
curl -X GET "https://agencyos.network/v1/reports/weekly?days=30" \
  -H "Authorization: Bearer $RAAS_API_KEY"
```

**Use for:**
- Board meetings
- Monthly OKR reviews
- Billing reconciliation

### Campaign Performance Analysis

```bash
# Pre-campaign vs post-campaign comparison
# Week 1 (before)
curl -X GET "https://agencyos.network/v1/reports/weekly?days=7&end=2026-03-12" \
  -H "Authorization: Bearer $RAAS_API_KEY"

# Week 2 (after campaign)
curl -X GET "https://agencyos.network/v1/reports/weekly?days=7&end=2026-03-19" \
  -H "Authorization: Bearer $RAAS_API_KEY"
```

---

## AI Summary Customization

### Industry-Specific Insights

**F&B (Coffee Shop):**
```json
{
  "recommendations": [
    "Push morning campaign (7-9 AM) — current send time 2 PM has low open rate",
    "Add weather-triggered messages — rainy days see 40% drop in foot traffic"
  ]
}
```

**E-commerce:**
```json
{
  "recommendations": [
    "Abandoned cart campaign cần send trong 1 giờ — hiện tại send sau 24h, conversion rate thấp",
    "Thêm SMS channel cho high-value carts (>500kđ)"
  ]
}
```

**Services:**
```json
{
  "recommendations": [
    "Setup booking reminder campaign — no-show rate 15% cần giảm",
    "Add post-service feedback request — hiện tại 0% collection rate"
  ]
}
```

---

## Data Retention

| Data Type | Retention Period |
|-----------|------------------|
| Raw metrics | 90 days |
| Weekly reports | 1 year |
| AI summaries | 1 year |
| Aggregated monthly | Unlimited |

---

## Related Endpoints

- [GET /v1/crm/contacts](./crm.md) — Contact metrics
- [GET /v1/content](./content.md) — Content post metrics
- [GET /v1/crm/campaigns](./crm.md) — Campaign metrics
- [POST /v1/agents/content-writer/run](./agents.md) — Content generation

---

## Next Steps

- [Payment API](./payment.md) — Vietnam payment gateways (MoMo, VNPAY)
- [Governance API](./governance.md) — Quadratic voting and proposals
- [Ledger API](./ledger.md) — Double-entry accounting
