---
description: ⚡ Quick trade analysis — scan + signal + risk in <1min, NO execution
argument-hint: [pair] [timeframe: 1h|4h|1d]
---

**Ultrathink** quick analysis: <args>$ARGUMENTS</args>

**CWD:** `apps/algo-trader` | Mode: analysis only, NO execution.

## Pipeline (5 steps, ~30s)

### 1. Health (5s)
- `tsc --noEmit` → 0 errors
- `src/netdata/HealthManager.ts` → exchange connectivity dry check

### 2. Scan (15s)
- `src/analysis/indicators.ts` → `Indicators.rsi()`, `.sma()`, `.macd()`, `.bollingerBands()`
- 4 strategies: MacdBollingerRsi(0.30), RsiSma(0.25), Bollinger(0.25), MacdCrossover(0.20)
- Regime detection: trending/ranging/volatile

### 3. Signal (5s)
- `src/core/SignalGenerator.ts` → `aggregate(WeightedSignal[])`
- Config: `{ consensusThreshold: 0.6, minVotes: 2 }`

### 4. Risk (3s)
- `src/core/RiskManager.ts` → `calculatePositionSize(balance, 2, price)`
- `checkStopLossTakeProfit()` → SL 2%, TP 5%
- R:R ratio

### 5. Report (instant)
```
## Quick Analysis — {pair} {date}
📊 Regime: {trending/ranging/volatile}
📡 Signal: {BUY/SELL/HOLD} (confidence {XX}%)
🎯 Entry: ${price} | SL: ${sl} | TP: ${tp}
📐 R:R: 1:{ratio} | Risk: ${amount} ({pct}%)
⚡ Quality: {score}/100
🗳️ Votes: {strategy1}={vote}, {strategy2}={vote}, ...

→ Execute: /trading:auto {pair} {mode}
→ Deep: /trading:auto:parallel {pair1} {pair2} {mode}
```

## Defaults
```
Pair: BTC/USDT | Timeframe: 1h | Exchanges: binance, okx, bybit
```
