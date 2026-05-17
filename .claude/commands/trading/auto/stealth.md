---
description: ⚡⚡⚡⚡⚡⚡ Phantom Stealth Arbitrage — ẩn danh tàng hình, multi-exchange arb, không bị sàn phát hiện
argument-hint: [pairs] [exchanges: binance,okx,bybit] [budget: $amount] [duration: Xh]
---

**Ultrathink parallel** stealth arbitrage: <args>$ARGUMENTS</args>

**CWD:** `apps/algo-trader`
**MỤC TIÊU:** Chênh lệch giá cross-exchange, KHÔNG bị sàn detect là bot.
**TRIẾT LÝ:** 孫子兵法 虛實 — "Tỵ thực nhi kích hư" (Tránh chỗ mạnh, đánh chỗ yếu)

---

## STEALTH STACK — 10 Lớp Tàng Hình

```
Lớp 10: [Binh Pháp Strategy]     ← 13 chương Tôn Tử ánh xạ anti-detection
Lớp 9:  [Phantom Cloaking]       ← Session simulator + OTR + Adaptive rate
Lớp 8:  [Stealth Execution]      ← TWAP/VWAP/Iceberg + anti-pattern
Lớp 7:  [Fingerprint Masking]    ← Browser headers + session rotation
Lớp 6:  [Anti-Detection Safety]  ← Order randomizer safety layer
Lớp 5:  [Adaptive Circuit]       ← Per-exchange circuit breaker
Lớp 4:  [Atomic Executor]        ← Cross-exchange atomic orders
Lớp 3:  [Exchange Router]        ← Fallback + health routing
Lớp 2:  [Connection Pool]        ← CCXT connection management
Lớp 1:  [Gateway Middleware]     ← Portkey-inspired pipeline
```

## MODULE MAP — 15 Files Orchestrated

| # | Module | File | Chức năng |
|---|--------|------|-----------|
| 1 | `PhantomStealthMath` | `phantom-stealth-math.ts` | Poisson delay, log-normal sizing, round number avoidance |
| 2 | `StealthMiddleware` | `stealth-cli-fingerprint-masking-middleware.ts` | Browser UA, Accept-Language, Sec-Fetch-*, session rotation |
| 3 | `StealthAlgorithms` | `stealth-execution-algorithms.ts` | TWAP, VWAP, Iceberg + anti-pattern camouflage |
| 4 | `PhantomCloaking` | `phantom-order-cloaking-engine.ts` | Session simulator (20-90min on/5-20min off), OTR tracker, adaptive rate |
| 5 | `BinhPhapStealth` | `binh-phap-stealth-trading-strategy.ts` | 13-chapter stealth: terrain profiles per exchange |
| 6 | `AntiDetection` | `anti-detection-order-randomizer-safety-layer.ts` | Order randomizer safety |
| 7 | `CircuitBreaker` | `adaptive-circuit-breaker-per-exchange.ts` | Per-exchange adaptive circuit breaker |
| 8 | `AtomicExecutor` | `atomic-cross-exchange-order-executor.ts` | Simultaneous buy+sell cross-exchange |
| 9 | `ArbEngine` | `arbitrage-execution-engine.ts` | Master wiring: scanner→breaker→executor→stealth |
| 10 | `ArbScanner` | `realtime-arbitrage-scanner.ts` | Real-time spread detection |
| 11 | `FundingArb` | `funding-rate-arbitrage-scanner.ts` | Funding rate differential arb |
| 12 | `TriangularArb` | `triangular-arbitrage-live-scanner.ts` | Triangular arb paths |
| 13 | `SpreadCalc` | `fee-aware-cross-exchange-spread-calculator.ts` | Fee-inclusive spread calculation |
| 14 | `OrderBook` | `order-book-depth-analyzer.ts` | Depth analysis for slippage |
| 15 | `TelegramBot` | `telegram-trade-alert-bot.ts` | Silent alerts to Telegram |

---

## PIPELINE — 8 Steps

### 1. PREFLIGHT: Exchange Terrain Profiling (始計)

**Module:** `binh-phap-stealth-trading-strategy.ts` → `ExchangeTerrainProfile`

Per exchange, load profile:
```typescript
{
  id: 'binance',
  safeOrdersPerMin: number,      // conservative rate
  safeOrdersPerHour: number,
  minPairIntervalMs: number,     // min gap same pair
  detectsUniformSizes: boolean,  // needs log-normal
  detectsCancelReplace: boolean, // avoid cancel-replace
  highVolumeHoursUtc: number[],  // trade during these hours
  rateLimitPerMin: number,       // API limit
  riskLevel: 'low'|'medium'|'high'
}
```

```bash
tsc --noEmit                  # 0 errors
pnpm test --testPathPattern="phantom|stealth|arbitrage" 2>&1 | tail -5
```

**GATE:** All exchanges profiled + connected.

### 2. INIT: Stealth Engine Boot

Initialize ALL stealth layers in order:
```typescript
// 1. Gateway middleware pipeline
const gateway = new ExchangeGateway();
gateway.use(createStealthMiddleware({
  enableMicroDelay: true,         // Poisson inter-arrival
  targetCallsPerMin: 12,          // conservative
  enableSessionRotation: true,    // rotate identity every 20-90min
  injectBrowserHeaders: true,     // Chrome/Firefox/Safari UA
}));

// 2. Phantom cloaking engine
const phantom = new PhantomCloakingEngine({
  targetOrdersPerMin: 4,          // very conservative
  minSessionMs: 20 * 60_000,      // 20min sessions
  maxSessionMs: 90 * 60_000,      // 90min max
  minBreakMs: 5 * 60_000,         // 5min breaks
  maxBreakMs: 20 * 60_000,        // 20min breaks
  otrThreshold: 15,               // cancel ratio limit
  adaptiveRateFloor: 0.40,        // use 40-65% of rate limit
  adaptiveRateCeiling: 0.65,
  sizeSigma: 0.25,                // log-normal spread
});

// 3. Binh Pháp strategy
const stealth = new BinhPhapStealthStrategy(exchangeProfiles);

// 4. Arbitrage execution engine
const arbEngine = new ArbitrageExecutionEngine({
  dryRun: false,                  // or true for paper mode
  enableStealth: true,            // activate all layers
  maxDailyLossUsd: budget,
  phantomConfig: { ... },
});
```

### 3. PARALLEL: Multi-Exchange Scan (謀攻 — Win Without Fighting)

3 scanners chạy parallel:

**Scanner A — Spot Spread:**
- `realtime-arbitrage-scanner.ts` → `RealtimeArbitrageScanner`
- Binance vs OKX vs Bybit bid/ask spread
- `fee-aware-cross-exchange-spread-calculator.ts` → net profit after fees
- `order-book-depth-analyzer.ts` → slippage estimation

**Scanner B — Funding Rate:**
- `funding-rate-arbitrage-scanner.ts` → `FundingRateArbitrageScanner`
- Perpetual futures funding rate differentials
- Cash-and-carry arb opportunities

**Scanner C — Triangular:**
- `triangular-arbitrage-live-scanner.ts` → `TriangularArbitrageLiveScanner`
- Intra-exchange triangular paths (BTC→ETH→USDT→BTC)
- Cross-exchange triangular hybrid

**Output:** Ranked opportunities sorted by net profit (after fees + slippage).

### 4. FILTER: Binh Pháp Stealth Assessment (兵勢 — Momentum)

For each opportunity:
```typescript
const plan = stealth.planExecution(exchange, size, pair);
// plan.shouldProceed — safe to trade?
// plan.delay — how long to wait (Poisson)
// plan.sizes[] — child order sizes (log-normal)
// plan.route — which exchange route
```

**Filters (ALL must pass):**
- Net profit ≥ 0.1% after fees + slippage
- Exchange terrain risk ≤ medium
- Within high-volume hours UTC (兵勢: trade when volume hides you)
- OTR ratio < 15% (avoid cancel-heavy patterns)
- Phantom session active (not on break)

### 5. EXECUTE: Phantom Cloaked Atomic Execution (虛實 — Deception)

For each approved opportunity:

```typescript
// Step 1: Phantom decision
const decision = phantom.cloak(exchange, baseSize, pair);
if (!decision.proceed) {
  // On break or OTR too high → skip
  continue;
}

// Step 2: Stealth sizing (log-normal + round number avoidance)
const size = decision.size; // already stealth-processed

// Step 3: Wait stealth delay (Poisson process)
await sleep(decision.delayMs);

// Step 4: Choose execution algorithm
const execPlan = StealthExecutionAlgorithms.createTwapPlan(size, 60_000, 5);
// Or: createVwapPlan() for large orders
// Or: createIcebergPlan() for limit orders

// Step 5: Anti-pattern camouflage
const cloakedPlan = StealthExecutionAlgorithms.applyAntiPatternCamouflage(execPlan);

// Step 6: Atomic cross-exchange execution
const result = await atomicExecutor.execute({
  buyExchange, sellExchange, pair, size: decision.size
});
```

**Order Cloaking Techniques Active:**
| Technique | Module | What It Does |
|-----------|--------|-------------|
| Poisson timing | `phantom-stealth-math.ts` | Non-uniform intervals (clustering + gaps) |
| Log-normal sizing | `phantom-stealth-math.ts` | Natural size distribution |
| Round number kill | `phantom-stealth-math.ts` | No 0.01000, 0.50000, etc. |
| Browser fingerprint | `stealth-cli-fingerprint-masking-middleware.ts` | Chrome/Firefox UA + headers |
| Session rotation | `stealth-cli-fingerprint-masking-middleware.ts` | New identity every 20-90min |
| TWAP slicing | `stealth-execution-algorithms.ts` | Split big orders over time |
| Iceberg tips | `stealth-execution-algorithms.ts` | Show small, hide big |
| Human hesitation | `stealth-execution-algorithms.ts` | Random 1.5-3x pauses |
| Session breaks | `phantom-order-cloaking-engine.ts` | 5-20min "rest" periods |
| OTR monitoring | `phantom-order-cloaking-engine.ts` | Keep cancel ratio <15% |
| Adaptive rate | `phantom-order-cloaking-engine.ts` | Use 40-65% of rate limit |
| Exchange terrain | `binh-phap-stealth-trading-strategy.ts` | Per-exchange risk profiles |
| Volume timing | `binh-phap-stealth-trading-strategy.ts` | Trade during peak hours |

### 6. MONITOR: Ghost Mode Dashboard (行軍 — Movement)

**Modules:**
- `HealthManager` → exchange health
- `PhantomCloakingEngine.getStatus()` → session/OTR/rate status
- `telegram-trade-alert-bot.ts` → silent Telegram alerts (no console spam)

**Dashboard (silent — log only, no stdout):**
```
[PHANTOM] Session: ACTIVE (42min) | Break: 0min
[PHANTOM] OTR: binance=3.2% okx=1.8% bybit=2.1% (all <15% ✅)
[PHANTOM] Rate: binance=52% okx=48% bybit=55% (adaptive)
[PHANTOM] Trades: 7 exec | 5 win | 2 loss | PnL: +$23.45
[PHANTOM] Next break: ~18min | Daily budget: $76.55 remaining
```

### 7. CIRCUIT BREAKERS (軍形 — Defense)

| Breaker | Trigger | Action |
|---------|---------|--------|
| Daily loss | P&L ≤ -$budget | HALT all |
| Exchange 429 | Rate limit hit | `phantom.recordRateWarning()` → drop rate 5% |
| OTR spike | Cancel/order >15% | Block orders on that exchange |
| Session timer | Duration expired | Phantom session break (5-20min) |
| Spread vanish | Spread < fee cost | Skip (don't chase) |
| Exchange down | Health DEGRADED | `ExchangeRouter` failover |

### 8. REPORT (用間 — Intelligence)

Save: `plans/reports/trading-stealth-arb-{date}.md`

```
## Phantom Stealth Arb Report — {date}
🥷 Duration: {Xh} | Sessions: {N} | Breaks: {N}

### Stealth Metrics
| Exchange | Orders | OTR | Rate Used | Warnings |
|----------|--------|-----|-----------|----------|

### Trades
| # | Buy@Exchange | Sell@Exchange | Pair | Spread | Net P&L |
|---|-------------|---------------|------|--------|---------|

### Performance
| Metric | Value |
|--------|-------|
| Net P&L | +$XX.XX |
| Win Rate | XX% |
| Avg Spread | 0.XX% |
| Phantom Sessions | N |
| Breaks Taken | N |
| Rate Warnings | N |
| Detection Risk | LOW ✅ |
```

---

## BINH PHÁP 13-CHAPTER STEALTH MAP

| Ch | Principle | Implementation |
|----|-----------|----------------|
| 始計 | Assessment | Exchange terrain profiling before ANY order |
| 作戰 | Resources | API budget: use 40-65% of rate limit only |
| 謀攻 | Win w/o Fight | Passive scan > aggressive trading. Skip low-profit |
| 軍形 | Defense | 4-layer circuit breaker stack |
| 兵勢 | Momentum | Trade only during high-volume hours (blend in) |
| 虛實 | Deception | TWAP/VWAP/Iceberg splits + log-normal sizing |
| 軍爭 | Maneuver | Rotate exchanges: don't hammer one exchange |
| 九變 | Adapt | Dynamic strategy: regime→algorithm selection |
| 行軍 | Movement | Vary routing: A→B, B→C, C→A (not always A→B) |
| 地形 | Terrain | Per-exchange profiles (Binance strict, OKX relaxed) |
| 九地 | Escalation | 3 losses → downgrade autonomy → user confirm |
| 火攻 | Strike | Execute ONLY >0.1% net profit opportunities |
| 用間 | Intelligence | Monitor exchange ToS changes, new restrictions |

---

## DEFAULT CONFIG

```
Pairs: BTC/USDT, ETH/USDT
Exchanges: binance, okx, bybit
Budget: $100/day
Duration: 4h
Mode: dry-run (paper arb, safe default)
Phantom rate: 4 orders/min
Session: 20-90min active, 5-20min break
OTR limit: 15%
Rate usage: 40-65% of exchange limit
Size sigma: 0.25 (log-normal)
Min profit: 0.1% net (after fees+slippage)
```

## USAGE

```bash
# Paper mode (safe — no real orders)
/trading:auto:stealth BTC/USDT ETH/USDT binance,okx,bybit $200 8h

# Live mode (real money + full stealth)
/trading:auto:stealth BTC/USDT live binance,okx $100 4h
# → "⚠️ LIVE STEALTH: Real money. Phantom cloaking active. Confirm to proceed."

# With funding rate arb
/trading:auto:stealth BTC/USDT funding binance,okx $500 12h

# Quick spread check first
/trading:auto:fast BTC/USDT        # check spreads
/trading:auto:stealth BTC/USDT ... # then run stealth
```
