---
description: ⚡⚡⚡⚡⚡ Deep Trading Pipeline — auto có kiểm soát, multi-pair parallel, AutonomyController-driven
argument-hint: [pairs] [mode: backtest|paper|arb|live] [autonomy: observe|plan|confirm|auto]
---

**Ultrathink parallel** full trading pipeline: <args>$ARGUMENTS</args>

**IMPORTANT:** Activate `trading` + `arbitrage` skills. Max token efficiency. YAGNI, KISS, DRY.
**CWD:** `apps/algo-trader`

---

## ARCHITECTURE — ClaudeKit ↔ Algo-Trader Deep Map

```
ClaudeKit Layer              Algo-Trader Module                    File Path
─────────────────────────────────────────────────────────────────────────────
Permission Modes      ←→     AutonomyController (4-tier)          src/core/autonomy-controller.ts
/bootstrap:auto       ←→     WorkflowPipelineEngine               src/pipeline/workflow-pipeline-engine.ts
researcher agent      ←→     indicators.ts + strategies/*          src/analysis/indicators.ts
planner agent         ←→     SignalGenerator (consensus)           src/core/SignalGenerator.ts
code-reviewer agent   ←→     RiskManager (gate)                   src/core/RiskManager.ts
tester agent          ←→     BacktestEngine (walk-forward)         src/backtest/BacktestEngine.ts
fullstack-developer   ←→     BotEngine + TradeExecutor             src/core/BotEngine.ts
debugger agent        ←→     HealthManager + ExchangeRouter        src/netdata/HealthManager.ts
docs-manager agent    ←→     HtmlReporter + PerformanceAnalyzer    src/reporting/
project-manager       ←→     A2UI SurfaceManager (dashboard)       src/a2ui/surface-manager.ts
git hooks             ←→     AgentEventBus (event system)          src/a2ui/agent-event-bus.ts
```

## AUTONOMY CONTROL — Trader's Permission Mode

| Autonomy Level | CC CLI Equivalent | Behavior | Source |
|----------------|-------------------|----------|--------|
| `OBSERVE` | `plan` mode | Scan only, hiển thị data, KHÔNG action | `AutonomyLevel.OBSERVE` |
| `PLAN` | `acceptEdits` | Scan + suggest trades, KHÔNG execute | `AutonomyLevel.PLAN` |
| `ACT_CONFIRM` | `default` | Execute with user approval PER TRADE | `AutonomyLevel.ACT_CONFIRM` |
| `AUTONOMOUS` | `bypassPermissions` | Full auto, circuit breakers active | `AutonomyLevel.AUTONOMOUS` |

**Default:** `ACT_CONFIRM` (safe). Escalation auto-downgrades on risk events.
**Source:** `src/core/autonomy-controller.ts` → `AutonomyController`
**Auto-restore:** After 5 successful trades, auto-restores previous level.

---

## PIPELINE — 10 Steps (mirrors /bootstrap:auto:parallel)

### 1. GATE: Health Check (Sequential)

**Maps to:** `/bootstrap:auto:parallel` Step 1 (Git Init)

```bash
cd apps/algo-trader
tsc --noEmit                                    # TypeScript: 0 errors
pnpm test --testPathPattern="HealthManager" 2>&1 | tail -3  # Health module tests
```

**Module chain:**
- `src/netdata/HealthManager.ts` → `HealthManager.getReport()`
- `src/execution/exchange-connection-pool.ts` → `ExchangeConnectionPool.getConnected()`
- `src/execution/exchange-health-monitor.ts` → `ExchangeHealthMonitor.getExchangeStatus()`
- `src/core/http-health-check-server.ts` → `/health` endpoint

**GATE:** ALL checks green → proceed. ANY red → diagnose with `debugger` agent → fix.

### 2. PARALLEL: Market Scan (2 researcher agents)

**Maps to:** `/bootstrap:auto:parallel` Step 2 (Research)

Launch **2 researcher agents** in parallel:

**Researcher A — Technical Analysis:**
- Read `src/analysis/indicators.ts` → `Indicators` class
  - Methods: `sma()`, `ema()`, `rsi()`, `macd()`, `bollingerBands()`, `atr()`, `stochastic()`
- Run all 4 strategies on each pair:
  - `src/strategies/MacdBollingerRsiStrategy.ts` (weight: 0.30)
  - `src/strategies/RsiSmaStrategy.ts` (weight: 0.25)
  - `src/strategies/BollingerBandStrategy.ts` (weight: 0.25)
  - `src/strategies/MacdCrossoverStrategy.ts` (weight: 0.20)
- Market regime per pair (trending/ranging/volatile)
- Output: `plans/reports/trading-scan-tech-{date}.md` (≤100 lines)

**Researcher B — Cross-Exchange Spreads:**
- Read `src/arbitrage/index.ts` → `ArbitrageEngine`
- Bid/ask spreads: Binance vs OKX vs Bybit per pair
- Funding rate differentials (perpetual futures)
- `src/cli/spread-detector-command.ts` → spread detection logic
- `src/execution/exchange-router-with-fallback.ts` → route scoring
- Output: `plans/reports/trading-scan-spreads-{date}.md` (≤100 lines)

### 3. SEQUENTIAL: Signal Consensus (needs scan results)

**Maps to:** `/bootstrap:auto:parallel` Step 3 (Tech Stack)

**Module:** `src/core/SignalGenerator.ts` → `SignalGenerator`
- Config: `{ consensusThreshold: 0.6, minVotes: 2 }`
- Input: `WeightedSignal[]` from 4 strategies
- Method: `SignalGenerator.aggregate(signals)` → `ConsensusSignal | null`
- Output fields: `type`, `confidence`, `votes[]`, `metadata.buyWeight/sellWeight`

**Pipeline integration:** `src/pipeline/workflow-pipeline-engine.ts`
- Factory: `createTradingPipeline({ onSignalDetect, onRiskCheck, ... })`
- Node flow: `Trigger → Signal → RiskCheck → Order → Report`

**A2UI events emitted:**
- `SIGNAL_RATIONALE` → per-strategy reasoning (`src/a2ui/signal-explainer.ts`)
- `CONFIDENCE_UPDATE` → overall confidence with factor breakdown
- `THOUGHT_SUMMARY` → aggregated analysis steps + regime

**Filter:** Only signals with `confidence ≥ 0.6` proceed. Rank top 5.

### 4. PARALLEL: Trade Planning (per signal)

**Maps to:** `/bootstrap:auto:parallel` Step 4 (Wireframe & Design)

For EACH top signal, launch `planner` agent in parallel:
- Entry/exit levels from signal price ± ATR
- Stop-loss: `RiskManager.checkStopLossTakeProfit()` → `src/core/RiskManager.ts:59`
  - Config: `{ stopLossPercent: 2, takeProfitPercent: 5 }`
- Position sizing: `RiskManager.calculatePositionSize(balance, riskPct, price)` → `src/core/RiskManager.ts:35`
- Exchange selection: `src/execution/exchange-router-with-fallback.ts` → best liquidity + fees
- R:R validation ≥ 1:1.5

**A2UI event:** `INTENT_PREVIEW` → shows planned trade to user
```typescript
{
  type: 'INTENT_PREVIEW',
  action: 'BUY', symbol: 'BTC/USDT',
  amount: 0.05, price: 65000,
  rationale: 'MACD+RSI+BB consensus 72%',
  confidence: 0.72,
  requiresConfirmation: true  // per AutonomyLevel
}
```

**AUTONOMY GATE:**
- `OBSERVE` → show plans only, skip to Step 9
- `PLAN` → show plans only, skip to Step 9
- `ACT_CONFIRM` → **Ask user to approve ALL plans at once**
- `AUTONOMOUS` → auto-approve, proceed

### 5. GATE: Portfolio Risk (Sequential)

**Maps to:** `/bootstrap:auto:parallel` Step 7 (Code Review)

**Module:** `src/core/RiskManager.ts`
- Total exposure: sum(all position sizes × prices)
- Daily loss check: `RiskManager.isDailyLossLimitHit(dailyPnL, limitUsd)` → `src/core/RiskManager.ts:94`
- Correlation check: avoid correlated longs (BTC+ETH same direction)
- Trailing stop init: `RiskManager.initTrailingStop(price, config)` → `src/core/RiskManager.ts:102`

**A2UI event:** `RISK_ALERT` if threshold exceeded
```typescript
{
  type: 'RISK_ALERT',
  alertType: 'daily_loss' | 'drawdown' | 'volatility',
  value: currentExposure, threshold: maxExposure,
  message: 'Portfolio exposure 85% of max'
}
```

**GATE:** Risk LOW/MEDIUM → proceed. HIGH → `AutonomyController.escalate()` auto-downgrades level → reduce positions → re-check.

### 6. PARALLEL: Backtest Validation

**Maps to:** `/bootstrap:auto:parallel` Step 6 (Testing)

Run `tester` agent PER strategy/pair in parallel:

**Module:** `src/backtest/BacktestEngine.ts`
- Metrics: `src/backtest/backtest-engine-metrics-and-statistics-calculator.ts`
- Result types: `src/backtest/backtest-engine-result-types.ts`
- Walk-forward analysis (anti-overfitting)

**Criteria (MUST ALL PASS):**
| Metric | Threshold | Source |
|--------|-----------|--------|
| Sharpe Ratio | > 1.0 | `MetricsCalculator.sharpeRatio()` |
| Win Rate | > 55% | `MetricsCalculator.winRate()` |
| Max Drawdown | < 10% | `MetricsCalculator.maxDrawdown()` |
| Profit Factor | > 1.5 | `MetricsCalculator.profitFactor()` |

**Fail → adjust params → retest (max 2 iterations).**

### 7. EXECUTION (mode-dependent)

**Maps to:** `/bootstrap:auto:parallel` Step 5 (Implementation)

| Mode | Module | Action |
|------|--------|--------|
| `backtest` | `BacktestEngine` | Report results → Step 9 |
| `paper` | `src/core/paper-trading-engine.ts` → `PaperTradingEngine` | Simulated execution → Step 8 |
| `arb` | `src/arbitrage/index.ts` → `ArbitrageEngine` | Cross-exchange arb → Step 8 |
| `live` | `src/core/BotEngine.ts` → `BotEngine.start()` | **⚠️ USER CONFIRM** → Step 8 |

**BotEngine composition (live mode):**
```
BotEngine
├── IStrategy (from strategies/)
├── IDataProvider (LiveDataProvider via CCXT)
├── IExchange (via exchange-connection-pool)
├── RiskManager (SL/TP/trailing/daily limit)
├── OrderManager (order lifecycle)
├── PluginManager (plugin system)
├── AgentEventBus (A2UI events)
├── SignalExplainer (rationale generation)
├── TradeAuditLogger (audit trail)
├── AutonomyController (permission dial)
├── SignalMesh (netdata signal routing)
├── TickStore (time-series storage)
└── HealthManager (exchange health)
```

**A2UI event on execution:** `TRADE_EXECUTED`
```typescript
{ type: 'TRADE_EXECUTED', orderId, side, symbol, amount, price, fee, pnl }
```

### 8. CONTINUOUS: Live Monitor (if paper/arb/live)

**Maps to:** `/bootstrap:auto:parallel` Step 9 (Onboarding = ongoing)

**Modules:**
- `src/netdata/HealthManager.ts` → exchange health polling
- `src/netdata/SignalMesh.ts` → real-time signal routing
- `src/netdata/TickStore.ts` → price time-series
- `src/a2ui/surface-manager.ts` → dashboard rendering

**Circuit breakers (auto-halt conditions):**
- Daily loss ≥ `dailyLossLimitUsd` → `RISK_ALERT` + halt
- Drawdown ≥ 10% → `ESCALATION` (severity: critical) + auto-downgrade autonomy
- Exchange disconnect → `ExchangeRouter` auto-failover
- WS disconnect → auto-reconnect (3 retries, exponential backoff)

**A2UI event:** `ESCALATION`
```typescript
{
  type: 'ESCALATION', severity: 'critical',
  reason: 'Daily loss limit hit: -$102.50',
  suggestedAction: 'Close all positions',
  autoHalted: true
}
```

### 9. SEQUENTIAL: Performance Review

**Maps to:** `/bootstrap:auto:parallel` Step 7 (Code Review)

**Module:** `src/reporting/PerformanceAnalyzer.ts`
- Win Rate, Sharpe, Sortino, Calmar, Max DD
- Per-pair breakdown
- Per-exchange breakdown
- Fee + slippage impact analysis
- `src/a2ui/trade-audit-logger.ts` → full audit trail

### 10. FINAL: Report & Decision

**Maps to:** `/bootstrap:auto:parallel` Step 10 (Final Report)

**Module:** `src/reporting/HtmlReporter.ts` + `src/reporting/ConsoleReporter.ts`

Save: `plans/reports/trading-auto-parallel-{date}.md`

```
## Trading Session Report — {date}
🤖 Autonomy: {level} | Mode: {mode}
📊 Pairs: {pairs} | Exchanges: {exchanges}

### Signals
| Pair | Signal | Confidence | Strategy Votes |
|------|--------|------------|----------------|

### Trades
| # | Pair | Side | Entry | Exit | P&L | Fee |
|---|------|------|-------|------|-----|-----|

### Performance
| Metric | Value |
|--------|-------|
| Net P&L | |
| Win Rate | |
| Sharpe | |
| Max DD | |

### Circuit Breaker Events
- {timestamp}: {event}

### Recommendations
1. ...

→ Next: `/trading:auto:parallel {pairs} {mode}` to continue
→ Adjust: `/trading:auto {pair} {mode}` for single-pair focus
→ Quick check: `/trading:auto:fast {pair}` for instant analysis
```

---

## PARALLEL EXECUTION MAP

```
Step 1:  [Health Check]                              ← GATE (sequential)
              │ ✅
Step 2:  [Scan Tech] ║ [Scan Spreads]                ← 2 researcher agents
              │ merge
Step 3:  [Signal Consensus]                          ← SignalGenerator.aggregate()
              │ top signals
Step 4:  [Plan A] ║ [Plan B] ║ [Plan C]              ← planner agents (parallel)
              │ user approval (per AutonomyLevel)
Step 5:  [Risk Gate]                                 ← RiskManager (sequential)
              │ ✅
Step 6:  [Backtest A] ║ [Backtest B] ║ [Backtest C]  ← tester agents (parallel)
              │ all pass criteria
Step 7:  [Execute]                                   ← BotEngine / PaperEngine / ArbEngine
              │
Step 8:  [Monitor]                                   ← continuous (HealthManager + SignalMesh)
              │ session end
Step 9:  [Review]                                    ← PerformanceAnalyzer
              │
Step 10: [Report]                                    ← HtmlReporter + ConsoleReporter
```

## SAFETY INVARIANTS

```
1. DEFAULT_MODE = backtest (KHÔNG real money unless explicit)
2. DEFAULT_AUTONOMY = ACT_CONFIRM (user approves each trade)
3. CIRCUIT_BREAKERS = always active (cannot disable in live mode)
4. RISK_ESCALATION = auto-downgrade autonomy on risk events
5. DAILY_LOSS_LIMIT = $100 default (configurable)
6. MAX_RISK_PER_TRADE = 2% of balance
7. AUDIT_TRAIL = every action logged via TradeAuditLogger
8. LIVE_MODE = requires explicit "yes" confirmation
```

## DEFAULT CONFIG

```
Pairs: BTC/USDT, ETH/USDT
Exchanges: binance, okx, bybit
Mode: backtest
Autonomy: ACT_CONFIRM
Risk/trade: 2%
Daily loss: $100
Consensus: 0.6 (60%)
Min votes: 2
SL: 2% | TP: 5%
R:R min: 1:1.5
Backtest Sharpe min: 1.0
Backtest WR min: 55%
Backtest DD max: 10%
```
