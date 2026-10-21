# Dual-Track Plan: Maritime Auxiliary Automation Batch 21 (Phases 543–546) & Quantitative Desk Waves 304–306

**Date:** 2026-10-14
**Status:** Complete

## Brainstorm Contract (`/ak-brainstorm --deep`)
- **Outcome:** Deliver Maritime Auxiliary Automation Batch 21 (Phases 543–546) in `mekong-cli` and Quantitative Desk Models Waves 304–306 in `algo-trader`.
- **Constraints:** All code files strictly $< 85\text{ LOC}$, deterministic zero-mock verification, zero `:any` types in TypeScript, full bilingual CLI aliases (`maritime-aux21` / `phukienhanghai21`).
- **Non-goals:** Touching unrelated CLI funnels or external APIs.
- **Acceptance Criteria:** `pytest` 6/6 green for Batch 21 (`ruff` 0 errors) and `vitest` 3/3 green for Waves 304–306.

## Track 1: Maritime Auxiliary Automation Batch 21 (Phases 543–546, `mekong-cli`)
1. **Phase 543:** `src/core/maritime/phase_543_scr_urea_ammonia_slip_interlock.py`
2. **Phase 544:** `src/core/maritime/phase_544_cargo_tank_pv_breaker_mast_interlock.py`
3. **Phase 545:** `src/core/maritime/phase_545_azipod_slewing_seal_stator_interlock.py`
4. **Phase 546:** `src/core/maritime/phase_546_lng_esd_drybreak_erc_interlock.py`
5. **Coordinator, CLI & Tests:**
   - `src/core/maritime_safety_auxiliary_batch21_engine.py`
   - `src/cli/commands/maritime_safety_auxiliary_batch21_command.py` (`maritime-aux21` / `phukienhanghai21`)
   - Registration in `src/cli/app_setup.py`
   - `tests/test_maritime_phases_543_546_suite.py`

## Track 2: Quantitative Desk Models Waves 304–306 (`algo-trader`)
1. **Wave 304:** `src/desk/contkukanovstoikov2014deepofi/`
2. **Wave 305:** `src/desk/gueantlehalle2015targetpov/`
3. **Wave 306:** `src/desk/gatheraljaisson2018hawkes/`
4. **Barrel & Vitest Suite:**
   - Export in `src/desk/index.ts`
   - `tests/unit/desk/waves_304_306_suite.test.ts`
