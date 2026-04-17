---
description: ⚡⚡⚡ Founder Budget — 5-tier allocation management, rebalancing triggers, P&L tracking per tier
argument-hint: [action: review|rebalance|set] [tier: cash|paper|live|aggressive|stealth] [amount: $XX]
---

**Ultrathink** Founder budget management: <args>$ARGUMENTS</args>

**CWD:** `apps/algo-trader` | **REF:** `docs/founder-sops.md` SOP-F03

## 5-Tier Framework

| Tier | Target | Risk | Mode | Command |
|------|--------|------|------|---------|
| 1. Cash Reserve | 40% | None | Idle | — |
| 2. Paper Trading | 20% | Zero | `/trading:auto:agi paper` | Test strategies |
| 3. Live Conservative | 25% | Low | `/trading:auto:agi live` confirm | Small budget |
| 4. Live Aggressive | 10% | Medium | `/trading:auto:agi live` auto | Verified strategies |
| 5. Stealth Arb | 5% | High | `/trading:auto:stealth` | Cross-exchange |

## Pipeline (4 steps)

### 1. Current Allocation
Read recent reports, calculate current % per tier.
```
Tier         Target    Current    Delta     Status
────────────────────────────────────────────────────
Cash Reserve   40%      XX%       +/-X%     🟢/🔴
Paper          20%      XX%       +/-X%     🟢/🔴
Live Cons.     25%      XX%       +/-X%     🟢/🔴
Live Aggr.     10%      XX%       +/-X%     🟢/🔴
Stealth Arb     5%      XX%       +/-X%     🟢/🔴
```

### 2. Scale Rules Check
| Condition | Action |
|-----------|--------|
| Paper profitable 3 days | Move 5% Tier 2→3 |
| Live profitable 1 week | Move 5% Tier 1→3 |
| Live profitable 1 month | Move 5% Tier 3→4 |
| Loss >10% Tier 3 in week | Move ALL Tier 3→2 |
| Loss >20% portfolio | HALT ALL |

### 3. P&L Per Tier
| Tier | Capital | P&L Week | P&L Month | ROI % |
|------|---------|----------|-----------|-------|

### 4. Rebalance Plan
If any tier drifts >10% from target → generate move instructions.

## USAGE
```bash
/trading:founder:budget review           # Show current allocation
/trading:founder:budget rebalance        # Generate rebalance plan
/trading:founder:budget set paper 25%    # Adjust tier target
```
