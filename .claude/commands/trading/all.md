---
description: ⚡⚡⚡⚡⚡⚡⚡ MASTER COMMAND — Orchestrate ALL 14 roles (C-Suite + Founder + Trader) in parallel, full system review
argument-hint: [scope: full|quick|emergency] [period: daily|weekly|monthly|quarterly]
---

**Ultrathink parallel** MASTER orchestration — ALL roles: <args>$ARGUMENTS</args>

**CWD:** `apps/algo-trader`
**ROLE:** Supreme Commander — orchestrate entire C-Suite + Operations simultaneously.
**REF:** All SOPs in `docs/` | All commands in `trading:*`

---

## MASTER ARCHITECTURE

```
/trading:all                          ← THIS: Supreme orchestrator
    ├── C-Suite (11):
    │   ├── /trading:ceo      (parallel)  ← Strategy + capital + exits
    │   ├── /trading:coo      (parallel)  ← Operations + health + incidents
    │   ├── /trading:cmo      (parallel)  ← Brand + growth + content
    │   ├── /trading:cfo      (parallel)  ← P&L + fees + tax + financial model
    │   ├── /trading:cdo      (parallel)  ← Data quality + feeds + analytics
    │   ├── /trading:cpo      (parallel)  ← Roadmap + features + releases
    │   ├── /trading:cto      (parallel)  ← Architecture + tech debt
    │   ├── /trading:cxo      (parallel)  ← UX + onboarding + A2UI
    │   ├── /trading:chro     (parallel)  ← Team + hiring + culture
    │   ├── /trading:caio     (parallel)  ← AI + signals + learning
    │   ├── /trading:cso      (parallel)  ← Security + stealth
    │   └── /trading:cco      (parallel)  ← Revenue + sales + B2B
    ├── Tactical (2):
    │   ├── /trading:founder  (parallel)  ← Budget + risk + strategy + scaling
    │   └── /trading:auto:*  (sequential) ← Execute decisions from above
    └── Intelligence (5):
        /trading:auto:agi | :stealth | :parallel | :fast
```

**Mapping to /bootstrap:auto:parallel:**
```
bootstrap:auto:parallel         →  trading:all
────────────────────────────────────────────────────
1. Git Init                     →  1. System Health Gate
2. Research (parallel)          →  2. Intelligence Gathering (5 parallel agents)
3. Tech Stack                   →  3. Portfolio + Infrastructure Snapshot
4. Wireframe & Design           →  4. Cross-Role Analysis
5. Parallel Planning & Impl     →  5. Decision Engine (parallel)
6. Testing                      →  6. Risk + Compliance Audit
7. Code Review                  →  7. Action Plan Consolidation
8. Documentation                →  8. Master Report Generation
9. Onboarding                   →  9. Delegation & Execution
10. Final Report                →  10. Supreme Commander Summary
```

---

## SCOPE MODES

### FULL (Quarterly — 4h)
All 10 steps, all 5 roles, comprehensive review.
```bash
/trading:all full quarterly
```

### QUICK (Weekly — 30min)
Steps 1-3-5-8 only, focused metrics.
```bash
/trading:all quick weekly
```

### EMERGENCY (Immediate)
Steps 1-6-7-9 only, crisis response.
```bash
/trading:all emergency "drawdown 18%"
```

---

## PIPELINE — 10 Steps

### 1. SYSTEM HEALTH GATE

Pre-flight for all roles:
```bash
tsc --noEmit 2>&1 | tail -3           # Build health
pnpm test 2>&1 | tail -5              # Test health
curl -s http://localhost:9191/health   # Proxy health
```

| Check | Status | Gate |
|-------|--------|------|
| TypeScript | 0 errors | PASS/FAIL |
| Tests | all PASS | PASS/FAIL |
| Exchange connectivity | all UP | PASS/FAIL |
| Circuit breakers | active | PASS/FAIL |
| Proxy (9191) | responding | PASS/FAIL |

**GATE:** All PASS → proceed. Any FAIL → flag + continue with warnings.

### 2. INTELLIGENCE GATHERING (5 Parallel Agents)

Launch 5 `researcher` agents simultaneously:

**Agent CEO-Intel:** Market thesis, macro analysis, competitor moves
**Agent COO-Intel:** System health deep scan, incident history, infrastructure
**Agent CMO-Intel:** Community metrics, content performance, SEO rankings
**Agent Founder-Intel:** Strategy performance, P&L per tier, risk events
**Agent Trader-Intel:** Signal quality, execution metrics, exchange health

Each agent: ≤80 lines report.

### 3. PORTFOLIO + INFRASTRUCTURE SNAPSHOT

Consolidated view from all roles:

```
╔════════════════════════════════════════════════════════╗
║              MASTER DASHBOARD — {date}                  ║
╠════════════════════════════════════════════════════════╣
║                                                        ║
║  CEO METRICS                 COO METRICS               ║
║  Monthly ROI:    XX% 🟢     System Uptime: XX% 🟢     ║
║  Sharpe:         X.XX 🟢    Incidents:     N   🟢     ║
║  Max DD:         XX%  🟢    Latency:       Xms 🟢     ║
║  Cash Reserve:   XX%  🟢    CB Triggers:   N   🟢     ║
║                                                        ║
║  CMO METRICS                 FOUNDER METRICS           ║
║  GitHub Stars:   N    🟢    Budget Used:   XX% 🟢     ║
║  Discord:        N    🟢    Win Rate:      XX% 🟢     ║
║  WAT:            N    🟢    Live P&L:     +$XX 🟢     ║
║  MRR:           $N    🟢    Scale Status:  UP  🟢     ║
║                                                        ║
║  TRADER METRICS                                        ║
║  Signals/Day:    N           Fill Rate:     XX%        ║
║  Avg Latency:    Xms         Slippage:      Xbps       ║
║  Active Pairs:   N           Active Exch:   N          ║
║                                                        ║
╠════════════════════════════════════════════════════════╣
║  Overall Score: XX/40 GREEN | Alerts: [list]           ║
╚════════════════════════════════════════════════════════╝
```

### 4. CROSS-ROLE ANALYSIS

Identify conflicts and synergies between roles:

| Cross-Check | Finding | Action |
|-------------|---------|--------|
| CEO capital vs Founder budget | Aligned? | Rebalance if drift >10% |
| COO health vs Trader execution | Latency affecting fills? | Optimize routing |
| CMO growth vs CEO revenue | Conversion tracking? | Funnel audit |
| Founder risk vs COO incidents | CB threshold appropriate? | Adjust if needed |
| CEO roadmap vs COO capacity | Infrastructure supports growth? | Plan scaling |

### 5. DECISION ENGINE (3 Parallel Agents)

**Agent Strategy:** Synthesize CEO + Founder data → capital/strategy decisions
**Agent Operations:** Synthesize COO + Trader data → operations/execution decisions
**Agent Growth:** Synthesize CMO data → marketing/growth decisions

Each produces prioritized decision list.

### 6. RISK + COMPLIANCE AUDIT

Unified risk view across all roles:

```
Risk Layer          Owner       Status    Last Check
──────────────────────────────────────────────────────
Per-Trade Limits    Trader Bot  🟢 Active  Real-time
Circuit Breakers    COO         🟢 Active  Real-time
Daily Loss Limit    Founder     🟢 $100    Today
Weekly Risk         Founder     🟢 5%      This week
Portfolio Risk      CEO         🟢 10% DD  This month
Exchange Compliance CEO         🟢 KYC     This quarter
Tax Records         CEO         🟢 Updated This month
Operational Security COO        🟢 2FA     This quarter
Brand Risk          CMO         🟢 Clean   This month
```

### 7. ACTION PLAN CONSOLIDATION

Merge all role decisions into single priority list:

| # | Action | Role | Priority | Command | Deadline |
|---|--------|------|----------|---------|----------|
| 1 | {action} | CEO | P0 | {command} | {date} |
| 2 | {action} | COO | P0 | {command} | {date} |
| 3 | {action} | Founder | P1 | {command} | {date} |
| 4 | {action} | CMO | P1 | {command} | {date} |
| 5 | {action} | Trader | P2 | {command} | {date} |

**Conflict resolution:** CEO > COO > Founder > CMO > Trader

### 8. MASTER REPORT GENERATION

Save: `plans/reports/master-{scope}-{date}-all-roles-review.md`

```markdown
## MASTER REVIEW — {scope} {date}

### Executive Summary
[5 bullets: 1 per role, key finding]

### Master Dashboard
[Combined metrics table from Step 3]

### Cross-Role Analysis
[Conflicts + synergies from Step 4]

### Role Reports
#### CEO: [1-2 sentences]
#### COO: [1-2 sentences]
#### CMO: [1-2 sentences]
#### Founder: [1-2 sentences]
#### Trader: [1-2 sentences]

### Unified Risk Assessment
[Risk layer table from Step 6]

### Consolidated Action Plan
[Priority table from Step 7]

### Next Review
- Daily check: /trading:all quick daily
- Weekly review: /trading:all quick weekly
- Monthly deep: /trading:all full monthly
- Quarterly strategic: /trading:all full quarterly
```

### 9. DELEGATION & EXECUTION

Auto-delegate actions to appropriate commands:

```
CEO actions      → /trading:ceo:allocate, /trading:ceo:risk
COO actions      → /trading:coo:health, /trading:coo:incident
CMO actions      → /trading:cmo:content, /trading:cmo:growth
Founder actions  → /trading:founder:budget, /trading:founder:scale
Trader actions   → /trading:auto:agi, /trading:auto:stealth
Emergency        → /trading:founder:emergency red
```

### 10. SUPREME COMMANDER SUMMARY

Final output:

```
══════════════════════════════════════════
  SUPREME COMMANDER VERDICT — {date}
══════════════════════════════════════════
  System:    🟢 OPERATIONAL / 🟡 DEGRADED / 🔴 CRITICAL
  Trading:   🟢 CONTINUE / 🟡 REDUCE / 🔴 HALT
  Growth:    🟢 SCALE UP / 🟡 HOLD / 🔴 SCALE DOWN
  Risk:      🟢 WITHIN LIMITS / 🟡 APPROACHING / 🔴 EXCEEDED
  Next:      {recommended next action + command}
══════════════════════════════════════════
```

---

## ROLE COMMAND MAP (Quick Reference)

```
ROLE            MAIN                  SUBORDINATES
────────────────────────────────────────────────────────────────
CEO             /trading:ceo          :dashboard :allocate :risk
  └ (delegates to all C-levels)
COO             /trading:coo          :health :perf :incident
  └ SRE         /trading:sre          uptime|alerts|recovery|monitor
CMO             /trading:cmo          :content :growth :launch
  └ Growth      /trading:growth       funnel|experiment|viral|conversion
CTO             /trading:cto          audit
  └ Backend     /trading:backend      audit|architecture|quality|modules
CFO             /trading:cfo          review|costs|tax|model
  └ Fin Analyst /trading:fin-analyst  pnl|attribution|costs|breakeven
CDO             /trading:cdo          audit|feeds|pipeline|backtest
  └ Data Eng    /trading:data-eng     pipeline|feeds|storage|health
CPO             /trading:cpo          review|roadmap|prioritize|release
  └ Prod Analyst/trading:product-analyst metrics|adoption|segments|impact
CXO             /trading:cxo          audit|onboard|a2ui
CHRO            /trading:chro         audit
CAIO            /trading:caio         audit|weights|learning|model
  ├ Quant       /trading:quant        discover|backtest|alpha|propose
  └ ML Eng      /trading:ml-eng       learning|weights|features|model
CSO             /trading:cso          audit|scan|stealth|keys
  └ Sec Analyst /trading:sec-analyst  scan|stealth|keys|vuln
CCO             /trading:cco          review|revenue|pipeline|pricing|b2b
Founder         /trading:founder      :budget :strategy :scale :emergency
  ├ Risk Analyst/trading:risk-analyst var|stress|correlation|report
  └ Mkt Analyst /trading:market-analyst regime|macro|sentiment|intel
Trader          /trading:auto         :parallel :fast :agi :stealth
  └ Exec Spec   /trading:exec-spec    routing|fills|slippage|health
MASTER          /trading:all          full|quick|emergency
```

**Total: 26 roles (14 C-Suite + 12 Subordinates) | 59 trading commands | 1 master orchestrator**

---

## USAGE

```bash
# Full quarterly review (all roles, all steps)
/trading:all full quarterly

# Quick weekly check (focused metrics)
/trading:all quick weekly

# Daily morning glance
/trading:all quick daily

# Emergency response
/trading:all emergency "portfolio drawdown 20%"

# Monthly deep dive
/trading:all full monthly
```
