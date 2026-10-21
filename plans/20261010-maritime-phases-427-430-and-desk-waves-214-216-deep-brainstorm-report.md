# Deep Brainstorming & Architecture Report: Maritime Phases 427–430 & Quantitative Waves 214–216

**Focus Tracks:**
- **Track 1 (Maritime Automation / Mekong CLI):** Engine Cylinder Lubrication Alpha ACC, IMO Tier III SCR Urea De-NOx Kinetics, Cargo Hold Bilge Suction Interlocks & Dewatering Eductors, and Hull ICAF & Ultrasonic Anti-Biofouling.
- **Track 2 (Quantitative Desk / Algo Trader):** Almgren-Thum-Hauptmann-Li (2005) Non-Linear Impact Square-Root Law, Gatheral (2010) No-Dynamic-Arbitrage Decay Kernels, and Avellaneda-Lipkin (2003) Hard-to-Borrow Short Squeeze Dynamics.

**Standards & Doctrines:**
- CIMAC Recommendation No. 32 (Cylinder Lubrication Guidelines), MEPC.340(77), IMO Tier III NOx Technical Code 2008.
- SOLAS II-1 Reg 21, SOLAS XII Reg 12 (Water Ingress Detection), IACS UR SC18.
- IMO Biofouling Guidelines Res. MEPC.378(80), ISO 12473, ASTM D6990.
- Quantitative Microstructure: Almgren et al. (2005), Gatheral (2010), Avellaneda & Lipkin (2003).

---

## Part 1: Track 1 — Maritime Automation Phases 427–430

### Phase 427: Main Engine Cylinder Lubrication Alpha Adaptive Feed Rate (CIMAC No.32, MEPC.340(77))
1. **Physical Kinetics & Chemical Neutralization:**
   - Two-stroke low-speed marine diesel engines (e.g. MAN B&W ME-C, WinGD X-DF) suffer from cold corrosion if liner temperature drops below the sulfuric acid dew point ($T_{\text{dew}} \approx 140 - 165^\circ\text{C}$).
   - Sulfuric acid generation rate:
     $$\dot{m}_{\text{H}_2\text{SO}_4} \propto \text{Power}_{\text{ME}} \cdot \text{SFOC} \cdot \left(\frac{\%S_{\text{fuel}}}{100}\right) \cdot \eta_{\text{conversion}}$$
   - Alpha ACC (Adaptive Cylinder-oil Control) formula calculates the specific lubricant dosage:
     $$F_{\text{cyl}} = \max\left(F_{\text{min}}, k_{\text{ACC}} \cdot \%S_{\text{fuel}} \cdot \frac{P_{\text{engine}}}{P_{\text{MCR}}}\right) \quad [\text{g/(kWh)}]$$
     where baseline $F_{\text{min}} \approx 0.60\text{ g/(kWh)}$, maximum safe feed rate $F_{\text{max}} \approx 1.60\text{ g/(kWh)}$, and $k_{\text{ACC}} \in [0.20, 0.40]\text{ g/(kWh}\cdot\%S)$.
   - Base Number (BN) flux neutralization:
     $$\text{BN}_{\text{balance}} = F_{\text{cyl}} \cdot \text{BN}_{\text{oil}} - \kappa_{\text{stoich}} \cdot \%S_{\text{fuel}}$$
   - Scrape-down drain oil monitoring:
     - Normal: Residual $\text{BN} \ge 15.0\text{ mg KOH/g}$, Iron wear $\text{Fe} \le 200\text{ ppm}$.
     - Corrosive wear alert: $\text{BN} < 10.0\text{ mg KOH/g}$, $\text{Fe} \in [200, 500]\text{ ppm}$.
     - Catastrophic scuffing: $\text{Fe} > 500\text{ ppm}$ with magnetic iron ratio $> 40\%$.

2. **Telemetry & Assessment Contract:**
   - `CylinderLubricationTelemetry`: engine power kW, MCR kW, rpm, fuel sulfur %, lubricant BN, scavenge air temp °C, liner wall temp °C, drain BN, drain iron ppm.
   - `CylinderLubricationAssessment`: recommended feed rate g/(kWh), daily consumption L/day, neutralization status, corrosion risk level, over-lubrication/ash deposit warning.

---

### Phase 428: Selective Catalytic Reduction (SCR) Urea / DEF Injection & De-NOx Kinetics (IMO Tier III, NOx Code 2008)
1. **Chemical Reactions & Operating Envelopes:**
   - Aqueous urea (AUS 40: 40% urea solution) decomposition into ammonia:
     $$\text{Thermal decomposition: } (NH_2)_2CO \to NH_3 + HNCO$$
     $$\text{Hydrolysis: } HNCO + H_2O \to NH_3 + CO_2$$
   - Catalytic De-NOx Reduction (Vanadium-Titanium or Zeolite catalyst):
     $$\text{Standard SCR: } 4NO + 4NH_3 + O_2 \to 4N_2 + 6H_2O$$
     $$\text{Fast SCR: } 2NO + 2NO_2 + 4NH_3 \to 4N_2 + 6H_2O$$
   - Stoichiometric Ammonia-to-NOx Ratio ($\alpha$):
     $$\alpha = \frac{\dot{n}_{NH_3}}{\dot{n}_{NO_x}}, \quad \text{optimal } \alpha \in [0.90, 0.98]$$
   - Critical Safety & Degradation Interlocks:
     - Minimum Operating Temperature (MOT): Exhaust gas $T_{\text{in}} \ge 300^\circ\text{C}$ to prevent Ammonium Bisulfate ($\text{NH}_4\text{HSO}_4$, ABS) condensation which poisons catalyst pores. If $T_{\text{in}} < 300^\circ\text{C}$, DEF dosing is inhibited.
     - Ammonia Slip Limit: Under IMO Tier III, unreacted $NH_3$ emission must not exceed $10.0\text{ ppm}$.
     - Catalyst differential pressure $\Delta P_{\text{cat}}$: Clean $\le 1.2\text{ kPa}$, warning $\ge 2.2\text{ kPa}$, emergency bypass $\ge 3.5\text{ kPa}$.

2. **Telemetry & Assessment Contract:**
   - `SCRDeNOxTelemetry`: exhaust flow kg/h, NOx raw ppm, catalyst inlet temp °C, catalyst dP kPa, DEF tank level %, urea concentration %, ammonia slip ppm.
   - `SCRDeNOxAssessment`: urea dosing rate L/h, De-NOx reduction efficiency %, tier III compliance flag, ABS condensation risk, sootblower demand, ammonia slip alarm.

---

### Phase 429: Cargo Hold Bilge Suction Valve Interlock & Dewatering Eductor Sizing (SOLAS II-1 Reg 21, IACS UR SC18)
1. **Hydraulic Dynamics & Statutory Flooding Safety:**
   - SOLAS II-1 Reg 21 & IACS UR SC18 prohibit open connections between cargo hold bilges and machinery piping to eliminate cross-flooding hazards.
   - Screw-down non-return (SDNR) valves with mechanical position feedback and acoustic flow sensing.
   - Water Ingress Detection System (WIDS - SOLAS XII Reg 12):
     - Level 1 Pre-alarm: $h_{\text{water}} \ge 0.50\text{ m}$ above inner bottom.
     - Level 2 Main alarm: $h_{\text{water}} \ge 2.0\text{ m}$ (or 15% cargo hold depth).
   - Water Eductor (Jet Venturi) dewatering model:
     - Driven by seawater fire/ballast pump ($P_{\text{motive}} \ge 6.0\text{ bar}$).
     - Suction lift $H_{\text{lift}} = z_{\text{eductor}} - z_{\text{hold\_bottom}} \le 6.5\text{ m}$.
     - Entrainment volumetric ratio:
       $$R_q = \frac{Q_{\text{bilge}}}{Q_{\text{motive}}} = K_{\text{eductor}} \sqrt{\frac{P_{\text{motive}} - P_{\text{dis}}}{P_{\text{dis}} + \rho g H_{\text{lift}}}}$$
     - Interlock: Eductor motive valve must open BEFORE bilge suction valve opens to prevent backflow of sea pressure water into cargo hold.

2. **Telemetry & Assessment Contract:**
   - `CargoHoldBilgeTelemetry`: hold id, water level m, valve position feedback, motive pressure bar, eductor suction pressure bar, discharge pressure bar, sea state Hs.
   - `CargoHoldBilgeAssessment`: water ingress alarm level (NORMAL / LEVEL1 / LEVEL2), dewatering rate m3/h, backflow protection interlock intact, eductor cavitating flag.

---

### Phase 430: Hull Impressed Current Anti-Fouling (ICAF) & Ultrasonic Acoustic Bio-Fouling (IMO Res. MEPC.378(80))
1. **Electrolytic & Acoustic Marine Growth Prevention:**
   - Electrolytic ICAF (MGPS):
     - Copper ($Cu$) anode release: Ion concentration $C_{\text{Cu}} = 1.0 - 5.0\ \mu\text{g/L}$ ($\text{ppb}$) in sea chest intake.
     - Aluminum ($Al$) or Soft Iron ($Fe$) anode release: Produces gelatinous hydroxide precipitate $\text{Al(OH)}_3$ which carries copper ions along internal seawater pipe walls, forming a smooth anti-corrosive, anti-fouling barrier.
     - Faraday's Law for electrolytic anode loss:
       $$\dot{m}_{\text{anode}} = \frac{I \cdot M}{z \cdot F} \cdot \eta_{\text{current}}$$
   - Ultrasonic Cavitation / Acoustic Streaming:
     - Piezoelectric transducers bonded to hull plating emitting dual frequencies ($28\text{ kHz} / 40\text{ kHz}$).
     - Generates localized micro-acoustic streaming that disrupts cell vacuoles of green algae (*Enteromorpha*) and barnacle cyprid larvae settlement without ablating coatings.
   - Biofouling Risk Index (IMO Res. MEPC.378(80) / ASTM D6990):
     - Evaluated via idle days in warm tropical waters ($T_{\text{sea}} > 22^\circ\text{C}$), hull speed profile ($v < 8\text{ knots}$), and ultrasonic power density ($P_{\text{acoustic}} \ge 1.2\text{ W/m}^2$).

2. **Telemetry & Assessment Contract:**
   - `HullAntiFoulingTelemetry`: sea water flow m3/h, Cu anode current A, Al anode current A, anode voltage V, ultrasonic power W, transducer impedance ohm, seawater temp °C, vessel idle days.
   - `HullAntiFoulingAssessment`: copper dosing ppb, anode wear % consumed, ultrasonic cavitation active, biofouling risk index (LOW / MODERATE / HIGH / CRITICAL), pipe fouling alert.

---

## Part 2: Track 2 — Quantitative Desk Waves 214–216

### Wave 214: Almgren, Thum, Hauptmann & Li (2005) Non-Linear Equity Market Impact
1. **Mathematical Theory & Calibration:**
   - Models market impact of meta-orders across US equity markets showing distinct square-root behavior for temporary impact and linear behavior for permanent impact.
   - Temporary Price Impact:
     $$g(\nu) = \eta \cdot \sigma \cdot \left(\frac{|\nu|}{V}\right)^\alpha \cdot \text{sgn}(\nu)$$
     where $\alpha \approx 0.5$ (concave square root impact), $\nu = \frac{dx}{dt}$ is trade speed, $V$ is Average Daily Volume (ADV), and $\sigma$ is daily asset volatility.
   - Permanent Price Impact:
     $$J(x) = \gamma \cdot \sigma \cdot \left(\frac{x}{V}\right)$$
     strictly linear to preserve no-arbitrage martingale properties of price.
   - Expected Execution Slippage under TWAP vs optimal non-linear schedule:
     $$\text{Cost}_{\text{temp}} = \int_0^T g(\nu(t)) \, \nu(t) \, dt = \eta \sigma V^{-\alpha} \int_0^T |\nu(t)|^{1 + \alpha} \, dt$$

2. **Module Architecture (`src/desk/almgrenthum/`):**
   - `almgren-thum-types.ts`: Parameters, trajectory points, impact decomposition.
   - `almgren-thum-math.ts`: Evaluates $g(\nu)$, $J(x)$, total implementation shortfall, non-linear Euler-Lagrange trajectories.
   - `almgren-thum-engine.ts`: High-level engine executing optimal execution sizing and slippage forecasting.
   - `index.ts`: Module exports.

---

### Wave 215: Gatheral (2010) No-Dynamic-Arbitrage Principle of Impact Kernels
1. **Mathematical Theory & Kernel Admissibility:**
   - Examines whether transient price impact models admit price manipulation (profitable round-trip round-trip trades $\oint P_t \, dX_t < 0$).
   - Price dynamics under transient impact:
     $$S(t) = S(0) + \int_0^t f(\dot{x}(s)) G(t - s) \, ds + \sigma W_t$$
   - Gatheral's Theorem: If impact function $f(v)$ is non-linear ($f(v) = v^\alpha$ with $\alpha \ne 1$), then for any non-constant decaying kernel $G(\tau)$, there exist round-trip manipulation strategies yielding positive expected profit.
   - To avoid price manipulation with non-linear impact, the kernel must either be:
     1. Strictly permanent: $G(\tau) = G_0 = \text{const}$.
     2. Power-law decay with critical exponent restriction $\gamma \ge 1 - \alpha$.
   - Positive-definiteness Fourier test:
     $$\hat{G}(\omega) = \int_0^\infty G(t) \cos(\omega t) \, dt > 0 \quad \forall \omega \ge 0$$

2. **Module Architecture (`src/desk/gatheral/`):**
   - `gatheral-types.ts`: Kernel parameters, manipulation detection metrics, Fourier spectrum.
   - `gatheral-math.ts`: Power-law kernel decay $G(\tau) = \frac{c}{(\tau + \delta)^\gamma}$, round-trip execution cost integral, positive-definiteness validation.
   - `gatheral-engine.ts`: Validates impact kernel parameters against dynamic arbitrage and calculates optimal round-trip cost bounds.
   - `index.ts`: Module exports.

---

### Wave 216: Avellaneda & Lipkin (2003) Hard-to-Borrow Securities & Short Squeeze Dynamics
1. **Mathematical Theory & Non-Linear Feedback:**
   - Models equities with high short interest ($SI / \text{Float} \ge 25\%$) subject to short borrow fee rate $r_b$ and lender recall risk.
   - Short squeeze feedback loop:
     - Cumulative short position $Q(t)$.
     - Forced buy-in rate $\nu_{\text{squeeze}}(t) = \lambda(S, r_b) \cdot \max(0, S(t) - S_{\text{threshold}})$.
     - Price impact from forced liquidation:
       $$\frac{dS_t}{S_t} = \left(\mu + \kappa \cdot \nu_{\text{squeeze}}(t) - r_b\right) dt + \sigma dW_t$$
   - Explosive Phase Transition Regime:
     When $\kappa \cdot \frac{\partial \nu_{\text{squeeze}}}{\partial S} \cdot S > \text{mean-reversion strength}$, the market enters a super-exponential short squeeze bubble.
   - Optimal inventory liquidation and borrow fee cost under squeeze probability.

2. **Module Architecture (`src/desk/avellanedalipkin/`):**
   - `avellaneda-lipkin-types.ts`: Short interest, borrow fee, squeeze probability, critical threshold.
   - `avellaneda-lipkin-math.ts`: Feedback drift calculation, phase transition indicator, Monte Carlo / PDE squeeze trajectory.
   - `avellaneda-lipkin-engine.ts`: Evaluates squeeze risk scores, borrow cost drag, and provides safe exit boundaries.
   - `index.ts`: Module exports.

---

## Part 3: Architecture & Quality Enforcement

1. **Strict File LOC Ceiling:**
   - Every module strictly $< 180\text{ LOC}$.
   - Clean separation between types, pure mathematics/physics, engine facade, and CLI/API wrappers.

2. **Zero Mocks & Zero Fake Data:**
   - Tests instantiate real domain engines with analytical physics and quantitative market inputs.
   - All tests must pass with 100% green status.

3. **TypeScript Standards:**
   - Zero `:any` types.
   - Strict compiler checks (`tsc --noEmit`).

4. **Integration Points:**
   - `mekong-cli`: Register CLI commands with bilingual aliases in `src/cli/app_setup.py`, master facade in `src/core/`, unit tests in `tests/`.
   - `algo-trader`: Export engines in `src/desk/index.ts`, unit test suite in `tests/unit/desk/waves_214_216_suite.test.ts`.
