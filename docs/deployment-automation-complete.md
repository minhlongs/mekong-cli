# Deployment Automation - Mekong IDE

Complete deployment automation for Cloudflare Workers-based infrastructure.

## Quick Start

```bash
# Full production deployment (all components)
make deploy

# Deploy to staging
make deploy-staging

# Deploy individual components
make deploy-dashboard    # Dashboard to Cloudflare Pages
make deploy-api          # API Worker to Cloudflare Workers
make deploy-workers      # Other workers (mekong-engine, zalo-parser)
```

## Scripts

### `scripts/deploy-all.sh`
Unified deployment orchestrator that deploys all components in the correct order.

**Features:**
- Deploys dashboard, API, and workers
- Supports staging and production environments
- Optional parallel deployment for independent components
- Dry-run mode for preview
- Health checks after deployment
- Color-coded output

**Usage:**
```bash
./scripts/deploy-all.sh                    # Deploy everything to production
./scripts/deploy-all.sh --staging         # Deploy to staging
./scripts/deploy-all.sh --dashboard       # Deploy dashboard only
./scripts/deploy-all.sh --api            # Deploy API only
./scripts/deploy-all.sh --workers        # Deploy workers only
./scripts/deploy-all.sh --dry-run        # Preview without deploying
./scripts/deploy-all.sh --parallel       # Deploy dashboard + API in parallel
```

### `scripts/deploy-dashboard.sh`
Deploy the Next.js dashboard to Cloudflare Pages.

**Usage:**
```bash
./scripts/deploy-dashboard.sh              # Production
./scripts/deploy-dashboard.sh --preview   # Preview branch
```

**What it does:**
1. Installs dependencies (if needed)
2. Builds the Next.js app
3. Deploys to Cloudflare Pages project `mekong-ide`
4. Configures custom domain `ide.mekongmind.com`

### `scripts/deploy-api.sh`
Deploy the API Gateway worker to Cloudflare Workers.

**Features:**
- Runs database migrations before deploy
- Builds TypeScript code
- Deploys with environment-specific configuration
- Post-deployment health checks
- Rollback guidance on failure

**Usage:**
```bash
./scripts/deploy-api.sh                   # Deploy to production
./scripts/deploy-api.sh --staging        # Deploy to staging
./scripts/deploy-api.sh --dry-run        # Preview only
./scripts/deploy-api.sh --no-wait        # Skip health check
```

**What it does:**
1. Checks prerequisites (wrangler, Node.js)
2. Runs D1 database migrations (sessions, audit)
3. Builds TypeScript code
4. Deploys with `wrangler deploy`
5. Waits for health check endpoint to return 200
6. Displays deployment summary

**Health Check:**
- Production: `https://api.cashclaw.cc/healthz`
- Staging: `https://mekong-api-staging.workers.dev/healthz`

### `scripts/deploy-workers.sh`
Deploy auxiliary workers (mekong-engine, zalo-parser).

**Usage:**
```bash
./scripts/deploy-workers.sh               # Production
./scripts/deploy-workers.sh --staging    # Staging
./scripts/deploy-workers.sh --dry-run    # Preview
```

**Workers deployed:**
- `packages/mekong-engine` - PEV orchestration engine
- `packages/zalo-parser` - Zalo messaging parser

## Prerequisites

### One-Time Setup

1. **Install Wrangler CLI**
   ```bash
   npm install -g wrangler
   ```

2. **Login to Cloudflare**
   ```bash
   wrangler login
   ```

3. **Create Cloudflare Resources**
   ```bash
   # D1 Databases
   wrangler d1 create mekong-sessions
   wrangler d1 create mekong-audit

   # KV Namespaces
   wrangler kv:namespace create RATE_LIMIT_KV
   wrangler kv:namespace create CACHE_KV

   # Get account ID from Cloudflare Dashboard
   ```

4. **Update Configuration**
   - Edit `apps/api/wrangler.toml` with actual database IDs and KV IDs
   - Set secrets: `wrangler secret put WEBHOOK_SECRET`

5. **Test Locally**
   ```bash
   cd apps/dashboard && npm run dev
   cd apps/api && npm run dev
   ```

### Environment Variables

Optional environment variables:
- `CF_API_TOKEN` - Cloudflare API token (falls back to wrangler auth)
- `CF_ACCOUNT_ID` - Cloudflare account ID (falls back to wrangler.toml)
- `SKIP_DASHBOARD` - Set to "1" to skip dashboard in `deploy-all.sh`
- `SKIP_API` - Set to "1" to skip API in `deploy-all.sh`
- `SKIP_WORKERS` - Set to "1" to skip workers in `deploy-all.sh`

## CI/CD Integration

GitHub Actions workflows are already configured:

- **`.github/workflows/deploy-cf.yml`** - Deploys dashboard, API, and workers on push to `main`
- **`.github/workflows/deploy-dashboard.yml`** - Dedicated dashboard deployment

These workflows:
1. Run type checking and linting
2. Build the applications
3. Deploy to Cloudflare
4. Perform health checks
5. Post deployment status as PR comments

## Rollback Procedures

If a deployment introduces issues:

### API Worker Rollback
```bash
make rollback-api
# or manually:
./scripts/quick-rollback-api.sh HEAD~1
```

### Full System Rollback
```bash
make rollback-full
# or manually:
./scripts/full-rollback.sh HEAD~1
```

### Cloudflare Pages Rollback (Dashboard)
1. Go to Cloudflare Dashboard → Pages → mekong-ide → Deployments
2. Click "..." on previous successful deployment → "Set as live"

### Cloudflare Workers Rollback
```bash
wrangler rollback --env production
```

See `docs/rollback-procedures.md` for detailed procedures.

## Verification

After deployment, verify everything is working:

```bash
# 1. Check dashboard
curl -s -o /dev/null -w "%{http_code}" https://ide.mekongmind.com || echo "Dashboard not responding"

# 2. Check API health
curl https://api.cashclaw.cc/health || echo "API not responding"

# 3. View logs
wrangler tail mekong-api
wrangler tail mekong-engine
wrangler tail zalo-parser

# 4. Check Cloudflare dashboard
# https://dash.cloudflare.com/workers/services
```

## Troubleshooting

### Deployment fails with "wrangler not found"
```bash
npm install -g wrangler
wrangler login
```

### Health check timeout
- Worker may still be propagating; wait 30-60 seconds
- Check logs: `wrangler tail mekong-api`
- Verify database connections are configured correctly

### Database migration fails
```bash
# Check database exists
wrangler d1 list

# Manually apply migration
cd apps/api
wrangler d1 execute mekong-sessions --file=migrations/sessions/001_initial.sql
```

### Build fails with missing dependencies
```bash
cd apps/api && npm ci
cd apps/dashboard && npm ci
```

### "Account ID not found"
Update `account_id` in `apps/api/wrangler.toml`:
```toml
account_id = "your-account-id"
```

Find account ID in Cloudflare Dashboard → Overview → Account ID.

## Architecture

```
Cloudflare Edge Deployment
├── Dashboard (Next.js) → Cloudflare Pages
│   └── apps/dashboard/
│       └── wrangler.toml (pages config)
├── API Gateway → Cloudflare Workers
│   └── apps/api/
│       ├── src/index.ts (main worker)
│       ├── migrations/ (D1 schemas)
│       └── wrangler.toml (worker config)
├── Mekong Engine → Cloudflare Workers
│   └── packages/mekong-engine/
└── Zalo Parser → Cloudflare Workers
    └── packages/zalo-parser/
```

## Environment-Specific Configuration

### Production
- API: `https://api.cashclaw.cc`
- Dashboard: `https://ide.mekongmind.com`
- Workers: Direct `wrangler deploy` (no env flag)

### Staging
- API: `https://mekong-api-staging.workers.dev`
- Dashboard: Preview branch via `--preview` flag
- Workers: `wrangler deploy --env staging` (if supported)

Configure staging environment in `wrangler.toml` under `[env.staging]`.

## Monitoring

### Cloudflare Dashboard
- Workers: https://dash.cloudflare.com/workers/services
- Pages: https://dash.cloudflare.com/pages
- D1 Databases: https://dash.cloudflare.com/d1
- KV: https://dash.cloudflare.com/kv

### Logs
```bash
# Tail worker logs in real-time
wrangler tail mekong-api
wrangler tail mekong-engine --env staging
```

### Metrics
- Request count, error rate, latency available in Cloudflare dashboard
- OpenTelemetry instrumentation (see `observability/`)

## Cost Optimization

Cloudflare free tier limits:
- Workers: 100K requests/day
- D1: 5GB storage, 1K reads/writes/day
- KV: 100K reads/writes/day
- Pages: Unlimited requests, 500 builds/month

Best practices:
1. Cache responses in KV with appropriate TTL
2. Batch D1 writes
3. Implement rate limiting (already configured)
4. Monitor usage in Cloudflare dashboard
5. Set up alerts for quota warnings

## Security

### Secrets Management
All secrets stored via `wrangler secret put`:
```bash
cd apps/api
wrangler secret put WEBHOOK_SECRET
wrangler secret put JWT_SECRET  # if used
```

### Never commit:
- `.env` files with secrets
- `wrangler.toml` with real database IDs (use placeholders in repo)
- API tokens or keys

### CI/CD Secrets
GitHub Actions uses:
- `CF_API_TOKEN` - Cloudflare API token
- `CF_ACCOUNT_ID` - Account ID

Add in repo Settings → Secrets and variables → Actions.

## Support

- **Documentation**: See `docs/deployment-guide.md`
- **Runbooks**: See `docs/runbooks/`
- **Issues**: https://github.com/longtho638-jpg/mekong-cli/issues
- **Cloudflare Docs**: https://developers.cloudflare.com/workers/

## References

- [Cloudflare Workers Documentation](https://developers.cloudflare.com/workers/)
- [Wrangler CLI Reference](https://developers.cloudflare.com/workers/wrangler/)
- [D1 Database Guide](https://developers.cloudflare.com/d1/)
- [KV Storage](https://developers.cloudflare.com/kv/)
