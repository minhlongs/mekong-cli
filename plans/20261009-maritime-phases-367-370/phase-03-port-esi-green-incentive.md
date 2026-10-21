# Phase 369: World Ports Environmental Ship Index (ESI) & Green Port Dues Incentive Engine

## Context Links
- IAPH World Ports Climate Initiative (WPCI) Environmental Ship Index (ESI)
- Thông tư 39/2023/TT-BGTVT biểu khung giá dịch vụ hoa tiêu, cầu bến, phao neo cảng biển
- EU Directive 2019/883 Port Reception Facilities

## Overview
- **Priority:** High
- **Status:** Planned
- **File:** `src/core/maritime/phase_369_port_esi_green_incentive.py` (< 200 LOC)

## Requirements
- Tính toán các điểm thành phần ESI:
  - ESI_NOx: Tính dựa trên tỷ lệ cắt giảm phát thải so với giới hạn IMO Tier I/II/III.
  - ESI_SOx: Tính dựa trên hàm lượng lưu huỳnh nhiên liệu tiêu thụ (<= 0.50% hoặc scrubber <= 0.10%).
  - ESI_CO2: Cải thiện hiệu suất năng lượng EEOI/CII.
  - ESI_OPS: Thưởng nguồn điện bờ Onshore Power Supply (+35 điểm nếu trang bị).
- Điểm tổng hợp ESI_Total:
  - ESI_Total = (2 * ESI_NOx + 2 * ESI_SOx + ESI_CO2 + ESI_OPS) / 5 (giới hạn [0, 100]).
- Xếp hạng ưu đãi phí cảng biển (Port Dues Rebate):
  - ESI >= 50.0: Hạng Vàng (Giảm 20% phí trọng tải và cầu bến).
  - 30.0 <= ESI < 50.0: Hạng Bạc (Giảm 10%).
  - 20.0 <= ESI < 30.0: Hạng Đồng (Giảm 5%).
  - ESI < 20.0: Tiêu chuẩn (Không giảm).
