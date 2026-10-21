# Deep Brainstorming: Maritime Phases 447–450 & Quantitative Desk Waves 229–231

## Overview
Autonomous, continuous dual-track delivery:
1. **Track 1 (`mekong-cli`)**: Maritime Automation Physical Engineering (Phases 447–450)
   - Phase 447: Crude Oil Washing (COW) & Tank Cleaning Machine Operation (IMO A.446(XI) / MARPOL Annex I)
   - Phase 448: Fixed Deck Foam Fire-Extinguishing System for Tankers (SOLAS II-2 Reg 10.8 / FSS Code Ch.14)
   - Phase 449: Marine Auxiliary Boiler Flue Gas Desulfurization & Demister (MARPOL Annex VI / MEPC.259(68))
   - Phase 450: Vapor Emission Control System (VECS) & Detonation Arrestor (IMO MSC/Circ.585 / USCG 46 CFR 39)
2. **Track 2 (`algo-trader`)**: Institutional Quantitative Trading Models (Waves 229–231)
   - Wave 229: Bouchaud, Farmer & Lillo (2009) Metaorder Square-Root Impact & Relaxation
   - Wave 230: Curato, Borger & Lillo (2017) Optimal Execution with Endogenous Queue Transitions
   - Wave 231: Jaisson & Rosenbaum (2016) Microstructural High-Frequency Hawkes Foundations of Rough Heston

---

## Track 1: Maritime Automation Physical Engineering

### Phase 447: Crude Oil Washing (COW) & Tank Cleaning (IMO A.446(XI))
- Wash supply pressure $P_{\text{wash}} \in [8.0, 12.0]\,\text{bar}$ (alarm $< 8.0\,\text{bar}$, trip $< 7.0\,\text{bar}$).
- Tank inert gas oxygen concentration $O_2 \le 8.0\%\,\text{vol}$ (mandatory wash emergency trip if $> 8.0\%$).
- Stripping capacity ratio $R_{\text{strip}} = \dot{V}_{\text{strip}} / \dot{V}_{\text{wash}} \ge 1.25$ to prevent bottom accumulation.
- Machine rotation speed $\omega_{\text{rot}} \in [1.0, 3.0]\,\text{deg/s}$.

### Phase 448: Fixed Deck Foam Fire-Extinguishing (SOLAS II-2 / FSS Code Ch.14)
- Foam solution application rate $\ge 0.60\,\text{L/min/m}^2$ across deck area.
- Foam concentrate induction ratio $R_{\text{ind}} \in [2.7\%, 3.3\%]$ for $3\%$ AFFF concentrate.
- Monitor nozzle pressure $P_{\text{mon}} \ge 6.0\,\text{bar}$, horizontal throw distance $\ge 50.0\,\text{m}$.
- Minimum autonomous foam concentrate duration $\ge 20.0\,\text{min}$.

### Phase 449: Marine Boiler Flue Gas Desulfurization (MEPC.259(68))
- Scrubber pack differential pressure $\Delta P_{\text{scrub}} \in [100.0, 450.0]\,\text{Pa}$ (alarm $> 450.0\,\text{Pa}$, trip $> 550.0\,\text{Pa}$).
- Alkaline washwater liquid-to-gas ratio $L/G \ge 2.5\,\text{L/Nm}^3$ ensuring $> 97\%\,SO_x$ removal.
- Demister droplet moisture carryover $\le 1.5\%\,\text{wt}$.
- Washwater discharge effluent $pH \ge 6.5$.

### Phase 450: Vapor Emission Control System (VECS) (USCG 46 CFR 39)
- Vapor manifold pressure $P_{\text{man}} \in [-10.0, +80.0]\,\text{mbar}$ (high alarm $+65.0\,\text{mbar}$, high-high trip $+80.0\,\text{mbar}$, vacuum trip $-35.0\,\text{mbar}$).
- Detonation flame arrester thermal sensor $T_{\text{darr}} \le 65.0^\circ\text{C}$ (flame trip $> 80.0^\circ\text{C}$).
- Oxygen concentration in vapor line $O_2 \le 8.0\%\,\text{vol}$ (warning $> 7.0\%$, ESD trip $> 8.0\%$).
- Condensate knock-out drum level $\le 50.0\%$ volume.

---

## Track 2: Institutional Quantitative Trading Desk

### Wave 229: Bouchaud, Farmer & Lillo (2009) Metaorder Square-Root Impact
- Square-root scaling: $I(Q) = Y \sigma \sqrt{\frac{Q}{V}}$.
- Post-execution relaxation decay: $R(t) = I(Q) \cdot \left(\frac{1}{1 + (t / T)^\beta}\right)$ with $\beta \approx 0.5$.

### Wave 230: Curato, Borger & Lillo (2017) Endogenous Queue Transitions
- Limit order fill probability $P_{\text{fill}}(q, \lambda, \mu) = \frac{\mu}{\lambda + \mu} e^{-\kappa q}$.
- Maker vs Taker decision policy: Switch to aggressive sweep when latency penalty and adverse selection exceed spread savings.

### Wave 231: Jaisson & Rosenbaum (2016) Microstructural Hawkes to Rough Heston
- Hawkes self-excitation kernel with heavy tails: $\phi(t) \sim t^{-(1+\alpha)}$.
- Branching ratio criticality $\eta \to 1^-$.
- Convergence of high-frequency order arrivals to fractional Brownian motion with Hurst index $H = \alpha - 1/2 < 1/2$.
