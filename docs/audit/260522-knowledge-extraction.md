# Knowledge Extraction — Mekong CLI v6.0.0

**Date:** 2026-05-22 | **Auditor:** Claude Opus 4.6 | **Confidence:** Varies (noted per finding)

---

## 1. Hidden Conventions

### 1.1 Command Discovery via YAML Frontmatter

All `.claude/commands/*.md` files use YAML frontmatter with fields: `description`, `allowed-tools`, `argument-hint`. The `src/core/command_loader.py` parses these at runtime. Convention: command filename = CLI command name. No registry file — discovery is filesystem-based.

**Confidence:** High — verified in command_loader.py.

### 1.2 Factory Contract Cascade

`factory/contracts/` contains 567 JSON files. Contracts reference other contracts via `$ref`-style links, forming a cascade hierarchy. The PEV task classifier uses these to route commands. Convention: contract name mirrors command name with `.json` extension.

**Confidence:** Medium — cascade mechanism inferred from file cross-references, not traced through execution.

### 1.3 Dual Namespace Convention

The repo maintains parallel AI configurations:
- `.claude/` — CC CLI consumer (Claude Code)
- `.agent/` — Gemini/Antigravity consumer

Convention: same capability exists in both but with different syntax. `.claude/commands/cook.md` and `.agent/skills/cook/SKILL.md` do equivalent things for different runtimes.

**Confidence:** High — verified both directories.

### 1.4 MCU Deduction Timing

Credits are deducted AFTER successful delivery, not before. This is a deliberate business decision (customer-friendly). Convention enforced in `src/core/mcu_billing.py` — the `deduct()` call is always inside the success path.

**Confidence:** High — verified in billing code.

### 1.5 VN Pilot Identity Pattern

Pilot users are identified by `MEKONG_USER_ID=opc_NNN_xxxxxx` env var. Format: `opc_` prefix + 3-digit sequence + underscore + 6-char random. Commands without this env var run in anonymous mode (events logged, no credit gate). This is by design for gradual adoption.

**Confidence:** High — documented in CLAUDE.md and verified in code.

### 1.6 Append-Only JSONL Pattern

All pilot data uses append-only JSONL files (`~/.mekong/*.jsonl`). No updates, no deletes. Latest state derived by replaying events. This is a deliberate choice for simplicity and auditability over database complexity.

**Confidence:** High — verified file patterns.

### 1.7 Fire-and-Forget Webhook Pattern

VietQR webhook and signup webhook both return 200 on application errors (not 4xx/5xx). This prevents bank/service retry-storms. Errors logged locally. Convention: webhook handlers are maximally tolerant of upstream quirks.

**Confidence:** High — documented in CLAUDE.md with explicit rationale.

### 1.8 Provider Fallback Chain Order

LLM client fallback order is deliberate: OpenRouter (aggregator, cheapest) → DashScope/Qwen (free tier) → DeepSeek (cheap) → Anthropic → OpenAI → Gemini → Ollama (local, zero cost) → Offline. Order optimizes for cost, not quality.

**Confidence:** High — verified in llm_client.py.

---

## 2. Implicit Patterns

### 2.1 "Phase" Architecture (Seed→Tree→Forest→Land)

The codebase follows a 4-phase evolution model:
- **Seed** (`seed/`): Standalone, stdlib-only, Ollama
- **Tree** (`src/`): Full Python backend with FastAPI
- **Forest** (`apps/` + `packages/`): TypeScript monorepo
- **Land** (production): Deployed infrastructure

This isn't enforced anywhere — it's a mental model reflected in docs and directory structure. New code should go in the appropriate phase.

**Confidence:** Medium — documented in strategy docs, not enforced.

### 2.2 6-Layer Business Hierarchy

Commands are organized into 6 layers: Studio (23), Founder (52), Business (71), Product (31), Engineering (66), Ops (41). This hierarchy determines MCU costs and feature gating. Higher layers = more expensive operations.

**Confidence:** High — verified in CLAUDE.md command tables.

### 2.3 LaunchDaemon Pattern for macOS

Production services on macOS use LaunchDaemons (plist files in `/Library/LaunchDaemons/`). Convention: `com.mekong.{service}.plist`. Env vars injected via EnvironmentVariables dict. Restart via `launchctl kickstart`.

**Confidence:** High — documented in CLAUDE.md.

### 2.4 "mekong-wrapper.sh" as Universal Entry

All CLI access goes through `scripts/mekong-wrapper.sh`. It handles provider routing (claude/gemini/qwen), permission flags, and working directory. Direct invocation of `claude` or `python3 src/main.py` bypasses this layer.

**Confidence:** High — verified in script.

---

## 3. Technical Debt

### 3.1 Coverage Exclusion List (CRITICAL)

`pyproject.toml` excludes from coverage: `raas/`, `main.py`, `nlp_commander.py`, `telegram_bot.py`, `memory_client.py`, `pages/`, `exceptions.py`, `binh_phap/`, `commands/`, `cli/`, `agi_loop.py`, `cc_spawner.py`, `llm_client.py`, `config.py`.

This means the most critical paths (LLM client, CLI commands, RaaS billing) have no coverage enforcement. The 6,160 collected tests likely cover utility functions, not business logic.

**Confidence:** High — verified in pyproject.toml.

### 3.2 RaaS Subsystem Size (20K LOC)

`src/raas/` is the largest subsystem at 20,034 LOC. This is a complete billing engine (credits, checkout, marketplace, webhooks, tenants, A/B testing) embedded inside the monorepo. It should arguably be its own service.

**Confidence:** High — LOC counted by scout.

### 3.3 Scaffold Apps (28+)

At least 28 of 38 apps in `apps/` are scaffolds or early-stage with minimal code. They consume monorepo resources (pnpm install, turbo build) without providing value. Examples: `crm`, `saas-dashboard`, `roi-calculator`, `raas-demo`, `starter-template`, `vibe-coding-cafe`.

**Confidence:** High — verified by checking package.json and src/ directories.

### 3.4 Scaffold Packages (20+)

Many packages in `packages/` are version `0.0.1` with minimal content: `vibe-agents`, `vibe-arbitrage-engine`, `vibe-embedded-finance`, `vibe-crm`, `vibe-money`, etc. They add noise to the dependency graph.

**Confidence:** High — verified version numbers.

### 3.5 Oversized Core Files

Several critical files exceed the 200-line guideline:
- `src/core/planner.py` — 667 lines
- `src/core/executor.py` — 445 lines
- `src/core/verifier.py` — 482 lines
- `src/core/orchestrator/` — 1,243 lines (split across files)

**Confidence:** High — LOC verified.

### 3.6 Dual Payment Provider Remnants

Despite the "ALL-IN POLAR.SH" rule, Stripe dependencies remain in `pyproject.toml` and `packages/vibe-stripe/`. The migration is incomplete.

**Confidence:** Medium — Stripe may be needed for specific use cases (Win House platform exception).

### 3.7 stale docs/system-architecture.md

Last updated 2026-04-16 (36 days ago). References "Phase 01-04" structure that predates current v6.0 organization. Several sections describe planned features as if complete.

**Confidence:** High — verified timestamp and content.

---

## 4. Dead Code Candidates

### 4.1 Legacy Apps

Apps that appear abandoned (no recent commits, minimal code):
- `apps/sa-dec-flower-hunt` — Event-specific app, likely past its date
- `apps/vibe-coding-cafe` — Concept project
- `apps/com-anh-duong-10x` — Customer-specific
- `apps/starter-template` — Template, not an app

**Confidence:** Medium — need git log to confirm last activity.

### 4.2 Legacy Scripts

`scripts/` contains 100+ scripts. At least 20+ appear to be legacy:
- M1 optimization scripts (may be outdated for current hardware)
- One-off migration scripts
- Duplicate functionality (multiple deploy scripts for same target)

**Confidence:** Low — scripts may be used infrequently but still needed.

### 4.3 Unused Packages

Several `vibe-*` packages at version 0.0.1 with no consumers in `apps/`:
- `vibe-arbitrage-engine`
- `vibe-embedded-finance`
- `vibe-money`

To confirm: `grep -r "vibe-arbitrage-engine" apps/ packages/` would reveal if consumed.

**Confidence:** Medium — need grep to verify zero consumers.

---

## 5. Duplicated Logic

### 5.1 Auth Implementations

Auth logic exists in at least 4 locations:
- `src/auth/` (Python, ~4,738 LOC)
- `src/middleware/auth_middleware.py`
- `packages/vibe-auth/`
- `packages/vibe-supabase/` (auth helpers)

Different auth patterns for Python backend vs TypeScript frontend vs edge workers.

**Confidence:** High — verified all 4 locations.

### 5.2 Billing Logic

Billing/payment logic in at least 3 locations:
- `src/core/mcu_billing.py` (Python MCU system)
- `src/raas/` (Python RaaS engine, 20K LOC)
- `packages/vibe-payment/` + `packages/vibe-stripe/` (TypeScript)

**Confidence:** High — verified all 3 locations.

### 5.3 Command Definitions

Commands defined in 3 formats:
- `.claude/commands/*.md` (342+ markdown files with YAML frontmatter)
- `factory/contracts/*.json` (567 JSON machine contracts)
- `src/commands/*.py` (Python implementations)

Sync between these three sources is manual.

**Confidence:** High — all three verified.

---

## 6. Risky Abstractions

### 6.1 LLM Client Provider Chain

The 10-provider fallback chain is complex. Each provider has different API formats, rate limits, and failure modes. The circuit breaker (3 failures → 15s cooldown) may not be sufficient for providers with different SLAs.

**Risk:** Provider-specific bugs masked by fallback. A subtle failure (e.g., wrong model response format) could cascade.

**Confidence:** Medium — architecture verified, failure modes theoretical.

### 6.2 PEV Engine Recursion

The orchestrator can recursively invoke PEV loops (plan → subtask → plan → sub-subtask). No explicit depth limit found in code review. Unbounded recursion could exhaust resources.

**Confidence:** Medium — need deeper code review of orchestrator loop control.

### 6.3 Factory Contract Cascade

567 contracts with cross-references create a dependency graph. A change to one contract could have cascading effects on routing. No validation tool found for contract graph integrity.

**Confidence:** Medium — cascade mechanism inferred, not fully traced.

---

## 7. Bottlenecks

### 7.1 Single Gateway Instance

`api.cashclaw.cc` appears to be a single FastAPI instance. All API traffic, webhooks, and pilot operations route through it. No load balancer or horizontal scaling evidence.

**Confidence:** Medium — no infra config found for scaling.

### 7.2 File-Based State

`~/.mekong/*.jsonl` files are the source of truth for pilot operations. No concurrent write protection. No backup mechanism. A corrupted JSONL file could lose pilot data.

**Confidence:** High — file-based pattern verified.

### 7.3 pnpm Install Time

58 packages + 38 apps in pnpm workspace. `pnpm install` and `turbo build` process all of them, including 28+ scaffolds. Build times are likely dominated by unused packages.

**Confidence:** Medium — not measured, inferred from package count.

---

## Unresolved Questions

1. Is there a max depth for PEV orchestrator recursion?
2. Are factory contracts auto-generated from commands, or manually maintained?
3. Which of the 58 packages are actually published to npm vs workspace-only?
4. Is `packages/cleo-new/` intentionally embedded or should it be extracted?
5. What's the relationship between `src/raas/` (Python) and `packages/raas-sdk/` (TypeScript)?
