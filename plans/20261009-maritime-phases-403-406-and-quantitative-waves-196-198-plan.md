# Architectural Design and Implementation Plan: Maritime Phases 403-406 & Quantitative Desk Waves 196-198

**Date:** 2026-10-09  
**Authors:** Senior Quantitative Financial Engineer & Chief Naval Architect / Maritime Systems Architect  
**Targets:**
- Track 1: `mekong-cli` — Maritime Advanced Engineering AH (Phases 403-406)
- Track 2: `algo-trader` — Quantitative Desk Triad (Waves 196-198)

---

## Executive Summary & CTO Advisory Review

This document provides the formal architectural design, physical/mathematical formulations, and implementation roadmap for:
1. **Track 1 (`mekong-cli`):** Marine Bilge Water Separator & ODMCS (Phase 403), Marine Inert Gas System & N2 Generator (Phase 404), Marine Stern Tube Bearing Lubrication & Bio-oil Sealing (Phase 405), and Marine High-Fog / Water Mist Local Extinguishing System (Phase 406). Includes Master Facade, Typer CLI with 8 bilingual aliases, and FastMCP tool endpoints.
2. **Track 2 (`algo-trader`):** Carr-Madan (1998) Static Replication of Barrier Options (Wave 196), Madan-Carr-Chang (1998) Variance Gamma Process & Option Pricing (Wave 197), and Joel Hasbrouck (1991) VAR/VECM Microstructure & Information Content (Wave 198).

### Architectural Constraints & Quality Gates
- **Line Count Guards:** All Python files in `mekong-cli` strictly `< 200 LOC`. All TypeScript files in `algo-trader` strictly `< 180 LOC`.
- **Zero Mocks:** Pure analytical physics, thermodynamic balances, PDE/SDE discretizations, and numerical linear algebra.
- **Type Safety:** Python 3.11+ type annotations with Dataclasses and Enums; TypeScript with 0 `:any`, 0 `unknown` without guard, strict null checks, and 0 `console.log`.

---

## Behavioral Checklist & Assumption Analysis

### 1. Assumptions Challenged

#### Maritime Engineering (Track 1)
- **Assumption 1: Pure Stokes Settling in Bilge Water Separation (Phase 403)**  
  *Challenge:* Relying solely on unhindered Stokes settling ($v = rac{2}{9}rac{\Delta ho}{\mu}g R^2$) assumes rigid spherical oil droplets in laminar flow ($Re < 1$) within a quiescent continuous medium. In modern machinery spaces, surfactant-stabilized emulsions (detergents, cleaning solvents) create micro-droplets ($d < 10\,\mu	ext{m}$) where buoyant force is balanced by Brownian motion and interfacial tension. Without active coalescence modeling and secondary adsorption/filtration stages, an unhindered Stokes model dramatically overestimates separation efficiency and fails to predict realistic 15 ppm ASD trip frequencies.  
  *Correction:* Couple Stokes gravity separation with a coalescer efficiency factor and secondary polishing stage filter pressure-drop dynamics.

- **Assumption 2: Static Membrane Selectivity in N2 Generation (Phase 404)**  
  *Challenge:* Assuming constant oxygen/nitrogen permeability ratios across variable intake air temperatures and pressures ignores Arrhenius temperature dependence and membrane compaction. Higher ambient compressor discharge temperatures drastically degrade selectivity, leading to dangerous $O_2 > 5\%$ off-spec gas entering cargo tanks.  
  *Correction:* Implement temperature- and feed-pressure-dependent permeability curves with automated waste-vent interlocks.

- **Assumption 3: Perpetual Hydrodynamic Full-Film Lubrication in Stern Tube Bearings (Phase 405)**  
  *Challenge:* Assuming the bearing operating parameter $\lambda = h_{	ext{min}}/\sigma > 3$ holds globally ignores low-speed harbor maneuvering, shaft turning gear operation, and shaft deflection induced by heavy propeller overhang. At Sommerfeld numbers $S < 0.05$, the system drops into mixed or boundary friction regimes.  
  *Correction:* Model the Stribeck transition curve with viscosity-temperature compensation (Walther-ASTM) and hydrostatic header tank differential pressure ($\Delta P_{	ext{seal}} = P_{	ext{lube}} - P_{	ext{draft}} \in [0.15, 0.30]\,	ext{bar}$).

- **Assumption 4: Monodisperse Water Mist Droplet Evaporation (Phase 406)**  
  *Challenge:* Utilizing an average Sauter mean diameter ($D_{32}$) ignores the log-normal distribution ($D_{99} < 100/300\,\mu	ext{m}$). Coarse droplets fall out prematurely while ultra-fine droplets get swept away by compartment thermal updrafts.  
  *Correction:* Model dual droplet regimes (cooling momentum vs rapid latent heat volumetric expansion 1:1600) with oxygen depletion rate calculations.

#### Quantitative Microstructure & Derivatives (Track 2)
- **Assumption 5: Continuous Strike Continuum in Carr-Madan Static Replication (Wave 196)**  
  *Challenge:* The Carr-Madan spanning identity $H(S_T) = H(S_*) + H'(S_*)(S_T - S_*) + \int_0^{S_*} H''(K)(K - S_T)^+ dK + \int_{S_*}^\infty H''(K)(S_T - K)^+ dK$ assumes an infinite, continuous strip of vanilla options. In reality, exchange-traded options (Deribit/CBOE) exist on discrete, irregular strike grids with wide bid-ask spreads in deep out-of-the-money wings. Standard trapezoidal quadrature diverges near barrier discontinuities without strike mesh clustering.  
  *Correction:* Implement piecewise linear/quadratic payoff interpolation and strike-weight regularization with boundary-matching reflection parity.

- **Assumption 6: Grid Independence in Variance Gamma FFT Pricing (Wave 197)**  
  *Challenge:* Standard Carr-Madan FFT pricing links strike step $\Delta k$ and frequency step $\Delta v$ by the reciprocity relation $\Delta k \cdot \Delta v = 2\pi / N$. For short maturities ($T < 0.1$), the VG characteristic function decays slowly, inducing severe aliasing and truncation errors unless $N \ge 4096$, which creates excessive memory overhead.  
  *Correction:* Employ direct 32-point Gauss-Kronrod or adaptive Simpson quadrature on the damped Gil-Pelaez inversion integral, providing machine-precision pricing in sub-millisecond execution without grid entanglement.

- **Assumption 7: Homoskedastic Noise & Fixed Lag Length in Hasbrouck VAR (Wave 198)**  
  *Challenge:* Assuming a fixed VAR lag order $p$ across liquid and illiquid trading sessions produces over-fitting during quiet regimes and under-captures autocorrelation during high-frequency microbursts. Furthermore, treating trade signs $x_t \in \{-1, +1\}$ as exogenous ignores signed volume and hidden order execution.  
  *Correction:* Formulate the bivariate VAR system with signed volume weighting and compute information share via Cholesky orthogonalization of permanent random walk variance.

---

### 2. Alternatives Surfaced & Trade-off Quantification

| System | Option A (Dismissed / Naive) | Option B (Balanced Industrial Standard) | Option C (Elite Continuous Engine - Selected) |
| :--- | :--- | :--- | :--- |
| **Track 1: Bilge & ODMCS (403)** | Single-tank gravity separation with static 15 ppm threshold comparator. | Dual-stage separator with empirical oil-content lookup table. | **Hydrodynamic Stokes Settling + Coalescer Differential Permeability + Non-Volatile Ring Buffer Audit Logger.** |
| *Trade-offs* | Complexity: O(1). Latency: <1ms. Physics: Unrealistic (fails on emulsions). | Complexity: Moderate. Latency: 2ms. Calibration: Fragile across oil grades. | **Complexity: Moderate. Latency: <5ms. Maintainability: High. Deterministic certification compliant with MEPC.108(49).** |
| **Track 1: Inert Gas & N2 (404)** | Linear oxygen dilution model with fixed compressor delivery. | Empirical pressure swing adsorption (PSA) cycle simulation. | **Hollow-Fiber Solution-Diffusion Membrane Model + Dual-Zone P/V Breaker Liquid Seal Hydrostatics.** |
| *Trade-offs* | Complexity: Low. Safety: Inadequate (fails SOLAS II-2 Reg 4.5.5). | Complexity: High. Cycle states: Excessive state space for real-time CLI. | **Complexity: High. Latency: <3ms. Maintainability: High. Rigorous thermodynamic & explosion limit verification.** |
| **Track 1: Stern Tube & EAL (405)** | Hydrostatic draft table with static oil level check. | Empirical Sommerfeld lookup with fixed mineral oil properties. | **Thermo-Viscous Walther-ASTM Model + Reynolds Hydrodynamic Film ($\lambda > 3$) + EPA VGP Bio-Degradation Degradation.** |
| *Trade-offs* | Complexity: Low. Wear prediction: None. Seal integrity: Blind. | Complexity: Moderate. Viscosity: Inaccurate across operational temps (0°C to 70°C). | **Complexity: High. Latency: <2ms. Maintainability: Clean. Prevents cat-fines wear & seawater ingress.** |
| **Track 1: Water Mist (406)** | Total water volume / area rule-of-thumb discharging. | Static NFPA 750 nozzle discharge coefficient formula. | **Droplet Size Evaporative Kinetics + Latent Heat Thermal Flash (1:1600) + MSC.1165 Compartment Smothering Model.** |
| *Trade-offs* | Complexity: Trivial. Physics: No steam expansion or cooling tracking. | Complexity: Low. Droplet spectrum: Ignores droplet coalescence and flash steam. | **Complexity: Moderate. Latency: <2ms. Maintainability: High. Deterministic flame quenching validation.** |
| **Track 2: Carr-Madan Replic. (196)** | Naive discrete delta-hedging simulation with rebalancing costs. | Pure European call/put portfolio matching via Black-Scholes inversion. | **Static Spanning Formula with Piecewise Payoff Regularization & Discrete Strike Calibration.** |
| *Trade-offs* | Complexity: High. Latency: >50ms. Transaction costs: Path dependent. | Complexity: Low. Exotic boundaries: Severe leakage at barrier strikes. | **Complexity: Moderate. Latency: <1ms. Maintainability: High. Analytical replication without delta-rebalance slippage.** |
| **Track 2: Variance Gamma (197)** | Monte Carlo simulation with subordinated gamma time-steps. | Standard Carr-Madan 4096-point FFT with fixed spacing reciprocity. | **Closed-Form Characteristic Function + Adaptive Gil-Pelaez Simpson Quadrature + Method of Moments Calibration.** |
| *Trade-offs* | Complexity: High. Latency: >100ms. Variance: Noisy. | Complexity: High. Latency: 5ms. Memory: High grid allocation; short-dated aliasing. | **Complexity: Moderate. Latency: <1.5ms. Maintainability: High. Machine precision across entire volatility smile.** |
| **Track 2: Hasbrouck VAR (198)** | Univariate OLS of midpoint returns on contemporaneous order sign. | Unconstrained VAR(p) with heuristic lag selection. | **Bivariate Structural VAR(p) with Signed Volume Weighting & Permanent/Transitory Cholesky Variance Decomposition.** |
| *Trade-offs* | Complexity: Low. Microstructure: Fails to separate permanent vs transitory impact. | Complexity: High. Latency: 10ms. Numerical: Matrix collinearity on high lags. | **Complexity: High. Latency: <3ms. Maintainability: High. Quantifies Hasbrouck information share ($R_w^2$) rigorously.** |

---

### 3. Second-Order Effects & Downstream Consequences

1. **Environmental & Port State Control (PSC) Sanctions (Track 1 - 403):**  
   If the Bilge Water Separator engine incorrectly validates discharge under high emulsion conditions, oil droplets $< 15\,\mu	ext{m}$ escape into coastal waters. Real-world consequences: Vessel detention by PSC, US Coast Guard criminal prosecution under the Act to Prevent Pollution from Ships (APPS), and $5M+ fines. The engine's non-volatile ring buffer logging is legally audited.
2. **Explosion Hazard in Cargo Tanks (Track 1 - 404):**  
   Under-predicting membrane degradation leads to feeding inert gas with $O_2 > 5\%$ into hydrocarbon-vapor-filled ullage spaces. If the P/V breaker freezes or liquid level drops, overpressure ruptures cargo tank bulkheads, or vacuum implodes deck plating.
3. **Propeller Shaft Seizure & Sterntube Catastrophe (Track 1 - 405):**  
   EAL bio-lubricants are susceptible to ester hydrolysis under seawater contamination ($> 1000\,	ext{ppm}$). Hydrolysis produces free fatty acids, lowering pH, destroying bearing white metal (babbitt), and accelerating boundary friction wear ($\lambda < 1$).
4. **Machinery Space Flash Fires (Track 1 - 406):**  
   Premature activation of local water mist with droplet sizes $> 300\,\mu	ext{m}$ causes thermal shock cracking on engine cylinder heads and turbocharger casings without suffocating diesel spray fires. High-pressure droplet atomization ($D_{99} < 100\,\mu	ext{m}$) must guarantee rapid flash boiling and steam displacement without splashing flaming fuel.
5. **Exotic Barrier Arbitrage & P&L Blowup (Track 2 - 196):**  
   Approximating barrier replication weights without strike regularization creates localized synthetic negative prices near the barrier strike, producing phantom arbitrage signals and excessive margin drawdowns.
6. **Calibration Non-Convexity & Regime Shifting (Track 2 - 197):**  
   Variance Gamma parameter estimation via unconstrained optimization can yield non-martingale drift compensator arguments ($1 - 	heta
u - rac{1}{2}\sigma^2
u \le 0$). The implementation must enforce strict parameter bounds: $
u > 0$, $\sigma > 0$, and $	heta \in \left(-\infty, rac{1}{
u} - rac{\sigma^2}{2}ight)$.
7. **Order Flow Toxicity & Inventory Depletion (Track 2 - 198):**  
   Misclassifying transitory inventory bounces as permanent informational price revisions leads market-making algorithms to widen spreads excessively or withdraw liquidity during informed trading cascades.

---

### 4. Simplest Viable Options Identified
- **Track 1:** 4 deterministic single-purpose engine classes implementing exact analytical balances, wrapped by a unified facade with immutable dataclass inputs/outputs.
- **Track 2:** Functional/class TypeScript modules separating pure math/matrix operators from trading execution engines, ensuring testability without external runtime dependencies.

---

## Technical Track 1: Maritime Advanced Engineering AH (`mekong-cli`)

### Phase 403: Marine Bilge Water Separator & ODMCS
- **Regulatory Framework:** MARPOL 73/78 Annex I, Regulations 14, 31 & 32; IMO Resolutions MEPC.108(49), MEPC.240(65).
- **Physical & Mathematical Model:**
  - Stokes' Settling Velocity for Oil Droplet Rise:
    $$v_s = rac{2}{9} rac{(ho_w - ho_o)}{\mu_w} g R_d^2$$
    where $ho_w pprox 1025\,	ext{kg/m}^3$ (seawater), $ho_o pprox 880	ext{--}991\,	ext{kg/m}^3$ (fuel/lube oil), $\mu_w pprox 1.05 	imes 10^{-3}\,	ext{Pa}\cdot	ext{s}$, $g = 9.80665\,	ext{m/s}^2$, and $R_d$ is droplet radius ($10	ext{--}100\,\mu	ext{m}$).
  - Coalescence Plate Separator Efficiency:
    $$\eta_{	ext{grav}} = 1 - \exp\left(-rac{v_s \cdot A_{	ext{eff}}}{Q_{	ext{bilge}}}ight)$$
    where $A_{	ext{eff}}$ is total projected plate area and $Q_{	ext{bilge}}$ is flow rate ($	ext{m}^3/	ext{h}$).
  - 15 ppm Overboard Discharge Interlock:
    $$C_{	ext{oil,out}} = C_{	ext{oil,in}} \cdot (1 - \eta_{	ext{grav}}) \cdot (1 - \eta_{	ext{coal}})$$
    - If $C_{	ext{oil,out}} \le 15.0\,	ext{ppm}$: 3-Way Overboard Solenoid Valve `OPEN`.
    - If $C_{	ext{oil,out}} > 15.0\,	ext{ppm}$: Automatic Stopping Device (ASD) trip; valve switches immediately to `RECIRCULATE_TO_HOLDING_TANK`.
  - Non-Volatile Oil Discharge Monitoring & Control (ODMCS) Logging:
    - Minimum 18-month audit record containing: UTC timestamp, GPS latitude/longitude, oil concentration (ppm), instantaneous discharge rate ($	ext{L/h}$), ship speed (knots), and overboard valve position.

### Phase 404: Marine Inert Gas System & N2 Generator
- **Regulatory Framework:** SOLAS II-2 Reg 4.5.5; IMO FSS Code Chapter 15; USCG 46 CFR Part 32.
- **Physical & Thermodynamic Model:**
  - Hollow-Fiber Membrane Permeation Kinetics:
    $$J_i = rac{P_i}{l} (p_{f} x_{i} - p_{p} y_{i})$$
    where $P_{O_2} / P_{N_2} pprox 4	ext{--}6$ (selectivity ratio), $p_f$ is feed pressure ($6	ext{--}10\,	ext{bar}$), $p_p$ is permeate pressure ($1\,	ext{bar}$).
  - Nitrogen Purity & Oxygen Mass Fraction:
    $$C_{O_2,	ext{IGS}} = f(T_{	ext{feed}}, P_{	ext{feed}}, Q_{	ext{feed}})$$
    - Normal Operation: $C_{O_2} < 5.0\%\,	ext{vol}$.
    - Alarm Threshold: $C_{O_2} \ge 5.0\%\,	ext{vol}$.
    - Safety Trip (Automatic Venting to Atmosphere & Cargo Isolation): $C_{O_2} \ge 8.0\%\,	ext{vol}$.
  - Deck Water Seal & P/V Breaker Hydrostatics:
    $$\Delta P_{	ext{deck seal}} = ho_{	ext{water}} \cdot g \cdot h_{	ext{seal}} \ge 250\,	ext{mmWG} \quad (2.45\,	ext{kPa})$$
    $$\Delta P_{	ext{pv,pos}} \le +2400\,	ext{mmWG} \quad (+23.5\,	ext{kPa}), \quad \Delta P_{	ext{pv,neg}} \ge -800\,	ext{mmWG} \quad (-7.85\,	ext{kPa})$$

### Phase 405: Marine Stern Tube Bearing Lubrication & Bio-oil Sealing
- **Regulatory Framework:** DNV-RU-SHIP Pt.4 Ch.2; US EPA Vessel General Permit (VGP) Section 2.2.9 (Environmentally Acceptable Lubricants - EALs).
- **Physical & Tribological Model:**
  - Viscosity-Temperature Dependence (Walther-ASTM D341):
    $$\log_{10}(\log_{10}(
u + 0.7)) = A - B \log_{10}(T_K)$$
  - Hydrodynamic Lubrication Regime (Sommerfeld Number & Film Parameter):
    $$S = \left(rac{R}{c}ight)^2 rac{\mu N}{P_{	ext{proj}}}, \quad h_{	ext{min}} = c (1 - \epsilon)$$
    $$\lambda = rac{h_{	ext{min}}}{\sqrt{\sigma_{	ext{journal}}^2 + \sigma_{	ext{bearing}}^2}}$$
    - Full-film hydrodynamic regime: $\lambda \ge 3.0$ (Zero metallic contact).
    - Mixed lubrication alert: $1.0 \le \lambda < 3.0$.
    - Boundary friction critical trip: $\lambda < 1.0$.
  - Sealing Pressure Differential (Forward & Aft Lip Seals):
    $$\Delta P_{	ext{aft seal}} = P_{	ext{lube header}} - P_{	ext{seawater draft}} \in [0.15, 0.30]\,	ext{bar}$$
  - EAL Biodegradability & Water Ingress Monitoring:
    - Water contamination limit: $\le 1000\,	ext{ppm}$ ($0.10\%$). Alarm at $> 1500\,	ext{ppm}$.
    - Total Acid Number (TAN) delta: $\Delta 	ext{TAN} \le 0.5\,	ext{mg KOH/g}$.

### Phase 406: Marine High-Fog / Water Mist Local Extinguishing System
- **Regulatory Framework:** SOLAS II-2 Reg 10.5.6; IMO MSC/Circ.1165; NFPA 750 Standard on Water Mist Fire Protection Systems.
- **Physical & Thermodynamic Model:**
  - Droplet Diameter Spectrum:
    $$D_{99} \le 100\,\mu	ext{m} \quad (	ext{Total Flooding}), \quad D_{99} \le 300\,\mu	ext{m} \quad (	ext{Local Application})$$
  - Latent Heat of Vaporization & Volumetric Flash Expansion:
    $$Q_{	ext{cool}} = \dot{m}_{	ext{mist}} \left( c_{p,w}(100^\circ	ext{C} - T_{	ext{ambient}}) + L_v ight), \quad L_v pprox 2257\,	ext{kJ/kg}$$
    $$	ext{Expansion Ratio} = rac{ho_{	ext{water}}}{ho_{	ext{steam}}(100^\circ	ext{C})} pprox 1673 : 1$$
  - Oxygen Depletion Rate in Enclosed Machinery Fire Plume:
    $$X_{O_2}(t) = 0.209 \left(1 - rac{V_{	ext{steam}}(t)}{V_{	ext{compartment}}}ight) \le 0.13	ext{--}0.15 \quad (	ext{Flame extinction})$$
  - Discharge Nozzle Hydraulics:
    $$Q = K \sqrt{P}, \quad P \in [70, 140]\,	ext{bar} \quad (K	ext{-factor } pprox 1.2	ext{--}3.5\,	ext{L/min/bar}^{0.5})$$

---

## Technical Track 2: Quantitative Desk Triad (`algo-trader`)

### Wave 196: Carr-Madan (1998) Static Replication of Barrier Options
- **Mathematical Spanning Identity:**
  Every European payoff $H(S_T)$ with continuous second derivative can be statically synthesized by cash, forward contracts, and an out-of-the-money continuum of put and call options:
  $$H(S_T) = H(S_*) + H'(S_*)(S_T - S_*) + \int_0^{S_*} H''(K) (K - S_T)^+ dK + \int_{S_*}^\infty H''(K) (S_T - K)^+ dK$$
  where $S_*$ is an arbitrary reference strike (typically current forward price $F$).
- **Barrier Option Static Replication via Reflection Principle:**
  For an Up-and-Out or Down-and-Out barrier option with barrier $B$, match the boundary condition $H(B, t) = 0$ along the boundary $S = B$ for all $t \in [0, T]$.
  Using the method of images:
  $$H_{	ext{barrier}}(S_T) = H(S_T) - \left(rac{S_T}{B}ight)^{1 - 2r/\sigma^2} H\left(rac{B^2}{S_T}ight)$$
  - Static replicate portfolio decomposed into weights $w(K_i)$ on discrete strikes $K_i$:
    $$w(K_i) pprox rac{H''(K_i) \Delta K_i}{1}$$
  - Enforce strike boundary regularization to prevent infinite weights at the barrier strike.

### Wave 197: Madan-Carr-Chang (1998) Variance Gamma (VG) Process
- **Stochastic Specification:**
  Returns modeled as a Brownian motion with drift $	heta$ and diffusion $\sigma$, evaluated at a random time given by an independent Gamma process with mean rate $1$ and variance $
u$:
  $$X_t = 	heta \gamma_t(
u) + \sigma W_{\gamma_t(
u)}$$
  where $\gamma_t \sim 	ext{Gamma}(t/
u, 
u)$.
- **Characteristic Function:**
  $$\phi_{X_t}(u) = \mathbb{E}\left[e^{i u X_t}ight] = \left( 1 - i u 	heta 
u + rac{1}{2} \sigma^2 
u u^2 ight)^{-t/
u}$$
  Risk-neutral asset price: $S_t = S_0 \exp\left((r - q + \omega)t + X_tight)$, where drift compensator:
  $$\omega = rac{1}{
u} \ln\left(1 - 	heta 
u - rac{1}{2}\sigma^2 
uight)$$
- **Analytical Moments:**
  $$	ext{Mean} = 	heta t, \quad 	ext{Variance} = (\sigma^2 + 
u 	heta^2)t$$
  $$	ext{Skewness} = rac{	heta 
u (3\sigma^2 + 2
u 	heta^2)}{(\sigma^2 + 
u 	heta^2)^{3/2} \sqrt{t}}$$
  $$	ext{Kurtosis} = 3 + 3
u rac{2\sigma^4 + 4
u \sigma^2 	heta^2 + 
u^2 	heta^4}{(\sigma^2 + 
u 	heta^2)^2 t}$$
- **Option Pricing via Adaptive Gil-Pelaez Inversion:**
  $$C(S_0, K, T) = S_0 e^{-q T} \Pi_1 - K e^{-r T} \Pi_2$$
  $$\Pi_j = rac{1}{2} + rac{1}{\pi} \int_0^\infty 	ext{Re}\left( rac{e^{-i u \ln K} \phi_j(u)}{i u} ight) du$$
  Integrated via 32-node Gauss-Kronrod / Simpson quadrature without FFT grid constraints.

### Wave 198: Joel Hasbrouck (1991) VAR/VECM Microstructure & Information Content
- **Bivariate Structural VAR System:**
  Decompose quote revisions (midpoint returns $r_t$) and signed trade order flows ($x_t$):
  $$r_t = \sum_{i=1}^p lpha_i r_{t-i} + \sum_{i=0}^p eta_i x_{t-i} + \epsilon_{1,t}$$
  $$x_t = \sum_{i=1}^p \gamma_i r_{t-i} + \sum_{i=1}^p \phi_i x_{t-i} + \epsilon_{2,t}$$
  where $\epsilon_{1,t}$ is the unpredicted quote revision and $\epsilon_{2,t}$ is the unexpected trade innovation.
- **VECM Moving Average Representation & Permanent Price Impact:**
  Inverting the VAR yields the vector moving average:
  $$egin{pmatrix} r_t \ x_t \end{pmatrix} = egin{pmatrix} a(L) & b(L) \ c(L) & d(L) \end{pmatrix} egin{pmatrix} \epsilon_{1,t} \ \epsilon_{2,t} \end{pmatrix}$$
  The permanent price impact of a trade innovation of size $x$:
  $$I_{	ext{perm}} = \sum_{j=0}^\infty b_j = b(1)$$
- **Hasbrouck Information Share ($R_w^2$):**
  Decomposing price into a permanent random walk component $m_t$ and a transitory noise component $s_t$:
  $$p_t = m_t + s_t, \quad \sigma_w^2 = 	ext{Var}(\Delta m_t)$$
  $$\sigma_w^2 = [1 + a(1)]^2 \sigma_{\epsilon 1}^2 + [b(1)]^2 \sigma_{\epsilon 2}^2 + 2[1 + a(1)] b(1) \sigma_{\epsilon 1, \epsilon 2}$$
  The trade-correlated information share:
  $$R_w^2 = rac{\sigma_{w,x}^2}{\sigma_w^2} \in [0, 1]$$
  Quantifies exactly how much permanent variance is attributable to private information conveyed through order flow.

---

## File Architecture & LOC Budget Allocation

### Track 1: `mekong-cli`
All files reside in `/Users/macbook/mekong-cli/` and are strictly `< 200 LOC`:

1. `src/core/maritime/phase_403_bilge_water_separator_odmcs.py` (~150 LOC)
   - `BilgeSeparatorEngine`, `BilgeInput`, `BilgeResult`, `ASDValveStatus`
2. `src/core/maritime/phase_404_inert_gas_n2_generator.py` (~155 LOC)
   - `InertGasEngine`, `InertGasInput`, `InertGasResult`, `IGSSafetyStatus`
3. `src/core/maritime/phase_405_stern_tube_bio_lubrication.py` (~160 LOC)
   - `SternTubeEngine`, `SternTubeInput`, `SternTubeResult`, `LubricationRegime`
4. `src/core/maritime/phase_406_water_mist_fire_extinguishing.py` (~150 LOC)
   - `WaterMistEngine`, `WaterMistInput`, `WaterMistResult`, `MistDischargeStatus`
5. `src/core/maritime_bilge_inertgas_sterntube_watermist_engine.py` (~140 LOC)
   - `MaritimeBilgeInertGasSternTubeWaterMistEngine` (Unified Master Facade)
6. `src/cli/commands/maritime_bilge_inertgas_sterntube_watermist_command.py` (~175 LOC)
   - 4 Typer apps with 8 bilingual aliases (`bilgeseparator`/`tachnuocdaytau`, `inertgas`/`khitro`, `sterntube`/`ongbaotruc`, `watermist`/`suongmuphongchay`)
7. Registration in `src/cli/app_setup.py` (~25 LOC addition)
8. Registration of 4 FastMCP tools in `scripts/mcp_server.py` (~80 LOC addition)
9. Zero-mock unit & integration test suite in `tests/test_maritime_phases_403_406_unit_suite.py` (~190 LOC)

### Track 2: `algo-trader`
All files reside in `/Users/macbook/algo-trader/` and are strictly `< 180 LOC`, 0 `:any`, 0 `console.log`:

1. `src/desk/carrmadan/carr-madan-static-types.ts` (~80 LOC)
2. `src/desk/carrmadan/carr-madan-static-math.ts` (~130 LOC)
3. `src/desk/carrmadan/carr-madan-static-engine.ts` (~145 LOC)
4. `src/desk/variancegamma/variance-gamma-moments-types.ts` (~80 LOC)
5. `src/desk/variancegamma/variance-gamma-moments-math.ts` (~140 LOC)
6. `src/desk/variancegamma/variance-gamma-moments-engine.ts` (~155 LOC)
7. `src/desk/hasbrouck/hasbrouck-vecm-types.ts` (~90 LOC)
8. `src/desk/hasbrouck/hasbrouck-vecm-math.ts` (~145 LOC)
9. `src/desk/hasbrouck/hasbrouck-vecm-engine.ts` (~160 LOC)
10. `tests/unit/desk/carrmadan/carr-madan-static.test.ts` (~120 LOC)
11. `tests/unit/desk/variancegamma/variance-gamma-moments.test.ts` (~130 LOC)
12. `tests/unit/desk/hasbrouck/hasbrouck-vecm.test.ts` (~140 LOC)

---

## Detailed Implementation Steps

### Step 1: Track 1 Core Physics & Maritime Engines (`mekong-cli`)
- Implement `phase_403_bilge_water_separator_odmcs.py`: Stokes settling with droplet radius, water viscosity temperature curve, plate coalescer geometry, 15 ppm ASD trip, and 18-month non-volatile logging simulator.
- Implement `phase_404_inert_gas_n2_generator.py`: Solution-diffusion hollow-fiber permeability, $O_2$ concentration calculation, deck water seal anti-backflow head, and P/V breaker vacuum/overpressure safety trips.
- Implement `phase_405_stern_tube_bio_lubrication.py`: Walther-ASTM viscosity, Sommerfeld number, film thickness parameter $\lambda$, header tank draft differential $\Delta P \in [0.15, 0.30]\,	ext{bar}$, and EPA VGP bio-lubricant degradation alarms.
- Implement `phase_406_water_mist_fire_extinguishing.py`: Droplet size distribution ($D_{99} < 100/300\,\mu	ext{m}$), high-pressure K-factor nozzle hydraulics, latent heat cooling capacity, steam expansion ratio (1:1600), and $O_2$ flame smothering time.

### Step 2: Track 1 Central Facade, CLI & MCP Server (`mekong-cli`)
- Implement `maritime_bilge_inertgas_sterntube_watermist_engine.py`: Single call evaluating all 4 auxiliary systems with consolidated safety score and alarms.
- Implement `maritime_bilge_inertgas_sterntube_watermist_command.py`: Clean Rich tables, interactive Typer options, bilingual help strings.
- Wire into `src/cli/app_setup.py`: Register 8 bilingual aliases (`bilgeseparator`, `tachnuocdaytau`, `inertgas`, `khitro`, `sterntube`, `ongbaotruc`, `watermist`, `suongmuphongchay`).
- Wire into `scripts/mcp_server.py`: Expose `mekong_maritime_bilge_separator_evaluate`, `mekong_maritime_inert_gas_evaluate`, `mekong_maritime_stern_tube_evaluate`, `mekong_maritime_water_mist_evaluate`.
- Run pytest suite: `python3 -m pytest tests/test_maritime_phases_403_406_unit_suite.py -v`.

### Step 3: Track 2 Quantitative Desk Triad Engines (`algo-trader`)
- Implement Wave 196 (Carr-Madan Static Replication): Spanning formula weights on discrete strikes, reflection principle boundary weights for barrier claims, and hedging tracking error quantification.
- Implement Wave 197 (Variance Gamma Moments & Surface): Analytical skewness/kurtosis formulas, method-of-moments inversion from empirical return series, and Gil-Pelaez adaptive quadrature pricer.
- Implement Wave 198 (Hasbrouck VECM & Information Content): Bivariate OLS estimation, VMA impulse response function, permanent random walk variance decomposition, and Hasbrouck information share $R_w^2$.
- Run vitest suite: `cd /Users/macbook/algo-trader && npx vitest run tests/unit/desk/carrmadan/ tests/unit/desk/variancegamma/ tests/unit/desk/hasbrouck/`.

---

## Verification & Validation Criteria

### Track 1 Acceptance Tests
1. **Phase 403:** Bilge oil concentration $> 15.0\,	ext{ppm}$ triggers `ASDValveStatus.RECIRCULATE` within $< 1.0\,	ext{s}$ simulation time, with log entry recorded.
2. **Phase 404:** Inert gas $O_2 \ge 5.0\%$ raises `ALARM`, and $O_2 \ge 8.0\%$ triggers `SAFETY_TRIP_VENTING`; P/V breaker trips if pressure exceeds $+2400\,	ext{mmWG}$ or falls below $-800\,	ext{mmWG}$.
3. **Phase 405:** Bearing film parameter $\lambda \ge 3.0$ yields `FULL_FILM_HYDRODYNAMIC`; water ingress $> 1000\,	ext{ppm}$ or seal differential $< 0.15\,	ext{bar}$ raises critical maintenance alarms.
4. **Phase 406:** High-fog water mist generates steam expansion $pprox 1600:1$, reducing local $O_2$ below $14\%$ within rated extinguishing time when $P \ge 70\,	ext{bar}$.
5. **App Wiring:** CLI returns exit code 0 on all 8 aliases; MCP endpoints return valid JSON dictionaries.

### Track 2 Acceptance Tests
1. **Wave 196:** Replicated portfolio matches European vanilla call payoff within $< 10^{-3}$ maximum absolute error across liquid strike strip. Barrier reflection weights identically cancel out payoff at barrier boundary $S = B$.
2. **Wave 197:** VG kurtosis strictly exceeds 3.0 for all $
u > 0$. Method of moments recovers ground truth parameters $(\sigma, 
u, 	heta)$ from simulated VG paths within $5\%$ tolerance. Gil-Pelaez option price obeys Put-Call parity within $10^{-5}$.
3. **Wave 198:** Permanent price impact $I_{	ext{perm}} > 0$ for positive buy volume shock. Hasbrouck information share $R_w^2 \in [0, 1]$ and increases monotonically with trade order flow informativeness.
4. **Strict Quality:** 100% green tests, 0 TypeScript errors (`npx tsc --noEmit`), 0 lint warnings.
