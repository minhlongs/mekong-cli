# Hướng dẫn Thiết kế Giao diện & Trực quan hóa Dữ liệu: Maritime Phases 379–382

## 1. Bảng Màu & Chỉ báo Trạng thái (Design Tokens)
- **Cảnh báo Nguy cấp (Critical Alarm / Trip)**: Đỏ (#EF4444) — Áp suất khí khởi động $< 12.0\text{ bar}$ (không thể đề máy), chênh áp lưới lọc đáy $\Delta P > 0.5\text{ bar}$ (nguy cơ mất nước làm mát), két chất lỏng báo động tràn $> 98\%$, mục tiêu ARPA $\text{CPA} < 1.0\text{ NM}$ và $\text{TCPA} < 12.0\text{ phút}$.
- **Cảnh báo Suy giảm (Warning / Degraded)**: Vàng Hổ phách (#F59E0B) — Tốc độ đón hoa tiêu $> 8.0\text{ knots}$, két báo động mức cao $> 95\%$, xả nước đọng bình khí quá hạn, nhiệt độ nước biển $< 2^\circ\text{C}$ kích hoạt sấy hơi.
- **Tuân thủ Hoàn toàn (Compliant / Normal)**: Xanh Lục (#10B981) — Áp suất bình khí $\ge 30.0\text{ bar}$, nạp đầy $< 1.0\text{ giờ}$, MGPS hoạt động chuẩn, mớn nước cân bằng, hành lang hoa tiêu an toàn.
- **Chủ đề Hàng hải Kỹ thuật số (Maritime Dark Theme)**: Nền tối Deep Navy (#0F172A), Slate Blue (#1E293B), Điểm nhấn Radar Cyan (#06B6D4).

## 2. Bố cục Hiển thị Dữ liệu (Component Layout)
- **Starting Air & Compressor Dashboard**: Đồng hồ đo áp suất kép (Dual Receivers), trạng thái máy nén 1 & 2, số lần khởi động khả dụng ($N_{\text{starts}} \ge 12$), thời gian xả nước tự động.
- **Seachest & Cooling Ingress Monitor**: Sơ đồ van hút đáy cao/thấp (High/Low Seachest), đồng hồ chênh áp phin lọc $\Delta P$, dòng điện phân MGPS ($I_{\text{mgps}}$), nhiệt độ nước làm mát vào/ra.
- **Draft Hydrostatics & Tank Sounding Gauging**: Mô hình 3D thân tàu hiển thị mớn nước Mũi/Lái/Mạn (Fore/Aft/Mid), góc nghiêng $\theta$, độ võng $h_{\text{sag}}$, biểu đồ cột mức dung tích các két (Ballast/HFO/MDO).
- **ARPA Radar & Pilotage Collision Avoidance Display**: Màn hình radar quét 360 độ hiển thị vệt vector mục tiêu (True/Relative Vectors), cung tròn CPA/TCPA, vùng đón hoa tiêu Pilot Boarding Station và lực kéo tàu dắt Tug Escort.
