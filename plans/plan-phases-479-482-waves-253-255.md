# Implementation Plan: Dual-Track Execution Phases 479-482 & Waves 253-255

## Track 1: Maritime Safety Phases 479-482 (`mekong-cli`)
- [x] Phase 479: `src/core/maritime/phase_479_cargo_hold_bilge_eductor.py` (SOLAS XII/9, motive P >= 4.5 bar, deltaP >= 0.8 bar)
- [x] Phase 480: `src/core/maritime/phase_480_turbocharger_aux_blower.py` (IACS UR M9, scavenge cut-in < 0.85 bar, cut-out >= 1.15 bar, surge dP/dt <= -0.25 bar/s)
- [x] Phase 481: `src/core/maritime/phase_481_boiler_feedwater_deaerator.py` (IACS UR M14, conductivity <= 5 uS/cm alarm > 5 trip > 10, deaerator 0.20-0.45 bar)
- [x] Phase 482: `src/core/maritime/phase_482_steering_gear_phase_failure.py` (SOLAS II-1/29, level < 35% isolation, phase imbalance > 10%, standby start < 45s)
- [x] Coordinator: `src/core/maritime_safety_auxiliary_batch5_engine.py` (< 95 LOC)
- [x] CLI: `src/cli/commands/maritime_safety_auxiliary_batch5_command.py` (< 100 LOC) & register in `src/cli/app_setup.py`
- [x] Tests: `tests/test_maritime_phases_479_482_suite.py` (100% green pytest)

## Track 2: Quantitative Desk Models Waves 253-255 (`algo-trader`)
- [x] Wave 253: `src/desk/almgrenpowerlawv2/` (Almgren 2003 non-linear power-law execution, < 100 LOC/file)
- [x] Wave 254: `src/desk/gatheralschied2012/` (Gatheral, Schied & Slynko 2012 transient impact kernel & Cholesky no-arbitrage check, < 100 LOC/file)
- [x] Wave 255: `src/desk/avellanedagueantjump/` (Avellaneda-Stoikov / Guéant jump-diffusion market making, < 100 LOC/file)
- [x] Barrel: Update `src/desk/index.ts`
- [x] Tests: `tests/unit/desk/waves_253_255_suite.test.ts` (100% green vitest)
