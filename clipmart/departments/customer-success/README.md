# Customer Success Department as a Service

> Replace a CS team with AI agents that onboard customers, detect churn, and drive expansion — 24/7.

## Value Proposition

| What you replace | Annual cost | What you pay |
|-----------------|-------------|--------------|
| 2 CSMs ($80k each) | $160,000/yr | $49/mo floor |
| Gainsight / ChurnZero | $24,000/yr | Included |
| **Total replaced** | **$184,000/yr** | **~$2,400/yr** |

## What This Department Does

1. **Customer Onboarding** — Automated onboarding sequences tailored to customer segment
2. **Health Score Monitoring** — Real-time churn risk detection from product usage signals
3. **QBR Generation** — Quarterly business reviews with ROI analysis
4. **Expansion Plays** — Identify upsell/cross-sell opportunities, trigger expansion outreach
5. **NPS Programs** — Survey design, collection, analysis, and action plans

## Outcome-Based Pricing

| Deliverable | Price |
|------------|-------|
| Customer onboarding sequence | $10 |
| Churn risk alert + action plan | $8 |
| QBR report generated | $15 |
| NPS survey + analysis | $12 |
| Expansion play executed | $10 |

**Monthly floor:** $49.

## Included Commands

```bash
mekong business-client-onboard   # Customer onboarding workflow
mekong business-revenue-engine   # Revenue expansion plays
mekong sales-forecast            # Renewal + expansion forecast
```

## Install

```bash
mekong install dept-customer-success
```

## Configuration

```bash
# .mekong/.env.dept-customer-success
DEPT_CS_CRM=hubspot
DEPT_CS_CRM_API_KEY=your_key
DEPT_CS_PRODUCT_ANALYTICS=mixpanel  # mixpanel|amplitude|segment
DEPT_CS_CHURN_RISK_THRESHOLD=0.7
DEPT_CS_QBR_CADENCE=quarterly
DEPT_CS_NPS_FREQUENCY=90  # days between NPS surveys
```

## Example Workflow: Churn Prevention

```
[Daily Auto] Health score check: usage < 3 logins/week for enterprise customer

[Alert] "AcmeCorp: CHURN RISK HIGH (score 0.8)"
  → Agent generates personalized rescue plan
  → Drafts outreach email for CSM approval

[Human approves] Email sent + EBR booked

[Post-meeting] mekong business-revenue-engine --account acme --play expansion
  → Expansion opportunity identified, proposal drafted
```
