# DevOps Department as a Service

> Replace a DevOps/platform engineer with AI agents that manage CI/CD, infra provisioning, and rollbacks.

## Value Proposition

| What you replace | Annual cost | What you pay |
|-----------------|-------------|--------------|
| DevOps Engineer ($170k) | $170,000/yr | $49/mo floor |
| Infrastructure tools | $12,000/yr | Included |
| **Total replaced** | **$182,000/yr** | **~$2,400/yr** |

## What This Department Does

1. **CI/CD Pipeline Management** — GitHub Actions workflows, deploy gates, notifications
2. **Infrastructure Provisioning** — Cloudflare Workers, Pages, D1, KV, R2 setup
3. **Rollback Execution** — Zero-downtime rollbacks with health check validation
4. **Network Topology** — CDN configuration, routing optimization, DDoS settings
5. **Regional Expansion** — Multi-region deploy orchestration

## Outcome-Based Pricing

| Deliverable | Price |
|------------|-------|
| CI/CD pipeline deploy | $6 |
| Rollback executed | $5 |
| Infra region provisioned | $20 |
| Network topology optimization | $15 |
| Infra gateway configuration | $12 |

**Monthly floor:** $49.

## Included Commands

```bash
mekong devops-deploy-pipeline   # CI/CD pipeline deployment
mekong devops-rollback          # Execute rollback
mekong deploy                   # Deploy application
mekong infra-gateway            # API gateway configuration
mekong infra-network            # Network topology management
mekong infra-optimize           # Infra cost + performance optimization
mekong infra-region             # Regional provisioning
mekong infra-topology           # Topology planning
```

## Install

```bash
mekong install dept-devops
```

## Configuration

```bash
# .mekong/.env.dept-devops
DEPT_DEVOPS_PLATFORM=cloudflare  # cloudflare|vercel|aws
DEPT_DEVOPS_CF_API_TOKEN=your_token
DEPT_DEVOPS_CF_ACCOUNT_ID=your_account_id
DEPT_DEVOPS_GITHUB_TOKEN=your_github_token
DEPT_DEVOPS_REPO=org/repo
DEPT_DEVOPS_PROD_BRANCH=main
```
