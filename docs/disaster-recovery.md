# Disaster Recovery Plan — Mekong Engine

> **RTO (Recovery Time Objective):** 4 hours
> **RPO (Recovery Point Objective):** 24 hours
> **Last Updated:** 2026-03-20
> **Version:** 1.0

---

## 1. Overview

This document outlines the disaster recovery procedures for Mekong Engine, the Cloudflare Workers-based PEV (Plan-Execute-Verify) engine that powers AgencyOS RaaS (Revenue-as-a-Service).

### 1.1 Critical Systems

| System | Platform | Priority | Recovery Time |
|--------|----------|----------|---------------|
| Database (D1) | Cloudflare D1 | P0 | 2 hours |
| API (Workers) | Cloudflare Workers | P0 | 30 minutes |
| KV Cache | Cloudflare KV | P1 | 1 hour |
| File Storage | Cloudflare R2 | P2 | 4 hours |
| Secrets | Cloudflare Secrets | P0 | 30 minutes |

---

## 2. Backup Strategy

### 2.1 Database Backups (D1)

**Automated Backups:**
- Cloudflare D1 provides **point-in-time recovery** automatically
- Backups are retained for **30 days**
- No manual intervention required for daily backups

**Manual Backup Script:**
```bash
# Export D1 database to SQL file
wrangler d1 export mekong-db --output=./backups/mekong-db-$(date +%Y%m%d).sql

# Upload to R2 for off-site storage
wrangler r2 object put backups/mekong-db-$(date +%Y%m%d).sql --file=./backups/mekong-db-$(date +%Y%m%d).sql
```

**Backup Verification:**
```bash
# Restore to local DB and verify
wrangler d1 execute mekong-db --local --file=./backups/mekong-db-$(date +%Y%m%d).sql

# Run verification queries
wrangler d1 execute mekong-db --local --command "SELECT COUNT(*) FROM tenants;"
wrangler d1 execute mekong-db --local --command "SELECT COUNT(*) FROM missions WHERE status='completed';"
```

### 2.2 KV Cache Backups

KV cache is **ephemeral** and can be rebuilt from D1. No backup required.

### 2.3 R2 Bucket Backups

**Enable Versioning:**
```bash
wrangler r2 bucket update mekong-storage --versioning enabled
```

**Cross-Region Replication (Optional):**
Configure R2 bucket replication to a secondary region for disaster recovery.

### 2.4 Secrets Backup

**Store secrets in a secure password manager (1Password/LastPass):**

| Secret Name | Description | Rotation Frequency |
|-------------|-------------|-------------------|
| `SERVICE_TOKEN` | Internal service auth | Quarterly |
| `POLAR_WEBHOOK_SECRET` | Polar.sh webhook verification | Quarterly |
| `LLM_API_KEY` | Default LLM provider key | Quarterly |
| `DATABASE_URL` | External DB connection (if used) | Quarterly |

---

## 3. Disaster Recovery Procedures

### 3.1 Scenario: Database Corruption

**Symptoms:**
- Queries failing with constraint errors
- Missing tables or data
- Inconsistent query results

**Recovery Steps:**

```bash
# Step 1: Assess damage
wrangler d1 execute mekong-db --command "SELECT name FROM sqlite_master WHERE type='table';"

# Step 2: Identify last good backup
ls -la ./backups/

# Step 3: Create new D1 database
wrangler d1 create mekong-db-recovery

# Step 4: Restore from backup
wrangler d1 execute mekong-db-recovery --file=./backups/mekong-db-YYYYMMDD.sql

# Step 5: Verify restoration
wrangler d1 execute mekong-db-recovery --command "SELECT COUNT(*) FROM tenants;"

# Step 6: Update Worker binding to recovery DB
# In Cloudflare Dashboard: Workers → mekong-engine → Settings → D1 Bindings
# Change DB binding from mekong-db to mekong-db-recovery

# Step 7: Redeploy Worker
wrangler deploy

# Step 8: Verify service health
curl -s https://mekong-engine.agencyos-openclaw.workers.dev/health | jq
```

### 3.2 Scenario: Worker Deployment Failure

**Symptoms:**
- 500 errors on all endpoints
- Worker not responding
- Deployment errors in Cloudflare Dashboard

**Recovery Steps:**

```bash
# Step 1: Check deployment status
wrangler deploy --dry-run

# Step 2: Rollback to previous deployment
# In Cloudflare Dashboard: Workers → mekong-engine → Deployments
# Click "Rollback" on last known good version

# Step 3: Alternatively, redeploy from last good commit
git checkout <last-good-commit>
wrangler deploy

# Step 4: Verify health
curl -s https://mekong-engine.agencyos-openclaw.workers.dev/health | jq
```

### 3.3 Scenario: Secret Rotation Required

**Triggers:**
- Suspected key leakage
- Quarterly rotation schedule
- Employee departure

**Rotation Steps:**

```bash
# Step 1: Generate new secret
export NEW_SERVICE_TOKEN=$(openssl rand -hex 32)

# Step 2: Update Cloudflare Secrets
wrangler secret put SERVICE_TOKEN
# Paste new token when prompted

# Step 3: Update all dependent services
# Update internal services that use SERVICE_TOKEN

# Step 4: Rotate other secrets as needed
wrangler secret put POLAR_WEBHOOK_SECRET
wrangler secret put LLM_API_KEY

# Step 5: Verify service still works
curl -s https://mekong-engine.agencyos-openclaw.workers.dev/health | jq
```

### 3.4 Scenario: Regional Outage

**Symptoms:**
- Cloudflare region experiencing issues
- High latency or timeouts from specific regions

**Recovery Steps:**

1. **Cloudflare Workers are automatically multi-region** - no action required
2. **For D1:** Failover to replica region (if configured)
3. **Monitor Cloudflare Status:** https://www.cloudflarestatus.com/

---

## 4. Monitoring & Alerting

### 4.1 Health Check Endpoints

```bash
# Health check (should return 200)
curl -s https://mekong-engine.agencyos-openclaw.workers.dev/health

# Metrics endpoint (Prometheus format)
curl -s https://mekong-engine.agencyos-openclaw.workers.dev/metrics \
  -H "Authorization: Bearer $SERVICE_TOKEN"
```

### 4.2 Uptime Monitoring

Configure external monitoring:

| Provider | URL | Check Interval | Alert Threshold |
|----------|-----|----------------|-----------------|
| Better Uptime | `/health` | 1 min | 3 consecutive failures |
| Uptime Robot | `/health` | 5 min | 1 failure |

### 4.3 Alert Configuration

**Error Rate Alert:**
- Trigger: Error rate > 1% over 5 minutes
- Action: Slack notification to #alerts
- Escalation: PagerDuty after 15 minutes

**Latency Alert:**
- Trigger: p99 latency > 1000ms over 10 minutes
- Action: Slack notification to #alerts

**Downtime Alert:**
- Trigger: Health check fails 3 consecutive times
- Action: SMS + Slack + PagerDuty

---

## 5. Recovery Drill Schedule

| Drill Type | Frequency | Duration | Owner |
|------------|-----------|----------|-------|
| Database restore | Quarterly | 2 hours | CTO |
| Worker rollback | Monthly | 30 minutes | Lead Dev |
| Secret rotation | Quarterly | 1 hour | Security |
| Full DR simulation | Bi-annually | 4 hours | CTO |

### 5.1 Drill Checklist

- [ ] Schedule drill with team
- [ ] Document baseline metrics
- [ ] Execute recovery procedure
- [ ] Measure actual RTO/RPO
- [ ] Compare against targets
- [ ] Document lessons learned
- [ ] Update runbook if needed

---

## 6. Emergency Contacts

| Role | Name | Contact | Escalation |
|------|------|---------|------------|
| On-Call Engineer | [Name] | [Phone/Slack] | Primary |
| Lead Developer | [Name] | [Phone/Slack] | Secondary |
| CTO | OpenClaw | [Slack] | Final |

---

## 7. Post-Incident Review

After any disaster recovery event:

1. **Within 24 hours:** Conduct blameless post-mortem
2. **Document:** What happened, timeline, actions taken
3. **Identify:** Root cause, contributing factors
4. **Action items:** Prevent recurrence, improve processes
5. **Share:** Post-mortem with team

### 7.1 Post-Mortem Template

```markdown
# Incident Post-Mortem

**Date:** YYYY-MM-DD
**Duration:** X hours Y minutes
**Severity:** P0/P1/P2/P3

## Summary
[Brief description of what happened]

## Timeline
- HH:MM - Incident started
- HH:MM - Detected
- HH:MM - Response began
- HH:MM - Mitigation applied
- HH:MM - Service restored

## Root Cause
[Technical root cause]

## Contributing Factors
- [Factor 1]
- [Factor 2]

## Action Items
- [ ] Prevent recurrence: ...
- [ ] Improve detection: ...
- [ ] Update runbook: ...

## Lessons Learned
- [Lesson 1]
- [Lesson 2]
```

---

## 8. Appendix: Recovery Commands Quick Reference

```bash
# Database export
wrangler d1 export mekong-db --output=./backup.sql

# Database restore
wrangler d1 execute mekong-db --file=./backup.sql

# Deploy Worker
wrangler deploy

# Check deployment status
wrangler deployments list

# Rotate secret
wrangler secret put SECRET_NAME

# Health check
curl https://mekong-engine.agencyos-openclaw.workers.dev/health

# Get metrics
curl https://mekong-engine.agencyos-openclaw.workers.dev/metrics -H "Authorization: Bearer $TOKEN"
```

---

**Document Owner:** CTO
**Review Frequency:** Quarterly
**Next Review:** 2026-06-20
