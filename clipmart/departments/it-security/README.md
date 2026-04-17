# IT Security Department as a Service

> Replace an IT security team with AI agents that run security scans, manage endpoints, and respond to incidents — 24/7.

## Value Proposition

| What you replace | Annual cost | What you pay |
|-----------------|-------------|--------------|
| IT Security Engineer ($150k) | $150,000/yr | $49/mo floor |
| CrowdStrike / endpoint tools | $12,000/yr | $4/action |
| Snyk / security scanning | $4,800/yr | Included |
| **Total replaced** | **$166,800/yr** | **~$2,400/yr** |

## What This Department Does

1. **Security Scanning** — Dependency vulnerabilities, SAST, secret detection, DAST
2. **Endpoint Management** — Compliance checks, patching coordination, inventory
3. **Service Desk** — IT tickets: access requests, password resets, SaaS provisioning
4. **IT Inventory** — Hardware/software asset tracking, license audits
5. **Incident Response** — Alert triage, containment recommendations, post-mortems

## Outcome-Based Pricing

| Deliverable | Price |
|------------|-------|
| Security scan + report | $20 |
| Endpoint compliance check | $8 |
| Service ticket resolved | $5 |
| IT inventory audit | $15 |
| Incident response report | $25 |

**Monthly floor:** $49.

## Included Commands

```bash
mekong security-scan    # Security vulnerability scan
mekong it-endpoint      # Endpoint management
mekong it-inventory     # IT inventory audit
mekong it-service       # IT service desk ticket
mekong audit-compliance # Compliance audit
```

## Install

```bash
mekong install dept-it-security
```

## Configuration

```bash
# .mekong/.env.dept-it-security
DEPT_IT_MDM=jamf  # jamf|intune|kandji
DEPT_IT_MDM_API_KEY=your_key
DEPT_IT_IDENTITY=okta  # okta|azure-ad|google-workspace
DEPT_IT_IDENTITY_API_KEY=your_key
DEPT_IT_GITHUB_TOKEN=your_token  # for secret scanning
DEPT_IT_SNYK_TOKEN=your_token    # for dep scanning
DEPT_IT_ALERT_CHANNEL=slack
```

## Comparison

| Metric | IT Security Team | IT Security Dept SaS |
|--------|-----------------|----------------------|
| Annual cost | $150,000+ | $49 floor |
| Scan frequency | Weekly | On-commit + daily |
| Incident response | Business hours | 24/7 |
| Mean time to detect | Hours | Minutes |
