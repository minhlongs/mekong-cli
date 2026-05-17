---
description: ⚡⚡⚡ Full trading pipeline (sequential) — AutonomyController-driven, single-pair focus
argument-hint: [pair] [mode: backtest|paper|arb|live] [autonomy: observe|plan|confirm|auto]
---

**Ultrathink** full trading pipeline: <args>$ARGUMENTS</args>

**IMPORTANT:** Activate `trading` + `arbitrage` skills. Token efficiency. YAGNI, KISS, DRY.
**CWD:** `apps/algo-trader`

---

## AUTONOMY = Trader's Permission Mode

| Level | Behavior | AutonomyController method |
|-------|----------|--------------------------|
| `observe` | Scan only, NO action | `requiresConfirmation()=true, canExecute()=false` |
| `plan` | Scan + suggest, NO execute | `requiresConfirmation()=true, canExecute()=false` |
| `confirm` | Execute with approval PER trade | `requiresConfirmation()=true, canExecute()=true` |
| `auto` | Full auto, circuit breakers active | `requiresConfirmation()=false, canExecute()=true` |

**Default:** `confirm`. Source: `src/core/autonomy-controller.ts`

---

## PIPELINE — 10 Sequential Steps

### 1. Health Gate
- `src/netdata/HealthManager.ts` → `getReport()`
- `src/execution/exchange-connection-pool.ts` → connectivity
- `tsc --noEmit` → 0 errors
- **GATE:** all green → proceed

### 2. Market Scan
- Single `researcher` agent
- `src/analysis/indicators.ts` → RSI, SMA, MACD, BBands, ATR
- 4 strategies: MacdBollingerRsi (0.30), RsiSma (0.25), Bollinger (0.25), MacdCrossover (0.20)
- Market regime detection per pair
- Report: `plans/reports/trading-scan-{date}.md`

### 3. Signal Consensus
- `src/core/SignalGenerator.ts` → `aggregate(WeightedSignal[])`
- Config: `{ consensusThreshold: 0.6, minVotes: 2 }`
- A2UI: `SIGNAL_RATIONALE` + `CONFIDENCE_UPDATE` events
- Filter: confidence ≥ 0.6 only

### 4. Trade Planning
- Entry/exit from signal price ± ATR
- `RiskManager.calculatePositionSize(balance, riskPct, price)`
- `RiskManager.checkStopLossTakeProfit()` → SL 2%, TP 5%
- R:R ≥ 1:1.5
- A2UI: `INTENT_PREVIEW` event
- **AUTONOMY GATE:** observe/plan → skip to 9. confirm → ask user. auto → proceed.

### 5. Risk Gate
- `RiskManager.isDailyLossLimitHit(dailyPnL, $100)`
- Portfolio exposure check
- Correlation check
- A2UI: `RISK_ALERT` if exceeded
- **GATE:** LOW/MED → proceed. HIGH → `AutonomyController.escalate()` → downgrade

### 6. Backtest Validation
- `src/backtest/BacktestEngine.ts` → walk-forward
- Criteria: Sharpe >1.0, WR >55%, DD <10%, PF >1.5
- Fail → adjust → retest (max 2x)

### 7. Execution
| Mode | Module | Gate |
|------|--------|------|
| `backtest` | BacktestEngine | → Step 9 |
| `paper` | PaperTradingEngine | → Step 8 |
| `arb` | ArbitrageEngine | → Step 8 |
| `live` | BotEngine.start() | **⚠️ confirm** → Step 8 |

### 8. Monitor (paper/arb/live only)
- `src/netdata/HealthManager.ts` → health polling
- `src/netdata/SignalMesh.ts` → signal routing
- Circuit breakers: daily loss, drawdown 10%, exchange disconnect
- A2UI: `ESCALATION` on critical events

### 9. Performance Review
- `src/reporting/PerformanceAnalyzer.ts`
- Win Rate, Sharpe, Sortino, Max DD, fees, slippage
- `src/a2ui/trade-audit-logger.ts` → audit trail

### 10. Report
- Save: `plans/reports/trading-auto-{date}-{slug}.md`
- Summary table, P&L, recommendations
- Next: continue / adjust / stop

## SAFETY

```
DEFAULT_MODE = backtest | DEFAULT_AUTONOMY = confirm
CIRCUIT_BREAKERS = always on | RISK_PER_TRADE = 2%
DAILY_LOSS = $100 | AUDIT = TradeAuditLogger
LIVE = explicit confirm | ESCALATION = auto-downgrade
```
