# BizOps Department as a Service

> Replace a BizOps manager with AI agents that run revenue operations, quarterly reviews, and cross-functional coordination.

## Value Proposition

| What you replace | Annual cost | What you pay |
|-----------------|-------------|--------------|
| BizOps Manager ($120k) | $120,000/yr | $49/mo floor |
| RevOps tools | $12,000/yr | Included |
| **Total replaced** | **$132,000/yr** | **~$1,200/yr** |

## What This Department Does

1. **Revenue Operations** — CRM hygiene, pipeline analysis, forecast accuracy
2. **Quarterly Business Reviews** — Cross-functional QBR packs with metrics + narrative
3. **Hiring Sprints** — Coordinate recruiting across departments, headcount planning
4. **Operational Reporting** — Weekly business health reports across all functions
5. **Business Campaigns** — Coordinate launches across sales, marketing, product

## Outcome-Based Pricing

| Deliverable | Price |
|------------|-------|
| Quarterly business review | $40 |
| Revenue ops dashboard build | $30 |
| Hiring sprint coordination | $25 |
| Weekly business report | $12 |
| Campaign launch coordination | $20 |

**Monthly floor:** $49.

## Included Commands

```bash
mekong business-quarterly-review   # QBR preparation
mekong business-revenue-engine     # Revenue operations
mekong business-report             # Business health report
mekong business-hiring-sprint      # Hiring sprint coordination
mekong business-campaign-launch    # Cross-functional campaign launch
mekong business-client-onboard     # Client onboarding coordination
```

## Install

```bash
mekong install dept-bizops
```

## Configuration

```bash
# .mekong/.env.dept-bizops
DEPT_BIZOPS_PM_TOOL=linear  # linear|jira|asana
DEPT_BIZOPS_COMMS=slack
DEPT_BIZOPS_DOCS=notion
DEPT_BIZOPS_QBR_CADENCE=quarterly
DEPT_BIZOPS_REPORT_CADENCE=weekly
```
