# Dual-Track Plan: Maritime Auxiliary Automation Batch 14 (Phases 515–518) & Quantitative Desk Waves 283–285

**Date:** 2026-10-14
**Status:** In Progress

## Track 1: Maritime Auxiliary Automation Batch 14 (Phases 515–518, `mekong-cli`)

All modules strictly $< 85\text{ LOC}$, deterministic, zero mocks.

1. **Phase 515: Anchor Windlass Chain Cable Payout Velocity, Bitter End & Hawsepipe Wash Interlock (IACS UR A1 & SOLAS II-1)**
   - File: `src/core/maritime/phase_515_anchor_windlass_payout_brake.py`
   - Evaluates free-fall / walk-back chain cable payout velocity ($\le 6.0\text{ m/s}$ safe envelope, runaway chain band brake auto-clamp trip $> 7.5\text{ m/s}$), remaining shackles in chain locker ($\le 1.5\text{ shackles}$ bitter-end tension pin alarm), and hawsepipe mud-box flushing water pressure ($\ge 2.0\text{ bar}$ during heaving).

2. **Phase 516: Main Switchboard 440V/6.6kV Earth Fault Insulation Monitoring & Preferential Trip Load Shedding (SOLAS II-1 Reg 41 & IACS UR E11)**
   - File: `src/core/maritime/phase_516_switchboard_insulation_load_shed.py`
   - Evaluates live AC bus insulation resistance to hull ($> 1.0\text{ M}\Omega$ nominal, earth fault warning $< 0.2\text{ M}\Omega$, critical ground fault $< 0.05\text{ M}\Omega$) and generator bus kW overload preferential trip stages ($> 100\%$ Stage 1 galley/HVAC shed at $5\text{ s}$, $> 110\%$ Stage 2 non-essential deck machinery shed).

3. **Phase 517: Stern Ramp & Bow Visor Hydraulic Locking Cleat & Watertight Seal Integrity (SOLAS II-1 Reg 15-1 & IACS UR S8/S9)**
   - File: `src/core/maritime/phase_517_bow_visor_stern_ramp_cleat.py`
   - Evaluates Ro-Ro shell door / bow visor proximity indicators (all hydraulic cleats locked before vessel leaves berth), pneumatic hollow rubber gasket seal pressure ($\ge 2.5\text{ bar}$), and inner collision door sea-water leakage bilge well float alarm.

4. **Phase 518: Accommodation Elevator Machinery Space Smoke, Over-Speed Governor & Sea-State Roll Lockout (SOLAS II-1 & EN 81-41 / ISO 8383 Marine Lifts)**
   - File: `src/core/maritime/phase_518_marine_elevator_roll_governor.py`
   - Evaluates vessel heavy-weather roll angle ($\ge 15.0^\circ$ automatic homing to embarkation deck & door park lockout to prevent guide-shoe derailment), hoistway smoke detection emergency recall, and mechanical safety gear governor overspeed trip ($\ge 115\%$ rated speed).

5. **Coordinator, CLI & Tests**:
   - `src/core/maritime_safety_auxiliary_batch14_engine.py`
   - `src/cli/commands/maritime_safety_auxiliary_batch14_command.py` (`maritime-aux14` / `phukienhanghai14`)
   - Registration in `src/cli/app_setup.py`
   - `tests/test_maritime_phases_515_518_suite.py`

## Track 2: Quantitative Desk Models Waves 283–285 (`algo-trader`)

All modules strictly $< 85\text{ LOC}$, zero `:any` types, pure TypeScript math.

1. **Wave 283: Alfonsi, Fruth & Schied (2010) Optimal Execution Strategies in Limit Order Books with General Shape Functions (`src/desk/alfonsifruthschied2010shape/`)**
   - Models non-linear order book density shape function $f(x)$ (exponential/power book resilience) where a discrete block trade $x_k$ shifts the volume measure $E_{t^+} = E_t + x_k$ and price displacement $D_{t^+}$, computing optimal initial & intermediate U-shaped block trades vs continuous interior rate.

2. **Wave 284: Cartea, Jaimungal & Penalva (2015) Statistical Arbitrage and Pairs Trading with Execution Cost (`src/desk/carteajaimungal2015statarb/`)**
   - Solves optimal dynamic inventory holdings $q_t^*$ for a co-integrated Ornstein-Uhlenbeck spread $dX_t = \kappa_X(\theta - X_t)dt + \sigma_X dW_t$ subject to quadratic temporary market impact $\eta \nu_t^2$ and running inventory risk $\phi q_t^2$.

3. **Wave 285: Cont, Kukanov & Stoikov (2014) The Price Impact of Order Book Events (`src/desk/contkukanovstoikov2014ofi/`)**
   - Computes high-frequency Order Flow Imbalance $\text{OFI}_k = \sum_{n} e_n$ from L1 bid/ask price and size changes $(P^b_n, q^b_n, P^a_n, q^a_n)$ and estimates the inverse market depth coefficient $\beta_{\text{OFI}}$ linking $\Delta P_k = \beta_{\text{OFI}} \cdot \text{OFI}_k + \epsilon_k$.

4. **Barrel & Vitest Suite**:
   - Export in `src/desk/index.ts`
   - `tests/unit/desk/waves_283_285_suite.test.ts`
