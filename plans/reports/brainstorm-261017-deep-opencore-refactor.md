# Deep Refactor Brainstorm Contract (`--deep`)

**Date:** 2026-10-17 | **Workflow:** `/ak-bootstrap` → `/ak-brainstorm refactor --deep`  
**Target Repository:** `/Users/macbook/mekong-cli`  
**Scope:** DRY consolidation & LOC headroom refactoring across the Open-Core + SaaS monetization spine (`src/core/opencore/`, `src/cli/`, `src/api/`, `src/middleware/`, `src/raas/`)

---

## 1. Brainstorm Contract (4 Mandatory Fields)

- **Outcome:** Eliminate cross-layer logic duplication (`blueprint` synchronization audit duplicated across CLI and FastAPI) and establish $\ge 25\text{ LOC}$ safety headroom below the 185 LOC Open-Core ceiling across boundary-critical modules without altering public CLI flags, FastAPI routes, or core import neutrality.
- **Constraints:**
  1. Every touched module in Open-Core/CLI/API/RaaS scope must end strictly $\le 160\text{ LOC}$ (well below the 185 LOC test assertion in `test_idea_deep_opencore_brainstorm.py` and `test_company_blueprint_sync.py`).
  2. `src/core/` must remain 100% stdlib-pure and provider-neutral (`tests/test_core_boundary.py` must pass 100%).
  3. All existing public entrypoints (`mekong idea {run,brainstorm}`, `mekong opencore-saas {steps,audit,hygiene,blueprint,brainstorm}`, `GET /api/open-core/{status,brainstorm}`) and re-exports must remain 100% backward-compatible.
  4. Update existing files directly or extract focused helper modules only when required by the LOC gate (`development-rules.md`).
- **Non-Goals:**
  1. Do not refactor unrelated legacy domain engines (`src/core/mcp_server.py`, maritime/legal domain simulators) in the same wave.
  2. Do not change JSON response schemas, CLI argument signatures, or `.mekong/company.json` data structure.
  3. Do not introduce third-party libraries or database migrations.
- **Acceptance Criteria:**
  1. Single source of truth for 25-step blueprint synchronization in `src/core/opencore/` consumed by both `src/cli/commands/opencore_saas_restructuring_command.py` and `src/api/opencore_status_routes.py`.
  2. Boundary-critical files (`phase_560_opencore_saas_readiness_engine.py`, `idea_commands.py`, `auth_middleware.py`, `billing_engine.py`, `autopilot.py`) reduced to $\le 160\text{ LOC}$ each.
  3. `python3 -m pytest tests/test_idea_deep_opencore_brainstorm.py tests/test_company_blueprint_sync.py tests/test_opencore_saas_25_step_suite.py tests/test_core_boundary.py -v` passes 100%.
  4. `python3 -m ruff check` passes with 0 errors across all refactored files.

---

## 2. Live Codebase Evidence (Scout Findings)

1. **DRY Violation — Duplicated 25-Step Blueprint Audit:**
   - `src/cli/commands/opencore_saas_restructuring_command.py:93-130` (`check_blueprint`) and `src/api/opencore_status_routes.py:29-70` (`build_blueprint_audit`) duplicate the exact same 35-line file-reading, slug-matching, Tri-Layer `[Business]`/`[Agentic]`/`[Governance]` check, and `.mekong/company.json` `revenue_events` verification.
2. **Tight LOC Headroom on Open-Core Gate Modules ($\le 185\text{ LOC}$ ceiling):**
   - `src/cli/idea_commands.py`: **182 LOC** (only 3 lines of headroom before failing `test_loc_invariants_for_deep_brainstorm_modules`).
   - `src/core/opencore/phase_560_opencore_saas_readiness_engine.py`: **181 LOC** (only 4 lines of headroom before failing `test_blueprint_and_opencore_loc_invariants`).
3. **SaaS / Middleware Boundary Hotspots Approaching 200 LOC Ceiling:**
   - `src/middleware/auth_middleware.py`: **199 LOC** (1 line below the 200 LOC `development-rules.md` limit).
   - `src/raas/billing_engine.py`: **196 LOC** and `src/raas/autopilot.py`: **196 LOC** (4 lines below the 200 LOC limit, tested against $\le 195\text{ LOC}$ in `test_opencore_saas_25_step_suite.py`).

---

## 3. Viable Refactoring Approaches (YAGNI → KISS → DRY)

| Option | Scope & Mechanism | Pros | Cons | Verdict |
|---|---|---|---|---|
| **Option A (Recommended)** | **Targeted Open-Core Spine & SaaS Boundary Refactor (DRY + Headroom)**<br>1. Move `audit_blueprint(repo_root)` into `src/core/opencore/` so CLI (`opencore_saas_restructuring_command.py`) and API (`opencore_status_routes.py`) share one stdlib-pure implementation.<br>2. Trim/decompose `phase_560_opencore_saas_readiness_engine.py` (181→$\le 150$ LOC), `idea_commands.py` (182→$\le 150$ LOC), `auth_middleware.py` (199→$\le 155$ LOC), `billing_engine.py` (196→$\le 155$ LOC), and `autopilot.py` (196→$\le 155$ LOC). | Fixes the real DRY violation; creates $\ge 25\text{ LOC}$ safety margin on every Open-Core + SaaS gate module; zero blast radius on unrelated engines; fast deterministic test verification. | Scoped to the Open-Core/SaaS spine rather than all 553 legacy files in `src/`. | **RECOMMENDED** |
| **Option B** | **Minimal Open-Core-Only DRY Cleanup**<br>Consolidate `audit_blueprint` and compact `idea_commands.py` + `phase_560_opencore_saas_readiness_engine.py` only; leave `auth_middleware.py` (199 LOC) and `src/raas/*` (196 LOC) untouched. | Smallest diff (4 files). | Leaves `auth_middleware.py` at 199 LOC and `billing_engine.py`/`autopilot.py` at 196 LOC where a 2-line edit breaks the 195/200 LOC gate. | Runner-up |
| **Option C** | **Repo-Wide Monolith Sweep (All 553 files > 185 LOC)**<br>Attempt to split `src/core/mcp_server.py` (33,837 LOC) and 25+ domain engines in one pass. | Addresses legacy monoliths. | Violates YAGNI/KISS; massive blast radius across unrelated legal/maritime domains. | Rejected |

---

## 4. Handoff to `/ak:plan` & `/ak:cook`

- **Selected Direction:** **Option A (Targeted Open-Core Spine & SaaS Boundary Refactor)**.
- **Next Step:** Proceed to `/ak:plan` → `/ak:cook` → `/ak:test` to execute the 6-file DRY + LOC headroom refactor and verify 100% test pass rate.
- **Unresolved Questions:** None blocking Option A; whether to schedule a separate wave for `src/cli/commands/*_command.py` (>400 LOC domain CLI wrappers) can be decided after this spine refactor ships.
