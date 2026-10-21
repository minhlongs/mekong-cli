# Phase 370: Mooring Winch Auto-Tension & Active Heave Compensation (AHC) Engine

## Context Links
- OCIMF MEG4 Mooring Equipment Guidelines
- ISO 3730 Shipbuilding - Mooring Winches
- IMCA D 018 Heave Compensation Systems

## Overview
- **Priority:** High
- **Status:** Planned
- **File:** `src/core/maritime/phase_370_mooring_autotension_ahc.py` (< 200 LOC)

## Requirements
- Kiểm soát Lực căng Tự động Auto-Tension:
  - Lực căng mục tiêu T_target: 15% - 25% MBL (Minimum Breaking Load).
  - Ngưỡng nhả tự động (Auto-Render): T_line >= 1.25 * T_target (xả cáp tránh đứt).
  - Ngưỡng thu tự động (Auto-Heave): T_line <= 0.75 * T_target (thu cáp ép mạn tàu).
- Bù chuyển vị đứng do sóng AHC (Active Heave Compensation):
  - Đo chuyển vị nhấp nhô tàu: z_ship(t) = A_h * sin(omega * t).
  - Vòng điều khiển Feedforward bù trừ vận tốc tời: v_winch(t) = - dz_ship/dt.
  - Hiệu suất bù nhấp nhô: eta_AHC = (1 - RMS(z_load) / RMS(z_ship)) * 100% >= 85.0%.
  - Cảnh báo quá tải công suất hoặc vận tốc tời vượt giới hạn an toàn.
