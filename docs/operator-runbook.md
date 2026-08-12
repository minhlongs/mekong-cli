# Mekong CLI — Internal Operator Runbook

**Version**: 2.0 | **Date**: 2026-06-20 | **Status**: Production

This runbook provides operational guidance for running Mekong CLI infrastructure in production. It is intended for system operators, SREs, and DevOps engineers responsible for maintaining the platform.

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture Summary](#2-architecture-summary)
3. [Deployment Topology](#3-deployment-topology)
4. [Service Inventory](#4-service-inventory)
5. [Environment Configuration](#5-environment-configuration)
6. [Monitoring & Observability](#6-monitoring--observability)
7. [CI/CD Pipelines](#7-cicd-pipelines)
8. [Deployment Procedures](#8-deployment-procedures)
9. [Daily Operations](#9-daily-operations)
10. [Maintenance Tasks](#10-maintenance-tasks)
11. [Backup & Restore](#11-backup--restore)
12. [Troubleshooting Guide](#12-troubleshooting-guide)
13. [Emergency Procedures](#13-emergency-procedures)
14. [Security Operations](#14-security-operations)
15. [Cost Management](#15-cost-management)
16. [Contact Information](#16-contact-information)
17. [Quick Reference](#17-quick-reference)

---

## 1. System Overview

### What is Mekong CLI?

Mekong CLI is an AI-operated business platform that enables the "one-person billion-dollar company" concept. It provides 10 business layers (Founder, Business, Product, Engineering, Ops, Studio, CTO, PM, Dev, Worker) with 443+ commands that can be autonomously executed by AI agents.

### Core Purpose

- Enable solo founders to operate entire businesses with AI agents
- Provide autonomous goal execution via PEV (Plan-Execute-Verify) engine
- Support plugin extensibility with security isolation
- Billing via MCU (Mekong Credit Units) system
- Constitutional AI governance (9-principle ethical review)

### Key Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Uptime | 99.9% | To be measured |
| API Response Time (p95) | <500ms | To be measured |
| Command Startup (cold) | <1s | ~50ms (CF Workers) |
| Concurrent Users | 1000+ | To be measured |
| LLM Cost per Command | <$0.01 | Variable |

---

## 2. Architecture Summary

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Cloudflare Edge                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐         ┌─────────────────────────┐  │
│  │  Cloudflare     │         │  Cloudflare Workers     │  │
│  │  Pages          │◄───────►│  API Gateway            │  │
│  │  Dashboard      │         │  (apps/api)             │  │
│  │  ide.mekongmind.com      │                         │  │
│  └─────────────────┘         │  ┌─────────────────────┐│  │
│                               │  │ D1 Databases        ││  │
│                               │  │ • sessions          ││  │
│                               │  │ • audit_logs        ││  │
│                               │  └─────────────────────┘│  │
│                               │                         │  │
│                               │  ┌─────────────────────┐│  │
│                               │  │ KV Stores           ││  │
│                               │  │ • RATE_LIMIT_KV     ││  │
│                               │  │ • CACHE_KV          ││  │
│                               │  └─────────────────────┘│  │
│                               │                         │  │
│                               │  ┌─────────────────────┐│  │
│                               │  │ AI Binding          ││  │
│                               │  │ (@cf/meta/llama)    ││  │
│                               │  └─────────────────────┘│  │
│                               └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘

Backend Services (origin server)
├── PostgreSQL (or Cloudflare D1 for edge)
├── Redis (optional caching)
└── LLM Provider APIs (OpenRouter, Anthropic, OpenAI, Ollama)
```

### Component Inventory

| Component | Location | Technology | Purpose |
|-----------|----------|------------|---------|
| Dashboard | Cloudflare Pages | Next.js 16 | User IDE interface |
| API Gateway | Cloudflare Workers | TypeScript/Workers | Edge routing, auth, rate limiting |
| Mekong Engine | Cloudflare Workers | TypeScript/Workers | LLM orchestration |
| Zalo Parser | Cloudflare Workers | TypeScript/Workers | Zalo message parsing |
| CLI (local) | User machines | Python | Command execution |
| Database | D1 / PostgreSQL | SQLite-compatible | Sessions, audit logs |

### Data Flow

1. **User Command** → CLI or Dashboard → API Gateway
2. **Authentication** → Session validation (D1)
3. **Rate Limiting** → KV namespace check
4. **Route** → Proxy to backend or direct AI binding
5. **Audit Logging** → All requests logged to D1 audit_logs
6. **Response** → Return to client

---

## 3. Deployment Topology

### Environments

| Environment | Dashboard URL | API URL | Purpose |
|-------------|---------------|---------|---------|
| Production | https://ide.mekongmind.com | https://api.cashclaw.cc | Live customer traffic |
| Staging | https://staging.ide.mekongmind.com | https://staging-api.cashclaw.cc | Pre-release testing |

### Cloudflare Configuration

**Projects:**
- `mekong-ide` — Cloudflare Pages project for dashboard
- `mekong-api` — Cloudflare Worker for API gateway
- `mekong-engine` — Cloudflare Worker for LLM orchestration
- `zalo-parser` — Cloudflare Worker for Zalo integration

**Resources:**
- D1 Databases:
  - `mekong-sessions` — User session storage
  - `mekong-audit` — Request audit logs
- KV Namespaces:
  - `RATE_LIMIT_KV` — Rate limit counters
  - `CACHE_KV` — General caching

### CI/CD Pipeline

**Triggers:**
- Push to `main` → Deploy to production
- Pull request → Deploy to preview (dashboard only)

**Workflow**: `.github/workflows/deploy-cf.yml`
1. Checkout code
2. Setup Node.js
3. Install dependencies
4. Run type check
5. Run lint
6. Deploy to Cloudflare

---

## 4. Service Dependencies

### External Services

| Service | Purpose | Status | Contact |
|---------|---------|--------|---------|
| Cloudflare | Hosting, Edge network | ✅ Healthy | CF Dashboard |
| Supabase | Database for dashboard | ✅ Healthy | Supabase Dashboard |
| Polar.sh | Payment/checkout | ✅ Healthy | Polar Dashboard |
| OpenRouter | LLM routing | ✅ Healthy | OpenRouter Dashboard |
| Anthropic | Claude API (fallback) | ✅ Healthy | Anthropic Console |

### Environment Variables

**API Worker** (`apps/api/wrangler.toml`):

| Variable | Required | Description |
|----------|----------|-------------|
| `BACKEND_API_URL` | Yes | Backend service URL (origin) |
| `WEBHOOK_SECRET` | Yes | Secret for webhook signature verification |
| `ENVIRONMENT` | Yes | `production` or `staging` |
| `POLAR_WEBHOOK_SECRET` | No | Polar webhook verification |
| `MEKONG_ADMIN_TOKEN` | No | Admin authentication token |

**Dashboard** (Cloudflare Pages environment variables):

| Variable | Required | Description |
|----------|----------|-------------|
| `NEXT_PUBLIC_SUPABASE_URL` | Yes | Supabase project URL |
| `SUPABASE_SERVICE_KEY` | Yes | Supabase service role key |
| `NEXT_PUBLIC_API_URL` | No | Override API gateway URL |

### Service Health Endpoints

| Service | Health URL | Expected Response |
|---------|------------|-------------------|
| API Gateway | `https://api.cashclaw.cc/health` | `{"status":"healthy",...}` |
| Dashboard | `https://ide.mekongmind.com` | HTTP 200, Claude-styled page |
| Mekong Engine | Cloudflare Workers metrics | Via `wrangler tail` |

---

## 5. Monitoring & Alerting

### Health Checks

**Automated Health Check (every 1 minute):**
```bash
#!/usr/bin/env bash
# scripts/health-check.sh

API_HEALTH=$(curl -s https://api.cashclaw.cc/health | jq -r '.status // "unknown"')
DASH_STATUS=$(curl -sI https://ide.mekongmind.com | head -1 | awk '{print $2}')

if [[ "$API_HEALTH" != "healthy" ]]; then
    echo "❌ API health check failed: $API_HEALTH"
    exit 1
fi

if [[ "$DASH_STATUS" != "200" ]]; then
    echo "❌ Dashboard health check failed: $DASH_STATUS"
    exit 1
fi

echo "✅ All services healthy"
exit 0
```

### Key Metrics to Monitor

#### API Gateway Metrics

| Metric | Threshold | Description |
|--------|-----------|-------------|
| Request rate | Alert if >80K/day | approaching free tier limit |
| Error rate (5xx) | Alert if >1% | Service degradation |
| Response time (p95) | Alert if >2s | Performance issue |
| Rate limit hits | Monitor trends | Potential abuse |

#### Database Metrics

| Metric | Threshold | Description |
|--------|-----------|-------------|
| D1 reads/writes | Alert if >80% of daily quota | Cost control |
| Session count | Monitor growth | Capacity planning |
| Audit log size | Alert if >1GB/month | Storage management |

#### Billing Metrics

| Metric | Threshold | Description |
|--------|-----------|-------------|
| Active subscriptions | Monitor | Business metric |
| MCU credits remaining | Alert if <20% | Customer experience |
| Payment failures | Alert if >5% | Billing issues |

#### Plugin Health Metrics

| Metric | Threshold | Description |
|--------|-----------|-------------|
| Plugin health status | Alert if any unhealthy/error | Plugin system health |
| Error rate per plugin | Alert if >20% (warning), >50% (critical) | Plugin reliability |
| Load time (p95) | Alert if >5s (warning), >10s (critical) | Plugin performance |
| Memory usage per plugin | Alert if >100 MB | Resource consumption |
| Consecutive failures | Alert if >3 (warning), >5 (critical) | Recovery needed |
| Recovery attempts rate | Alert if >3 in 10 min | Instability indicator |
| Plugins degraded count | Alert if >2 | Multiple issues |

**Health Endpoint:** Plugin health is included in the main `/health` endpoint under the `plugins` component. Additionally, individual plugin health can be queried via:

```bash
# Get overall plugin health via health endpoint
curl https://api.cashclaw.cc/health | jq '.components.plugins'

# Or check plugin health directly (if exposed)
mekong plugin health
mekong plugin health <plugin-name>
```

**Grafana Dashboard:** `Plugin Health Monitoring` dashboard available at:
- URL: `https://grafana.m1max.cashclaw.cc/d/mekong-plugin-health`
- Shows: plugin status timeline, error rates, load times, recovery attempts

**Alert Rules:** Configured in `observability/alerts.yml`:
- `PluginIsolationBreach` - Critical: plugin in unhealthy/error state
- `PluginMemorySpike` - Critical: memory > 100 MB
- `PluginHighErrorRate` - Warning: error rate > 20%
- `PluginCriticalErrorRate` - Critical: error rate > 50%
- `PluginSlowLoad` - Warning: p95 load > 5s
- `PluginVerySlowLoad` - Critical: p99 load > 10s
- `PluginConsecutiveFailures` - Warning: 3+ consecutive failures
- `PluginFrequentRecovery` - Warning: >3 recovery attempts in 10m
- `PluginBillingAnomalyHighVolume` - Critical: 10x normal command rate
- `MultipleDegradedPlugins` - Warning: >2 degraded simultaneously
- `AllPluginsUnhealthy` - Critical: all plugins unhealthy

### Cloudflare Metrics

Access via Cloudflare Dashboard or `wrangler`:

```bash
# Worker metrics
wrangler metrics mekong-api --since 1h

# Pages deployment status
npx wrangler pages deployment list mekong-ide --limit=10

# D1 database size
wrangler d1 info mekong-sessions
```

### Log Aggregation

**Current logging setup:**
- API requests: D1 `request_logs` table
- Worker logs: `wrangler tail mekong-api`
- Build logs: GitHub Actions artifacts

**Recommended centralized logging:**
- Set up Cloudflare Logpush to export logs to R2 or external service
- Consider Logflare or Better Stack for log aggregation

### Alerting Setup

Using GitHub Actions (scheduled):

```yaml
# .github/workflows/monitoring.yml
name: Production Health Check
on:
  schedule:
    - cron: '*/5 * * * *'  # Every 5 minutes
jobs:
  health-check:
    runs-on: ubuntu-latest
    steps:
      - name: Check API health
        run: |
          STATUS=$(curl -s https://api.cashclaw.cc/health | jq -r '.status')
          if [[ "$STATUS" != "healthy" ]]; then
            # Send alert via webhook
            curl -X POST $SLACK_WEBHOOK_URL -d '{"text":"API health check failed"}'
            exit 1
          fi
```

---

#### Plugin Health Monitoring

The plugin health monitoring system provides comprehensive observability for all Mekong CLI plugins. It tracks plugin load times, command execution metrics, errors, and recovery attempts.

**Health Endpoint:**
```bash
# CLI local health endpoint (includes plugin status)
curl http://localhost:9192/health | jq '.components.plugins'

# Or full health status
mekong health
```

**Grafana Dashboard:**
- Dashboard: `observability/dashboards/plugin-health.json`
- Import into Grafana via: + → Import → Upload JSON file
- Metrics source: Prometheus endpoint `http://otel-collector:8889`

**Alert Rules:**
Prometheus alert rules are defined in `observability/rules/plugin-health-rules.yml`. Key alerts:
- `PluginMemorySpike`: Plugin memory >200MB for 2min
- `PluginMemoryCritical`: Plugin memory >500MB for 1min  
- `PluginHighErrorRate`: Error rate >50% for 3min
- `PluginCriticalErrorRate`: Error rate >80% for 1min
- `PluginConsecutiveFailures`: >5 consecutive failures
- `PluginUsageSpike`: >1000 commands/min (potential abuse)
- `ExcessivePluginCount`: >50 plugins loaded (security)

**CLI Commands:**
```bash
# Check plugin health status
mekong plugin health

# Check specific plugin
mekong plugin health <plugin-name>

# View health history
mekong plugin health history

# Force health check
mekong plugin health check <plugin-name>

# Manual recovery
mekong plugin recovery trigger <plugin-name>

# Auto-recovery management
mekong plugin recovery enable
mekong plugin recovery disable
```

**Troubleshooting:**

1. **Unhealthy Plugin**
   - Check plugin-specific logs: `~/.mekong/plugins/<name>/logs/`
   - Run manual health check: `mekong plugin health check <name>`
   - Review Grafana dashboard for error patterns
   - Attempt recovery: `mekong plugin recovery trigger <name>`
   - If recovery fails, disable plugin: `mekong plugin disable <name>`

2. **High Memory Usage**
   - Identify memory-heavy plugins via Grafana
   - Check for memory leaks in plugin code
   - Restart CLI session to clear memory
   - Consider plugin isolation limits adjustment

3. **High Error Rate**
   - Review recent command failures
   - Check plugin dependencies and configuration
   - Verify external service connectivity
   - Update plugin to latest version

**Configuration:**
Plugin health monitoring configuration: `~/.mekong/plugin_health.yaml`

```yaml
monitoring:
  check_interval_seconds: 60
  telemetry_enabled: true

auto_recovery:
  enabled: true
  max_attempts: 3
  cooldown_seconds: 300
  strategies: ["graceful", "force"]

thresholds:
  error_rate_warning: 0.20
  error_rate_critical: 0.50
  consecutive_failures_warning: 3
  consecutive_failures_critical: 5
  load_time_ms_warning: 5000
  load_time_ms_critical: 10000
```

---


## 6. Daily Operations

### Morning Checklist (15 minutes)

- [ ] Check health endpoints: API and Dashboard responding 200
- [ ] Review error rate from previous 24h (<1% target)
- [ ] Verify D1 database quotas not exceeded
- [ ] Check Cloudflare analytics for unusual traffic spikes
- [ ] Review any failed deployments from overnight
- [ ] Check payment webhook processing (Polar)

### Weekly Tasks (30 minutes)

- [ ] Export D1 database backups (sessions + audit)
- [ ] Review KV namespace sizes (clean if needed)
- [ ] Check LLM provider costs and usage
- [ ] Review Polar subscription events
- [ ] Update dependencies (security patches)
- [ ] Test rollback procedure in staging

### Monthly Tasks (1 hour)

- [ ] Full system backup verification (restore test)
- [ ] Security audit review
- [ ] Cost optimization review
- [ ] Capacity planning assessment
- [ ] Update runbook with new procedures
- [ ] Review and rotate secrets (if policy requires)

---

## 7. Common Procedures

### Deploy Dashboard

```bash
# Manual deployment
cd ~/mekong-cli/apps/dashboard
npm run build
npx wrangler pages deploy .next/static --project-name=mekong-ide --branch=production

# Or use script
./scripts/deploy-dashboard.sh

# Verify
curl -sI https://ide.mekongmind.com | head -1
# Expected: HTTP/2 200
```

### Deploy API Worker

```bash
cd ~/mekong-cli/apps/api
npm run deploy    # Production
# or
npm run deploy:staging  # Staging

# Verify
curl https://api.cashclaw.cc/health | jq .
```

### Database Backup

```bash
#!/usr/bin/env bash
# scripts/backup-d1-databases.sh

BACKUP_DIR="/tmp/backups/d1/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

# Export databases
wrangler d1 export mekong-sessions --output="$BACKUP_DIR/sessions-$(date +%H%M%S).sql"
wrangler d1 export mekong-audit --output="$BACKUP_DIR/audit-$(date +%H%M%S).sql"

# Optional: Upload to R2
# wrangler r2 object put mekong-backups/... --file=...

# Cleanup old backups (>30 days)
find /path/to/backup/dir -name "*.sql" -mtime +30 -delete

echo "Backup complete: $BACKUP_DIR"
```

### Database Restore

```bash
# 1. List backups
ls -la backups/d1/

# 2. Restore (WARNING: replaces entire database)
wrangler d1 restore mekong-sessions --file=backups/d1/sessions-YYYYMMDD-HHMMSS.sql
wrangler d1 restore mekong-audit --file=backups/d1/audit-YYYYMMDD-HHMMSS.sql

# 3. Verify
wrangler d1 execute mekong-sessions --command="SELECT count(*) FROM sessions;"
```

### View Worker Logs

```bash
# Tail live logs
wrangler tail mekong-api

# With timestamps
wrangler tail mekong-api --format=pretty

# Follow specific environment
wrangler tail mekong-api --env staging

# Past logs (last 100 lines)
wrangler tail mekong-api --since 5m | tail -100
```

### Query D1 Database

```bash
# List databases
wrangler d1 list

# Database info
wrangler d1 info mekong-sessions

# Execute query
wrangler d1 execute mekong-sessions --command="
  SELECT user_id, created_at FROM sessions
  WHERE created_at > datetime('now', '-1 day')
  ORDER BY created_at DESC
  LIMIT 10;
"

# Interactive session
wrangler d1 execute mekong-audit --interactive
```

### KV Namespace Management

```bash
# List keys (first 1000)
wrangler kv:key list RATE_LIMIT_KV --limit=1000

# Get value
wrangler kv:key get RATE_LIMIT_KV "rate-limit:192.168.1.1"

# Set value with TTL (expires in 1 hour)
wrangler kv:key put RATE_LIMIT_KV "key" "value" --ttl=3600

# Delete key
wrangler kv:key delete RATE_LIMIT_KV "key"

# Flush all keys (DESTRUCTIVE)
wrangler kv:key list RATE_LIMIT_KV --format=json | jq -r '.[].name' | \
  xargs -I {} wrangler kv:key delete RATE_LIMIT_KV {}
```

### Secrets Rotation

```bash
# 1. Generate new secret
NEW_SECRET=$(openssl rand -base64 32)

# 2. Update in Cloudflare
cd apps/api
wrangler secret put WEBHOOK_SECRET <<< "$NEW_SECRET"

# 3. Update any dependent configs
# (Update in Polar dashboard webhook secret, etc.)

# 4. Verify
# Test that webhooks still work with new secret
```

---

## 8. Troubleshooting Guide

### API Gateway Returns 5xx Errors

**Symptom:** `curl https://api.cashclaw.cc/health` returns 500 or times out.

**Diagnosis:**
```bash
# 1. Check worker logs
wrangler tail mekong-api --since 10m | grep -i error

# 2. Check recent deployments
git log --oneline apps/api -5

# 3. Test locally
cd apps/api
pnpm dev
curl http://localhost:8787/health
```

**Resolution:**
- If recent deploy caused issue → rollback (see Emergency Procedures)
- If database errors → check D1 status
- If memory errors → check for infinite loops or large payloads

### Dashboard Not Loading

**Symptom:** `ide.mekongmind.com` shows Cloudflare error page or blank.

**Diagnosis:**
```bash
# 1. Check Pages deployment status
npx wrangler pages deployment list mekong-ide --limit=5

# 2. Check build logs in GitHub Actions

# 3. Verify custom domain mapping
# Cloudflare Dashboard → Pages → mekong-ide → Custom domains
```

**Resolution:**
- If deployment failed → fix build errors and redeploy
- If domain not mapped → add `ide.mekongmind.com` to custom domains
- Wait 2-5 minutes for DNS propagation after adding domain

### Payment Webhook Not Firing

**Symptom:** Polar subscription created but credits not allocated.

**Diagnosis:**
```bash
# 1. Check webhook configuration in Polar dashboard
# Verify URL is: https://api.cashclaw.cc/v1/webhooks/polar

# 2. Check recent webhook attempts
curl -sH "Authorization: Bearer $ADMIN_TOKEN" \
  https://api.cashclaw.cc/v1/webhooks/recent | jq .

# 3. Check worker logs for webhook processing
wrangler tail mekong-api --since 1h | grep -i webhook
```

**Resolution:**
1. Verify `POLAR_WEBHOOK_SECRET` is set correctly
2. Check webhook signature verification code
3. Replay test event from Polar dashboard
4. Ensure endpoint is publicly accessible (no auth required)

### High LLM Costs

**Symptom:** LLM provider bills exceeding expectations.

**Diagnosis:**
```bash
# Check usage logs
tail -100 ~/.mekong/usage_events.jsonl | jq -r '.model + " " + .tokens' | sort | uniq -c | sort -nr

# Check OpenRouter dashboard for usage breakdown
```

**Resolution:**
1. Implement token limits per command in MCU costing
2. Cache frequent LLM responses
3. Route cheaper models for simple tasks
4. Set up alerts for cost thresholds

### Rate Limiting Too Aggressive

**Symptom:** Legitimate users hitting rate limits.

**Diagnosis:**
```bash
# Check rate limit KV entries for user
wrangler kv:key get RATE_LIMIT_KV "rate-limit:user-ip-or-id"

# Check current limits in code
grep -r "rate-limit" apps/api/src/
```

**Resolution:**
1. Adjust rate limit thresholds
2. Consider authenticated rate limits vs IP-based
3. Implement token bucket algorithm for smoother limits

### Database Quota Exceeded

**Symptom:** D1 operations failing with quota errors.

**Resolution:**
1. Review free tier limits: 1K reads/day, 1K writes/day
2. Upgrade Cloudflare plan for higher quotas
3. Implement caching to reduce reads
4. Batch writes where possible
5. Consider moving to dedicated PostgreSQL for scale

### Plugin Health Issues

**Symptom:** Alerts firing for plugin health, or plugins failing to load/execute.

**Diagnosis:**
```bash
# 1. Check overall plugin health via health endpoint
curl https://api.cashclaw.cc/health | jq '.components.plugins'

# 2. Check local plugin health (CLI-side)
cd ~/mekong-cli
mekong plugin health

# 3. Check detailed status for specific plugin
mekong plugin health <plugin-name>

# 4. View plugin health history
mekong plugin health history --limit 20

# 5. Check Grafana dashboard for trends
# Open: https://grafana.m1max.cashclaw.cc/d/mekong-plugin-health

# 6. Check plugin logs (CLI-side)
tail -100 ~/.mekong/plugin_health.json | jq .

# 7. Check for isolation breaches (security)
grep -i "isolation" ~/.mekong/security_audit.log 2>/dev/null || echo "No isolation events"
```

**Common Issues & Resolution:**

| Issue | Symptoms | Resolution |
|-------|----------|------------|
| **Plugin Isolation Breach** | Alert `PluginIsolationBreach`, plugin status = unhealthy/error | 1. Check plugin logs for crash traces<br>2. Verify plugin manifest permissions<br>3. Try `mekong plugin recover <plugin>`<br>4. If persistent, disable plugin: `mekong plugin disable <plugin>` |
| **High Memory Usage** | Alert `PluginMemorySpike`, slow performance | 1. Identify memory-heavy plugin via Grafana<br>2. Check for memory leaks in plugin code<br>3. Restart CLI to clear memory<br>4. Consider plugin isolation limits |
| **High Error Rate** | Alert `PluginHighErrorRate`, commands failing | 1. Check plugin's health_check() implementation<br>2. Review plugin dependencies/network access<br>3. Examine recent code changes<br>4. Rollback plugin update if applicable |
| **Slow Plugin Load** | Alert `PluginSlowLoad`, long startup times | 1. Profile plugin initialization<br>2. Check for slow imports or network calls<br>3. Consider lazy loading heavy dependencies<br>4. Cache plugin compiled bytecode |
| **Frequent Recoveries** | Alert `PluginFrequentRecovery`, unstable plugin | 1. Check plugin logs for root cause<br>2. Verify plugin resource limits<br>3. Update plugin to latest version<br>4. If unrecoverable, remove plugin |
| **Billing Anomaly** | Alert `PluginBillingAnomalyHighVolume` | 1. Verify no abuse/auto-loop<br>2. Check plugin command execution patterns<br>3. Temporarily disable plugin if suspicious<br>4. Review MCU costing for that plugin |

**Plugin Recovery Procedures:**

```bash
# View recovery status
mekong plugin recovery status

# Manually trigger recovery for a plugin
mekong plugin recover <plugin-name>

# Disable auto-recovery (during debugging)
mekong plugin recovery disable

# Enable auto-recovery
mekong plugin recovery enable

# Reset failure count for a plugin
mekong plugin recovery reset-failures <plugin-name>
```

**Plugin Isolation Security Check:**

If you suspect an isolation breach (plugin accessing unauthorized resources):

1. **Immediate containment:**
   ```bash
   mekong plugin disable <plugin-name>
   ```

2. **Audit plugin manifest:**
   ```bash
   cat ~/.mekong/plugins/<plugin-name>/manifest.yaml | grep -E "permissions|capabilities"
   ```

3. **Review security audit log:**
   ```bash
   # Check for sandbox escapes, file access violations
   grep -i "SECURITY" ~/.mekong/security_audit.log
   ```

4. **Run isolation test suite:**
   ```bash
   cd ~/mekong-cli
   pytest tests/test_isolation.py -v
   ```

5. **Report incident** if confirmed breach (see Emergency Procedures).

### CLI Commands Failing (User-side)

**Symptom:** Users reporting command errors.

**Diagnosis:**
```bash
# Ask user to run:
mekong status
mekong version
echo $LLM_BASE_URL $LLM_MODEL
```

**Common Issues:**
- Missing API key → guide to set LLM_* env vars
- Outdated CLI → instruct to `git pull && pip install -r requirements.txt`
- Plugin conflicts → `mekong admin plugin disable <plugin>`

---

## 9. Emergency Procedures

### Incident Response Flow

```
Incident Detected
    │
    ▼
┌─────────────┐
│  Assess     │  Impact: users affected? data loss? security?
│  Severity   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Contain    │  Stop the bleeding (rollback, disable, block)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Notify     │  Stakeholders, customers if SLA impact
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Resolve    │  Apply fix, rollback, or workaround
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Post-Mortem│  Document, prevent recurrence
└─────────────┘
```

### Severity Levels

| Level | Criteria | Response Time | Notification |
|-------|----------|---------------|--------------|
| P0 | Complete outage, data loss, security breach | Immediate (<5 min) | All hands, customer notice |
| P1 | Major feature down, paying customers affected | <30 min | Team lead, customer comms |
| P2 | Non-critical feature down, minor impact | <2 hours | Team notification |
| P3 | Minor bugs, no customer impact | Next business day | Ticket only |

### Rollback Decision Matrix

| Situation | Action | Timeline |
|-----------|--------|----------|
| API Worker deployment broke health check | Immediate rollback | <5 min |
| Dashboard build failure | Cancel deploy, fix forward | <10 min |
| Database migration failure | Restore from backup | <30 min |
| LLM provider outage | Switch to fallback provider | <2 min |
| DDoS attack | Enable enhanced WAF rules | <5 min |

### Immediate Rollback Procedures

#### Dashboard Rollback (Fastest)

```bash
cd ~/mekong-cli
git log --oneline apps/dashboard -3

# Revert last deployment
git revert <bad-commit> -m 1
git push origin main

# Deploy reverted code
./scripts/deploy-dashboard.sh

# Verify
curl -sI https://ide.mekongmind.com
```

#### API Worker Rollback

```bash
cd ~/mekong-cli/apps/api
git log --oneline -3

# Revert
git revert <bad-commit>
git push origin main

# Deploy
npm run deploy

# Verify
curl https://api.cashclaw.cc/health | jq .
```

#### Full System Rollback

Use `scripts/full-rollback.sh` (if exists) or:

```bash
# Revert all deployable components
cd ~/mekong-cli
git revert <bad-commit> -- apps/dashboard/ apps/api/
git push origin main

# Deploy each
./scripts/deploy-dashboard.sh
cd apps/api && npm run deploy
```

### Service Degradation Workarounds

**If API Gateway is overloaded:**
1. Enable Cloudflare caching rules for static endpoints
2. Increase rate limit thresholds temporarily
3. Route some traffic directly to backend (bypass gateway for non-critical)

**If LLM provider is down:**
1. Switch `LLM_BASE_URL` to fallback provider
2. Enable offline mode for non-critical commands
3. Queue commands for later execution

**If database is unavailable:**
1. Enable read-only mode (serve cached data)
2. Redirect users to status page
3. Start emergency D1 restore if corruption

---

## 10. Maintenance Tasks

### Dependency Updates

**Dashboard:**
```bash
cd apps/dashboard
pnpm update
# Test locally before deploying
pnpm test  # if tests exist
pnpm build
```

**API Worker:**
```bash
cd apps/api
pnpm update
pnpm build  # if applicable
npm run deploy:staging  # Test in staging first
```

**Python CLI (user-side):**
```bash
cd ~/mekong-cli
pip install --upgrade -r requirements.txt
# Users get updates via git pull
```

### Security Patching

**Process:**
1. Monitor `dependabot` alerts in GitHub
2. Review security advisories weekly
3. Apply patches within 48 hours for critical CVEs
4. Test in staging before production

**Secrets Audit:**
```bash
# Check for accidentally committed secrets
git grep -i "api_key\|secret\|password\|token" -- '*.py' '*.ts' '*.json' '*.env*' | grep -v '.env.example'

# Scan with Gitleaks
gitleaks detect --source . --config .gitleaks.toml
```

### Database Maintenance

**D1:**
- Automatic backups via daily export (set up cron)
- Monitor database size monthly
- Archive old audit logs (>6 months) to R2

**PostgreSQL (if used):**
- VACUUM ANALYZE weekly
- Index optimization monthly
- Connection pool tuning as needed

### Cache Warmup

After deployment, warm caches:

```bash
# Health check to populate cache
for i in {1..10}; do
  curl -s https://api.cashclaw.cc/health > /dev/null
done

# Trigger common endpoints
curl -s https://api.cashclaw.cc/v1/pricing
```

### Performance Optimization

**Monthly review:**
1. Check Cloudflare analytics for slow endpoints
2. Review worker CPU time (wrangler metrics)
3. Optimize slow database queries
4. Cache layer effectiveness analysis

### GDPR Data Retention Cleanup

**Purpose:** Automatically delete or anonymize data according to GDPR retention periods.

**Retention Policy:**
| Data Type | Retention | Action |
|-----------|-----------|--------|
| Webhook events | 90 days | Delete |
| Poll responses | 2 years | Delete |
| Audit logs | 2 years | Anonymize (keep metadata) |
| GDPR audit logs | 7 years | Keep (compliance) |
| Conversion records | 7 years | Keep (legal hold) |
| Pilot records (deleted) | 30 days | Anonymize after deletion |

**Setup:**
1. Locate the cleanup script: `scripts/gdpr_data_retention_cleanup.py`
2. Test dry-run: `python3 scripts/gdpr_data_retention_cleanup.py --dry-run --verbose`
3. Install cron job from `scripts/cron/gdpr-retention-cron.conf`

**Cron Configuration:**
```bash
# Edit crontab
crontab -e

# Add (runs daily at 2 AM):
0 2 * * * cd /path/to/mekong-cli && MEKONG_CONFIG_DIR=~/.mekong /opt/homebrew/bin/python3 scripts/gdpr_data_retention_cleanup.py --execute --report 2>&1 | /usr/bin/logger -t gdpr-retention
```

**Environment Variables:**
- `MEKONG_CONFIG_DIR` - Config directory (default: ~/.mekong)
- `MEKONG_PILOT_STORAGE` - Storage backend (jsonl or sqlite)

**Monitoring:**
- Log file: `~/.mekong/gdpr_retention_log.jsonl`
- Syslog tag: `gdpr-retention`
- Alert on: non-zero exit code, errors in log

**Verification:**
```bash
# Check last run status
tail -n 50 ~/.mekong/gdpr_retention_log.jsonl | grep '"event_type":"cleanup_completed"'

# View recent deletions
tail -n 100 ~/.mekong/gdpr_retention_log.jsonl | grep '"action":"deleted"'
```

**Rollback:** Data deletion is permanent. Restore from backup if needed:
```bash
# Restore pilots from backup
cp ~/.mekong/backups/pilots-YYYY-MM-DD.jsonl ~/.mekong/pilots.jsonl
```

**Related Documentation:**
- `docs/privacy/ropa-20260620.md` - Full retention policy
- `docs/compliance/gdpr-remediation-tracker-20260620.md` - Remediation tracker

---

## 11. Security Operations

### Access Control

**Cloudflare:**
- Use SSO if available for team access
- Enable 2FA for all admin accounts
- Principle of least privilege for API tokens
- Rotate API tokens quarterly

**GitHub:**
- Require 2FA for all collaborators
- Code review required for production branches
- Branch protection on `main`
- Secret scanning enabled

**Local Development:**
- `.env` files in `.gitignore`
- Never commit API keys or secrets
- Use `.env.local` for local overrides (gitignored)

### Secrets Management

**Production Secrets Location:**
- Cloudflare Worker secrets (via `wrangler secret put`)
- GitHub repository secrets (for CI/CD)
- Local `~/.mekong/` for developer environments (gitignored)

**Rotation Schedule:**

| Secret | Rotation Frequency | Next Due |
|--------|-------------------|----------|
| `WEBHOOK_SECRET` | Quarterly | - |
| `POLAR_WEBHOOK_SECRET` | Quarterly | - |
| Cloudflare API token | Semi-annually | - |
| LLM API keys | Per provider policy | - |

### Audit Logging

All API requests logged to `request_logs` table:

```sql
-- Sample query: failed auth attempts
SELECT user_id, endpoint, status_code, timestamp
FROM request_logs
WHERE status_code >= 400
  AND timestamp > datetime('now', '-1 day')
ORDER BY timestamp DESC;
```

**Log Retention:**
- D1 audit logs: 90 days (automatic)
- Cloudflare logs: 7 days (free tier)
- Recommended: Export to R2 for long-term storage

### Security Monitoring

**Alerts to set up:**
1. Multiple failed auth attempts from same IP
2. Unusual LLM token usage spikes
3. Database export operations
4. Worker secret access patterns

**Weekly review:**
- GitHub security alerts
- Cloudflare security events
- Polar subscription anomalies

### Incident Response

**For suspected breach:**
1. Immediately rotate all secrets
2. Review audit logs for unauthorized access
3. Check for data exfiltration
4. Notify affected users (compliance requirement)
5. Consider temporary service suspension

---

## 12. Contact Information

### Internal Team

| Role | Contact | Escalation |
|------|---------|------------|
| Lead Developer | - | Primary contact for code issues |
| DevOps/SRE | - | Infrastructure issues |
| Security Officer | - | Security incidents |

### External Services Support

| Service | Support URL | SLA |
|---------|-------------|-----|
| Cloudflare | https://support.cloudflare.com | 24/7 for Enterprise |
| Supabase | https://supabase.com/support | Business hours |
| Polar.sh | support@polar.sh | 24/7 |
| OpenRouter | https://openrouter.ai/support | Community |

### Monitoring Dashboards

| Dashboard | URL | Purpose |
|-----------|-----|---------|
| Cloudflare Analytics | CF Dashboard → Analytics | Traffic, errors, performance |
| Polar Subscriptions | polar.sh → Dashboard | Billing, subscriptions |
| OpenRouter Usage | openrouter.ai → Usage | LLM costs, models |
| GitHub Actions | github.com/.../actions | CI/CD status |

### Documentation

| Document | Location |
|----------|----------|
| Deployment Guide | `docs/deployment-guide.md` |
| Rollback Procedures | `docs/rollback-procedures.md` |
| Troubleshooting Guide | `docs/troubleshooting.md` |
| Go-Live Playbook | `GO_LIVE_PLAYBOOK.md` |
| Architecture | `ARCHITECTURE.md` |

---

## Appendix

### Quick Command Reference

```bash
# Health checks
curl https://api.cashclaw.cc/health | jq .
curl -sI https://ide.mekongmind.com

# Deploy
./scripts/deploy-dashboard.sh
cd apps/api && npm run deploy

# Logs
wrangler tail mekong-api
wrangler d1 execute mekong-audit --command="SELECT * FROM request_logs LIMIT 10;"

# Database
wrangler d1 export mekong-sessions --output=backup.sql
wrangler d1 restore mekong-sessions --file=backup.sql

# KV
wrangler kv:key list RATE_LIMIT_KV
wrangler kv:key delete RATE_LIMIT_KV "key"

# Rollback
git revert <sha> && ./scripts/deploy-dashboard.sh
```

### Checklist Templates

**Pre-Deployment Checklist:**
- [ ] Tests passing locally
- [ ] Type check passes (`npx tsc --noEmit`)
- [ ] Lint passes (`pnpm lint`)
- [ ] Build succeeds (`npm run build`)
- [ ] Staging deployed and verified
- [ ] Database migrations reviewed
- [ ] Rollback plan documented

**Post-Deployment Checklist:**
- [ ] Health check returns 200
- [ ] Smoke tests passing
- [ ] No error rate increase (monitor 15 min)
- [ ] LLM costs normal
- [ ] Payment flow working
- [ ] Team notified of deployment

---

**Document Maintenance:** This runbook should be reviewed quarterly and updated after any major incident or architectural change.
