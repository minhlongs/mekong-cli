# Mekong CLI — Operator Quick Reference

**Emergency Contacts** | Cloudflare Support | polar.sh support | OpenRouter support

---

## Health Status (Check First)

```bash
# All-in-one health check
curl -s https://api.cashclaw.cc/health | jq .status
curl -sI https://ide.mekongmind.com | head -1
# Expected: {"status":"healthy"} and HTTP/2 200
```

---

## Deployments

| Component | Command | Verify |
|-----------|---------|--------|
| Dashboard | `./scripts/deploy-dashboard.sh` | `curl -sI https://ide.mekongmind.com` |
| API Worker | `cd apps/api && npm run deploy` | `curl https://api.cashclaw.cc/health` |
| Staging | `npm run deploy:staging` | `curl https://staging-api.../health` |

---

## Logs

```bash
# Live logs
wrangler tail mekong-api

# Past logs (last 30 min)
wrangler tail mekong-api --since 30m

# Database query logs
wrangler d1 execute mekong-audit --command="SELECT * FROM request_logs WHERE status_code >= 500 ORDER BY timestamp DESC LIMIT 20;"
```

---

## Database Operations

```bash
# Backup
wrangler d1 export mekong-sessions --output=backup.sql
wrangler d1 export mekong-audit --output=backup-audit.sql

# Restore (WARNING: replaces data)
wrangler d1 restore mekong-sessions --file=backup.sql

# Query
wrangler d1 execute mekong-sessions --command="SELECT count(*) FROM sessions;"
wrangler d1 execute mekong-audit --command="SELECT * FROM request_logs LIMIT 10;"
```

---

## KV Namespace

```bash
# List keys
wrangler kv:key list RATE_LIMIT_KV --limit=100

# Get value
wrangler kv:key get RATE_LIMIT_KV "key-name"

# Delete key
wrangler kv:key delete RATE_LIMIT_KV "key-name"

# Flush all (DESTRUCTIVE)
wrangler kv:key list RATE_LIMIT_KV --format=json | jq -r '.[].name' | xargs -I {} wrangler kv:key delete RATE_LIMIT_KV {}
```

---

## Rollbacks (EMERGENCY ONLY)

```bash
# Dashboard (revert last commit)
git revert <sha> && ./scripts/deploy-dashboard.sh

# API Worker
git revert <sha> && cd apps/api && npm run deploy

# Full rollback script (if exists)
./scripts/full-rollback.sh <good-commit-sha>
```

---

## Monitoring Commands

```bash
# API metrics
wrangler metrics mekong-api --since 1h

# D1 database info
wrangler d1 info mekong-sessions
wrangler d1 info mekong-audit

# Pages deployments
npx wrangler pages deployment list mekong-ide --limit=5
```

---

## Secrets

```bash
# Set/update secret
cd apps/api
wrangler secret put WEBHOOK_SECRET
# (paste secret, press Ctrl+D)

# List secrets (names only, not values)
wrangler secret list
```

---

## Common Issues & Quick Fixes

| Issue | Quick Fix |
|-------|-----------|
| 5xx errors | Check `wrangler tail mekong-api`, rollback if recent deploy |
| Dashboard not loading | Check Pages deployments, verify custom domain |
| Webhook not firing | Verify Polar webhook URL, check secret |
| High costs | Check OpenRouter usage, implement caching |
| Rate limits hit | Review `RATE_LIMIT_KV` entries, adjust thresholds |
| DB quota exceeded | Upgrade Cloudflare plan or reduce queries |

---

## Important URLs

| Resource | URL |
|----------|-----|
| Dashboard (prod) | https://ide.mekongmind.com |
| API Gateway | https://api.cashclaw.cc |
| API Health | https://api.cashclaw.cc/health |
| Polar Dashboard | https://polar.sh/dashboard |
| Cloudflare Dashboard | https://dash.cloudflare.com |
| OpenRouter Usage | https://openrouter.ai/usage |

---

## Files to Know

```
apps/
├── dashboard/          # Next.js frontend
│   └── wrangler.toml   # Pages config
└── api/                # API Worker
    └── wrangler.toml   # Worker config

docs/
├── operator-runbook.md     # This runbook (detailed)
├── deployment-guide.md     # Deployment instructions
├── rollback-procedures.md  # Detailed rollback steps
└── troubleshooting.md      # Full troubleshooting

scripts/
├── deploy-dashboard.sh     # Dashboard deploy script
├── backup-d1-databases.sh  # Database backup
└── health-check.sh         # Health monitoring
```

---

## Escalation Path

1. **Self-service**: Check troubleshooting guide, run diagnostics
2. **Team lead**: If unresolved after 15 minutes of investigation
3. **All-hands**: P0/P1 incidents (service down, data loss)
4. **Customer notice**: If SLA impact >30 minutes

---

**Keep this card handy. Full details in `docs/operator-runbook.md`**
