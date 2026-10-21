# Implementation Plan - Maritime Phases 419-422 & Desk Waves 208-210

## Overview
Implement Maritime Automation Phases 419–422 (EGR Bleed-off WTS, Shaft Gen AFE THD, BWMS Chlorination, Stern Thruster CPP Cavitation) and Quantitative Desk Waves 208–210 (Realized Semivariance, Realized Beta, VIX Uncertainty/Risk Aversion Decomposition).

## Strict Engineering Constraints
- All Python files < 200 LOC, all TypeScript files < 180 LOC.
- Zero mock dependencies; physical & econometric formulas only.
- Zero `:any` types in TypeScript.
- 100% test pass rate with pytest and vitest.

## Phase Breakdown

### Track 1: Maritime Automation (Phases 419–422 in mekong-cli)
- **Phase 419 Engine**: `src/core/maritime/phase_419_egr_bleedoff_water_treatment.py`
  - MEPC.307(73) & MARPOL Annex VI Tier III criteria: Oil < 15 ppm, Turbidity < 25 FNU, pH >= 6.5.
  - Fail-safe 3-way divert valve logic.
- **Phase 420 Engine**: `src/core/maritime/phase_420_shaft_generator_afe_harmonics.py`
  - IACS UR E24 & IEEE 519: THD_V <= 5.0%, individual harmonics <= 3.0%.
  - Reverse power detection & GFRT ride-through.
- **Phase 421 Engine**: `src/core/maritime/phase_421_bwms_chlorination_neutralization.py`
  - IMO BWM D-2 & USCG Phase-II: TRO 1.5-2.0 mg/L ballasting, discharge <= 0.10 mg/L.
  - Hydrogen degassing interlock (< 1.0% vol).
- **Phase 422 Engine**: `src/core/maritime/phase_422_stern_thruster_cavitation_pitch.py`
  - DNV Pt.4 Ch.5 & ITTC: Cavitation index sigma, threshold 0.85.
  - High-frequency acoustic sensors (10-40 kHz) & CPP derate.
- **Facade & Orchestrator**: `src/core/maritime_egr_afe_bwms_thruster_engine.py`
- **Typer CLI & Commands**: `src/cli/commands/maritime_egr_afe_bwms_thruster_command.py`
- **App Wiring & FastMCP**: `src/cli/app_setup.py`, `scripts/mcp_server.py`
- **Unit & Integration Tests**: `tests/test_maritime_phases_419_422.py`

### Track 2: Quantitative Desk (Waves 208–210 in algo-trader)
- **Wave 208 (Semivariance)**: `src/desk/semivariance/` (Types, Math, Engine, Index).
  - Barndorff-Nielsen et al. (2010): RS+, RS-, Signed Jumps.
- **Wave 209 (Realized Beta)**: `src/desk/realizedbeta/` (Types, Math, Engine, Index).
  - Andersen et al. (2006): Realized beta, continuous vs jump beta via BCOV.
- **Wave 210 (Bekaert VIX Decomposition)**: `src/desk/bekaert/` (Types, Math, Engine, Index).
  - Bekaert et al. (2013): VIX^2 = E[RV] + VRP decomposition into uncertainty & risk aversion.
- **Desk Barrel Export**: `src/desk/index.ts`
- **Zero-Mock Vitest Suite**: `tests/unit/desk/waves_208_210_suite.test.ts`
