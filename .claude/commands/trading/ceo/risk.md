---
description: ⚡⚡⚡ CEO Risk Governance — risk appetite levels, audit, circuit breaker review, concentration analysis
argument-hint: [action: audit|set|review] [level: conservative|moderate|aggressive]
---

**Ultrathink** CEO risk governance: <args>$ARGUMENTS</args>

**CWD:** `apps/algo-trader` | **REF:** `docs/ceo-sops.md` SOP-C04, SOP-C05

---

## RISK APPETITE LEVELS

### Conservative (Default — first 6 months)
```
Daily loss:    $100  | Weekly: $500   | Monthly: $1,500
Max drawdown:  10%   | Per-trade: 1%  | Exchanges: 2
Pairs: BTC/USDT, ETH/USDT only
Strategies: Paper + backtest verified only
```

### Moderate (After 6 months profitable)
```
Daily loss:    $300  | Weekly: $1,500 | Monthly: $5,000
Max drawdown:  15%   | Per-trade: 2%  | Exchanges: 3
Pairs: Top 5 by volume
Strategies: Paper verified + live small
```

### Aggressive (After 1 year, proven track record)
```
Daily loss:    $1,000 | Weekly: $5,000 | Monthly: $15,000
Max drawdown:  20%    | Per-trade: 3%  | Exchanges: 5+
Pairs: Top 10 + funding arb
Strategies: AGI + Stealth arb
```

---

## PIPELINE (6 steps)

### 1. Current Risk Profile
- Read `src/core/RiskManager.ts` config values
- Read `src/core/autonomy-controller.ts` current level
- Read recent reports for loss/drawdown data

### 2. Risk Audit Checklist
```
Per-Trade Controls:
- [ ] Position sizing correct? (1-3% per risk level)
- [ ] SL/TP configured? (SL 2%, TP 5%)
- [ ] R:R minimum met? (≥1:1.5)

Daily Controls:
- [ ] Daily loss limit appropriate?
- [ ] Circuit breakers active? (always yes)
- [ ] Consecutive loss limit set? (3 → escalate)

Portfolio Controls:
- [ ] Exchange concentration <40%?
- [ ] Pair concentration <25%?
- [ ] Strategy concentration <30%?
- [ ] Cash reserve ≥10%?

Strategic Controls:
- [ ] Weekly loss limit set?
- [ ] Monthly loss limit set?
- [ ] Max drawdown threshold correct?
- [ ] Exit strategy defined? (SOP-C09)
```

### 3. Circuit Breaker Analysis
- Count activations this period
- Which breakers triggered most?
- Any thresholds need adjustment?
- False positive rate?

**Source modules:**
| Breaker | File | Check |
|---------|------|-------|
| Daily loss | `src/core/RiskManager.ts` | `isDailyLossLimitHit()` |
| Drawdown | `src/core/RiskManager.ts` | `checkStopLossTakeProfit()` |
| Consecutive loss | `src/core/autonomy-controller.ts` | `escalate()` |
| Exchange down | `src/execution/exchange-health-monitor.ts` | Health status |
| Adaptive (stealth) | `src/execution/adaptive-circuit-breaker-per-exchange.ts` | Per-exchange |

### 4. Concentration Analysis
```
Exchange Concentration:
├── Binance: XX% volume  (limit: 40%)
├── OKX:     XX% volume  (limit: 40%)
└── Bybit:   XX% volume  (limit: 40%)

Pair Concentration:
├── BTC/USDT: XX% (limit: 25%)
├── ETH/USDT: XX% (limit: 25%)
└── Others:   XX%

Strategy Concentration:
├── MacdBollingerRsi: weight XX% (limit: 30%)
├── RsiSma:           weight XX%
├── Bollinger:        weight XX%
└── MacdCrossover:    weight XX%
```

### 5. Level Transition Check
| From → To | Criteria |
|-----------|----------|
| Conservative → Moderate | 6mo profitable, Sharpe >1.0, DD <10% |
| Moderate → Aggressive | 12mo profitable, Sharpe >1.5, DD <15% |
| Any → Conservative | Monthly loss >limit, DD >threshold |

### 6. Report
Save: `plans/reports/ceo-risk-{date}.md`

## USAGE
```bash
/trading:ceo:risk audit                 # Full risk audit
/trading:ceo:risk set conservative      # Set risk level
/trading:ceo:risk set moderate          # Upgrade (if criteria met)
/trading:ceo:risk review                # Quick risk dashboard
```
