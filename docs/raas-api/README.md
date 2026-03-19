# RaaS API Documentation

> **Revenue-as-a-Service API** - AI-operated business platform với credit metering, revenue distribution, và progressive decentralization.

**Version:** 5.0.0 | **License:** MIT

---

## Quick Start

### 1. Tạo Tenant (Nhận 10 credits free)

```bash
curl -X POST https://api.raas.mekong.network/billing/tenants \
  -H "Content-Type: application/json" \
  -d '{"name": "My Cafe"}'
```

**Response:**
```json
{
  "tenant_id": "tenant_abc123",
  "api_key": "sk_live_7x8y9z0a1b2c3d4e5f6g",
  "credits": 10,
  "message": "Save your API key — it cannot be recovered if lost!"
}
```

### 2. Tạo Mission Đầu Tiên

```bash
curl -X POST https://api.raas.mekong.network/v1/tasks \
  -H "Authorization: Bearer sk_live_7x8y9z0a1b2c3d4e5f6g" \
  -H "Content-Type: application/json" \
  -d '{"goal": "Write a blog post about coffee brewing"}'
```

### 3. Track Progress qua SSE

```bash
curl -X GET https://api.raas.mekong.network/v1/tasks/mission_xyz789/stream \
  -H "Authorization: Bearer sk_live_7x8y9z0a1b2c3d4e5f6g"
```

---

## Table of Contents

### Core APIs
| Category | File | Endpoints | Description |
|----------|------|-----------|-------------|
| [Tasks](./endpoints/tasks.md) | `endpoints/tasks.md` | 5 | Mission management với credit metering |
| [Agents](./endpoints/agents.md) | `endpoints/agents.md` | 2 | Agent execution (git, file, shell, content-writer) |
| [Billing](./endpoints/billing.md) | `endpoints/billing.md` | 6 | Tenant creation, API keys, Polar.sh webhooks |
| [Settings](./endpoints/settings.md) | `endpoints/settings.md` | 3 | LLM BYOK configuration |
| [Onboarding](./endpoints/onboarding.md) | `endpoints/onboarding.md` | 5 | 4-step tenant onboarding flow |

### Communication & Content
| Category | File | Endpoints | Description |
|----------|------|-----------|-------------|
| [Chat](./endpoints/chat.md) | `endpoints/chat.md` | 3 | Zalo OA + Facebook Messenger webhooks |
| [Content](./endpoints/content.md) | `endpoints/content.md` | 3 | AI content generation for social media |
| [CRM](./endpoints/crm.md) | `endpoints/crm.md` | 4 | Contact management, remarketing campaigns |
| [Reports](./endpoints/reports.md) | `endpoints/reports.md` | 2 | Analytics với AI-generated summaries |
| [Payment](./endpoints/payment.md) | `endpoints/payment.md` | 4 | Vietnam payment gateways (MoMo, VNPAY) |

### Governance & Finance
| Category | File | Endpoints | Description |
|----------|------|-----------|-------------|
| [Governance](./endpoints/governance.md) | `endpoints/governance.md` | 8 | Quadratic voting, proposals, Ngũ Sự scoring |
| [Ledger](./endpoints/ledger.md) | `endpoints/ledger.md` | 4 | Double-entry accounting transfers |
| [Equity](./endpoints/equity.md) | `endpoints/equity.md` | 6 | Equity entities, grants, cap tables, SAFE |
| [Revenue](./endpoints/revenue.md) | `endpoints/revenue.md` | 1 | 6-way revenue split distribution |
| [Funding](./endpoints/funding.md) | `endpoints/funding.md` | 5 | Quadratic funding rounds với matching pool |

### Advanced Features
| Category | File | Endpoints | Description |
|----------|------|-----------|-------------|
| [Matching](./endpoints/matching.md) | `endpoints/matching.md` | 3 | Skill/expert matching system |
| [Conflicts](./endpoints/conflicts.md) | `endpoints/conflicts.md` | 4 | 5-level conflict resolution với SLA |
| [Decentralization](./endpoints/decentralization.md) | `endpoints/decentralization.md` | 2 | Progressive decentralization phase tracking |
| [RBAC](./endpoints/rbac.md) | `endpoints/rbac.md` | 2 | Permission checking for stakeholders |

---

## Authentication

Tất cả endpoints yêu cầu Bearer token API key (trừ health check và webhook endpoints).

```bash
Authorization: Bearer sk_live_7x8y9z0a1b2c3d4e5f6g
```

### Security Levels

| Endpoint Type | Auth Required | Notes |
|---------------|---------------|-------|
| Health check | ❌ No | Public endpoint |
| Webhooks (Zalo, Facebook, Polar.sh, MoMo, VNPAY) | ❌ No | HMAC signature verification |
| All other endpoints | ✅ Yes | Bearer token required |

---

## Credit System

### Credit Costs by Complexity

| Complexity | Credits | Examples |
|------------|---------|----------|
| Simple | 1 | "Summarize this document", "Fix typo" |
| Standard | 3 | "Write a blog post", "Analyze sales data" |
| Complex | 5 | "Build a landing page", "Refactor auth module" |

### Credit Flow

```
1. Check tenant credit balance
2. Deduct estimated credits (before execution)
3. Execute mission
4. Refund unused credits (on completion/cancel)
```

### Refund Policy

- **Mission cancelled** (pending): Full refund
- **Mission failed** (system error): Full refund
- **Mission failed** (user error): No refund

---

## Governance Levels

| Level | Name | Description |
|-------|------|-------------|
| 1 | Community | Basic participation |
| 2 | Customer | Product users |
| 3 | Developer | Code contributors |
| 4 | Expert | Domain experts |
| 5 | Founder | Core team |
| 6 | Owner | Full control |

### Quadratic Voting Formula

```
votes = √credits
cost = votes² credits
```

### Quadratic Funding Formula

```
sqrtSum = Σ√ci
directSum = Σci
qfScore = sqrtSum² - directSum

matched = (qfScore / totalQfScore) × matching_pool
```

---

## Ngũ Sự Scoring Framework

5 yếu tố đánh giá proposal terrain:

| Terrain | Name | Description |
|---------|------|-------------|
| Tản Địa | Dispersive | Người muốn về |
| Khinh Địa | Shallow | Vào nông |
| Tranh Địa | Contentious | Ai kiểm soát? |
| Giao Địa | Open | Tự do qua lại |
| Trung Địa | Central | Ngã tư |
| Vi Địa | Remote | Xa xôi |
| Tử Địa | Desperate | Đường cùng |

---

## Base URLs

| Environment | URL |
|-------------|-----|
| Production | `https://agencyos.network` |
| Staging | `https://staging.agencyos.network` |
| Local Development | `http://localhost:8787` |

---

## Error Handling

### Standard Error Format

```json
{
  "error": "VALIDATION_ERROR",
  "code": "INVALID_INPUT",
  "details": [
    {"field": "goal", "message": "Goal is required"}
  ]
}
```

### HTTP Status Codes

| Code | Error | Description |
|------|-------|-------------|
| 400 | BAD_REQUEST | Invalid request body |
| 401 | UNAUTHORIZED | Missing or invalid API key |
| 402 | INSUFFICIENT_CREDITS | Not enough credits |
| 404 | NOT_FOUND | Resource not found |
| 409 | CONFLICT | Resource conflict |
| 503 | SERVICE_UNAVAILABLE | Database not configured |

---

## Rate Limits

| Tier | Requests/minute | Notes |
|------|-----------------|-------|
| Free | 60 | 1 request/second |
| Starter | 120 | 2 requests/second |
| Pro | 300 | 5 requests/second |
| Enterprise | 1000 | 16 requests/second |

---

## SDKs & Libraries

- **TypeScript SDK**: Coming soon
- **Python SDK**: Coming soon
- **OpenAPI Spec**: [raas-api-reference.yaml](https://github.com/agencyos/mekong-cli/blob/main/raas-api-reference.yaml)

---

## Related Documentation

- [Getting Started Guide](../../getting-started.md) — From signup to first AI task
- [Onboarding Guide](../../docs/onboarding.md) — 4-step tenant onboarding
- [Governance Guide](../../docs/governance.md) — Quadratic voting & proposals
- [Binh Pháp Philosophy](../../docs/binh-phap-philosophy.md) — Strategic framework

---

**Support:** support@agencyos.network | **Discord:** https://discord.gg/agencyos
