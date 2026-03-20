# Mekong Engine — Support Runbook

**Version:** 3.2.0 | **Last Updated:** 2026-03-20 | **Status:** Production Ready

## Quick Reference

| Item | Value |
|------|-------|
| **Production URL** | `https://mekong-engine.agencyos-openclaw.workers.dev` |
| **Cloudflare Dashboard** | https://dash.cloudflare.com |
| **D1 Database** | `mekong-db` |
| **KV Namespace** | `RATE_LIMIT_KV` |
| **Support Email** | support@agencyos.network |

---

## 1. Health Checks

### Automated Monitoring

```bash
# Basic health check (run every 5 min)
curl -s https://mekong-engine.agencyos-openclaw.workers.dev/health

# Expected response (200 OK):
# {"status":"ok","version":"3.2.0","bindings":{"d1":true,"kv":true,"ai":true},"uptime_seconds":12345}
```

### Manual Verification

| Check | Command | Expected |
|-------|---------|----------|
| **API Status** | `GET /health` | `status: "ok"` |
| **Database** | Check `bindings.d1` | `true` |
| **Rate Limiting** | Check `bindings.kv` | `true` |
| **AI** | Check `bindings.ai` | `true` |
| **Latency** | Response time | `< 200ms` |

---

## 2. Common Issues & Resolutions

### Issue: 503 Service Unavailable

**Symptoms:**
- Health endpoint returns 503
- All API calls fail with "SERVICE_UNAVAILABLE"

**Root Causes:**

| Cause | Diagnosis | Fix |
|-------|-----------|-----|
| D1 not configured | `bindings.d1: false` | Link D1: `wrangler d1 link mekong-db` |
| KV not configured | `bindings.kv: false` | Create KV: `wrangler kv:namespace create RATE_LIMIT_KV` |
| AI binding missing | `bindings.ai: false` | Add `[ai]` to wrangler.toml |

**Resolution Steps:**
```bash
# 1. Check current bindings
curl https://mekong-engine.agencyos-openclaw.workers.dev/health

# 2. Verify wrangler.toml
cat wrangler.toml | grep -A2 "d1_databases\|kv_namespaces\|ai"

# 3. Deploy fix if needed
wrangler deploy
```

---

### Issue: 401 Unauthorized

**Symptoms:**
- API returns `{"error": "UNAUTHORIZED", "message": "Invalid API key"}`

**Root Causes:**

| Cause | Diagnosis | Fix |
|-------|-----------|-----|
| Invalid API key | Key format wrong | Verify key starts with `mk_` |
| Tenant deleted | Tenant not found in DB | Recreate tenant |
| Key expired | Session expired | Regenerate API key |

**Resolution Steps:**
```bash
# 1. Verify API key format
echo $API_KEY | grep "^mk_"

# 2. Test with known good key
curl -H "Authorization: Bearer mk_valid_key" https://.../health

# 3. Regenerate key if needed
curl -X POST https://.../billing/tenants/regenerate-key \
  -H "Authorization: Bearer mk_old_key"
```

---

### Issue: 402 Payment Required

**Symptoms:**
- API returns `{"error": "INSUFFICIENT_CREDITS"}`

**Root Causes:**

| Cause | Diagnosis | Fix |
|-------|-----------|-----|
| Credit balance zero | `GET /billing/credits` returns 0 | Purchase credits via Polar.sh |
| Subscription expired | Tier downgraded | Renew subscription |

**Resolution Steps:**
```bash
# 1. Check credit balance
curl https://mekong-engine.agencyos-openclaw.workers.dev/billing/credits \
  -H "Authorization: Bearer mk_xxx"

# 2. Guide customer to purchase
# Navigate to: https://polar.sh/agencyos/products
```

---

### Issue: 429 Rate Limit Exceeded

**Symptoms:**
- API returns `{"error": "RATE_LIMIT_EXCEEDED"}`

**Rate Limits by Tier:**

| Tier | Hourly | Daily |
|------|--------|-------|
| Free | 50 | 500 |
| Pro | 500 | 5,000 |
| Enterprise | 5,000 | 50,000 |

**Resolution Steps:**
```bash
# 1. Check tenant tier
curl https://mekong-engine.agencyos-openclaw.workers.dev/billing/tenants/me \
  -H "Authorization: Bearer mk_xxx"

# 2. Upgrade tier if needed
# Contact sales@agencyos.network for enterprise upgrade
```

---

### Issue: BYOK LLM Not Working

**Symptoms:**
- Custom LLM key returns errors
- Fallback to Workers AI

**Root Causes:**

| Cause | Diagnosis | Fix |
|-------|-----------|-----|
| Invalid API key | Provider rejects key | Verify key in provider dashboard |
| Key expired | Subscription ended | Renew provider subscription |
| Wrong provider | Mismatch provider setting | Re-save with correct provider |

**Resolution Steps:**
```bash
# 1. Check current LLM config
curl https://mekong-engine.agencyos-openclaw.workers.dev/v1/settings/llm \
  -H "Authorization: Bearer mk_xxx"

# 2. Re-save LLM config
curl -X POST https://.../v1/settings/llm \
  -H "Authorization: Bearer mk_xxx" \
  -H "Content-Type: application/json" \
  -d '{"provider":"openai","api_key":"sk-new-key"}'

# 3. Test LLM connection
curl -X POST https://.../ai/test \
  -H "Authorization: Bearer mk_xxx"
```

---

### Issue: Webhook Failures

**Symptoms:**
- Polar.sh/Zalo/Facebook webhooks not processing
- 401/403 errors on webhook endpoint

**Root Causes:**

| Cause | Diagnosis | Fix |
|-------|-----------|-----|
| Wrong webhook secret | Signature mismatch | Update webhook secret |
| Endpoint unreachable | Network/firewall | Check Cloudflare firewall rules |
| Payload format changed | Provider updated schema | Update webhook handler |

**Resolution Steps:**
```bash
# 1. Check webhook secret
# Polar.sh: Dashboard → Developers → Webhooks → Signing secret
# Zalo: OA Dashboard → API → Secret key

# 2. Update secret
wrangler secret put POLAR_WEBHOOK_SECRET
wrangler secret put ZALO_WEBHOOK_SECRET

# 3. Test webhook
# Use provider's webhook test tool
```

---

## 3. Escalation Matrix

| Severity | Description | Response Time | Escalation |
|----------|-------------|---------------|------------|
| **P0** | Production down | 15 min | CTO + Engineering |
| **P1** | Critical feature broken | 1 hour | Engineering Lead |
| **P2** | Non-critical bug | 4 hours | Support Team |
| **P3** | Feature request | 24 hours | Product Team |

### Escalation Contacts

| Role | Contact | Slack |
|------|---------|-------|
| **On-call Engineer** | oncall@agencyos.network | #oncall |
| **Engineering Lead** | eng-lead@agencyos.network | #engineering |
| **CTO** | cto@agencyos.network | #leadership |

---

## 4. Diagnostic Commands

### Database Diagnostics

```bash
# Check D1 database status
wrangler d1 info mekong-db

# List tables
wrangler d1 execute mekong-db --command "SELECT name FROM sqlite_master WHERE type='table';"

# Check recent missions
wrangler d1 execute mekong-db --command "SELECT * FROM missions ORDER BY created_at DESC LIMIT 10;"

# Check tenant count
wrangler d1 execute mekong-db --command "SELECT COUNT(*) FROM tenants;"
```

### KV Diagnostics

```bash
# List KV namespaces
wrangler kv:namespace list

# Check rate limit keys
wrangler kv:key list --namespace-id RATE_LIMIT_KV_ID

# Get rate limit for tenant
wrangler kv:key get --namespace-id RATE_LIMIT_KV_ID "ratelimit:tenant_id:hour"
```

### Log Analysis

```bash
# View recent deployment logs
wrangler tail --status error

# Live log streaming
wrangler tail --format pretty

# Filter by tenant
wrangler tail | grep "tenant_id: tnt_xyz"
```

---

## 5. Recovery Procedures

### Database Recovery

```bash
# 1. Check backup availability
# Cloudflare D1 → Backups → Select backup point

# 2. Restore from backup
wrangler d1 backup restore mekong-db --backup-id BACKUP_ID

# 3. Verify data integrity
wrangler d1 execute mekong-db --command "SELECT COUNT(*) FROM tenants;"
```

### Service Recovery

```bash
# 1. Redeploy service
wrangler deploy

# 2. Force rollback to previous version
wrangler rollback --version VERSION_ID

# 3. Verify health
curl https://mekong-engine.agencyos-openclaw.workers.dev/health
```

### Credit Ledger Recovery

```bash
# 1. Export ledger entries
wrangler d1 execute mekong-db --command "SELECT * FROM ledger_entries WHERE tenant_id='tnt_xyz';"

# 2. Calculate correct balance
wrangler d1 execute mekong-db --command "SELECT SUM(amount) FROM ledger_entries WHERE tenant_id='tnt_xyz';"

# 3. Create adjustment entry
wrangler d1 execute mekong-db --command "INSERT INTO ledger_entries (tenant_id, amount, description) VALUES ('tnt_xyz', 100, 'Balance adjustment');"
```

---

## 6. Performance Troubleshooting

### High Latency

```bash
# 1. Check global latency
curl -w "@curl-format.txt" https://mekong-engine.agencyos-openclaw.workers.dev/health

# curl-format.txt:
# time_namelookup:  %{time_namelookup}\n
# time_connect:     %{time_connect}\n
# time_starttransfer: %{time_starttransfer}\n
# time_total:       %{time_total}\n

# 2. Check Cloudflare Analytics
# Dashboard → Analytics → Performance

# 3. Identify slow queries
wrangler d1 execute mekong-db --command "SELECT query, avg_duration FROM query_stats ORDER BY avg_duration DESC LIMIT 10;"
```

### Memory Issues

```bash
# Check worker memory usage
# Cloudflare Dashboard → Workers → mekong-engine → Metrics

# Check for memory leaks
# Monitor memory over time in Cloudflare Metrics
```

---

## 7. Security Procedures

### Suspected API Key Compromise

```bash
# 1. Immediately regenerate key
curl -X POST https://.../billing/tenants/regenerate-key \
  -H "Authorization: Bearer mk_compromised_key"

# 2. Notify tenant
# Email: security@agencyos.network

# 3. Audit access logs
wrangler tail | grep "tenant_id: tnt_xyz"
```

### Rate Limit Abuse

```bash
# 1. Identify abuse pattern
wrangler d1 execute mekong-db --command "SELECT tenant_id, COUNT(*) FROM missions WHERE created_at > datetime('now', '-1 hour') GROUP BY tenant_id ORDER BY COUNT(*) DESC LIMIT 10;"

# 2. Temporarily suspend tenant
wrangler d1 execute mekong-db --command "UPDATE tenants SET status='suspended' WHERE tenant_id='tnt_abuser';"

# 3. Notify tenant
# Email: abuse@agencyos.network
```

---

## 8. Communication Templates

### P0 Incident Notification

```
Subject: [INCIDENT] Mekong Engine Production Outage

Team,

We are experiencing a production outage affecting Mekong Engine.

Impact: All API endpoints returning 503
Started: {TIME}
Detected by: {MONITORING/USER_REPORT}
Status: INVESTIGATING

Next update in: 15 minutes

- On-call Engineer
```

### Resolution Notification

```
Subject: [RESOLVED] Mekong Engine Production Outage

Team,

The production outage has been resolved.

Root cause: {DESCRIPTION}
Resolution: {FIX_APPLIED}
Duration: {DURATION}
Impact: {NUMBER_OF_AFFECTED_USERS}

Post-mortem scheduled for: {DATE/TIME}

- On-call Engineer
```

---

## Appendix: Environment Variables

| Variable | Purpose | How to Set |
|----------|---------|------------|
| `SERVICE_TOKEN` | Encryption key + admin auth | `wrangler secret put SERVICE_TOKEN` |
| `POLAR_WEBHOOK_SECRET` | Polar.sh webhook validation | `wrangler secret put POLAR_WEBHOOK_SECRET` |
| `LLM_API_KEY` | Global LLM fallback | `wrangler secret put LLM_API_KEY` |
| `LLM_BASE_URL` | Global LLM endpoint | `.dev.vars` (local) / `wrangler secret` (prod) |
| `DEFAULT_LLM_MODEL` | Default model name | Optional config |
| `ENVIRONMENT` | `production` or `development` | Wrangler config |

---

**Last Reviewed:** 2026-03-20 | **Next Review:** 2026-04-20
