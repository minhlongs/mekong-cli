# Polymarket Integration Implementation Plan

**Date:** March 22, 2026
**Target:** $1M ARR via cross-market arbitrage + binary market making
**Effort:** 5-8 days | **Team:** 1 senior + 1 mid dev
**Status:** Ready for Phase 1 kickoff

---

## PHASE 1: STUB → REAL (Days 1-2)

**Goal:** Deploy orders to Polymarket testnet, handle settlements.

### Task 1.1: WebSocket Feed for Polymarket Prices
**File:** `src/feeds/polymarket-ws-feed.ts`
**Dependencies:** @polymarket/clob-client (already installed)

```typescript
// Pseudo-structure
class PolymarketWebSocketFeed {
  // Subscribe to orderbook updates for market IDs
  async subscribe(marketId: string): Promise<OrderBook>

  // Parse CLOB orderbook into { bid, ask, timestamp }
  private parseOrderBook(data: CLOBOrderBook): PricePoint

  // Emit tick events (compatible with existing TickStore)
  private emit('tick', PricePoint)
}
```

**Subtasks:**
- [ ] Connect to `https://clob.polymarket.com/ws` WebSocket
- [ ] Parse orderbook updates → PricePoint format
- [ ] Auto-reconnect + heartbeat (mirror Binance/OKX logic)
- [ ] Test with 5 sample markets (2024 Election, Bitcoin price, etc.)

**Test file:** `tests/feeds/polymarket-ws-feed.test.ts`

---

### Task 1.2: CLOB Order Signer
**File:** `src/execution/polymarket-signer.ts`
**Dependencies:** ethers.js v6, @polymarket/clob-client

```typescript
class ClobSignerService {
  constructor(privateKey: string) // Polygon wallet private key

  // Sign CLOB order with ECDSA
  async signOrder(order: CLOBOrder): Promise<SignedCLOBOrder>

  // Verify signature (for testing)
  async verifySignature(signed: SignedCLOBOrder): Promise<boolean>
}
```

**Subtasks:**
- [ ] Initialize ethers Wallet from PRIVATE_KEY env var
- [ ] Map CLOBOrder fields → EIP-712 signature format
- [ ] Add nonce management (prevent replay attacks)
- [ ] Test signing 10x sample orders, verify with CLOB API

**Test file:** `tests/execution/polymarket-signer.test.ts`

---

### Task 1.3: Replace Stub PolymarketAdapter
**File:** `src/execution/polymarket-adapter.ts` (rewrite existing stub)
**Dependencies:** ClobSignerService, @polymarket/clob-client

```typescript
class PolymarketAdapter implements IExchangeAdapter {
  constructor(signer: ClobSignerService, config: ExecConfig)

  // Place limit order on CLOB
  async placeOrder(order: Order): Promise<string> // returns orderId

  // Cancel order
  async cancelOrder(orderId: string, marketId: string): Promise<boolean>

  // Get order status
  async getOrderStatus(orderId: string): Promise<OrderStatus>

  // Fetch current positions (from contract)
  async getPositions(): Promise<Position[]>
}
```

**Subtasks:**
- [ ] Implement `placeOrder()` → sign + submit via CLOB HTTP API
- [ ] Implement `cancelOrder()` → sign + submit cancellation
- [ ] Add error handling for CLOB-specific errors (invalid balance, mint constraints)
- [ ] Fetch wallet balance → validate before order submission
- [ ] Test vs. testnet: place, cancel, refund flow

**Test file:** `tests/execution/polymarket-adapter.test.ts`

---

### Task 1.4: Settlement Event Listener
**File:** `src/settlement/settlement-listener.ts`
**Dependencies:** ethers.js (CTF contract interface), @polymarket/clob-client

```typescript
class SettlementListener {
  // Subscribe to resolution events for market IDs
  async watchMarketResolution(marketId: string): Promise<void>

  // Fetch settlement price + outcome
  async getSettlement(marketId: string): Promise<Settlement>

  // Calculate realized P&L for position
  async realizePosition(position: Position, settlement: Settlement): Promise<PnL>
}
```

**Subtasks:**
- [ ] Subscribe to CTF contract events (on Polygon RPC)
- [ ] Parse resolution event → outcome (YES/NO) + price
- [ ] Calculate realized P&L: (outcome_price - entry_price) × quantity
- [ ] Update database: mark trade as settled
- [ ] Test with 3 resolved markets from Polymarket history

**Test file:** `tests/settlement/settlement-listener.test.ts`

---

### Task 1.5: Integration Test (Phase 1 Validation)
**File:** `tests/integration/polymarket-e2e-phase1.test.ts`

**Test Flow:**
```
1. Fund testnet wallet with USDC.e
2. Subscribe to BTC market orderbook
3. Place limit order (long YES at 0.50)
4. Check order status
5. Cancel order
6. Verify wallet balance refunded
7. Cleanup
```

**Expected Result:** ✅ All 5 operations succeed on testnet.

---

## PHASE 2: BINARY ARBITRAGE (Days 3-4)

**Goal:** Auto-detect YES/NO price inefficiencies, execute atomic 2-leg arbs.

### Task 2.1: Binary Opportunity Detector
**File:** `src/arbitrage/binary-opportunity-detector.ts`
**Dependencies:** PolymarketWebSocketFeed

```typescript
class BinaryArbitrageDetector {
  // Scan YES/NO pair prices
  async detectOpportunities(marketId: string): Promise<BinaryOpportunity[]>

  // Check: YES_price + NO_price ≠ 1.0 (inefficiency)
  private checkImbalance(yesBid: number, yesAsk: number,
                         noBid: number, noAsk: number): number // imbalance %

  // Calculate risk-adjusted profit
  private scoreOpportunity(opp: BinaryOpportunity): number // 0-100
}
```

**Subtasks:**
- [ ] Fetch YES + NO orderbooks for a market
- [ ] Calculate mint constraint: `YES + NO = 1.00` (perfect pricing)
- [ ] Detect imbalance: `|YES + NO - 1.00| > tolerance` (e.g., 0.1%)
- [ ] Score by: profit % − fees − slippage
- [ ] Scan top 10 markets every 5 seconds
- [ ] Test vs. live testnet: detect 5+ real opportunities in 1 hour

**Test file:** `tests/arbitrage/binary-opportunity-detector.test.ts`

---

### Task 2.2: Binary Arbitrage Executor
**File:** `src/arbitrage/binary-arbitrage-executor.ts`
**Dependencies:** PolymarketAdapter, PositionManager

```typescript
class BinaryArbitrageExecutor {
  // Execute atomic 2-leg arb: long YES, short NO (or vice versa)
  async execute(opp: BinaryOpportunity): Promise<ExecutionResult>

  // Place both orders, monitor fills
  private async placeAndWait(leg1: Order, leg2: Order): Promise<[orderId, orderId]>

  // Rollback on partial fill
  private async rollback(filledLeg: ExecutedLeg): Promise<void>
}
```

**Subtasks:**
- [ ] Implement atomic 2-leg placement (Promise.all with timeout)
- [ ] Add rollback: if one leg fails, cancel the other + refund
- [ ] Track execution cost (slippage, fees)
- [ ] Update position manager with both legs
- [ ] Add max daily loss circuit breaker
- [ ] Test vs. testnet: execute 5 arbs, verify P&L

**Test file:** `tests/arbitrage/binary-arbitrage-executor.test.ts`

---

### Task 2.3: Integration with Existing Risk Framework
**File:** Modified `src/risk/position-manager.ts`

**Changes:**
- [ ] Add binary position type (distinct from perpetual futures)
- [ ] Calculate unrealized P&L: `(YES_price - entry_price) × qty` for long YES
- [ ] Mark position as "awaiting settlement" when both legs filled
- [ ] On settlement event, close position + realize P&L

---

### Task 2.4: Dashboard Updates
**File:** Modified `dashboard/src/stores/trading-store.ts`

**Changes:**
- [ ] Add Polymarket position view (market name, YES/NO, entry price, current P&L)
- [ ] Add settlement countdown (days until resolution)
- [ ] Add binary market heat map (shows all markets sorted by imbalance %)

**UI Components:**
- [ ] PolymarketPositionCard
- [ ] BinaryMarketHeatmap

---

### Task 2.5: Phase 2 Integration Test
**File:** `tests/integration/polymarket-e2e-phase2.test.ts`

**Test Flow:**
```
1. Subscribe to 5 markets
2. Detect imbalance in 1 market (manually inject for test)
3. Score opportunity
4. Execute 2-leg arb (both orders placed)
5. Monitor fills + settlement
6. Verify P&L calculation
7. Cleanup
```

**Expected Result:** ✅ Full arb flow succeeds with positive P&L.

---

## PHASE 3: BINARY MARKET MAKING (Days 5-7)

**Goal:** Passively provide liquidity at 1-2% spreads, earn statistical edge.

### Task 3.1: Probability Calibration Engine
**File:** `src/strategies/probability-calibrator.ts`
**Dependencies:** External data sources (Twitter API, Metaculus, etc.)

```typescript
class ProbabilityCalibrator {
  // Fetch external probability estimates
  async getExternalProbability(marketId: string): Promise<number> // 0-1

  // Source: Twitter sentiment, Metaculus, historical resolution accuracy
  // Compare vs market price → identify edge
  async calibrate(marketId: string): Promise<{
    externalProb: number,
    marketProb: number,
    edge: number, // percentage points of edge
    confidence: number // 0-100, based on data quality
  }>
}
```

**Data Sources:**
- Twitter sentiment API (trending keywords for event)
- Metaculus community forecast
- Polling aggregators (FiveThirtyEight for elections)
- Historical resolution accuracy (Polymarket bots)
- On-chain signals (whale transactions, borrowing rates)

**Subtasks:**
- [ ] Integrate Twitter API for sentiment (keywords: "Bitcoin", "election", etc.)
- [ ] Fetch Metaculus forecast (public API)
- [ ] Historical accuracy baseline (Polymarket past 30 days)
- [ ] Score confidence: high = multiple data sources agree
- [ ] Test calibration on 10 markets vs. ground truth (post-settlement)

**Test file:** `tests/strategies/probability-calibrator.test.ts`

---

### Task 3.2: Binary Market Maker Strategy
**File:** `src/strategies/binary-market-maker.ts`
**Dependencies:** ProbabilityCalibrator, PolymarketAdapter, RegimeDetector

```typescript
class BinaryMarketMaker implements IStrategy {
  async onCandle(candle: Candle): Promise<Signal[]>

  // MM logic: place BID/ASK around fair value
  private calculateFairValue(prob: number): number

  // If market prob < external prob + edge margin → place BID
  // If market prob > external prob - edge margin → place ASK
  private generateMMOrders(fair: number, spread: number): [BidOrder, AskOrder]

  // Position sizing: Kelly fraction of capital
  private getPositionSize(capital: number, edge: number, confidence: number): number
}
```

**Subtasks:**
- [ ] Calculate fair value: `price = probability × $1.00`
- [ ] Generate MM orders: spread around fair (adaptive based on regime)
- [ ] Position sizing: Kelly Criterion with edge estimate
  - `f = (edge % − fees %) / odds` → fraction of capital per side
- [ ] Inventory management: if holds 100+ YES contracts, only post BID (reduce inventory)
- [ ] Test on testnet: maintain spreads 1-2%, achieve 30%+ fill rate

**Test file:** `tests/strategies/binary-market-maker.test.ts`

---

### Task 3.3: Spread Monitoring & Rebalancing
**File:** `src/strategies/mm-rebalancer.ts`

```typescript
class MMRebalancer {
  // Monitor positions + orderbook
  async rebalancePositions(): Promise<void>

  // If probability changes, update fair value + orders
  private async adjustOrders(newFair: number, oldFair: number): Promise<void>

  // If inventory skewed, reduce size on favored side
  private async balanceInventory(): Promise<void>
}
```

**Subtasks:**
- [ ] Check every 10 seconds: probability estimate vs market price
- [ ] If > 2% divergence, cancel old orders + place new ones
- [ ] If holding >100 YES, reduce BID size (make it less attractive)
- [ ] Same for NO position → reduce ASK size
- [ ] Test: rebalancer responds within 30 seconds of price shift

**Test file:** `tests/strategies/mm-rebalancer.test.ts`

---

### Task 3.4: Dashboard Enhancements
**File:** Modified `dashboard/src/stores/trading-store.ts`

**Changes:**
- [ ] MM active positions view (market, fair value, current bid/ask, inventory)
- [ ] Probability vs market price chart (shows edge opportunity)
- [ ] Daily P&L by strategy (arb vs MM)
- [ ] Win rate + fill rate metrics

**UI Components:**
- [ ] MMPositionCard
- [ ] ProbabilityDivergenceChart
- [ ] MMMetricsPanel

---

### Task 3.5: Phase 3 Integration Test + Go-Live Validation
**File:** `tests/integration/polymarket-e2e-phase3.test.ts`

**Test Scenarios:**
```
Scenario 1: MM provides spreads, market taker hits bid
  - Start with 1000 USDC capital
  - Place 10 USDC BID at 0.55 (YES market prob 0.60)
  - Simulate market taker hitting bid (buys 10 YES from us)
  - Check: position = +10 YES, cash = 945 USDC (10 filled × 0.55)

Scenario 2: Probability shift → rebalance
  - Market prob moves 0.60 → 0.70
  - Fair value shifts → cancel old BID/ASK, place new ones
  - Check: new orders reflect 0.70 probability

Scenario 3: Inventory rebalance
  - Hold 200 YES, prob is 0.60 (fair)
  - System reduces BID size (too much YES)
  - Check: BID filled at lower rates vs ASK

Scenario 4: Settlement realized P&L
  - Market resolves YES
  - Position closes: +200 YES × $1.00 = $200
  - Check: P&L correctly calculated vs entry prices
```

**Expected Result:** ✅ All 4 scenarios pass, MM bot runs 24h+ with positive Sharpe ratio.

---

## TESTING MATRIX

| Phase | Unit Tests | Integration Tests | Testnet Validation |
|-------|------------|-------------------|-------------------|
| 1 | WebSocket, Signer, Adapter, Listener | E2E order flow | Place/cancel 5 trades |
| 2 | Detector, Executor, Risk | Full arb flow | Execute 5 arbs, +P&L |
| 3 | Calibrator, MM, Rebalancer | MM + settlement | 24h MM run, Sharpe > 0.5 |

**Total Test Coverage Goal:** 95%+ (maintain consistency with existing codebase)

---

## DEPLOYMENT CHECKLIST

### Pre-Testnet (Phase 1-2)
- [ ] All unit tests pass locally
- [ ] Integration tests pass vs. mock CLOB (hardcoded orderbook)
- [ ] Private key handling reviewed (no logs, env vars only)
- [ ] Code review: ECDSA signing, error handling

### Testnet (Phase 2-3)
- [ ] Fund testnet wallet with USDC.e (testnet faucet)
- [ ] Bot places + cancels 10 orders successfully
- [ ] Bot executes 2-leg arb with positive P&L (dry-run first)
- [ ] MM bot runs 24h with spreads 1-2% and 30%+ fill rate
- [ ] Settlement events trigger correctly post-resolution
- [ ] Dashboard reflects real-time positions + P&L

### Mainnet (Go-Live)
- [ ] License gate: Polymarket features locked behind PRO tier
- [ ] Capital deployment: Start with $50K (arb + MM blend)
- [ ] Monitoring: Grafana dashboard for P&L, execution latency, error rates
- [ ] On-call: 24/7 ops for first 2 weeks
- [ ] Rollback plan: Manual halt + close all positions if issues detected

---

## EFFORT BREAKDOWN

| Task | Days | Dev | Notes |
|------|------|-----|-------|
| 1.1 WebSocket feed | 0.5 | Mid | Mirror existing Binance logic |
| 1.2 CLOB signer | 0.75 | Senior | ECDSA + nonce management |
| 1.3 Adapter | 0.75 | Senior | Error handling, balance checks |
| 1.4 Settlement listener | 0.5 | Mid | Contract ABI parsing |
| 1.5 Phase 1 test | 0.5 | Mid | End-to-end validation |
| **Phase 1 Total** | **2** | 1S+1M | |
| 2.1 Binary detector | 1 | Mid | Imbalance calculation |
| 2.2 Binary executor | 1 | Senior | Rollback logic, atomicity |
| 2.3 Risk integration | 0.5 | Mid | Position manager updates |
| 2.4 Dashboard | 0.5 | Mid | Heat map + position view |
| 2.5 Phase 2 test | 0.5 | Mid | Arb flow validation |
| **Phase 2 Total** | **3** | 1S+1M | |
| 3.1 Probability calibrator | 1 | Senior | API integrations (Twitter, Metaculus) |
| 3.2 MM strategy | 1.5 | Senior | Kelly sizing, spread logic |
| 3.3 MM rebalancer | 0.75 | Mid | Inventory tracking |
| 3.4 Dashboard MM | 0.75 | Mid | Probability chart |
| 3.5 Phase 3 test + go-live | 1 | Senior | Testnet validation, monitoring setup |
| **Phase 3 Total** | **5** | 1S+1M | |
| **Grand Total** | **10** | 3S+3M | But sequential = 5-8 calendar days |

**Timeline (with parallelization):**
- Day 1: Phase 1 (both devs, no parallelization)
- Days 2-3: Phase 2 (can overlap Phase 1 testnet validation)
- Days 4-5: Phase 3 (Phase 2 testnet running in background)

---

## REVENUE IMPACT

### Assumptions
- **Capital deployed:** $200K (mix of internal + customer partnerships)
- **Arb strategy:** 15-20% monthly ROI (conservative for binary markets)
- **MM strategy:** 5-10% monthly ROI on $100K tied up
- **Commission:** 20% of profits (to platform)

### Projections
```
Monthly:
- Arb profit: $200K × 0.175 = $35K × 0.20 = $7K platform revenue
- MM profit: $100K × 0.075 = $7.5K × 0.20 = $1.5K platform revenue
- Subscriptions: 50 PRO users × $99/mo = $4.95K
- Total monthly: ~$13.5K

Annual: ~$160K direct revenue (before market expansion)

With 3x capital + user growth:
- Year 2: $50K+/month ($600K ARR)
```

---

## RISK MITIGATION

| Risk | Mitigation |
|------|-----------|
| Private key compromised | Use hardware wallet proxy (Ledger via WalletConnect) |
| CLOB order timeout | Add client-side order timeout, auto-cancel stale orders |
| Settlement delays | Track position as "pending settlement" separately; don't double-count |
| Slippage blowups | Conservative position sizing, wide tolerance bands during testing |
| Probability calibration drift | Validate against ground truth weekly (post-settlement accuracy) |
| Capital loss | Start with $50K, scale only after 4 weeks of positive P&L |

---

## SUCCESS CRITERIA (Phase 3 Completion)

- ✅ 95%+ test coverage
- ✅ 24h+ testnet run: arb bot executes 10+ profitable trades, MM bot maintains spreads
- ✅ Settlement: 5+ markets resolve, P&L correctly calculated
- ✅ Dashboard: Live position tracking, P&L attribution by strategy
- ✅ Security: Private key handling reviewed, no secrets in logs
- ✅ Documentation: SOPs written for trader deployment
- ✅ License gating: Polymarket features PRO tier only
- ✅ Monitoring: Grafana dashboard for mainnet go-live
- ✅ Rollback plan: Manual halt + close positions documented

---

## NEXT STEPS

1. **Approve plan** — leadership review, allocate budget
2. **Assign resources** — 1 senior (ECDSA + arb logic), 1 mid (WebSocket + dashboard)
3. **Kick Phase 1** — target 2-day completion
4. **Parallel Phase 2** — detector + executor while Phase 1 testnet runs
5. **Phase 3 go-live** — after 5 days, launch with $50K capital

---

**Plan Generated:** 2026-03-22 23:41
**Estimated Start Date:** 2026-03-24
**Target Completion:** 2026-03-31 (8 calendar days)
