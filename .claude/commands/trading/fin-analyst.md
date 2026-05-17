---
description: ⚡⚡⚡ Financial Analyst — P&L attribution, per-strategy breakdown, cost modeling, break-even analysis
argument-hint: [action: pnl|attribution|costs|breakeven]
---

**Ultrathink** Financial analysis: <args>$ARGUMENTS</args>

**CWD:** `apps/algo-trader` | **REF:** `docs/trading-team-subordinates-sops.md` PART 8
**Reports to:** CFO (`/trading:cfo`)

## Pipeline (4 steps)

### 1. P&L ATTRIBUTION
Using `src/reporting/PerformanceAnalyzer.ts`, `src/core/pnl-realtime-snapshot-service.ts`:
| Dimension | Breakdown | P&L | % Total |
|-----------|-----------|-----|---------|
| By strategy | MacdBollingerRsi | ${X} | XX% |
| | RsiSma | ${X} | XX% |
| | BollingerBand | ${X} | XX% |
| | MacdCrossover | ${X} | XX% |
| By pair | BTC/USDT | ${X} | XX% |
| | ETH/USDT | ${X} | XX% |
| By exchange | Binance | ${X} | XX% |
| | OKX | ${X} | XX% |

### 2. COST MODELING
| Category | Fixed/Variable | Monthly | Model |
|----------|---------------|---------|-------|
| Exchange fees | Variable | ${X} | Fee tier × volume |
| Slippage | Variable | ${X} | Historical avg |
| Infrastructure | Fixed | ${X} | Flat rate |
| API/LLM tokens | Variable | ${X} | Usage-based |
| Opportunity cost | Calculated | ${X} | Risk-free rate |

### 3. BREAK-EVEN ANALYSIS
```
Fixed costs/mo:    ${X}
Variable ratio:    XX%
Break-even revenue: ${X}/mo
Current revenue:    ${X}/mo
Gap:                ±${X}
Days to break-even: X days
```

### 4. REPORT
Save: `plans/reports/fin-analysis-{date}.md`

## USAGE
```bash
/trading:fin-analyst pnl          # Real-time P&L snapshot
/trading:fin-analyst attribution  # Strategy/pair/exchange breakdown
/trading:fin-analyst costs        # Cost model deep dive
/trading:fin-analyst breakeven    # Break-even dashboard
```
