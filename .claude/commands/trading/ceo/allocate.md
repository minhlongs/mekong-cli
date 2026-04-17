---
description: ⚡⚡⚡ CEO Capital Allocation — portfolio rebalancing, tier management, asset class optimization
argument-hint: [action: review|rebalance|set] [tier: algo|hodl|yield|cash] [percentage: XX%]
---

**Ultrathink** CEO capital allocation: <args>$ARGUMENTS</args>

**CWD:** `apps/algo-trader` | **REF:** `docs/ceo-sops.md` SOP-C03, `docs/founder-sops.md` SOP-F03

---

## ALLOCATION FRAMEWORK

### Level 1: Asset Classes (CEO decides)

| Class | Target Range | Description |
|-------|-------------|-------------|
| Algo Trading | 30-50% | Bot-managed active trading |
| HODLing | 30-40% | Long-term BTC/ETH/blue-chips |
| Stablecoin Yield | 10-20% | Lending, LP, T-Bill stables |
| Cash Reserve | 10-20% | Emergency fund, 6mo runway |

### Level 2: Algo Trading Tiers (Founder manages)

| Tier | Target | Risk | Mode |
|------|--------|------|------|
| Cash Reserve | 40% | None | Idle |
| Paper Trading | 20% | Zero | `/trading:auto:agi paper` |
| Live Conservative | 25% | Low | `/trading:auto:agi live` confirm |
| Live Aggressive | 10% | Medium | `/trading:auto:agi live` auto |
| Stealth Arb | 5% | High | `/trading:auto:stealth` |

---

## PIPELINE (5 steps)

### 1. Current State
- Read recent trading reports for P&L data
- Calculate current allocation percentages
- Identify drift from targets

### 2. Drift Analysis
```
Asset Class     Target    Current    Drift     Action
─────────────────────────────────────────────────────
Algo Trading    40%       XX%        +/-X%     REBALANCE?
HODLing         35%       XX%        +/-X%     REBALANCE?
Stable Yield    15%       XX%        +/-X%     REBALANCE?
Cash Reserve    10%       XX%        +/-X%     REBALANCE?
```
**Trigger:** Rebalance if ANY class drifts >10% from target.

### 3. Rebalance Plan
- Calculate exact amounts to move
- Prioritize: Cash Reserve FIRST (never below 10%)
- Generate step-by-step rebalance instructions

### 4. Scaling Check (SOP-F09)
| Milestone | Met? | Action |
|-----------|------|--------|
| Paper profitable 1 week | | Start live $50 |
| Live profitable 2 weeks | | Increase $100 |
| Live profitable 1 month | | Increase $200 |
| Weekly loss >5% | | Cut 50% |
| Sharpe <0.5 | | Back to paper |

### 5. Report
Save: `plans/reports/ceo-allocation-{date}.md`

## USAGE
```bash
/trading:ceo:allocate review           # Show current allocation
/trading:ceo:allocate rebalance        # Generate rebalance plan
/trading:ceo:allocate set algo 45%     # Set algo trading target
```
