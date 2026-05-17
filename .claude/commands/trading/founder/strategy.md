---
description: ⚡⚡⚡ Founder Strategy Lifecycle — promote/demote/kill strategies, phase transitions, weight optimization
argument-hint: [action: review|promote|demote|kill] [strategy: macd-bollinger-rsi|rsi-sma|bollinger|macd-crossover|all]
---

**Ultrathink** Founder strategy lifecycle: <args>$ARGUMENTS</args>

**CWD:** `apps/algo-trader` | **REF:** `docs/founder-sops.md` SOP-F07

## Strategy Lifecycle — 5 Phases

```
RESEARCH → BACKTEST → PAPER → LIVE SMALL → LIVE SCALE
   1-2d      1d        3-7d     2-4 weeks    ongoing
```

## Pipeline (4 steps)

### 1. Strategy Inventory
| Strategy | Weight | Phase | Trades | WR | Sharpe | DD | Status |
|----------|--------|-------|--------|-----|--------|-----|--------|
| MacdBollingerRsi | 0.30 | {phase} | {N} | XX% | X.XX | XX% | 🟢/🟡/🔴 |
| RsiSma | 0.25 | {phase} | {N} | XX% | X.XX | XX% | 🟢/🟡/🔴 |
| Bollinger | 0.25 | {phase} | {N} | XX% | X.XX | XX% | 🟢/🟡/🔴 |
| MacdCrossover | 0.20 | {phase} | {N} | XX% | X.XX | XX% | 🟢/🟡/🔴 |

**Source:** `src/core/SignalGenerator.ts`, trading reports

### 2. Kill Criteria Check (Per Strategy)
- [ ] Sharpe <0.5 for 1 week live? → **KILL**
- [ ] Win Rate <40% (20+ trades)? → **KILL**
- [ ] Max DD >15%? → **KILL**
- [ ] 5 consecutive losses? → **DEMOTE**

### 3. Promotion Criteria Check
| Transition | Criteria | Met? |
|-----------|----------|------|
| RESEARCH → BACKTEST | Hypothesis documented | ✅/❌ |
| BACKTEST → PAPER | Sharpe >1, WR >55%, DD <10% | ✅/❌ |
| PAPER → LIVE SMALL | ≥20 trades, consistent P&L | ✅/❌ |
| LIVE SMALL → LIVE SCALE | 2 weeks profitable | ✅/❌ |

### 4. Weight Optimization
Self-learning adjustments:
- Win → strategy weight +0.05
- Loss → strategy weight -0.05
- Rebalance: ensure sum = 1.0

**Source:** `src/core/autonomy-controller.ts` → `recordSuccess()`, `escalate()`

## USAGE
```bash
/trading:founder:strategy review              # Full strategy review
/trading:founder:strategy promote rsi-sma     # Promote to next phase
/trading:founder:strategy demote bollinger     # Demote to previous phase
/trading:founder:strategy kill macd-crossover  # Kill strategy
```
