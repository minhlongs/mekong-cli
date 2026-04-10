---
description: How to implement churn prevention and client retention strategies
---

# 🔄 Retention Plays Workflow

Implement proven retention strategies to reduce churn and maximize LTV.

## 🤖 Quick Execute
```bash
Execute workflow: https://mekongmind.com/docs/workflows/retention-plays
```

## ⚡ Step-by-Step Execution

### Step 1: Audit Current Churn (5 min)
// turbo
```bash
# Analyze client retention metrics
mekong analytics:churn --period 12m

# Expected output:
# ┌─────────────────────────────────┐
# │ Churn Rate: X%                  │
# │ At-Risk Clients: N              │
# │ NRR (Net Revenue Retention): X% │
# └─────────────────────────────────┘
```

### Step 2: Segment At-Risk Clients (3 min)
// turbo
```bash
# Identify clients with low engagement
mekong crm:segment --filter "engagement<50"

# Risk factors:
# - No contact in 30+ days
# - Declining usage
# - Payment delays
# - Support tickets spike
```

### Step 3: Configure Health Scoring (3 min)
// turbo
```bash
# Apply health score model
mekong retention:health-score --enable

# Health Score Factors:
# - Feature usage: 30%
# - Support satisfaction: 25%
# - Payment history: 25%
# - Communication frequency: 20%
```

### Step 4: Deploy Retention Plays (5 min)
// turbo
```bash
# Activate automated retention workflows
mekong retention:activate --plays all

# Available Plays:
# 1. win-back - Re-engage dormant clients
# 2. upsell - Expand successful accounts
# 3. qbr - Quarterly business reviews
# 4. nps-follow - Act on detractor feedback
```

### Step 5: Schedule QBR Cadence (2 min)
// turbo
```bash
# Set quarterly review schedule
mekong calendar:qbr --frequency quarterly --auto-schedule

# Expected: ✅ QBR meetings auto-scheduled
```

## 📋 Retention Play Templates

### Health Score Thresholds
```yaml
health_scoring:
  healthy: 80-100    # Green: nurture and upsell
  at_risk: 50-79     # Yellow: proactive outreach
  critical: 0-49     # Red: urgent intervention
```

### Win-Back Email Sequence
```yaml
win_back_sequence:
  day_1: "We miss you" - Personal check-in
  day_7: Value reminder - Recent wins
  day_14: Special offer - Loyalty discount
  day_30: Exit interview - Learn why
```

## ✅ Success Criteria
- [ ] Churn rate tracked monthly
- [ ] Health scoring active for all clients
- [ ] At-risk clients identified and tagged
- [ ] QBR schedule created
- [ ] Win-back sequence configured

## 🔗 Next Workflow
After retention plays: `/customer-success`

## 🏯 Binh Pháp Alignment
"善守者藏于九地之下" (The skilled defender hides beneath nine earths) - Proactive retention beats reactive recovery.
