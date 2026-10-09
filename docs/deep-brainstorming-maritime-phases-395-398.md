# Deep Brainstorming: Maritime Phases 395-398 (Maritime Advanced Engineering AF)

## 1. Executive Summary
Maritime Phases 395-398 expand the autonomous marine engineering and classification intelligence of Mekong CLI v6.0 into critical environmental compliance, freshwater production, deck cargo handling, and structural hull integrity:
1. **Phase 395:** Exhaust Gas Cleaning System (EGCS) SOx Wet Scrubber (IMO MARPOL Annex VI Reg 14 & Res. MEPC.340(77)).
2. **Phase 396:** Vacuum Plate Fresh Water Generator (FWG) Evaporator (SOLAS II-1 Reg 26 & WHO Guide to Ship Sanitation).
3. **Phase 397:** Electro-Hydraulic Deck Crane Anti-Sway & Dynamic SWL Limiter (ILO Convention 152 & DNV-ST-0378).
4. **Phase 398:** Ultrasonic Thickness Measurement (UTM) Hull Gauging & Wastage Renewal (IACS UR Z10.1/Z10.2 & IMO ESP Code).

---

## 2. Mathematical Models & Physics Formulations

### Phase 395: EGCS SOx Scrubber (MEPC.340(77))
- **SO2/CO2 Emission Ratio:**
  $$\text{Ratio} = \frac{SO_2\text{ (ppm)}}{CO_2\text{ (\% vol)}}$$
  - Global Cap (0.50% S equivalent): $\text{Ratio} \le 21.7$.
  - Emission Control Area (SECA, 0.10% S equivalent): $\text{Ratio} \le 4.3$.
- **Washwater Discharge Quality (Continuous In-line Monitoring):**
  - Acidity: $pH \ge 6.5$ measured 4 meters from discharge outlet point.
  - PAH Concentration: $\Delta \text{PAH} = \text{PAH}_{\text{discharge}} - \text{PAH}_{\text{inlet}} \le 50.0\ \mu\text{g/L}$ (phenanthrene equivalents).
  - Turbidity: $\Delta \text{Turbidity} \le 25.0\text{ FNU/NTU}$.
  - Temperature: $\Delta T \le 2.0^\circ\text{C}$ over ambient seawater.
- **Operating Modes:**
  - `OPEN_LOOP`: Seawater bicarbonate alkalinity ($HCO_3^-$) absorption ($SO_2 + 2HCO_3^- \to SO_3^{2-} + 2CO_2 + H_2O$). Prohibited in restricted waters with low alkalinity or local port bans.
  - `CLOSED_LOOP`: Recirculated freshwater with sodium hydroxide ($NaOH$) neutralization ($2NaOH + SO_2 \to Na_2SO_3 + H_2O$), bleed-off diverted to holding tank for zero-discharge compliance.
  - `HYBRID_SWITCHOVER`: Seamless transition between modes during coastal/ECA approach.

### Phase 396: Vacuum Plate Fresh Water Generator (FWG)
- **Sub-Atmospheric Boiling Equilibrium:**
  - Clausius-Clapeyron vacuum boiling temperature:
    $$T_{\text{sat}}(P) \approx 40.0^\circ\text{C to } 48.0^\circ\text{C}\quad \text{at}\quad P_{\text{abs}} = 7.5\text{ to } 11.5\text{ kPa (vacuum } -0.92\text{ to } -0.95\text{ bar)}$$
  - Driving thermal energy: Main Engine High-Temperature (HT) jacket cooling water ($T_{\text{JW,in}} = 75-85^\circ\text{C}, T_{\text{JW,out}} = 65-75^\circ\text{C}$).
- **Distillate Purity & Salinity Solenoid Trip:**
  - Salinity threshold: $\text{TDS} \le 10.0\text{ ppm}$ (or electrical conductivity $\le 20.0\ \mu\text{S/cm}$).
  - Solenoid Diverter Valve:
    - $\text{TDS} \le 10.0\text{ ppm} \implies$ Divert to Potable / Boiler Feed Water Tanks (`STORAGE`).
    - $\text{TDS} > 10.0\text{ ppm} \implies$ Emergency solenoid diversion to Bilge / Evaporator feed (`RECIRC_DUMP`).
- **Brine Concentration Factor:**
  $$CF = \frac{\text{Salinity}_{\text{brine}}}{\text{Salinity}_{\text{feed}}} \le 1.50$$
  Prevents severe $CaCO_3$ and $CaSO_4$ scale crystallization on titanium plate packs.

### Phase 397: Deck Crane Anti-Sway & Dynamic SWL Limiter (DNV-ST-0378)
- **Overturning & Tipping Moment Balance:**
  $$M_{\text{load}} = M \cdot R = M \cdot L_{\text{boom}} \cos(\alpha)$$
  Where $M$ is suspended mass (tonnes), $R$ is working radius (m), $L_{\text{boom}}$ is boom length, and $\alpha$ is luffing angle.
- **Dynamic Derating Factor (Offshore / Harbor Sea State):**
  $$\text{SWL}_{\text{dyn}} = \frac{\text{SWL}_{\text{static}}}{F_{\text{dyn}}},\quad F_{\text{dyn}} = 1.0 + 0.35 \cdot H_s$$
  Where $H_s$ is significant wave height (m).
- **Anti-Sway Pendulum Dampening Dynamics:**
  $$\ddot{\theta} + \frac{g}{L_{\text{rope}}}\theta = -\frac{\ddot{x}_{\text{slewing}}}{L_{\text{rope}}}$$
  Feedforward acceleration profiles damp swinging amplitude to safe limit $\theta \le 2.5^\circ$.
- **Hydraulic Interlocking Envelope:**
  - Boom angle working limits: $15.0^\circ \le \alpha \le 82.0^\circ$.
  - Load threshold alarms: $90\%$ SWL caution, $100\%$ SWL visual/audible alarm, $110\%$ SWL fail-safe hydraulic hoisting cutoff.

### Phase 398: UTM Hull Gauging & Corrosion Wastage (IACS UR Z10)
- **Diminishing Wastage Ratio:**
  $$\text{Wastage } \% = \frac{t_{\text{as-built}} - t_{\text{actual}}}{t_{\text{as-built}}} \times 100\%$$
- **IACS Classification Renewal Limits:**
  - Category A (Deck & Bottom shell longitudinal strength plates): Maximum allowable wastage $= 15.0\%$.
  - Category B (Side shell, inner bottom, transverse watertight bulkheads): Maximum allowable wastage $= 20.0\%$.
  - Category C (Internal web frames, stiffeners, floor plates): Maximum allowable wastage $= 25.0\%$.
- **Substantial Corrosion Condition:**
  $$\text{Wastage} \ge 0.75 \times \text{Allowable Wastage}$$
  Triggers mandatory annual intermediate surveys and ultrasonic re-gauging.
- **Pitting Corrosion Pitted Area Fraction:**
  $$\text{Pitting Ratio} = \frac{\sum A_{\text{pits}}}{A_{\text{plate}}} \times 100\%$$
  Pitting density $> 15\%$ or pit depth exceeding $50\%$ remaining plate requires structural steel renewal or epoxy cladding.

---

## 3. Architecture & File Layout
Following Mekong CLI constitutional guidelines:
- Every code file strictly `< 200 LOC`.
- Zero-mock tests with 100% deterministic physics.
- Bilingual Typer CLI commands with Vietnamese aliases.
- FastMCP tool registration in `scripts/mcp_server.py`.
