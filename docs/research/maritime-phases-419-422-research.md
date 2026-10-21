---
name: maritime-phases-419-422-research
description: Engineering research for Maritime Automation Phases 419-422 (EGR Bleed-off, Shaft Generator AFE, BWMS Neutralization, Stern Thruster CPP)
metadata:
  type: reference
---

# Maritime Phases 419–422 Engineering Research

## 1. Marine Exhaust Gas Recirculation (EGR) & Bleed-off Treatment (Phase 419)
- **Regulations:** IMO MARPOL Annex VI Tier III NOx ($\le 3.4\,\text{g/kWh}$ at $n < 130\,\text{rpm}$), MEPC.307(73) 2018 Guidelines for EGR Bleed-off Water Discharge.
- **Thermodynamic Principle:** Exhaust gas recirculated ($\sim 30\text{--}40\%$) into scavenge air reduces peak combustion temperature below thermal NOx threshold ($>1600^\circ\text{C}$).
- **Bleed-off Water Treatment (WTS):** High-temperature particulate scrubber wash water contains soot, unburned fuel, and sulfuric acid.
- **Centrifugal Water Separation:** Hydrocyclone / disc-stack separator lowers turbidity.
- **Discharge Criteria:** Overboard discharge strictly monitored:
  - Oil content $< 15\,\text{ppm}$
  - Turbidity $< 25\,\text{FNU}$ (or NTU above inlet water)
  - $\text{pH} \ge 6.5$ (neutralization via NaOH dosing)
  - PAH (Polycyclic Aromatic Hydrocarbons) concentration $\Delta\text{PAH} \le 50\,\mu\text{g/L}$.
- **Interlocks:** Overboard 3-way divert valve switches to holding tank when discharge criteria fail.

## 2. Marine Shaft Generator AFE Frequency Converter & Harmonics THD (Phase 420)
- **Regulations:** IACS UR E24, IEEE 519-2022, DNV Pt.4 Ch.8 Electrical Installations.
- **Electrical Architecture:** Power Take-Off (PTO) synchronous generator driven by variable-speed main engine ($50\text{--}100\,\text{rpm}$) feeding constant $60\,\text{Hz} / 440\,\text{V}$ ship service switchboard.
- **Active Front End (AFE):** IGBT PWM rectifier and inverter with LCL filter eliminating low-order harmonics (5th, 7th, 11th, 13th).
- **Harmonic Distortion Limits:**
  - Total Harmonic Distortion $\text{THD}_V \le 5.0\%$ at main busbar.
  - Individual harmonic voltage component $\le 3.0\%$.
  - Voltage unbalance factor $\le 2.0\%$.
- **Grid Fault Ride-Through (GFRT):** Fast reactive power support during voltage dips down to $30\%$ for $t \le 150\,\text{ms}$ without trip.
- **Reverse Power Protection:** PTO power anti-motoring threshold $-5\%$ for $t > 3.0\,\text{s}$ triggers breaker trip to prevent driving main engine shaft.

## 3. Ballast Water Management System (BWMS) Electro-Chlorination & Neutralization (Phase 421)
- **Regulations:** IMO BWM Convention Reg D-2, USCG Phase-II ETV protocol, MEPC.300(72) Code for Approval of BWMS.
- **Electrochemical Disinfection:** Seawater electrolysis generates sodium hypochlorite ($NaOCl$):
  $$2\,Cl^- \to Cl_2 + 2\,e^-,\quad Cl_2 + H_2O \to HOCl + H^+ + Cl^-$$
  Target Total Residual Oxidant (TRO) concentration during ballasting: $1.5\text{--}2.0\,\text{mg/L}$ as $Cl_2$.
- **De-ballasting Neutralization:** Sodium thiosulfate ($Na_2S_2O_3$) or sodium bisulfite ($NaHSO_3$) stoichiometric dosing:
  $$HOCl + NaHSO_3 \to NaCl + H_2SO_4$$
- **Discharge Toxicity Boundary:** Overboard discharge TRO must be strictly $\le 0.10\,\text{mg/L}$ ($0.1\,\text{ppm}$) (USCG $< 0.05\,\text{mg/L}$).
- **Hydrogen Safety Interlock:** Degassing blower ensures $H_2$ concentration in electrolytic cell $< 25\%$ LEL ($< 1.0\%$ vol).

## 4. Marine Stern Thruster Tunnel Grate & CPP Pitch Cavitation Inception (Phase 422)
- **Regulations:** DNV-RU-SHIP Pt.4 Ch.5 Sec.3, ITTC 1978/2011 Cavitation Criteria, ISO 10816-3.
- **Tunnel Hydrodynamics & Grate Drag:**
  - Suction tunnel inlet loss coefficient $K_{\text{inlet}}$ and steel bar debris grate resistance:
    $$\Delta P_{\text{loss}} = \frac{1}{2} \rho v_{\text{tunnel}}^2 \left(K_{\text{inlet}} + \zeta_{\text{grate}}\right)$$
- **Thrust & Blade Pitch Control:** Controllable Pitch Propeller (CPP) variable blade pitch angle $\theta \in [-25^\circ, +25^\circ]$ driving bi-directional transverse maneuvering thrust.
- **Cavitation Inception Index:**
  $$\sigma = \frac{P_{\text{amb}} - P_{\text{vapor}}}{\frac{1}{2} \rho v_{\text{tip}}^2}$$
  Critical cavitation inception threshold $\sigma_{\text{crit}} \approx 0.85$. When $\sigma < \sigma_{\text{crit}}$, blade tip vortex sheet cavitation collapses, causing acoustic high-frequency erosion.
- **Acoustic & Vibration Sensors:** Accelerometers detect ultrasonic shock wave impulses ($10\text{--}40\,\text{kHz}$). Automatic pitch derating limits tip cavitation erosion while preserving $80\%$ emergency docking thrust.
