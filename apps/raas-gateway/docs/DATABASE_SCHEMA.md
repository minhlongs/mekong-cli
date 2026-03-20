# RaaS Gateway Database Schema

## Entity Relationship Diagram

```
┌─────────────┐       ┌─────────────┐
│  tenants    │       │  api_keys   │
├─────────────┤       ├─────────────┤
│ id (PK)     │◄──────│ tenant_id   │
│ name        │       │ key_hash    │
│ email       │       │ name        │
│ tier        │       │ revoked     │
│ active      │       └─────────────┘
│ expires_at  │
│ used_credits│       ┌─────────────┐
└──────┬──────┘       │  missions   │
       │              ├─────────────┤
       │─────────────►│ tenant_id   │
       │              │ goal        │
       │              │ status      │
       │              │ credits_cost│
       │              └─────────────┘
       │
       │              ┌─────────────┐
       │─────────────►│ usage_logs  │
       │              ├─────────────┤
       │              │ tenant_id   │
       │              │ mission_id  │
       │              │ credits_cost│
       │              └─────────────┘
       │
       │              ┌─────────────────────┐
       └─────────────►│ credit_transactions │
                      ├─────────────────────┤
                      │ tenant_id           │
                      │ amount              │
                      │ type                │
                      └─────────────────────┘
```

## Tables

### tenants

Stores tenant organization licenses and credit balances.

| Column | Type | Description |
|--------|------|-------------|
| id | TEXT | UUID primary key |
| name | TEXT | Organization name |
| email | TEXT | Contact email |
| tier | TEXT | starter/pro/enterprise |
| active | INTEGER | 1=active, 0=inactive |
| expires_at | INTEGER | License expiry (epoch ms) |
| used_credits | INTEGER | Credits used this period |
| billing_period_start | INTEGER | Period start (epoch ms) |
| settings | TEXT | JSON settings |

### api_keys

Stores hashed API keys for tenant authentication.

| Column | Type | Description |
|--------|------|-------------|
| id | TEXT | UUID primary key |
| tenant_id | TEXT | FK to tenants |
| key_hash | TEXT | SHA-256 hash of API key |
| name | TEXT | User-friendly name |
| last_used_at | TEXT | Last usage timestamp |
| revoked | INTEGER | 1=revoked, 0=active |
| permissions | TEXT | JSON array of permissions |

### missions

Tracks mission execution state.

| Column | Type | Description |
|--------|------|-------------|
| id | TEXT | UUID primary key |
| tenant_id | TEXT | FK to tenants |
| goal | TEXT | Mission goal description |
| complexity | TEXT | simple/standard/complex |
| status | TEXT | Current state |
| credits_cost | INTEGER | Estimated credit cost |
| project | TEXT | Optional project name |

### usage_logs

Audit trail for credit consumption.

| Column | Type | Description |
|--------|------|-------------|
| id | TEXT | UUID primary key |
| tenant_id | TEXT | FK to tenants |
| mission_id | TEXT | FK to missions |
| credits_cost | INTEGER | Credits consumed |
| timestamp | TEXT | ISO 8601 timestamp |
| success | INTEGER | 1=success, 0=failure |

### credit_transactions

Billing history and credit adjustments.

| Column | Type | Description |
|--------|------|-------------|
| id | TEXT | UUID primary key |
| tenant_id | TEXT | FK to tenants |
| amount | INTEGER | Credit amount (+/-) |
| type | TEXT | purchase/mission/refund/etc |
| description | TEXT | Human-readable description |
| metadata | TEXT | JSON (Polar order ID, etc) |

## Indexes

| Table | Index | Purpose |
|-------|-------|---------|
| tenants | idx_tenants_email | Look up by email |
| tenants | idx_tenants_active | Filter active tenants |
| api_keys | idx_api_keys_hash | Look up by key hash |
| api_keys | idx_api_keys_tenant | Get tenant's keys |
| api_keys | idx_api_keys_active | Filter non-revoked keys |
| missions | idx_missions_tenant | Get tenant's missions |
| missions | idx_missions_status | Filter by status |
| missions | idx_missions_pending | Get queued/executing |
| usage_logs | idx_usage_logs_tenant | Tenant usage history |
| usage_logs | idx_usage_logs_mission | Mission usage |
| credit_transactions | idx_transactions_tenant | Tenant billing history |
| credit_transactions | idx_transactions_purchase | Filter purchases |

## Migrations

Migrations are located in `migrations/` and applied via:

```bash
# Local
npx wrangler d1 migrations apply mekong-raas-db --local

# Production
npx wrangler d1 migrations apply mekong-raas-db --remote
```
