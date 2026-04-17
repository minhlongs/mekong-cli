---
description: ⚡⚡⚡ SRE Engineer — uptime monitoring, auto-recovery, alerting, circuit breaker status, health endpoints
argument-hint: [action: uptime|alerts|recovery|monitor]
---

**Ultrathink** SRE review: <args>$ARGUMENTS</args>

**CWD:** `apps/algo-trader` | **REF:** `docs/trading-team-subordinates-sops.md` PART 6
**Reports to:** COO (`/trading:coo`)

## Pipeline (4 steps)

### 1. UPTIME DASHBOARD
| Component | SLA Target | Current | Status |
|-----------|-----------|---------|--------|
| Bot engine | 99.9% | XX.X% | 🟢/🔴 |
| Price feeds | 99.5% | XX.X% | 🟢/🔴 |
| Order execution | 99.0% | XX.X% | 🟢/🔴 |
| Alerting | 99.9% | XX.X% | 🟢/🔴 |
Health endpoint: `src/core/http-health-check-server.ts`

### 2. CIRCUIT BREAKER STATUS
Using `src/execution/adaptive-circuit-breaker-per-exchange.ts`:
| Exchange | CB State | Triggers/24h | Last Reset |
|----------|---------|-------------|------------|
| Binance | CLOSED/OPEN/HALF | X | {time} |
| OKX | CLOSED/OPEN/HALF | X | {time} |
| Bybit | CLOSED/OPEN/HALF | X | {time} |

### 3. ALERT RULES
Using `src/core/alert-rules-engine.ts`:
| Rule | Condition | Status | Last Fired |
|------|-----------|--------|------------|
| High error rate | >5 errors/min | Active | {time} |
| Feed stale | >30s no ticks | Active | {time} |
| CB triggered | Any CB OPEN | Active | {time} |
| Memory high | >80% RAM | Active | {time} |
| Latency spike | >2s E2E | Active | {time} |

### 4. AUTO-RECOVERY STATUS
| Failure Type | Recovery | Last Tested |
|-------------|----------|-------------|
| Bot crash | Auto-restart | {date} |
| WS disconnect | Reconnect (exp backoff) | {date} |
| Exchange down | Failover routing | {date} |
| High memory | Graceful restart | {date} |

## USAGE
```bash
/trading:sre uptime     # Uptime SLA dashboard
/trading:sre alerts     # Alert rules status
/trading:sre recovery   # Auto-recovery check
/trading:sre monitor    # Full monitoring review
```
