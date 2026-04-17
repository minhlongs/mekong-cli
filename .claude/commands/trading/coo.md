---
description: ⚡⚡⚡⚡⚡⚡ COO Operations Command — system health, incident response, performance optimization, capacity planning
argument-hint: [action: daily|weekly|monthly] [focus: health|perf|incident|change]
---

**Ultrathink parallel** COO operations: <args>$ARGUMENTS</args>

**CWD:** `apps/algo-trader`
**ROLE:** COO — operations officer. System uptime, incidents, optimization.
**REF:** `docs/coo-sops.md` | `docs/ceo-sops.md` | `docs/founder-sops.md`

---

## COO COMMAND ARCHITECTURE

```
/trading:coo                    ← THIS: Full operations review
/trading:coo:health             ← 5-pillar system health check
/trading:coo:perf               ← Performance analysis + optimization
/trading:coo:incident           ← Incident response workflow
```

---

## PIPELINE — 8 Steps (Parallel Where Possible)

### 1. SYSTEM HEALTH GATE (5 pillars)

**Parallel checks:**

```bash
tsc --noEmit                              # TypeScript health
pnpm test 2>&1 | tail -5                  # Test suite health
```

| Pillar | Module | Check |
|--------|--------|-------|
| Exchange | `src/netdata/HealthManager.ts` | Connectivity, latency, rate usage |
| Bot Engine | `src/core/BotEngine.ts` | Process health, memory, CPU |
| Strategy | `src/core/SignalGenerator.ts` | Signal generation active |
| Infrastructure | Tôm Hùm daemon, proxy 9191 | Daemon + proxy alive |
| Data | `src/netdata/TickStore.ts` | Price feeds current, no gaps |

**Output:** Health scorecard (5 pillars × GREEN/YELLOW/RED)

### 2. INCIDENT REVIEW (Parallel — 2 Agents)

**Agent A — Overnight Incidents:**
- Scan recent reports for circuit breaker activations
- Check autonomy level changes (escalations)
- Check exchange failover events
- Report: ≤80 lines

**Agent B — Alert Analysis:**
- Telegram alerts (if configured)
- Rate limit warnings from `PhantomCloakingEngine`
- OTR ratio spikes
- Report: ≤80 lines

### 3. PERFORMANCE SNAPSHOT

**Sources:**
- `src/reporting/PerformanceAnalyzer.ts` → metrics
- Trading reports in `plans/reports/`

**Metrics:**
```
Execution Performance:
├── Order placement latency: XXms avg
├── Fill rate: XX%
├── Slippage: XX bps avg
├── Signal accuracy: XX%
└── Strategy alpha: +/-XX%

Operational Metrics:
├── System uptime: XX%
├── Exchange API utilization: XX%
├── Circuit breaker activations: N
├── Autonomy escalations: N
└── Incident count: N (P0/P1/P2/P3)
```

### 4. STRATEGY HEALTH CHECK

For each active strategy:
- Current weight vs target
- Recent win rate (last 20 trades)
- Sharpe trend (improving/stable/declining)
- Regime alignment (strategy fits current market?)

**Source:** `src/core/SignalGenerator.ts`, `src/core/autonomy-controller.ts`

### 5. INFRASTRUCTURE STATUS

| Component | Check | Source |
|-----------|-------|--------|
| TypeScript | `tsc --noEmit` | Build system |
| Tests | `pnpm test` | Test suite |
| Disk | `df -h` | Storage |
| Memory | Process RSS | Node.js runtime |
| Proxy | `curl localhost:9191/health` | Antigravity |
| Tôm Hùm | Process check | Daemon |

### 6. CAPACITY ANALYSIS

- API rate utilization per exchange
- Order volume trend
- Data storage growth rate
- Connection pool usage
- Scaling recommendations

### 7. OPERATIONS DECISION

Based on all data, determine:

| Status | Criteria | Action |
|--------|----------|--------|
| **GREEN** | All 5 pillars healthy, no P0/P1 | Continue normal operations |
| **YELLOW** | 1-2 pillars degraded, P2 incidents | Monitor closely, reduce exposure |
| **RED** | 3+ pillars down, P0/P1 active | Halt trading, escalate CEO |

### 8. REPORT

Save: `plans/reports/coo-ops-{period}-{date}.md`

```markdown
## COO Operations Report — {period} {date}

### System Health: 🟢/🟡/🔴
| Pillar | Status | Details |
|--------|--------|---------|

### Incidents (Period)
| # | Severity | Description | Resolved? |

### Performance KPIs
| Metric | Value | Trend | Status |

### Strategy Health
| Strategy | Weight | WR | Sharpe | Status |

### Infrastructure
| Component | Status | Notes |

### Operations Decision: GREEN/YELLOW/RED
Recommendation: [continue/monitor/halt]

### Action Items
- [ ] ...
```

---

## SAFETY

```
COO CAN:                          COO CANNOT:
────────────────────────────────────────────────
Monitor all systems               Change capital allocation (CEO)
Respond to incidents              Set risk appetite levels (CEO)
Optimize performance              Approve live mode (Founder)
Adjust config parameters          Disable circuit breakers (nobody)
Escalate to CEO/Founder           Override safety hierarchy
Change management                 Trade directly
```

---

## USAGE

```bash
# Daily ops check (default)
/trading:coo daily

# Weekly operations review
/trading:coo weekly

# Monthly infrastructure audit
/trading:coo monthly

# Specific sub-commands
/trading:coo:health               # 5-pillar health check
/trading:coo:perf                 # Performance analysis
/trading:coo:incident P1 "desc"   # Incident response
```
