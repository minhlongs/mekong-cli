---
description: ⚡⚡ CEO Dashboard — 8 KPI metrics real-time, traffic light status
argument-hint: [period: today|week|month|quarter]
---

**Ultrathink** CEO dashboard: <args>$ARGUMENTS</args>

**CWD:** `apps/algo-trader` | **REF:** `docs/ceo-sops.md` SOP-C08

## Pipeline (4 steps)

### 1. Collect Data
- Read recent reports: `ls -t plans/reports/trading-*.md | head -10`
- Extract P&L, Sharpe, Win Rate, Max DD from each
- `src/netdata/HealthManager.ts` → system uptime
- `src/core/RiskManager.ts` → current exposure

### 2. Calculate KPIs
| # | Metric | Source | Green | Yellow | Red |
|---|--------|--------|-------|--------|-----|
| 1 | Monthly ROI % | P&L / Capital | >5% | 0-5% | <0% |
| 2 | Sharpe Ratio | Risk-adjusted return | >1.5 | 0.5-1.5 | <0.5 |
| 3 | Max Drawdown % | Worst peak-to-trough | <10% | 10-20% | >20% |
| 4 | System Uptime % | Health reports | >99% | 95-99% | <95% |
| 5 | Cost/Revenue | Fees+infra / Gross P&L | <20% | 20-50% | >50% |
| 6 | Alpha Decay | Sharpe trend (30d slope) | Stable/up | -10% | -20%+ |
| 7 | Exchange Concentration | Max % on 1 exchange | <40% | 40-60% | >60% |
| 8 | Cash Reserve % | Undeployed / Total | >20% | 10-20% | <10% |

### 3. Render Dashboard
```
╔══════════════════════════════════════════════╗
║           CEO DASHBOARD — {date}             ║
╠══════════════════════════════════════════════╣
║ 1. Monthly ROI      XX%        🟢/🟡/🔴    ║
║ 2. Sharpe Ratio     X.XX       🟢/🟡/🔴    ║
║ 3. Max Drawdown     XX%        🟢/🟡/🔴    ║
║ 4. System Uptime    XX%        🟢/🟡/🔴    ║
║ 5. Cost/Revenue     XX%        🟢/🟡/🔴    ║
║ 6. Alpha Decay      XX%        🟢/🟡/🔴    ║
║ 7. Exchange Conc.   XX%        🟢/🟡/🔴    ║
║ 8. Cash Reserve     XX%        🟢/🟡/🔴    ║
╠══════════════════════════════════════════════╣
║ Overall: X/8 GREEN | Alerts: [list]          ║
╚══════════════════════════════════════════════╝
```

### 4. Alerts
- Any RED metric → flag with recommended action
- Refer to specific SOP for resolution

## Defaults
```
Period: week | Source: plans/reports/ | Format: table + alerts
```
