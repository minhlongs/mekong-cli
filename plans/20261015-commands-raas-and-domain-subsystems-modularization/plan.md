# Plan: Commands, RaaS Engine & 15 Supporting Domain Subsystems `< 200` LOC Modularization

## Context & Brainstorm Contract
- **Outcome:** Decompose all 31 Python files `>= 200` LOC in `src/commands/`, `src/command_fabric/`, and `src/design_intelligence/`, all 41 Python files `>= 200` LOC in `src/raas/`, and all 49 Python files `>= 200` LOC across 15 domain directories (`src/mekong/`, `src/polymarket/`, `src/lib/`, `src/graph/`, `src/usage/`, `src/models/`, `src/providers/`, `src/jobs/`, `src/learning/`, `src/plugins/`, `src/analytics/`, `src/telemetry/`, `src/security/`, `src/studio/`, `src/ai/`) to strictly `< 200` LOC (`<= 185` LOC target).
- **Constraints:** Preserve 100% of existing exports, Typer command registrations, monkeypatch targets, and runtime behavior; keep every modified and created file strictly `< 200` LOC (`<= 185` LOC target).
- **Non-goals:** No changes to external API routes or CLI command names.
- **Acceptance Criteria:**
  1. Every `.py` file in `src/commands/`, `src/command_fabric/`, and `src/design_intelligence/` is strictly `< 200` lines.
  2. Every `.py` file in `src/raas/` is strictly `< 200` lines.
  3. Every `.py` file across the 15 domain directories (`src/mekong/`, `src/polymarket/`, `src/lib/`, `src/graph/`, `src/usage/`, `src/models/`, `src/providers/`, `src/jobs/`, `src/learning/`, `src/plugins/`, `src/analytics/`, `src/telemetry/`, `src/security/`, `src/studio/`, `src/ai/`) is strictly `< 200` lines.
  4. All `pytest` and `ruff check` suites pass 100%.

## Phases
- [x] **Phase 1 — `src/commands/`, `src/command_fabric/`, & `src/design_intelligence/` `< 200` LOC Modularization (31 files)** (COMPLETE — all files <= 185 LOC, 0 ruff errors)
- [x] **Phase 2 — `src/raas/` `< 200` LOC Modularization (41 files)** (COMPLETE — all files <= 185 LOC, 0 ruff errors)
- [x] **Phase 3 — 15 Domain Subsystems `< 200` LOC Modularization (49 files)** (COMPLETE — all files <= 185 LOC across `src/mekong/`, `src/polymarket/`, `src/lib/`, `src/graph/`, `src/usage/`, `src/models/`, `src/providers/`, `src/jobs/`, `src/learning/`, `src/plugins/`, `src/analytics/`, `src/telemetry/`, `src/security/`, `src/studio/`, `src/ai/`)
- [x] **Phase 4 — Verification (`pytest`, `ruff check`)** (COMPLETE — 752 Python files verified < 200 LOC, test_pilot_modified_files_under_200_loc passes, 0 ruff errors)

