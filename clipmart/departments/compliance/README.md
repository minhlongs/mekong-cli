# Compliance Department as a Service

> Replace a $50k/yr compliance officer with AI agents that run SOX, SOC2, ITGC, and continuous compliance monitoring.

## Value Proposition

| What you replace | Annual cost | What you pay |
|-----------------|-------------|--------------|
| Compliance Officer ($120k) | $120,000/yr | $49/mo floor |
| Vanta / Drata | $15,000/yr | $5/control |
| External audit prep | $30,000/yr | Included |
| **Total replaced** | **$165,000/yr** | **~$3,600/yr** |

## What This Department Does

1. **SOC2 Readiness** — Evidence collection, gap analysis, control testing
2. **SOX Compliance** — Quarterly SOX cycles, ITGC testing, attestation prep
3. **Continuous Monitoring** — Real-time control checks, drift detection, alerts
4. **Audit Trail** — Immutable audit logs, evidence archiving, reviewer reports
5. **Compliance Calendar** — Automated scheduling of all compliance activities

## Outcome-Based Pricing

| Deliverable | Price |
|------------|-------|
| SOC2 readiness assessment | $80 |
| SOX cycle run | $50 |
| ITGC control test | $20 |
| Audit trail report | $15 |
| Compliance check (single control) | $5 |
| SOC2 evidence pack | $100 |

**Monthly floor:** $49.

## Included Commands

```bash
mekong compliance-check         # Individual control check
mekong compliance-monitor       # Continuous compliance monitoring
mekong compliance-soc2-prep     # SOC2 readiness prep
mekong compliance-sox-cycle     # SOX cycle execution
mekong audit-compliance         # Compliance audit
mekong audit-execute            # Audit execution
mekong audit-itgc               # ITGC testing
mekong audit-plan               # Audit planning
mekong audit-report             # Audit reporting
mekong audit-sox                # SOX-specific audit
mekong audit-trail              # Audit trail management
```

## Install

```bash
mekong install dept-compliance
```

## Configuration

```bash
# .mekong/.env.dept-compliance
DEPT_COMPLIANCE_FRAMEWORKS=soc2,sox  # comma-separated
DEPT_COMPLIANCE_GDPR=true
DEPT_COMPLIANCE_CCPA=true
DEPT_COMPLIANCE_EVIDENCE_STORE=notion  # notion|google-drive|s3
DEPT_COMPLIANCE_AUDIT_FREQUENCY=quarterly
DEPT_COMPLIANCE_SLACK_ALERTS=true
```

## Comparison

| Metric | Compliance Officer | Compliance Dept SaS |
|--------|------------------|---------------------|
| Annual cost | $120,000+ | $49 floor |
| Control coverage | Manual | 100% automated |
| Evidence freshness | Quarterly | Continuous |
| SOC2 prep time | 6-9 months | 8-12 weeks |
