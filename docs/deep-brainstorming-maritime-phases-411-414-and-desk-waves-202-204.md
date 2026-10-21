# Deep Brainstorming & Architecture Blueprint: Maritime Phases 411-414 & Quantitative Waves 202-204

**Date:** 2026-10-09  
**Status:** Architecture Blueprint & Implementation Specification  
**Enforcement Rules:** Strictly < 180 LOC per file (Python) / < 150 LOC (TypeScript), zero mocks, real mathematical & physical models, zero `:any` types, 100% test coverage.

---

## Executive Summary & Architectural Overview

This blueprint establishes the coordinated next-horizon expansion across **Mekong CLI Maritime Auxiliary & Propulsion Platforms** and **Algo-Trader Quantitative High-Frequency Desks**:

1. **Track 1: Mekong CLI Maritime Auxiliary, Propulsion & Fire Safety (Phases 411–414)**
   - **Phase 411**: Marine Main Engine Jacket Water High-Temp Preheating & Thermostatic Cooling (ISO 8217 / MAN Energy Solutions / WinGD)
   - **Phase 412**: Marine Main Starting Air Compressor Auto-Unloading & Dual Relief Safety (SOLAS II-1 Reg 26 / DNV Pt.4 Ch.6)
   - **Phase 413**: Marine Fixed High-Pressure CO2 Total Flooding Fire Extinguishing System (SOLAS II-2 Reg 10 / IMO FSS Code Ch.5)
   - **Phase 414**: Marine Bow Visor & Inner Bow Door Hydraulic Latching & Water Ingress Detection for Ro-Ro Cargo/Passenger Ships (SOLAS II-1 Reg 17-1 / IACS UR S8)
   - **Unified Facade**: `MaritimePropulsionFireSafetyEngine` (Phases 411–414)
   - **CLI & FastMCP**: Typer command modules & FastMCP tool handlers in `scripts/mcp_server.py`.

2. **Track 2: Algo-Trader Quantitative Desks (Waves 202–204)**
   - **Wave 202**: Gatheral (2006) / Lee (2004) SVI (Stochastic Volatility Inspired) Implied Volatility Surface & Arbitrage-Free Verification (`src/desk/svi/`)
   - **Wave 203**: Madhavan, Richardson & Roomans (1997) (MRR) Structural Market Microstructure Trade Indicator Model (`src/desk/mrr/`)
   - **Wave 204**: Andersen, Bollerslev, Diebold & Labys (2003) & Corsi (2009) HAR-RV Multi-Component Volatility Forecasting Framework (`src/desk/abdl/`)

---

## Detailed Specifications: Track 1 — Maritime Automation (Mekong CLI)

### Phase 411: Marine Main Engine Jacket Water High-Temp Preheating & Thermostatic Cooling (ISO 8217 / MAN ES / WinGD)
- **Domain:** Two-Stroke Marine Diesel Cylinder Liner Heat Management & Cold Start Thermal Shock Prevention.
- **Thermodynamic Model & Control Laws:**
  - **Cold Start Preheating Interlock:** Cylinder jacket cooling water must be circulated and preheated to $T_{\text{JW}} \ge 60.0^\circ\text{C}$ prior to main engine startup (alarm below $55.0^\circ\text{C}$, start permissive locked out below $50.0^\circ\text{C}$).
  - **Operating Temperature Regulation:** High-Temperature (HT) circuit setpoint $T_{\text{out}} = 85.0^\circ\text{C} \pm 2.0^\circ\text{C}$ at full Sea Load via 3-way thermostatic mixing valve PID control.
  - **Temperature Rise Across Engine:** $\Delta T_{\text{JW}} = T_{\text{out}} - T_{\text{in}} \le 12.0^\circ\text{C}$ (excessive $\Delta T$ signals inadequate circulation pump flow or heat transfer fouling).
  - **Expansion Tank Head Pressure & Chemical Condition:** Static head pressure $P_{\text{static}} \ge 1.5\,\text{bar}$, expansion tank level $\ge 40\%$, and cooling water nitrite corrosion inhibitor concentration $c_{\text{NO2}} \in [700, 1500]\,\text{ppm}$.

### Phase 412: Marine Main Starting Air Compressor Auto-Unloading & Dual Relief Safety (SOLAS II-1 Reg 26 / DNV Pt.4)
- **Domain:** Main Engine Compressed Air Storage, Charging Automation & Overpressure Protection.
- **Pneumatics & Charging Thermodynamics:**
  - **Two-Stage Compression:** Intermediate interstage pressure $P_1 \in [4.5, 6.5]\,\text{bar}$ with interstage air cooler condensate trap; final stage discharge pressure $P_2 = 30.0\,\text{bar}$.
  - **Automatic Unloading & Drainage:** Solenoid-actuated auto-drain unloader purging moisture during startup and every $\tau_{\text{drain}} = 15.0\,\text{min}$ under load to prevent water carryover and hydraulic lock.
  - **Pressure Switch Control Hysteresis:** Automatic compressor start at receiver pressure $P_{\text{recv}} \le 25.0\,\text{bar}$, automatic cutoff at $P_{\text{recv}} \ge 30.0\,\text{bar}$.
  - **Dual Relief Valves & Charging Rate:** Spring-loaded safety relief valve set at $1.10 \times P_{\text{work}} = 33.0\,\text{bar}$. Receiver capacity test: 2 independent starting air receivers recharged from atmospheric pressure ($0\,\text{bar}$) to $30.0\,\text{bar}$ within $t_{\text{charge}} \le 60.0\,\text{min}$.

### Phase 413: Marine Fixed High-Pressure CO2 Total Flooding Fire Extinguishing System (SOLAS II-2 Reg 10 / IMO FSS Code Ch.5)
- **Domain:** Machinery Space Category A & Cargo Hold Total Flooding Fire Protection.
- **Fluid Dynamics & Safety Interlocks:**
  - **Protected Space Net Volume:** $V_{\text{free}} = V_{\text{gross}} - V_{\text{machinery}}$.
  - **Required CO2 Mass Calculation:**
    $$m_{\text{CO2}} = \max\left(0.40 \times V_{\text{free}} \times \rho_{\text{free}},\, 0.35 \times V_{\text{gross}} \times \rho_{\text{gross}}\right)$$
    Standard cylinder capacity: 67.5 L high-pressure steel cylinders containing $45.0\,\text{kg}$ liquid CO2 (filling ratio $\le 0.67\,\text{kg/L}$).
  - **Rapid Discharge Requirement:** $85\%$ of the total required CO2 quantity must be discharged into the engine room within $t_{\text{discharge}} \le 120.0\,\text{s}$ (2 minutes).
  - **Pre-Discharge Alarm & Ventilation Interlock:** Pneumatic time delay ($20\text{--}30\,\text{s}$) with audible siren and visual flashing beacon. Main engine fuel quick-closing valves, boiler fuel pumps, and engine room ventilation supply/exhaust fan dampers automatically trip upon cabinet door opening.

### Phase 414: Marine Bow Visor & Inner Bow Door Hydraulic Latching & Water Ingress Detection for Ro-Ro Cargo/Passenger Ships (SOLAS II-1 Reg 17-1 / IACS UR S8)
- **Domain:** Ro-Ro Ferry Bow Door Sealing, Hydraulic Locking Integrity & Catastrophic Ingress Prevention.
- **Structural Mechanics & Instrumentation:**
  - **Hydraulic Wedge Locking:** Multi-point hydraulic locking cleats and wedges; verification that hydraulic operating pressure $P_{\text{hyd}} \ge 160.0\,\text{bar}$ and locking pins are fully engaged.
  - **Dual Redundant Sensor Monitoring:** Closed and locked states verified by dual independent microswitches/inductive proximity sensors (Sensor A and Sensor B must agree: discrepancy triggers bridge warning).
  - **Pneumatic Inflatable Seal Pressure:** Inflatable rubber perimeter seal pressure $P_{\text{seal}} \ge 3.5\,\text{bar}$ (alarm if $P_{\text{seal}} < 3.0\,\text{bar}$).
  - **Bow Coaming Water Ingress Level:** Water level sensors in the compartment between bow door and inner collision bulkhead: Level 1 warning ($h \ge 0.10\,\text{m}$), Level 2 emergency trip ($h \ge 0.50\,\text{m}$), with bridge audible alarm and vessel speed interlock ($V_{\text{ship}} > 0.5\,\text{knots}$ triggers immediate navigation alert).

---

## Detailed Specifications: Track 2 — Quantitative Desk (Algo-Trader)

### Wave 202: Gatheral (2006) / Lee (2004) SVI Implied Volatility Surface (`src/desk/svi/`)
- **Seminal References:** Jim Gatheral (2006), "A Parabolic Volatility Surface"; Gatheral & Jacquier (2014), "Arbitrage-free SVI volatility surfaces", *Quantitative Finance*; Roger Lee (2004), "The Moment Formula for Implied Volatility at Extreme Strikes", *Mathematical Finance*.
- **Raw SVI Parameterization:**
  $$w(k; \chi) = a + b \left( \rho (k - m) + \sqrt{(k - m)^2 + \sigma^2} \right)$$
  where $k = \ln(K / F)$ is log-moneyness, $a \in \mathbb{R}$, $b \ge 0$, $|\rho| < 1$, $m \in \mathbb{R}$, and $\sigma > 0$.
- **Arbitrage-Free Conditions:**
  - **Non-negativity:** $a + b \sigma \sqrt{1 - \rho^2} \ge 0$.
  - **Lee's Wing Slopes:** As $k \to \pm \infty$, $\lim \frac{w(k)}{|k|} = b(1 \pm \rho) \le \frac{2}{T}$.
  - **Butterfly Arbitrage Freedom (Durrleman 2004):**
    $$g(k) = \left( 1 - \frac{k w'(k)}{2 w(k)} \right)^2 - \frac{(w'(k))^2}{4} \left( \frac{1}{w(k)} + \frac{1}{4} \right) + \frac{w''(k)}{2} \ge 0 \quad \forall k \in \mathbb{R}$$
- **Quasi-Explicit Calibration (Zeliade 2009):**
  Given $(m, \sigma, \rho)$, parameters $(a, b)$ are determined by 2D non-negative constrained ordinary least squares.

### Wave 203: Madhavan, Richardson & Roomans (1997) (MRR) Structural Market Microstructure (`src/desk/mrr/`)
- **Seminal Reference:** Ananth Madhavan, David Richardson & Mark Roomans (1997), "Why Do Security Prices Change? A Transaction-Level Analysis of NYSE Stocks", *Review of Financial Studies*.
- **Structural Dynamics:**
  - Unobserved true value: $v_t = v_{t-1} + \theta (x_t - \rho x_{t-1}) + \epsilon_t$, where $x_t \in \{-1, +1\}$ is trade indicator.
  - Price quote: $p_t = v_t + \phi x_t + \xi_t$, with order processing cost $\phi$.
  - Price change: $\Delta p_t = (\phi + \theta) x_t - (\phi + \rho \theta) x_{t-1} + u_t$.
- **Moment Conditions & Estimator:**
  $$\gamma_0 = \text{Var}(\Delta p_t) = (\phi + \theta)^2 + (\phi + \rho \theta)^2 - 2 \rho (\phi + \theta)(\phi + \rho \theta) + \sigma_u^2$$
  $$\gamma_1 = \text{Cov}(\Delta p_t, \Delta p_{t-1}) = -(\phi + \rho \theta)(\phi + \theta) + \rho (\phi + \theta)^2 + \rho (\phi + \rho \theta)^2$$
  Allows exact decomposition of the effective bid-ask spread into adverse selection component $\theta$ vs. order processing markup $\phi$.

### Wave 204: Andersen, Bollerslev, Diebold & Labys (2003) & Corsi (2009) HAR-RV Framework (`src/desk/abdl/`)
- **Seminal References:** Torben G. Andersen, Tim Bollerslev, Francis X. Diebold & Paul Labys (2003), "Modeling and Forecasting Realized Volatility", *Econometrica*; Fulvio Corsi (2009), "A Simple Approximate Long-Memory Model of Realized Volatility", *Journal of Financial Econometrics*.
- **Heterogeneous Autoregressive Realized Volatility (HAR-RV):**
  $$RV_{t+1}^{(d)} = \beta_0 + \beta_d RV_t^{(d)} + \beta_w RV_t^{(w)} + \beta_m RV_t^{(m)} + \varepsilon_{t+1}$$
  where:
  - Daily: $RV_t^{(d)} = RV_t$
  - Weekly: $RV_t^{(w)} = \frac{1}{5} \sum_{i=0}^4 RV_{t-i}$
  - Monthly: $RV_t^{(m)} = \frac{1}{22} \sum_{i=0}^{21} RV_{t-i}$
- **Jump-Augmented Specification (HAR-RV-J):**
  Using Barndorff-Nielsen & Shephard Bipower Variation $BV_t$:
  $$J_t = \max\left(0,\, RV_t - BV_t\right), \quad C_t = RV_t - J_t$$
  $$RV_{t+1}^{(d)} = \beta_0 + \beta_{cd} C_t^{(d)} + \beta_{cw} C_t^{(w)} + \beta_{cm} C_t^{(m)} + \beta_j J_t + \varepsilon_{t+1}$$
- **Forecast Verification:** Mincer-Zarnowitz regression $RV_{t+1} = a + b \widehat{RV}_{t+1} + e_{t+1}$ testing unbiasedness ($a = 0, b = 1$).

---

## Technical Stack & Quality Assurance Blueprint

| Module | Files & Responsibility | Strict Line Cap | Target Test Coverage |
|---|---|---|---|
| **Phase 411 Jacket Water** | `src/core/maritime/phase_411_jacket_water_preheating.py` | < 180 LOC | Preheating interlock, PID 3-way valve, nitrite concentration |
| **Phase 412 Air Compressor** | `src/core/maritime/phase_412_starting_air_compressor.py` | < 180 LOC | 2-stage pressures, auto-drain unloader, 60min charging test |
| **Phase 413 Fixed CO2 System** | `src/core/maritime/phase_413_fixed_co2_fire_extinguishing.py` | < 180 LOC | Net volume, 85% 2-min discharge, fan/fuel trip interlocks |
| **Phase 414 Ro-Ro Bow Door** | `src/core/maritime/phase_414_roro_bow_door_latching.py` | < 180 LOC | Hydraulic wedge lock, dual proximity microswitch, water ingress alarm |
| **Maritime Propulsion & Fire Facade** | `src/core/maritime_propulsion_fire_safety_engine.py` | < 180 LOC | Consolidated telemetry & unified status assessment |
| **Typer CLI & FastMCP** | `src/cli/commands/maritime_jacket_air_co2_bow_command.py` + `scripts/mcp_server.py` | < 180 LOC | Typer commands & 5 FastMCP tools |
| **Wave 202 SVI Volatility** | `src/desk/svi/` (4 modules + barrel) | < 150 LOC per file | Butterfly/calendar arbitrage, Lee wing slope, Zeliade calibration |
| **Wave 203 MRR Microstructure** | `src/desk/mrr/` (3 modules + barrel) | < 150 LOC per file | Autocovariances $\gamma_0, \gamma_1$, adverse selection $\theta$, order processing $\phi$ |
| **Wave 204 ABDL HAR-RV** | `src/desk/abdl/` (3 modules + barrel) | < 150 LOC per file | Daily/weekly/monthly aggregation, jump decomposition, Mincer-Zarnowitz |

---

## Implementation Sequence (Step-by-Step)

```
[Phase 411: Jacket Water]  --> [Phase 412: Air Compressor]  --> [Phase 413: Fixed CO2]  --> [Phase 414: Ro-Ro Bow Door]
          \                               \                           /                          /
           \-------------------------------> [Unified Facade Engine] <-------------------------/
                                                        |
                                      [Typer CLI & FastMCP Tools]
                                                        |
                                          [pytest Suite (7/7 Green)]

[Wave 202: SVI Vol Surface] --> [Wave 203: MRR Microstructure] --> [Wave 204: ABDL HAR-RV Volatility]
          \                                  |                                     /
           \-----------------------> [Vitest Suite (100% Green)] <----------------/
```

**Approval Status:** COMPLETED ARCHITECTURAL BLUEPRINT. READY TO IMPLEMENT.
