# Research Report 13: Vietnam Inland Waterway Navigation & Container Feeder Barging

## 1. Statutory & Regulatory Framework
- **Luật Giao thông Đường thủy nội địa 2004 (Luật sửa đổi 2014)**: Quy định phân cấp kỹ thuật luồng tuyến ĐTNĐ (Cấp Đặc biệt, I, II, III, IV, V, VI), chiều cao tĩnh không thông thuyền (air draft clearance), mớn nước luồng (channel draft).
- **Thông tư 248/2016/TT-BTC & Thông tư 74/2021/TT-BTC**: Biểu mức thu phí, lệ phí đường thủy nội địa:
  - Phí trọng tải phương tiện: Tính theo DWT hoặc GT (VND/tấn/lượt cập cảng bến thủy nội địa).
  - Lệ phí ra, vào cảng, bến thủy nội địa: 10,000 - 50,000 VND/lượt tùy theo tải trọng phương tiện thủy.
- **Thông tư 39/2023/TT-BGTVT**: Biểu khung giá cước dịch vụ bốc dỡ sà lan và giá kéo đẩy sà lan tại khu vực cảng biển TP.HCM - Cái Mép - Đồng Nai - Cần Thơ:
  - Giá cước trung chuyển container bằng sà lan (feeder container barging freight): Tính theo TEU/FEU giữa Cảng TP.HCM / Đồng bằng Sông Cửu Long và Cụm cảng nước sâu Cái Mép - Thị Vải.
  - Phụ phí sà lan chở hàng nguy hiểm (DG container: +10%), quá cảnh Campuchia (Hiệp định Vận tải thủy Việt Nam - Campuchia: kiểm tra liên vận và phụ phí hoa tiêu luồng sông Tiền).

## 2. Mathematical Models & Operational Invariants
- **Tĩnh không & Mớn nước luồng**:
  $$\text{Air Draft Clearance} = H_{\text{bridge\_clearance}} - (\text{Airdraft}_{\text{barge}} - \text{Draft}_{\text{actual}})$$
  Điều kiện thông hành an toàn: $\text{Air Draft Clearance} \ge 0.5\text{ m}$ (safety margin).
  Mớn nước khả dụng: $\text{Under Keel Clearance (UKC)} = \text{Depth}_{\text{channel}} - \text{Draft}_{\text{vessel}} \ge 0.3\text{ m}$.
- **Cước vận tải sà lan feeder (Barging Tariff Matrix)**:
  $$\text{Total Feeder Freight} = \sum (\text{TEU\_Count} \times R_{\text{TEU}} + \text{FEU\_Count} \times R_{\text{FEU}}) \times M_{\text{DG}} + \text{Port\_Dues}_{\text{TT248}}$$

## 3. Implementation Plan
- Class: `InlandWaterwayBargingEngine`
- Methods: `calculate_port_dues`, `calculate_feeder_barging_freight`, `evaluate_bridge_channel_clearance`.
