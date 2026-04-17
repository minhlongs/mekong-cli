---
description: ⚡⚡⚡ Risk Analyst — VaR modeling, correlation matrix, stress testing, Monte Carlo, portfolio risk
argument-hint: [action: var|stress|correlation|report]
---

**Ultrathink** Risk analysis: <args>$ARGUMENTS</args>

**CWD:** `apps/algo-trader` | **REF:** `docs/trading-team-subordinates-sops.md` PART 2
**Reports to:** Founder (`/trading:founder`)

## Pipeline (4 steps)

### 1. VaR CALCULATION
Using `src/core/historical-var-calculator.ts`:
| Method | 1-Day | 7-Day | 30-Day |
|--------|-------|-------|--------|
| Historical VaR (95%) | ${X} | ${X} | ${X} |
| Historical VaR (99%) | ${X} | ${X} | ${X} |
| Parametric VaR | ${X} | ${X} | ${X} |

### 2. CORRELATION MATRIX
Using `src/core/portfolio-correlation-matrix-calculator.ts`:
| Pair | BTC | ETH | SOL | ... |
|------|-----|-----|-----|-----|
| BTC | 1.0 | X.X | X.X | |
| ETH | X.X | 1.0 | X.X | |
Portfolio diversification score: X/10

### 3. STRESS TEST
| Scenario | Max Loss | CB Triggers? | Survival |
|----------|----------|-------------|----------|
| Flash crash -20% | ${X} | Yes/No | ✅/❌ |
| Exchange outage 4h | ${X} | Yes/No | ✅/❌ |
| Correlation spike | ${X} | Yes/No | ✅/❌ |
| Black swan -40% | ${X} | Yes/No | ✅/❌ |
| Liquidation cascade | ${X} | Yes/No | ✅/❌ |

### 4. RISK REPORT
Using `src/core/PortfolioRiskManager.ts`, `portfolio-var-kelly-calculator.ts`:
Save: `plans/reports/risk-analysis-{date}.md`

## USAGE
```bash
/trading:risk-analyst var          # VaR calculation
/trading:risk-analyst stress       # Stress test scenarios
/trading:risk-analyst correlation  # Pair correlation matrix
/trading:risk-analyst report       # Full risk report
```
