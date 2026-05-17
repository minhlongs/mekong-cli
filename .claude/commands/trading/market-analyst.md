---
description: ⚡⚡⚡ Market Analyst — regime detection, macro analysis, sentiment scoring, market intelligence
argument-hint: [action: regime|macro|sentiment|intel]
---

**Ultrathink** Market analysis: <args>$ARGUMENTS</args>

**CWD:** `apps/algo-trader` | **REF:** `docs/trading-team-subordinates-sops.md` PART 3
**Reports to:** CAIO (`/trading:caio`)

## Pipeline (4 steps)

### 1. REGIME DETECTION
Using `src/execution/market-regime-detector.ts`, `src/core/signal-market-regime-detector.ts`:
| Indicator | Value | Signal |
|-----------|-------|--------|
| ADX | XX | Trending/Ranging |
| Price vs SMA200 | Above/Below | Bull/Bear |
| ATR vs avg | X.Xx | Vol high/low/normal |
| BB width | X.X% | Squeeze/Expansion |
**Current regime:** TREND_UP / TREND_DOWN / RANGING / VOLATILE

### 2. MACRO INDICATORS
| Indicator | Current | Trend | Impact |
|-----------|---------|-------|--------|
| BTC Dominance | XX% | ↑↓→ | Alt season? |
| Fear & Greed | XX | ↑↓→ | Contrarian |
| DXY | XXX | ↑↓→ | Inverse BTC |
| Funding rates | X.XX% | ↑↓→ | Positioning |
| Open interest | $XB | ↑↓→ | Leverage |

### 3. SENTIMENT SCORE
| Source | Weight | Score | Signal |
|--------|--------|-------|--------|
| Funding rates | 0.30 | X/100 | — |
| Open interest | 0.25 | X/100 | — |
| Social momentum | 0.20 | X/100 | — |
| Reddit sentiment | 0.15 | X/100 | — |
| Exchange reserves | 0.10 | X/100 | — |
| **Composite** | 1.00 | **X/100** | FEAR/NEUTRAL/GREED |

### 4. INTELLIGENCE REPORT
Save: `plans/reports/market-intel-{date}.md`

## USAGE
```bash
/trading:market-analyst regime     # Market regime detection
/trading:market-analyst macro      # Macro indicator dashboard
/trading:market-analyst sentiment  # Sentiment scoring
/trading:market-analyst intel      # Full intelligence report
```
