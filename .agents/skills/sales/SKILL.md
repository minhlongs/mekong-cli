---
name: sales
description: >-
  Sales, SDR, and dealflow command suite — pipeline, outreach, lead qualify, deal close, VC dealflow.
---

# /sales — Sales & Revenue Command Suite

**AUTO-EXECUTE MODE.** Detect sub-command from user prompt and execute.

## Native CLI Command Surface

The `mekong sales` command provides full sales lifecycle management backed by SQLite persistence (`.mekong/sales.db`):

```bash
# Executive Pipeline Overview & Forecast (Console or JSON)
mekong sales
mekong sales --json

# Add Opportunity to Pipeline
mekong sales add "Enterprise Tier" --company "VNG Corp" --value 24000 --stage qualified --email cto@vng.com.vn --json

# List Deals by Stage
mekong sales list
mekong sales list --stage proposal --json

# Update Deal Stage / Value / Notes
mekong sales update <deal_id> --stage negotiation --value 28000 --notes "Added multi-tenant enterprise support" --json

# Multi-Channel Outreach Copy & Cadence (email / linkedin / zalo)
mekong sales outreach "MoMo" --persona "VP Engineering" --channel email --json
mekong sales outreach "VNPAY" --persona "Giám đốc Công nghệ" --channel zalo --json

# Account Executive Deal Preparation & Objection Handling
mekong sales prep "Tiki" --value 18000 --pain "Slow sprint velocity, fragmented review cycles" --json

# Deal Close & Customer Success Onboarding Receipt
mekong sales close <deal_id> --json
```

## Native Model Context Protocol (MCP) Tools

- **`mekong_sales_pipeline(stage: str = "")`**: Query pipeline revenue metrics, win rate, and weighted forecasts.
- **`mekong_sales_deal_add(name: str, company: str, value: float, stage: str = "lead", email: str = "")`**: Add new opportunity to pipeline ledger.
- **`mekong_sales_outreach(company: str, persona: str = "CTO", channel: str = "email")`**: Generate tailored multi-channel outreach copy and cadence.

---

## Sales Commands

### `/sales pipeline-build` — Build Sales Pipeline
1. Define ICP (Ideal Customer Profile)
2. Research target companies/contacts
3. Create lead list
4. Design outreach sequences
5. Setup CRM pipeline stages
6. Output: `reports/sales/pipeline/`

### `/sales deal-close` — Close Deal
1. Preparation checklist
2. Pricing strategy
3. Objection handling playbook
4. Contract template reference
5. Follow-up sequence

### `/sales weekly-review` — Weekly Sales Review
1. Pipeline metrics (new leads, conversions, revenue)
2. Win/loss analysis
3. Forecast update
4. Next week focus

## SDR Commands

### `/sdr prospect` — Prospecting
1. Research target market segment
2. Build prospect list with contact info
3. Qualify against ICP criteria
4. Prioritize by fit score

### `/sdr outreach-blast` — Outreach Campaign
1. Email sequences (cold, warm, referral)
2. LinkedIn messaging templates
3. Follow-up cadences
4. A/B test variations

### `/sdr lead-qualify` — Lead Qualification
1. BANT framework (Budget, Authority, Need, Timeline)
2. Scoring criteria
3. Handoff to AE process

## Account Executive Commands

### `/ae deal-prep` — Deal Preparation
1. Prospect research deep-dive
2. Pain point mapping
3. Solution fit presentation
4. Competitive differentiation

### `/ae follow-up` — Follow-Up
1. Meeting recap
2. Action items
3. Next steps timeline
4. Stakeholder mapping

### `/ae close-report` — Close Report
1. Deal summary
2. Revenue attribution
3. Lessons learned
4. Customer success handoff

## Dealflow Commands (VC/Studio)

### `/dealflow source` — Source Deals
1. Market scanning by vertical
2. Referral network activation
3. Pipeline building

### `/dealflow screen` — Screen Opportunities
1. Quick assessment criteria
2. Go/No-Go decision matrix
3. Follow-up classification

### `/dealflow diligence` — Due Diligence
1. Financial analysis
2. Market validation
3. Team assessment
4. Technical review

### `/dealflow term-sheet` — Term Sheet
1. Key terms definition
2. Valuation framework
3. Protection clauses

### `/dealflow close` — Close Deal
1. Final checks
2. Legal documentation
3. Signing process
4. Post-close integration

## Portfolio Matching

### `/match founder-idea` — Match Founder to Idea
Analyze founder skills/background → recommend best-fit ideas

### `/match vc-startup` — Match VC to Startup  
Analyze VC thesis → match with portfolio startups

## CLI Invocation

```bash
// turbo
mekong sales $ARGUMENTS
```
