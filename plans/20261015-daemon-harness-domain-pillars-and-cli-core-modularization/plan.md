# Plan: Daemon/Harness, Agents/Auth/DB/Governance & `mekong-cli-core` `< 200` LOC Modularization

## Context & Brainstorm Contract
- **Outcome:** Decompose all 23 Python files `>= 200` LOC in `src/daemon/` and `src/harness/`, all 29 Python files `>= 200` LOC in `src/agents/`, `src/auth/`, `src/db/`, and `src/governance/`, and all 35 production TypeScript files `>= 200` LOC in `packages/mekong-cli-core/src/` (plus all 18 files with `: any` / `as any` casts across `packages/mekong-cli-core/`) to strictly `< 200` LOC and zero `: any`.
- **Constraints:** Preserve 100% of existing exports, monkeypatch targets, and runtime behavior; keep every modified and created file strictly `< 200` LOC (`<= 185` LOC target); zero `: any` or `as any` in TypeScript.
- **Non-goals:** No changes to external API routes or CLI command names.
- **Acceptance Criteria:**
  1. Every `.py` file in `src/daemon/` and `src/harness/` is strictly `< 200` lines.
  2. Every `.py` file in `src/agents/`, `src/auth/`, `src/db/`, and `src/governance/` is strictly `< 200` lines.
  3. Every production `.ts` file in `packages/mekong-cli-core/src/` is strictly `< 200` lines, and zero `.ts` files in `packages/mekong-cli-core/` contain `: any` or `as any`.
  4. All `pytest`, `ruff check`, and Vitest suites pass 100%.

## Phases
- [x] **Phase 1 — `src/daemon/` & `src/harness/` `< 200` LOC Modularization (23 files)** (COMPLETE — 80 files across `src/daemon/` and `src/harness/`, max 185 LOC, 752/752 tests pass, 0 ruff errors)
- [x] **Phase 2 — `src/agents/`, `src/auth/`, `src/db/`, & `src/governance/` `< 200` LOC Modularization (29 files)** (COMPLETE — 87 files across all 4 directories, max 196 LOC, 1,295/1,295 tests pass, 0 ruff errors)
- [x] **Phase 3 — `packages/mekong-cli-core/src/` `< 200` LOC & Zero `:any` (35 files + 18 `:any` files)** (COMPLETE — 255 production `.ts` files `< 200` LOC, 0 `: any` across all 317 `.ts` files, 908/908 tests pass)
- [x] **Phase 4 — Verification (`pytest`, `ruff check`, `vitest`)** (COMPLETE)
