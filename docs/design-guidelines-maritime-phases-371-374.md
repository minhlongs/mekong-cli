# Hướng dẫn Thiết kế Giao diện & Trực quan hóa Dữ liệu: Maritime Phases 371–374

## 1. Màu sắc & Mã trạng thái (Design Tokens)
- **Cảnh báo Nguy cấp (Critical Violation / Trip)**: Đỏ (#EF4444) — Điểm chớp cháy dầu thải < 60°C, LoF >= 4 vi phạm an toàn sinh học cấm cạo rỉ cảng, PTO vượt tải mô-men xoắn > 80% MCR, vi phạm khoảng cách an toàn cần cẩu < 35m.
- **Cảnh báo Suy giảm (Warning / Attention)**: Hổ phách (#F59E0B) — Tốc độ máy chính < 65% MCR khóa PTO, cần lọc rác sinh học thu gom 99% (LoF 2-3), nước lẫn dầu trước xả đạt 10-15 ppm, trễ thủy triều luồng sâu.
- **Tối ưu & Tuân thủ (Optimal / Compliant)**: Xanh Ngọc (#10B981) — Chế độ phát điện trục hòa lưới tiết kiệm nhiên liệu, luồng cập cầu thỏa mãn UKC >= 1.5m, dầu tái chế RFO LHV >= 38 MJ/kg đạt chỉ tiêu clinker.
- **Chủ đề Hàng hải Kỹ thuật (Maritime Deep Tech)**: Xanh Hải quân Đậm (#0B132B), Nền Slate (#1C2541), Cyan (#48CAE4).

## 2. Bố cục Chỉ số & Bảng điều khiển (HUD Components)
1. **Shaft Generator PTO/PTI Telemetry Gauge**:
   - Biểu đồ phân bổ công suất: Tải máy chính (ME Load % MCR), Tần số lưới (Hz), Hệ số công suất $\cos\phi$, Suất tiêu hao nhiên liệu so sánh (SFOC Save kg/h).
2. **Port Berth & Quay Crane Spatial Gantt**:
   - Tọa độ bến (Berth Position X meters), Thời gian neo đậu (ETA - ETD timeline), Vùng an toàn tĩnh cần cẩu (>= 35m spacing buffer), Mớn nước an toàn theo thủy triều (Tidal Depth vs Draft + 1.5m UKC).
3. **Biofouling & In-Water Cleaning Compliance Matrix**:
   - Thang đo LoF (0–5), Tổn thất thủy động lực học (% added power penalty), Điều kiện cho phép vệ sinh (Grooming / Filtered Capture 99% / Drydock Mandatory).
4. **Circular Waste Oil De-Watering & Co-Processing Card**:
   - Cảnh báo điểm chớp cháy Pensky-Martens (>= 60°C gate), Tỷ lệ tách nước (> 95%), Hàm lượng dầu xả thải (<= 15 ppm), Tín chỉ carbon tái chế clinker ($1.2\text{ kg CO}_2\text{/kg RFO}$).
