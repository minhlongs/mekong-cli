# Brainstorming & Architecture Report: Maritime Phases 387–390

**Focus:** Maritime Engineering, HVAC/Reefer Climate, Waste Bioprocessing, Controllable Pitch Propeller (CPP) & Cryogenic Leak Detection
**Compliance Frameworks:** SOLAS II-1/II-2, MARPOL Annex V, DNV-RU-SHIP, IMO IGC Code, ISO 5149, ASHRAE 26
**Target Architecture:** Hybrid Modular Facade pattern, strictly `< 200 LOC` per module, Zero Mocks, Bilingual Typer CLI, FastMCP RPC integration.

---

## 1. Domain Breakdown & Physical Formulations

### Phase 387: Marine Central Chilled Water & Cargo Hold HVAC Climate Control
- **Core Standard:** ISO 5149 / ASHRAE Guideline 26 / DNV-RU-SHIP Pt.4 Ch.6.
- **Thermodynamic Model:**
  - Chilled water closed loop energy balance:
    $$\dot{Q}_{\text{chill}} = \dot{m}_{\text{cw}} \cdot c_p \cdot (T_{\text{return}} - T_{\text{supply}})$$
    where $c_p \approx 4.184\text{ kJ/(kg}\cdot\text{K)}$.
  - Coefficient of Performance (COP):
    $$\text{COP} = \frac{\dot{Q}_{\text{chill}}}{P_{\text{compressor}}}$$
    Threshold: $\text{COP} \ge 3.2$ optimal; $< 2.5$ sub-optimal alert.
  - Cargo hold dew point control (cargo sweat & ship sweat prevention):
    $$T_{\text{dp}} \approx T_{\text{air}} - \left(\frac{100 - \text{RH}}{5}\right)$$
    Interlock: Hold ventilation shut-off when outside dew point exceeds hold cargo surface temperature ($T_{\text{dp,out}} > T_{\text{cargo}}$) to prevent condensation damage.
  - Refrigerant leak detection threshold: Halocarbon sensor $> 25.0\text{ ppm}$ alarm; $> 100.0\text{ ppm}$ compressor trip and machinery room purge extraction.

### Phase 388: Food Waste Pulper & Bio-Digestion (MARPOL Annex V Reg 4/5)
- **Core Standard:** MARPOL Annex V, IMO Res. MEPC.295(71), 2017 Guidelines for Implementation of Annex V.
- **Biochemical & Comminution Criteria:**
  - Comminution mesh size threshold: Maximum particle diameter $d_{\text{particle}} \le 25.0\text{ mm}$ (ground through a screen with openings no greater than 25 mm).
  - Discharge distance rules:
    - Outside Special Area & comminuted ($\le 25\text{ mm}$): Distance from nearest land $\ge 3.0\text{ NM}$ en route.
    - Outside Special Area & un-comminuted: Distance $\ge 12.0\text{ NM}$ en route.
    - Inside Special Areas (e.g. Baltic, Mediterranean, Red Sea, Gulfs, Wider Caribbean, Antarctic): Discharges strictly prohibited unless comminuted AND distance $\ge 12.0\text{ NM}$ en route.
  - Anaerobic bio-digester methane output and volatile fatty acid (VFA) stability:
    $$\text{VFA}/\text{TIC} \le 0.30 \quad (\text{stable bio-digestion})$$
  - Grease trap / greywater oil content interlock: Oil content $\le 15.0\text{ ppm}$ before overboard discharge.

### Phase 389: Controllable Pitch Propeller (CPP) Hydraulics & Pitch Load Control
- **Core Standard:** DNV-RU-SHIP Pt.4 Ch.5, IACS UR M43, ISO 484-1/2 (Marine Propeller Tolerances).
- **Control & Hydraulic Dynamics:**
  - Propeller thrust and pitch ratio ($P/D$):
    $$\text{Pitch Angle } \theta = \arctan\left(\frac{P}{2\pi r}\right)$$
  - Pitch travel time rate: Ahead full ($+25^\circ$) to Astern full ($-15^\circ$) in $t \le 25.0\text{ s}$ via hydraulic servomotor stroke.
  - Hydraulic actuating oil pressure: Working pressure $P_{\text{work}} \in [40.0, 70.0]\text{ bar}$; low pressure alarm $< 35.0\text{ bar}$; relief valve setpoint $85.0\text{ bar}$.
  - Main Engine Combinator Curve & Pitch Auto-Reduction:
    - If Engine Load $> 100\%\text{ MCR}$ or Exhaust Gas Temp $> 480^\circ\text{C}$, trigger pitch de-rating:
      $$\Delta \theta_{\text{cut}} = k \cdot (\text{Load} - 100\%)$$
  - Oil-to-Sea shaft seal header tank differential pressure:
    $$P_{\text{seal}} - P_{\text{sea,draft}} \ge 0.30\text{ bar}$$
    preventing seawater ingress into stern tube and oil pollution to sea.

### Phase 390: Cryogenic Cargo Tank Leak Sniffing & Insulation Pressure Relief
- **Core Standard:** IMO IGC Code Ch. 8 & Ch. 13, SIGTTO Guidelines for Liquefied Gas Carriers.
- **Cryogenic & Vacuum/Inert Annulus Monitoring:**
  - Annular / Interbarrier space inerting: Dew point $T_{\text{dew}} \le -40.0^\circ\text{C}$, $O_2 \le 1.0\%\text{ vol}$ (dry $N_2$).
  - Helium trace sniff & Hydrocarbon sniffer:
    - Background methane in interbarrier space: Warning at $\ge 0.5\%\text{ vol CH}_4$; critical primary barrier failure trip at $\ge 30.0\%\text{ LEL}$ ($\approx 1.5\%\text{ vol}$).
  - Insulation Space Pressure Differential:
    $$\Delta P = P_{\text{insulation}} - P_{\text{cargo tank}} \in [-5.0, +2.0]\text{ kPa}$$
    Relief valve lift setting: $+3.5\text{ kPa}$ overpressure venting to mast.
  - Secondary barrier temperature cold-spot detection:
    $$\text{Hull Steel Temp } T_{\text{inner hull}} \ge 0.0^\circ\text{C}$$
    If $T_{\text{inner hull}} < 0.0^\circ\text{C}$, trigger secondary barrier cryogenic leakage alarm & heating glycol loop boost.

---

## 2. Architecture Plan & File Layout

All source modules strictly `< 200 LOC`:
1. `src/core/maritime/phase_387_chilled_water_hvac_control.py` (~130 LOC)
2. `src/core/maritime/phase_388_food_waste_pulper_biodigestion.py` (~130 LOC)
3. `src/core/maritime/phase_389_cpp_pitch_hydraulic_load.py` (~130 LOC)
4. `src/core/maritime/phase_390_cryogenic_tank_leak_insulation.py` (~130 LOC)
5. `src/core/maritime_chw_food_cpp_cryo_engine.py` (~100 LOC) — central aggregator
6. `src/cli/commands/maritime_chw_food_cpp_cryo_command.py` (~175 LOC) — Typer Rich CLI
7. Registered in `src/cli/app_setup.py`:
   - English: `chilledhvac`, `foodwaste`, `cpppropeller`, `cryoleak`
   - Vietnamese: `dieuhoatrungtam`, `nghienracthucpham`, `chanvitbienbuoc`, `rorikhibang`
8. Registered FastMCP tools in `scripts/mcp_server.py`:
   - `mekong_maritime_chilled_water_hvac_evaluate`
   - `mekong_maritime_food_waste_pulper_evaluate`
   - `mekong_maritime_cpp_pitch_control_evaluate`
   - `mekong_maritime_cryogenic_leak_sniff_evaluate`
9. Tests:
   - `tests/test_maritime_chw_food_unit_suite.py` (~140 LOC)
   - `tests/test_maritime_cpp_cryo_unit_suite.py` (~140 LOC)
   - `tests/test_maritime_387_to_390_cli_mcp_suite.py` (~105 LOC)
