# Strategy Department as a Service

> Replace a Chief of Staff + $30k strategy consultant with autonomous AI agents that run annual planning, OKRs, competitive analysis, and board reporting.

## Value Proposition

| What you replace | Annual cost | What you pay |
|-----------------|-------------|--------------|
| Chief of Staff ($150k) | $150,000/yr | $49/mo floor |
| Strategy consultant | $30,000/yr | $15/deliverable |
| Board prep materials | $10,000/yr | Included |
| **Total replaced** | **$190,000/yr** | **~$1,200/yr** |

## What This Department Does

1. **Annual Planning** — Translate vision into 1-year operating plan with milestones
2. **OKR Management** — Cascade company OKRs to teams, track weekly, alert on drift
3. **SWOT + Competitive Intel** — Quarterly competitive landscape updates
4. **Board Reporting** — Monthly board packs: metrics, narrative, risks, asks
5. **IPO Readiness** — Pre-IPO gap analysis and board governance prep

## Outcome-Based Pricing

| Deliverable | Price |
|------------|-------|
| Annual OKR plan | $75 |
| Quarterly board report | $45 |
| SWOT + competitive analysis | $30 |
| 3-year financial model | $90 |
| IPO readiness assessment | $150 |

**Monthly floor:** $49.

## Included Commands

```bash
mekong annual                    # Annual planning cycle
mekong okr                       # OKR cascade and tracking
mekong swot                      # SWOT analysis
mekong board-report              # Board pack generation
mekong board-manage              # Board management workflow
mekong board-minutes             # Meeting minutes
mekong business-quarterly-review # QBR preparation
mekong ipo-readiness-check       # IPO gap analysis
mekong ipo-board-prep            # IPO board prep checklist
```

## Install

```bash
mekong install dept-strategy
```

## Configuration

```bash
# .mekong/.env.dept-strategy
DEPT_STRATEGY_COMPANY_STAGE=seed  # seed|series-a|series-b|growth|pre-ipo
DEPT_STRATEGY_FISCAL_YEAR_START=01  # month (01=January)
DEPT_STRATEGY_BOARD_CADENCE=monthly  # monthly|quarterly
DEPT_STRATEGY_OKR_CADENCE=quarterly
DEPT_STRATEGY_COMPETITOR_WATCHLIST=competitor1.com,competitor2.com
```

## Example Workflow: Quarterly OKR + Board Pack

```
Week 1 (Monday): mekong okr --quarter Q2 --cascade
  → Draft Q2 OKRs from Q1 performance + annual plan

Week 1 (Review): Human approves/edits OKRs

Week 2-12: [Auto] Weekly OKR progress tracking, drift alerts

End of Quarter: mekong board-report --quarter Q2
  → Full board pack: OKR results, financials, risks, Q3 plan
```

## Comparison

| Metric | Chief of Staff | Strategy Dept SaS |
|--------|---------------|-------------------|
| Monthly cost | $12,500 | $49 floor |
| Board pack prep time | 2-3 days | 2-3 hours |
| OKR tracking | Manual spreadsheet | Automated alerts |
| Competitive updates | Quarterly | Continuous |
