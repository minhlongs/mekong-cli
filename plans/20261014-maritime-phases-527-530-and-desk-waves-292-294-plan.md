# Dual-Track Plan: Maritime Auxiliary Automation Batch 17 (Phases 527–530) & Quantitative Desk Waves 292–294

**Date:** 2026-10-14
**Status:** Complete

## Brainstorm Contract (`/ak-brainstorm --deep`)
- **Outcome:** Deliver Maritime Auxiliary Automation Batch 17 (Phases 527–530) in `mekong-cli` and Quantitative Desk Models Waves 292–294 in `algo-trader`, completing both Batch 16/17 and Waves 289–294.
- **Constraints:** All code files strictly $< 85\text{ LOC}$, deterministic zero-mock verification, zero `:any` types in TypeScript, full bilingual CLI aliases.
- **Non-goals:** Touching unrelated CLI funnels or external APIs.
- **Acceptance Criteria:** `pytest` 12/12 green across Batch 16 & Batch 17 (`ruff` 0 errors) and `vitest` 6/6 green across Waves 289–291 & Waves 292–294.

## Track 1: Maritime Auxiliary Automation Batch 17 (Phases 527–530, `mekong-cli`)

1. **Phase 527: Main Engine Cylinder Lubricator Alpha/Pulse Feed-Rate & Sulfur-Adaptive TBN Dosing Control (IACS UR M10 & MAN B&W ACC / WinGD)**
   - File: `src/core/maritime/phase_527_cylinder_lubricator_alpha_dosage.py`
   - Evaluates sulfur-proportional ACC feed rate ($\ge 0.60\text{ g/kWh}$ minimum floor), fuel sulfur vs cylinder oil Base Number mismatch (high-sulfur acid corrosion risk or ULSFO high-BN calcium deposit risk), and quill non-return flow sensor fault.

2. **Phase 528: Engine Room Bilge Holding Tank Oil-Water Interface & High-Level Overfill Alarm (MARPOL Annex I Reg 16/17 & IACS UR M24)**
   - File: `src/core/maritime/phase_528_bilge_holding_tank_interface.py`
   - Supervises bilge holding tank capacity ($\ge 80.0\%$ OWS auto-start, $\ge 90.0\%$ high-level alarm, $\ge 95.0\%$ overfill transfer lock), oil-layer interface thickness ($\ge 250.0\text{ mm}$ sludge skimming), and heating coil temperature ($> 70.0^\circ\text{C}$ vapor flash warning).

3. **Phase 529: Cargo Hold Fixed Smoke Detection Sample Extraction & Three-Way CO2 Valve Supervision (SOLAS II-2 Reg 7.2 & FSS Code Ch. 10)**
   - File: `src/core/maritime/phase_529_cargo_smoke_extraction_fan_supervision.py`
   - Supervises extraction fan suction differential pressure ($< 80.0\text{ Pa}$ standby fan auto-cut-in), sampling line smoke obscuration ($\ge 2.0\%\text{/m}$ pre-alarm, $\ge 4.0\%\text{/m}$ hold fire alarm), and 3-way selector valve fault.

4. **Phase 530: Free-Fall Lifeboat Hydraulic Release Hook, Ramp Securing Pin & Thruster Interlock (SOLAS III Reg 16/20 & LSA Code Ch. IV 4.7)**
   - File: `src/core/maritime/phase_530_freefall_lifeboat_release_interlock.py`
   - Enforces removal of harbor maintenance securing pins at sea ($> 1.0\text{ kn}$), hydraulic primary release pressure ($\ge 150.0\text{ bar}$), and boarding hatch/seat harness readiness.

5. **Coordinator, CLI & Tests**:
   - `src/core/maritime_safety_auxiliary_batch17_engine.py`
   - `src/cli/commands/maritime_safety_auxiliary_batch17_command.py` (`maritime-aux17` / `phukienhanghai17`)
   - Registration in `src/cli/app_setup.py`
   - `tests/test_maritime_phases_527_530_suite.py`

## Track 2: Quantitative Desk Models Waves 292–294 (`algo-trader`)

1. **Wave 292: Guéant (2017) Optimal Market Making with Inventory and Terminal Penalty (`src/desk/gueant2017optimalmm/`)**
   - Computes asymptotic closed-form bid/ask half-spreads $\delta^b(q), \delta^a(q)$ and inventory reservation skew under exponential order fill intensity $\Lambda(\delta) = A e^{-k\delta}$.

2. **Wave 293: Cartea & Jaimungal (2015) Hybrid Limit and Market Order Execution (`src/desk/carteajaimungal2015hybrid/`)**
   - Computes the optimal regime switch and aggressive market order sweep rate when inventory urgency $\phi q_t$ exceeds the passive limit fill benefit $\lambda_{\text{fill}} \Delta_{\text{spread}}$.

3. **Wave 294: Gatheral, Jaisson & Rosenbaum (2018) Rough Heston Fractional Kernel Discretization (`src/desk/gatheraljaisson2018heston/`)**
   - Evaluates the discrete fractional Volterra kernel weights $K(\tau_j) = \frac{\tau_j^{H-1/2}}{\Gamma(H+1/2)}$ for $H \in (0, 0.5)$ and computes rough variance memory concentration.

4. **Barrel & Vitest Suite**:
   - Export in `src/desk/index.ts`
   - `tests/unit/desk/waves_292_294_suite.test.ts`
