# Implementation Plan: Dual-Track Execution Phases 487-490 & Waves 259-261

## Track 1: Maritime Safety Phases 487-490 (`mekong-cli`)
- [x] Phase 487: `src/core/maritime/phase_487_jacket_cooling_temp_flow.py` (IACS UR M10/M3, HT outlet >= 92°C, flow dP < 0.6 bar, expansion tank < 30%)
- [x] Phase 488: `src/core/maritime/phase_488_deck_water_seal_level.py` (SOLAS II-2/4.5.5, water column < 450 mm, trace heating < 5°C, auto-refill)
- [x] Phase 489: `src/core/maritime/phase_489_central_cooling_3way_valve.py` (IACS UR M14, LT target 36°C, 3-way valve bypass split, seawater dP)
- [x] Phase 490: `src/core/maritime/phase_490_starting_air_compressor_unloader.py` (IACS UR M12, max 30 bar, relief 31.5 bar, stage temp > 160°C trip, purge)
- [x] Coordinator: `src/core/maritime_safety_auxiliary_batch7_engine.py` (< 95 LOC)
- [x] CLI: `src/cli/commands/maritime_safety_auxiliary_batch7_command.py` (< 100 LOC) & register in `src/cli/app_setup.py`
- [x] Tests: `tests/test_maritime_phases_487_490_suite.py` (100% green pytest)

## Track 2: Quantitative Desk Models Waves 259-261 (`algo-trader`)
- [x] Wave 259: `src/desk/alfonsischied2012/` (Alfonsi, Schied & Slynko 2012 resilient non-linear impact, < 100 LOC/file)
- [x] Wave 260: `src/desk/carteajaimungal2014alpha/` (Cartea, Jaimungal & Ricci 2014 alpha-driven market making, < 100 LOC/file)
- [x] Wave 261: `src/desk/gatheralschied2011kernel/` (Gatheral, Schied & Slynko 2011 exponential decay kernel, < 100 LOC/file)
- [x] Barrel: Update `src/desk/index.ts`
- [x] Tests: `tests/unit/desk/waves_259_261_suite.test.ts` (100% green vitest)
