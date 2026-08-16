# Kongming Advisory: OmniRoute Architecture Mapping for Mekong CLI Open-Source Go-Live

---

## TL;DR

OmniRoute is a **local-first LLM gateway** with a **chain-of-responsibility combo router**, **12-engine compression pipeline**, **MCP/A2A plugin surface**, and **zero-config strategy defaults**. Mekong CLI is a **Vietnam-focused AI business platform** (billing, tax, Zalo OA, AI video) with **43 Typer commands**, **PEV constitutional engine**, **MCU billing**, and **license-gated middleware**.

**Minimum viable go-live**: Ship the **PEV Engine + CLI command fabric + tiered billing middleware** as the public core. Keep `engine/billing/`, `engine/license/`, `engine/payments/`, `apps/`, `.env*`, `.claude/`, `.agents/`, `.archive/`, `src/billing/` private. First public commit = MIT license + README + CONTRIBUTING + SECURITY + CODE_OF_CONDUCT + `env.example` + license headers on all public `.py` files.

**One pattern to borrow now**: OmniRoute's **Strategy Registry + Auto-Combo fallback chain** → map to Mekong's **Provider Registry + Hybrid Router + Tier Fallback** for LLM routing and billing tier degradation.

---

## Reframed Problem

**What is actually being decided:**
- Mekong CLI is MIT-licensed, public repo, targeting Vietnamese one-person companies
- Need to define the **curated public surface** for open-source launch
- Need to extract **transferable architectural patterns** from OmniRoute (mature local-first LLM gateway)
- Need to draw **hard private boundaries** — what never leaves the repo

**Requirements:**
- Public surface must be buildable, testable, and documented for external contributors
- Private services (billing engine, license JWT, payment webhooks, client projects) must not leak
- Go-live must not break existing paid-customer flows (Polar webhook → credit deduction)

**Goals:**
- Clean public repo that external developers can `git clone && poetry install && mekong --help`
- Architectural clarity: which OmniRoute patterns map to Mekong domains
- Actionable checklist for first public commit

**Non-goals:**
- Rewriting Mekong core to mimic OmniRoute
- Exposing Polar/NOWPayments integration code
- Opening client projects in `apps/`

---

## 1. OmniRoute Architectural Essence (Scouted from GitHub)

| Abstraction | Implementation | Key Insight |
|------------|----------------|-------------|
| **Routing Engine** | 19 pluggable strategies (priority, weighted, round-robin, cost-optimized, auto, fusion, pipeline) + Auto-Combo scores 14 factors | **Strategy Pattern + Chain of Responsibility** — combos are ordered model chains; failure slides silently to next |
| **Middleware Pipeline** | 12 composable compression engines (RTK → Caveman default, 78–95% token savings) + Guardrails (prompt-injection, credential masking, OIDC) | **Pipeline of Processors** — each engine independently toggleable per combo |
| **Circuit Breaker** | 3 layers: provider-level (408/5xx), connection cooldown (exp backoff), model lockout (per-model 429/404) | **Resilience as middleware**, not scattered in callers |
| **Dispatch / Registry** | Single `/v1` endpoint serves OpenAI/Anthropic/Responses formats → Smart Router → 4-tier fallback (Sub → API → Cheap → Free) | **Unified dispatch + tiered fallback** |
| **Plugin/Tool Surface** | MCP stdio/HTTP/SSE (109 tools, 33 scopes) + A2A JSON-RPC 2.0 (6 skills, `/.well-known/agent.json`) | **Protocol-first plugins** — MCP for tools, A2A for agent delegation |
| **CLI Registration** | 80+ commands across namespaces (`providers`, `combo`, `models`, `cache`, `mcp`, `a2a`, `skills`…) + `omniroute setup` wizard | **Namespace-scoped Typer apps** with guided onboarding |
| **Local-First / Proxy** | Loopback-only, AES-256-GCM credential encryption, zero telemetry default | **Privacy by architecture**, not config |

---

## 2. Transferable Patterns: OmniRoute → Mekong Domain Mapping

| OmniRoute Pattern | Mekong Domain | Mapping Notes |
|-------------------|---------------|---------------|
| **Strategy Registry (19 strategies)** | `src/core/provider_registry.py` + `src/core/hybrid_router.py` | Mekong already has `ProviderRegistry` and `HybridRouter` — **promote strategy selection to explicit registry** (cost-optimized, latency-first, quota-aware) |
| **Auto-Combo Fallback Chain** | MCU Billing tier degradation (MASTER → ENTERPRISE → PREMIUM → BASIC) | **Direct port**: build `TierFallbackChain` that mirrors combo chain — when tier quota exhausted, auto-downgrade to next tier's model set |
| **Compression Pipeline (12 engines)** | `src/core/llm_cache.py` + `src/middleware/` | Mekong has caching; **add token-compression middleware** (RTK/Caveman equivalents) as optional pipeline stage before LLM call |
| **Circuit Breaker (3 layers)** | `src/core/circuit_breaker.py` (exists) | **Extend to tier-aware**: per-tier breaker configs, model lockout per provider |
| **Unified Dispatch Endpoint** | `src/api/gateway.py` (FastAPI :8000) | **Already aligned** — Mekong's gateway is the dispatch point; ensure it returns `X-Mekong-Decision` header (provider/tier/latency) like OmniRoute's `X-OmniRoute-Decision` |
| **MCP Tool Surface (109 tools)** | `src/core/mcp_server.py` (44k lines) + `src/cli/plugin_integration.py` | Mekong's MCP is massive; **extract skill registry** → expose via MCP/A2A for external agents |
| **A2A Agent Protocol** | `src/core/agent_registry.py` + `src/core/agent_dispatcher.py` | **Implement `/.well-known/agent.json`** → publish Mekong's agent card for cross-agent delegation |
| **CLI Namespace Commands** | `src/cli/app_setup.py` (43 commands wired) | **Already strong** — add `mekong setup` wizard (like `omniroute setup`) for first-run LLM/tier config |
| **Zero-Config Defaults** | `src/core/smart_router.py` + `src/seed/config/` | **Add `auto` tier strategy** — if user provides no tier config, infer from connected providers (OpenRouter, Anthropic, etc.) |
| **Structured Decision Headers** | `src/middleware/license_gate.py` + `src/middleware/pilot_credit_gate.py` | **Add `X-Mekong-Decision`** on every response: `tier`, `provider`, `model`, `latency_ms`, `credits_deducted`, `fallback_used` |

---

## 3. What to Borrow Immediately (Concrete Design Techniques)

### 3.1 Strategy Registry + Auto Fallback Chain (Highest Leverage)

**OmniRoute pattern:** `ComboEngine` holds ordered list of `ModelStep`; each step has a `RoutingStrategy`. On quota/429/5xx, `CircuitBreaker` marks step unhealthy → `AutoComboEngine` selects next step.

**Mekong port:**
```python
# New: src/core/tier_fallback_chain.py
class TierFallbackChain:
    """Mirrors OmniRoute's Combo chain but for billing tiers."""
    TIER_ORDER = ["master", "enterprise", "premium", "basic", "free"]
    
    def __init__(self, provider_registry: ProviderRegistry):
        self.registry = provider_registry
        self.breaker = CircuitBreaker()  # existing
    
    def select_model(self, tier: str, task_type: str) -> ModelSelection:
        # Start at requested tier, slide down on quota/429
        for t in self.TIER_ORDER[self.TIER_ORDER.index(tier):]:
            models = self.registry.get_models_for_tier(t, task_type)
            for m in models:
                if self.breaker.is_healthy(m.provider, m.model_id):
                    return ModelSelection(model=m, tier=t, fallback=True if t != tier else False)
        raise NoHealthyModelError()
```

**Why:** Maps 1:1 to OmniRoute's combo chain. Gives Mekong **graceful degradation** when Polar webhook hasn't credited user yet — they still get `free` tier models instead of 403.

### 3.2 Structured Decision Headers (Observability)

**OmniRoute:** Every response includes `X-OmniRoute-Decision: strategy=auto, provider=anthropic, model=claude-sonnet-4, latency=234ms, fallback=false`

**Mekong port:** Add to `license_gate.py` and `pilot_credit_gate.py`:
```python
response.headers["X-Mekong-Decision"] = (
    f"tier={tier}, provider={provider}, model={model_id}, "
    f"latency_ms={latency}, credits_deducted={credits}, fallback={fallback_used}"
)
```

**Why:** External contributors can debug routing without logs. Matches OmniRoute's transparency.

### 3.3 MCP Skill Registry + `/.well-known/agent.json`

**OmniRoute:** Publishes Agent Card at `/.well-known/agent.json` with 6 Conductor skills. MCP exposes 109 tools.

**Mekong port:** 
- Extract `src/core/mcp_server.py` skills into a **registry** (`src/core/skill_registry.py`)
- Add `GET /.well-known/agent.json` endpoint in `src/api/gateway.py`
- Expose Zalo OA, Tax Engine, Sophia Video as **named skills**

**Why:** Enables agent-to-agent delegation (e.g., external agent calls `mekong.tax.calculate_tncn` via A2A).

### 3.4 `mekong setup` Guided Wizard

**OmniRoute:** `omniroute setup` walks user through provider OAuth, key storage, default combo.

**Mekong port:** Add `src/cli/setup_wizard.py`:
```bash
mekong setup
# → Prompts: LLM provider (OpenRouter/Anthropic/OpenAI), API key, default tier
# → Writes ~/.mekong/config.yaml (encrypted via machine_fingerprint)
# → Validates with a test call
```

**Why:** Lowers barrier for external contributors. Current `vn_setup` is Vietnam-specific; need generic onboarding.

---

## 4. What to Skip (Anti-Patterns for Mekong)

| OmniRoute Feature | Why Skip for Mekong |
|-------------------|---------------------|
| **Electron desktop app** | Mekong is CLI + API gateway; no desktop wrapper needed |
| **Browser pool (Puppeteer/Playwright)** | Mekong doesn't scrape; Zalo OA uses webhooks |
| **43-language i18n docs** | Mekong is VN-first; bilingual (VN/EN) only |
| **109 MCP tools** | Mekong's MCP is already 44k lines — **curate down to 15-20 core skills** (tax, Zalo, video, billing) |
| **A2A with 6 skills** | Start with **1 skill per funnel** (3 total); expand after go-live |
| **Zero-telemetry local-first** | Mekong needs **opt-in telemetry** for billing/usage metering (Polar webhook correlation) |
| **12 compression engines** | Start with **1-2** (RTK + cache); token compression is nice-to-have, not go-live blocker |
| **Remote CLI plugins (`launch-codex`)** | Mekong's plugin system (`src/cli/plugin_integration.py`) is sufficient |

---

## 5. Non-Negotiable Private Set (Never Public)

Based on CLAUDE.md boundary rules and scouted audit:

### Directories (Entire)
```
/apps/                          # 5 client projects with node_modules, .next builds
/apps/api/                      # Private API deployments
/apps/dashboard/                # Private dashboard (Cloudflare Pages)
/apps/landing/                  # Private marketing
/apps/mekong-ide/               # Private IDE
/apps/nhipdieuxanh-orchestrator/ # Private orchestrator
/apps/sophia-ai-factory/        # Private AI Video Factory
/engine/billing/                # Internal billing workspace (CLAUDE.md #5)
/engine/license/                # JWT license generator (private service)
/engine/payments/               # NOWPayments → Polar integration (private)
/src/billing/                   # Internal workspace (CLAUDE.md #5)
/src/commercial/                # Commercial code
/.archive/                      # Archived code
/.agents/                       # Agent configs
/.claude/                       # Local Claude Code config (CLAUDE.md: "Do not bundle .claude/")
/.mekong/                       # Local runtime data
/.github/                       # CI/CD workflows (keep private until go-live)
/.ci/                           # CI scripts
/.orchestrate/                  # Orchestration state
/.specify/                      # Spec-kit local state
/.turbo/                        # Turbo cache
/.venv/ .venv-seed/             # Virtual envs
/node_modules/                  # JS deps
/packages/                      # Monorepo packages (private)
/venture-os/                    # Internal venture tooling
/particle/                      # Internal particle system
/polymarket/                    # Internal prediction market
/factory/                       # Internal factory
/recipes/                       # Internal recipes
/data/                          # Local data
/logs/                          # Runtime logs
/sops/                          # Secrets ops
/observability/                 # Grafana/PostHog configs (private dashboards)
/cloudflare-skills/             # Private CF Workers skills
/harness/                       # Test harness
/evals/                         # Evaluation data
/benchmarks/                    # Benchmark results
/test-results/                  # Test outputs
/scripts/                       # Deploy scripts (contain secrets)
```

### Files (Hard Private)
```
/.env
/.env.local
/.env.test
/.env.secrets
/.gitguardian.yaml
/.sentryclirc
/.ck.json
/cto-daemon.sh
/mekong.spec
/OPUS_HANDOFF_PROMPT.md
/ORIGINAL_REQUEST.md
/DEPLOYMENT_SUMMARY.md
/IDEA_AUTOPILOT.md
/ZENOS.md
/ANTIGRAVITY.md
/AGY.md
/PUBLISH.sh
/ecosystem.social.cjs
/content_tweets_agencyos_20260117.txt
/tsc-errors.txt                 # 18KB TypeScript error dump — tracked but private
/usage_2026-03-09_current.json  # Untracked usage data
/src/billing/engine.py.bak      # Backup file
/src/commands/license_admin.py.bak*  # 4 backup files
/src/core/*.bak                 # 10+ backup files in core/
/apply_all_fixes*.py            # One-time fix scripts
/reapply_fixes.py
/fix_*.py
/verify_brand.py
/fix_indent.py
/run_validation.log
/run_validation.sh
/Makefile                       # Contains private deploy targets
/docker-compose*.yml            # Private infra
/Dockerfile*                    # Private images
/pnpm-workspace.yaml
/poetry.lock                    # Lockfile OK but large
/package-lock.json              # Lockfile OK but large
/VERSION                        # Version file
```

### Private Services (Code That Must Not Leak)
- **Polar webhook handler** (`src/api/billing/`, `src/services/polar_client.py`)
- **NOWPayments IPN** (`engine/payments/`)
- **JWT license generator/validator** (`engine/license/jwt_license_generator.py`)
- **MCU billing singleton** (`src/core/mcu_billing.py`, `engine/billing/`)
- **License enforcement middleware** (`src/middleware/license_gate.py`, `src/middleware/pilot_credit_gate.py`)
- **Telegram bot webhook** (`src/core/telegram_bot/`, `src/commands/telegram_commands.py`)
- **Zalo OA integration** (`src/commands/zalo_oa.py`, `src/tree/zalo/`)
- **Tax engine (thue_dnvn, ke_toan)** (`src/commands/thue_dnvn.py`, `src/commands/ke_toan.py`, `src/raas/`)
- **Sophia AI Video** (`apps/sophia-ai-factory/`, `src/ai/`)

---

## 6. Minimum Viable Go-Live Scope (Curated Ticket List, Ordered)

### Phase 0: Repository Hygiene (Do First — 1 commit)
| # | Ticket | Verification |
|---|--------|--------------|
| 0.1 | **Delete all `.bak` files** (`src/commands/license_admin.py.bak*`, `src/core/*.bak`, `src/billing/engine.py.bak`) | `git status` shows no `.bak` |
| 0.2 | **Remove `tsc-errors.txt`** (18KB tracked error dump) | `git rm tsc-errors.txt` |
| 0.3 | **Remove `usage_2026-03-09_current.json`** (untracked usage data) | `git rm --cached usage_2026-03-09_current.json` |
| 0.4 | **Add `.gitignore` entries** for all private directories/files above | `git check-ignore apps/ engine/billing/ .env` all match |
| 0.5 | **Create `env.example`** with all required vars (no values) | `cat env.example` shows `LLM_API_KEY=`, `POLAR_WEBHOOK_SECRET=`, etc. |

### Phase 1: Public Surface Documentation (1 commit)
| # | Ticket | Verification |
|---|--------|--------------|
| 1.1 | **Verify LICENSE** (MIT, exists) | `cat LICENSE` |
| 1.2 | **Verify CONTRIBUTING.md** (exists, has setup + test commands) | `cat CONTRIBUTING.md` |
| 1.3 | **Verify SECURITY.md** (exists, bilingual, email security@agencyos.dev) | `cat SECURITY.md` |
| 1.4 | **Verify CODE_OF_CONDUCT.md** (exists, Contributor Covenant 1.4) | `cat CODE_OF_CONDUCT.md` |
| 1.5 | **Add license headers** to all public `.py` files (`src/`, `engine/` public parts) | `head -20 src/main.py` shows MIT header |
| 1.6 | **Create `NOTICE`** file if any third-party licenses require attribution | `cat NOTICE` |

### Phase 2: Core Public API (1 commit)
| # | Ticket | Verification |
|---|--------|--------------|
| 2.1 | **Expose `mekong setup` wizard** (new `src/cli/setup_wizard.py`) | `mekong setup --help` works |
| 2.2 | **Add `X-Mekong-Decision` header** to license_gate + pilot_credit_gate | `curl -I` shows header |
| 2.3 | **Implement `GET /.well-known/agent.json`** in gateway | `curl /.well-known/agent.json` returns Agent Card |
| 2.4 | **Extract skill registry** from `mcp_server.py` → `src/core/skill_registry.py` | `python -c "from src.core.skill_registry import SKILLS; print(len(SKILLS))"` ≥ 3 |
| 2.5 | **Add TierFallbackChain** (Section 3.1) | `mekong cook "test"` works on free tier without Polar |

### Phase 3: Contributor Onboarding (1 commit)
| # | Ticket | Verification |
|---|--------|--------------|
| 3.1 | **Update README** with accurate command count (not "443") | `find .claude/commands -name "*.md" \| wc -l` |
| 3.2 | **Add `DEVELOPMENT.md`** with local dev setup (poetry, pre-commit, test) | New contributor can `poetry install && pytest tests/ -q` in <5 min |
| 3.3 | **Add `ARCHITECTURE.md`** mapping public modules (seed, core, cli, commands, middleware) | `cat ARCHITECTURE.md` |
| 3.4 | **GitHub Issue Templates** (bug, feature, security) | `.github/ISSUE_TEMPLATE/` exists |

### Phase 4: CI/CD for Public Repo (Post-go-live, separate PR)
- `.github/workflows/ci.yml` (pytest, ruff, mypy on push/PR)
- `.github/workflows/release.yml` (PyPI publish on tag)
- **Not required for first commit** — playbook says "Add after Step 5"

---

## 7. Three Ambiguous Artifacts: Risk & Recommended Action

| Artifact | Risk | Recommended Action |
|----------|------|-------------------|
| **`src/billing/engine.py.bak`** | Backup of internal billing engine — contains Polar/NOWPayments logic, MCU singleton. **HIGH RISK** if committed. | **DELETE immediately** (Phase 0.1). Original is in `engine/billing/` (private). |
| **`tsc-errors.txt`** (18KB, tracked) | TypeScript error dump from dashboard build. No value for Python contributors. **LOW RISK** but noise. | **DELETE** (Phase 0.2). Dashboard is in `apps/dashboard/` (private). |
| **`usage_2026-03-09_current.json`** (untracked) | Usage metering snapshot. Could contain tenant IDs, credit balances. **MEDIUM RISK** if committed. | **REMOVE from working tree** (Phase 0.3). Add `usage_*.json` to `.gitignore`. |

---

## 8. First Checkpoint Commit (Exact Description)

**Commit message:**
```
chore: open-source go-live — curated public surface

- Remove all .bak files, tsc-errors.txt, usage_*.json
- Add .gitignore for private boundaries (apps/, engine/, .env*, .claude/, etc.)
- Add env.example with required vars (LLM_, POLAR_, JWT_, TELEGRAM_, ZALO_)
- Add MIT license headers to all public .py files (src/, engine/ public)
- Verify LICENSE, CONTRIBUTING.md, SECURITY.md, CODE_OF_CONDUCT.md present
- Add NOTICE for third-party attributions

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

**Files changed in this commit:**
- `.gitignore` (expanded)
- `env.example` (new)
- `NOTICE` (new, if needed)
- `src/**/*.py` (license headers added)
- `engine/billing/tier_rate_limit_*.py` (headers added)
- Deleted: `*.bak`, `tsc-errors.txt`, `usage_2026-03-09_current.json`

**Verification:**
```bash
git clone https://github.com/minhlongs/mekong-cli.git
cd mekong-cli
poetry install
mekong --help          # Shows 43 commands
mekong setup --help    # Shows wizard
pytest tests/ -q       # Passes
ruff check src/ tests/ # Passes (or known lint debt documented)
```

---

## 9. Success Metrics (How to Tell the Decision Worked)

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Clone → `mekong --help` time** | < 3 minutes | Fresh VM, `time poetry install && mekong --help` |
| **Test pass rate** | 100% on public surface | `pytest tests/ -q` exits 0 |
| **Private leakage** | 0 files | `git ls-files \| grep -E "(apps/|engine/billing/|\\.env|\\.bak)"` returns empty |
| **External contributor onboarding** | < 10 minutes to first `mekong cook` | Stopwatch test with new contributor |
| **Decision header present** | 100% of API responses | `curl -I https://api.cashclaw.cc/v1/health \| grep X-Mekong-Decision` |
| **Agent Card valid** | Passes A2A schema | `curl /.well-known/agent.json \| jq .` validates |

---

## 10. Assumptions (With Confidence)

| Assumption | Confidence | What Would Flip It |
|------------|------------|-------------------|
| `engine/billing/tier_config.py` is safe to publish (only rate limit configs, no Polar keys) | **High** — verified: only `RateLimitConfig` dataclass | If `tier_config.py` imports `jwt_license_generator` or `polar_client` |
| `engine/license/` JWT validation (not generation) is safe | **Medium** — need to split validator from generator | If `validate_jwt_license` shares secret derivation with generator |
| `engine/payments/usage_metering_*.py` interfaces only (no NOWPayments) | **Medium** — need to verify no webhook secrets | If files contain `NOWPAYMENTS_` or `POLAR_` constants |
| MIT license headers on all `.py` files satisfies PyPI + GitHub | **High** — standard practice | If any dependency requires NOTICE (check `pip-licenses`) |
| `mekong setup` wizard can encrypt config via `machine_fingerprint.py` | **High** — already used in `license_manager.py` | If `machine_fingerprint` is tied to license enforcement |
| First public commit should NOT include CI/CD workflows | **High** — playbook explicitly says "Add after Step 5" | If user demands CI from day 1 |

---

## 11. Work Checklist (For Fullstack-Developer Agent)

```markdown
## Phase 0: Repository Hygiene
- [ ] Delete all `.bak` files (find . -name "*.bak" -delete)
- [ ] git rm tsc-errors.txt
- [ ] git rm --cached usage_2026-03-09_current.json
- [ ] Expand .gitignore with all private paths (Section 5)
- [ ] Create env.example from .env (keys only, no values)

## Phase 1: Documentation
- [ ] Verify LICENSE, CONTRIBUTING.md, SECURITY.md, CODE_OF_CONDUCT.md
- [ ] Add MIT license header to all public .py files (scripts/add_license_headers.py)
- [ ] Create NOTICE if needed (pip-licenses --format=plain-vertical)

## Phase 2: Core Public API
- [ ] Implement src/cli/setup_wizard.py (mekong setup)
- [ ] Add X-Mekong-Decision header to license_gate.py + pilot_credit_gate.py
- [ ] Add GET /.well-known/agent.json to src/api/gateway.py
- [ ] Extract skill_registry.py from mcp_server.py (15-20 core skills)
- [ ] Implement TierFallbackChain in src/core/tier_fallback_chain.py
- [ ] Wire TierFallbackChain into hybrid_router.py

## Phase 3: Contributor Onboarding
- [ ] Update README command count (actual from find command)
- [ ] Create DEVELOPMENT.md (local dev, test, lint, pre-commit)
- [ ] Create ARCHITECTURE.md (public module map)
- [ ] Add .github/ISSUE_TEMPLATE/{bug,feature,security}.md

## Phase 4: First Public Commit
- [ ] Stage all changes
- [ ] Commit with exact message from Section 8
- [ ] Tag v6.0.0-public-alpha
- [ ] Verify clone → mekong --help works in clean env
```

---

## 12. Appendix: OmniRoute Pattern Quick Reference

| Pattern | File in OmniRoute | Mekong Equivalent / Port Target |
|---------|-------------------|--------------------------------|
| Strategy Registry | `src/routing/strategies/` | `src/core/provider_registry.py` → add `RoutingStrategy` ABC |
| Auto-Combo Engine | `src/routing/auto_combo.py` | `src/core/tier_fallback_chain.py` (NEW) |
| Compression Pipeline | `src/compression/engines/` | `src/middleware/token_compression.py` (NEW, optional) |
| Circuit Breaker | `src/resilience/circuit_breaker.py` | `src/core/circuit_breaker.py` (EXTEND: tier-aware) |
| MCP Server | `src/mcp/server.ts` | `src/core/mcp_server.py` (CURATE: skill registry) |
| A2A Agent Card | `/.well-known/agent.json` | `src/api/gateway.py` endpoint (NEW) |
| CLI Namespaces | `src/cli/namespaces/` | `src/cli/app_setup.py` (ALREADY GOOD) |
| Setup Wizard | `src/cli/setup_wizard.ts` | `src/cli/setup_wizard.py` (NEW) |
| Decision Headers | Middleware `X-OmniRoute-Decision` | `src/middleware/license_gate.py` (ADD) |
| Zero-Config Defaults | `src/config/auto.ts` | `src/seed/config/auto_strategy.py` (NEW) |

---

*Advisory only — no code written. This report is the migration plan for the fullstack-developer agent.*