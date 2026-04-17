---
description: ⚡⚡⚡⚡⚡⚡ AGI Trading — full autonomous loop, self-learning, auto-escalation, circuit breakers only safety
argument-hint: [pairs] [mode: paper|arb|live] [budget: $amount] [duration: Xh]
---

**Ultrathink parallel** AGI autonomous trading: <args>$ARGUMENTS</args>

**CWD:** `apps/algo-trader`
**AUTONOMY:** `AUTONOMOUS` — NO human confirmation per trade. Circuit breakers = ONLY safety.
**⚠️ LIVE MODE:** Requires explicit "I understand the risks" before start.

---

## AGI vs AUTO — What's Different

| Feature | `/trading:auto:parallel` | `/trading:auto:agi` |
|---------|--------------------------|---------------------|
| Autonomy | ACT_CONFIRM (user approves) | AUTONOMOUS (no approval) |
| Duration | Single session | Continuous loop (Xh) |
| Learning | None | Self-learning: win→loosen, loss→tighten |
| Escalation | Manual | Auto-downgrade on risk events |
| Recovery | Manual restart | Auto-recovery + strategy rotation |
| Gate count | 5 gates (user checks) | 2 gates (health + circuit breaker) |

**Mapping:** This is `--dangerously-skip-permissions` for trading.
- ClaudeKit Coder: `claude --dangerously-skip-permissions` = runs without asking
- ClaudeKit Trader: `/trading:auto:agi` = trades without asking (circuit breakers active)

---

## ARCHITECTURE — Self-Learning Loop

```
                    ┌──────────────────────────────┐
                    │         AGI MAIN LOOP         │
                    │  AutonomyLevel.AUTONOMOUS     │
                    └──────────────┬───────────────┘
                                   │
         ┌─────────────────────────┼─────────────────────────┐
         ▼                         ▼                         ▼
   [SCAN CYCLE]              [EXECUTE CYCLE]           [LEARN CYCLE]
   Every 60s:                Per signal:               Per trade result:
   - indicators.ts           - BotEngine.start()       - recordSuccess()
   - SignalGenerator          - TradeExecutor            - escalate() on loss
   - regime detection         - OrderManager             - strategy weight adjust
         │                         │                         │
         └─────────────┬──────────┘                         │
                        │                                    │
                  [CIRCUIT BREAKER]◄─────────────────────────┘
                  Always watching:
                  - dailyLossLimit ($100)
                  - maxDrawdown (10%)
                  - exchangeDown → failover
                  - 3 consecutive losses → ESCALATE
```

## Source Modules

| Component | File | Method |
|-----------|------|--------|
| Autonomy dial | `src/core/autonomy-controller.ts` | `AutonomyController` |
| Event bus | `src/a2ui/agent-event-bus.ts` | `AgentEventBus.emit()` |
| Signal explainer | `src/a2ui/signal-explainer.ts` | `SignalExplainer` |
| Audit logger | `src/a2ui/trade-audit-logger.ts` | `TradeAuditLogger` |
| Bot engine | `src/core/BotEngine.ts` | `BotEngine.start()` |
| Trade executor | `src/core/bot-engine-trade-executor-and-position-manager.ts` | `BotTradeExecutor` |
| Plugin system | `src/core/bot-engine-plugins.ts` | `PluginManager` |
| Pipeline | `src/pipeline/workflow-pipeline-engine.ts` | `createTradingPipeline()` |
| Signal mesh | `src/netdata/SignalMesh.ts` | `SignalMesh` |
| Tick store | `src/netdata/TickStore.ts` | `TickStore` |
| Health mgr | `src/netdata/HealthManager.ts` | `HealthManager` |
| Exchange pool | `src/execution/exchange-connection-pool.ts` | `ExchangeConnectionPool` |
| Exchange router | `src/execution/exchange-router-with-fallback.ts` | `ExchangeRouter` |
| Exchange health | `src/execution/exchange-health-monitor.ts` | `ExchangeHealthMonitor` |
| Live manager | `src/execution/live-exchange-manager.ts` | `LiveExchangeManager` |
| Arb engine | `src/arbitrage/index.ts` | `ArbitrageEngine` |
| Strategies | `src/strategies/*.ts` | `BaseStrategy` subclasses |
| Indicators | `src/analysis/indicators.ts` | `Indicators` |
| Signal gen | `src/core/SignalGenerator.ts` | `SignalGenerator.aggregate()` |
| Risk mgr | `src/core/RiskManager.ts` | `RiskManager` |
| Backtest | `src/backtest/BacktestEngine.ts` | `BacktestEngine` |
| Config schema | `src/utils/config-schema.ts` | Zod validation |
| Credentials | `src/utils/CredentialVault.ts` | `CredentialVault` |
| Sanitizer | `src/utils/trading-input-sanitizer-and-validator.ts` | input validation |

---

## PIPELINE — 8 Steps (Streamlined for AGI)

### 1. PREFLIGHT (one-time)
```bash
tsc --noEmit          # 0 errors
pnpm test 2>&1 | tail -3  # all PASS
```
- `HealthManager.getReport()` → all exchanges connected
- `CredentialVault` → API keys loaded
- `config-schema.ts` → Zod validates config
- `trading-input-sanitizer-and-validator.ts` → sanitize all inputs
- **GATE:** ALL green. Any fail → abort (not auto-fixable in AGI mode).

### 2. STRATEGY ENSEMBLE INIT
- `src/core/StrategyEnsemble.ts` → load all 4 strategies
- Initial weights: MacdBollingerRsi(0.30), RsiSma(0.25), Bollinger(0.25), MacdCrossover(0.20)
- `src/core/strategy-auto-detector.test.ts` → auto-detect best strategy per regime
- `src/core/strategy-config-cascade.ts` → config inheritance chain
- `AutonomyController` → set level `AUTONOMOUS` for all strategies

### 3. SCAN LOOP (continuous, every 60s)
For EACH pair, in parallel:
- `Indicators.rsi()`, `.sma()`, `.macd()`, `.bollingerBands()`, `.atr()`
- `SignalGenerator.aggregate(WeightedSignal[])` → consensus
- Regime detection → adjust strategy weights dynamically
- `SignalMesh` → route signals to interested subscribers
- `TickStore` → persist price data for learning

**No user interaction.** Signals auto-flow to Step 4.

### 4. AUTO-EXECUTE (per signal, NO confirmation)
Pipeline: `createTradingPipeline()` → Trigger → Signal → RiskCheck → Order → Report

- **Risk check (automated):**
  - `RiskManager.calculatePositionSize(balance, 2%, price)` → size
  - `RiskManager.checkStopLossTakeProfit()` → SL 2%, TP 5%
  - `RiskManager.isDailyLossLimitHit()` → budget guard
  - R:R ≥ 1:1.5 → auto-reject if not met

- **Execute:**
  - `BotTradeExecutor` → place order via `LiveExchangeManager`
  - `ExchangeRouter` → best exchange (liquidity + fees + health)
  - `OrderManager` → order lifecycle tracking

- **A2UI events (silent logging, no prompts):**
  - `TRADE_EXECUTED` → logged to audit trail
  - `TRADE_AUDIT` → undoable action record
  - `SIGNAL_RATIONALE` → why this trade was taken

### 5. CIRCUIT BREAKERS (always active, CANNOT disable)

| Breaker | Trigger | Action | Source |
|---------|---------|--------|--------|
| Daily loss | P&L ≤ -$budget | HALT all trading | `RiskManager.isDailyLossLimitHit()` |
| Max drawdown | DD ≥ 10% | HALT + close positions | `RiskManager.checkStopLossTakeProfit()` |
| Consecutive losses | 3 losses in row | `escalate()` → ACT_CONFIRM | `AutonomyController.escalate()` |
| Exchange down | health DEGRADED/DOWN | `ExchangeRouter` failover | `ExchangeHealthMonitor` |
| WS disconnect | no data 30s | auto-reconnect (3 retries) | `LiveExchangeManager` |
| Anomaly | price move >5% in 1min | PAUSE + alert | Custom detector |

**On HALT:** `ESCALATION` event (severity: critical, autoHalted: true)
**On ESCALATE:** autonomy auto-downgrades one level (AUTONOMOUS → ACT_CONFIRM)

### 6. SELF-LEARNING LOOP (per trade result)

```typescript
// After each trade completes:
if (trade.profitable) {
  autonomyController.recordSuccess(strategy);
  // After 5 consecutive wins → restore previous autonomy level
  // Increase winning strategy weight by 0.05
} else {
  autonomyController.escalate(strategy, `Loss: ${trade.pnl}`);
  // Decrease losing strategy weight by 0.05 (min 0.10)
  // 3 losses → downgrade to ACT_CONFIRM (user must approve)
}
```

**Strategy weight adaptation:**
- Win → weight += 0.05 (max 0.50)
- Loss → weight -= 0.05 (min 0.10)
- Weights auto-normalized to sum = 1.0
- Regime change → reset to defaults

**Autonomy adaptation:**
- 5 wins → `recordSuccess()` → may restore higher autonomy
- Risk event → `escalate()` → downgrade one level
- Critical event → force `OBSERVE` mode

### 7. CONTINUOUS MONITOR
- `HealthManager` → poll every 30s
- `SignalMesh` → real-time signal routing across strategies
- `TickStore` → persist all price data
- `A2UI SurfaceManager` → dashboard (if UI connected)
- Duration: runs for `Xh` (default 4h), then auto-stop

### 8. SESSION REPORT (on stop/halt)
- `PerformanceAnalyzer` → full metrics
- `TradeAuditLogger` → complete audit trail
- Strategy weight evolution (start → end)
- Autonomy level changes log
- Circuit breaker activations
- Save: `plans/reports/trading-agi-{date}.md`

---

## SAFETY HIERARCHY

```
Layer 1: CIRCUIT BREAKERS          ← hardware safety (CANNOT disable)
  │       dailyLoss, drawdown, consecutive losses
  │
Layer 2: AUTONOMY ESCALATION       ← adaptive safety
  │       auto-downgrade on risk events
  │       3 losses → ACT_CONFIRM → user must approve
  │
Layer 3: RISK MANAGER              ← per-trade safety
  │       position sizing, SL/TP, R:R validation
  │
Layer 4: EXCHANGE ROUTER           ← infrastructure safety
          failover, reconnect, health monitoring
```

**INVARIANT:** Even in AUTONOMOUS mode, Layers 1-4 are ALWAYS active.
**NO OVERRIDE.** No `--force`, no `--skip-safety`. These are hardcoded.

## DEFAULT CONFIG

```
Pairs: BTC/USDT, ETH/USDT
Exchanges: binance, okx, bybit
Mode: paper (AGI default = paper, NOT backtest)
Autonomy: AUTONOMOUS
Budget: $100/day
Duration: 4h
Risk/trade: 2%
SL: 2% | TP: 5%
Consensus: 0.6
Min votes: 2
Scan interval: 60s
Health poll: 30s
Max consecutive losses: 3 (→ escalate)
Auto-restore after: 5 wins
```

## USAGE

```bash
# Paper mode (safe default)
/trading:auto:agi BTC/USDT ETH/USDT paper $200 8h

# Arbitrage mode
/trading:auto:agi BTC/USDT arb $500 4h

# Live mode (requires explicit confirmation)
/trading:auto:agi BTC/USDT ETH/USDT live $100 2h
# → "⚠️ LIVE MODE: Real money. Circuit breakers active. Type 'I understand the risks' to proceed."

# Quick analysis then AGI
/trading:auto:fast BTC/USDT          # check market first
/trading:auto:agi BTC/USDT paper $100 4h  # then run AGI
```
