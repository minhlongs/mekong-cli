# Dual-Track Plan: Maritime Auxiliary Automation Batch 13 (Phases 511–514) & Quantitative Desk Waves 280–282

**Date:** 2026-10-14
**Status:** In Progress

## Track 1: Maritime Auxiliary Automation Batch 13 (Phases 511–514, `mekong-cli`)

All modules strictly $< 85\text{ LOC}$, deterministic, zero mocks.

1. **Phase 511: Main Engine Scavenge Air Receiver Condensation Water Drain & Cooler Carryover Control (IACS UR M10 & MAN B&W / WinGD Rules)**
   - File: `src/core/maritime/phase_511_scavenge_air_condensate_drain.py`
   - Evaluates ambient relative humidity dewpoint condensation vs scavenge air receiver temperature ($T_{\text{scav}} < T_{\text{dew}} + 3.0^\circ\text{C}$ undercooling alarm causing cylinder liner oil film washing), condensate collector float drain trap level ($\ge 80.0\%$ blocked trap alarm), and water mist catcher carryover differential pressure.

2. **Phase 512: Shipboard Hospital Medical Oxygen & Nitrous Oxide Cylinder Manifold Pressure & Leak Alarm (SOLAS II-1 & WHO/ILO IMGS Ship's Medicine Chest Guidelines)**
   - File: `src/core/maritime/phase_512_medical_oxygen_manifold_safety.py`
   - Evaluates primary duty cylinder bank pressure ($< 35.0\text{ bar}$ auto-changeover to reserve bank), line delivery pressure ($4.0\text{--}5.0\text{ bar}$ nominal, low line pressure alarm $< 3.5\text{ bar}$), and storage locker ambient oxygen enrichment leak detector ($\ge 23.5\%\text{ O}_2$ fire hazard extraction boost & isolation trip).

3. **Phase 513: Mooring Winch Hydraulic Brake Holding Capacity & Render-Recover Tension Control (OCIMF MEG4 & ISO 3730)**
   - File: `src/core/maritime/phase_513_mooring_winch_brake_render.py`
   - Evaluates split-drum first-layer brake holding load ($60.0\%$ of Minimum Breaking Load $\text{MBL}$ nominal, never exceeding $80.0\%\text{ MBL}$ per OCIMF MEG4), auto-tension surging line render warning ($\ge 55.0\%\text{ MBL}$), and hydraulic brake band wear sensor interlock.

4. **Phase 514: Engine Room Fixed Local Application Water-Mist Fire Fighting System (SOLAS II-2 Reg 10.5.6 & IMO MSC/Circ.1387)**
   - File: `src/core/maritime/phase_514_water_mist_local_application.py`
   - Evaluates dual-coincidence flame + smoke/heat detection over machinery hotspots (ME cylinder tops, Aux Gen fuel flats, purifier room, boiler fronts; single detector triggers pre-alarm only, dual coincidence opens section solenoid valve & starts high-pressure mist pump at $\ge 80.0\text{ bar}$) without shutting down main propulsion or evacuating the engine room.

5. **Coordinator, CLI & Tests**:
   - `src/core/maritime_safety_auxiliary_batch13_engine.py`
   - `src/cli/commands/maritime_safety_auxiliary_batch13_command.py` (`maritime-aux13` / `phukienhanghai13`)
   - Registration in `src/cli/app_setup.py`
   - `tests/test_maritime_phases_511_514_suite.py`

## Track 2: Quantitative Desk Models Waves 280–282 (`algo-trader`)

All modules strictly $< 85\text{ LOC}$, zero `:any` types, pure TypeScript math.

1. **Wave 280: Almgren (2012) Optimal Trading with Stochastic Liquidity and Volatility (`src/desk/almgren2012stochasticliq/`)**
   - Models optimal execution when temporary market impact parameter $\eta_t$ follows mean-reverting dynamics $d\eta_t = \kappa_\eta(\bar{\eta} - \eta_t)dt + \xi dZ_t$, adjusting the trading rate $\nu_t^*$ to accelerate in high-liquidity (low $\eta_t$) windows and slow down during liquidity droughts.

2. **Wave 281: Cartea & Jaimungal (2016) Incorporating Order-Flow into Optimal Execution (`src/desk/carteajaimungal2016orderflow/`)**
   - Solves the optimal execution trajectory when net market order flow $\mu_t = \lambda^+_t - \lambda^-_t$ follows an Ornstein-Uhlenbeck process $d\mu_t = -\kappa_\mu \mu_t dt + \sigma_\mu dW^\mu_t$, deriving the closed-form forward-looking order-flow alpha integral.

3. **Wave 282: Gatheral (2010) No-Dynamic-Arbitrage and Market Impact Decay Power-Law Bounds (`src/desk/gatheral2010nodarb/`)**
   - Evaluates the joint admissibility condition $\gamma + \beta \ge 1$ between non-linear instantaneous trade size impact $f(v) = v^\delta$ and power-law transient decay kernel $G(\tau) = \tau^{-\gamma}$ to detect round-trip price manipulation vulnerabilities.

4. **Barrel & Vitest Suite**:
   - Export in `src/desk/index.ts`
   - `tests/unit/desk/waves_280_282_suite.test.ts`
