# Phase 03: Green Port Electric Tug & Cold Ironing

**Mục tiêu:** Xây dựng micro-engine quản lý năng lượng tàu lai điện / hybrid và trạm cấp điện bờ Cold Ironing theo IEC/IEEE 80005-1/3.

## Yêu cầu Kỹ thuật
1. Kiểm tra hòa lưới cấp điện bờ (HVSC/LVSC) và công suất giới hạn trạm bờ.
2. Thuật toán bù tải đỉnh Peak Shaving: $P_{\text{shore}} = P_{\text{vessel}} - P_{\text{bat\_discharge}}$.
3. Cảnh báo dung lượng ắc quy dự phòng khẩn cấp $\text{SoC} < 20\%$.
4. Định mức năng lượng lực kéo (Bollard Pull Metric): $E_{\text{pull}} \le 0.15\text{ kWh/(ton}\cdot\text{h)}$.
5. Tính lượng phát thải giảm thiểu ($CO_2$ và $NO_x$) so với dầu MGO.
6. File code: `src/core/maritime/phase_337_electric_tug_cold_ironing.py` ($< 200\text{ LOC}$).
