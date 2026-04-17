---
description: ⚡⚡⚡⚡ CAIO AI Command — signal quality audit, self-learning review, model performance, strategy weight optimization
argument-hint: [action: audit|weights|learning|model]
---

**Ultrathink** CAIO AI review: <args>$ARGUMENTS</args>

**CWD:** `apps/algo-trader` | **REF:** `docs/caio-cso-cco-sops.md` PART 1

## Pipeline (4 steps)

### 1. SIGNAL QUALITY
| Strategy | Accuracy | Weight | Trend | Status |
|----------|----------|--------|-------|--------|
| MacdBollingerRsi | XX% | 0.30 | ↑↓→ | 🟢/🔴 |
| RsiSma | XX% | 0.25 | ↑↓→ | 🟢/🔴 |
| Bollinger | XX% | 0.25 | ↑↓→ | 🟢/🔴 |
| MacdCrossover | XX% | 0.20 | ↑↓→ | 🟢/🔴 |

Config: `consensusThreshold: 0.6, minVotes: 2`
Source: `src/core/SignalGenerator.ts`

### 2. SELF-LEARNING LOOP
- Win→weight +0.05 (cap 0.5) working?
- Loss→weight -0.05 (floor 0.05) working?
- Normalization (sum=1.0) correct?
- 3 losses → escalate triggered?
- 5 wins → restore triggered?
Source: `src/core/autonomy-controller.ts`

### 3. MODEL PERFORMANCE
| Metric | Value | Target |
|--------|-------|--------|
| LLM latency | Xms | <2000ms |
| Token cost/day | $X | <$5 |
| Signal gen time | Xs | <5s |
| False positive rate | XX% | <20% |

### 4. RECOMMENDATIONS
- Adjust weights? Threshold? MinVotes?
- New strategy candidates?
- Model upgrade needed?

## USAGE
```bash
/trading:caio audit      # Full AI audit
/trading:caio weights    # Strategy weight review
/trading:caio learning   # Self-learning loop check
/trading:caio model      # Model performance
```
