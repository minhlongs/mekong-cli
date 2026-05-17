---
description: ⚡⚡⚡⚡ CDO Data Command — data quality audit, price feed integrity, analytics pipeline, backtesting data, historical management
argument-hint: [action: audit|feeds|pipeline|backtest]
---

**Ultrathink** CDO data review: <args>$ARGUMENTS</args>

**CWD:** `apps/algo-trader` | **REF:** `docs/cdo-sops.md`

## Pipeline (5 steps)

### 1. PRICE FEED HEALTH
| Check | Module | Status |
|-------|--------|--------|
| Tick freshness (<5s) | `TickStore.ts` | 🟢/🔴 |
| WS connection | `HealthManager.ts` | 🟢/🔴 |
| Cross-exchange delta (<0.5%) | Compare feeds | 🟢/🔴 |
| Candle gaps (0 missing) | `tick-to-candle-aggregator.ts` | 🟢/🔴 |
| Order book depth (>$10K) | `order-book-depth-analyzer.ts` | 🟢/🔴 |

### 2. DATA QUALITY AUDIT
| Dimension | Check | Score |
|-----------|-------|-------|
| Completeness | No missing candles | X/10 |
| Accuracy | Cross-validate 3+ exchanges | X/10 |
| Timeliness | Tick age <5s | X/10 |
| Consistency | OHLCV math valid | X/10 |
| Uniqueness | No duplicate ticks | X/10 |
| **Total** | | **X/50** |

### 3. ANALYTICS PIPELINE
```
Exchange WS → TickStore → Aggregator → Indicators → SignalGenerator
                 ↓
          HealthManager ← CollectorRegistry ← AgiDbEngine
                 ↓
          SignalMesh (cross-strategy)
```
| KPI | Current | Target |
|-----|---------|--------|
| E2E latency | Xs | <2s |
| Tick throughput | X/s | >10/s |
| Candle gaps/day | X | 0 |
| Signal freshness | Xs | <10s |

### 4. BACKTEST DATA
| Pair | History | Completeness | Last Updated |
|------|---------|-------------|-------------|
| BTC/USDT | Xmo | XX% | YYYY-MM-DD |
| ETH/USDT | Xmo | XX% | YYYY-MM-DD |
| (others) | Xmo | XX% | YYYY-MM-DD |
Min: 6mo, >99.5% complete

### 5. REPORT
Save: `plans/reports/cdo-data-quality-{date}.md`

## USAGE
```bash
/trading:cdo audit      # Full data quality audit
/trading:cdo feeds      # Price feed health check
/trading:cdo pipeline   # Analytics pipeline status
/trading:cdo backtest   # Backtesting data review
```
