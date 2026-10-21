# Dual-Track Plan: Maritime Auxiliary Automation Batch 16 (Phases 523–526) & Quantitative Desk Waves 289–291

**Date:** 2026-10-14
**Status:** Complete

## Brainstorm Contract (`/ak-brainstorm --deep`)
- **Outcome:** Deliver Maritime Auxiliary Automation Batch 16 (Phases 523–526) in `mekong-cli` and Quantitative Desk Models Waves 289–291 in `algo-trader`.
- **Constraints:** All modules strictly $< 85\text{ LOC}$, deterministic math/statutory logic, zero mocks, zero `:any` types.
- **Non-goals:** Modifying unrelated CLI groups or external network webhooks.
- **Acceptance Criteria:** `pytest` 6/6 green (`ruff` clean) in `mekong-cli` and `vitest` 3/3 green in `algo-trader`.

## Track 1: Maritime Auxiliary Automation Batch 16 (Phases 523–526, `mekong-cli`)

1. **Phase 523: Main Engine Torsional Vibration Damper & Barred Speed Range (BSR) Control (IACS UR M68 & MAN B&W / WinGD)**
   - File: `src/core/maritime/phase_523_torsional_vibration_bsr_damper.py`
   - Evaluates shaft RPM against the Barred Speed Range ($42.0\text{--}54.0\text{ RPM}$), enforces fast-passage boost inside the BSR, triggers governor slowdown/leave-BSR trip when BSR dwell time reaches $\ge 25.0\text{ s}$, and alarms on torsional shear stress $\ge 45.0\text{ MPa}$ or damper silicone/oil temperature $\ge 90.0^\circ\text{C}$.

2. **Phase 524: Bridge Navigational Watch Alarm System (BNWAS) Dead-Man Cascade (IMO Res. MSC.128(75) & SOLAS V/19.2.2.3)**
   - File: `src/core/maritime/phase_524_bnwas_watch_alarm_cascade.py`
   - Supervises dormant period ($180\text{--}720\text{ s}$) and three-stage dead-man alarm cascade: Stage 1 bridge visual/audible alert at $T_d$, Stage 2 backup officer cabin call at $T_d + 15.0\text{ s}$, and Stage 3 shipwide emergency alarm at $T_d + 105.0\text{ s}$.

3. **Phase 525: Paint & Flammable Liquid Locker Explosion-Proof Vent & Water-Spray Interlock (SOLAS II-2 Reg 10.6.3 & IEC 60092)**
   - File: `src/core/maritime/phase_525_paint_locker_vent_waterspray.py`
   - Releases fixed water-spray deluge and closes fire dampers on fire detection, isolates power at $\ge 20.0\%\text{ LEL}$, and de-energizes Ex-lighting when ventilation falls below $6.0\text{ ACH}$ or the exhaust fan stops.

4. **Phase 526: Accommodation Ladder & Gangway Winch Inclination, SWL & Stowage Safety (SOLAS II-1 Reg 3-9, MSC.1/Circ.1331 & ISO 5488)**
   - File: `src/core/maritime/phase_526_accommodation_ladder_winch_safety.py`
   - Locks out lowering and engages mechanical pawl when inclination exceeds $55.0^\circ$, live load exceeds rated SWL, or the ladder is unstowed at vessel speed $> 0.5\text{ kn}$.

5. **Coordinator, CLI & Tests**:
   - `src/core/maritime_safety_auxiliary_batch16_engine.py`
   - `src/cli/commands/maritime_safety_auxiliary_batch16_command.py` (`maritime-aux16` / `phukienhanghai16`)
   - Registration in `src/cli/app_setup.py`
   - `tests/test_maritime_phases_523_526_suite.py`

## Track 2: Quantitative Desk Models Waves 289–291 (`algo-trader`)

1. **Wave 289: Gatheral & Schied (2011) Optimal Trade Execution under Geometric Brownian Motion (`src/desk/gatheralschied2011gbm/`)**
   - Computes optimal execution urgency $\kappa = \sqrt{\frac{\lambda \sigma^2 S_0^2}{\eta}}$, initial execution velocity $v_0 = \frac{\kappa X_0}{\tanh(\kappa T)}$, mid-horizon inventory $X_{T/2}$, and total expected cost under GBM dollar-variance risk aversion.

2. **Wave 290: Cartea, Donnelly & Jaimungal (2017) Algorithmic Trading with Model Uncertainty (`src/desk/carteadonnellyjaimungal2017uncertainty/`)**
   - Computes ambiguity-adjusted urgency $\tilde{\kappa} = \sqrt{\frac{\phi_{\text{inv}} + 0.5 \phi_{\text{drift}} \sigma^2}{\eta}}$, worst-case drift shift $-\phi_{\text{drift}} \sigma^2 q_t$, and robust liquidation rate vs the ambiguity-neutral baseline.

3. **Wave 291: Alfonsi, Schied & Slynko (2012) Order Book Resilience and Positive Portfolio Execution (`src/desk/alfonsischiedslynko2012positive/`)**
   - Solves discrete execution weights for a convex resilience decay kernel $G(|t_i - t_j|)$ and verifies the Positive Portfolio Property ($\min_i x_i > 0$, absence of price manipulation).

4. **Barrel & Vitest Suite**:
   - Export in `src/desk/index.ts`
   - `tests/unit/desk/waves_289_291_suite.test.ts`
