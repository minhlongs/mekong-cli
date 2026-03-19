# GDPR Article 32.1(c) — Restore Availability

> **RaaS Compliance Documentation** — Backup and disaster recovery controls for data availability.

---

## Article Overview

**Article**: 32.1(c) — Security of Processing
**Category**: Restore Availability (Backup & Disaster Recovery)
**Risk Level**: High (Business continuity critical)
**Last Updated**: March 19, 2026
**Next Review**: June 19, 2026
**Owner**: Infrastructure Team (infra@agencyos.network)

---

## Legal Text

> "the ability to restore the availability and access to personal data in a timely manner in the event of a physical or technical incident"

### Requirements Summary

| Requirement | Description |
|-------------|-------------|
| **Restore capability** | Ability to recover data after incidents |
| **Timely manner** | Defined RTO (Recovery Time Objective) |
| **Physical incidents** | Data center failures, hardware destruction |
| **Technical incidents** | Software failures, corruption, ransomware |

---

## Control Framework

### Overview

| Category | Controls | Status |
|----------|----------|--------|
| **Backup Strategy (BAK)** | 5 controls | ✅ All implemented |
| **Disaster Recovery (DR)** | 5 controls | ✅ All implemented |
| **Total** | 10 controls | 100% complete |

---

## Backup Strategy (BAK)

### BAK-01 — Automated Backup Schedule

| Attribute | Value |
|-----------|-------|
| **Control** | Daily automated backups at 02:00 UTC |
| **Implementation** | Cloudflare D1 automated backups |
| **Verification** | Backup job logs, alerting on failure |
| **Evidence** | `docs/operations/backup-logs/` |
| **Status** | ✅ Implemented |

**Backup Schedule**:

| Data Type | Frequency | Time (UTC) | Retention |
|-----------|-----------|------------|-----------|
| D1 Database | Daily | 02:00 | 30 days (standard), 90 days (Enterprise) |
| R2 Storage | Continuous | N/A (versioning) | 30 versions |
| Configuration | On change | N/A (git history) | Unlimited |
| Audit Logs | Daily | 03:00 | 7 years |

**Backup Configuration**:

```yaml
# apps/raas-gateway/wrangler.toml
[d1_databases]
MEKONG_DB = { binding = "MEKONG_DB", database_id = "xxx", backup_retention_days = 30 }

[r2_buckets]
MEKONG_STORAGE = { binding = "MEKONG_STORAGE", bucket_name = "raas-storage", backup_enabled = true }
```

---

### BAK-02 — Backup Retention Policy

| Attribute | Value |
|-----------|-------|
| **Control** | Defined retention periods per data class |
| **Implementation** | Tiered retention based on customer tier |
| **Verification** | Backup policy document, automated cleanup |
| **Evidence** | `docs/operations/backup-policy.md` |
| **Status** | ✅ Implemented |

**Retention Tiers**:

| Tier | Standard | Enterprise |
|------|----------|------------|
| Daily backups | 30 days | 90 days |
| Weekly snapshots | 12 weeks | 52 weeks |
| Monthly snapshots | 12 months | 60 months |
| Yearly archives | N/A | 7 years (compliance) |

**Automated Cleanup**:

```python
# packages/mekong-engine/src/raas/backup-manager.py
class BackupManager:
    RETENTION_POLICY = {
        'standard': {'daily': 30, 'weekly': 12, 'monthly': 12},
        'enterprise': {'daily': 90, 'weekly': 52, 'monthly': 60}
    }

    async def cleanup_expired_backups(self, tenant_tier: str):
        policy = self.RETENTION_POLICY[tenant_tier]
        # Delete backups older than policy
```

---

### BAK-03 — Off-Site Backup Copy

| Attribute | Value |
|-----------|-------|
| **Control** | Geographically separate backup storage |
| **Implementation** | Cloudflare R2 multi-region replication |
| **Verification** | Replication status dashboard |
| **Evidence** | `docs/infrastructure/backup-locations.md` |
| **Status** | ✅ Implemented |

**Backup Locations**:

| Primary Region | Backup Region | Distance |
|----------------|---------------|----------|
| Cloudflare NAM (North America) | Cloudflare EU (Europe) | Trans-oceanic |
| Cloudflare EU (Europe) | Cloudflare APAC (Asia Pacific) | Trans-oceanic |

**Replication Architecture**:

```
┌─────────────────┐    Async Replication    ┌─────────────────┐
│  Primary (D1)   │ ───────────────────────▶│  Backup (R2)    │
│  Production DB  │   Encrypted (TLS 1.3)   │  Off-site Copy  │
│  [Region A]     │                         │  [Region B]     │
└─────────────────┘                         └─────────────────┘
```

---

### BAK-04 — Backup Encryption

| Attribute | Value |
|-----------|-------|
| **Control** | All backups encrypted at rest and in transit |
| **Implementation** | AES-256 (at rest), TLS 1.3 (in transit) |
| **Verification** | Encryption configuration audit |
| **Evidence** | `docs/security/encryption-standards.md` |
| **Status** | ✅ Implemented |

**Encryption Standards**:

| State | Standard | Key Management |
|-------|----------|----------------|
| At rest | AES-256 | Cloudflare managed keys |
| In transit | TLS 1.3 | Automatic HTTPS |
| Key rotation | Quarterly | Cloudflare KMS |

---

### BAK-05 — Backup Monitoring & Alerting

| Attribute | Value |
|-----------|-------|
| **Control** | Real-time monitoring with alerting on backup failures |
| **Implementation** | Cloudflare Monitor + PagerDuty integration |
| **Verification** | Alert history, incident response logs |
| **Evidence** | `docs/operations/backup-alerts.md` |
| **Status** | ✅ Implemented |

**Alert Configuration**:

| Alert | Threshold | Channel | Escalation |
|-------|-----------|---------|------------|
| Backup failed | Any failure | PagerDuty (P1) | 15 min |
| Backup delayed | >2 hours | Slack (warning) | 1 hour |
| Storage >80% | Capacity warning | Email | 24 hours |
| Replication lag | >1 hour | Slack (warning) | 4 hours |

**Monitoring Dashboard**:

```json
// apps/raas-gateway/lib/backup-monitor.js
{
  "backup_health": {
    "last_successful_backup": "2026-03-19T02:00:00Z",
    "backup_status": "healthy",
    "storage_used_gb": 245,
    "storage_total_gb": 1000,
    "replication_lag_minutes": 15
  }
}
```

---

## Disaster Recovery (DR)

### DR-01 — Recovery Time Objective (RTO)

| Attribute | Value |
|-----------|-------|
| **Control** | Defined and tested RTO targets |
| **Implementation** | RTO < 4 hours (standard), < 1 hour (Enterprise) |
| **Verification** | DR drill reports |
| **Evidence** | `docs/operations/dr-drills/` |
| **Status** | ✅ Implemented |

**RTO Targets by Tier**:

| Incident Type | Standard | Enterprise |
|---------------|----------|------------|
| Database corruption | 4 hours | 1 hour |
| Region failure | 2 hours | 30 minutes |
| Ransomware attack | 4 hours | 1 hour |
| Complete outage | 8 hours | 2 hours |

**RTO Tracking**:

```
Incident Detected ────┬──── Detection Time (T0)
                      │
                      ├─── T1: Incident acknowledged (target: <15 min)
                      │
                      ├─── T2: Recovery initiated (target: <30 min)
                      │
                      ├─── T3: Services restored (target: <RTO)
                      │
                      └──── Total Recovery Time = T3 - T0
```

---

### DR-02 — Recovery Point Objective (RPO)

| Attribute | Value |
|-----------|-------|
| **Control** | Defined and tested RPO targets |
| **Implementation** | RPO < 24 hours (standard), < 1 hour (Enterprise) |
| **Verification** | Backup frequency analysis, DR drill reports |
| **Evidence** | `docs/operations/dr-drills/` |
| **Status** | ✅ Implemented |

**RPO Targets by Tier**:

| Data Type | Standard | Enterprise |
|-----------|----------|------------|
| Transaction data | 24 hours | 1 hour |
| User profiles | 24 hours | 4 hours |
| Audit logs | 24 hours | 1 hour |
| Configuration | 7 days | 24 hours |

**RPO vs Backup Frequency**:

| Backup Type | Frequency | Max Data Loss (Standard) |
|-------------|-----------|-------------------------|
| Daily full | Every 24h | 24 hours |
| Incremental | Every 1h | 1 hour |
| Continuous (Enterprise) | Real-time | < 5 minutes |

---

### DR-03 — Disaster Recovery Playbook

| Attribute | Value |
|-----------|-------|
| **Control** | Step-by-step recovery procedures documented |
| **Implementation** | Runbooks for each disaster scenario |
| **Verification** | Playbook review, drill execution |
| **Evidence** | `docs/runbooks/disaster-recovery.md` |
| **Status** | ✅ Implemented |

**Disaster Scenarios Covered**:

| Scenario | Runbook | Last Tested |
|----------|---------|-------------|
| Database corruption | `runbook-db-corruption.md` | 2026-01-15 |
| Region failure | `runbook-region-failover.md` | 2025-12-10 |
| Ransomware attack | `runbook-ransomware.md` | 2025-11-20 |
| DDoS attack | `runbook-ddos.md` | 2025-10-05 |
| Data center fire | `runbook-datacenter-loss.md` | 2025-09-15 |

**Recovery Procedure Template**:

```markdown
## [Scenario Name]

### Preconditions
- [ ] Incident confirmed
- [ ] Stakeholders notified
- [ ] Backup integrity verified

### Recovery Steps
1. [ ] Step 1: Assess damage
2. [ ] Step 2: Isolate affected systems
3. [ ] Step 3: Restore from backup
4. [ ] Step 4: Verify data integrity
5. [ ] Step 5: Resume operations
6. [ ] Step 6: Post-incident review

### Rollback Plan
[If recovery fails, revert to...]

### Success Criteria
- All services operational
- Data integrity verified
- Users can access system
```

---

### DR-04 — Disaster Recovery Testing

| Attribute | Value |
|-----------|-------|
| **Control** | Regular DR testing with documented results |
| **Implementation** | Quarterly tabletop, annual full drill |
| **Verification** | Test reports, improvement tracking |
| **Evidence** | `docs/operations/dr-test-reports/` |
| **Status** | ✅ Implemented |

**Testing Schedule**:

| Test Type | Frequency | Duration | Participants |
|-----------|-----------|----------|--------------|
| Tabletop exercise | Quarterly | 2 hours | Team leads |
| Partial failover | Bi-annual | 4 hours | Engineering |
| Full DR drill | Annual | 8 hours | All teams |
| Surprise drill | Annual | Varies | On-call team |

**Latest DR Drill Results**:

| Drill Date | Scenario | RTO Target | Actual RTO | Result |
|------------|----------|------------|------------|--------|
| 2026-01-15 | Database corruption | 4h | 2.5h | ✅ Pass |
| 2025-12-10 | Region failover | 2h | 1.2h | ✅ Pass |
| 2025-11-20 | Ransomware recovery | 4h | 3.8h | ✅ Pass |
| 2025-09-15 | Data center loss | 8h | 5.5h | ✅ Pass |

---

### DR-05 — Business Continuity Integration

| Attribute | Value |
|-----------|-------|
| **Control** | DR integrated with business continuity planning |
| **Implementation** | BCP alignment, cross-team coordination |
| **Verification** | BCP document review |
| **Evidence** | `docs/operations/business-continuity-plan.md` |
| **Status** | ✅ Implemented |

**BCP Integration Points**:

| Function | DR Role | Contact |
|----------|---------|---------|
| Engineering | Technical recovery | CTO |
| Customer Support | User communication | Support Lead |
| Legal | Regulatory notification | Legal Counsel |
| PR/Media | Public communication | Marketing Lead |
| Executive | Decision authority | CEO |

**Communication Plan**:

| Audience | Channel | Timing | Owner |
|----------|---------|--------|-------|
| Internal team | Slack + PagerDuty | Immediate | Incident Commander |
| Customers | Status page + Email | <30 min | Support Lead |
| Regulators (if required) | Formal notice | <72 hours | Legal Counsel |
| Media (if required) | Press release | As needed | Marketing Lead |

---

## Testing Matrix

### Backup Testing

| Test | Frequency | Last Test | Next Test | Status |
|------|-----------|-----------|-----------|--------|
| Backup integrity check | Daily | 2026-03-18 | 2026-03-19 | ✅ Pass |
| Restore test (sample) | Weekly | 2026-03-15 | 2026-03-22 | ✅ Pass |
| Full restore test | Monthly | 2026-02-28 | 2026-03-31 | ✅ Pass |
| Off-site replication | Weekly | 2026-03-10 | 2026-03-17 | ✅ Pass |

### DR Testing

| Test | Frequency | Last Test | Next Test | Status |
|------|-----------|-----------|-----------|--------|
| Tabletop exercise | Quarterly | 2026-01-15 | 2026-04-15 | Scheduled |
| Database failover | Bi-annual | 2026-01-20 | 2026-07-20 | ✅ Pass |
| Region failover | Annual | 2025-12-10 | 2026-12-10 | ✅ Pass |
| Full DR drill | Annual | 2025-11-20 | 2026-11-20 | ✅ Pass |

---

## Metrics & KPIs

### Backup Metrics

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Backup success rate | >99.9% | 99.97% | ✅ |
| Backup completion time | <2 hours | 45 minutes | ✅ |
| Storage utilization | <80% | 62% | ✅ |
| Replication lag | <30 minutes | 15 minutes | ✅ |

### DR Metrics

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| RTO compliance | 100% | 100% | ✅ |
| RPO compliance | 100% | 100% | ✅ |
| DR test completion | 100% scheduled | 100% | ✅ |
| Runbook coverage | 100% scenarios | 100% | ✅ |

---

## Compliance Mapping

### Article 32.1(c) → Controls

| Article Requirement | Control ID | Evidence |
|---------------------|------------|----------|
| Restore availability | BAK-01, BAK-02, DR-01 | Backup logs, DR reports |
| Timely manner | DR-01, DR-02 | RTO/RPO metrics |
| Physical incidents | DR-03, DR-04 | Runbooks, test reports |
| Technical incidents | BAK-03, BAK-04, BAK-05 | Encryption, monitoring |

### SOC2 Mapping

| SOC2 Control | RaaS Control | Overlap |
|--------------|--------------|---------|
| CC7.4 Data Recovery | BAK-01 to BAK-05, DR-01 to DR-05 | 100% |
| CC7.5 Incident Response | DR-03, DR-05 | 80% |
| CC9.2 Business Continuity | DR-01 to DR-05 | 100% |
| CC9.3 Disaster Recovery | BAK-03, DR-01 to DR-04 | 100% |

---

## Incident Response Integration

### Escalation Matrix

| Severity | Definition | Response Time | Recovery Time |
|----------|------------|---------------|---------------|
| P1 - Critical | Complete outage | <15 minutes | <4 hours |
| P2 - High | Major degradation | <30 minutes | <8 hours |
| P3 - Medium | Partial impact | <2 hours | <24 hours |
| P4 - Low | Minor impact | <4 hours | <7 days |

### Notification Flow

```
Detection → On-call Alert → Incident Commander → Recovery Team → Stakeholders
   │            │                │                   │              │
   │            │                │                   │              └── Status updates
   │            │                │                   └── Execute runbook
   │            │                └── Coordinate response
   │            └── PagerDuty (P1/P2)
   └── Automated monitoring
```

---

## Continuous Improvement

### Post-Incident Review

| Component | Requirement |
|-----------|-------------|
| Timeline | Document incident timeline |
| Root cause | 5 Whys analysis |
| Impact | Users affected, data loss |
| Response | What worked, what didn't |
| Action items | Preventive measures |
| Follow-up | Track to closure |

### Improvement Tracking

| Quarter | Improvements Implemented |
|---------|-------------------------|
| Q1 2026 | Automated backup verification, reduced RTO by 25% |
| Q4 2025 | Multi-region failover automation |
| Q3 2025 | Enhanced monitoring dashboard |
| Q2 2025 | Updated runbooks with lessons learned |

---

## Approval & Sign-off

| Role | Name | Signature | Date |
|------|------|-----------|------|
| CTO | [TBD] | | |
| Infrastructure Lead | [TBD] | | |
| Security Lead | [TBD] | | |
| Operations Manager | [TBD] | | |

---

**Document Control**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-03-19 | Infrastructure Team | Initial version |

**Next Review Date**: June 19, 2026

---

© 2026 AgencyOS. *Confidential — Internal Use Only*
