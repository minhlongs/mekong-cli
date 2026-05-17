---
description: ⚡⚡⚡⚡⚡⚡ Founder Command — budget management, risk oversight, strategy lifecycle, scaling decisions, emergency protocols
argument-hint: [action: daily|weekly|morning|emergency] [focus: budget|risk|strategy|scale]
---

**Ultrathink parallel** Founder operations: <args>$ARGUMENTS</args>

**CWD:** `apps/algo-trader`
**ROLE:** Founder — budget owner. Between CEO (strategy) and Trader (execution).
**REF:** `docs/founder-sops.md` | `docs/ceo-sops.md` | `docs/trader-sops.md`

---

## FOUNDER COMMAND ARCHITECTURE

```
/trading:founder                ← THIS: Full Founder review (weekly)
/trading:founder:budget         ← Budget allocation, tier management
/trading:founder:strategy       ← Strategy lifecycle, kill/promote/demote
/trading:founder:scale          ← Scaling decisions, milestone tracking
/trading:founder:emergency      ← Emergency protocols (Red/Orange/Yellow)
```

**Mapping to /bootstrap:auto:parallel:**
```
bootstrap:auto:parallel         →  trading:founder
────────────────────────────────────────────────────
1. Git Init                     →  1. System Preflight
2. Research                     →  2. Market Scan (parallel fast)
3. Tech Stack                   →  3. Portfolio Snapshot
4. Wireframe & Design           →  4. Budget Tier Review
5. Parallel Planning & Impl     →  5. Strategy Lifecycle (parallel)
6. Testing                      →  6. Risk Limits Audit
7. Code Review                  →  7. Scaling Assessment
8. Documentation                →  8. Weekly Report Generation
9. Onboarding                   →  9. Action Items & Delegation
10. Final Report                →  10. Founder Weekly Report
```

---

## PIPELINE — 10 Steps

### 1. SYSTEM PREFLIGHT

Quick system check before reviewing:
```bash
tsc --noEmit 2>&1 | tail -3     # Build healthy?
ls -t plans/reports/trading-*.md | head -5  # Recent reports exist?
```

Verify:
- Bot engine responsive
- Exchange connections active
- Circuit breakers status (always on)

### 2. MARKET SCAN (Parallel — 2 Agents)

Launch 2 `researcher` agents:

**Agent A — Quick Market Scan:**
- `/trading:auto:fast BTC/USDT` equivalent analysis
- BTC trend: bull/bear/sideways
- Key support/resistance levels
- Report: ≤50 lines

**Agent B — Multi-Pair Scan:**
- Top 5 pairs by volume: quick signal check
- Cross-exchange spread check (arb opportunity?)
- Funding rate differentials
- Report: ≤50 lines

### 3. PORTFOLIO SNAPSHOT

From recent trading reports:
```
Portfolio Snapshot — {date}:
├── Total Capital: $XX
├── Deployed: $XX (XX%)
├── P&L Today: +/-$XX
├── P&L This Week: +/-$XX
├── Open Positions: N
├── Win Rate (7d): XX%
├── Sharpe (7d): X.XX
├── Max DD (7d): XX%
└── Cash Reserve: XX%
```

**Source:** `plans/reports/trading-*.md`, `src/core/RiskManager.ts`

### 4. BUDGET TIER REVIEW

**Framework (SOP-F03):**

| Tier | Target | Current | Delta | Action |
|------|--------|---------|-------|--------|
| Cash Reserve | 40% | XX% | +/-X% | — |
| Paper Trading | 20% | XX% | +/-X% | — |
| Live Conservative | 25% | XX% | +/-X% | — |
| Live Aggressive | 10% | XX% | +/-X% | — |
| Stealth Arb | 5% | XX% | +/-X% | — |

**Scale Rules Check:**
- Paper profitable 3 days? → Move 5% Tier 2→3
- Live profitable 1 week? → Move 5% Tier 1→3
- Live profitable 1 month? → Move 5% Tier 3→4
- Loss >10% Tier 3 this week? → Move ALL Tier 3→2
- Loss >20% portfolio? → HALT ALL

### 5. STRATEGY LIFECYCLE (Parallel — 2 Agents)

**Agent C — Active Strategy Review:**
For each strategy, determine lifecycle phase (SOP-F07):
```
RESEARCH → BACKTEST → PAPER → LIVE SMALL → LIVE SCALE
```

| Strategy | Phase | WR | Sharpe | DD | Status |
|----------|-------|-----|--------|-----|--------|
| MacdBollingerRsi | {phase} | XX% | X.XX | XX% | 🟢/🟡/🔴 |
| RsiSma | {phase} | XX% | X.XX | XX% | 🟢/🟡/🔴 |
| Bollinger | {phase} | XX% | X.XX | XX% | 🟢/🟡/🔴 |
| MacdCrossover | {phase} | XX% | X.XX | XX% | 🟢/🟡/🔴 |

**Agent D — Kill Criteria Check:**
For each strategy, evaluate (SOP-F07 kill criteria):
- [ ] Sharpe <0.5 for 1 week?
- [ ] Win Rate <40% (20+ trades)?
- [ ] Max DD >15%?
- [ ] 5 consecutive losses?

Recommend: **PROMOTE / HOLD / DEMOTE / KILL**

### 6. RISK LIMITS AUDIT

**3-tier check (SOP-F05):**

```
Tier 1 — PER-TRADE (Bot manages):
  Position size: 2% ← correct?
  SL: 2% ← correct?
  TP: 5% ← correct?
  R:R ≥1:1.5 ← met?

Tier 2 — DAILY (Circuit breaker):
  Daily loss limit: $100 ← hit today?
  3 consecutive losses: ← triggered?
  Exchange down: ← failover worked?

Tier 3 — STRATEGIC (Founder decides):
  Weekly loss limit: 5% ← within limit?
  Monthly loss limit: 10% ← within limit?
  Max per strategy: 30% ← within limit?
  Max per exchange: 40% ← within limit?
  Max per pair: 25% ← within limit?
```

### 7. SCALING ASSESSMENT

**Milestones (SOP-F09):**

| Milestone | Condition | Met? | Action |
|-----------|-----------|------|--------|
| Start live | Paper profitable 1 week | ✅/❌ | Live $50/day |
| Increase $100 | Live profitable 2 weeks | ✅/❌ | Budget +$50 |
| Increase $200 | Live profitable 1 month | ✅/❌ | Budget +$100 |
| Add AGI mode | Sharpe >1.5 sustained | ✅/❌ | Enable AGI |
| Add stealth arb | Spread >0.1% detected | ✅/❌ | Enable stealth |
| Cut 50% | Weekly loss >5% | ✅/❌ | Reduce budget |
| Back to paper | Sharpe <0.5 | ✅/❌ | Demote to paper |

### 8. WEEKLY REPORT GENERATION

Save: `plans/reports/founder-weekly-{date}.md`

```markdown
## Founder Weekly Review — {date}

### Morning Decision: HOLD / OBSERVE / TRADE

### Portfolio Status
| Tier | Allocation | P&L This Week | Status |
|------|-----------|---------------|--------|

### Key Metrics
| Metric | This Week | Last Week | Trend |
|--------|-----------|-----------|-------|
| Total P&L | | | |
| Win Rate | | | |
| Sharpe | | | |
| Max DD | | | |
| Trades | | | |

### Strategy Status
| Strategy | Phase | Recommendation |
|----------|-------|---------------|

### Risk Audit
[Tier 1/2/3 results]

### Scaling Decision
[Scale up / hold / scale down + reasoning]

### Budget Changes
[Any tier rebalancing needed]

### Action Items
- [ ] ...
```

### 9. ACTION ITEMS & DELEGATION

| Decision | Delegate | Command |
|----------|----------|---------|
| Run backtest | Trader SOPs | `/trading:auto BTC/USDT backtest` |
| Start paper | Trader SOPs | `/trading:auto:agi BTC/USDT paper $100 2h` |
| Start live | Trader SOPs | `/trading:auto:agi BTC/USDT live $50 4h` |
| Start arb | Trader SOPs | `/trading:auto:stealth BTC/USDT binance,okx $100 4h` |
| Change risk | Self | Update RiskManager config |
| Emergency halt | Self | SOP-F08 |
| Escalate to CEO | CEO SOPs | `/trading:ceo` |

### 10. MORNING DECISION OUTPUT

Final output — 1 of 3:
- **HOLD** — Không chạy bot
- **OBSERVE** — Bot observe mode chỉ thu thập data
- **TRADE** — Bot paper/live theo budget + strategy phù hợp

---

## SAFETY

```
Founder CAN:                      Founder CANNOT:
─────────────────────────────────────────────────
Set daily/weekly budget            Set capital allocation (CEO)
Approve paper → live transition    Set risk appetite level (CEO)
Kill/promote strategies            Disable circuit breakers (nobody)
Trigger emergency protocols        Change business model (CEO)
Scale up/down budget               Override safety hierarchy
Delegate to Trader commands        Trade directly
```

---

## USAGE

```bash
# Morning review (daily, 5 min)
/trading:founder morning

# Full weekly review
/trading:founder weekly

# Quick daily check
/trading:founder daily

# Emergency
/trading:founder emergency red

# Specific sub-commands
/trading:founder:budget             # Budget tier management
/trading:founder:strategy           # Strategy lifecycle
/trading:founder:scale              # Scaling decisions
/trading:founder:emergency red      # Emergency protocol
```
