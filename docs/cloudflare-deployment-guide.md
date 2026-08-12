# Cloudflare Workers Deployment - Complete Setup Guide

This guide provides step-by-step instructions to deploy all Mekong CLI components to Cloudflare.

## Architecture Overview

```
Cloudflare Deployment
├── Dashboard (Next.js) → Cloudflare Pages
│   └── Project: mekong-ide
│   └── URL: https://ide.mekongmind.com
├── API Gateway → Cloudflare Workers
│   └── Worker: mekong-api
│   └── URL: https://mekong-api.{account-id}.workers.dev
├── Mekong Engine → Cloudflare Workers
│   └── Worker: mekong-engine
└── Zalo Parser → Cloudflare Workers
    └── Worker: zalo-parser
```

## Prerequisites

1. **Cloudflare Account** - Sign up at https://cloudflare.com
2. **Node.js 18+** - `node --version`
3. **pnpm** - `npm install -g pnpm@9.15.0`
4. **Wrangler CLI** - `npm install -g wrangler`

## Quick Start (Automated)

Run the complete setup script:

```bash
cd ~/mekong-cli
./scripts/setup-cloudflare-complete.sh
```

This script will:
- ✓ Create D1 databases (mekong-sessions, mekong-audit, mekong-d1)
- ✓ Create KV namespaces (RATE_LIMIT_KV, CACHE_KV)
- ✓ Apply database migrations
- ✓ Update all wrangler.toml files with real IDs
- ✓ Set required secrets from .env files
- ✓ Validate all configurations

**Note:** You must be logged in to Cloudflare first (`wrangler login`) and have appropriate permissions to create resources.

## Manual Setup (If Automated Fails)

### Step 1: Create D1 Databases

```bash
# Create databases
wrangler d1 create mekong-sessions
wrangler d1 create mekong-audit
wrangler d1 create mekong-d1

# Copy the database IDs from the output
```

Update `apps/api/wrangler.toml`:
```toml
[[d1_databases]]
binding = "SESSIONS_DB"
database_name = "mekong-sessions"
database_id = "paste-sessions-db-id-here"
migrations_dir = "migrations/sessions"

[[d1_databases]]
binding = "AUDIT_DB"
database_name = "mekong-audit"
database_id = "paste-audit-db-id-here"
migrations_dir = "migrations/audit"
```

Update `packages/zalo-parser/wrangler.toml`:
```toml
[[d1_databases]]
binding = "DB"
database_name = "mekong-d1"
database_id = "paste-zalo-db-id-here"
migrations_dir = "migrations"
```

### Step 2: Create KV Namespaces

```bash
# Create namespaces
wrangler kv:namespace create RATE_LIMIT_KV
wrangler kv:namespace create CACHE_KV

# Copy the namespace IDs from the output
```

Update `apps/api/wrangler.toml`:
```toml
[[kv_namespaces]]
binding = "RATE_LIMIT_KV"
id = "paste-rate-limit-kv-id-here"

[[kv_namespaces]]
binding = "CACHE_KV"
id = "paste-cache-kv-id-here"
```

Note: `packages/mekong-engine/wrangler.toml` already has KV configured with ID `982a12a5ea414244988a51d743eb14e7`.

### Step 3: Apply Database Migrations

```bash
# For API worker databases
cd apps/api
wrangler d1 execute mekong-sessions --file=migrations/sessions/001_initial.sql
wrangler d1 execute mekong-audit --file=migrations/audit/001_initial.sql

# For other workers (if they have migrations)
cd packages/mekong-engine
wrangler d1 execute mekong-db --file=migrations/001_initial.sql 2>/dev/null || true

cd packages/zalo-parser
wrangler d1 execute mekong-d1 --file=migrations/001_initial.sql 2>/dev/null || true
```

### Step 4: Set Secrets

For **API Worker** (`apps/api`):
```bash
cd apps/api

# Required
WEBHOOK_SECRET=$(openssl rand -hex 32)
wrangler secret put WEBHOOK_SECRET <<< "$WEBHOOK_SECRET"

# Optional (if using)
wrangler secret put API_KEY
```

For **Zalo Parser** (`packages/zalo-parser`):
```bash
cd packages/zalo-parser

# Required if using Zalo integration
ZALO_OA_SECRET_KEY="your-zalo-secret"
wrangler secret put ZALO_OA_SECRET_KEY <<< "$ZALO_OA_SECRET_KEY"
```

For **Mekong Engine** (`packages/mekong-engine`):
```bash
cd packages/mekong-engine

# Optional secrets
wrangler secret put LLM_API_KEY
wrangler secret put SERVICE_TOKEN
wrangler secret put POLAR_WEBHOOK_SECRET
```

### Step 5: Validate Configuration

```bash
./scripts/validate-cloudflare-deploy.sh
```

All checks should pass with green checkmarks.

## Deployment

### Deploy Everything

```bash
# From project root
pnpm run deploy:all
```

This will deploy:
1. Dashboard → Cloudflare Pages (project: mekong-ide)
2. API Gateway → Cloudflare Workers (worker: mekong-api)
3. Mekong Engine → Cloudflare Workers (worker: mekong-engine)
4. Zalo Parser → Cloudflare Workers (worker: zalo-parser)

### Deploy Individual Components

```bash
# Dashboard only
pnpm run deploy:dashboard

# API only
pnpm run deploy:api

# Staging (API only)
cd apps/api && npm run deploy:staging
```

### CI/CD

Push to `main` branch triggers automatic deployment via GitHub Actions.

Workflow: `.github/workflows/deploy-cf.yml`

**Required GitHub Secrets:**
- `CF_API_TOKEN` - Cloudflare API token (with Workers and Pages edit permissions)
- `CF_ACCOUNT_ID` - Your Cloudflare account ID

## Verification

### Health Checks

```bash
# Dashboard
curl -sI https://ide.mekongmind.com | head -1
# Expect: HTTP/2 200

# API Worker
ACCOUNT_ID=$(grep -o 'account_id = "[^"]*"' apps/api/wrangler.toml | cut -d'"' -f2)
curl https://mekong-api.${ACCOUNT_ID}.workers.dev/health | jq .
```

Expected API health response:
```json
{
  "status": "healthy",
  "service": "mekong-api-gateway",
  "environment": "production",
  "timestamp": "2026-06-20T...",
  "version": "6.0.0",
  "services": {
    "rate-limit-kv": "connected",
    "cache-kv": "connected",
    "sessions-db": "connected",
    "audit-db": "connected",
    "ai-binding": "connected"
  },
  "uptime": 12345
}
```

### View Logs

```bash
# Tail API worker logs
wrangler tail mekong-api

# Tail other workers
wrangler tail mekong-engine
wrangler tail zalo-parser
```

### Query Audit Logs

```bash
# Get recent request logs
wrangler d1 execute mekong-audit \
  --command "SELECT * FROM request_logs ORDER BY timestamp DESC LIMIT 10"

# Get payment events
wrangler d1 execute mekong-audit \
  --command "SELECT * FROM payment_events WHERE user_id = 'your-user-id'"
```

## Configuration Reference

### API Worker Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `ENVIRONMENT` | `production` or `staging` | Yes | `production` |
| `BACKEND_API_URL` | Backend service URL | Yes | `https://api.mekong-os.com` |
| `WEBHOOK_SECRET` | HMAC secret for webhooks | Yes | (secret) |
| `RATE_LIMIT_KV` | KV namespace binding | Auto | - |
| `CACHE_KV` | KV namespace binding | Auto | - |
| `SESSIONS_DB` | D1 database binding | Auto | - |
| `AUDIT_DB` | D1 database binding | Auto | - |
| `AI` | AI binding | Auto | - |

### Database Schemas

**Sessions DB** (`mekong-sessions`):
```sql
CREATE TABLE sessions (
  id TEXT PRIMARY KEY,
  data TEXT NOT NULL,
  created_at TEXT NOT NULL,
  expires_at TEXT NOT NULL
);
CREATE INDEX idx_sessions_expires ON sessions(expires_at);
```

**Audit DB** (`mekong-audit`):
```sql
CREATE TABLE request_logs (
  id TEXT PRIMARY KEY,
  path TEXT NOT NULL,
  method TEXT NOT NULL,
  status INTEGER NOT NULL,
  timestamp TEXT NOT NULL,
  user_agent TEXT,
  ip TEXT
);
CREATE INDEX idx_request_logs_timestamp ON request_logs(timestamp);

CREATE TABLE payment_events (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  amount REAL NOT NULL,
  currency TEXT NOT NULL,
  status TEXT NOT NULL,
  raw_payload TEXT NOT NULL,
  received_at TEXT NOT NULL
);

CREATE TABLE user_events (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  email TEXT,
  event_type TEXT NOT NULL,
  raw_payload TEXT NOT NULL,
  received_at TEXT NOT NULL
);
```

## Troubleshooting

### Validation Errors

```bash
# Check wrangler config syntax
npx wrangler validate --config apps/api/wrangler.toml
npx wrangler validate --config apps/dashboard/wrangler.toml
```

### Database Connection Issues

```bash
# Check database info
wrangler d1 info mekong-sessions
wrangler d1 info mekong-audit

# Test query
wrangler d1 execute mekong-sessions --command "SELECT COUNT(*) FROM sessions"
```

### Worker Fails to Deploy

Common causes:
1. **Missing account_id** - Check `account_id` in wrangler.toml
2. **Invalid database ID** - Ensure UUID format is correct
3. **Insufficient permissions** - API token needs Workers and Pages edit rights
4. **Build errors** - Run `pnpm run build` locally first

### Worker Fails to Start

```bash
# Check logs
wrangler tail mekong-api --since 1h

# Test locally
cd apps/api && pnpm dev
```

### Placeholder IDs Not Being Replaced

The automated setup script (`setup-cloudflare-complete.sh`) only updates IDs with placeholder pattern:
- `replace_with_*_id`
- `00000000-0000-0000-0000-000000000000`

If your wrangler.toml uses different placeholders, manually replace them or update the file to use the standard placeholders before running the script.

## Cost Optimization

Cloudflare free tier limits (sufficient for early stage):
- **Workers**: 100K requests/day
- **D1**: 5GB storage, 1K reads/writes/day
- **KV**: 100K reads/writes/day
- **R2**: 10GB storage, 100K Class A operations/month

Best practices:
1. **Cache aggressively** - Use KV for frequently accessed data with TTL
2. **Batch D1 writes** - Queue writes and flush periodically
3. **Set rate limits** - Prevent abuse (already configured: 100 req/min per IP)
4. **Monitor usage** - `wrangler metrics` and Cloudflare dashboard

## Next Steps After Setup

1. ✅ Run `./scripts/setup-cloudflare-complete.sh`
2. ✅ Verify with `./scripts/validate-cloudflare-deploy.sh`
3. ✅ Deploy to staging: `cd apps/api && npm run deploy:staging`
4. ✅ Test staging endpoints
5. ✅ Deploy to production: `pnpm run deploy:all`
6. ✅ Configure custom domain for dashboard (ide.mekongmind.com)
7. ✅ Set up monitoring and alerts
8. ✅ Review costs in Cloudflare dashboard

## Files Reference

| File | Purpose |
|------|---------|
| `apps/api/wrangler.toml` | API Worker config |
| `apps/dashboard/wrangler.toml` | Dashboard Pages config |
| `packages/mekong-engine/wrangler.toml` | Engine Worker config |
| `packages/zalo-parser/wrangler.toml` | Zalo Parser config |
| `.github/workflows/deploy-cf.yml` | CI/CD pipeline |
| `scripts/setup-cloudflare-complete.sh` | Automated setup |
| `scripts/validate-cloudflare-deploy.sh` | Configuration validator |
| `scripts/deploy-dashboard.sh` | Dashboard deploy helper |
| `CLOUD_FLARE_DEPLOYMENT.md` | Quick reference |
| `GO_LIVE_PLAYBOOK.md` | Complete go-live checklist |

## Support

- **Documentation**: See `CLOUD_FLARE_DEPLOYMENT.md` and `GO_LIVE_PLAYBOOK.md`
- **Issues**: https://github.com/longtho638-jpg/mekong-cli/issues
- **Cloudflare Docs**: https://developers.cloudflare.com/workers/
