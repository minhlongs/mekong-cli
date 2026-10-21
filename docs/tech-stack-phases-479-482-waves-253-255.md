# Technical Stack & Specification: Maritime Phases 479-482 & Desk Waves 253-255

## Track 1: Maritime Automation Safety (mekong-cli)
- **Runtime**: Python 3.9+ / Typer CLI / Rich / Pytest.
- **Architectural Rules**: Pure deterministic physics evaluation, zero mocks, frozen dataclasses, strictly < 120 LOC per module.
- **Modules**:
  1. `Phase 479`: Cargo Hold Bilge Ingress & Eductor Stripping (SOLAS XII/9, IACS UR S24).
  2. `Phase 480`: ME Turbocharger Auxiliary Blower & Surge Protection (IACS UR M9).
  3. `Phase 481`: Boiler Feedwater Salinity & Deaerator Steam Blanketing (IACS UR M14).
  4. `Phase 482`: Steering Gear Hydraulic Power Actuator Phase Failure & Dual Loop (SOLAS II-1/29).
  5. `Coordinator`: `MaritimeSafetyAuxiliaryBatch5Engine` & `maritime_aux5_app` CLI.

## Track 2: Quantitative Desk Models (algo-trader)
- **Runtime**: Node.js / TypeScript 5.x / Vitest.
- **Architectural Rules**: Zero `:any` types, zero external numerical dependencies, strictly deterministic mathematical algorithms, < 120 LOC per file.
- **Modules**:
  1. `Wave 253`: Almgren-Chriss (2000/2003) Non-Linear Power-Law Execution (`almgrenpowerlawv2`).
  2. `Wave 254`: Gatheral, Schied & Slynko (2012) Transient Kernel Decay & No-Dynamic-Arbitrage (`gatheralschied2012`).
  3. `Wave 255`: Avellaneda-Stoikov & Guéant (2017) Jump-Diffusion High-Frequency Market Making (`avellanedagueantjump`).
  4. `Desk Barrel & Tests`: Exports in `src/desk/index.ts`, unit suite in `tests/unit/desk/waves_253_255_suite.test.ts`.
