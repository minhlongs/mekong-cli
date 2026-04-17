---
description: ⚡⚡⚡ COO Performance Analysis — execution metrics, strategy alpha, optimization recommendations
argument-hint: [period: yesterday|week|month] [focus: execution|strategy|capacity]
---

**Ultrathink** COO performance analysis: <args>$ARGUMENTS</args>

**CWD:** `apps/algo-trader` | **REF:** `docs/coo-sops.md` SOP-O04

## Pipeline (4 steps — Measure → Analyze → Optimize → Verify)

### 1. MEASURE
Collect from `plans/reports/trading-*.md`:

```
Execution Metrics:
├── Order latency: XXms avg (target <500ms)
├── Fill rate: XX% (target >95%)
├── Slippage: XX bps (target <5bps)
├── Signal accuracy: XX% (target >60%)
└── Strategy alpha: +/-XX% vs BTC hold

Operational Metrics:
├── System uptime: XX%
├── Exchange API utilization: XX% per exchange
├── Circuit breaker activations: N
├── Autonomy escalations: N
└── Phantom session breaks: N (stealth only)
```

### 2. ANALYZE
- Which strategy best risk-adjusted returns?
- Which exchange best execution?
- Which pairs best spreads?
- What time of day performs best?
- Circuit breakers triggering too often/rarely?
- Alpha decay trend (30d Sharpe slope)

### 3. OPTIMIZE
Recommendations:
- Strategy weights adjustment (±0.05)
- Execution timing (shift to peak hours)
- Exchange routing (best execution priority)
- Pair selection (highest alpha pairs)
- Circuit breaker threshold tuning

### 4. VERIFY
- Backtest optimized config before applying
- Compare before/after metrics
- Rollback plan if worse

## Output
```
Performance Report — {period}
| Metric          | Value  | Target | Status | Trend |
|-----------------|--------|--------|--------|-------|
| Order Latency   | XXms   | <500ms | 🟢/🔴 | ↑↓→  |
| Fill Rate       | XX%    | >95%   | 🟢/🔴 | ↑↓→  |
| Slippage        | XX bps | <5bps  | 🟢/🔴 | ↑↓→  |
| Signal Accuracy | XX%    | >60%   | 🟢/🔴 | ↑↓→  |
| Alpha           | XX%    | >0%    | 🟢/🔴 | ↑↓→  |
| Uptime          | XX%    | >99%   | 🟢/🔴 | ↑↓→  |

Optimization: [N recommendations]
```
