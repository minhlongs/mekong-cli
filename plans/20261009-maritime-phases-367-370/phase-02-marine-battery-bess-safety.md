# Phase 368: Marine Battery Energy Storage System (BESS) & Peak Shaving Safety Engine

## Context Links
- DNV-RU-SHIP Pt.6 Ch.2 Battery(Power/Safety)
- IEC 62619 Industrial Secondary Lithium Cells and Batteries
- IMO MSC.1/Circ.1455 Guidelines for the Approval of Battery Systems

## Overview
- **Priority:** High
- **Status:** Planned
- **File:** `src/core/maritime/phase_368_marine_battery_bess_safety.py` (< 200 LOC)

## Requirements
- Đánh giá cửa sổ vận hành SoC (State of Charge):
  - Dải an toàn: 15.0% <= SoC <= 90.0%.
- Giám sát độ thoái hóa cell pin SoH (State of Health):
  - Cảnh báo: SoH < 80.0%.
  - Loại thải EOL: SoH <= 70.0%.
- Tốc độ sạc/xả C-rate:
  - Định mức liên tục: C <= 1.0C.
  - Xung phụ tải đỉnh (Peak Shaving): C_pulse <= 2.5C.
- Chênh lệch nhiệt độ giữa các cell:
  - Delta T <= 5.0°C; T_max <= 45.0°C.
- Hệ thống bảo vệ an toàn 3 cấp (Thermal Runaway Early Warning):
  - Khí thoát nguy hiểm: H2 >= 50 ppm hoặc CO >= 25 ppm.
  - Cấp 1 (Alarm & De-rate): T > 45°C hoặc Delta T > 5°C.
  - Cấp 2 (Electrical Contactor Trip): T > 55°C hoặc nồng độ khí H2/CO vượt ngưỡng.
  - Cấp 3 (Fire Suppression): T > 75°C kích hoạt xả sương nước áp lực cao (Water Mist Deluge).
