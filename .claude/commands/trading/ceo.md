---
description: ⚡⚡⚡⚡⚡⚡ CEO Strategic Command — full portfolio oversight, quarterly review, capital allocation, risk governance, exit strategy
argument-hint: [action: review|allocate|risk|roadmap|compliance|dashboard|exit|checklist] [period: daily|weekly|monthly|quarterly]
---

**Ultrathink parallel** CEO strategic operations: <args>$ARGUMENTS</args>

**CWD:** `apps/algo-trader`
**ROLE:** CEO — highest authority. System oversight, NOT execution.
**REF:** `docs/ceo-sops.md` | `docs/founder-sops.md` | `docs/trader-sops.md`

---

## CEO COMMAND ARCHITECTURE

```
/trading:ceo                    ← THIS: Full strategic review (quarterly)
/trading:ceo:dashboard          ← Real-time CEO metrics (8 KPIs)
/trading:ceo:allocate           ← Capital allocation optimizer
/trading:ceo:risk               ← Risk appetite framework management
```

**Mapping to /bootstrap:auto:parallel:**
```
bootstrap:auto:parallel         →  trading:ceo
────────────────────────────────────────────────
1. Git Init                     →  1. System Health Gate
2. Research                     →  2. Market Intelligence (parallel)
3. Tech Stack                   →  3. Portfolio Analysis
4. Wireframe & Design           →  4. Capital Allocation Review
5. Parallel Planning & Impl     →  5. Strategic Decision Engine (parallel)
6. Testing                      →  6. Risk Governance Audit
7. Code Review                  →  7. Compliance Check
8. Documentation                →  8. Report Generation
9. Onboarding                   →  9. Action Items & Delegation
10. Final Report                →  10. CEO Quarterly Report
```

---

## PIPELINE — 10 Steps (Parallel Where Possible)

### 1. SYSTEM HEALTH GATE

**Module:** `src/netdata/HealthManager.ts` → `getReport()`

```bash
tsc --noEmit                    # 0 errors
pnpm test 2>&1 | tail -5       # all PASS
```

Check:
- Exchange connectivity (all configured exchanges)
- API keys validity (`src/utils/CredentialVault.ts`)
- Circuit breakers status (active, cannot disable)
- Tôm Hùm daemon status (if applicable)

**GATE:** All systems GREEN → proceed. Any RED → flag for CEO attention.

### 2. MARKET INTELLIGENCE (Parallel — 3 Agents)

Launch 3 `researcher` agents in parallel:

**Agent A — Macro Analysis:**
- Crypto market cycle (bull/bear/accumulation)
- BTC dominance, total market cap trend
- Fed rates, regulation news, ETF flows
- Report: ≤100 lines

**Agent B — Exchange Intelligence:**
- Exchange health per configured exchange
- Fee changes, new restrictions, ToS updates
- Liquidity depth across pairs
- Stealth risk assessment (detection algorithm changes)
- Report: ≤100 lines

**Agent C — Strategy Performance:**
- Read all `plans/reports/trading-*.md` from period
- Aggregate: total P&L, Sharpe, Win Rate, Max DD
- Strategy weight evolution
- Alpha decay detection (declining Sharpe over time)
- Report: ≤100 lines

### 3. PORTFOLIO ANALYSIS

**Sources:**
- `src/core/RiskManager.ts` → portfolio exposure data
- `src/reporting/PerformanceAnalyzer.ts` → historical metrics
- Trading reports in `plans/reports/`

**Analysis:**
```
Portfolio Scorecard:
├── Total Capital: $XX
├── Deployed: $XX (XX%)
├── P&L Period: +/-$XX (XX%)
├── Sharpe: X.XX
├── Max DD: XX%
├── Win Rate: XX%
├── Avg Trades/Day: XX
├── Cost/Revenue: XX%
└── Cash Reserve: XX%
```

**Benchmark:** Compare vs BTC buy-and-hold same period.

### 4. CAPITAL ALLOCATION REVIEW

**Framework (from SOP-C03):**

| Asset Class | Target | Current | Action |
|------------|--------|---------|--------|
| Algo Trading | 30-50% | XX% | Rebalance? |
| HODLing | 30-40% | XX% | Rebalance? |
| Stablecoin Yield | 10-20% | XX% | Rebalance? |
| Cash Reserve | 10-20% | XX% | Rebalance? |

**Within Algo Trading (from SOP-F03):**

| Tier | Target | Current | Action |
|------|--------|---------|--------|
| Cash Reserve | 40% | XX% | — |
| Paper Trading | 20% | XX% | — |
| Live Conservative | 25% | XX% | — |
| Live Aggressive | 10% | XX% | — |
| Stealth Arb | 5% | XX% | — |

**Decision:** Rebalance needed? → Generate rebalance plan.

### 5. STRATEGIC DECISION ENGINE (Parallel — 2 Agents)

**Agent D — Strategy Lifecycle Manager:**
- For each active strategy, determine phase (SOP-F07):
  - RESEARCH → BACKTEST → PAPER → LIVE SMALL → LIVE SCALE
- Check kill criteria:
  - Sharpe <0.5 for 1 week?
  - Win Rate <40% (20+ trades)?
  - Max DD >15%?
  - 5 consecutive losses?
- Recommend: promote / hold / demote / kill

**Agent E — Scaling Advisor:**
- Check scaling milestones (SOP-F09):
  - Paper profitable 1 week → start live $50?
  - Live profitable 2 weeks → increase $100?
  - Live profitable 1 month → increase $200?
- Check scale-down signals:
  - Weekly loss >5%?
  - Sharpe <0.5?
  - Circuit breaker 3x/week?
- Recommend: scale up / hold / scale down

### 6. RISK GOVERNANCE AUDIT

**Framework (SOP-C04):**

Determine current risk level:
```
Conservative → Moderate → Aggressive
```

**Audit checklist:**
- [ ] Daily loss limits appropriate?
- [ ] Weekly loss limits appropriate?
- [ ] Monthly loss limits appropriate?
- [ ] Max drawdown threshold correct?
- [ ] Per-trade risk % correct?
- [ ] Exchange concentration <40% per exchange?
- [ ] Pair concentration <25% per pair?
- [ ] Strategy concentration <30% per strategy?

**Circuit Breaker Review:**
- How many activations this period?
- Which breakers triggered most?
- Any false positives?
- Thresholds need adjustment?

### 7. COMPLIANCE CHECK

**4 pillars (SOP-C07):**

```
Exchange Compliance:
- [ ] KYC verified all exchanges?
- [ ] ToS changes reviewed?
- [ ] Stealth mode risk acknowledged?

Tax Obligations:
- [ ] P&L recorded this period?
- [ ] Transaction exports up to date?

Regulatory:
- [ ] New crypto regulation in VN?
- [ ] International regulation changes?

Operational Security:
- [ ] API keys rotated recently?
- [ ] 2FA active all exchanges?
- [ ] Withdrawal whitelist on?
```

### 8. REPORT GENERATION

Generate comprehensive CEO report:

**Save:** `plans/reports/ceo-{period}-260303-0841-strategic-review.md`

```markdown
## CEO Strategic Review — {period} {date}

### Executive Summary
[3-5 bullet points: P&L, key decisions, risks]

### Portfolio Scorecard
[Table from Step 3]

### Market Intelligence
[Key findings from Step 2]

### Capital Allocation
[Current vs target, rebalance recommendations]

### Strategy Status
[Each strategy: phase, performance, recommendation]

### Risk Assessment
[Current risk level, audit results, adjustments]

### Compliance Status
[Checklist results, action items]

### CEO Dashboard (8 KPIs)
| Metric | Value | Status |
|--------|-------|--------|
| Monthly ROI | XX% | 🟢/🟡/🔴 |
| Sharpe Ratio | X.XX | 🟢/🟡/🔴 |
| Max Drawdown | XX% | 🟢/🟡/🔴 |
| System Uptime | XX% | 🟢/🟡/🔴 |
| Cost/Revenue | XX% | 🟢/🟡/🔴 |
| Alpha Decay | XX% | 🟢/🟡/🔴 |
| Exchange Concentration | XX% | 🟢/🟡/🔴 |
| Cash Reserve | XX% | 🟢/🟡/🔴 |

### Decisions Required
1. [Decision with options]
2. [Decision with options]

### Action Items
- [ ] [Action → Owner → Deadline]
```

### 9. ACTION ITEMS & DELEGATION

Map decisions to commands:

| Decision | Delegate To | Command |
|----------|------------|---------|
| Rebalance portfolio | Founder | Manual capital move |
| Scale up strategy | Founder SOPs | SOP-F09 |
| Kill strategy | Founder SOPs | SOP-F07 kill criteria |
| Add exchange | Trader SOPs | `/trading:deploy` |
| Adjust risk limits | Founder SOPs | SOP-F05 |
| Update roadmap | CEO | Edit `docs/project-roadmap.md` |
| Compliance fix | CEO | SOP-C07 |

### 10. CEO QUARTERLY REPORT

**Only for quarterly reviews (SOP-C01):**

Additional sections:
- Q{N} Market Thesis
- Technology roadmap progress (SOP-C05)
- Team/scaling assessment (SOP-C06)
- Exit strategy review (SOP-C09)
- Next quarter priorities

**Save:** `plans/reports/ceo-quarterly-Q{N}-{year}.md`

---

## SAFETY — CEO Cannot Break

```
CEO CAN:                          CEO CANNOT:
─────────────────────────────────────────────
Set risk appetite levels          Disable circuit breakers
Allocate capital                  Override daily loss limit
Kill strategies                   Skip backtest verification
Add/remove exchanges              Trade directly (use bot)
Approve live mode                 Remove audit trail
Change roadmap                    Bypass safety hierarchy
```

**Safety hierarchy (immutable):**
```
Layer 1: Circuit Breakers     ← CANNOT disable (hardcoded)
Layer 2: Autonomy Escalation  ← Auto-downgrade on risk
Layer 3: Risk Manager         ← Per-trade enforcement
Layer 4: Exchange Router      ← Infrastructure failover
Layer 5: CEO Risk Appetite    ← Strategic limits (THIS LEVEL)
```

---

## DEFAULT CONFIG

```
Review period: quarterly (default), weekly/monthly available
Report: plans/reports/ceo-{period}-{date}-strategic-review.md
Parallel agents: 5 max (A,B,C for intel + D,E for strategy)
Dashboard metrics: 8 KPIs
Risk levels: conservative/moderate/aggressive
```

## USAGE

```bash
# Full quarterly strategic review (default)
/trading:ceo quarterly

# Weekly CEO check (lighter)
/trading:ceo weekly

# Monthly review
/trading:ceo monthly

# Quick daily glance
/trading:ceo daily

# Specific actions
/trading:ceo:dashboard              # 8 KPI metrics
/trading:ceo:allocate               # Capital allocation review
/trading:ceo:risk moderate          # Set risk appetite
```
