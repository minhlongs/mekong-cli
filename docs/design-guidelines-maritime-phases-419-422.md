# Hướng dẫn Thiết kế Giao diện & Trực quan hóa Dữ liệu: Maritime Phases 419–422

## 1. Màu sắc & Bảng mã Trạng thái (Design Tokens)
- **Cảnh báo Nguy cấp (Critical Alarm / Trip)**: Đỏ (#EF4444)
  - EGR Bleed-off: Dầu $\ge 15\,\text{ppm}$, pH $< 6.5$ hoặc độ đục $\ge 25\,\text{FNU}$.
  - Shaft Gen AFE: $\text{THD}_V > 5.0\%$, ngắt công suất ngược $<-5\%$.
  - BWMS: TRO xả mạn $> 0.10\,\text{mg/L}$ hoặc $H_2 > 25\%\,\text{LEL}$.
  - Stern Thruster: Chỉ số xâm thực $\sigma < 0.85$, rung động $> 7.1\,\text{mm/s}$.
- **Cảnh báo Suy giảm / Điều chỉnh (Warning / Advisory)**: Vàng Hổ phách (#F59E0B)
  - EGR WTS: Đang chuyển van hồi lưu về két giữ (holding tank).
  - AFE: Méo sóng hài đơn lẻ tiến sát $3.0\%$.
  - BWMS: TRO đầu vào điện phân $< 1.5\,\text{mg/L}$.
  - Stern Thruster: Giảm góc bước cánh bướm tự động (derate pitch).
- **Trạng thái Hoạt động Bình thường (Normal / Compliant)**: Xanh Lục (#10B981)
  - Tất cả các tham số nằm trong dải quy chuẩn IMO MARPOL, IACS UR E24, BWM D-2, DNV Pt.4.
- **Nền Giao diện & Phông chữ (Theme & Typography)**:
  - Nền tối buồng điều khiển máy (Dark Mode): `#0F172A` / `#1E293B`.
  - Phông chữ kỹ thuật: Inter / JetBrains Mono hiển thị telemetry thời gian thực.

## 2. Bố cục 4 Bảng Điều khiển (Cockpit Sections)
1. **EGR Bleed-off Water Treatment Monitor**: Đồng hồ đo nồng độ dầu (ppm), cảm biến pH quang học, độ đục FNU, van 3 ngả xả mạn / két gom.
2. **Shaft Generator AFE & THD Grid Quality**: Phổ sóng hài 50Hz/60Hz, tổng biến dạng sóng hài $\text{THD}_V$, công suất phản kháng và dòng điện busbar.
3. **BWMS Electro-Chlorination & Neutralization**: Đo lường TRO nạp dằn, nồng độ $H_2$ tế bào điện phân, liều lượng chất trung hòa $Na_2S_2O_3$ và TRO xả mạn.
4. **Stern Thruster & Cavitation Acoustic Cockpit**: Góc bước cánh bướm CPP, áp suất hút đường hầm, hệ số xâm thực $\sigma$, cảm biến âm học siêu âm $10\text{--}40\,\text{kHz}$.
