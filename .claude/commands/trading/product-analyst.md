---
description: ⚡⚡⚡ Product Analyst — product metrics, feature adoption, user segmentation, impact analysis
argument-hint: [action: metrics|adoption|segments|impact]
---

**Ultrathink** Product analysis: <args>$ARGUMENTS</args>

**CWD:** `apps/algo-trader` | **REF:** `docs/trading-team-subordinates-sops.md` PART 12
**Reports to:** CPO (`/trading:cpo`)

## Pipeline (4 steps)

### 1. PRODUCT METRICS DASHBOARD
| Metric | Definition | Current | Trend |
|--------|-----------|---------|-------|
| DAU | Daily active bot instances | X | ↑↓→ |
| Feature adoption | % users per feature | XX% | ↑↓→ |
| Error rate | Errors per session | X.X | ↑↓→ |
| Task completion | Config→running | XX% | ↑↓→ |
| NPS proxy | Stars/issues ratio | X.X | ↑↓→ |

### 2. FEATURE ADOPTION
| Feature | Users | Adoption% | Trend |
|---------|-------|-----------|-------|
| Paper trading | X | XX% | ↑↓→ |
| Live trading | X | XX% | ↑↓→ |
| Arbitrage | X | XX% | ↑↓→ |
| Multi-exchange | X | XX% | ↑↓→ |
| Stealth mode | X | XX% | ↑↓→ |
| Custom strategies | X | XX% | ↑↓→ |

### 3. USER SEGMENTS
| Segment | Behavior | Size | Needs |
|---------|----------|------|-------|
| Beginner | Paper trading only | X | Easy setup, docs |
| Active trader | 1-3 pairs, conservative | X | Reliability, alerts |
| Power user | 5+ pairs, multi-exchange | X | Performance, API |
| Quant | Custom strategies | X | Extensibility |

### 4. FEATURE IMPACT ANALYSIS
| Feature | Before | After | Uplift | Keep? |
|---------|--------|-------|--------|-------|
| {feature} | X | X | ±X% | ✅/❌ |

## USAGE
```bash
/trading:product-analyst metrics    # Product metrics dashboard
/trading:product-analyst adoption   # Feature adoption tracking
/trading:product-analyst segments   # User segmentation
/trading:product-analyst impact     # Feature impact analysis
```
