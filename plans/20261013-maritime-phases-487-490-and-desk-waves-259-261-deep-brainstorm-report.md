# Deep Brainstorming & Architecture Report: Maritime Phases 487–490 & Quantitative Waves 259–261

**Date:** 2026-10-13  
**Focus Tracks:**
- **Track 1 (Maritime Automation / Mekong CLI):** Scavenge Air Intercooler Condensate Drain & Mist Catcher, Deck Cryogenic LNG Bunkering ESD-1/ESD-2 & Breakaway Coupler, EGCS SOx Scrubber Caustic Soda (NaOH 50%) Dosing & Tank Thermal Safeguard, and Main Propulsion Intermediate Shaft Earthing Potential & Slip Ring Monitor.
- **Track 2 (Quantitative Desk / Algo Trader):** Jaisson & Rosenbaum (2015, 2016) Rough Heston & Fractional Hawkes Limit Process, Cartea, Jaimungal & Ricci (2014) Optimal Market Making with High-Frequency Alpha & Adverse Selection, and Gatheral & Schied (2011) Optimal Execution under Geometric Brownian Motion & Non-Linear Power Impact.

**Regulatory Doctrines & Mathematical Standards:**
- IMO Res. MEPC.340(77), MARPOL Annex VI Reg 14, IMO IGF Code (MSC.391(95)), SIGTTO LNG Guidelines, IACS UR M59, IACS UR M78, IACS UR E24, ISO 8178, DNV-RU-SHIP Pt.4 Ch.8.
- Microstructure & Stochastic Optimal Control: Jaisson & Rosenbaum (2015, 2016), Cartea, Jaimungal & Ricci (2014), Gatheral & Schied (2011).

---

## Executive Summary & Architectural Overview

This engineering blueprint establishes the statutory engineering specifications, physical kinetics, numerical algorithms, data contracts, and zero-mock validation test suites for:
1. **Maritime Automation Phases 487–490 (`mekong-cli`)**: Expanding the autonomous marine auxiliary machinery suite to cover turbocharger intercooler condensation removal, LNG cryogenic bunkering ESD matrices, SOx scrubber caustic neutralization thermal-pH control, and intermediate shaft electrical discharge erosion prevention.
2. **Quantitative Desk Models Waves 259–261 (`algo-trader`)**: Implementing rough volatility scaling from nearly unstable Hawkes order flow, alpha-adapted predictive market making, and non-linear power-law liquidation under geometric asset dynamics.

### Architectural Invariants & Quality Gates
- **Modularity & File Limits:** All code modules strictly $\le 100\text{ LOC}$ (Python) and $\le 90\text{ LOC}$ (TypeScript), using kebab-case self-documenting naming.
- **Zero Mocks:** No synthetic test mocks or artificial timers; zero-mock deterministic validation.
- **Type Safety:** 100% strict typing in Python 3.12+ (dataclasses, enums) and zero `:any` types in TypeScript.
- **Test Pass Rate:** 100% green test suite execution under `pytest` and `vitest`.

---

## Part 1: Track 1 — Maritime Automation Phases 487–490 (`mekong-cli`)

### Phase 487: Auxiliary Engine Scavenge Air Intercooler Condensate Drain & Mist Catcher Engine
1. **Physical Kinetics & Statutory Requirements:**
   - Complies with **IACS UR M59**, **ISO 8178**, and engine builder specifications (MAN Energy Solutions / WinGD).
   - In tropical marine conditions ($T_{\text{ambient}} > 35^\circ\text{C}$, relative humidity $\text{RH} > 80\%$), high charge air compression cools below dew point in the Charge Air Cooler (CAC), generating massive moisture fallout:
     $$\dot{m}_{\text{cond}} = \dot{m}_{\text{air}} \cdot (w_{\text{in}} - w_{\text{sat}}(T_{\text{CAC}}, P_{\text{scav}}))$$
   - Excessive liquid droplet carryover past the vane-type water mist catcher causes hydraulic shock, boundary oil film dilution, and catastrophic cylinder liner scuffing.
   - **Operational Envelope:**
     - Condensate drain trap level $h_{\text{water}} \le 60\%$ (nominal automatic float discharge).
     - High water level alarm: $h_{\text{water}} \ge 80\%$ triggers auto bypass dump valve blowdown.
     - Air duct relative humidity post-demister: $\text{RH}_{\text{post}} \le 90\%$.
     - Differential pressure across mist catcher: $\Delta P_{\text{catcher}} \le 0.08\text{ bar}$ (fouling limit $\ge 0.12\text{ bar}$).
     - Scavenge air temperature post-cooler: $T_{\text{scav}} \ge 35^\circ\text{C}$ to suppress subcooling condensation.

2. **Data Contracts & System Interfaces:**
   - Module: `src/core/maritime/phase_487_scavenge_intercooler_drain.py` ($\le 95\text{ LOC}$)
   - Status Enum: `ScavengeDrainStatus` (`NORMAL`, `WATER_LEVEL_HIGH_BLOWDOWN`, `MIST_CATCHER_FOULING_ALARM`, `SCAVENGE_SUBCOOLING_TRIP`, `DRAIN_TRAP_FAILURE`).
   - Telemetry Dataclass:
     ```python
     @dataclass(frozen=True)
     class ScavengeDrainTelemetry:
         condensate_level_pct: float
         mist_catcher_dp_bar: float
         scavenge_air_temp_c: float
         air_relative_humidity_pct: float
         auto_drain_valve_open: bool
         bypass_blowdown_active: bool
     ```
   - Assessment Dataclass:
     ```python
     @dataclass(frozen=True)
     class ScavengeDrainAssessment:
         status: ScavengeDrainStatus
         bypass_blowdown_command: bool
         cylinder_lube_boost_command: bool
         drain_system_healthy: bool
         remarks: str
     ```

---

### Phase 488: Deck Cryogenic LNG Bunkering ESD-1/ESD-2 & Breakaway Coupler Safety Engine
1. **Physical Kinetics & Statutory Requirements:**
   - Complies with **IMO IGF Code (MSC.391(95))**, **SIGTTO LNG Transfer Manifolds**, and **IACS UR M78**.
   - Cryogenic liquid methane ($T = -162^\circ\text{C}$, $P = 1.0\text{--}4.5\text{ bar}$) transfer requires a dual-stage safety shutdown matrix:
     - **ESD-1 (Emergency Shut Down Stage 1):** Controlled cessation of transfer pumps and manifold ESD valve closure in $15\text{ s} \le t_{\text{close}} \le 30\text{ s}$ to prevent hydraulic surge / pressure spike ($P_{\text{surge}} \le 1.5 \times P_{\text{design}}$).
     - **ESD-2 (Emergency Shut Down Stage 2):** Mechanical or hydraulic Dry-Breakaway Coupler (ERC/CBC) separation with dual dry-disconnect flap seals and automated nitrogen purge curtain.
   - **Trip Conditions:**
     - Cryogenic spill onto drip tray: $T_{\text{drip\_tray}} < -50^\circ\text{C}$ initiates immediate ESD-1.
     - Gas detection at manifold zone: $\text{CH}_4 \ge 20\%\text{ LEL}$ (pre-alarm), $\ge 40\%\text{ LEL}$ (ESD-1 trip).
     - Manifold vapor return pressure: $P_{\text{vapor}} \ge 3.0\text{ bar}$ (surge hazard).
     - Mooring surge excursion / transfer arm envelope: displacement $\Delta x \ge 80\%$ (warning), $\ge 100\%$ (ESD-2 breakaway).

2. **Data Contracts & System Interfaces:**
   - Module: `src/core/maritime/phase_488_lng_bunkering_esd.py` ($\le 95\text{ LOC}$)
   - Status Enum: `LngBunkeringEsdStatus` (`NORMAL_TRANSFER`, `ESD1_GAS_LEAK_TRIP`, `ESD1_CRYOGENIC_SPILL_TRIP`, `ESD1_PRESSURE_SURGE_TRIP`, `ESD2_EMERGENCY_BREAKAWAY`).
   - Telemetry Dataclass:
     ```python
     @dataclass(frozen=True)
     class LngBunkeringEsdTelemetry:
         manifold_pressure_bar: float
         vapor_return_pressure_bar: float
         drip_tray_temp_c: float
         gas_concentration_pct_lel: float
         transfer_arm_envelope_pct: float
         esd_link_connected: bool
         nitrogen_purge_active: bool
     ```
   - Assessment Dataclass:
     ```python
     @dataclass(frozen=True)
     class LngBunkeringEsdAssessment:
         status: LngBunkeringEsdStatus
         esd1_valve_close_command: bool
         esd2_breakaway_command: bool
         bunkering_permissive: bool
         remarks: str
     ```

---

### Phase 489: EGCS SOx Scrubber Caustic Soda (NaOH 50%) Neutralization & Storage Tank Thermal Engine
1. **Physical Kinetics & Statutory Requirements:**
   - Complies with **IMO Resolution MEPC.340(77)** (2021 EGCS Guidelines) and **MARPOL Annex VI Reg 14**.
   - Closed-loop / hybrid scrubbers use concentrated $50\%\text{ w/w NaOH}$ for sulfur oxides neutralization:
     $$\text{SO}_2 + 2\text{NaOH} \to \text{Na}_2\text{SO}_3 + \text{H}_2\text{O}$$
   - **Physical Properties of 50% NaOH:**
     - Freezing/crystallization point is $+12.0^\circ\text{C}$! Fluid turns solid if unheated.
     - Safe storage temperature: $18.0^\circ\text{C} \le T_{\text{tank}} \le 35.0^\circ\text{C}$.
     - Low temperature alert: $T_{\text{tank}} < 15.0^\circ\text{C}$ (crystallization risk).
     - Overheat trip: $T_{\text{tank}} > 45.0^\circ\text{C}$ (accelerated caustic stress corrosion cracking in steel containment).
   - **Process Effluent Control:**
     - Discharge washwater $pH \ge 6.5$ (at 4m overboard distance).
     - Chemical dosing line pressure: $P_{\text{dosing}} \le 5.0\text{ bar}$ (burst disc trip at $6.0\text{ bar}$).
     - Bund leakage sensor: optical conductivity detection.

2. **Data Contracts & System Interfaces:**
   - Module: `src/core/maritime/phase_489_egcs_caustic_thermal.py` ($\le 95\text{ LOC}$)
   - Status Enum: `EgcsCausticStatus` (`NORMAL`, `TANK_LOW_TEMP_CRYSTAL_RISK`, `TANK_HIGH_TEMP_CORROSION_RISK`, `DOSING_OVERPRESSURE_TRIP`, `EFFLUENT_PH_ACIDIC_VIOLATION`, `BUND_LEAK_DETECTED`).
   - Telemetry Dataclass:
     ```python
     @dataclass(frozen=True)
     class EgcsCausticTelemetry:
         tank_temp_c: float
         dosing_pressure_bar: float
         process_washwater_ph: float
         bund_leakage_detected: bool
         heating_loop_energized: bool
         dosing_pump_running: bool
     ```
   - Assessment Dataclass:
     ```python
     @dataclass(frozen=True)
     class EgcsCausticAssessment:
         status: EgcsCausticStatus
         tank_heating_command: bool
         dosing_pump_permissive: bool
         scrubber_chemical_safe: bool
         remarks: str
     ```

---

### Phase 490: Main Propulsion Intermediate Shaft Earthing Potential & Slip Ring Monitor Engine
1. **Physical Kinetics & Statutory Requirements:**
   - Complies with **IACS UR E24**, **ClassNK Guidance**, and **DNV Pt.4 Ch.8**.
   - Galvanic action between bronze propeller, steel hull, and cathodic protection creates electrical potential across propeller shaft and hull:
     - Oil film in stern tube bearings acts as an electrical insulator ($R_{\text{film}} \approx 10\text{--}100\,\Omega$).
     - When potential difference exceeds $\Delta V \ge 80.0\text{ mV}$, dielectric breakdown occurs, creating electrical spark erosion micro-arcing. This creates micro-pitting, destroys white metal bearing surfaces, and leads to journal bearing seizure.
   - **Shaft Earthing System Operation:**
     - High-silver contact brushes ($80\%\text{ Ag}$) riding on copper slip ring discharge current directly to hull.
     - Acceptable running potential: $\Delta V \le 50.0\text{ mV}$.
     - Warning threshold: $50.0\text{ mV} < \Delta V < 80.0\text{ mV}$.
     - Critical spark erosion alert: $\Delta V \ge 80.0\text{ mV}$ (requires immediate brush contact cleaning / changeover).
     - Brush wear limit: Remaining length $L_{\text{brush}} \le 12.0\text{ mm}$ (from nominal $40.0\text{ mm}$).

2. **Data Contracts & System Interfaces:**
   - Module: `src/core/maritime/phase_490_shaft_earthing_monitor.py` ($\le 95\text{ LOC}$)
   - Status Enum: `ShaftEarthingStatus` (`NORMAL`, `POTENTIAL_HIGH_WARNING`, `SPARK_EROSION_CRITICAL_TRIP`, `BRUSH_WEAR_DEPLETED`, `SLIP_RING_DIRT_CONTAMINATION`).
   - Telemetry Dataclass:
     ```python
     @dataclass(frozen=True)
     class ShaftEarthingTelemetry:
         shaft_potential_mv: float
         shaft_current_discharge_a: float
         brush_wear_remaining_mm: float
         shaft_rpm: float
         auxiliary_monitoring_brush_mv: float
     ```
   - Assessment Dataclass:
     ```python
     @dataclass(frozen=True)
     class ShaftEarthingAssessment:
         status: ShaftEarthingStatus
         spark_erosion_risk: bool
         brush_replacement_due: bool
         earthing_effective: bool
         remarks: str
     ```

---

### Batch 7 Master Coordinator & CLI Command Architecture
- **Coordinator Engine:** `src/core/maritime_safety_auxiliary_batch7_engine.py` ($\le 95\text{ LOC}$)
  - Combines Phases 487–490 into `MaritimePhases487to490Assessment`.
  - Determines `overall_safe: bool` and calculates active alarms count.
- **CLI Commands:** `src/cli/commands/maritime_safety_auxiliary_batch7_command.py` ($\le 100\text{ LOC}$)
  - Typer app `maritime_aux7_app` registered in `src/cli/app_setup.py` under `maritime-aux7` and Vietnamese alias `phukienhanghai7`.
  - Subcommands: `scavdrain-check`, `lngesd-check`, `egcscaustic-check`, `shaftearth-check`.
- **Pytest Suite:** `tests/test_maritime_phases_487_490_suite.py` ($\ge 6$ zero-mock unit and CLI test cases).

---

## Part 2: Track 2 — Quantitative Desk Models Waves 259–261 (`algo-trader`)

### Wave 259: Jaisson & Rosenbaum (2015, 2016) Rough Heston & Fractional Hawkes Limit Process
1. **Mathematical Foundations & Microstructure Dynamics:**
   - Demonstrates that high-frequency order arrivals modeled as nearly unstable Hawkes processes with heavy-tailed power-law memory $\phi(t) \sim t^{-(1+\alpha)}$ converge at macroscopic scales to the **Rough Heston Model** with Hurst parameter $H = \alpha - 1/2 \in (0, 1/2)$.
   - Subdiffusive fractional volatility kernel:
     $$K(t) = \frac{t^{H - 1/2}}{\Gamma(H + 1/2)}$$
   - Instantaneous rough variance:
     $$V_t = V_0 + \int_0^t \frac{(t-s)^{H-1/2}}{\Gamma(H+1/2)} \lambda (\theta - V_s) ds + \int_0^t \frac{(t-s)^{H-1/2}}{\Gamma(H+1/2)} \nu \sqrt{V_s} dW_s$$
   - Power-law term structure of at-the-money implied volatility skew:
     $$\psi(\tau) = \left|\frac{\partial \sigma_{\text{IV}}}{\partial \ln K}\right|_{\text{ATM}} \sim C \cdot \tau^{H - 1/2} = C \cdot \tau^{-\beta}, \quad \beta = \frac{1}{2} - H$$
   - Captures the steep explosion of ATM skew for short maturities ($\tau \to 0$) which classical Brownian models ($\beta = 0$) fail to reproduce.

2. **TypeScript Module Architecture:**
   - Directory: `src/desk/jaissonrosenbaum2016/`
   - Files: `types.ts`, `jaisson-rosenbaum-2016-math.ts`, `index.ts` ($\le 80\text{ LOC/file}$)
   - Key Function: `computeRoughHestonHawkesLimit(params: RoughHestonHawkesParams): RoughHestonHawkesResult`

---

### Wave 260: Cartea, Jaimungal & Ricci (2014) Optimal Market Making with High-Frequency Alpha & Adverse Selection
1. **Mathematical Foundations & Microstructure Dynamics:**
   - Incorporates short-term predictive order-flow alpha $\alpha_t$ into stochastic control for market makers:
     $$dS_t = \alpha_t dt + \sigma dW_t$$
     where $\alpha_t$ satisfies mean-reverting Ornstein-Uhlenbeck drift:
     $$d\alpha_t = -k \alpha_t dt + \sigma_\alpha dW_t^\alpha$$
   - Market maker posts active quotes $\delta_t^b$ and $\delta_t^a$ relative to mid-price.
   - Closed-form optimal bid/ask half-spreads with inventory penalty $\gamma$ and fill intensity decay $\kappa$:
     $$\delta^{b*}(q, \alpha) = \frac{1}{\kappa} + \frac{1}{2} \gamma \sigma^2 (2q - 1) - \frac{\alpha}{k + \kappa \sigma}$$
     $$\delta^{a*}(q, \alpha) = \frac{1}{\kappa} - \frac{1}{2} \gamma \sigma^2 (2q + 1) + \frac{\alpha}{k + \kappa \sigma}$$
   - When short-term predictive alpha is positive ($\alpha > 0$, impending upward price move):
     - The bid spread tightens ($\delta^{b*}$ decreases) to capture incoming aggressive sells before the rally.
     - The ask spread widens ($\delta^{a*}$ increases) to avoid adverse fill toxicity.

2. **TypeScript Module Architecture:**
   - Directory: `src/desk/carteajaimungalricci2014/`
   - Files: `types.ts`, `cartea-jaimungal-ricci-2014-math.ts`, `index.ts` ($\le 80\text{ LOC/file}$)
   - Key Function: `computeCarteaAlphaMarketMaking(params: CarteaAlphaMarketMakingParams): CarteaAlphaMarketMakingResult`

---

### Wave 261: Gatheral & Schied (2011) Optimal Trade Execution under Geometric Brownian Motion & Non-Linear Power Impact
1. **Mathematical Foundations & Microstructure Dynamics:**
   - Formulates optimal liquidation when asset price follows Geometric Brownian Motion rather than arithmetic Brownian motion:
     $$dS_t = S_t (\sigma dW_t - \eta |v_t|^{\alpha-1} v_t dt)$$
   - Avoids negative prices and models percentage impact on large blocks.
   - Non-linear instantaneous power-law impact ($\alpha \approx 0.5$, square-root law of market impact):
     $$f(v) = \eta \cdot v^\alpha$$
   - Solves the calculus of variations problem under log-utility or risk-neutral objective to derive the optimal liquidation path:
     $$q(t) = Q_0 \left(1 - \frac{t}{T}\right)^{\frac{\alpha + 1}{\alpha}}$$
   - Evaluates implementation shortfall $\mathbb{E}[\text{IS}]$, liquidity extraction friction, and risk-adjusted total execution cost.

2. **TypeScript Module Architecture:**
   - Directory: `src/desk/gatheralschied2011/`
   - Files: `types.ts`, `gatheral-schied-2011-math.ts`, `index.ts` ($\le 85\text{ LOC/file}$)
   - Key Function: `computeGatheralGbmLiquidation(params: GatheralGbmLiquidationParams): GatheralGbmLiquidationResult`

---

## Part 3: Implementation Roadmaps & Verification Matrix

### Verification Matrix & Execution Plan
| Track | Phase / Wave | File Path | Statutory / Academic Authority | Primary Metric / Assertion |
|---|---|---|---|---|
| **Track 1** | Phase 487 | `src/core/maritime/phase_487_scavenge_intercooler_drain.py` | IACS UR M59, ISO 8178 | Level $\ge 80\%$ auto bypass blowdown |
| **Track 1** | Phase 488 | `src/core/maritime/phase_488_lng_bunkering_esd.py` | IMO IGF Code, SIGTTO | Drip tray $<-50^\circ\text{C}$ / $\text{CH}_4 \ge 40\%$ ESD-1 |
| **Track 1** | Phase 489 | `src/core/maritime/phase_489_egcs_caustic_thermal.py` | IMO MEPC.340(77), MARPOL VI | Tank $T < 15^\circ\text{C}$ crystallization alert |
| **Track 1** | Phase 490 | `src/core/maritime/phase_490_shaft_earthing_monitor.py` | IACS UR E24, DNV Pt.4 Ch.8 | Potential $\ge 80\text{ mV}$ spark erosion alarm |
| **Track 1** | Coordinator | `src/core/maritime_safety_auxiliary_batch7_engine.py` | IACS / SOLAS Master Safety | Aggregate safety assessment & alarm counts |
| **Track 1** | CLI | `src/cli/commands/maritime_safety_auxiliary_batch7_command.py` | Typer CLI Suite | Bilingual subcommands & options |
| **Track 2** | Wave 259 | `src/desk/jaissonrosenbaum2016/` | Jaisson & Rosenbaum (2016) | $H \in (0, 0.5)$, Skew slope $\tau^{H-0.5} \to \infty$ |
| **Track 2** | Wave 260 | `src/desk/carteajaimungalricci2014/` | Cartea, Jaimungal, Ricci (2014) | $\alpha > 0 \implies \delta^{b*} \downarrow, \delta^{a*} \uparrow$ |
| **Track 2** | Wave 261 | `src/desk/gatheralschied2011/` | Gatheral & Schied (2011) | Power-law trajectory $q(T) = 0$ |
