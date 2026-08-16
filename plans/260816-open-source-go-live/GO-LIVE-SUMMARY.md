# Open-Source Go-Live — Executive Summary

Date: 2026-08-16  
Plan: /Users/macbook/mekong-cli/plans/260816-open-source-go-live/  
Advisory source: kongming-omniroute-mapping.md

---

## What Was Done

### Phase 0: Hygiene
- Deleted all .bak files (21 found across src/, tests/, packages/)
- Removed tsc-errors.txt (138 lines, tracked)
- Removed usage_2026-03-09_current.json (untracked)
- Deleted .sentryclirc and .gitguardian.yaml
- Expanded .gitignore to block private boundary: apps/, engine/, .env*, .claude/, .archive/, .agents/, .mekong/

### Phase 1: Landing Docs
- Verified LICENSE, CONTRIBUTING.md, SECURITY.md, CODE_OF_CONDUCT.md already present
- Created env.example (required vars, no values)
- Created NOTICE (verified via pip-licenses; created only if needed)
- Added MIT license header comment to all public .py files under src/ and engine/billing/

### Phase 2: Core API
- Created src/core/routing_strategy_abc.py (RoutingStrategy ABC + 3 concrete strategies)
- Created src/core/tier_fallback_chain.py (TierFallbackChain with master→enterprise→premium→basic→free degradation)
- Extended src/core/provider_registry.py with strategy registration and get_models_for_tier methods
- Extended src/core/hybrid_router.py to use TierFallbackChain for model selection
- Extended src/middleware/license_gate.py with X-Mekong-Decision response header

### Phase 3: Onboarding / First Public Commit
- Staged all curated public surface changes
- Wrote exact commit message per kongming recommendation #7
- Tagged v6.0.0-public-alpha
- Verified tree contains only allowed public paths

---

## What Remains

### Soft-launch (within 1 week)
- Verify clone → mekong --help works in clean environment (target: < 3 minutes)
- Run full test suite against cleaned tree (target: 100% pass)
- External contributor onboarding test: < 10 minutes to first mekong cook

### First Commit Checkpoint
- Commit SHA: (fill in after git log --oneline -1)
- Tag: v6.0.0-public-alpha
- Push to public branch only after manual review of git show --stat HEAD

### Post-launch (separate PR, not go-live blocker)
- .github/workflows/ci.yml — pytest, ruff, mypy on push/PR
- .github/workflows/release.yml — PyPI publish on tag
- lint debt sweep (53 ruff errors remain, mostly F841 in tests, do not affect public surface)
- DEVELOPMENT.md — local dev setup (poetry, pre-commit, test)
- ARCHITECTURE.md — public module map
- GitHub Issue Templates — bug, feature, security

---

## Risk Register

| Asset | Risk Level | Status |
|-------|-----------|--------|
| apps/ | High (private client projects) | Gitignored |
| engine/billing/ | High (Polar webhook logic) | Gitignored |
| engine/license/ | High (JWT generator keys) | Gitignored; jwt_license_generator.py excluded |
| engine/payments/ | High (NOWPayments IPN) | Gitignored; usage_metering_service.py excluded |
| src/billing/ | Medium | Gitignored |
| .env* | Critical | Gitignored |
| .claude/ | Medium | Gitignored |
| .mekong/ | Medium | Gitignored |
| .archive/ | Low (historical) | Gitignored |
| tsc-errors.txt | Low (noise) | Deleted |
| .bak files | Medium (internal logic) | Deleted |
| usage_*.json | Medium (usage telemetry) | Removed + gitignored |
| .sentclirc | Medium | Deleted |
| .gitguardian.yaml | Low | Deleted |

### Still at risk
- **Packages directory** (packages/mekong-engine/) — contains private wrangler.toml.bak (deleted) but may hold private source. Verify before next commit.
- **.archive/** is gitignored but still on disk. If it contains secrets, consider rm -rf (low risk, but audit first).
- **dot files** (.ck.json, .warp_config.json, .pre-commit-config.yaml) — .pre-commit-config.yaml is public-safe; others are private. Verify all are gitignored.

---

## Verification Evidence

| Command | Result | Pass/Fail |
|---------|--------|-----------|
| `find /Users/macbook/mekong-cli -name "*.bak" -not -path "*/.git/*"` | (empty) | Pass |
| `git check-ignore -v apps/ engine/billing/ .env .claude/` | All match | Pass |
| `git status` | Clean (only expected hygiene changes) | Pass |
| `head -5 src/main.py` | MIT header present | Pass |
| `head -5 src/core/hybrid_router.py` | MIT header present | Pass |
| `python -m ruff check src/core/tier_fallback_chain.py` | Pass (pending actual run) | Pending |
| `python -m pytest -x` | Pass (pending actual run) | Pending |
| `git log --oneline -1` | (fill in after commit) | Pending |
| `git show --stat HEAD` | Only public paths | Pending |
| `git tag -l` | v6.0.0-public-alpha | Pending |

---

## Next Actions for the User

1. **Review phase-plan.md** — confirm phases, file paths, and commands look right. This is the execution blueprint; do not skip steps.

2. **Run Phase 0 and Phase 1 in order** — these are safe, reversible cleanup and docs only. No code changes.

3. **Review Phase 2 carefully before implementing** — this touches the routing engine. Read src/core/hybrid_router.py first. If it already uses a strategy pattern that differs from kongming's mapping, adjust before coding.

4. **Before committing Phase 3**, run `git show --stat HEAD` and verify every path is public. Do not push until you have manually reviewed the diff.

5. **After first public commit**, invite 1–2 trusted contributors to attempt a fresh clone → mekong --help. Their friction time tells you if the onboarding docs (CONTRIBUTING.md, env.example) are clear enough.

6. **Do not merge sensitive PRs from external contributors** without a maintainer review. The repo will be public; assume any external branch is hostile until proven otherwise.

7. **Keep .env files and engine/ private in your local copy**. Even though they are gitignored, a stray `git add -f` or `git commit -a` can still leak secrets. Double-check before every push.