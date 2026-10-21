# Dual-Track Plan: Maritime Auxiliary Automation Batch 12 (Phases 507–510) & Quantitative Desk Waves 277–279

**Date:** 2026-10-14
**Status:** In Progress

## Track 1: Maritime Auxiliary Automation Batch 12 (Phases 507–510, `mekong-cli`)

All modules strictly $< 85\text{ LOC}$, deterministic, zero mocks.

1. **Phase 507: Shaft Grounding Slip Ring & Propeller Shaft Stray Current Spark Erosion Protection (IACS UR M10 & DNV Rules)**
   - File: `src/core/maritime/phase_507_shaft_grounding_slip_ring.py`
   - Evaluates silver-graphite brush to propeller shaft potential ($< 50.0\text{ mV}$ optimal earthing, brush wear warning $\ge 50.0\text{ mV}$, critical main bearing & thrust pad spark erosion alarm $\ge 100.0\text{ mV}$) and brush contact pressure / milliampere grounding continuity.

2. **Phase 508: Engine Room Bilge High-Level Flood Alarm & Emergency Bilge Direct Suction Valve Interlock (SOLAS II-1 Reg 35-1 & Reg 48)**
   - File: `src/core/maritime/phase_508_emergency_bilge_direct_suction.py`
   - Evaluates machinery space bilge well water level ($\ge 150.0\text{ mm}$ primary bilge pump auto-start, $\ge 350.0\text{ mm}$ SOLAS Reg 48 dual-independent flooding alarm, $\ge 600.0\text{ mm}$ catastrophic flooding opening emergency bilge direct suction injection valve on main seawater cooling pump while throttling sea chest inlet).

3. **Phase 509: Hydraulic Watertight Sliding Door Local/Remote Closure & Pinch Obstruction Safety (SOLAS II-1 Reg 13)**
   - File: `src/core/maritime/phase_509_watertight_sliding_door_safety.py`
   - Evaluates bridge master control mode ("LOCAL_CONTROL" vs "DOORS_CLOSED_AT_SEA"), stored hydraulic accumulator pressure ($\ge 160.0\text{ bar}$ nominal for 3 complete closures on blackout, low pressure alarm $< 145.0\text{ bar}$), closure transit time ($20.0\text{--}40.0\text{ s}$ SOLAS window), and personnel pinch strip re-open safety.

4. **Phase 510: Accommodation Helideck Foam Monitor Pop-Up Nozzle &Diffuser Fire System (SOLAS II-2 Reg 18 & ICAO Annex 14 / CAP 437)**
   - File: `src/core/maritime/phase_510_helideck_foam_monitor_system.py`
   - Evaluates deck-integrated pop-up nozzle manifold pressure ($\ge 7.0\text{ bar}$ nominal within $\le 15.0\text{ s}$ activation response), AFFF 3% foam proportioner induction ratio ($2.8\text{--}3.5\%$ nominal), and foam concentrate tank reserve capacity ($\ge 100\%$ for 5-minute continuous application rate at $6.0\text{ L/min/m}^2$).

5. **Coordinator, CLI & Tests**:
   - `src/core/maritime_safety_auxiliary_batch12_engine.py`
   - `src/cli/commands/maritime_safety_auxiliary_batch12_command.py` (`maritime-aux12` / `phukienhanghai12`)
   - Registration in `src/cli/app_setup.py`
   - `tests/test_maritime_phases_507_510_suite.py`

## Track 2: Quantitative Desk Models Waves 277–279 (`algo-trader`)

All modules strictly $< 85\text{ LOC}$, zero `:any` types, pure TypeScript math.

1. **Wave 277: Gatheral & Schied (2013) Dynamical Models of Market Impact and Predatory Trading (`src/desk/gatheralschied2013predatory/`)**
   - Models strategic interaction between a distressed liquidating trader ($Q_0$) and an opportunistic predatory trader under transient exponential price impact resilience $\rho$ and permanent impact $\gamma$, computing equilibrium liquidation cost inflation and predatory front-running profit.

2. **Wave 278: Avellaneda & Stoikov (2008) / Guéant, Lehalle & Fernandez-Tapia (2013) Closed-Form Asymptotic Market Making with Inventory Bounds (`src/desk/gueantlehalle2013mm/`)**
   - Computes closed-form asymptotic bid and ask quoting depths $(\delta_t^{b,*}, \delta_t^{a,*})$ and reservation price spreads under hard inventory risk caps $|q| \le Q_{\max}$ using exact CARA value function ratio coefficients $v_q$.

3. **Wave 279: Bouchaud, Farmer & Lillo (2009) How Markets Slowly Digest Changes in Supply and Demand (`src/desk/bouchaudfarmerlillo2009digest/`)**
   - Computes long-memory order-splitting metaorder square-root impact law $\Delta P(Q) = Y \sigma \sqrt{Q / V}$ followed by power-law post-execution relaxation decay toward permanent plateau $I_\infty$.

4. **Barrel & Vitest Suite**:
   - Export in `src/desk/index.ts`
   - `tests/unit/desk/waves_277_279_suite.test.ts`
