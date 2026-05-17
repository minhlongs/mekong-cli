---
description: ⚡⚡⚡ Data Engineer — data pipeline health, ETL monitoring, feed ingestion, storage management
argument-hint: [action: pipeline|feeds|storage|health]
---

**Ultrathink** Data engineering review: <args>$ARGUMENTS</args>

**CWD:** `apps/algo-trader` | **REF:** `docs/trading-team-subordinates-sops.md` PART 5
**Reports to:** CDO (`/trading:cdo`)

## Pipeline (4 steps)

### 1. DATA PIPELINE STATUS
```
Exchange WS/REST → websocket-multi-exchange-price-feed-manager.ts
    ↓
TickStore.ts (raw) → tick-to-candle-aggregator.ts (OHLCV)
    ↓
CollectorRegistry.ts → AgiDbEngine.ts (persistent)
    ↓
SignalMesh.ts (correlation) → HealthManager.ts (monitor)
```
| Stage | Status | Throughput | Errors |
|-------|--------|-----------|--------|
| Ingestion | 🟢/🔴 | X ticks/s | X |
| Aggregation | 🟢/🔴 | X candles/m | X |
| Storage | 🟢/🔴 | X writes/s | X |
| Correlation | 🟢/🔴 | X updates/m | X |

### 2. FEED INGESTION
| Pair | Exchange | WS Status | Tick Rate | Stale? |
|------|----------|-----------|-----------|--------|
| BTC/USDT | Binance | 🟢/🔴 | X/s | No/Yes |
| ETH/USDT | Binance | 🟢/🔴 | X/s | No/Yes |

### 3. STORAGE HEALTH
| Store | Size | Retention | Last Write |
|-------|------|-----------|------------|
| TickStore (memory) | XMB | 24h | Xs ago |
| AgiDbEngine | XMB | 30d | Xs ago |
| SignalMesh | XMB | 7d | Xs ago |

### 4. RECOMMENDATIONS
Fix pipeline bottlenecks, optimize storage, suggest archival.

## USAGE
```bash
/trading:data-eng pipeline   # Full pipeline status
/trading:data-eng feeds      # Feed ingestion check
/trading:data-eng storage    # Storage health
/trading:data-eng health     # Quick health check
```
