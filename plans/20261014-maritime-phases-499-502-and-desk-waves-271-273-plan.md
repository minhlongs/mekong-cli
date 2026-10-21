# Dual-Track Plan: Maritime Auxiliary Automation Batch 10 (Phases 499–502) & Quantitative Desk Waves 271–273

**Date:** 2026-10-14
**Status:** In Progress

## Track 1: Maritime Auxiliary Automation Batch 10 (Phases 499–502, `mekong-cli`)

All modules strictly $\le 90\text{ LOC}$, deterministic, zero mocks.

1. **Phase 499: Main Engine Turbocharger Overspeed, Lube Oil Header & Surge Protection (IACS UR M10 & MAN B&W / WinGD Rules)**
   - File: `src/core/maritime/phase_499_turbocharger_overspeed_surge.py`
   - Evaluates TC speed ($N_{\text{tc}}$ nominal $\le 18000\text{ RPM}$, overspeed alarm $\ge 18500\text{ RPM}$, emergency engine slowdown trip $\ge 19500\text{ RPM}$), bearing lube oil inlet pressure ($P_{\text{lo}} \ge 1.2\text{ bar}$ nominal, low pressure alarm $< 1.2\text{ bar}$, critical trip $< 0.8\text{ bar}$), exhaust gas inlet temperature ($T_{\text{exh}} \le 520.0^\circ\text{C}$ nominal, high alarm $> 550.0^\circ\text{C}$), and compressor surge pulse counter ($\ge 3\text{ pulses/min}$ opening wastegate/bypass valve).

2. **Phase 500: Fresh Water Generator (FWG) Vacuum Boiling, Ejector Pressure & Distillate Salinity Control (IACS UR M10 & WHO Maritime Potable Water Standards)**
   - File: `src/core/maritime/phase_500_fresh_water_generator_salinity.py`
   - Evaluates shell vacuum ($\le -0.85\text{ bar}$ nominal for $40\text{--}45^\circ\text{C}$ evaporation, low vacuum alarm $> -0.80\text{ bar}$), combined brine/air ejector motive water pressure ($\ge 2.5\text{ bar}$ nominal, low pressure trip $< 2.2\text{ bar}$), distillate salinity salinometer ($\le 2.0\text{ ppm}$ nominal, dump solenoid diversion to bilge at $> 10.0\text{ ppm}$), and jacket heating water inlet temperature ($75.0\text{--}85.0^\circ\text{C}$).

3. **Phase 501: Cargo Hold Fixed CO2 Fire Extinguishing Total Flooding & Gang Release Interlock (SOLAS II-2 Reg 10.4 & IMO FSS Code Ch. 5)**
   - File: `src/core/maritime/phase_501_co2_total_flooding_interlock.py`
   - Evaluates cabinet door pre-discharge audiovisual evacuated space alarm ($> 20.0\text{ s}$ mandatory time delay before main valve opening), cargo hold ventilation fan auto-trip interlock, fire damper closure verification, and pilot cylinder manifold pressure ($\ge 50.0\text{ bar}$ nominal, low pressure alarm $< 45.0\text{ bar}$).

4. **Phase 502: Main Engine Fuel Oil Viscosity Viscometer & Steam Heater PID Modulation (IACS UR M10 & ISO 8217 Marine Residual Fuels)**
   - File: `src/core/maritime/phase_502_fuel_oil_viscometer_heater.py`
   - Evaluates HFO injection viscosity ($12.0\text{--}15.0\text{ cSt}$ nominal at fuel rail, high viscosity alarm $> 18.0\text{ cSt}$, low viscosity lubricity alarm $< 10.0\text{ cSt}$), fuel temperature ramp rate ($\le 2.0^\circ\text{C/min}$ to protect plunger/barrel from thermal seizure during MGO-to-HFO changeover), and steam tracing valve modulation.

5. **Coordinator, CLI & Tests**:
   - `src/core/maritime_safety_auxiliary_batch10_engine.py`
   - `src/cli/commands/maritime_safety_auxiliary_batch10_command.py` (`maritime-aux10` / `phukienhanghai10`)
   - Registration in `src/cli/app_setup.py`
   - `tests/test_maritime_phases_499_502_suite.py`

## Track 2: Quantitative Desk Models Waves 271–273 (`algo-trader`)

All modules strictly $\le 85\text{ LOC}$, zero `:any` types, pure TypeScript math.

1. **Wave 271: Cartea & Jaimungal (2015) Optimal Execution with Limit and Market Orders (`src/desk/carteajaimungal2015limitmarket/`)**
   - Models hybrid execution combining posted passive limit orders (earning spread rebate $\delta_t^*$ at fill rate $\lambda e^{-\kappa \delta_t^*}$) and aggressive market orders (crossing spread at rate $\nu_t^*$ with temporary impact $\eta \nu_t^*$) to liquidate inventory $Q_0$ by horizon $T$.

2. **Wave 272: Guéant & Lehalle (2015) General Intensity Models for Optimal Liquidation (`src/desk/gueantlehalle2015intensity/`)**
   - Solves Hamilton-Jacobi-Bellman ODEs for optimal ask reservation spread $\delta^*(t, q)$ under general exponential-power execution intensity $\Lambda(\delta) = A (1 + \frac{\kappa}{\beta} \delta)^{-\beta}$ and CARA risk aversion $\gamma$.

3. **Wave 273: Bouchaud, Gefen, Potters & Wyart (2004) Fluctuations and Response in Financial Markets (`src/desk/bouchaud2004response/`)**
   - Computes bare lag-$\ell$ propagator kernel $G_0(\ell) = \Gamma_0 (\ell + \ell_0)^{-\beta}$, trade sign autocorrelation $C(\ell) = C_0 \ell^{-\gamma}$, and lag-$\ell$ price response function $R(\ell)$ alongside diffusivity $D(\ell)$.

4. **Barrel & Vitest Suite**:
   - Export in `src/desk/index.ts`
   - `tests/unit/desk/waves_271_273_suite.test.ts`
