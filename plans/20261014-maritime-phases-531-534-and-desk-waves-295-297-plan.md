# Dual-Track Plan: Maritime Auxiliary Automation Batch 18 (Phases 531–534) & Quantitative Desk Waves 295–297

**Date:** 2026-10-14
**Status:** Complete

## Brainstorm Contract (`/ak-brainstorm --deep`)
- **Outcome:** Deliver Maritime Auxiliary Automation Batch 18 (Phases 531–534) in `mekong-cli` and Quantitative Desk Models Waves 295–297 in `algo-trader`.
- **Constraints:** All code files strictly $< 85\text{ LOC}$, deterministic zero-mock verification, zero `:any` types in TypeScript, full bilingual CLI aliases (`maritime-aux18` / `phukienhanghai18`).
- **Non-goals:** Touching unrelated CLI funnels or external APIs.
- **Acceptance Criteria:** `pytest` 6/6 green for Batch 18 (`ruff` 0 errors) and `vitest` 3/3 green for Waves 295–297.

## Track 1: Maritime Auxiliary Automation Batch 18 (Phases 531–534, `mekong-cli`)

1. **Phase 531: Main Engine High-Pressure Double-Walled Fuel Pipe Leakage & Quick-Closing Valve Interlock (SOLAS II-2 Reg 4.2.2.5.2 & IACS UR M10 / M75)**
   - File: `src/core/maritime/phase_531_double_wall_fuel_pipe_leak.py`
   - Supervises jacketed HP fuel pipe annular pressure ($\ge 1.5\text{ bar}$) and drain collection tank level ($\ge 35.0\%$ weeping pre-alarm, $\ge 80.0\%$ rupture slowdown trip), SOLAS II-2 Reg 4.2.2.6 hot surface shielding temperature ($> 220.0^\circ\text{C}$), and service tank quick-closing valve (QCV) pneumatic reserve ($< 4.5\text{ bar}$).

2. **Phase 532: Inert Gas Generator (IGG) Combustion Chamber Stoichiometry, O2 Analyzer & Scrubber Cooling Tower Supervision (SOLAS II-2 Reg 4.5.5 & IMO FSS Code Ch. 15)**
   - File: `src/core/maritime/phase_532_inert_gas_generator_stoichiometry.py`
   - Supervises IGG delivered flue gas oxygen concentration ($\le 5.0\%$ nominal, $> 5.0\%$ alarm, $\ge 8.0\%$ deck isolation & atmosphere vent trip), scrubber outlet gas temperature ($> 65.0^\circ\text{C}$) / cooling water pressure ($< 1.5\text{ bar}$), and burner stoichiometry equivalence ratio ($\lambda \in [0.95, 1.15]$).

3. **Phase 533: Stern Tube Air-Guard Seal Pressure Balance & Biodegradable EAL Lube Oil Header Supervision (IACS UR M10, VGP EAL & ClassNK / DNV Rules)**
   - File: `src/core/maritime/phase_533_stern_tube_airguard_seal_balance.py`
   - Supervises aft air-barrier seal overpressure margin ($\Delta P_{\text{air-sea}} \ge 0.10\text{ bar}$ minimum, $0.20\text{--}0.35\text{ bar}$ target), aft seal air consumption ($> 45.0\text{ NL/min}$ ring wear warning), and biodegradable EAL lube oil water emulsification ($\ge 1.0\%$) / bearing temperature ($\ge 65.0^\circ\text{C}$).

4. **Phase 534: Enclosed Space Entry Fixed Multi-Gas Sampling & Mechanical Ventilation Interlock (SOLAS XI-1 Reg 7 & IMO Res. A.1050(27))**
   - File: `src/core/maritime/phase_534_enclosed_space_entry_gas_interlock.py`
   - Enforces safe entry atmosphere ($\text{O}_2 \in [20.8\%, 21.5\%]$, $\text{LEL} < 1.0\%$, $\text{CO} < 20.0\text{ ppm}$, $\text{H}_2\text{S} < 5.0\text{ ppm}$) and pre-entry mechanical ventilation purge ($\ge 30.0\text{ min}$ at $\ge 10.0\text{ ACH}$) before unlocking the enclosed space entry permit interlock.

5. **Coordinator, CLI & Tests**:
   - `src/core/maritime_safety_auxiliary_batch18_engine.py`
   - `src/cli/commands/maritime_safety_auxiliary_batch18_command.py` (`maritime-aux18` / `phukienhanghai18`)
   - Registration in `src/cli/app_setup.py`
   - `tests/test_maritime_phases_531_534_suite.py`

## Track 2: Quantitative Desk Models Waves 295–297 (`algo-trader`)

1. **Wave 295: Gatheral & Schied (2013) Dynamical Models of Market Impact (`src/desk/gatheralschied2013dynamical/`)**
   - Computes coupled transient exponential resilience impact and permanent price drift, verifying round-trip manipulation non-negativity.

2. **Wave 296: Cartea, Jaimungal & Kinzebulatov (2016) FX Triplet Cross-Rate Arbitrage (`src/desk/carteajaimungal2016fxtriplet/`)**
   - Computes logarithmic triangular FX mispricing $M_t = \ln(S^{XY}_t S^{YZ}_t / S^{XZ}_t)$, optimal mean-reverting execution rates, and inventory-penalized cross-rate skew.

3. **Wave 297: Bouchaud, Gefen, Potters & Wyart (2004) Long-Memory Propagator & Diffusive Variance (`src/desk/bouchaud2004propagator/`)**
   - Computes the critical propagator exponent $\beta^* = (1 - \gamma)/2$ from order-flow sign memory exponent $\gamma \in (0, 1)$, bare impact decay, and diffusive variance stability ratio.

4. **Barrel & Vitest Suite**:
   - Export in `src/desk/index.ts`
   - `tests/unit/desk/waves_295_297_suite.test.ts`
