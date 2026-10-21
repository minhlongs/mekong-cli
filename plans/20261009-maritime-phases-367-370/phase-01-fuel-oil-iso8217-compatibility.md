# Phase 367: Marine Fuel Oil Quality Assessment & ISO 8217 Bunker Compatibility Engine

## Context Links
- ISO 8217:2024 Marine Fuel Standard
- CIMAC Guidelines on Fuel Treatment & Cat Fines
- ASTM D4740 Cleanliness and Compatibility Test

## Overview
- **Priority:** High
- **Status:** Planned
- **File:** `src/core/maritime/phase_367_fuel_oil_iso8217_compatibility.py` (< 200 LOC)

## Requirements
- Kiểm tra nồng độ mạt xúc tác Al + Si:
  - Ngưỡng giới hạn ISO 8217: <= 60.0 mg/kg.
  - Ngưỡng cảnh báo CIMAC trước máy lọc ly tâm: <= 25.0 mg/kg.
- Kiểm tra điểm chớp cháy Pensky-Martens Closed Cup:
  - Bắt buộc SOLAS: T_flash >= 60.0°C.
- Phân tích cặn tiềm năng (Total Sediment Potential - TSP):
  - Giới hạn: TSP <= 0.10% m/m.
- Đánh giá tương thích phối trộn nhiên liệu theo ASTM D4740 Spot Test (thang điểm 1 đến 5):
  - Điểm 1-2: Tương thích tốt (COMPATIBLE).
  - Điểm 3: Ranh giới rủi ro kết tủa (BORDERLINE).
  - Điểm 4-5: Không tương thích, nguy cơ tắc lọc (INCOMPATIBLE).
- Đưa ra khuyến nghị nhiệt độ hâm sấy để đạt độ nhớt vòi phun 10-15 cSt.
