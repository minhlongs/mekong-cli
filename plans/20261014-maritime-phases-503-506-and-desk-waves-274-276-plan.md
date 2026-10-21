# Dual-Track Plan: Maritime Auxiliary Automation Batch 11 (Phases 503–506) & Quantitative Desk Waves 274–276

**Date:** 2026-10-14
**Status:** In Progress

## Track 1: Maritime Auxiliary Automation Batch 11 (Phases 503–506, `mekong-cli`)

All modules strictly $< 90\text{ LOC}$, deterministic, zero mocks.

1. **Phase 503: Hull Impressed Current Cathodic Protection (ICCP) Reference Electrode & Anode Shield Current Control (IACS UR Z3 & ISO 13174)**
   - File: `src/core/maritime/phase_503_iccp_hull_potential_anode.py`
   - Evaluates Ag/AgCl reference electrode hull potential ($-800\text{ to }-900\text{ mV}$ optimal protection window, under-protection corrosion alarm $> -750\text{ mV}$, over-protection hydrogen embrittlement / dielectric shield disbondment trip $< -1050\text{ mV}$), and thyristor rectifier anode output current limit.

2. **Phase 504: Marine Growth Prevention System (MGPS) Sea Chest Electrolytic Cu/Al Anode Dosing (IACS UR M14 & ClassNK Rules)**
   - File: `src/core/maritime/phase_504_mgps_sea_chest_dosing.py`
   - Evaluates copper bio-fouling anti-mussel anode current density ($2.0\text{ ppb}$ target concentration, low-flow sea chest stagnant gas accumulation trip when cooling seawater flow $< 25.0\text{ m}^3/\text{h}$), aluminum/ferrous anti-corrosion flocculation current, and anode depletion end-of-life voltage rise ($> 14.5\text{ V}$).

3. **Phase 505: Accommodation HVAC Galley Exhaust Fire Damper & Smoke Extraction Interlock (SOLAS II-2 Reg 9.7.5 & ISO 7547)**
   - File: `src/core/maritime/phase_505_hvac_galley_fire_damper.py`
   - Evaluates galley range hood grease duct temperature ($> 70.0^\circ\text{C}$ pre-alarm, $\ge 74.0^\circ\text{C}$ fusible link / pneumatic fire damper snap-closure & extraction fan trip), fixed CO2/wet-chemical galley hood extinguishing release, and accommodation recirculation smoke detector fresh-air purge mode.

4. **Phase 506: Provision Refrigeration Plant Brine Chiller, Defrost & Refrigerant Leak Safety (IACS UR M15 & ISO 5149)**
   - File: `src/core/maritime/phase_506_provision_reefer_leak_safety.py`
   - Evaluates machinery space refrigerant gas concentration ($\ge 300\text{ ppm}$ pre-alarm activating emergency mechanical extraction ventilation, $\ge 1000\text{ ppm}$ solenoid liquid line pump-down trip & personnel trapped-in-chamber audiovisual alarm), meat room $-18.0^\circ\text{C}$ / vegetable room $+4.0^\circ\text{C}$ setpoint tracking, and compressor high discharge head cutout ($\ge 22.0\text{ bar}$).

5. **Coordinator, CLI & Tests**:
   - `src/core/maritime_safety_auxiliary_batch11_engine.py`
   - `src/cli/commands/maritime_safety_auxiliary_batch11_command.py` (`maritime-aux11` / `phukienhanghai11`)
   - Registration in `src/cli/app_setup.py`
   - `tests/test_maritime_phases_503_506_suite.py`

## Track 2: Quantitative Desk Models Waves 274–276 (`algo-trader`)

All modules strictly $< 85\text{ LOC}$, zero `:any` types, pure TypeScript math.

1. **Wave 274: Gatheral, Jaisson & Rosenbaum (2018) Volatility is Rough: Fractional Kernel Estimation (`src/desk/gatheraljaisson2018rough/`)**
   - Estimates Hurst exponent $H \in (0, 0.5)$ via $q$-th absolute moment scaling $m(q, \Delta) = \frac{1}{N} \sum |\log \sigma_{t+\Delta} - \log \sigma_t|^q \propto \Delta^{q H}$ and forecasts rough log-volatility via fractional kernel weights.

2. **Wave 275: Cartea, Donnelly & Jaimungal (2018) Enhancing Trading Strategies with Order Book Signals (`src/desk/carteadonnelly2018signals/`)**
   - Computes multi-level weighted volume order book imbalance (VOI) across $L$ depths with exponential depth decay $w_\ell = e^{-\alpha (\ell-1)}$ and derives signal-conditioned optimal execution skew.

3. **Wave 276: Cont, Stoikov & Talreja (2010) A Stochastic Model for Order Book Dynamics (`src/desk/contstoikov2010book/`)**
   - Computes Birth-Death-Cancellation Laplace-transform conditional probabilities that the mid-price moves up before moving down (and that the best bid depletes before the best ask) given level-1 queue depths $(q_b, q_a)$, limit arrival rate $\lambda$, market sweep rate $\mu$, and cancellation rate $\theta$.

4. **Barrel & Vitest Suite**:
   - Export in `src/desk/index.ts`
   - `tests/unit/desk/waves_274_276_suite.test.ts`
