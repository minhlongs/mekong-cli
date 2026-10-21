# Technical Stack & Specification: Maritime Phases 487-490 & Desk Waves 259-261

## Track 1: Maritime Automation Safety (mekong-cli)
- **Runtime**: Python 3.9+ / Typer CLI / Rich / Pytest.
- **Architectural Rules**: Pure deterministic physics evaluation, zero mocks, frozen dataclasses, strictly < 100 LOC per module.
- **Modules**:
  1. `Phase 487`: ME Cylinder Head Jacket Cooling Water High Temp & Low Flow Interlock (`phase_487_jacket_cooling_temp_flow.py`, IACS UR M10 & M3, outlet temp >= 92°C slowdown, low flow dP trip, expansion tank < 30% alarm).
  2. `Phase 488`: Deck Water Seal Dry-Run & Low Level Interlock (`phase_488_deck_water_seal_level.py`, SOLAS II-2/4.5.5, minimum water column H < 450 mm, auto-refill, trace heating < 5°C).
  3. `Phase 489`: Central Cooling Fresh Water High/Low-Temp 3-Way Thermostatic Valve Control (`phase_489_central_cooling_3way_valve.py`, IACS UR M14, LT target 36°C, HT jacket mixing bypass split, seawater cooling head dP).
  4. `Phase 490`: Main Starting Air Compressor Auto-Unloader & Safety Relief Valve Interlock (`phase_490_starting_air_compressor_unloader.py`, IACS UR M12, receiver max 30 bar, relief valve lift 31.5 bar, stage discharge temp > 160°C trip, condensate purge).
  5. `Coordinator & CLI`: `MaritimeSafetyAuxiliaryBatch7Engine` & `maritime_aux7_app` CLI registered under `maritime-aux7` and `phukienhanghai7`.

## Track 2: Quantitative Desk Models (algo-trader)
- **Runtime**: Node.js / TypeScript 5.x / Vitest.
- **Architectural Rules**: Zero `:any` types, zero external numerical dependencies, strictly deterministic mathematical algorithms, < 100 LOC per file.
- **Modules**:
  1. `Wave 259`: Alfonsi, Schied & Slynko (2012) Resilient Non-Linear Order Book Impact (`alfonsischied2012`, power-law shape function F(x), resilient recovery rate rho, non-linear price trajectory).
  2. `Wave 260`: Cartea, Jaimungal & Ricci (2014) Optimal Market Making with High-Frequency Alpha Signals (`carteajaimungal2014alpha`, short-term drift predictor alpha_t, reservation price skew, dynamic inventory penalty).
  3. `Wave 261`: Gatheral, Schied & Slynko (2011) Continuous-Time Exponential-Kernel Transient Impact (`gatheralschied2011kernel`, kernel G(t) = G_0 exp(-beta t), Fredholm equation, optimal deterministic execution schedule without price manipulation).
  4. `Desk Barrel & Tests`: Exports in `src/desk/index.ts`, unit suite in `tests/unit/desk/waves_259_261_suite.test.ts`.
