# Researcher Report: Maritime Phases 391-394 Engineering Specifications

**Domain:** Advanced Marine Systems AE
**Standard Regulations:** MEPC.107(49), DNV-RP-B401, TEMA/ASME Sec VIII, IMO IBC Code Ch. 15

---

### Phase 391: Oily Water Separator (OWS) 15 ppm & Ceramic Ultrafiltration Membrane
- **Standard:** IMO Res. MEPC.107(49), MARPOL Annex I Reg 14.
- **Physical Dynamics:**
  - Stokes gravity separation: $v_t = \frac{g d^2 (\rho_w - \rho_o)}{18 \mu_w}$. Coalescer coalesces droplets $d \ge 20\,\mu\text{m}$.
  - Ceramic membrane cross-flow flux: $J = \frac{\Delta P}{\mu_w (R_m + R_c)}$. Transmembrane pressure $\text{TMP} = \frac{P_{\text{in}} + P_{\text{out}}}{2} - P_{\text{permeate}}$.
  - 15 ppm Bilge Alarm Interlock: Continuous optical/turbidity sensing. If oil concentration $C_{\text{oil}} \ge 15.0\text{ ppm}$, instant 3-way solenoid valve trip ($t_{\text{trip}} < 3.0\text{ s}$) diverting flow back to bilge holding tank; discharge overboard permitted strictly when $C_{\text{oil}} < 15.0\text{ ppm}$ and vessel is en route.

---

### Phase 392: Impressed Current Cathodic Protection (ICCP) & Propeller Shaft Grounding
- **Standard:** DNV-RP-B401, NACE SP0169, ISO 12473.
- **Electrochemical Dynamics:**
  - Steel polarization protection window: Protective hull potential vs. $\text{Ag/AgCl}$ reference electrode: $-800\text{ mV} \ge E_{\text{hull}} \ge -1050\text{ mV}$.
  - Over-protection boundary: $E_{\text{hull}} < -1050\text{ mV}$ induces cathodic hydrogen embrittlement and coating disbondment.
  - Under-protection boundary: $E_{\text{hull}} > -800\text{ mV}$ triggers active galvanic hull corrosion.
  - Anode loop current control: $I_{\text{demand}} = k_p (E_{\text{set}} - E_{\text{meas}}) + k_i \int \Delta E \, dt$.
  - Propeller shaft slip-ring grounding: Shaft-to-hull potential millivoltmeter $\Delta V_{\text{shaft}} \le 50\text{ mV}$ (preventing spark erosion on stern tube bearings).

---

### Phase 393: Central Titanium Plate Heat Exchanger (PHE) & Ultrasonic Anti-Fouling
- **Standard:** TEMA Class R, ASME Sec VIII Div 1, DNV-RU-SHIP Pt.4 Ch.6.
- **Thermal & Acoustic Dynamics:**
  - Heat Duty & LMTD: $\dot{Q} = U A F \Delta T_{\text{lm}}$, where $\Delta T_{\text{lm}} = \frac{(T_{h1} - T_{c2}) - (T_{h2} - T_{c1})}{\ln((T_{h1} - T_{c2}) / (T_{h2} - T_{c1}))}$.
  - Fouling Resistance Factor: $R_f = \frac{1}{U_{\text{fouled}}} - \frac{1}{U_{\text{clean}}}$. Alert when $R_f \ge 0.00015\,\text{m}^2\cdot\text{K/W}$.
  - Plate hydraulic pressure drop: $\Delta P \le 0.80\text{ bar}$. Backwash / ultrasonic transducer cleaning triggered if $\Delta P \ge 1.20\text{ bar}$.
  - Ultrasonic piezoceramic power: Acoustic intensity $I_{\text{us}} \ge 1.5\,\text{W/cm}^2$ at $28-40\,\text{kHz}$ preventing marine biofilm attachment.

---

### Phase 394: Chemical Tanker Cofferdam Vapor Sniffing & Inerting
- **Standard:** IMO IBC Code Ch. 15, SOLAS II-2 Reg 4.5.10, ISGOTT Ch. 5.
- **Gas & Differential Pressure Dynamics:**
  - Toxic / Flammable cargo vapor migration: Continuous optical / photoionization sniffing in void cofferdam separating cargo tanks from engine/pump spaces.
  - Pre-alarm threshold: VOC $\ge 10.0\%\text{ LEL}$ or toxic vapor $\ge 50.0\%\text{ TLV-TWA}$.
  - Critical breach alarm: VOC $\ge 20.0\%\text{ LEL}$, initiating immediate emergency inert gas ($N_2$) purge.
  - Inert condition compliance: $O_2 \le 5.0\%\text{ vol}$ in cofferdam.
  - Differential pressure barrier: Positive cofferdam overpressure $\Delta P_{\text{cofferdam}} = P_{\text{cofferdam}} - P_{\text{adj}} \ge +0.20\text{ kPa}$ to prevent chemical vapor ingress.
