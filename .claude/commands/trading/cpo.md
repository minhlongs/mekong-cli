---
description: ⚡⚡⚡⚡ CPO Product Command — product roadmap, feature prioritization (ICE), release management, user feedback loop
argument-hint: [action: review|roadmap|prioritize|release]
---

**Ultrathink** CPO product review: <args>$ARGUMENTS</args>

**CWD:** `apps/algo-trader` | **REF:** `docs/cpo-sops.md`

## Pipeline (5 steps)

### 1. ROADMAP STATUS
Read `docs/project-roadmap.md` and report:
| Phase | Status | Progress | ETA |
|-------|--------|----------|-----|
| Phase 1 | ✅/🔄/⏳ | XX% | — |
| Phase 2 | ✅/🔄/⏳ | XX% | — |
| Phase N | ✅/🔄/⏳ | XX% | — |

Allocation check:
| Category | Target | Actual | Balanced? |
|----------|--------|--------|-----------|
| Core Trading | 40% | XX% | ✅/❌ |
| Safety & Risk | 25% | XX% | ✅/❌ |
| Stealth & Edge | 15% | XX% | ✅/❌ |
| Platform & UX | 15% | XX% | ✅/❌ |
| Infra & Ops | 5% | XX% | ✅/❌ |

### 2. FEATURE PRIORITIZATION (ICE)
Scan GitHub issues + backlog, score each:
| Feature | Impact | Confidence | Ease | ICE | Priority |
|---------|--------|------------|------|-----|----------|
| {name} | X/10 | X/10 | X/10 | X.X | P0/P1/P2 |

ICE = Impact×0.4 + Confidence×0.3 + Ease×0.3
- P0 (8-10): Do Now
- P1 (6-7.9): Next Sprint
- P2 (4-5.9): Backlog

### 3. RELEASE READINESS
| Check | Status |
|-------|--------|
| Tests pass (1216+) | ✅/❌ |
| No `any` types | ✅/❌ |
| No `@ts-ignore` | ✅/❌ |
| No `console.log` | ✅/❌ |
| Docs updated | ✅/❌ |
| Changelog entry | ✅/❌ |
| CI/CD GREEN | ✅/❌ |

### 4. PRODUCT METRICS
| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Active strategies | X | ≥4 | 🟢/🔴 |
| Win rate | XX% | >55% | 🟢/🔴 |
| System uptime | XX% | >99% | 🟢/🔴 |
| Time to first trade | Xm | <15min | 🟢/🔴 |

### 5. REPORT
Save: `plans/reports/cpo-product-{date}.md`

## USAGE
```bash
/trading:cpo review      # Full product review
/trading:cpo roadmap     # Roadmap status check
/trading:cpo prioritize  # ICE feature scoring
/trading:cpo release     # Release readiness check
```
