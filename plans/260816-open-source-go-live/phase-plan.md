# Open-Source Go-Live — Phase Plan

## Overview

| Phase | Title | Goal | Verified by |
|-------|-------|------|-------------|
| Phase 0 | Hygiene | Remove all private/risk artifacts, update `.gitignore`, clean working tree | `git status --ignored` shows clean public surface |
| Phase 1 | Landing Docs | Add `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, `env.example`, license headers on all public `.py` files | `head -5 src/main.py` shows MIT header; docs exist |
| Phase 2 | Core API | Implement `src/core/tier_fallback_chain.py` and extend `src/core/provider_registry.py` with strategy ABC from kongming's mapping | `ruff check src` + `python3 -m pytest -x` pass |
| Phase 3 | Onboarding / First Public Commit | Prepare commit with exact message and file list from kongming recommendation #7 (first checkpoint commit) | `git log --oneline -1` matches expected message; tree is clean |

**Work context:** /Users/macbook/mekong-cli
**Reports path:** /Users/macbook/mekong-cli/plans/reports/
**Plans path:** /Users/macbook/mekong-cli/plans/

---

## Key Private Boundary (DO NOT include in public surface)

- `apps/` (all 5 client projects)
- `engine/billing/`, `engine/license/`, `engine/payments/`
- `src/billing/`
- `.claude/`, `.agents/`, `.archive/`
- `tsc-errors.txt` (DELETE)
- `src/billing/engine.py.bak` (DELETE)
- `usage_*.json` (REMOVE)
- `.env*`, `.env.*`, `.gitguardian.yaml`, `.ck.json`, `.sentryclirc`

---

## Phase 0: Hygiene

### Objective
Remove all private/risk artifacts, update `.gitignore`, clean working tree so the public surface contains no sensitive internal data.

### File list
- **CREATE:** None
- **MODIFY:** `/Users/macbook/mekong-cli/.gitignore`
- **DELETE:**
  - `/Users/macbook/mekong-cli/tsc-errors.txt`
  - `/Users/macbook/mekong-cli/usage_2026-03-09_current.json`
  - `/Users/macbook/mekong-cli/*.bak` (in root)
  - `/Users/macbook/mekong-cli/src/*.bak`
  - `/Users/macbook/mekong-cli/src/commands/*.bak`
  - `/Users/macbook/mekong-cli/src/middleware/*.bak`
  - `/Users/macbook/mekong-cli/src/core/*.bak`
  - `/Users/macbook/mekong-cli/src/security/*.bak`
  - `/Users/macbook/mekong-cli/tests/*.bak`
  - `/Users/macbook/mekong-cli/tests/e2e/*.bak`
  - `/Users/macbook/mekong-cli/packages/mekong-engine/*.bak`
  - `/Users/macbook/mekong-cli/particle/.ck.json`
  - `/Users/macbook/mekong-cli/.sentryclirc`
  - `/Users/macbook/mekong-cli/.gitguardian.yaml`

### Step-by-step instructions

1. **Delete all `.bak` files:**
   ```bash
   find /Users/macbook/mekong-cli -name "*.bak" -not -path "*/.git/*" -delete
   ```

2. **Delete `tsc-errors.txt` (tracked):**
   ```bash
   git rm --cached tsc-errors.txt
   rm -f tsc-errors.txt
   ```

3. **Remove usage data (untracked):**
   ```bash
   rm -f usage_2026-03-09_current.json
   ```

4. **Delete sentry config and gitguardian config:**
   ```bash
   rm -f .sentryclirc .gitguardian.yaml
   ```

5. **Update `.gitignore`** to add the full private boundary from kongming:
   ```
   # Private applications
   apps/
   
   # Private services (Polar webhook, NOWPayments, JWT license gen, telemetry)
   engine/billing/
   engine/license/
   engine/payments/
   src/billing/
   
   # Agent/tooling configs
   .claude/
   .agents/
   .archive/
   .mekong/
   
   # Credentials/secrets
   .env*
   .env.*
   .ck.json
   .gitguardian.yaml
   .sentryclirc
   
   # Private scratch
   *.bak
   usage_*.json
   tsc-errors.txt
   .sentryclirc
   ```

6. **Stage the `.gitignore` update:**
   ```bash
   git add .gitignore
   ```

### Verification commands

```bash
# Verify no .bak files remain
find /Users/macbook/mekong-cli -name "*.bak" -not -path "*/.git/*"

# Verify tsc-errors.txt gone
ls /Users/macbook/mekong-cli/tsc-errors.txt 2>&1

# Verify gitignore blocks private paths
git check-ignore -v apps/ engine/billing/ .env .claude/

# Check git status for unexpected changes
git status
```

### Risks / edge cases
- `.archive/` contains large historical artifacts but is untracked (gitignored already). Deleting it risks losing scoped historical research.
- `usage_2026-03-09_current.json` is untracked; `--cached` not needed.
- Some `.bak` files may be referenced by other scripts. Verify none are imported before deletion.

### Success criteria
- [ ] No `.bak` files exist in the tree
- [ ] `tsc-errors.txt` is not in working tree or index
- [ ] `git check-ignore` returns matches for all private paths
- [ ] `git status` reflects only hygiene changes

---

## Phase 1: Landing Docs

### Objective
Add CONTRIBUTING.md, SECURITY.md, CODE_OF_CONDUCT.md, env.example, and MIT license headers on all public .py files so the repo has standard open-source governance artifacts.

### File list
- **CREATE:** env.example (NOTICE only if third-party attribution required)
- **MODIFY:** all public .py files under src/ and engine/billing/tier_rate_limit_*.py, engine/billing/tier_config.py
- **NOTE:** LICENSE, CONTRIBUTING.md, SECURITY.md, CODE_OF_CONDUCT.md already exist (verified 2026-08-16)

### Step-by-step instructions

1. Verify existing governance docs:
   ```bash
   ls -la /Users/macbook/mekong-cli/LICENSE /Users/macbook/mekong-cli/CONTRIBUTING.md /Users/macbook/mekong-cli/SECURITY.md /Users/macbook/mekong-cli/CODE_OF_CONDUCT.md
   ```

2. Create env.example with required variables and empty values:
   ```
   LLM_BASE_URL=https://openrouter.ai/api/v1
   LLM_API_KEY=
   LLM_MODEL=anthropic/claude-sonnet-4
   POLAR_WEBHOOK_SECRET=
   POLAR_ORG_ID=
   JWT_SECRET_KEY=
   TELEGRAM_BOT_TOKEN=
   ZALO_OA_ID=
   ZALO_OA_SECRET=
   SENTRY_DSN=
   ```

3. Verify NOTICE necessity:
   ```bash
   pip-licenses --format=plain-vertical
   ```
   Create NOTICE only if third-party attribution is required.

4. Add MIT license header to all public .py files. Header format:
   ```python
   # Mekong CLI — AI-Powered Business Operations for Vietnam
   # MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.
   ```
   Target files: all .py under src/ (excluding .bak, __pycache__), engine/billing/tier_rate_limit_dispatch.py, engine/billing/tier_rate_limit_events.py, engine/billing/tier_rate_limit_middleware.py, engine/billing/tier_rate_limit_policy.py, engine/billing/tier_config.py.

5. Exclude private files from header addition: engine/license/jwt_license_generator.py, engine/license/license_generator.py, engine/payments/usage_metering_service.py.

### Verification commands
```bash
head -5 /Users/macbook/mekong-cli/src/main.py
head -5 /Users/macbook/mekong-cli/src/core/hybrid_router.py
head -5 /Users/macbook/mekong-cli/src/core/provider_registry.py
grep -c "=" /Users/macbook/mekong-cli/env.example
head -3 /Users/macbook/mekong-cli/engine/license/jwt_license_generator.py
```

### Risks / edge cases
- Some .py files already have docstrings at the top; prepend header as a comment block, do not replace existing content.
- Private engine files (JWT generator, usage metering service) must not receive public headers.

### Success criteria
- [ ] env.example exists with required variables and no actual values
- [ ] All public .py files in src/ have MIT header comment at top
- [ ] Private engine files do NOT have public headers (spot check jwt_license_generator.py)
- [ ] NOTICE created (or confirmed not needed)

---

## Phase 2: Core API

### Objective
Implement src/core/tier_fallback_chain.py and extend src/core/provider_registry.py with strategy ABC from kongming's mapping. This adds graceful tier degradation matching OmniRoute's combo chain.

### File list
- CREATE: /Users/macbook/mekong-cli/src/core/tier_fallback_chain.py, /Users/macbook/mekong-cli/src/core/routing_strategy_abc.py
- MODIFY: /Users/macbook/mekong-cli/src/core/provider_registry.py, /Users/macbook/mekong-cli/src/core/hybrid_router.py

### Step-by-step instructions

1. Create src/core/routing_strategy_abc.py — Strategy ABC per kongming Section 3.1 pattern.
   - Class RoutingStrategy(ABC) with abstract method select_model(tier, task_type) -> ModelSelection.
   - Concrete strategies: CostOptimizedStrategy, LatencyFirstStrategy, QuotaAwareStrategy.

2. Extend src/core/provider_registry.py.
   - Import RoutingStrategy.
   - Add method register_strategy(name, strategy: RoutingStrategy).
   - Add method get_strategy(name) -> RoutingStrategy.
   - Add method get_models_for_tier(tier, task_type) uses registered strategies.

3. Create src/core/tier_fallback_chain.py (NEW).
   - Class TierFallbackChain with:
     - TIER_ORDER = ["master", "enterprise", "premium", "basic", "free"]
     - __init__(self, provider_registry: ProviderRegistry, breaker: CircuitBreaker)
     - select_model(self, tier: str, task_type: str) -> ModelSelection
   - select_model logic: iterate t in TIER_ORDER starting at requested tier, call registry.get_models_for_tier(t, task_type). For each model, check breaker.is_healthy(provider, model_id). Return first healthy with fallback flag (True if degraded).
   - Raise NoHealthyModelError if entire chain exhausted.

4. Extend src/core/hybrid_router.py.
   - Import TierFallbackChain.
   - Initialize TierFallbackChain with existing ProviderRegistry and CircuitBreaker.
   - Replace direct provider selection with chain.select_model(user_tier, task_type).
   - Propagate ModelSelection.tier and ModelSelection.fallback to response headers (X-Mekong-Decision).

5. Add X-Mekong-Decision header in src/middleware/license_gate.py (optional extension if not already present).
   - After successful auth, set response.headers["X-Mekong-Decision"] = f"tier={tier}, provider={provider}, model={model_id}, latency_ms={latency}, credits_deducted={credits}, fallback={fallback_used}".

### Verification commands
```bash
python -c "from src.core.tier_fallback_chain import TierFallbackChain; print('TierFallbackChain imported')"
python -c "from src.core.routing_strategy_abc import RoutingStrategy; print('RoutingStrategy ABC imported')"
python -m ruff check src/core/tier_fallback_chain.py src/core/routing_strategy_abc.py src/core/provider_registry.py
python -m pytest tests/ -x -q
```

### Risks / edge cases
- hybrid_router.py may not currently use explicit strategy objects; refactoring to strategy pattern requires careful mapping of existing routing logic.
- CircuitBreaker is not tier-aware in existing code; chain.select_model may get quorum that is valid for free but not for master — ensure breaker configs are tier-respectful.
- Tests may need new fixtures for TierFallbackChain; verify existing tests still pass.

### Success criteria
- [ ] TierFallbackChain implemented and importable
- [ ] RoutingStrategy ABC added with at least one concrete strategy
- [ ] provider_registry.py exposes new strategy methods
- [ ] hybrid_router.py uses TierFallbackChain for model selection
- [ ] python -m ruff check src and python -m pytest -x pass

---

## Phase 3: Onboarding / First Public Commit

### Objective
Stage all go-live changes, write a clean checkpoint commit with the exact message from kongming recommendation #7, and tag the milestone. The tree should be clean and reproducible after this commit.

### Commit message (copy exactly)
```
chore: open-source go-live — curated public surface

- Remove all .bak files, tsc-errors.txt, usage_*.json
- Add .gitignore for private boundaries (apps/, engine/, .env*, .claude/, etc.)
- Add env.example with required vars (LLM_, POLAR_, JWT_, TELEGRAM_, ZALO_)
- Add MIT license headers to all public .py files (src/, engine/billing public)
- Verify LICENSE, CONTRIBUTING.md, SECURITY.md, CODE_OF_CONDUCT.md present
- Add TierFallbackChain + RoutingStrategy ABC (omnia fallback pattern)

Public surface: src/ (PEV engine, CLI, commands, middleware, seed),
                engine/billing/tier_config.py (rate limit config only),
                engine/license/ (JWT validation only, no generator),
                engine/payments/ (usage metering interfaces only),
                tests/, docs/, README.md, pyproject.toml

Private (excluded): apps/, engine/billing/*.py (except tier_config),
                    engine/license/jwt_license_generator.py,
                    engine/payments/usage_metering_service.py,
                    src/billing/, src/commercial/, .claude/, .env*,
                    .archive/, .agents/, .mekong/, node_modules/, packages/
```

### Step-by-step instructions

1. Stage all changes:
   ```bash
   git add .gitignore env.example NOTICE
   git add -A src/
   git add -A engine/billing/tier_rate_limit_*.py engine/billing/tier_config.py
   ```

2. Verify staged diff excludes private paths:
   ```bash
   git diff --cached --name-only | grep -E "(apps/|engine/license/jwt_license_generator.py|engine/payments/usage_metering_service.py)" && echo "PRIVATE FILES LEAKED" || echo "Clean"
   ```

3. Write the exact commit message above:
   ```bash
   git commit -m "chore: open-source go-live — curated public surface

- Remove all .bak files, tsc-errors.txt, usage_*.json
- Add .gitignore for private boundaries (apps/, engine/, .env*, .claude/, etc.)
- Add env.example with required vars (LLM_, POLAR_, JWT_, TELEGRAM_, ZALO_)
- Add MIT license headers to all public .py files (src/, engine/billing public)
- Verify LICENSE, CONTRIBUTING.md, SECURITY.md, CODE_OF_CONDUCT.md present
- Add TierFallbackChain + RoutingStrategy ABC (omnia fallback pattern)

Public surface: src/ (PEV engine, CLI, commands, middleware, seed),
                engine/billing/tier_config.py (rate limit config only),
                engine/license/ (JWT validation only, no generator),
                engine/payments/ (usage metering interfaces only),
                tests/, docs/, README.md, pyproject.toml

Private (excluded): apps/, engine/billing/*.py (except tier_config),
                    engine/license/jwt_license_generator.py,
                    engine/payments/usage_metering_service.py,
                    src/billing/, src/commercial/, .claude/, .env*,
                    .archive/, .agents/, .mekong/, node_modules/, packages/

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
   ```

4. Tag the milestone:
   ```bash
   git tag v6.0.0-public-alpha
   ```

5. Capture commit SHA and verify tree:
   ```bash
   git log --oneline -1
   git status
   ```

### Verification commands
```bash
git status --ignored | grep -E "(\.env|\.bak|tsc-errors|usage_)"
git log --oneline -1
git show --stat HEAD
git tag -l
```

### Risks / edge cases
- Commit may still include private files if listing was incorrect. Always inspect `git show --stat HEAD` before pushing.
- If `usage_*.json` reappear, they are untracked and ignored after Step 5. Verify with `git check-ignore usage_2026-03-09_current.json`.
- Tagging on main branch is fine for initial public milestone. Use annotated tags for release: `git tag -a v6.0.0-public-alpha -m "..."`.

### Success criteria
- [ ] Commit message matches kongming recommendation #7 exactly
- [ ] git show --stat HEAD contains only allowed public paths
- [ ] Tag v6.0.0-public-alpha exists
- [ ] git status is clean (no staged/unstaged changes)
- [ ] All prior phase success criteria are met

---