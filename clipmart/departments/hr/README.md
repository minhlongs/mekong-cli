# HR Department as a Service

> Replace an HR manager with AI agents. Onboard employees, run performance cycles, and manage policies — for less than Gusto's per-seat fee.

## Value Proposition

| What you replace | Annual cost | What you pay |
|-----------------|-------------|--------------|
| HR Manager ($90k) | $90,000/yr | $49/mo floor |
| Gusto ($12/person/mo × 20 people) | $2,880/yr | $3/action |
| BambooHR | $1,800/yr | Included |
| **Total replaced** | **$94,680/yr** | **~$1,200/yr** |

## What This Department Does

1. **Employee Onboarding** — 30-60-90 day plans, tool provisioning checklists, buddy assignments
2. **Performance Cycles** — 360 reviews, calibration prep, rating distributions
3. **HR Policy Management** — Policy drafts, annual updates, employee handbook sections
4. **Review Coordination** — Annual review scheduling, self-review templates, manager guides
5. **Offboarding** — Checklist, knowledge transfer, exit interview scheduling

## Outcome-Based Pricing

| Deliverable | Price |
|------------|-------|
| Employee onboarding package | $15 |
| Performance review cycle run | $20 |
| HR policy document | $12 |
| Annual review coordination (team) | $25 |
| Offboarding checklist | $10 |

**Monthly floor:** $49.

## Included Commands

```bash
mekong hr-onboard           # Employee onboarding workflow
mekong hr-performance-cycle # Performance review cycle
mekong hr-policy            # Policy document management
mekong hr-review            # Review coordination
mekong hr-recruit           # Recruiting integration
mekong business-hiring-sprint # Hiring sprint coordination
```

## Install

```bash
mekong install dept-hr
```

## Configuration

```bash
# .mekong/.env.dept-hr
DEPT_HR_HRIS=bamboohr  # bamboohr|rippling|gusto
DEPT_HR_HRIS_API_KEY=your_key
DEPT_HR_COMPANY_SIZE=20
DEPT_HR_REVIEW_CYCLE=annual  # annual|semi-annual
DEPT_HR_ONBOARDING_LENGTH_DAYS=90
DEPT_HR_SLACK_WORKSPACE=your_workspace
```
