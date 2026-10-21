# Implementation Plan: Maritime Phases 427–430 & Quantitative Desk Waves 214–216

**Target:** Zero mocks, strictly `< 180 LOC` per file, 100% green tests, bilingual CLI, and zero `:any` types.

## Track 1: Maritime Automation Phases 427–430 (mekong-cli)
- **Phase 427: ME Cylinder Lubrication Alpha Adaptive Feed Rate**:
  - `src/core/maritime/phase_427_cylinder_lubrication_alpha.py` (< 160 LOC)
  - Kinetics: Alpha ACC formula, BN neutralization, drain scrape-down Fe/BN analysis.
- **Phase 428: Selective Catalytic Reduction (SCR) Urea / DEF De-NOx Kinetics**:
  - `src/core/maritime/phase_428_scr_urea_denox.py` (< 160 LOC)
  - Kinetics: Thermolysis/hydrolysis, standard/fast SCR, ABS minimum operating temp ($300^\circ$C), ammonia slip.
- **Phase 429: Cargo Hold Bilge Suction Valve Interlock & Dewatering Eductor Sizing**:
  - `src/core/maritime/phase_429_cargo_hold_bilge_eductor.py` (< 160 LOC)
  - Hydraulics: SOLAS II-1 Reg 21 interlocks, WIDS level 1 & 2 alarms, jet venturi eductor dewatering.
- **Phase 430: Hull Impressed Current Anti-Fouling (ICAF) & Ultrasonic Bio-Fouling**:
  - `src/core/maritime/phase_430_hull_icaf_ultrasonic.py` (< 160 LOC)
  - Physics: Faraday's law Cu/Al electrolytic release, dual-frequency ultrasonic cavitation, biofouling risk index.
- **Master Engine Facade & CLI Wiring**:
  - `src/core/maritime_cyl_scr_bilge_icaf_engine.py` (< 120 LOC)
  - `src/cli/commands/maritime_cyl_scr_bilge_icaf_command.py` (< 150 LOC)
  - Register in `src/cli/app_setup.py` (8 bilingual sub-apps).
- **Unit & Integration Test Suite**:
  - `tests/test_maritime_phases_427_430_suite.py` (< 175 LOC, zero mocks, real physics).

## Track 2: Quantitative Desk Waves 214–216 (algo-trader)
- **Wave 214: Almgren-Thum-Hauptmann-Li (2005) Non-Linear Impact Square-Root Law**:
  - `src/desk/almgrenthum/`: `almgren-thum-types.ts`, `almgren-thum-math.ts`, `almgren-thum-engine.ts`, `index.ts`.
- **Wave 215: Gatheral (2010) No-Dynamic-Arbitrage Decay Kernels**:
  - `src/desk/gatheral/`: `gatheral-types.ts`, `gatheral-math.ts`, `gatheral-engine.ts`, `index.ts`.
- **Wave 216: Avellaneda-Lipkin (2003) Hard-to-Borrow Short Squeeze Dynamics**:
  - `src/desk/avellanedalipkin/`: `avellaneda-lipkin-types.ts`, `avellaneda-lipkin-math.ts`, `avellaneda-lipkin-engine.ts`, `index.ts`.
- **Exports & Unit Test Suite**:
  - Export all 3 waves in `src/desk/index.ts`.
  - `tests/unit/desk/waves_214_216_suite.test.ts` (< 175 LOC, zero mocks, zero `:any`).
  - Vitest + `npx tsc --noEmit` validation.

## Quality Gates & DoD
1. All files `< 180 LOC`.
2. 0 mocks, 0 fake data, 0 `:any`.
3. pytest 100% pass on mekong-cli (`python3 -m pytest tests/test_maritime_phases_427_430_suite.py`).
4. Vitest 100% pass on algo-trader (`npm test tests/unit/desk/waves_214_216_suite.test.ts`).
5. Memory record committed to memory index.
