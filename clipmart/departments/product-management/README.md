# Product Management Department as a Service

> Replace a senior PM ($180k/yr) with AI agents that run discovery, sprint planning, competitive intel, and feature launches.

## Value Proposition

| What you replace | Annual cost | What you pay |
|-----------------|-------------|--------------|
| Senior PM ($180k) | $180,000/yr | $49/mo floor |
| ProductBoard | $6,000/yr | Included |
| Competitive intel tools | $3,600/yr | Included |
| **Total replaced** | **$189,600/yr** | **~$1,200/yr** |

## What This Department Does

1. **Sprint Planning** — Break down epics into tickets, estimate, sequence, assign
2. **Product Discovery** — User interview synthesis, opportunity sizing, hypothesis testing
3. **Competitive Intelligence** — Monitor competitors, feature gap analysis, win/loss
4. **Feature Launches** — Launch checklists, internal comms, external messaging
5. **Retrospectives** — Sprint retros with action items, velocity tracking

## Outcome-Based Pricing

| Deliverable | Price |
|------------|-------|
| Sprint plan + ticket breakdown | $20 |
| Feature launch checklist + comms | $15 |
| Competitive intelligence report | $25 |
| Product retrospective | $12 |
| Discovery synthesis (5 interviews) | $30 |

**Monthly floor:** $49.

## Included Commands

```bash
mekong product-sprint-plan        # Sprint planning workflow
mekong product-discovery          # Discovery synthesis
mekong product-launch-feature     # Feature launch orchestration
mekong product-competitive-intel  # Competitive analysis
mekong product-retrospective      # Sprint retrospective
```

## Install

```bash
mekong install dept-product-management
```

## Configuration

```bash
# .mekong/.env.dept-product-management
DEPT_PM_TOOL=linear  # linear|jira|notion
DEPT_PM_API_KEY=your_key
DEPT_PM_SPRINT_LENGTH_DAYS=14
DEPT_PM_COMPETITORS=competitor1.com,competitor2.com
DEPT_PM_TEAM_SIZE=5
```
