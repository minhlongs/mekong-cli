# Project Changelog

## v6.3.0 — 2026-09-08

**Super Command #8 — Gap #4: Harness Verifier Merge + DAG Scheduler Swap:**

- `MekongCoreRuntimeImpl.verify()` now delegates to `RecipeVerifier` (was: thin
  `_evaluate_check` with only `exit_code` + `output_pattern`). Three helpers bridge
  the gap: `_ExecResultLike` (core `Result` → `ExecutionResult`-shaped object),
  `_criteria_to_verifier_dict` (core `CheckSpec` → verifier criteria-dict),
  `_report_to_verification` (`VerificationReport` → core `Verification`).
  Empty-criteria path falls back to legacy `Verification(passed=(result.error is None))`.
- `_run_goal` executes multi-step plans in topological (DAG) order via
  `_topological_task_order` (string-ID-keyed Kahn's algorithm, NOT `DAGScheduler`,
  which keys by int `order`). Fast path via `_plan_has_dependencies` preserves
  single-step `mekong run` behavior exactly.
- `verify()` injected via `__init__(verifier=None)` defaulting to
  `RecipeVerifier(strict_mode=True)`.
- **27 new tests** across 3 files:
  - `tests/test_runtime_verify_merge.py` — 14 tests (verifier delegation)
  - `tests/test_runtime_dag_order.py` — 8 tests (topological ordering)
  - `tests/test_runtime_multistep_cycle.py` — 5 E2E tests (full multi-step cycle)
- **Parity:** 8182 passed, 256 failed, 77 skipped. Baseline 277 failures → −21 net
  improvement; **0 new failures from SC8** (1 pre-existing `test_plugin_loading`,
  verified on base commit `8dcb6f759`).
- `ruff check` clean on changed files.
- Architecture doc refreshed to v0.2; gap #4 marked CLOSED in
  `docs/development-roadmap.md`.

## v6.2.0 — 2026-08-29

**Super Command #5 — Economic Bus + Capability Bus + Agent Registry (PR #11):**
- Clean `src/core/` ↔ `src/core/adapters/` boundary: no vendor SDK imports in core at module level
- Canonical `LLMProvider` port (`generate/stream/structured_output/tool_call/health`); two conformant providers
- YAML single-source agent registry (`agents/registry.yaml`); Python discovery + CLI are adapters
- Capability bus wired into `mekong run` (11 builtin capabilities, failure-tolerant)
- MCP→capability bridge (`mcp:<tool_name>` ids) via `McpCapabilityAdapter` + `ToolCapabilityAdapter`
- Scheme-agnostic economic bus: x402 + MPP providers, fail-closed config, no custody
- Canonical Buzz transport (hermetic-by-injection, fail-loud `BuzzConfigError` at call time)
- `CloudflareTransport(Protocol)` with `.dispatch(payload) -> dict`; single import site isolated
- Agent-loop E2E test driving the full GOAL→CONTEXT→PLAN→DELEGATE→EXECUTE→OBSERVE→VERIFY→REPAIR→REMEMBER→COMMIT lifecycle
- 54 files, +5,127 / −843 lines; Core DNA manifest bumped to v2026.08.29
- Quality gates green: ruff clean, pyright 0 new errors, parity gate EMPTY at 277 baseline
- Architecture doc refreshed to v0.2 (scores + next-actions reflect SC5 deliverables)

## v6.1.0 — 2026-08-23

**Design Intelligence (Hallmark deep integration):**
- New `src/design_intelligence/` package: Pydantic v2 schemas (DesignDNA 23 fields,
  DesignBrief, AuditReport, Theme), 58 gates (29 objective / 29 heuristic / 8 visual),
  9-axis scoring, archetype→macrostructure pipeline, provider-agnostic visual QA
- Knowledge base: 58 gates, 21 macrostructures, 12 themes, 4 genres, 16 archetypes
- New `mekong ui` sub-app: audit, study, redesign, build, approve, benchmark
- Three evidence tiers (objective/heuristic/opinion) and three visual-QA tiers
  (full/screenshot/static) kept strictly separate — never over-claimed
- Design memory: approved DNA / rejected patterns via MemoryStore `design:` namespace
  (Sophia contract); `study --export-json` emits parseable DesignDNA JSON
- Change detection + opt-in `mekong deploy --design-audit` advisory hook
  (frontend diffs suggest audit; backend/migration/CLI/infra-only skip)
- Anti-gaming benchmark: 10 fixtures, 7 derived metrics, good vs slop separation
- 140 design-intelligence tests; docs/design-intelligence.md

## v6.0.0 — 2026-08-16

**Highlights:**
- MIT license applied
- Python-only contributor workflow finalized
- 48 commands mapped in COMMAND_REGISTRY.md
- spec-kit SDD artifacts added (specs/, trace.rb, traceability.json)

**Repo parity fixes:**
- Release metadata synced to `minhlongs/mekong-cli`
- GitHub Actions PyPI-only publish path validated