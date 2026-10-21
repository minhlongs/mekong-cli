# Deep Brainstorming: Maritime Phases 443–446 & Quantitative Desk Waves 226–228

## Overview
Continuous dual-track autonomous delivery:
1. **Track 1 (`mekong-cli`)**: Maritime Automation Physical Engineering (Phases 443–446)
   - Phase 443: Cargo Tank Deepwell Submerged Pump Hydraulic Header Pressure & Stripping Interlock (FRAMO)
   - Phase 444: Nitrogen PSA Inert Gas Membrane Purity & Low-Pressure Buffer Interlock (IMO FSS Code Ch.15)
   - Phase 445: Cargo Hold Toxic H2S Gas Detection & Vapor Extraction Fan Safety Interlock (IMSBC / ISGOTT)
   - Phase 446: Double-Bottom Fuel Tank Emergency High-Level Radar Overfill Protection (MARPOL Annex I Reg 12A)
2. **Track 2 (`algo-trader`)**: Institutional Quantitative Trading Models (Waves 226–228)
   - Wave 226: Mastromatteo, Toth & Bouchaud (2014) Agent-Based Linear Impact Models
   - Wave 227: Gatheral & Wang (2012) Dynamic Optimal Execution under Transient Market Impact
   - Wave 228: Almgren (2003) Optimal Execution with Non-Linear Power-Law Impact Functions

---

## Track 1: Maritime Automation Physical Engineering

### Phase 443: Cargo Deepwell Hydraulic & Stripping Interlock (FRAMO)
- **Standard**: OCIMF & SOLAS II-2 Reg 4, DNV-RU-SHIP Pt.4 Ch.6.
- **Physical Dynamics**:
  - Hydraulic ring main supply pressure $P_{\text{hyd}} \in [220.0, 260.0]\,\text{bar}$. Alarm $< 190.0\,\text{bar}$, trip $< 160.0\,\text{bar}$.
  - Hydraulic return line backpressure $P_{\text{ret}} \le 25.0\,\text{bar}$ (overpressure trip $> 35.0\,\text{bar}$ prevents seal blowout).
  - Cofferdam purge pressure and leakage detection: purge flow $\le 0.5\,\text{L/min}$; hydraulic oil ingress or cargo ingress triggers trip.
  - Stripping pump cavitation prevention: suction pressure head $\ge 0.15\,\text{bar}$.

### Phase 444: Nitrogen PSA Inert Gas Membrane Purity & Buffer Interlock
- **Standard**: IMO MSC.98(73) FSS Code Ch.15 & SOLAS II-2 Reg 4.5.5.
- **Physical Dynamics**:
  - Nitrogen product purity: Oxygen content $O_2 \le 5.0\%\,\text{vol}$ (alarm $> 4.0\%$, dump valve opens to atmosphere if $> 5.0\%$).
  - Membrane feed air pressure $P_{\text{feed}} \in [7.0, 10.0]\,\text{bar}$; inlet air temperature $T_{\text{in}} \in [35.0, 50.0]^\circ\text{C}$ for membrane efficiency.
  - Feed air dew point $T_{\text{dew}} \le -40.0^\circ\text{C}$ (refrigerated/desiccant dryer alarm $> -35.0^\circ\text{C}$).
  - Buffer tank pressure $P_{\text{buff}} \in [6.0, 8.5]\,\text{bar}$; low buffer pressure trip $< 4.5\,\text{bar}$.

### Phase 445: Cargo Hold Toxic H2S Gas Detection & Vapor Extraction Fan Safety
- **Standard**: IMO MSC.268(85) IMSBC Code & ISGOTT Ch.2.
- **Physical Dynamics**:
  - Toxic Hydrogen Sulfide concentration: $\text{H}_2\text{S} \le 5.0\,\text{ppm}$ (TLV-TWA). Warning at $> 5.0\,\text{ppm}$, evacuation & emergency extraction trip at $> 10.0\,\text{ppm}$.
  - Combustible Lower Explosive Limit: $\text{LEL} \le 10.0\%$ (trip lockout at $> 20.0\%$).
  - Extraction fan differential pressure $\Delta P_{\text{fan}} \ge 250.0\,\text{Pa}$ confirming airflow velocity $\ge 12.0\,\text{m/s}$.
  - Spark-proof ATEX airflow temperature $T_{\text{ex}} \le 60.0^\circ\text{C}$.

### Phase 446: Double-Bottom Fuel Tank Radar Overfill Protection
- **Standard**: SOLAS II-1 Reg 20, MARPOL Annex I Reg 12A & USCG 46 CFR 39.2009.
- **Physical Dynamics**:
  - FMCW radar gauge continuous sounding: High level alarm at $95.0\%$ volumetric capacity.
  - Independent acoustic/vibrating-fork high-high alarm at $98.0\%$ volumetric capacity.
  - Auto-closure of bunker manifold valve within $\le 30.0\,\text{seconds}$ on $98\%$ level trip to prevent hydrostatic hull rupture.
  - Vent pipe expansion trunk pressure $P_{\text{vent}} \in [-10.0, +25.0]\,\text{mbar}$.

---

## Track 2: Institutional Quantitative Trading Desk

### Wave 226: Mastromatteo, Toth & Bouchaud (2014) Agent-Based Linear Impact
- **Dynamics**:
  - Emergence of linear/square-root impact from order flow coordination and latent liquidity clearance.
  - Equilibrium spread $\Delta$ and clearing price impact:
    $I_{\text{ABM}}(Q) = \lambda \frac{Q}{\sqrt{V_0 \cdot \tau}} \cdot \left(1 + \frac{\rho_a}{1 - \rho_a}\right)$
  - Excess order accumulation causing liquidity breakdown if order imbalance ratio $\Omega = \frac{|Q_{\text{buy}} - Q_{\text{sell}}|}{Q_{\text{total}}} > \Omega_{\text{crit}}$.

### Wave 227: Gatheral & Wang (2012) Transient Market Impact
- **Dynamics**:
  - Optimal execution under exponential decay transient impact kernel: $G(t - s) = \gamma e^{-\rho (t - s)}$.
  - Instantaneous price change $S_t = S_0 + \int_0^t G(t - s) v_s \, ds$.
  - Optimal rate of trading with block trades at boundaries $t=0$ and $t=T$:
    $v^*(t) = \frac{X_0}{\rho T + 2}$, boundary impulses $\Delta X_0 = \Delta X_T = \frac{X_0}{\rho T + 2}$.

### Wave 228: Almgren (2003) Non-Linear Power-Law Impact Execution
- **Dynamics**:
  - Temporary impact with power law $h(v) = \eta |v|^\alpha \operatorname{sgn}(v)$ with $\alpha \in (0, 1]$ (empirically $\alpha \approx 0.5$).
  - Permanent impact $g(v) = \gamma v$.
  - Objective: Minimize $E[X] + \lambda \operatorname{Var}[X]$.
  - Trajectory velocity profile with nonlinear deceleration:
    $v(t) = \left[ v_0^{1-\alpha} - (1-\alpha) \left(\frac{\lambda \sigma^2}{\eta}\right) t \right]^{\frac{1}{1-\alpha}}$.
