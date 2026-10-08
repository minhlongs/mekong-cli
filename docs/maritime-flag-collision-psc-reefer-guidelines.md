# Architecture & Design Guidelines: Phases 259-262

## 1. Mục Tiêu Thiết Kế
Triển khai bộ 4 động cơ tính toán cho:
1. `BareboatRegistrationEngine` (Phase 259)
2. `CollisionLiabilityBothToBlameEngine` (Phase 260)
3. `TokyoMOUPSCInspectionEngine` (Phase 261)
4. `PortReeferMonitoringEngine` (Phase 262)

## 2. Tiêu Chuẩn Kỹ Thuật (Strict Constraints)
- **Zero-Dependency Standard Library Rule:** Không dùng thư viện bên ngoài trong `src/core/maritime_flag_collision_psc_reefer_engine.py`. Chỉ dùng: `dataclasses`, `enum`, `typing`, `json`, `datetime`.
- **Hệ Thống CLI Typer:** Subcommands rõ ràng, có bí danh tiếng Việt, hỗ trợ `--json` output.
- **FastMCP & JSON-RPC:** Bổ sung schema trong `CORE_TOOLS_SPEC`, ánh xạ route trong `CORE_HANDLERS`, và decorator `@app.tool`.

## 3. Lược Đồ Dữ Liệu & Hợp Đồng Giao Diện
### Phase 259: Bareboat Charter Registry
- `BareboatCharterType`: `BAREBOAT_IN` (treo cờ VN), `BAREBOAT_OUT` (tạm hoãn cờ VN).
- `evaluate_bareboat_registration(...) -> BareboatRegistrationReport`
  - Kiểm tra điều kiện: Cờ gốc đã cấp Giấy phép tạm đình chỉ (Flag Suspension Cert)?
  - Thời hạn đăng ký tối đa không quá thời hạn hợp đồng thuê tàu.
  - Tỷ lệ sĩ quan/thuyền viên đáp ứng quy định quốc gia.

### Phase 260: Collision Cross-Liabilities & Both-to-Blame
- `BothToBlameSettlementResult`:
  - `vessel_a_fault_ratio`, `vessel_b_fault_ratio` (Tổng = 1.0).
  - Thiệt hại thân tàu A, thân tàu B.
  - Thiệt hại hàng hóa trên tàu A, hàng hóa trên tàu B.
  - Quyết toán thanh toán chéo (Single liability netting: $Net = (Loss_B \times Fault_A) - (Loss_A \times Fault_B)$).
  - Trách nhiệm Both-to-Blame Clause: Chủ hàng trên tàu A phải hoàn trả cho chủ tàu A khoản tiền mà chủ tàu B đã trừ từ chủ tàu A do chủ hàng kiện chủ tàu B.

### Phase 261: Tokyo MOU PSC Inspection & SRP Calculator
- `ShipRiskProfileGrade`: `LOW_RISK_SHIP` (LRS), `STANDARD_RISK_SHIP` (SRS), `HIGH_RISK_SHIP` (HRS).
- `InspectionPriorityWindow`: `PRIORITY_I` (sau 2-4 tháng), `PRIORITY_II` (sau 5-8 tháng), v.v.
- Điểm đánh giá: Flag Performance (White: 0, Grey: +1, Black: +2), RO Performance (High: 0, Medium: +1, Low: +2), Company Performance (High: -1, Medium: 0, Low: +2), Deficiencies per inspection, Detention count in 36 months (Mỗi lần bị giữ tàu: +3 điểm).

### Phase 262: Port Reefer Monitoring & Energy Tariff
- `CargoThermalClass`: `CHILLED` (+2°C to +4°C), `FROZEN` (-18°C to -25°C), `DEEP_FROZEN` (-60°C).
- `calculate_reefer_service_cost(...) -> ReeferMonitoringReport`
  - Thời gian cắm điện (giờ), Công suất danh định (kW) x Duty cycle thực tế.
  - Tổng điện năng tiêu thụ (kWh) x Biểu giá điện cảng biển (VND/kWh hoặc USD/kWh).
  - Phí cắm/rút phích cắm (Plug-in/Unplug tariff theo Thông tư 39/2023).
  - Đánh giá sai lệch nhiệt độ và chỉ số rủi ro bảo hiểm hàng hóa.
