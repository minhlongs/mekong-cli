# Technical Stack & Specification: Maritime Phases 483-486 & Desk Waves 256-258

## Track 1: Maritime Automation Safety (mekong-cli)
- **Runtime**: Python 3.9+ / Typer CLI / Rich / Pytest.
- **Architectural Rules**: Pure deterministic physics evaluation, zero mocks, frozen dataclasses, strictly < 120 LOC per module.
- **Modules**:
  1. `Phase 483`: STP Bio-Media Aeration & Sludge Return Interlock (`phase_483_stp_aeration_sludge_return.py`, IMO MEPC.227(64), DO >= 2.0 mg/L, blower failover < 30s).
  2. `Phase 484`: ME Crosshead & Main Bearing Mist / Temperature Slowdown (`phase_484_bearing_mist_slowdown.py`, IACS UR M10 & M3, crosshead >= 80°C, main bearing >= 78°C, L.O. inlet < 1.8 bar).
  3. `Phase 485`: Exhaust Gas Boiler Circulation & Dry-Run Interlock (`phase_485_egb_circulation_dryrun.py`, IACS UR M14 & ASME Sec I, dP >= 1.2 bar, loss trip < 15s).
  4. `Phase 486`: Emergency Generator Day Tank & Blackout Interlock (`phase_486_emergency_gen_blackout.py`, SOLAS II-1/43, 8h day tank, auto-start <= 45s).
  5. `Coordinator & CLI`: `MaritimeSafetyAuxiliaryBatch6Engine` & `maritime_aux6_app` CLI.

## Track 2: Quantitative Desk Models (algo-trader)
- **Runtime**: Node.js / TypeScript 5.x / Vitest.
- **Architectural Rules**: Zero `:any` types, zero external numerical dependencies, strictly deterministic mathematical algorithms, < 120 LOC per file.
- **Modules**:
  1. `Wave 256`: Cont & de Larrard (2013) Markovian LOB Queue Depletion (`contdelarrard2013`).
  2. `Wave 257`: Lehalle & Mounjid (2017) Optimal Execution with Adverse Selection (`lehallemounjid2017`).
  3. `Wave 258`: Guéant (2015) Closed-Form Multi-Asset Liquidation with Cross-Impact (`gueant2015multiasset`).
  4. `Desk Barrel & Tests`: Exports in `src/desk/index.ts`, unit suite in `tests/unit/desk/waves_256_258_suite.test.ts`.
