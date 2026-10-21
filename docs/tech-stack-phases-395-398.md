# Tech Stack: Maritime Phases 395-398

## 1. System Components
- **Language & Runtime:** Python 3.9+ / 3.14 (system standard).
- **Core Computational Engines:** Strictly pure Python standard libraries (`math`, `dataclasses`, `typing`, `enum`) for zero external overhead and high determinism.
- **CLI Framework:** Typer with Rich console tables, banners, and bilingual help formatting.
- **Protocol & Model Serving:** FastMCP tool registrations in `scripts/mcp_server.py`.
- **Testing Framework:** Pytest with zero mocking (`tests/`).

## 2. Engineering Dataclasses & Signatures

### Phase 395: EGCS SOx Scrubber (`phase_395_egcs_sox_wet_scrubber.py`)
- **Inputs:** `so2_ppm`, `co2_pct`, `washwater_ph`, `inlet_pah_ug_l`, `discharge_pah_ug_l`, `turbidity_fnu`, `operating_mode` (`OPEN_LOOP`, `CLOSED_LOOP`, `HYBRID`), `in_eca_or_restricted_port`.
- **Outputs:** `emission_ratio`, `mepc_340_77_compliant`, `sox_washwater_status`, `naoh_dosing_active`, `discharge_lockout`, `warnings`.

### Phase 396: Vacuum Plate FWG (`phase_396_vacuum_fresh_water_generator.py`)
- **Inputs:** `jacket_water_temp_c`, `evaporator_vacuum_bar`, `distillate_salinity_ppm`, `feed_seawater_flow_m3_h`, `distillate_flow_m3_h`.
- **Outputs:** `evaporator_boiling_temp_c`, `distillate_purity_status`, `three_way_dump_valve`, `scale_formation_risk`, `thermal_efficiency_pct`, `warnings`.

### Phase 397: Deck Crane Anti-Sway & Dynamic SWL (`phase_397_deck_crane_anti_sway_swl.py`)
- **Inputs:** `hook_load_tonnes`, `boom_radius_m`, `boom_angle_deg`, `significant_wave_height_m`, `sway_pendulum_angle_deg`, `hoist_wire_wraps`.
- **Outputs:** `dynamic_swl_tonnes`, `load_moment_ton_m`, `swl_utilization_pct`, `anti_sway_dampening_command`, `hoisting_safety_cutoff`, `warnings`.

### Phase 398: UTM Hull Gauging & Wastage Limits (`phase_398_utm_hull_gauging_corrosion.py`)
- **Inputs:** `plate_location_category` (`CATEGORY_A_STRENGTH_DECK_BOTTOM`, `CATEGORY_B_SIDE_SHELL_BULKHEAD`, `CATEGORY_C_INTERNAL_STIFFENER`), `original_as_built_thickness_mm`, `gauged_actual_thickness_mm`, `pitting_depth_mm`, `pitting_density_pct`.
- **Outputs:** `wastage_percentage`, `allowable_wastage_percentage`, `substantial_corrosion_detected`, `renewal_steel_required`, `survey_action_status`, `warnings`.

## 3. Constraints & Design Rules
- Line count ceiling: strictly `< 200 LOC` per module.
- Zero mock dependencies across all unit and integration test assertions.
- Bilingual CLI aliases in Vietnamese & English.
