# RaaS Platform - Technical Specifications

> **Revenue-as-a-Service Platform** - Enterprise-grade, serverless, globally distributed
> **Version:** 2.1.79 | **Last Updated:** 2026-03-19

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Infrastructure Architecture](#infrastructure-architecture)
3. [Revenue Distribution Engine](#revenue-distribution-engine)
4. [API Specifications](#api-specifications)
5. [Database Schema](#database-schema)
6. [Security Architecture](#security-architecture)
7. [Billing & MCU System](#billing--mcu-system)
8. [Scaling & Performance](#scaling--performance)
9. [Monitoring & Observability](#monitoring--observability)

---

## System Overview

### Platform Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    RaaS Platform Stack                           │
├─────────────────────────────────────────────────────────────────┤
│  Layer 1: Edge (Cloudflare)                                     │
│  • 275+ data centers • WAF/DDoS • CDN • TLS 1.3                │
├─────────────────────────────────────────────────────────────────┤
│  Layer 2: Compute (Workers + Pages)                             │
│  • API Gateway (Workers) • Dashboard (Pages/React)             │
├─────────────────────────────────────────────────────────────────┤
│  Layer 3: Core Engine (PEV)                                     │
│  • Planner • Executor • Verifier • Orchestrator                │
├─────────────────────────────────────────────────────────────────┤
│  Layer 4: Data (D1 + R2 + KV)                                   │
│  • D1 (SQLite) • R2 (Object Store) • KV (Cache)                │
└─────────────────────────────────────────────────────────────────┘
```

### Key Metrics

| Metric | Target | Current |
|--------|--------|---------|
| TTFB (Edge) | <50ms | ✅ 35-45ms |
| TTFB (Origin) | <200ms | ✅ 120-180ms |
| Cache Hit Rate | >95% | ✅ 96.2% |
| API Error Rate | <0.1% | ✅ 0.03% |
| Build Time | <10s | ✅ 6.8s |

---

## Infrastructure Architecture

### Global Edge Distribution

```
                    CLOUDFLARE GLOBAL NETWORK
    ┌────────────────┬────────────────┬────────────────┐
    │  NAM (40%)     │  EU (35%)      │  APAC (25%)    │
    │  Dallas, TX    │  Frankfurt, DE │  Singapore     │
    │  Ashburn, VA   │  Amsterdam, NL │  Tokyo, JP     │
    │  San Francisco │  London, UK    │  Sydney, AU    │
    └────────────────┴────────────────┴────────────────┘
```

### Compute Layer Specifications

| Component | Technology | Purpose |
|-----------|------------|---------|
| **API Gateway** | Cloudflare Workers | Auth, rate limiting, routing |
| **Dashboard** | Cloudflare Pages + React 19 | User interface |
| **RaaS Gateway** | Workers (TypeScript) | MCU validation, tenant auth |
| **PEV Engine** | Workers (Python/TS) | Plan-Execute-Verify loop |

### Data Layer Specifications

| Service | Type | Use Case | Retention |
|---------|------|----------|-----------|
| **D1** | SQLite (Edge) | Ledger, missions, tenants | Permanent |
| **R2** | S3-compatible | Backups, artifacts, logs | 30 days - 7 years |
| **KV** | Edge cache | Sessions, rate limits, config | 1 min - 24 hours |

---

## Revenue Distribution Engine

### Default Split Configuration (Binh Pháp Tam Giác Ngược)

```typescript
const DEFAULT_SPLIT = {
  platform: 0.20,       // 20% — Platform (AgencyOS)
  expert: 0.30,         // 30% — Expert/Partner
  ai_compute: 0.15,     // 15% — LLM inference cost
  developer: 0.15,      // 15% — Developer/agency
  community_fund: 0.10, // 10% — Treasury for quadratic funding
  customer_reward: 0.10 // 10% — Loyalty credits back to customer
}
// Sum: 100%
```

### Revenue Flow Diagram

```
Customer Payment → Platform Treasury → 6-Way Distribution
                           │
                           ▼
         ┌─────────────────────────────────┐
         │  Revenue Split Engine           │
         │  POST /v1/revenue/split         │
         └─────────────────────────────────┘
                           │
         ┌─────────────────┴─────────────────┐
         ▼                                   ▼
┌─────────────────┐               ┌─────────────────┐
│  Double-Entry   │               │  Stakeholder    │
│  Ledger (D1)    │               │  Accounts       │
│                 │               │                 │
│  • Debits: -1000│               │  • Platform: 200│
│  • Credits: +200│               │  • Expert: 300  │
│             +300│               │  • AI Compute   │
│             +150│               │    +150         │
│             +150│               │  • Developer    │
│             +100│               │    +150         │
│             +100│               │  • Community    │
└─────────────────┘               │    +100         │
                                  │  • Customer     │
                                  │    +100         │
                                  └─────────────────┘
```

### Worked Example: 1,000 MCU Task

| Recipient | % | Calculation | Amount (MCU) |
|-----------|---|-------------|--------------|
| Platform | 20% | 1000 × 0.20 | 200 |
| Expert | 30% | 1000 × 0.30 | 300 |
| AI Compute | 15% | 1000 × 0.15 | 150 |
| Developer | 15% | 1000 × 0.15 | 150 |
| Community Fund | 10% | 1000 × 0.10 | 100 |
| Customer Reward | 10% | 1000 × 0.10 | 100 |
| **TOTAL** | **100%** | | **1,000** |

### Partner Tier Bonuses

| Partner Tier | Base Expert Share | Bonus | Total Expert Share |
|--------------|-------------------|-------|-------------------|
| Registered | 30% | 0% | 30% |
| Certified | 30% | +5% | 35% |
| Strategic | 30% | +10% | 40% |
| Enterprise | 30% | +15-25% | 45-55% |

---

## API Specifications

### Base Configuration

```yaml
Base URL: https://api.mekong.engine
Auth: Bearer {tenant_api_key}
Content-Type: application/json
Rate Limit: 1000 req/min (per tenant)
```

### Core Endpoints

#### Revenue API

| Method | Endpoint | MCU Cost | Description |
|--------|----------|----------|-------------|
| POST | `/v1/revenue/split` | 15-25 | Execute 6-way distribution |
| GET | `/v1/revenue/split-config` | 1 | Get split percentages |
| GET | `/v1/revenue/summary` | 5 | Get revenue summary |

#### Ledger API

| Method | Endpoint | MCU Cost | Description |
|--------|----------|----------|-------------|
| POST | `/v1/ledger/transfer` | 10-15 | Transfer between accounts |
| POST | `/v1/ledger/topup` | 10-15 | Add credits from treasury |
| GET | `/v1/ledger/balance` | 1-5 | Get account balance |
| GET | `/v1/ledger/history` | 5-10 | Get transaction history |

#### Funding API (Quadratic Funding)

| Method | Endpoint | MCU Cost | Description |
|--------|----------|----------|-------------|
| POST | `/v1/funding/rounds` | 10-15 | Create funding round |
| POST | `/v1/funding/contribute` | 10-15 | Contribute to project |
| POST | `/v1/funding/rounds/:id/calculate` | 20-50 | Calculate QF matches |

#### Matching API

| Method | Endpoint | MCU Cost | Description |
|--------|----------|----------|-------------|
| POST | `/v1/matching/profiles` | 5-10 | Create skill profile |
| POST | `/v1/matching/requests` | 15-25 | Create match request |

### Example: Revenue Split Request

```bash
curl -X POST https://api.mekong.engine/v1/revenue/split \
  -H "Authorization: Bearer $MEKONG_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "total_credits": 1000,
    "customer_account": "customer:acme-corp",
    "expert_account": "expert:john-doe",
    "developer_account": "developer:agency-xyz",
    "description": "CRM integration setup"
  }'
```

### Example: Response

```json
{
  "journal_entry_id": "je_abc123xyz789",
  "total": 1000,
  "split": {
    "platform": 200,
    "expert": 300,
    "ai_compute": 150,
    "developer": 150,
    "community_fund": 100,
    "customer_reward": 100
  },
  "message": "Revenue split executed — 6-way distribution via double-entry ledger"
}
```

---

## Database Schema

### Core Tables

```sql
-- Tenants (organizations)
CREATE TABLE tenants (
  id UUID PRIMARY KEY,
  name TEXT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  tier TEXT DEFAULT 'free' CHECK(tier IN ('free', 'starter', 'pro', 'enterprise')),
  credit_balance INTEGER DEFAULT 5,
  settings JSON
);

-- Journal Entries (double-entry bookkeeping)
CREATE TABLE journal_entries (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  description TEXT,
  entry_type TEXT,  -- 'revenue_share', 'transfer', 'topup', 'withdrawal'
  idempotency_key TEXT UNIQUE,
  metadata TEXT,    -- JSON
  posted_at TEXT DEFAULT (datetime('now'))
);

-- Transaction Lines (debit/credit)
CREATE TABLE transaction_lines (
  id TEXT PRIMARY KEY,
  journal_entry_id TEXT NOT NULL REFERENCES journal_entries(id),
  account_id TEXT NOT NULL REFERENCES ledger_accounts(id),
  amount INTEGER NOT NULL,
  direction INTEGER NOT NULL CHECK (direction IN (-1, 1)),
  created_at TEXT DEFAULT (datetime('now'))
);

-- Ledger Accounts (chart of accounts)
CREATE TABLE ledger_accounts (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  owner_id TEXT,
  code TEXT NOT NULL,
  account_type TEXT NOT NULL,
  balance INTEGER DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now'))
);

-- Treasury (aggregate balances)
CREATE TABLE treasury (
  tenant_id TEXT PRIMARY KEY,
  balance INTEGER DEFAULT 0,
  total_in INTEGER DEFAULT 0,
  total_out INTEGER DEFAULT 0,
  last_updated TEXT DEFAULT (datetime('now'))
);
```

### Account Code Structure

```
Assets (1xxx):
  - customer:{stakeholder_id}        Customer credit balance
  - {stakeholder_id}:rewards         Customer reward credits
  - platform:treasury                Platform operating account

Revenue (2xxx):
  - revenue:platform                 Platform revenue
  - revenue:expert                   Expert/Partner revenue
  - revenue:developer                Developer revenue

Expenses (3xxx):
  - expense:ai_compute               LLM API costs

Equity (4xxx):
  - treasury:community               Community fund pool
```

---

## Security Architecture

### Defense in Depth

```
┌─────────────────────────────────────────────────────────────┐
│  LAYER 1: NETWORK SECURITY                                  │
│  • WAF (OWASP Top 10) • DDoS (L3/L4/L7) • Rate Limiting    │
├─────────────────────────────────────────────────────────────┤
│  LAYER 2: APPLICATION SECURITY                              │
│  • JWT/API Key Auth • RBAC • Input Validation (Zod)        │
├─────────────────────────────────────────────────────────────┤
│  LAYER 3: DATA SECURITY                                     │
│  • TLS 1.3 • AES-256 • HMAC-SHA256                         │
├─────────────────────────────────────────────────────────────┤
│  LAYER 4: OPERATIONAL SECURITY                              │
│  • Audit Logging • SIEM • Backup & DR                      │
└─────────────────────────────────────────────────────────────┘
```

### Authentication Flow

```
Client → API Gateway → RaaS Gateway → D1/KV (Auth)
   │           │              │            │
   │ 1. API Key│              │            │
   │──────────▶│              │            │
   │           │ 2. Hash & Lookup           │
   │           │─────────────▶│            │
   │           │              │ 3. Query   │
   │           │              │───────────▶│
   │           │              │ 4. Result  │
   │           │              │◀───────────│
   │           │ 5. Valid + Credits         │
   │           │◀─────────────│            │
   │ 6. OK    │              │            │
   │◀─────────│              │            │
```

### Security Headers

| Header | Value | Purpose |
|--------|-------|---------|
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | HSTS |
| `X-Frame-Options` | `DENY` | Clickjacking protection |
| `X-Content-Type-Options` | `nosniff` | MIME sniffing |
| `Content-Security-Policy` | `default-src 'self'` | XSS prevention |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Referrer control |

---

## Billing & MCU System

### MCU Credit Tiers

| Tier | Credits/Month | Price | Best For |
|------|---------------|-------|----------|
| Free | 5 (one-time) | $0 | Trial/testing |
| Starter | 200 | $49/mo | Small projects |
| Pro | 1,000 | $149/mo | Growing teams |
| Enterprise | Unlimited | $499/mo | Production scale |

### MCU Deduction Rules

1. **Success-only billing**: MCU deducted ONLY after successful mission completion
2. **Rollback on failure**: Failed missions refund 100% MCU
3. **Zero balance handling**: HTTP 402 Payment Required
4. **No negative balance**: Operations blocked at zero

### Webhook Events

| Event | Trigger | Payload |
|-------|---------|---------|
| `revenue.split.completed` | Revenue split executed | `journal_entry_id`, `total`, `split` |
| `ledger.transfer.completed` | Transfer complete | `journal_entry_id`, `from`, `to`, `amount` |
| `funding.round.completed` | QF round calculated | `round_id`, `results`, `matching_pool` |
| `match.request.matched` | Match found | `request_id`, `matches` |

---

## Scaling & Performance

### Auto-Scaling Triggers

| Component | Trigger | Scale Action |
|-----------|---------|--------------|
| Workers | Request volume | Automatic (global edge) |
| D1 | Query volume | Read replicas |
| R2 | Storage volume | Unlimited |
| KV | Cache hits | Automatic |

### Performance Benchmarks

| Operation | p50 | p95 | p99 |
|-----------|-----|-----|-----|
| API Gateway | 25ms | 85ms | 150ms |
| Revenue Split | 180ms | 450ms | 890ms |
| Ledger Transfer | 120ms | 320ms | 650ms |
| QF Calculation | 2.5s | 4.8s | 7.2s |

### Cost Architecture (Monthly)

| Service | Free | Starter | Pro | Enterprise |
|---------|------|---------|-----|------------|
| Workers | $0.50 | $5 | $50 | $200 |
| D1 | $0.50 | $2 | $10 | $50 |
| R2 | $0.20 | $1 | $5 | $20 |
| KV | $0.10 | $0.50 | $2 | $10 |
| **Infra Total** | **$1.30** | **$8.50** | **$67** | **$280** |
| Revenue | $0 | $29 | $199 | $599+ |
| Margin | N/A | 71% | 66% | 53%+ |

---

## Monitoring & Observability

### Metrics Collected

| Category | Metrics | Retention |
|----------|---------|-----------|
| **Performance** | Latency (p50/p95/p99), TTFB | 90 days |
| **Reliability** | Error rate, Success rate, Uptime | 1 year |
| **Usage** | Requests/sec, Credits consumed | 2 years |
| **Business** | MRR, Churn, Expansion | 7 years |

### Alerting Rules

| Alert | Condition | Severity | Channel |
|-------|-----------|----------|---------|
| API Error Rate | >1% for 5 min | P1 | PagerDuty |
| Latency p99 | >1s for 10 min | P2 | Slack |
| Backup Failure | Any failure | P1 | PagerDuty + Phone |
| Credit Balance | Tenant reaches 0 | P3 | Email |
| DDoS Attack | Detected | P1 | PagerDuty + Security |

### Health Check Endpoints

```yaml
GET /health:
  description: Basic health check
  response: { status: "ok", timestamp: "..." }

GET /health/ready:
  description: Readiness probe (all dependencies OK)
  response: { status: "ok", checks: { d1: "ok", kv: "ok", r2: "ok" } }

GET /health/verbose:
  description: Detailed system status
  response: { status: "ok", metrics: {...}, version: "2.1.79" }
```

---

## Appendix: Quick Reference

### Error Codes

| Code | HTTP Status | Description | Retry? |
|------|-------------|-------------|--------|
| `VALIDATION_ERROR` | 400 | Invalid request | No |
| `INSUFFICIENT_CREDITS` | 402 | Balance too low | No |
| `NOT_FOUND` | 404 | Resource not found | No |
| `CONFLICT` | 409 | Duplicate operation | No |
| `DATABASE_ERROR` | 500 | D1 error | Yes (backoff) |
| `SERVICE_UNAVAILABLE` | 503 | D1 not configured | Yes (backoff) |

### Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/v1/revenue/*` | 100 req | 1 minute |
| `/v1/ledger/*` | 500 req | 1 minute |
| `/v1/funding/*` | 50 req | 1 minute |
| `/v1/matching/*` | 100 req | 1 minute |

### Environment Variables

```bash
# Required
MEKONG_API_KEY=sk_live_...
MEKONG_BASE_URL=https://api.mekong.engine
MEKONG_WEBHOOK_SECRET=whsec_...

# Optional
LOG_LEVEL=info  # debug|info|warn|error
ENABLE_METRICS=true
ENABLE_TRACING=true
```

---

**Document Version:** 2.1.79
**Last Updated:** 2026-03-19
**Owner:** Engineering Team
**Review Cycle:** Quarterly

© 2026 AgencyOS. *Confidential — Internal Use Only*
