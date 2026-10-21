# Deep Brainstorming: Maritime Phases 399-402 & Quantitative Waves 193-195

**Date:** 2026-10-09  
**Status:** Architecture Blueprint & Implementation Specification  
**Constraints:** Strictly < 180 LOC per file, zero mocks, real mathematical & physical models, zero `:any` types.

---

## Track 1: Maritime Automation Phases 399-402 (mekong-cli)

### Phase 399: Marine Bow Thruster Dynamic Thrust & Pitch Control
- **Standards:** SOLAS II-1 Reg 29, DNV-RU-SHIP Pt.4 Ch.5, ISO 484-1/2.
- **Hydrodynamic & Electro-Hydraulic Model:**
  - Net Lateral Thrust: $T_{\text{net}} = \rho \cdot A_{\text{tunnel}} \cdot v_e \cdot (v_e - v_0) \cdot (1 - \xi_{\text{grid}})$, where $\xi_{\text{grid}} \approx 0.08\text{--}0.12$ is the tunnel protective grid obstruction drag factor.
  - Cavitation Inception Number: $\sigma = \frac{P_{\text{amb}} - P_v}{0.5 \rho V_{\text{tip}}^2}$, alert when $\sigma < \sigma_{\text{crit}} \approx 0.40$ (risk of blade erosion & noise).
  - Hydraulic/VFD Power Curve: $P_{\text{mech}} = \frac{T \cdot v_e}{\eta_{\text{prop}}}$, motor kW load monitoring with automatic power limiting at $\ge 100\%$ MCR.
  - Safety Interlocks: High hydraulic oil temperature alarm at $75^\circ\text{C}$, shutdown trip at $85^\circ\text{C}$; header tank low level cutoff; low lube oil pressure trip ($< 2.5\text{ bar}$).

### Phase 400: Inflatable Liferaft & Hydrostatic Release Unit (HRU) Deployment
- **Standards:** SOLAS III Reg 13, 20, 31 & IMO LSA Code Chapter IV (Life-Saving Appliances).
- **Physics & Release Mechanics:**
  - Hydrostatic Pressure Actuation: Submersion depth $h \in [1.5, 4.0]\text{ m}$ ($P_{\text{water}} \approx 15.0\text{--}40.0\text{ kPa}$), triggering spring-loaded cutting blade (Hammar H20).
  - Weak Link Breaking Strain: Engineered weak link fails at $F_{\text{break}} = 2.2 \pm 0.4\text{ kN}$, allowing inflated liferaft to break free from sinking vessel.
  - Painter Line Kinematics: Length $L_{\text{painter}} \ge \max(15.0\text{ m}, H_{\text{stowage}} + 10.0\text{ m})$, dual-chamber $\text{CO}_2 / \text{N}_2$ gas aspiration inflation time $t_{\text{inflate}} \le 60\text{ s}$ at $18\text{--}20^\circ\text{C}$.
  - Service Life & Expiration: Automated tracking of HRU 2-year hydrostatic membrane service lifespan and liferaft annual service intervals.

### Phase 401: Shipboard Waste High-Temperature Incinerator & Plasma Gasification
- **Standards:** IMO MARPOL Annex V Reg 16 & Resolution MEPC.244(66) (Standard Specification for Shipboard Incinerators).
- **Combustion Thermodynamics & Emissions:**
  - Two-Stage Thermal Destruction:
    - Primary combustion chamber: $T_{\text{primary}} \in [850^\circ\text{C}, 950^\circ\text{C}]$ for solid waste / sludge oil vaporization.
    - Secondary afterburner chamber: $T_{\text{secondary}} \in [1000^\circ\text{C}, 1200^\circ\text{C}]$ with flue gas residence time $\tau \ge 1.0\text{ s}$ for complete dioxin/furan destruction.
  - Flue Gas Compliance: CO concentration $\le 200\text{ mg/MJ}$, excess oxygen $O_2 \in [6.0\%, 12.0\%]$, flue smoke density $\le \text{Ringelmann } 1$.
  - Interlocks: Automatic waste charging lockout if $T_{\text{primary}} < 850^\circ\text{C}$; induced draft fan differential pressure fail-safe; flame failure emergency fuel trip.

### Phase 402: Marine Closed Vapor Emission Control System (VECS / VRU) for Tankers
- **Standards:** IMO MSC/Circ.585 & USCG 46 CFR Part 39 (Vapor Control Systems).
- **Fluid & Tank Pressure Dynamics:**
  - Manifold Pressure / Vacuum Window: High pressure alarm at $+0.10\text{ bar}$, emergency venting at $+0.14\text{ bar}$; low vacuum alarm at $-0.020\text{ bar}$, vacuum breaker trip at $-0.035\text{ bar}$.
  - Overfill Level Protection: High-level audio/visual alarm at $95\%$ tank capacity; independent High-High level cargo pump shutdown at $98\%$ tank capacity.
  - Inert Gas Oxygen Limitation: $O_2$ in vapor manifold must remain $< 8.0\%\text{ vol}$ (flammable envelope prevention); automated cargo loading stop if $O_2 \ge 8.0\%$.
  - Detonation Flame Arrester: Maximum pressure drop $\Delta P_{\text{arrester}} \le 0.05\text{ bar}$, temperature monitoring across quenching elements.

---

## Track 2: Quantitative Desk Triad Waves 193-195 (algo-trader)

### Wave 193: Dupire (1994) Continuous Local Volatility Surface
- **Seminal Reference:** Bruno Dupire (1994), "Pricing with a Smile", *Risk Magazine*.
- **Formulation:**
  $$\sigma_{\text{loc}}^2(K, T) = \frac{\frac{\partial C}{\partial T} + (r - q)K \frac{\partial C}{\partial K} + q C}{\frac{1}{2}K^2 \frac{\partial^2 C}{\partial K^2}}$$
- **Arbitrage-Free Conditions:** Calendar spread monotonicity ($\partial_T w \ge 0$), butterfly arbitrage non-negativity ($\partial_K^2 C > 0$).
- **Modules:** `src/desk/dupire/` (`dupire-types.ts`, `dupire-math.ts`, `dupire-calibrator.ts`, `dupire-engine.ts`, `index.ts`).

### Wave 194: Bollerslev (1986) GARCH(1,1) & GJR-GARCH (1993) Asymmetric Volatility
- **Seminal References:** Bollerslev (1986) J. Econometrics; Glosten, Jagannathan, Runkle (1993) J. Finance.
- **Formulation:**
  $$\sigma_t^2 = \omega + (\alpha + \gamma \cdot \mathbf{1}_{\{\epsilon_{t-1} < 0\}}) \epsilon_{t-1}^2 + \beta \sigma_{t-1}^2$$
- **Stationarity & Forecast:** $\alpha + \beta + \gamma/2 < 1$; forward variance forecast $E_t[\sigma_{t+k}^2] = \sigma_{\text{uncond}}^2 + (\alpha + \beta + \gamma/2)^{k-1}(\sigma_{t+1}^2 - \sigma_{\text{uncond}}^2)$.
- **Modules:** `src/desk/garch/` (`garch-types.ts`, `garch-math.ts`, `garch-estimator.ts`, `garch-engine.ts`, `index.ts`).

### Wave 195: Biais-Hillion-Spatt (1995) Empirical LOB Microstructure
- **Seminal Reference:** Biais, Hillion, Spatt (1995), *Journal of Finance*.
- **Formulation:** 11-event taxonomy, Markov transition probability matrix $P_{ij} = \mathbb{P}(E_t = j \mid E_{t-1} = i)$, diagonal clustering persistence $\lambda_{ii}$, and conditional spread impact $\Delta S(E_t)$.
- **Modules:** `src/desk/biais/` (`biais-types.ts`, `biais-classifier.ts`, `biais-math.ts`, `biais-engine.ts`, `index.ts`).
