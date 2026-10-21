# Implementation Plan: Phases 311-314 Simplest Viable Maritime Suite

## Executive Overview
Triển khai bộ 4 nghiệp vụ hàng hải và giám định thực tế theo kiến trúc Simplest Viable:
- **Phase 311**: Bunkering Mass Flow Meter (MFM) Discrepancy & Dispute Resolver (SS 600 / SS 648, dung sai 0.5%, cảnh báo Cappuccino bunker, tự động sinh Notice of Protest hash).
- **Phase 312**: Seaport Pilotage Booking & Tidal Window Clearance (Quy chuẩn TT 39/2023/TT-BGTVT, UKC an toàn theo đỉnh triều, định vị cửa sổ hành hải an toàn & tính biểu phí hoa tiêu).
- **Phase 313**: Draft Survey Cargo Displacement & Constant Calculator (Chuẩn UN ECE Draft Survey Code, Mean of Means Draft D_QM, Trim Correction 1st & 2nd, Density Correction, Net Cargo Loaded).
- **Phase 314**: Reefer Container Temperature Excursion & Cargo Claim Analyzer (Phân tích lệch nhiệt độ container lạnh theo Degree-Hours, phân xử trách nhiệm giữa Terminal vs Carrier vs Shipper).

---

## Technical Specifications & Interfaces

### 1. File Structure
- **Core Engine**: `src/core/maritime_bunker_pilot_draft_reefer_engine.py`
  - `BunkerMfmDisputeEngine`: Xử lý chênh lệch MFM sà lan vs Sounding tàu, tolerance 0.5%, kiểm tra bọt khí Cappuccino.
  - `PilotageTidalWindowEngine`: Tính UKC tĩnh/động, tìm slot hoa tiêu qua luồng nước cạn dựa trên bảng thủy triều giờ.
  - `DraftSurveyEngine`: Tính Quarter Mean Draft (D_QM), Trim thực tế, hiệu chỉnh dãn nước, tính sản lượng xếp dỡ tịnh.
  - `ReeferClaimEngine`: Tính độ lệch nhiệt độ tích lũy (Degree-Hours), xác định trách nhiệm tranh chấp tổn thất hàng đông lạnh.
- **Unit Tests**: `tests/test_maritime_bunker_pilot_draft_reefer_suite.py` (zero-mock, 100% deterministic).
- **Typer CLI**: `src/cli/commands/maritime_bunker_pilot_draft_reefer_command.py`
  - 4 sub-app: `mfm_app`, `pilot_app`, `draft_app`, `reefer_claim_app`.
- **CLI Registration**: `src/cli/app_setup.py`
  - Nhóm lệnh: `mfm`/`tranhchapdau`, `pilotwindow`/`hoatieuthuytrieu`, `draftsurvey`/`giamdinhton`, `reeferclaim`/`khieunailanh`.
- **FastMCP Tools**: `scripts/mcp_server.py`
  - `mekong_bunker_mfm_dispute_check`
  - `mekong_pilotage_tidal_window_evaluate`
  - `mekong_draft_survey_displacement_calculate`
  - `mekong_reefer_claim_analyze`

---

## Execution Steps
1. Khởi tạo plan file và đăng ký task.
2. Viết mã nguồn Core Engine `maritime_bunker_pilot_draft_reefer_engine.py`.
3. Viết test suite `test_maritime_bunker_pilot_draft_reefer_suite.py` và chạy pytest verify 100% pass.
4. Xây dựng CLI commands trong `maritime_bunker_pilot_draft_reefer_command.py`.
5. Đăng ký lệnh vào `app_setup.py` và tools vào `mcp_server.py`.
6. Cập nhật Memory và Git commit.
