# Báo Cáo Brainstorming Chuyên Sâu: Hàng Hải Nâng Cao Phases 383–386 (Maritime AC Suite)

## 1. Tóm tắt Định hướng Chiến lược (Executive Summary)
Tiếp nối thành công của việc hoàn thành và bàn giao 100% xanh cho Maritime Phases 379–382 (Starting Air, Seachest Ingress, Draft Tank Sounding, Port Pilotage ARPA), giai đoạn kế tiếp **Phases 383–386** sẽ tập trung vào các hệ thống tự động hóa cơ điện thủy, an toàn buồng máy và phòng chống sự cố nguy cấp trên tàu thương mại và tàu chở dầu/container hiện đại:
1. **Phase 383: Tự động hóa Máy lọc Dầu Ly tâm & Phân ly Cặn Nhiên liệu (Marine Centrifugal Fuel Oil Purifier & Clarifier Automation)** theo ISO 8217:2024, CIMAC và MEPC.1/Circ.753.
2. **Phase 384: Hệ thống Lái Phụ Khẩn cấp & Trạm Thủy lực Trợ lực Lái Độc lập (Auxiliary Emergency Steering Gear & Hydraulic Actuation)** theo SOLAS II-1 Quy định 29/30 và IMO Res. A.1052(27).
3. **Phase 385: Hệ thống Bơm Dằn Tự động Chống Nghiêng Tàu Container (Automatic Anti-Heeling Ballast Pumping & Rapid Counter-Flooding)** theo IMO Res. MSC.267(85) và hướng dẫn phân cấp DNV/IACS.
4. **Phase 386: Giám sát Khí Hydrocarbon & Ngửi Khí Tự động Buồng Bơm Tàu Dầu (Tanker Pump Room Atmospheric Hydrocarbon & Bilge Gas Sniffer Detection)** theo SOLAS II-2 Reg 4.5.10 và ISGOTT Ch. 5.

---

## 2. Phân tích Chi tiết Từng Phase

### Phase 383: Marine Fuel Purifier & Clarifier Automation (ISO 8217, CIMAC)
- **Mục tiêu**: Tối ưu hóa việc lọc tạp chất rắn và tách nước khỏi dầu cặn nặng (HFO/VLSFO), đặc biệt là hạt xúc tác nhôm-silic (Al+Si cat fines) nguy cơ gây xước nòng xy-lanh động cơ chính.
- **Công thức cốt lõi**:
  - Hệ số tách ly tâm $G = r \omega^2 / g \approx 5,000 - 7,500\times g$.
  - Hiệu suất lọc Al+Si: $\eta = (C_{\text{in}} - C_{\text{out}}) / C_{\text{in}} \ge 85\%$, kiểm soát $C_{\text{out}} \le 15.0\text{ ppm}$.
  - Nhiệt độ hâm sấy phân ly HFO: $98^\circ\text{C} \pm 2^\circ\text{C}$.
  - Giám sát rung động ISO 10816-3: Vận tốc rung $v \le 7.1\text{ mm/s RMS}$.
  - Chu kỳ xả cặn tự động: $\le 2.0\text{ giờ}$ kèm kiểm tra áp suất nước mở bát $P \ge 2.5\text{ bar}$.

### Phase 384: Auxiliary Emergency Steering Gear (SOLAS II-1 Reg 29/30)
- **Mục tiêu**: Đảm bảo năng lực điều động bánh lái trong điều kiện sự cố mất nguồn hoặc hỏng trạm lái chính.
- **Quy chuẩn thời gian SOLAS**:
  - Lái chính: Bẻ bánh lái từ $35^\circ$ mạn này sang $30^\circ$ mạn kia trong thời gian $\le 28.0\text{ giây}$ ở tốc độ khai thác lớn nhất.
  - Lái sự cố: Bẻ từ $15^\circ$ mạn này sang $15^\circ$ mạn kia trong $\le 60.0\text{ giây}$ ở tốc độ $\max(0.5 V_{\text{max}}, 7.0\text{ knots})$.
  - Nguồn điện khẩn cấp tự động khởi động và cấp tải cho bơm lái dự phòng trong vòng $\le 45.0\text{ giây}$.
  - Cảnh báo lệch góc lái: $|\theta_{\text{demand}} - \theta_{\text{actual}}| > 4.0^\circ$ kéo dài $\ge 3.0\text{ giây}$.
  - Mức dầu két giãn nở thủy lực: Báo động khi tụt dưới $40\%$.

### Phase 385: Anti-Heeling Ballast Pumping & Rapid Counter-Flooding (IMO MSC.267(85))
- **Mục tiêu**: Giữ tàu container cân bằng ngang khi cẩu bờ bốc xếp container nhanh (twin-lift, tandem-lift).
- **Quy chuẩn ổn định**:
  - Giới hạn góc nghiêng tĩnh cho phép khi làm hàng: $|\theta| \le 1.0^\circ$.
  - Ngưỡng cảnh báo: $|\theta| > 1.5^\circ$.
  - Ngưỡng dừng khẩn cấp bốc dỡ hàng: $|\theta| \ge 2.5^\circ$.
  - Bơm thuận nghịch công suất lớn ($Q \ge 1,000\text{ m}^3\text{/h}$) kích hoạt tự động khi tốc độ nghiêng $d\theta/dt > 0.15^\circ/\text{s}$.
  - Khóa liên động mức két dằn mạn: Không bơm khi két nguồn $< 5\%$ hoặc két đích $> 95\%$.

### Phase 386: Tanker Pump Room Hydrocarbon & Gas Sniffer (SOLAS II-2 Reg 4.5.10, ISGOTT)
- **Mục tiêu**: Giám sát liên tục môi trường khí quyển buồng bơm tàu dầu ngăn ngừa cháy nổ và nhiễm độc.
- **Ngưỡng nồng độ khí**:
  - Hydrocarbon: Báo động sớm tại $\ge 10.0\%\text{ LEL}$; Báo động nguy cấp & tự động ngắt bơm hàng tại $\ge 20.0\%\text{ LEL}$.
  - Khí độc $H_2S$: Cảnh báo tại $\ge 5.0\text{ ppm}$; Báo động khẩn cấp sơ tán tại $\ge 10.0\text{ ppm}$.
  - Nồng độ $O_2$: Bình thường $\ge 20.8\%$; Cảnh báo thiếu khí tại $< 19.5\%$.
  - Khóa liên động thông gió: Tối thiểu 20 lần trao đổi khí/giờ ($\ge 20\text{ ACH}$); ngắt bơm hàng nếu quạt thông gió dừng hoặc mất chênh áp.
  - Phao chống ngập la-gông buồng bơm: Cảnh báo mức nước đọng đáy $> 0.30\text{ m}$.

---

## 3. Kiến trúc Triển khai & Ranh giới Module (< 200 LOC)
1. `src/core/maritime/phase_383_marine_fuel_purifier_clarifier.py` (~120 LOC)
2. `src/core/maritime/phase_384_auxiliary_emergency_steering.py` (~130 LOC)
3. `src/core/maritime/phase_385_anti_heeling_ballast_pumping.py` (~125 LOC)
4. `src/core/maritime/phase_386_tanker_pumproom_gas_sniffer.py` (~135 LOC)
5. `src/core/maritime_purifier_steering_heeling_sniffer_engine.py` (~140 LOC - Central Facade)
6. `src/cli/commands/maritime_purifier_steering_heeling_sniffer_command.py` (~160 LOC - Bilingual CLI)
7. `scripts/mcp_server.py` (Bổ sung 4 FastMCP tools)
8. Các unit & CLI test suites (`tests/test_maritime_purifier_steering_unit_suite.py`, `tests/test_maritime_heeling_sniffer_unit_suite.py`, `tests/test_maritime_383_to_386_cli_mcp_suite.py`, mỗi file < 185 LOC).

---

## 4. Kế hoạch Hành động Kế tiếp (Next Steps)
1. Người dùng xác nhận hoặc kích hoạt lệnh triển khai code thực tế cho Maritime Phases 383–386.
2. Tiến hành triển khai song song các engine lõi tuân thủ tuyệt đối quy tắc `< 200 LOC` và zero-mock test.
