# Nghiên cứu Nghiệp vụ 31: Thiết bị phân ly dầu nước OWS 15 ppm & Tiền lương/Bảo lãnh Hồi hương Thuyền viên MLC 2006

Phạm vi: Phase 283 (MARPOL Annex I OWS & ORB) & Phase 284 (MLC 2006 SEA, Wages & Repatriation).

---

## 1. Thiết bị phân ly dầu nước la-gông OWS 15 ppm & Nhật ký dầu (Phase 283)

### Cơ sở Pháp lý & Kỹ thuật
- **MARPOL 73/78 Annex I Regulation 14 & 15**: Kiểm soát việc xả dầu từ buồng máy tàu biển.
- **IMO Res. MEPC.107(49)**: Quy chuẩn kỹ thuật sửa đổi cho thiết bị lọc dầu và thiết bị báo động 15 ppm (Oil Filtering Equipment & 15 ppm Bilge Alarm).
- **Bộ luật Hàng hải Việt Nam 2015 (Điều 65-72)** & **Thông tư 41/2020/TT-BGTVT**: Quy chuẩn quốc gia về ngăn ngừa ô nhiễm do tàu.

### Quy tắc Vận hành & Cảm biến OWS
- **Giới hạn nồng độ xả (Discharge Concentration Limit)**: Hàm lượng dầu trong nước la-gông sau xử lý xả qua mạn không được vượt quá **15 ppm** ($15\text{ mg/L}$).
- **Cơ chế van 3 ngả tự động (Automatic 3-Way Fail-Safe Valve)**: Khi cảm biến đo nồng độ dầu $C_{oil} \ge 15.0\text{ ppm}$ hoặc cảm biến mất tín hiệu/mất điện, van ngắt ngay lập tức đường xả qua mạn và hồi lưu toàn bộ về két la-gông (Bilge Holding Tank) trong vòng $\le 20\text{ giây}$.
- **Điều kiện địa lý & hàng hải**: Tàu phải đang hành trình ($v > 0\text{ knots}$); không được xả trong vùng cấm/vùng biển đặc biệt (Special Area) hoặc trong phạm vi $12\text{ hải lý}$ từ bờ trừ khi được quy chuẩn cho phép đặc biệt.
- **Nhật ký dầu (Oil Record Book Part I)**: Mã mục số (Code Letter & Item Number): Code C (Bơm la-gông buồng máy), Code D (Xả la-gông qua OWS), lưu trữ số hóa kèm mã hash SHA-256 bảo đảm tính toàn vẹn.

---

## 2. Hợp đồng Thuyền viên, Tính Lương MLC 2006 & Ký quỹ Hồi hương (Phase 284)

### Cơ sở Pháp lý
- **Maritime Labour Convention 2006 (MLC 2006)**: Tiêu chuẩn A2.1 (Hợp đồng lao động thuyền viên - SEA), A2.2 (Tiền lương), A2.5 (Hồi hương) & Bản sửa đổi 2014 (Bảo đảm tài chính khi thuyền viên bị bỏ rơi).
- **Bộ luật Hàng hải Việt Nam 2015 (Điều 58-64)**, **Nghị định 121/2014/NĐ-CP**, **Nghị định 05/2017/NĐ-CP** và **Bộ luật Lao động 2019**.

### Thuật toán Tính Lương & Làm thêm giờ
- **Lương cơ bản (Basic Wage)**: Không thấp hơn mức lương tối thiểu của ITF/ILO (khoảng $658\text{ USD/tháng}$ cho Thủy thủ trưởng thành AB).
- **Lương làm thêm giờ (Overtime Rate)**: Tối thiểu $1.25\times$ mức lương cơ bản theo giờ ($R_{OT} \ge 1.25 \times \frac{W_{basic}}{208}$). Trong trường hợp thỏa thuận lương làm thêm khoán (guaranteed overtime), số giờ khoán không dưới $48\text{ giờ/tháng}$.
- **Nghỉ phép có lương (Annual Leave Accrual)**: Tối thiểu $2.5\text{ ngày}$ phép cho mỗi tháng làm việc thực tế ($30\text{ ngày/năm}$).
- **Quỹ bảo lãnh hồi hương & Bỏ rơi (Repatriation & Abandonment Escrow)**:
  - Khi chủ tàu phá sản hoặc bỏ rơi thuyền viên, tổ chức tài chính/P&I Club chịu trách nhiệm chi trả tối đa **4 tháng tiền lương nợ đọng** (Standard A2.5.2).
  - Chi phí hồi hương trực tiếp: Vé máy bay chặng về nước định cư, tiền ăn, chỗ ở, sơ cấp cứu y tế trong thời gian chờ đợi.
