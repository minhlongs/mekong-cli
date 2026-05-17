---
description: ⚡⚡⚡ Quant Researcher — strategy discovery, backtest validation, alpha research, new signal candidates
argument-hint: [action: discover|backtest|alpha|propose]
---

**Ultrathink** Quant research: <args>$ARGUMENTS</args>

**CWD:** `apps/algo-trader` | **REF:** `docs/trading-team-subordinates-sops.md` PART 1
**Reports to:** CAIO (`/trading:caio`)

## Pipeline (4 steps)

### 1. STRATEGY INVENTORY
Current strategies in `src/strategies/`:
| Strategy | Weight | Win% | Status |
|----------|--------|------|--------|
| MacdBollingerRsi | 0.30 | XX% | 🟢/🔴 |
| RsiSma | 0.25 | XX% | 🟢/🔴 |
| BollingerBand | 0.25 | XX% | 🟢/🔴 |
| MacdCrossover | 0.20 | XX% | 🟢/🔴 |

### 2. ALPHA CANDIDATES
Scan `src/core/SignalGenerator.ts`, `signal-market-regime-detector.ts`, `SignalFilter.ts` for new signal ideas:
| Candidate | Type | Complexity | Expected Edge |
|-----------|------|-----------|---------------|
| {name} | Indicator/ML/Hybrid | Low/Med/High | XX% improvement |

### 3. BACKTEST VALIDATION
For each candidate, validate:
| Check | Criterion | Result |
|-------|-----------|--------|
| Sample size | >200 trades | ✅/❌ |
| Win rate | >52% | ✅/❌ |
| Profit factor | >1.3 | ✅/❌ |
| Max drawdown | <20% | ✅/❌ |
| Sharpe ratio | >1.0 | ✅/❌ |
| Walk-forward OOS | Passes | ✅/❌ |

### 4. PROPOSAL
Submit to CAIO with: signal logic, backtest results, recommended weight, risks.
Save: `plans/reports/quant-strategy-proposal-{date}.md`

## USAGE
```bash
/trading:quant discover    # Scan for new strategy ideas
/trading:quant backtest    # Validate strategy candidate
/trading:quant alpha       # Alpha source research
/trading:quant propose     # Submit strategy proposal
```
