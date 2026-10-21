# Implementation Plan: Dual-Track Execution Phases 491-494 & Waves 262-264

## Track 1: Maritime Safety Automation Batch 8 (Phases 491-494) (`mekong-cli`)
- [x] Phase 491: ME Thrust Bearing Temperature & Oil Wedge Film Pressure Protection (`src/core/maritime/phase_491_thrust_bearing_pad_temp.py`)
  - IACS UR M3/M10 compliance.
  - White-metal pad temp trip: >= 85.0°C (alarm 80.0°C).
  - Hydrodynamic lubrication oil film differential pressure: >= 0.8 bar.
  - Standby booster lube oil pump cut-in: < 0.8 bar.
  - Shaft axial displacement limit: >= 1.2 mm trip.
- [x] Phase 492: Vacuum Sewage Collecting Tank & Ejector Discharge Control (`src/core/maritime/phase_492_vacuum_sewage_tank_ejector.py`)
  - MARPOL Annex IV compliance.
  - Vacuum holding range: -0.65 to -0.45 bar gauge (ejector cut-in at -0.45 bar, cut-out at -0.65 bar).
  - Vacuum loss emergency alarm: > -0.30 bar.
  - Collecting tank high level macerator pump cut-in: >= 80%.
  - High-high level overboard discharge lockout & toilet valve isolation: >= 95%.
- [x] Phase 493: Exhaust Gas Scrubbing Washwater Demister & SOx Quench Loop (`src/core/maritime/phase_493_exhaust_scrubber_washwater_demister.py`)
  - MARPOL Annex VI Regulation 14 compliance (SOx emissions & water quality MEPC.340(77)).
  - Washwater inlet pH monitoring: neutralization caustic soda dosing if pH < 6.5.
  - Demister differential pressure: dP >= 2.5 kPa triggers auto-wash spray cycle.
  - Quench gas inlet high temperature trip: >= 250.0°C initiates scrubber bypass flap opening to protect demister packs.
  - Washwater discharge turbidity limit: <= 25 FNU.
- [x] Phase 494: Bow Thruster Tunnel Hydraulic Pitch & Overload Power Management (`src/core/maritime/phase_494_bow_thruster_pitch_power.py`)
  - DNV Rules for Ships / IACS UR M65.
  - Electric drive motor load limit: > 105% FLA triggers auto-pitch reduction.
  - Hydraulic servo oil pressure: < 25.0 bar triggers pitch freeze/lock and emergency stop.
  - Header tank level: < 40% triggers low level alarm.
  - Tunnel hydraulic oil temp: > 70.0°C triggers cooling water valve boost.
- [x] Coordinator: `src/core/maritime_safety_auxiliary_batch8_engine.py` (< 95 LOC)
- [x] CLI: `src/cli/commands/maritime_safety_auxiliary_batch8_command.py` (< 100 LOC) & register in `src/cli/app_setup.py`
- [x] Tests: `tests/test_maritime_phases_491_494_suite.py` (100% green pytest)

## Track 2: Quantitative Desk Models Waves 262-264 (`algo-trader`)
- [x] Wave 262: Guéant (2015) Closed-Form Approximations in Optimal Liquidation (`src/desk/gueant2015closedform/`)
  - Closed-form asymptotic expansion for non-linear power impact cost $H(v) = \eta |v|^{1+\alpha}$.
  - Perturbation solution for optimal liquidation schedule without PDE discretization.
  - Strict < 100 LOC/file, pure TypeScript math, zero external dependencies.
- [x] Wave 263: Lòpez de Prado (2018) Fractionally Differentiated Features for Stationarity (`src/desk/lopezdeprado2018fracdiff/`)
  - Memory-preserving stationary time-series via fractional differentiation operator $(1-B)^d$.
  - Binomial series weight generation: $w_k = -w_{k-1} \frac{d - k + 1}{k}$ with weight cutoff threshold $\tau$.
  - Real-time rolling convolution conserving statistical memory while achieving stationarity (ADF test equivalence).
- [x] Wave 264: Almgren & Li (2016) Option Hedging with Market Impact & Transient Slippage (`src/desk/almgrenli2016option/`)
  - Dynamic delta replication under temporary impact $\eta v$ and permanent impact $\gamma v$.
  - Optimal trading speed balancing tracking error variance and price impact friction: $v_t^* = \frac{\Delta_{t} - q_t}{\tau_{hedge}}$.
  - Liquidation penalty terminal condition.
- [x] Barrel: Update `src/desk/index.ts`
- [x] Tests: `tests/unit/desk/waves_262_264_suite.test.ts` (100% green vitest)
