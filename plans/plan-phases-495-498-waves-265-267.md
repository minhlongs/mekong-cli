# Implementation Plan: Dual-Track Execution Phases 495-498 & Waves 268-270

## Track 1: Maritime Safety Automation Batch 9 (Phases 495-498) (`mekong-cli`)
- [x] Phase 495: OWS 15 ppm Bilge Alarm & 3-Way Recirculation Valve Interlock (`src/core/maritime/phase_495_ows_15ppm_bilge_alarm.py`)
  - MARPOL Annex I Reg 14 & MEPC.107(49) compliance.
  - Oil content limit: > 15.0 ppm triggers immediate diversion valve to Bilge Holding Tank.
  - Sample water flow loss (< 0.5 L/min) or clean water flushing active triggers overboard lockout.
  - Special area zero-discharge geographic override.
- [x] Phase 496: Main Engine Crankcase Oil Mist Detector & Relief Valve Supervisory (`src/core/maritime/phase_496_crankcase_oil_mist_detector.py`)
  - IACS UR M10 & SOLAS Reg II-1/47 compliance.
  - Oil mist opacity: >= 1.0% obscuration (pre-alarm), >= 2.0% obscuration triggers automatic engine slowdown/stop.
  - Optical cell suction draft loss detection (fan differential pressure < 100 Pa).
  - Crankcase explosion relief valve flame arrester status check.
- [x] Phase 497: Auxiliary Boiler Water Level & Low-Water Fuel Oil Cutoff Interlock (`src/core/maritime/phase_497_boiler_water_level_fuel_cutoff.py`)
  - IACS UR M53 & ASME Section I Section C compliance.
  - Water level: normal band -50mm to +50mm; first low water alarm at -75mm.
  - Critical low-low water level at -120mm triggers instant burner safety shut-off valve trip & purge lockout.
  - Differential conductivity / electrode probe integrity fail-safe trip.
- [x] Phase 498: Emergency Fire Pump Sea Chest Suction & Priming Pressure Interlock (`src/core/maritime/phase_498_emergency_fire_pump_priming.py`)
  - SOLAS Reg II-2/10 & IACS UR F35 compliance.
  - Sea chest suction valve open interlock & suction lift vacuum monitoring (<= -0.40 bar).
  - Priming unit timer: if discharge pressure < 1.5 bar within 30.0s, activates standby priming ejector and triggers priming fault alarm.
  - Minimum fire main pressure delivery (>= 2.7 bar at highest hydrants).
- [x] Coordinator: `src/core/maritime_safety_auxiliary_batch9_engine.py` (< 95 LOC)
- [x] CLI: `src/cli/commands/maritime_safety_auxiliary_batch9_command.py` (< 100 LOC) & register in `src/cli/app_setup.py`
- [x] Tests: `tests/test_maritime_phases_495_498_suite.py` (100% green pytest)

## Track 2: Quantitative Desk Models Waves 268-270 (`algo-trader`)
- [x] Wave 268: Lehalle & Neuman (2019) Limit Order Book Queue-Reactive Liquidation (`src/desk/lehalleneuman2019queuereactive/`)
  - Queue-depletion Markovian state tracking $(q_t^a, q_t^b)$.
  - Dynamic switching between passive limit order placement and aggressive market order execution.
  - Optimal threshold distance and fill probability based on queue depth.
  - Strict < 100 LOC/file, pure TypeScript math, zero external dependencies.
- [x] Wave 269: Cartea & Jaimungal (2017) Ambiguity-Averse Market Making (`src/desk/carteajaimungal2017ambiguity/`)
  - Robust Knightian uncertainty / relative entropy penalty $\theta > 0$.
  - Worst-case drift adjustment shifting optimal bid-ask quotes under model misspecification: $\delta_a^* = \delta_a^{neutral} + \frac{1}{\theta} \log(1 + \frac{\theta q \sigma^2}{2 \kappa})$.
  - Strict < 100 LOC/file, pure TypeScript math, zero external dependencies.
- [x] Wave 270: Gatheral & Schied (2013) Fractional Brownian Motion & Rough Path Optimal Liquidation (`src/desk/gatheralschied2013rough/`)
  - Power-law memory kernel $K(t - s) = (t - s)^{H - 1/2}$ with Hurst parameter $H \in (0, 0.5)$.
  - Transient price impact execution without arbitrage or price manipulation.
  - Optimal liquidation trajectory discretization.
  - Strict < 100 LOC/file, pure TypeScript math, zero external dependencies.
- [x] Barrel: Update `src/desk/index.ts`
- [x] Tests: `tests/unit/desk/waves_268_270_suite.test.ts` (100% green vitest)
