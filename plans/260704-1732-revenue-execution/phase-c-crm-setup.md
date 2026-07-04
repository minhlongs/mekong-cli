# Phase C: CRM Setup — HubSpot + Pipeline + Lead Scoring

**Goal:** Track customer lifecycle: Lead → Trial → Paid → Churn.

## Steps

### C1. HubSpot Config
**Create:** `config/crm.yaml`
```yaml
provider: hubspot
api_key: "${HUBSPOT_API_KEY}"
pipelines:
  default: "Mekong Pipeline"
stages:
  - lead: "Installed CLI"
  - trial: "Active trial (MCU > 0)"
  - paid: "Active subscriber"
  - churned: "Cancelled/inactive"
```

### C2. Contact Creation Script
**Create:** `scripts/crm-sync.cjs`
- Creates HubSpot contact on signup
- Updates deal stage on trial start/payment/churn
- Daily sync: reads SQLite ledger → updates HubSpot

### C3. Lead Scoring Rules
```
Install script run     → +10 points
Trial started          → +20 points
Trial configured       → +20 points (>1 agent setup)
First workflow run     → +30 points
Payment (any tier)     → +50 points
30 days inactive       → -20 points
```

### C4. Pipeline Dashboard
- HubSpot free dashboard
- Pipeline view: leads → trials → paid
- Weekly email report (HubSpot built-in)
- Alerts on: 5+ leads without trial, 3+ trials without conversion

## Files
- Create: `config/crm.yaml`
- Create: `scripts/crm-sync.cjs`
- Create: `scripts/lead-scorer.cjs`

## Dependencies
- HubSpot free account + API key
- `npm install @hubspot/api-client`
