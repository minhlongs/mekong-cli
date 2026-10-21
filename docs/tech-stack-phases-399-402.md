# Tech Stack: Maritime Phases 399-402

## 1. System Components
- **Language & Runtime:** Python 3.9+ / 3.14 (system standard).
- **Core Computational Engines:** Strictly pure Python standard libraries (`math`, `dataclasses`, `typing`, `enum`) for zero external overhead, mathematical accuracy, and determinism.
- **CLI Framework:** Typer with Rich console tables, banners, and bilingual help formatting.
- **Protocol & Model Serving:** FastMCP tool registrations in `scripts/mcp_server.py`.
- **Testing Framework:** Pytest with zero mocking (`tests/`).

## 2. Engineering Dataclasses & Signatures

### Phase 399: Marine Bow Thruster Thrust & Pitch (`phase_399_bow_thruster_thrust_pitch.py`)
- **Standards:** SOLAS II-1 Reg 29, DNV-RU-SHIP Pt.4 Ch.5, ISO 484-1/2.
- **Inputs:** `pitch_ratio_p_d`, `tunnel_rpm`, `tunnel_diameter_m`, `vessel_speed_knots`, `hydraulic_oil_temp_c`, `lube_oil_pressure_bar`, `header_tank_level_pct`, `motor_rated_kw`.
- **Outputs:** `net_thrust_kn`, `cavitation_number`, `cavitation_risk_status`, `electrical_load_kw`, `power_limit_active`, `hydraulic_interlock_status`, `warnings`.

### Phase 400: Inflatable Liferaft & Hydrostatic Release Unit (`phase_400_inflatable_liferaft_hru_release.py`)
- **Standards:** SOLAS III Reg 13/20/31, IMO LSA Code Chapter IV.
- **Inputs:** `submersion_depth_m`, `weak_link_tension_kn`, `painter_line_deployed_m`, `stowage_height_m`, `ambient_temp_c`, `hru_service_age_months`, `liferaft_service_age_months`.
- **Outputs:** `hydrostatic_actuation_triggered`, `weak_link_parted`, `free_float_status`, `painter_length_compliant`, `service_validity_status`, `warnings`.

### Phase 401: Shipboard Waste High-Temp Incinerator (`phase_401_waste_incinerator_gasification.py`)
- **Standards:** IMO MARPOL Annex V Reg 16, Resolution MEPC.244(66).
- **Inputs:** `primary_chamber_temp_c`, `secondary_chamber_temp_c`, `residence_time_s`, `flue_gas_co_mg_mj`, `oxygen_content_pct`, `smoke_density_ringelmann`, `draft_pressure_pa`, `flame_detected`.
- **Outputs:** `combustion_efficiency_status`, `waste_charging_permitted`, `flue_emissions_compliant`, `safety_trip_active`, `dioxin_destruction_verified`, `warnings`.

### Phase 402: Marine Vapor Emission Control System (`phase_402_vapor_emission_control_vecs.py`)
- **Standards:** IMO MSC/Circ.585, USCG 46 CFR Part 39.
- **Inputs:** `manifold_pressure_bar`, `cargo_ullage_pct`, `vapor_oxygen_pct`, `detonation_arrester_dp_bar`, `arrester_temp_c`, `loading_rate_m3_h`.
- **Outputs:** `vapor_pressure_status`, `overfill_protection_level`, `oxygen_hazard_status`, `cargo_pumping_permitted`, `vent_valve_status`, `warnings`.

## 3. Constraints & Design Rules
- Line count ceiling: strictly `< 200 LOC` per module.
- Zero mock dependencies across all unit and integration test assertions.
- Bilingual CLI aliases in Vietnamese & English.
