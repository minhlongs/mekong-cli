# Deep Architecture Brainstorming: Maritime Phases 543-546 & Quantitative Waves 304-306

## Brainstorm Contract (`/ak-brainstorm --deep`)
- **Outcome:** Ship Maritime Safety Auxiliary Batch 21 (Phases 543–546) in `mekong-cli` and Quantitative Desk Models Waves 304–306 in `algo-trader`.
- **Constraints:** Every new source and test file strictly $< 85\text{ LOC}$; zero mocks; zero `:any` types; bilingual Typer CLI group (`maritime-aux21` / `phukienhanghai21`).
- **Non-goals:** Modifying unrelated funnels or external network services.
- **Acceptance Criteria:** `pytest` 6/6 green (`ruff` 0 errors) in `mekong-cli` and `vitest` 3/3 green in `algo-trader`.

---

## Track 1: Maritime Automation Safety Systems — Batch 21 (Phases 543-546)

### Phase 543: Main Engine Selective Catalytic Reduction (SCR) Urea Dosing & Ammonia Slip Interlock
- **Regulatory Framework:** MARPOL Annex VI Reg. 13 (NOx Tier III), IMO Res. MEPC.291(71) & MAN B&W / WinGD SCR Standards.
- **Physical Dynamics & Interlocks:**
  - Catalyst temperature $> 450.0^\circ\text{C}$ triggers `CATALYST_THERMAL_SINTERING_BYPASS_TRIP` (`urea_dosing_valve_open=False`, `reactor_bypass_valve_open=True`).
  - Exhaust temperature below the ammonium bisulfate ($\text{NH}_4\text{HSO}_4$) condensation threshold ($< 310.0^\circ\text{C}$ for sulfur $> 0.10\%$, or $< 270.0^\circ\text{C}$ for ULSFO) triggers `LOW_TEMP_BISULFATE_FOULING_DOSING_CUTOFF` (`urea_dosing_valve_open=False`, `reactor_bypass_valve_open=True`).
  - Ammonia slip $\ge 10.0\text{ ppm}$ triggers `HIGH_AMMONIA_SLIP_DOSING_TRIM_ALARM`.
  - Catalyst bed $\Delta P \ge 2.5\text{ kPa}$ triggers `CATALYST_SOOT_FOULING_PURGE_WARN` (`compressed_air_sootblow_purge_cmd=True`).

### Phase 544: Cargo Tank High-Velocity P/V Breaker & Inert Gas Mast Riser Flame Screen Supervision
- **Regulatory Framework:** SOLAS II-2 Reg. 4.5.3 / 11.6, IMO MSC/Circ.677 & OCIMF ISGOTT 6th Ed.
- **Physical Dynamics & Interlocks:**
  - Cargo tank pressure $\ge +24.0\text{ kPa}$ or vacuum $\le -7.0\text{ kPa}$ triggers `PV_BREAKER_BLOWOUT_CARGO_TRANSFER_TRIP` (`cargo_transfer_emergency_stop_cmd=True`).
  - Mast riser flame screen temperature $\ge 75.0^\circ\text{C}$ triggers `MAST_RISER_VENT_FIRE_N2_SNUFFING_TRIP` (`cargo_transfer_emergency_stop_cmd=True`, `mast_riser_n2_snuffing_open=True`).
  - P/V breaker liquid seal column $< 1600.0\text{ mmWG}$ triggers `PV_BREAKER_LIQUID_SEAL_LOW_LEVEL_ALARM`.

### Phase 545: Azimuth Podded Propulsor (Azipod) Slewing Seal, Pod Air-Cooling & Stator Winding Supervision
- **Regulatory Framework:** IACS UR M65 / E11, DNV Pt.4 Ch.5 & SOLAS II-1 Reg. 29.
- **Physical Dynamics & Interlocks:**
  - Stator winding temperature $\ge 155.0^\circ\text{C}$ or pod bilge water ingress $\ge 25.0\text{ L}$ triggers `POD_CRITICAL_STATOR_OR_INGRESS_PROPULSION_DERATE` (`propulsion_power_derate_cmd=True`, `standby_slewing_pump_cut_in=True`).
  - Stator winding temperature $\ge 135.0^\circ\text{C}$ or cooling air $> 55.0^\circ\text{C}$ triggers `STATOR_THERMAL_PRE_ALARM_COOLING_BOOST`.
  - Slewing hydraulic pressure $< 140.0\text{ bar}$ triggers `SLEWING_HYDRAULIC_LOW_PRESSURE_STANDBY_CUTIN`.

### Phase 546: Liquefied Gas Carrier (LNG/LPG) Emergency Shutdown (ESD-1 / ESD-2) & Dry-Break ERC Interlock
- **Regulatory Framework:** IMO IGC Code Ch. 18.10, SIGTTO ESD Guidelines & ISO 28460.
- **Physical Dynamics & Interlocks:**
  - Vessel surge drift-off $\ge 3.5\text{ m}$ (ESD-2 envelope) or manifold drip tray temperature $\le -110.0^\circ\text{C}$ triggers `ESD2_DRY_BREAK_ERC_DECOUPLE_TRIP` (`esd1_manifold_valves_close_cmd=True`, `esd2_erc_collar_release_cmd=True`, `cargo_pumps_compressors_trip_cmd=True`).
  - Surge drift-off $\ge 2.0\text{ m}$ (ESD-1 envelope) or lost ship-shore link triggers `ESD1_MANIFOLD_SHUTDOWN_TRIP`.
  - ERC hydraulic accumulator pressure $< 165.0\text{ bar}$ triggers `ERC_HYDRAULIC_ACCUMULATOR_LOW_WARN`.

---

## Track 2: Institutional Quantitative Trading Models — Waves 304-306

### Wave 304: Cont, Kukanov & Stoikov (2014) — Multi-Level Deep Queue Order Flow Imbalance (Deep OFI)
- Distance-weighted multi-level OFI across $M$ levels normalized by average queue depth.

### Wave 305: Guéant & Lehalle (2015) — General Intensity & Power-Law Target POV Schedule
- Optimal participation rate $\rho^*_t$ balancing power-law execution cost $\eta \rho^{1+\phi}$ against inventory variance penalty.

### Wave 306: Gatheral, Jaisson & Rosenbaum (2018) — Hawkes Endogeneity & Rough Volatility Link
- Connects Hawkes branching ratio $\alpha_T \in (0, 1)$ and power-law kernel exponent $\beta \in (0.5, 1.0)$ to the rough Hurst exponent $H = \beta - 0.5$ and endogenous variance multiplier $(1 - \alpha_T)^{-2}$.
