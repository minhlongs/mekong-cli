# Dual-Track Plan: Maritime Auxiliary Automation Batch 19 (Phases 535–538) & Quantitative Desk Waves 298–300

**Date:** 2026-10-14
**Status:** Complete

## Brainstorm Contract (`/ak-brainstorm --deep`)
- **Outcome:** Deliver Maritime Auxiliary Automation Batch 19 (Phases 535–538) in `mekong-cli` and Quantitative Desk Models Waves 298–300 in `algo-trader`.
- **Constraints:** All code files strictly $< 85\text{ LOC}$, deterministic zero-mock verification, zero `:any` types in TypeScript, full bilingual CLI aliases (`maritime-aux19` / `phukienhanghai19`).
- **Non-goals:** Touching unrelated CLI funnels or external APIs.
- **Acceptance Criteria:** `pytest` 6/6 green for Batch 19 (`ruff` 0 errors) and `vitest` 3/3 green for Waves 298–300.

## Track 1: Maritime Auxiliary Automation Batch 19 (Phases 535–538, `mekong-cli`)

1. **Phase 535: Main Engine Exhaust Valve Hydraulic Actuator Air-Spring Pressure & Spindle Rotation Supervision (IACS UR M10 & MAN B&W / WinGD Rules)**
   - File: `src/core/maritime/phase_535_exhaust_valve_actuator_supervision.py`
   - Supervises exhaust valve air-spring closing pressure ($\ge 7.0\text{ bar}$ normal, $< 6.0\text{ bar}$ warning, $< 5.0\text{ bar}$ cylinder fuel cutout & engine slowdown to prevent piston-to-valve impact), hydraulic actuator oil leak drain rate ($> 1.5\text{ L/h}$ seal wear alarm), and wing-driven spindle rotation ($\ge 8.0\text{ RPM}$ at load; zero-rotation seizure alarm).

2. **Phase 536: Cargo Oil Pump Room Mechanical Ventilation, Bilge High-Level & Hydrocarbon Gas Interlock (SOLAS II-2 Reg 4.5.4 & IBC/IGC Code)**
   - File: `src/core/maritime/phase_536_cargo_pumproom_vent_gas_interlock.py`
   - Supervises tanker cargo pump room extraction ventilation ($\ge 20.0\text{ ACH}$ mandatory before lighting/pump start), hydrocarbon gas concentration ($\ge 10.0\%\text{ LEL}$ continuous alarm, $\ge 30.0\%\text{ LEL}$ automatic cargo oil pump trip), and pump bearings temperature ($\ge 80.0^\circ\text{C}$ trip) / bilge high level ($\ge 250.0\text{ mm}$ alarm).

3. **Phase 537: Hull Stress Monitoring System (HSMS) Still-Water & Wave-Induced Bending Moment & Slamming Alarm (IMO MSC/Circ.646, IACS UR S11 & DNV HMON)**
   - File: `src/core/maritime/phase_537_hull_stress_slamming_monitor.py`
   - Supervises deck long-base strain gauge bending stress against permissible SWBM/VWBM limits ($\ge 85.0\%$ warning, $\ge 100.0\%$ critical speed/course alteration alarm) and bow bottom slamming accelerometer frequency ($\ge 4\text{ slams/10 min}$ or $> 0.45\text{ g}$ bow impact acceleration triggering pitch/speed reduction guidance).

4. **Phase 538: Shipboard Helicopter Refueling (JP-5 / Jet A-1) Static Bonding, Filter-Separator Water coalescer & Dead-Man Nozzle Interlock (SOLAS II-2 Reg 18.7 & UK CAA CAP 437)**
   - File: `src/core/maritime/phase_538_helideck_jp5_refueling_interlock.py`
   - Enforces aircraft-to-deck static earthing continuity ($< 10.0\text{ }\Omega$), filter-water separator differential pressure ($\le 1.0\text{ bar}$) and free-water slug detection ($\ge 15.0\text{ ppm}$ solenoid shutoff), and pneumatic dead-man handle engagement before permitting JP-5 fuel dispensing.

5. **Coordinator, CLI & Tests**:
   - `src/core/maritime_safety_auxiliary_batch19_engine.py`
   - `src/cli/commands/maritime_safety_auxiliary_batch19_command.py` (`maritime-aux19` / `phukienhanghai19`)
   - Registration in `src/cli/app_setup.py`
   - `tests/test_maritime_phases_535_538_suite.py`

## Track 2: Quantitative Desk Models Waves 298–300 (`algo-trader`)

1. **Wave 298: Guéant, Lehalle & Fernandez-Tapia (2012) Optimal Portfolio Liquidation with Limit Orders (`src/desk/gueantlehalle2012limitliq/`)**
   - Computes optimal limit order posting offset $\delta^*(t, q)$ and expected fill probability when liquidating a single-asset position with exponential execution intensity and terminal market sweep penalty.

2. **Wave 299: Cartea & Jaimungal (2016) Incorporation of Order-Flow into Optimal Execution (`src/desk/carteajaimungal2016incorporating/`)**
   - Computes the order-flow-adjusted liquidation rate $v^*_t = v^{\text{AC}}_t + \psi_t \hat{\mu}_t$ combining the Almgren-Chriss deterministic schedule with net order flow co-impact $\hat{\mu}_t$.

3. **Wave 300: Gatheral & Keller-Ressel (2019) Affine Forward Variance & Rough Heston Characteristic Exponent (`src/desk/gatheralkellerressel2019affine/`)**
   - Evaluates the fractional Riccati step approximation and forward variance curve convolution $\xi_t(u)$ for affine rough volatility pricing.

4. **Barrel & Vitest Suite**:
   - Export in `src/desk/index.ts`
   - `tests/unit/desk/waves_298_300_suite.test.ts`
