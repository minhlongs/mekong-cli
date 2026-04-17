---
description: ⚡⚡⚡ Execution Specialist — order routing, fill rate, slippage analysis, exchange health, stealth execution
argument-hint: [action: routing|fills|slippage|health]
---

**Ultrathink** Execution analysis: <args>$ARGUMENTS</args>

**CWD:** `apps/algo-trader` | **REF:** `docs/trading-team-subordinates-sops.md` PART 4
**Reports to:** Trader (`/trading:auto`)

## Pipeline (4 steps)

### 1. ORDER ROUTING ANALYSIS
| Module | Function | Status |
|--------|----------|--------|
| `exchange-router-with-fallback.ts` | Exchange selection | 🟢/🔴 |
| `stealth-execution-algorithms.ts` | Order type optimization | 🟢/🔴 |
| `phantom-stealth-math.ts` | Timing randomization | 🟢/🔴 |
| `anti-detection-order-randomizer-safety-layer.ts` | Size splitting | 🟢/🔴 |
| `phantom-order-cloaking-engine.ts` | Anti-detection cloaking | 🟢/🔴 |
| `atomic-cross-exchange-order-executor.ts` | Cross-exchange arb | 🟢/🔴 |

### 2. FILL RATE DASHBOARD
| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Fill rate | XX% | >95% | 🟢/🔴 |
| Avg slippage | X bps | <5 bps | 🟢/🔴 |
| Execution latency | Xms | <500ms | 🟢/🔴 |
| Partial fills | XX% | <10% | 🟢/🔴 |
| Rejected orders | XX% | <2% | 🟢/🔴 |

### 3. EXCHANGE HEALTH
| Exchange | Connection | Latency | Orders | Status |
|----------|-----------|---------|--------|--------|
| Binance | `exchange-connection-pool.ts` | Xms | OK | 🟢/🔴 |
| OKX | `exchange-health-monitor.ts` | Xms | OK | 🟢/🔴 |
| Bybit | `exchange-registry.ts` | Xms | OK | 🟢/🔴 |
Gateway: `portkey-inspired-exchange-gateway-middleware-pipeline.ts`

### 4. SPREAD & FEE ANALYSIS
Using `fee-aware-cross-exchange-spread-calculator.ts`:
| Pair | Spread | Fee Round-Trip | Net Edge | Tradeable? |
|------|--------|---------------|----------|------------|
| BTC/USDT | X bps | X bps | X bps | ✅/❌ |

## USAGE
```bash
/trading:exec-spec routing    # Order routing analysis
/trading:exec-spec fills      # Fill rate dashboard
/trading:exec-spec slippage   # Slippage deep dive
/trading:exec-spec health     # Exchange health check
```
