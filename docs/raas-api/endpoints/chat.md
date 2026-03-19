# Chat API — Messaging Webhooks

> **Purpose**: Tích hợp Zalo OA và Facebook Messenger webhooks để nhận và gửi messages với AI responses.

---

## Endpoints Overview

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/v1/chat/webhook/zalo` | ✅ | Zalo OA webhook |
| GET | `/v1/chat/webhook/facebook` | ❌ | Facebook webhook verification |
| POST | `/v1/chat/webhook/facebook` | ❌ | Facebook Messenger webhook |

---

## POST /v1/chat/webhook/zalo — Zalo OA Webhook

### Purpose

Nhận messages từ Zalo Official Account, xử lý qua AI, và gửi replies.

### Request Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Zalo OA    │ →   │  Webhook    │ →   │  AI Engine  │ →   │  Zalo OA    │
│  Message    │     │  Receiver   │     │  Response   │     │  Reply      │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
     ↓                   ↓                   ↓                   ↓
  User sends        Verify HMAC         Query KB/LLM      Send response
  message           Parse payload       Generate reply    back to user
```

### Request

```http
POST /v1/chat/webhook/zalo
Content-Type: application/json
webhook-signature: sha256=abc123...

{
  "sender": {
    "id": "user_zalo_123",
    "name": "Nguyen Van A"
  },
  "message": {
    "text": "Tôi muốn tư vấn về gói cước Pro",
    "type": "text"
  },
  "thread": {
    "id": "thread_abc123"
  },
  "timestamp": "2026-03-19T10:30:00Z"
}
```

### Request Headers

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `webhook-signature` | string | ✅ | HMAC-SHA256 signature |

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sender` | object | ✅ | Message sender |
| `message` | object | ✅ | Message content |
| `thread` | object | ❌ | Conversation thread |
| `timestamp` | string | ✅ | ISO 8601 timestamp |

### Sender Object

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Zalo user ID |
| `name` | string | User display name |

### Message Object

| Field | Type | Description |
|-------|------|-------------|
| `text` | string | Message text (for text messages) |
| `type` | string | `text`, `image`, `location`, etc. |

### Response (200 OK)

```json
{
  "status": "success",
  "reply": {
    "text": "Chào bạn! Gói Pro của chúng tôi bao gồm 200 credits/tháng với giá 499kđ. Bạn có thể xem chi tiết tại https://agencyos.network/pricing",
    "type": "text"
  },
  "processing_time_ms": 850
}
```

### Response Object

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | `success` or `error` |
| `reply` | object | AI-generated response |
| `processing_time_ms` | integer | Processing latency |

### Error Responses

**401 Invalid Signature:**
```json
{
  "error": "UNAUTHORIZED",
  "code": "INVALID_SIGNATURE",
  "message": "HMAC signature verification failed"
}
```

**400 Invalid Payload:**
```json
{
  "error": "BAD_REQUEST",
  "message": "Missing required field: sender"
}
```

---

## GET /v1/chat/webhook/facebook — Facebook Verification

### Purpose

Verify webhook subscription với Facebook Messenger Platform.

### Request

```http
GET /v1/chat/webhook/facebook?hub.mode=subscribe&hub.verify_token=your_token&hub.challenge=challenge_code
```

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `hub.mode` | string | ✅ | `subscribe` for verification |
| `hub.verify_token` | string | ✅ | Token configured in Facebook App |
| `hub.challenge` | string | ✅ | Challenge code to return |

### Response (200 OK)

```
<hub.challenge_value>
```

**Example:**
```
1234567890
```

### Facebook App Setup

1. **Create Facebook App:**
   - Go to https://developers.facebook.com
   - Create new app → Select "Business" → Add "Messenger" product

2. **Configure Webhook:**
   - Go to Messenger → Settings → Webhooks
   - Add callback URL: `https://agencyos.network/v1/chat/webhook/facebook`
   - Verify token: `your_secret_token` (configure in env)

3. **Subscribe Fields:**
   - `messages` — Receive message events
   - `messaging_postbacks` — Receive postback events
   - `messaging_optins` — Receive opt-in events

4. **Verify:**
   - Facebook sends GET request with `hub.mode=subscribe`
   - Return `hub.challenge` value to complete verification

---

## POST /v1/chat/webhook/facebook — Facebook Messenger Webhook

### Purpose

Nhận messages từ Facebook Messenger, xử lý qua AI, và gửi replies.

### Request

```http
POST /v1/chat/webhook/facebook
Content-Type: application/json

{
  "object": "page",
  "entry": [
    {
      "id": "page_123456",
      "time": 1710842400000,
      "messaging": [
        {
          "sender": {
            "id": "user_fb_789"
          },
          "recipient": {
            "id": "page_123456"
          },
          "timestamp": 1710842400000,
          "message": {
            "mid": "msg_abc123",
            "text": "I want to learn about your pricing"
          }
        }
      ]
    }
  ]
}
```

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `object` | string | ✅ | Always `page` |
| `entry` | array | ✅ | Array of page entries |

### Entry Object

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Page ID |
| `time` | integer | Unix timestamp (ms) |
| `messaging` | array | Array of messaging events |

### Messaging Event Object

| Field | Type | Description |
|-------|------|-------------|
| `sender` | object | User who sent the message |
| `recipient` | object | Page receiving the message |
| `timestamp` | integer | Message timestamp |
| `message` | object | Message content |

### Message Object

| Field | Type | Description |
|-------|------|-------------|
| `mid` | string | Message ID |
| `text` | string | Message text |
| `attachments` | array | Optional attachments (images, files) |

### Response (200 OK)

```json
{
  "status": "success",
  "message": "Webhook received and processing"
}
```

### Facebook Response Format

Facebook expects HTTP 200 OK response. If not received:
- Facebook retries delivery
- Events marked as failed after 3 attempts

### Send Message to Facebook

After processing, send reply via Facebook Graph API:

```bash
curl -X POST "https://graph.facebook.com/v18.0/me/messages" \
  -H "Authorization: Bearer <PAGE_ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "recipient": {"id": "user_fb_789"},
    "message": {
      "text": "Our pricing starts at $49/month for the Starter plan..."
    }
  }'
```

---

## Message Schema Definitions

### ZaloMessage

```typescript
interface ZaloMessage {
  sender: {
    id: string;      // Zalo user ID
    name: string;    // Display name
  };
  message: {
    text?: string;   // Message text (for text type)
    type: 'text' | 'image' | 'location' | 'sticker';
    url?: string;    // Image/sticker URL
  };
  thread: {
    id: string;      // Conversation thread ID
  };
  timestamp: string; // ISO 8601
}
```

### FacebookMessage

```typescript
interface FacebookMessage {
  object: 'page';
  entry: [
    {
      id: string;    // Page ID
      time: number;  // Unix timestamp (ms)
      messaging: [
        {
          sender: { id: string };
          recipient: { id: string };
          timestamp: number;
          message: {
            mid: string;
            text?: string;
            attachments?: Array<{
              type: string;
              payload: { url: string };
            }>;
          };
        }
      ];
    }
  ];
}
```

---

## Security

### HMAC Signature Verification (Zalo)

```typescript
const secret = c.env.ZALO_WEBHOOK_SECRET;
const signature = c.req.header('webhook-signature');
const rawBody = await c.req.text();

// Verify HMAC-SHA256 signature
const keyData = new TextEncoder().encode(secret);
const msgData = new TextEncoder().encode(rawBody);
const cryptoKey = await crypto.subtle.importKey(
  'raw', keyData, { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']
);
const sigBuffer = await crypto.subtle.sign('HMAC', cryptoKey, msgData);
const expectedSig = Array.from(new Uint8Array(sigBuffer))
  .map(b => b.toString(16).padStart(2, '0')).join('');

if (signature !== expectedSig) {
  return c.json({ error: 'Invalid signature' }, 401);
}
```

### Facebook Verify Token

```typescript
const verifyToken = c.env.FACEBOOK_VERIFY_TOKEN;
const params = c.req.query();

if (params['hub.mode'] === 'subscribe' &&
    params['hub.verify_token'] === verifyToken) {
  return new Response(params['hub.challenge']);
}

return new Response('Forbidden', { status: 403 });
```

---

## AI Processing Flow

### Step 1: Parse Incoming Message

```typescript
const { sender, message, thread } = await c.req.json();
const userId = sender.id;
const messageText = message.text;
```

### Step 2: Query Knowledge Base

```typescript
// Search KB for relevant articles
const kbResults = await d1.prepare(
  'SELECT * FROM kb_articles WHERE MATCH(?) ORDER BY score DESC LIMIT 5'
).bind(messageText).all();
```

### Step 3: Generate LLM Response

```typescript
const prompt = `
You are a helpful customer support agent.

Context from knowledge base:
${kbResults.results.map(r => r.content).join('\n')}

User question: ${messageText}

Provide a helpful, concise response.
`;

const response = await fetch(env.LLM_BASE_URL + '/chat/completions', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${env.LLM_API_KEY}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    model: env.LLM_MODEL,
    messages: [{ role: 'user', content: prompt }]
  })
});
```

### Step 4: Send Reply

**Zalo:**
```typescript
await fetch('https://openapi.zalo.me/v2.0/oa/message/send', {
  method: 'POST',
  headers: {
    'access_token': env.ZALO_OA_TOKEN
  },
  body: JSON.stringify({
    receiver: { user_id: userId },
    message: { msg: aiResponse }
  })
});
```

**Facebook:**
```typescript
await fetch(`https://graph.facebook.com/v18.0/me/messages`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${env.FACEBOOK_PAGE_TOKEN}`
  },
  body: JSON.stringify({
    recipient: { id: userId },
    message: { text: aiResponse }
  })
});
```

---

## Integration Examples

### Zalo OA Setup

1. **Create Zalo Official Account:**
   - Go to https://oa.zalo.me
   - Register business account
   - Complete verification

2. **Get Credentials:**
   - Go to OA Settings → API
   - Generate `client_id` and `secret_key`
   - Set webhook URL: `https://agencyos.network/v1/chat/webhook/zalo`

3. **Configure Environment:**
   ```bash
   export ZALO_OA_ID="1234567890"
   export ZALO_OA_TOKEN="your_access_token"
   export ZALO_WEBHOOK_SECRET="your_hmac_secret"
   ```

### Facebook Page Setup

1. **Create Facebook App:**
   - Go to https://developers.facebook.com
   - Create app → Business → Add Messenger

2. **Get Page Access Token:**
   - Go to Messenger → Settings → Access Token
   - Generate long-lived token
   - Or use Graph API Explorer

3. **Configure Webhook:**
   - Callback URL: `https://agencyos.network/v1/chat/webhook/facebook`
   - Verify Token: `your_secret_token`
   - Subscribe to: `messages`, `messaging_postbacks`

4. **Configure Environment:**
   ```bash
   export FACEBOOK_PAGE_ID="987654321"
   export FACEBOOK_PAGE_TOKEN="your_page_token"
   export FACEBOOK_VERIFY_TOKEN="your_verify_token"
   ```

---

## Error Handling

### Retry Logic

Both Zalo and Facebook retry failed deliveries:

- **Zalo:** 3 retries with exponential backoff
- **Facebook:** 3 retries over 1 hour

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `INVALID_SIGNATURE` | HMAC mismatch | Check webhook secret |
| `MISSING_VERIFY_TOKEN` | Facebook token mismatch | Verify token in env |
| `RATE_LIMITED` | Too many requests | Implement throttling |
| `INVALID_RECIPIENT` | User blocked OA/Page | Check user status |

---

## Related Endpoints

- [POST /v1/tasks](./tasks.md) — Create AI missions
- [POST /v1/agents/content-writer/run](./agents.md) — Content generation
- [GET /v1/settings/llm](./settings.md) — LLM configuration

---

## Next Steps

- [Tasks API](./tasks.md) — Create AI missions for complex queries
- [Agents API](./agents.md) — Run specialized content agents
- [Onboarding API](./onboarding.md) — Complete tenant setup
