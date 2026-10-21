# Phase 03: Tích hợp FastMCP Tools trong MCP Server

## 1. Mục tiêu
- Thêm 4 FastMCP tool definitions chuẩn vào `scripts/mcp_server.py` tại khu vực công cụ Hàng hải Phases 323–326.
- Đảm bảo đầy đủ kiểu dữ liệu, tài liệu mô tả chi tiết, xử lý lỗi an toàn (try/except) và trả về JSON chuẩn xác thực SHA-256 audit trail.

## 2. Danh sách FastMCP Tools
1. `mekong_tanker_cow_evaluate`:
   - Tham số: `tank_id`, `inert_gas_o2_percent`, `tank_pressure_mmwg`, `cow_machine_pressure_bar`, `remaining_sludge_volume_m3`, `max_allowable_sludge_m3`, `is_draining_dry`.
   - Kết quả: Thẩm duyệt quy trình COW theo MARPOL Annex I Reg 33/35.
2. `mekong_chemical_prewash_evaluate`:
   - Tham số: `tank_id`, `cargo_category`, `viscosity_at_unloading_temp_mpa_s`, `cargo_melting_point_c`, `unloading_temperature_c`, `stripping_residue_liters`, `effluent_concentration_ppm`, `vessel_speed_knots`, `distance_from_shore_nm`, `water_depth_meters`.
   - Kết quả: Thẩm duyệt Prewash theo IBC Code Ch.16 và điều kiện xả thải ngoài khơi.
3. `mekong_lng_bog_ctms_calculate`:
   - Tham số BOG: `cargo_volume_m3`, `lng_density_kg_per_m3`, `latent_heat_kj_per_kg`, `heat_ingress_kw`, `tank_design_marvs_kpa`, `current_tank_pressure_kpa`, `reliquefaction_capacity_kg_h`, `engine_gas_consumption_kg_h`.
   - Tham số CTMS: `ship_name`, `opening_volume_m3`, `closing_volume_m3`, `trim_list_correction_m3`, `liquid_temp_c`, `liquid_density_kg_per_m3`, `gross_calorific_value_mj_per_kg`, `vapour_return_volume_m3`, `vapour_density_kg_per_m3`.
   - Kết quả: Đánh giá BOR tự nhiên, kiểm soát áp suất và năng lượng chuyển giao (MMBtu).
4. `mekong_lifeboat_fpd_safety_evaluate`:
   - Tham số: `lifeboat_id`, `release_mode`, `lifeboat_total_weight_kg`, `hook_swl_tonnes`, `fpd_sling_mbl_tonnes`, `hydrostatic_interlock_engaged`, `hook_cam_wear_mm`, `fpd_pins_fitted`, `emergency_override_used`.
   - Kết quả: Đánh giá hệ số an toàn FPD, rủi ro tự bật móc và phê duyệt thả xuồng.
5. `mekong_enclosed_space_permit_evaluate`:
   - Tham số: `space_name`, `oxygen_percent`, `flammable_lel_percent`, `hydrogen_sulfide_ppm`, `carbon_monoxide_ppm`, `mechanical_ventilation_hours`, `ventilation_turnover_adequate`, `standby_person_equipped`, `pipes_isolated_blanked`.
   - Kết quả: Cấp giấy phép vào không gian kín 8 giờ theo IMO Res. A.1050(27).

## 3. Checklist Thực hiện
- [x] Định nghĩa các hàm tool với `@mcp.tool()` trong `scripts/mcp_server.py`.
- [x] Kiểm tra cú pháp script: `python3 -m py_compile scripts/mcp_server.py`.
