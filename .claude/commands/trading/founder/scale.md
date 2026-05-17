---
description: ⚡⚡⚡ Founder Scaling — milestone tracking, scale up/down decisions, budget progression, AGI/stealth enablement
argument-hint: [action: review|up|down] [reason: "milestone or signal"]
---

**Ultrathink** Founder scaling decisions: <args>$ARGUMENTS</args>

**CWD:** `apps/algo-trader` | **REF:** `docs/founder-sops.md` SOP-F09

## Pipeline (3 steps)

### 1. SCALE-UP Milestones

| # | Milestone | Condition | Met? | Action |
|---|-----------|-----------|------|--------|
| 1 | Start live | Paper profitable 1 week | ✅/❌ | Live $50/day |
| 2 | Increase budget | Live profitable 2 weeks | ✅/❌ | Budget → $100/day |
| 3 | Double budget | Live profitable 1 month | ✅/❌ | Budget → $200/day |
| 4 | Enable AGI | Sharpe >1.5 sustained | ✅/❌ | `/trading:auto:agi live` |
| 5 | Enable stealth | Cross-exchange spread >0.1% | ✅/❌ | `/trading:auto:stealth` |
| 6 | Add pairs | 1 month stable on 2 pairs | ✅/❌ | Add 3rd pair |
| 7 | Add exchange | 1 month stable on 2 exchanges | ✅/❌ | Add 3rd exchange |

### 2. SCALE-DOWN Signals

| Signal | Threshold | Action |
|--------|-----------|--------|
| Weekly loss | >5% portfolio | Cut budget 50% |
| Sharpe decline | <0.5 sustained | Back to paper |
| Circuit breaker | 3x/week trigger | Review + reduce |
| Max drawdown | >15% | HALT → SOP-F08 |
| Consecutive losses | 5 in a row | Downgrade autonomy |
| Exchange regulation | New restriction | Pause affected exchange |

### 3. SCALING REPORT

```markdown
## Scaling Assessment — {date}

### Current State
- Budget: $XX/day
- Mode: paper/live/agi/stealth
- Exchanges: N active
- Pairs: N active

### Milestones
| Milestone | Status | ETA |
|-----------|--------|-----|

### Recommendation: SCALE UP / HOLD / SCALE DOWN
Reasoning: ...
Next milestone target: ...
```

## USAGE
```bash
/trading:founder:scale review               # Full milestone review
/trading:founder:scale up "paper profitable 1 week"  # Document scale-up
/trading:founder:scale down "weekly loss 6%"         # Document scale-down
```
