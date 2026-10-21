# Design Guidelines: Maritime Phases 383–386

## Overview
Bộ hướng dẫn thiết kế chuẩn hóa cho giao diện Dòng lệnh (CLI Rich Terminal), Dashboard Tàu biển, và Phản hồi FastMCP đối với 4 phân hệ kỹ thuật nâng cao:
1. Centrifugal Fuel Purifier Automation (Phase 383)
2. Auxiliary Emergency Steering Gear (Phase 384)
3. Rapid Anti-Heeling Ballast Control (Phase 385)
4. Tanker Pump Room Atmospheric Gas Sniffer (Phase 386)

## Palette & Design Tokens
- **Bình thường / An toàn (Safe/Optimal)**: `green` / `#10B981` (Tách lọc đạt chuẩn, góc nghiêng < 1.0°, khí hydrocarbon < 10% LEL).
- **Cảnh báo Tiền nguy cấp (Warning/Elevated)**: `yellow` / `#F59E0B` (Nghiêng 1.0°-1.5°, cặn Al+Si ra > 15 ppm, H2S 5-10 ppm, áp suất thủy lực sụt).
- **Báo động Khẩn cấp (Critical Alarm / Trip)**: `bold red` / `#EF4444` (Khí hydrocarbon >= 20% LEL, H2S >= 10 ppm, góc nghiêng > 2.5°, rò rỉ buồng bơm, mất lái).
- **Chỉ số Kỹ thuật (Technical Metrics)**: `cyan` / `magenta` (G-force, RPM, thời gian bẻ lái giây, lưu lượng bơm m3/h).

## CLI Formatting & Layout Structure
- Banner song ngữ tiếng Việt & tiếng Anh với khung viền Rich Panel.
- Bảng hiển thị thông số chi tiết chia 3 cột: `Thông số / Metric`, `Giá trị / Value`, `Trạng thái / Status`.
- Cảnh báo và khuyến nghị an toàn biên theo đúng tiêu chuẩn SOLAS và IMO.
