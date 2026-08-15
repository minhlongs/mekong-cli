# Mekong CLI — Rollback Procedures

> Emergency procedures for undoing deployments and restoring service
> Last updated: 2026-06-20 | Version: 1.0

## Overview

This document describes how to rollback Mekong CLI infrastructure components
deployed on Cloudflare (Pages, Workers, D1, KV). Use these procedures when a
deployment causes:

- Service outages (5xx errors, timeouts)
- Data corruption or loss
- Security incidents
- Severe performance degradation
- Failed health checks

## Rollback Decision Tree

```
Deployment Issue Detected?
         │
         ▼
   ┌─────────────┐
   │ Is it a     │
   │ code bug?   │────Yes────► Fix-forward: patch + hotfix deploy
   └──────┬──────┘
          │ No
          ▼
   ┌─────────────┐
   │ Is data     │
   │ corrupted?  │────Yes────► DB/KV restore (full rollback)
   └──────┬──────┘
          │ No
          ▼
   ┌─────────────┐
   │ Is service  │
   │ down?       │────Yes────► Immediate rollback to last known good
   └──────┬──────┘
          │ No
          ▼
   ┌─────────────┐
   │ Is it       │
   │ severe?     │────Yes────► Rollback (customer impact >10%)
   └──────┬──────┘
          │ No
          ▼
   ┌─────────────┐
   │ Monitor +   │
   │ fix-forward │
   └─────────────┘
```

**Rule of thumb:** If health check fails for >2 minutes or paying customers are
affected, rollback immediately.

## Pre-Rollback Checklist

Before initiating any rollback, verify:

- [ ] Health check endpoint confirms failure: `curl https://api.cashclaw.cc/health`
- [ ] Dashboard is inaccessible or broken: `curl -sI https://ide.mekongmind.com`
- [ ] Recent deployment identified: `git log --oneline -5`
- [ ] Backup exists (for DB/KV): See backup verification section
- [ ] Stakeholders notified (if in production hours)
- [ ] Rollback approval obtained (for production, unless emergency)

## 1. Dashboard Rollback (Cloudflare Pages)

The dashboard (`apps/dashboard`) is deployed to Cloudflare Pages project
`mekong-ide` at `ide.mekongmind.com`.

### Method A: Git Revert + Redeploy (Recommended)

```bash
# 1. Identify bad commit
cd ~/mekong-cli
git log --oneline apps/dashboard | head -10

# 2. Revert the commit (creates new commit that undoes changes)
git revert <bad-commit-sha> -m 1
#   -m 1 for merge commits; omit for linear history

# 3. Push the revert
git push origin main

# 4. Redeploy (CI/CD will auto-deploy, or manual)
./scripts/deploy-dashboard.sh

# 5. Verify
curl -sI https://ide.mekongmind.com | head -1
# expect: HTTP/2 200
```

**Rollback time:** 3-5 minutes

### Method B: Branch Rollback (If using preview branches)

Cloudflare Pages keeps previous deployments. To promote a previous build:

```bash
# List recent deployments
npx wrangler pages deployment list mekong-ide --limit=20

# Promote a previous deployment (use deployment_id from list)
npx wrangler pages deployment promote <deployment-id> --project-name=mekong-ide
```

**Limitation:** Only works if previous deployment still in Pages retention
(default: 90 days).

### Emergency Rollback (No Git Access)

If you need immediate rollback but cannot push:

```bash
# 1. Checkout known good commit locally
git checkout <good-commit-sha> -- apps/dashboard/

# 2. Build and deploy manually
cd apps/dashboard
npm run build
npx wrangler pages deploy .next/static --project-name=mekong-ide --branch=production

# 3. Return to main branch
cd ~/mekong-cli
git checkout main
```

**Rollback time:** 5-8 minutes

## 2. API Worker Rollback (Cloudflare Workers)

The API Gateway (`apps/api`) is deployed as Cloudflare Worker `mekong-api`.

### Method A: Git Revert + Deploy

```bash
# 1. Identify bad commit
git log --oneline apps/api | head -10

# 2. Revert
git revert <bad-commit-sha>
git push origin main

# 3. Deploy (CI/CD auto-deploys, or manual)
cd apps/api
npm run deploy

# 4. Verify
curl https://api.cashclaw.cc/health
# expect: {"status":"ok",...}
```

**Rollback time:** 2-4 minutes

### Method B: Manual Deploy from Previous Tag

```bash
# 1. Find last good git tag
git tag --list | grep '^v' | tail -10
git show <tag-name> --stat

# 2. Deploy specific commit
cd apps/api
npx wrangler deploy --commit-dirty=false --no-bundle

# Or manually specify:
git checkout <good-commit-sha>
npx wrangler deploy
git checkout main
```

### Method C: Quick Rollback Script

```bash
#!/usr/bin/env bash
# scripts/quick-rollback-api.sh
# Usage: ./scripts/quick-rollback-api.sh <commit-sha>

set -euo pipefail

GOOD_COMMIT="${1:-}"
if [[ -z "$GOOD_COMMIT" ]]; then
    echo "Usage: $0 <good-commit-sha>"
    echo "Recent commits:"
    git log --oneline apps/api | head -5
    exit 1
fi

cd ~/mekong-cli

echo "Rolling back API Worker to $GOOD_COMMIT..."
git checkout "$GOOD_COMMIT" -- apps/api/

cd apps/api
npm run deploy

cd ~/mekong-cli
git checkout main -- apps/api/

echo "✅ API Worker rolled back"
echo "Verify: curl https://api.cashclaw.cc/health"
```

Save as `scripts/quick-rollback-api.sh` and make executable.

## 3. Database Rollback (D1)

D1 (Cloudflare's SQLite-based database) does not support traditional
transactional rollback. To restore data:

### Option A: Export/Restore (Recommended for Regular Backups)

**Prerequisites:** Regular D1 exports must be configured (see backup procedures).

```bash
# 1. Export current state (for safety before restore)
wrangler d1 export mekong-sessions --output=backups/sessions-pre-rollback-$(date +%Y%m%d-%H%M%S).sql
wrangler d1 export mekong-audit --output=backups/audit-pre-rollback-$(date +%Y%m%d-%H%M%S).sql

# 2. Restore from backup
wrangler d1 restore mekong-sessions --file=backups/sessions-YYYYMMDD-HHMMSS.sql
wrangler d1 restore mekong-audit --file=backups/audit-YYYYMMDD-HHMMSS.sql

# 3. Verify
wrangler d1 execute mekong-sessions --command="SELECT count(*) FROM sessions;"
wrangler d1 execute mekong-audit --command="SELECT count(*) FROM request_logs;"
```

**Important:** Restore replaces the entire database. All data after the backup
timestamp will be lost.

### Option B: Point-in-Time Recovery (Not Available)

D1 does not currently support point-in-time recovery. You must restore from a
specific export file.

### Option C: Swap Database (For Zero-Downtime)

If you have a backup database ready:

```bash
# 1. Create new database from backup
wrangler d1 create mekong-sessions-rollback
wrangler d1 restore mekong-sessions-rollback --file=backups/sessions-good.sql

# 2. Update wrangler.toml to point to new database
#    (requires redeploy to take effect)

# 3. Redeploy with new database ID
#    Cut over is atomic on redeploy.

# 4. After verification, delete old database
wrangler d1 delete mekong-sessions
wrangler d1 rename mekong-sessions-rollback mekong-sessions
```

**Downtime:** ~30 seconds during redeploy

### D1 Backup/Restore Reference

| Command | Purpose |
|---------|---------|
| `wrangler d1 export <db>` | Export database to SQL file |
| `wrangler d1 restore <db> --file=<path>` | Restore database from SQL file |
| `wrangler d1 info <db>` | Show database details |
| `wrangler d1 list` | List all D1 databases |
| `wrangler d1 execute <db> --command="SQL"` | Run query |

## 4. KV Namespace Rollback

KV stores (rate limiting, cache) have no built-in versioning. Restore from
exports if available.

### Export KV Periodically

```bash
# Export all keys (for backup)
wrangler kv:key list RATE_LIMIT_KV --format=json > backups/kv-rate-limit-$(date +%Y%m%d).json
wrangler kv:key list CACHE_KV --format=json > backups/kv-cache-$(date +%Y%m%d).json

# Export all key-value pairs
wrangler kv:key list RATE_LIMIT_KV --result=json | jq -r '.[].name' | while read key; do
    value=$(wrangler kv:key get RATE_LIMIT_KV "$key" --output=json)
    echo "{\"key\":\"$key\",\"value\":$value}" >> backups/kv-rate-limit-full-$(date +%Y%m%d).jsonl
done
```

### Restore KV from Backup

```bash
# Restore from full export (JSONL format)
cat backups/kv-rate-limit-full-YYYYMMDD.jsonl | while read line; do
    key=$(echo "$line" | jq -r .key)
    value=$(echo "$line" | jq -r .value)
    wrangler kv:key put RATE_LIMIT_KV "$key" "$value"
done
```

**Warning:** KV restoration is slow (rate-limited). For cache KV, consider
letting it warm naturally instead of restoring.

## 5. Other Workers Rollback

For `mekong-engine` and `zalo-parser` workers:

```bash
cd ~/mekong-cli

# Mekong Engine
cd packages/mekong-engine
git log --oneline | head -5
git revert <bad-commit>
npm run deploy
cd ~/mekong-cli

# Zalo Parser
cd packages/zalo-parser
git log --oneline | head -5
git revert <bad-commit>
npm run deploy
cd ~/mekong-cli
```

## 6. Full System Rollback

If multiple components are affected:

```bash
#!/usr/bin/env bash
# scripts/full-rollback.sh
# Emergency full system rollback to last known good state

set -euo pipefail

GOOD_COMMIT="${1:-HEAD~1}"  # Default: previous commit

echo "🚨 FULL SYSTEM ROLLBACK"
echo "======================="
echo "Target commit: $GOOD_COMMIT"
echo ""
read -p "Type 'ROLLBACK' to confirm: " CONFIRM
if [[ "$CONFIRM" != "ROLLBACK" ]]; then
    echo "Cancelled"
    exit 0
fi

cd ~/mekong-cli

# 1. Checkout good state for all deployable components
git checkout "$GOOD_COMMIT" -- apps/dashboard/ apps/api/ packages/mekong-engine/ packages/zalo-parser/

# 2. Deploy Dashboard
echo "==> Rolling back Dashboard..."
cd apps/dashboard
npm run build
npx wrangler pages deploy .next/static --project-name=mekong-ide --branch=production
cd ~/mekong-cli

# 3. Deploy API Worker
echo "==> Rolling back API Worker..."
cd apps/api
npm run deploy
cd ~/mekong-cli

# 4. Deploy other workers
echo "==> Rolling back Mekong Engine..."
cd packages/mekong-engine
npm run deploy
cd ~/mekong-cli

echo "==> Rolling back Zalo Parser..."
cd packages/zalo-parser
npm run deploy
cd ~/mekong-cli

# 5. Return to main branch (keep deployed code)
git checkout main -- apps/dashboard/ apps/api/ packages/mekong-engine/ packages/zalo-parser/

echo ""
echo "✅ Full rollback complete"
echo ""
echo "Verification checklist:"
echo "  [ ] Dashboard: https://ide.mekongmind.com"
echo "  [ ] API health: https://api.cashclaw.cc/health"
echo "  [ ] Payment flow: ./scripts/smoke-test-payment.sh"
```

**Rollback time:** 10-15 minutes

## Post-Rollback Verification

After any rollback, verify:

```bash
# 1. Health checks
curl -s https://api.cashclaw.cc/health | jq .
curl -sI https://ide.mekongmind.com | head -1

# 2. Smoke test payment flow
./scripts/smoke-test-payment.sh

# 3. Core endpoints
curl -sH "Authorization: Bearer $TEST_TOKEN" \
  https://api.cashclaw.cc/v1/me/credits | jq .

# 4. Database connectivity
wrangler d1 execute mekong-sessions --command="SELECT 1;"

# 5. Logs for errors
wrangler tail mekong-api --since 5m | grep -i error || echo "No errors"
```

## Rollback Limitations

| Component | Rollback Capability | Limitations |
|-----------|-------------------|-------------|
| Dashboard | Full (git-based) | Must redeploy to revert |
| API Worker | Full (git-based) | No hot rollback; requires deploy |
| D1 Databases | Backup restore only | Point-in-time not available |
| KV Namespaces | Manual key restore | No bulk restore command |
| D1 Migrations | Manual SQL revert | Auto-migration rollback not supported |

### D1 Migration Rollback

If a database migration caused issues:

```bash
# 1. Manually revert SQL changes
# Find the migration file that was applied
cat apps/api/migrations/sessions/002_add_column.sql

# Write inverse SQL:
#   ALTER TABLE sessions DROP COLUMN new_column;
#   (or whatever the migration did)

# 2. Execute manually
wrangler d1 execute mekong-sessions --command="ALTER TABLE sessions DROP COLUMN IF EXISTS new_column;"

# 3. Mark migration as unapplied (if using migration tracking)
# If you have a migrations table, update it:
wrangler d1 execute mekong-sessions --command="DELETE FROM migrations WHERE version='002';"
```

**Note:** Current schema doesn't have a migrations tracking table. Consider
adding one for production safety.

## Automated Backups

### D1 Automated Backup Script

```bash
#!/usr/bin/env bash
# scripts/backup-d1-databases.sh
# Daily backup of D1 databases to R2 or local storage

set -euo pipefail

BACKUP_DIR="/tmp/backups/d1"
R2_BUCKET="mekong-backups"  # Optional: configure R2

mkdir -p "$BACKUP_DIR"

echo "Backing up D1 databases..."

# Sessions DB
wrangler d1 export mekong-sessions --output="$BACKUP_DIR/sessions-$(date +%Y%m%d-%H%M%S).sql"

# Audit DB
wrangler d1 export mekong-audit --output="$BACKUP_DIR/audit-$(date +%Y%m%d-%H%M%S).sql"

# Optional: Upload to R2
if command -v wrangler &>/dev/null && [[ -n "${R2_BUCKET:-}" ]]; then
    for file in "$BACKUP_DIR"/*.sql; do
        wrangler r2 object put "$R2_BUCKET/$(basename "$file")" --file="$file"
    done
fi

# Cleanup old backups (keep 30 days)
find "$BACKUP_DIR" -name "*.sql" -mtime +30 -delete

echo "Backup complete: $(ls -1 $BACKUP_DIR | wc -l) files"
```

Schedule via cron (or GitHub Actions):

```cron
0 2 * * * /path/to/mekong-cli/scripts/backup-d1-databases.sh >> /var/log/mekong-backup.log 2>&1
```

### KV Backup Script

```bash
#!/usr/bin/env bash
# scripts/backup-kv-namespaces.sh

set -euo pipefail

BACKUP_DIR="/tmp/backups/kv/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

echo "Backing up KV namespaces..."

for ns in RATE_LIMIT_KV CACHE_KV; do
    echo "  Exporting $ns..."
    wrangler kv:key list "$ns" --format=json > "$BACKUP_DIR/$ns-keys.json"

    # Export values (respect rate limits)
    jq -r '.[].name' "$BACKUP_DIR/$ns-keys.json" | head -1000 | while read key; do
        value=$(wrangler kv:key get "$ns" "$key" --output=json 2>/dev/null || echo '""')
        echo "{\"k\":\"$key\",\"v\":$value}" >> "$BACKUP_DIR/$ns-full.jsonl"
    done
done

echo "KV backup complete: $BACKUP_DIR"
```

## Rollback Runbooks

### Runbook: Dashboard Deployment Failure

**Symptoms:**
- `npm run build` fails
- Wrangler deploy returns error
- Preview URL shows build error

**Actions:**
1. Check build logs: `cd apps/dashboard && npm run build 2>&1 | tail -50`
2. If code error: fix and re-deploy (not rollback)
3. If deploy infrastructure: rollback via Method A or B
4. Verify: `curl -sI https://ide.mekongmind.com`

### Runbook: API Worker 5xx Errors

**Symptoms:**
- `/health` returns 500
- `wrangler tail` shows exceptions
- Customers report failures

**Actions:**
1. Check worker logs: `wrangler tail mekong-api --since 10m`
2. Identify if recent deploy: `git log --oneline apps/api -1`
3. If yes and logs show code errors: rollback via git revert
4. If database errors: check D1 status, consider DB restore
5. After rollback, verify health: `curl https://api.cashclaw.cc/health`

### Runbook: Database Corruption

**Symptoms:**
- Database queries fail
- Migration errors
- `wrangler d1 execute` returns SQLite errors

**Actions:**
1. Stop accepting new writes (if possible): Update API worker to maintenance mode
2. Export current (corrupted) state for forensics: `wrangler d1 export mekong-sessions`
3. Restore from last known good backup
4. Verify: `wrangler d1 execute mekong-sessions --command="SELECT count(*) FROM sessions;"`
5. Redeploy API worker
6. Monitor for errors

### Runbook: KV Cache Poisoning

**Symptoms:**
- Widespread incorrect responses
- Malformed data in responses
- Cache entries with unexpected values

**Actions:**
1. Flush KV namespace (destructive but fast):
   ```bash
   # KV has no flush; must delete keys individually
   wrangler kv:key list RATE_LIMIT_KV --format=json | jq -r '.[].name' | xargs -I {} wrangler kv:key delete RATE_LIMIT_KV {}
   ```
2. For CACHE_KV, let it warm naturally (cache rebuild)
3. If rate limit KV cleared, rate limits reset (acceptable)
4. Monitor for recurrence

## Emergency Contacts & Escalation

| Issue Type | Response | Contact |
|------------|----------|---------|
| Service outage | Immediate (5 min) | Founder: check Slack/Discord |
| Data loss | Immediate | Stop all writes, restore from backup |
| Security breach | Immediate | Rotate secrets, review logs, rollback |
| Performance degradation | 1 hour | Monitor, consider rollback if SLA violated |

## Testing Rollback Procedures

Quarterly, perform rollback drills:

1. **Staging Environment:**
   ```bash
   # Deploy to staging, then rollback
   cd apps/api
   npm run deploy:staging
   # Verify staging works
   # Introduce test failure (bad config)
   # Rollback using procedures
   ```

2. **Document Timing:**
   - Record rollback duration
   - Note any issues encountered
   - Update procedures based on findings

3. **Verify Data Integrity:**
   - After DB restore, run checksums
   - Compare row counts with backup metadata

## Appendix: Quick Reference Commands

### Dashboard
```bash
git revert <sha> && ./scripts/deploy-dashboard.sh  # Rollback
npx wrangler pages deployment list mekong-ide      # List deployments
```

### API Worker
```bash
cd apps/api && npm run deploy                      # Deploy
git revert <sha> && cd apps/api && npm run deploy # Rollback
wrangler tail mekong-api                           # Tail logs
```

### Databases
```bash
wrangler d1 export mekong-sessions --output=file.sql    # Backup
wrangler d1 restore mekong-sessions --file=file.sql     # Restore
wrangler d1 execute mekong-sessions --command="SELECT 1" # Test
```

### KV Namespaces
```bash
wrangler kv:key list RATE_LIMIT_KV                    # List keys
wrangler kv:key put RATE_LIMIT_KV "key" "value"      # Set
wrangler kv:key get RATE_LIMIT_KV "key"              # Get
wrangler kv:key delete RATE_LIMIT_KV "key"           # Delete
```

## Revision History

| Date | Version | Changes |
|------|---------|---------|
| 2026-06-20 | 1.0 | Initial document |
