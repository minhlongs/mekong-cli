# Fundraising Department as a Service

> Replace a $20k/month fundraising advisor with AI agents that build investor pipelines, write pitch decks, and manage deal flow.

## Value Proposition

| What you replace | Annual cost | What you pay |
|-----------------|-------------|--------------|
| Fundraising advisor | $240,000/yr | $49/mo floor |
| Pitch deck designer | $15,000/yr | $5/touchpoint |
| CRM for investors | $3,600/yr | Included |
| **Total replaced** | **$258,600/yr** | **~$2,400/yr** |

## What This Department Does

1. **Pitch Deck Generation** — Problem/solution/market/traction narrative with slide structure
2. **Investor Outreach** — Personalized cold outreach to relevant VCs/angels
3. **Cap Table Analysis** — Dilution modeling, SAFE conversions, pro-forma cap table
4. **Due Diligence Prep** — Data room organization, due diligence Q&A preparation
5. **IPO Readiness** — Pre-IPO governance, S-1 narrative prep, board structuring

## Outcome-Based Pricing

| Deliverable | Price |
|------------|-------|
| Pitch deck generation | $50 |
| Investor outreach batch (25 contacts) | $25 |
| Cap table analysis + modeling | $20 |
| Due diligence data room prep | $75 |
| IPO readiness assessment | $150 |

**Monthly floor:** $49.

## Included Commands

```bash
mekong pitch                  # Generate pitch deck
mekong fundraise              # Fundraising workflow management
mekong vc/cap-table           # Cap table analysis
mekong ipo-readiness-check    # IPO gap analysis
mekong ipo-board-prep         # IPO board preparation
mekong board-report           # Investor update reports
```

## Install

```bash
mekong install dept-fundraising
```

## Configuration

```bash
# .mekong/.env.dept-fundraising
DEPT_FUNDRAISING_STAGE=seed  # seed|series-a|series-b
DEPT_FUNDRAISING_TARGET_RAISE_USD=2000000
DEPT_FUNDRAISING_INVESTOR_FOCUS=b2b-saas,fintech,developer-tools
DEPT_FUNDRAISING_CHECK_SIZE_MIN=250000
DEPT_FUNDRAISING_CHECK_SIZE_MAX=2000000
DEPT_FUNDRAISING_CRUNCHBASE_API_KEY=optional
```

## Example Workflow: Seed Round Campaign

```
Week 1: mekong pitch --stage seed --vertical saas --traction "10k MRR, 40% MoM"
  → Pitch deck draft (11 slides)

Week 1: Human reviews + edits pitch

Week 2: mekong fundraise --outreach --target-vcs "precursor,village-global,pear"
  → 50 personalized VC outreach emails

Week 2-6: [Auto] Follow-ups, calendar scheduling, CRM updates

Week 4: mekong vc/cap-table --raise 1500000 --pre-money 8000000
  → Dilution model, SAFE terms, pro-forma

Week 6: mekong fundraise --data-room
  → Organized data room: financials, legal, product, team
```
