# Deep Brainstorming & Architecture Report: Maritime Phases 483–486 & Quantitative Waves 256–258

**Date:** 2026-10-12  
**Focus Tracks:**
- **Track 1 (Maritime Automation / Mekong CLI):** STP Aeration & Air-Lift Sludge Return, Main Engine Bearing Mist Slowdown Protection, Exhaust Gas Boiler (EGB) Forced Circulation Dry-Run Interlock, and Emergency Diesel Generator Blackout Auto-Start & Fuel Day Tank Safety.
- **Track 2 (Quantitative Desk / Algo Trader):** Cont & de Larrard (2013) Markovian LOB Queue Depletion, Lehalle & Mounjid (2017) Optimal Limit Order Execution with Adverse Selection, and Guéant (2015) Closed-Form Multi-Asset Cross-Impact Liquidation.

**Regulatory Doctrines & Mathematical Standards:**
- IMO Res. MEPC.227(64), MARPOL Annex IV, IACS UR M10, IACS UR M3, SOLAS II-1 Reg 31, SOLAS II-1 Reg 43, IACS UR M14, IACS UR M51.
- Microstructure & Stochastic Optimal Control: Cont & de Larrard (2013), Lehalle & Mounjid (2017), Guéant (2015).

---

## Executive Summary & Architectural Overview

This engineering blueprint defines the specifications, deterministic physics models, statutory limits, data contracts, and zero-mock verification gates for:
1. **Maritime Automation Phases 483–486 (`mekong-cli`)**: Extending the autonomous shipboard machinery safety framework to wastewater aerobic treatment, main bearing thermal/optical blowout protection, exhaust economizer forced circulation safeguards, and SOLAS blackout emergency generation.
2. **Quantitative Desk Models Waves 256–258 (`algo-trader`)**: Implementing queue-reactive high-frequency execution, microstructural adverse selection mitigation, and multi-asset cross-impact matrix liquidation.

Both tracks strictly adhere to:
- Individual code files $< 100\text{ LOC}$ (modularized, self-documenting kebab-case).
- Zero mock objects (`unittest.mock` / fake timers prohibited).
- Deterministic mathematical models and analytical closed-form solutions.
- 100% test coverage with green passes under `pytest` and `vitest`.
- Zero `:any` types in TypeScript and strict typing in Python 3.12+.

---

## Part 1: Track 1 — Maritime Automation Phases 483–486 (`mekong-cli`)

### Phase 483: Sewage Treatment Plant (STP) Aeration Tank Dissolved Oxygen & Air-Lift Sludge Return Engine
1. **Statutory Standards & Biological Wastewater Kinetics:**
   - Complies with **IMO Resolution MEPC.227(64)** and **MARPOL Annex IV**.
   - Marine biological Sewage Treatment Plants utilize aerobic digestion with suspended biomass (activated sludge) in an aeration chamber followed by secondary clarification.
   - **Dissolved Oxygen (DO) Balance:**
     - Nitrification and aerobic digestion require continuous oxygenation:
       $$\frac{d[\text{DO}]}{dt} = K_L a \cdot ([\text{DO}]_{\text{sat}} - [\text{DO}]) - \text{OUR}_{\text{biomass}}$$
       where $K_L a$ is the volumetric oxygen transfer coefficient and $\text{OUR}$ is oxygen uptake rate.
     - Operational envelopes:
       - Nominal healthy aeration: $\text{DO} \ge 2.0\text{ mg/L}$.
       - Sub-optimal warning: $1.0\text{ mg/L} \le \text{DO} < 2.0\text{ mg/L}$.
       - Anaerobic septic trip: $\text{DO} < 1.0\text{ mg/L}$ (causes $\text{H}_2\text{S}$ formation, odor, and biomass die-off).
   - **Aeration Blower & Standby Failover:**
     - Duty blower discharge pressure: $0.20\text{ to }0.50\text{ bar}$.
     - Loss of aeration pressure ($P_{\text{blower}} < 0.15\text{ bar}$) or blower trip commands automatic cut-in of standby blower within $\le 30.0\text{ seconds}$.
   - **Air-Lift Sludge Return:**
     - Settled activated sludge is airlifted from the clarifier hopper back to the aeration compartment. Minimum required recirculation flow: $Q_{\text{sludge}} \ge 15.0\text{ L/min}$. Loss of sludge return flow flags sedimentation blockage.

2. **Telemetry & Assessment Contract:**
   - Module: `src/core/maritime/phase_483_stp_aeration_sludge_return.py` (< 100 LOC)
   - Status Enum: `StpAerationStatus` (`NORMAL`, `LOW_DO_WARNING`, `SEPTIC_ALARM_STANDBY_START`, `BLOWER_PRESSURE_LOST`, `SLUDGE_RECIRC_FAILURE`).
   - Telemetry Dataclass:
     ```python
     @dataclass(frozen=True)
     class StpAerationTelemetry:
         dissolved_oxygen_mg_l: float
         aeration_pressure_bar: float
         blower_running: bool
         standby_blower_ready: bool
         airlift_sludge_flow_l_min: float
         blower_failover_elapsed_s: float
     ```
   - Assessment Dataclass:
     ```python
     @dataclass(frozen=True)
     class StpAerationAssessment:
         status: StpAerationStatus
         standby_blower_start_command: bool
         sludge_recirculation_ok: bool
         aerobic_treatment_healthy: bool
         remarks: str
     ```

---

### Phase 484: Main Engine Bearing Temperature & Optical Oil Mist Slowdown Protection Engine
1. **Physical Failure Modes & Safety Doctrine:**
   - Complies with **IACS UR M10 & M3**, **SOLAS II-1 Reg 31**.
   - Mechanical friction in two-stroke crosshead, crankpin, or main journal bearings produces localized hotspots ($T > 180^\circ\text{C}$), vaporizing lube oil into explosive sub-micron aerosol droplets (crankcase oil mist).
   - **Thermal Monitoring Envelopes:**
     - Normal bearing temp: $\le 72.0^\circ\text{C}$.
     - Crosshead bearing alert: $\ge 80.0^\circ\text{C}$ (trip / slowdown $\ge 85.0^\circ\text{C}$).
     - Main journal bearing alert: $\ge 78.0^\circ\text{C}$ (trip / slowdown $\ge 82.0^\circ\text{C}$).
     - Inter-bearing temperature spread: $\Delta T_{\text{bearing}} = T_{\text{max}} - T_{\text{avg}} \ge 12.0^\circ\text{C}$ indicates localized wiping.
   - **Crankcase Optical Oil Mist Detection:**
     - Optical absorption density: Normal $< 1.0\%\text{ LEL}$.
     - Mist pre-alarm: $\ge 1.5\%\text{ LEL}$.
     - Automatic engine slowdown: $\ge 2.5\%\text{ LEL}$ (limits engine RPM / fuel rack to $< 40\%$) to prevent catastrophic crankcase explosion.
   - **Lube Oil Inlet Pressure:**
     - Main lube oil header pressure: Normal $\ge 2.0\text{ bar}$. Low lube oil alarm: $< 1.8\text{ bar}$. Emergency slowdown: $< 1.5\text{ bar}$.

2. **Telemetry & Assessment Contract:**
   - Module: `src/core/maritime/phase_484_bearing_mist_slowdown.py` (< 100 LOC)
   - Status Enum: `BearingMistStatus` (`NORMAL`, `BEARING_HIGH_TEMP_ALERT`, `OIL_MIST_PRE_ALARM`, `EMERGENCY_SLOWDOWN_TRIP`, `LUBE_OIL_PRESSURE_CRITICAL`).
   - Telemetry Dataclass:
     ```python
     @dataclass(frozen=True)
     class BearingMistSlowdownTelemetry:
         max_crosshead_temp_c: float
         max_main_bearing_temp_c: float
         bearing_delta_t_c: float
         crankcase_oil_mist_pct_lel: float
         lube_oil_inlet_p_bar: float
         engine_load_pct: float
     ```
   - Assessment Dataclass:
     ```python
     @dataclass(frozen=True)
     class BearingMistSlowdownAssessment:
         status: BearingMistStatus
         slowdown_command: bool
         crankcase_explosion_risk: bool
         lube_oil_pressure_ok: bool
         remarks: str
     ```

---

### Phase 485: Exhaust Gas Boiler (EGB) Forced Circulation Pump & Dry-Run Interlock Engine
1. **Thermal Hydraulics & Protection Criteria:**
   - Complies with **IACS UR M14** and **ASME Section I**.
   - Exhaust gas economizers capture waste heat from main engine exhaust ($280 - 360^\circ\text{C}$). To prevent nucleate boiling burnout, dry running, and soot fire deflagrations, water must be forcibly circulated through tube bundles at a rate $2.5\times$ steam evaporation.
   - **Circulation Pump Differential Pressure:**
     - Differential pressure across circulating pump: $\Delta P = P_{\text{dis}} - P_{\text{suct}} \ge 1.2\text{ bar}$.
     - Low circulation threshold: $\Delta P < 0.8\text{ bar}$ indicates pump vapor cavitation or impeller loss.
   - **Automatic Standby Takeover & Diverter Damper Trip:**
     - Upon loss of differential pressure, standby circulation pump auto-starts.
     - If differential pressure remains $< 0.8\text{ bar}$ for $> 15.0\text{ seconds}$ (dry-run condition), the safety system must immediately trip the exhaust gas divert bypass damper (exhaust directed straight up funnel bypassing economizer) to prevent tube bundle meltdown.
   - **Subcooling / Vapor-Lock Margin:**
     - Water inlet temperature must remain below saturation: $T_{\text{inlet}} \le T_{\text{sat}} - 8.0^\circ\text{C}$ to avoid steam binding in pump suction.

2. **Telemetry & Assessment Contract:**
   - Module: `src/core/maritime/phase_485_egb_circulation_dryrun.py` (< 100 LOC)
   - Status Enum: `EgbCirculationStatus` (`NORMAL`, `STANDBY_PUMP_CUT_IN`, `DRY_RUN_DAMPER_BYPASS_TRIP`, `PUMP_CAVITATION_WARNING`, `VAPOR_LOCK_RISK`).
   - Telemetry Dataclass:
     ```python
     @dataclass(frozen=True)
     class EgbCirculationTelemetry:
         pump_diff_pressure_bar: float
         water_flow_m3_h: float
         standby_pump_available: bool
         loss_of_flow_duration_s: float
         exhaust_gas_inlet_temp_c: float
         economizer_inlet_temp_c: float
         tsat_c: float
     ```
   - Assessment Dataclass:
     ```python
     @dataclass(frozen=True)
     class EgbCirculationAssessment:
         status: EgbCirculationStatus
         standby_pump_start_command: bool
         exhaust_diverter_bypass_trip: bool
         circulation_adequate: bool
         remarks: str
     ```

---

### Phase 486: Emergency Diesel Generator (EDG) Blackout Auto-Start & Fuel Day Tank Interlock Engine
1. **Statutory Standards & Electrical Blackout Restoration:**
   - Complies with **SOLAS II-1 Reg 43** and **IACS UR M51 / ClassNK Pt.D**.
   - Under dead ship / total blackout conditions (main bus voltage drop $< 20\%$ for $> 0.5\text{ s}$), the Emergency Diesel Generator must start autonomously from cold condition without external power.
   - **Restoration Time Limit:**
     - Under SOLAS II-1/43, emergency generator must start, stabilize at rated speed and voltage ($440\text{ V} \pm 2.5\%$, $60\text{ Hz} \pm 1.0\%$), and close the emergency switchboard breaker within $\le 45.0\text{ seconds}$ (typical target $\le 30.0\text{ s}$).
   - **Dedicated Fuel Oil Day Tank Interlock:**
     - Gravity-fed emergency fuel day tank must contain sufficient fuel for $\ge 8\text{ hours}$ continuous operation under MCR.
     - Tank level thresholds:
       - Nominal: $\ge 60\%$.
       - Low level alarm: $< 40\%$ (less than 8h endurance remaining).
       - Critical shutdown inhibit / low fuel trip: $< 15\%$.
   - **Starting Battery / Compressed Air Reserves:**
     - Must possess energy for $\ge 3$ consecutive cold start attempts. If attempts reach 0 without start, flag `CRANK_FAILURE_LOCKOUT`.

2. **Telemetry & Assessment Contract:**
   - Module: `src/core/maritime/phase_486_emergency_gen_blackout.py` (< 100 LOC)
   - Status Enum: `EmergencyGenStatus` (`NORMAL`, `BLACKOUT_CRANKING_ACTIVE`, `EMERGENCY_POWER_CONNECTED`, `TAKEOVER_TIME_EXCEEDED`, `FUEL_RESERVE_DEPLETED`, `CRANK_FAILURE_LOCKOUT`).
   - Telemetry Dataclass:
     ```python
     @dataclass(frozen=True)
     class EmergencyGenTelemetry:
         main_bus_voltage_pct: float
         edg_frequency_hz: float
         edg_voltage_v: float
         blackout_elapsed_s: float
         fuel_day_tank_level_pct: float
         start_attempts_remaining: int
         breaker_closed: bool
     ```
   - Assessment Dataclass:
     ```python
     @dataclass(frozen=True)
     class EmergencyGenAssessment:
         status: EmergencyGenStatus
         crank_start_command: bool
         breaker_close_permissive: bool
         emergency_power_restored: bool
         fuel_endurance_ok: bool
         remarks: str
     ```

---

### Batch 6 Coordinator & CLI Command Group
1. **Coordinator Engine (`src/core/maritime_safety_auxiliary_batch6_engine.py`, < 95 LOC):**
   - Coordinates Phases 483–486 in `MaritimeSafetyAuxiliaryBatch6Engine`.
   - Generates unified `MaritimePhases483to486Assessment` with `overall_safe: bool` and total active alarms count.
2. **CLI Group (`src/cli/commands/maritime_safety_auxiliary_batch6_command.py`, < 100 LOC):**
   - Exposes commands:
     - `stpaeration-check`
     - `bearingmist-check`
     - `egbcirc-check`
     - `edgblackout-check`
   - Registered under `maritime-aux6` and Vietnamese alias `phukienhanghai6` in `src/cli/app_setup.py`.

---

## Part 2: Track 2 — Quantitative Desk Models Waves 256–258 (`algo-trader`)

### Wave 256: Cont & de Larrard (2013) Markovian LOB Queue Depletion Dynamics
1. **Microstructure Doctrine & Stochastic Queueing Model:**
   - Reference: Cont, R., & de Larrard, A. (2013). *Price Dynamics in a Markovian Limit Order Book*. SIAM Journal on Financial Mathematics, 4(1), 1–25.
   - The state of the order book is described by the depth of the first level on the bid $q^b \in \mathbb{N}$ and ask $q^a \in \mathbb{N}$.
   - Order events occur as independent Poisson streams:
     - Limit orders arrive at rate $\lambda$.
     - Market orders consume quotes at rate $\mu$.
     - Cancellations occur at rate $\theta$.
   - Effective net depletion rate per unit queue: $\nu = \mu + \theta - \lambda$.
   - **Tick Change Probabilities:**
     - When the bid queue is depleted ($q^b = 0$), the price moves down by 1 tick.
     - When the ask queue is depleted ($q^a = 0$), the price moves up by 1 tick.
     - Probability that the next price change is an upward move:
       $$p_{\text{up}}(q^b, q^a) = \frac{\Phi(q^a, q^b)}{\Phi(q^a, q^b) + \Phi(q^b, q^a)}$$
       For balanced symmetric queues under drift $\nu$, the probability simplifies to:
       $$p_{\text{up}}(q^b, q^a) = \frac{q^b}{q^b + q^a}$$
       with second-order correction for order flow imbalance $\Delta\lambda = \lambda_b - \lambda_a$.
   - **Expected Duration to Next Price Move:**
     - The first exit time $\tau = \inf\{t > 0: q_t^b = 0 \text{ or } q_t^a = 0\}$ has expectation:
       $$\mathbb{E}[\tau | q^b, q^a] = \frac{q^b \cdot q^a}{\lambda + \mu + \theta}$$
2. **Implementation Directory:**
   - Path: `src/desk/contdelarrard2013/`
   - Files: `types.ts`, `cont-de-larrard-2013-math.ts`, `index.ts` (all $< 80\text{ LOC}$, zero `:any`).

---

### Wave 257: Lehalle & Mounjid (2017) Optimal Execution with Adverse Selection & Queue Dynamics
1. **Mathematical Formulation & Adverse Selection:**
   - Reference: Lehalle, C.-A., & Mounjid, O. (2017). *Limit Order Books and Optimal Execution: How to Use Liquidity with Queue Dynamics and Adverse Selection*.
   - A trader executes an order by placing passive limit orders inside the queue at priority rank $k \in \{1, \dots, Q\}$.
   - **Adverse Selection Penalty:**
     - When a passive order at the bid is filled, it indicates that informed selling has occurred, producing a negative short-term post-trade price jump $\Delta S_{\tau+}$:
       $$\mathbb{E}[\Delta S_{\tau+} | \text{fill at bid}] = -\alpha_{\text{adverse}} \cdot \sqrt{\text{spread}} \cdot \left(\frac{\text{flow\_toxicity}}{\kappa}\right)$$
   - **Queue Fill Probability:**
     - Fill probability before queue depletion depends on trader position $k$ and cancellation rate of preceding quotes:
       $$P_{\text{fill}}(k, Q, \Delta t) = \exp\left(-\frac{k}{\mu_{\text{cancel}} + \theta_{\text{mo}}}\right) \cdot (1 - \exp(-\lambda_{\text{arrival}} \Delta t))$$
   - **Optimal Action Policy:**
     - Calculates effective expected cost of passive execution versus crossing the spread with a market order. If expected adverse drift exceeds the half-spread, the engine recommends immediate aggressive crossing (`CROSS_SPREAD`), otherwise `MAINTAIN_PASSIVE_QUEUE`.
2. **Implementation Directory:**
   - Path: `src/desk/lehallemounjid2017/`
   - Files: `types.ts`, `lehalle-mounjid-2017-math.ts`, `index.ts` (all $< 80\text{ LOC}$, zero `:any`).

---

### Wave 258: Guéant (2015) Closed-Form Multi-Asset Cross-Impact Liquidation
1. **Hamiltonian System & Matrix Closed-Form Solution:**
   - Reference: Guéant, O. (2015). *Optimal Execution with Cross-Impact: Complete and Explicit Solutions*. Finance and Stochastics.
   - For a portfolio of $d$ assets with inventory vector $q(t) \in \mathbb{R}^d$, target liquidation horizon $T$, cross-asset temporary impact matrix $\eta \in \mathbb{R}^{d \times d}$ and return covariance matrix $\Sigma \in \mathbb{R}^{d \times d}$.
   - The optimal execution trajectory solves the Euler-Lagrange matrix ODE:
     $$\ddot{q}(t) - \Omega^2 q(t) = 0$$
     where the matrix characteristic frequency is:
     $$\Omega = \left(\eta^{-1} \cdot (\gamma \Sigma)\right)^{1/2}$$
     with risk aversion parameter $\gamma > 0$.
   - **Closed-Form Solution Trajectory:**
     $$q(t) = \sinh\left((T - t)\Omega\right) \cdot \left[\sinh(T\Omega)\right]^{-1} \cdot q(0)$$
     For diagonalized systems with eigenvalues $\omega_i > 0$:
     $$q_i(t) = q_i(0) \cdot \frac{\sinh(\omega_i (T - t))}{\sinh(\omega_i T)}$$
   - Computes expected execution cost, liquidation speeds $v(t) = -\dot{q}(t)$, and portfolio risk variance.
2. **Implementation Directory:**
   - Path: `src/desk/gueant2015multiasset/`
   - Files: `types.ts`, `gueant-2015-multiasset-math.ts`, `index.ts` (all $< 80\text{ LOC}$, zero `:any`).

---

## Part 3: Test Verification Matrix & Zero-Mock DoD

| Component | Target File | Verification Metric | Strict LOC Limit |
| :--- | :--- | :--- | :--- |
| **Phase 483** | `src/core/maritime/phase_483_stp_aeration_sludge_return.py` | 100% test pass on DO warning/trip & blower failover | $< 100\text{ LOC}$ |
| **Phase 484** | `src/core/maritime/phase_484_bearing_mist_slowdown.py` | 100% test pass on bearing $\Delta T$, mist LEL & slowdown | $< 100\text{ LOC}$ |
| **Phase 485** | `src/core/maritime/phase_485_egb_circulation_dryrun.py` | 100% test pass on pump $\Delta P$, dry-run damper trip | $< 100\text{ LOC}$ |
| **Phase 486** | `src/core/maritime/phase_486_emergency_gen_blackout.py` | 100% test pass on 45s blackout restoration & 8h fuel | $< 100\text{ LOC}$ |
| **Batch 6 Coordinator** | `src/core/maritime_safety_auxiliary_batch6_engine.py` | Unified assessment & multi-system alarm count | $< 95\text{ LOC}$ |
| **Batch 6 CLI** | `src/cli/commands/maritime_safety_auxiliary_batch6_command.py` | Typer command invocations with Rich table display | $< 100\text{ LOC}$ |
| **Batch 6 Test Suite** | `tests/test_maritime_phases_483_486_suite.py` | Zero mocks, boundary condition coverage | 100% pass |
| **Wave 256** | `src/desk/contdelarrard2013/` | Markovian queue depletion, $p_{\text{up}}$, exit duration | $< 80\text{ LOC/file}$ |
| **Wave 257** | `src/desk/lehallemounjid2017/` | Adverse selection penalty, fill probability, action policy | $< 80\text{ LOC/file}$ |
| **Wave 258** | `src/desk/gueant2015multiasset/` | Closed-form matrix $\sinh(\Omega(T-t))$ liquidation | $< 80\text{ LOC/file}$ |
| **Waves 256–258 Tests** | `tests/unit/desk/waves_256_258_suite.test.ts` | Vitest test suite, zero `:any`, strict typing | 100% pass |

---

## Part 4: Implementation Schedule & Next Steps

1. **Step 1:** Implement Track 1 Maritime Safety Engines (Phases 483–486), Master Coordinator, CLI commands, and test suite in `mekong-cli`.
2. **Step 2:** Run `pytest tests/test_maritime_phases_483_486_suite.py` and `ruff check` to ensure zero lint errors.
3. **Step 3:** Implement Track 2 Quantitative Desk Models (Waves 256–258), update barrel `src/desk/index.ts`, and create test suite in `algo-trader`.
4. **Step 4:** Run `vitest run tests/unit/desk/waves_256_258_suite.test.ts` and `tsc --noEmit` to confirm zero regressions.
5. **Step 5:** Record changelog, update roadmap documentation, and persist completion memory.
