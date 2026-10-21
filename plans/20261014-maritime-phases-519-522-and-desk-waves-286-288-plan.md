# Dual-Track Plan: Maritime Auxiliary Automation Batch 15 (Phases 519–522) & Quantitative Desk Waves 286–288

**Date:** 2026-10-14
**Status:** In Progress

## Track 1: Maritime Auxiliary Automation Batch 15 (Phases 519–522, `mekong-cli`)

All modules strictly $< 85\text{ LOC}$, deterministic, zero mocks.

1. **Phase 519: Main Engine Turning Gear Engagement & Starting Air Safety Interlock (SOLAS II-1 Reg 27 & IACS UR M10)**
   - File: `src/core/maritime/phase_519_turning_gear_start_interlock.py`
   - Evaluates turning gear pinion proximity limit switch engagement (blocks main starting air distributor valve whenever engaged), indicator cock open verification during slow turning, and starting air automatic shut-off valve lock status during crankcase maintenance.

2. **Phase 520: Accommodation & Galley Grey Water Collecting Tank High-Level & H2S Ventilation Safety (MARPOL Annex IV & ISO 15749)**
   - File: `src/core/maritime/phase_520_grey_water_tank_ventilation.py`
   - Evaluates grey water tank level ($\ge 80.0\%$ standby macerator transfer pump cut-in, $\ge 92.0\%$ high-level overflow alarm), tank space hydrogen sulfide ($\text{H}_2\text{S} \ge 5.0\text{ ppm}$ warning, $\ge 10.0\text{ ppm}$ toxic gas lockdown & emergency extraction boost), and port-state zero-discharge overboard valve seal verification.

3. **Phase 521: Deck Crane Hydraulic Slewing & Hoisting Overload Moment Limiter (SOLAS II-1 Reg 3-13 & IACS UR A2 / ILO 152)**
   - File: `src/core/maritime/phase_521_deck_crane_overload_limiter.py`
   - Evaluates hoist hook load vs Safe Working Load ($\ge 100.0\%\text{ SWL}$ overload warning, $\ge 110.0\%\text{ SWL}$ hydraulic relief bypass & luffing/hoisting cutout), jib boom upper/lower limit switch stops, and loose-gear slack-wire drum anti-fouling trip.

4. **Phase 522: Engine Room Emergency Escape Trunk Pressurization & Lighting Continuity (SOLAS II-2 Reg 13.4.2 & FSS Code Ch. 13)**
   - File: `src/core/maritime/phase_522_escape_trunk_pressurization.py`
   - Evaluates vertical escape trunk positive overpressure differential ($\ge 20.0\text{ Pa}$ to prevent engine room smoke ingress, $\le 50.0\text{ Pa}$ so self-closing fire doors remain operable with $\le 100\text{ N}$ handle force), lower/upper self-closing fire door status, and 24V DC emergency battery luminaire continuity.

5. **Coordinator, CLI & Tests**:
   - `src/core/maritime_safety_auxiliary_batch15_engine.py`
   - `src/cli/commands/maritime_safety_auxiliary_batch15_command.py` (`maritime-aux15` / `phukienhanghai15`)
   - Registration in `src/cli/app_setup.py`
   - `tests/test_maritime_phases_519_522_suite.py`

## Track 2: Quantitative Desk Models Waves 286–288 (`algo-trader`)

All modules strictly $< 85\text{ LOC}$, zero `:any` types, pure TypeScript math.

1. **Wave 286: Obizhaeva & Wang (2013) Optimal Trading Strategy and Supply/Demand Dynamics (`src/desk/obizhaevawang2013supply/`)**
   - Computes the exact canonical Obizhaeva-Wang block-continuous-block schedule: initial impulse trade $X_0 = \frac{Q_0}{\rho T + 2}$, continuous interior rate $\nu_t = \frac{\rho Q_0}{\rho T + 2}$ matching exponential order book resilience $\rho$, and terminal impulse trade $X_T = X_0$, plus expected execution cost.

2. **Wave 287: Cartea, Jaimungal & Kinzebulatov (2016) Algorithmic Trading with Learning (`src/desk/carteajaimungal2016learning/`)**
   - Models Bayesian filter updating of an unobservable drift state $\mu_t$ from noisy price increments with posterior mean $\hat{\mu}_t$ and posterior variance $v_t = \frac{\sigma_\mu^2 v_0}{\sigma^2 + v_0 t}$, adjusting the Almgren-Chriss execution speed according to filtered drift and parameter uncertainty.

3. **Wave 288: Gatheral, Schied & Slynko (2012) Transient Linear Price Impact and Fredholm Integral Equations (`src/desk/gatheralschied2012fredholm/`)**
   - Solves the discretized Fredholm first-kind matrix system $\sum_{j=0}^{N} G(|t_i - t_j|) x_j = \lambda$ on a time grid for a general convex decay kernel $G(\tau)$ so that the marginal impact potential stays constant across the horizon, yielding a symmetric U-shaped trade vector.

4. **Barrel & Vitest Suite**:
   - Export in `src/desk/index.ts`
   - `tests/unit/desk/waves_286_288_suite.test.ts`
