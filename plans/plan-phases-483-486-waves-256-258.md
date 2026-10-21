# Implementation Plan: Dual-Track Execution Phases 483-486 & Waves 256-258

## Track 1: Maritime Safety Phases 483-486 (`mekong-cli`)
- [x] Phase 483: `src/core/maritime/phase_483_stp_aeration_sludge_return.py` (IMO MEPC.227(64), DO >= 2.0 mg/L, blower failover < 30s)
- [x] Phase 484: `src/core/maritime/phase_484_bearing_mist_slowdown.py` (IACS UR M10/M3, crosshead >= 80°C, main bearing >= 78°C, L.O. inlet < 1.8 bar)
- [x] Phase 485: `src/core/maritime/phase_485_egb_circulation_dryrun.py` (IACS UR M14, pump dP >= 1.2 bar, loss trip < 15s)
- [x] Phase 486: `src/core/maritime/phase_486_emergency_gen_blackout.py` (SOLAS II-1/43, 8h day tank, auto-start <= 45s)
- [x] Coordinator: `src/core/maritime_safety_auxiliary_batch6_engine.py` (< 95 LOC)
- [x] CLI: `src/cli/commands/maritime_safety_auxiliary_batch6_command.py` (< 100 LOC) & register in `src/cli/app_setup.py`
- [x] Tests: `tests/test_maritime_phases_483_486_suite.py` (100% green pytest)

## Track 2: Quantitative Desk Models Waves 256-258 (`algo-trader`)
- [x] Wave 256: `src/desk/contdelarrard2013/` (Cont & de Larrard 2013 Markovian LOB queue depletion, < 100 LOC/file)
- [x] Wave 257: `src/desk/lehallemounjid2017/` (Lehalle & Mounjid 2017 optimal execution with adverse selection, < 100 LOC/file)
- [x] Wave 258: `src/desk/gueant2015multiasset/` (Guéant 2015 closed-form multi-asset cross-impact liquidation, < 100 LOC/file)
- [x] Barrel: Update `src/desk/index.ts`
- [x] Tests: `tests/unit/desk/waves_256_258_suite.test.ts` (100% green vitest)
