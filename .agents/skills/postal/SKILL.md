---
name: postal
description: Vietnamese Postal, Express Delivery & Courier Logistics Suite.
---

# 📦 Postal — Vietnamese Postal, Express Delivery & Courier Logistics

Autonomous operations engine for Vietnamese postal services, express delivery, courier waybills, volumetric weight tariffing, transit time SLA auditing under QCVN 01:2018/BTTTT, contraband security screening, and statutory loss/damage indemnity calculations under the Law on Post 2010 (Law 49/2010/QH12), Decree 47/2011/NĐ-CP, Decree 25/2022/NĐ-CP, Circular 22/2014/TT-BTTTT, and Decision 2475/QĐ-BTTTT.

## Statutory Legal Framework

1. **Luật Bưu chính 2010 (Luật số 49/2010/QH12)**:
   - Thẩm quyền cấp Giấy phép bưu chính: Bộ Thông tin và Truyền thông (phạm vi liên tỉnh, quốc tế) và Sở Thông tin và Truyền thông (nội tỉnh).
   - Điều kiện vốn điều lệ tối thiểu:
     * Nội tỉnh / Liên tỉnh: Tối thiểu 2 tỷ đồng VND.
     * Quốc tế: Tối thiểu 5 tỷ đồng VND.
   - Trách nhiệm của doanh nghiệp bưu chính trong việc bảo đảm an toàn, an ninh bưu chính và bồi thường thiệt hại.

2. **Quy Chuẩn Kỹ Thuật Quốc Gia Thời Gian Toàn Trình (QCVN 01:2018/BTTTT)**:
   - Chỉ tiêu thời gian toàn trình (SLA):
     * Bưu gửi nội tỉnh: Thời gian phát đạt chuẩn $D+1$ ngày.
     * Bưu gửi liên tỉnh trục Bắc - Nam (Hà Nội <-> TP.HCM): Thời gian phát chuẩn đường bay $D+2$ ngày.
     * Bưu gửi liên tỉnh thông thường: Chuẩn $D+3$ ngày.
   - Tỷ lệ bưu gửi đạt thời gian toàn trình cam kết tối thiểu $\ge 90\%$.

3. **Cước Phí Vận Chuyển & Trọng Lượng Thể Tích Quy Đổi**:
   - Trọng lượng tính cước là giá trị lớn hơn giữa trọng lượng thực tế và trọng lượng quy đổi thể tích theo công thức quốc tế:
     $$W_{\text{vol}} = \frac{\text{Dài (cm)} \times \text{Rộng (cm)} \times \text{Cao (cm)}}{5000} \text{ (kg)}$$
   - Biểu cước gồm cước chính, phí bảo hiểm khai giá (1.0%) và phí thu hộ tiền hàng COD (1.2%, tối thiểu 10,000 VND).

4. **Kiểm Tra An Ninh & Vật Phẩm Cấm Gửi (Điều 12 Luật Bưu chính)**:
   - Cấm gửi vũ khí, vật liệu nổ, chất ma túy, hóa chất độc hại, chất lỏng dễ cháy, văn hóa phẩm đồi trụy hoặc phản động, tiền mặt/kim khí quý không khai giá.
   - Đình chỉ vận chuyển và chuyển giao cơ quan chức năng khi phát hiện vật phẩm cấm.

5. **Bồi Thường Thiệt Hại Bưu Chính (Nghị định 47/2011/NĐ-CP)**:
   - Mất/hỏng toàn bộ bưu gửi khai giá: Bồi thường $100\%$ giá trị khai giá ghi trên vận đơn.
   - Bưu kiện thông thường không khai giá: Bồi thường tối đa 04 lần cước dịch vụ hoặc định mức $100,000\text{ VND/kg}$.
   - Phát chậm quá thời hạn cam kết: Hoàn lại $100\%$ tiền cước dịch vụ đã thu.

---

## CLI Usage

```bash
# Báo cáo telemetry tổng quan mạng lưới bưu chính & chuyển phát nhanh
mekong postal status
mekong postal status --json

# Thẩm định và cấp giấy phép bưu chính
mekong postal license "VNPost Express EMS" "0101889977" --scope INTER_PROVINCE --capital 5000000000 --json

# Tạo vận đơn bưu gửi chuyển phát nhanh và tính cước
mekong postal waybill "Nguyễn Văn Hùng" "Hoàn Kiếm, Hà Nội" "10000" "Lê Thị Lan" "Quận 1, TP.HCM" "70000" --service EXPRESS_PARCEL --weight 1.8 --length 30 --width 20 --height 15 --declared 2000000 --cod 500000 --json

# Thẩm tra chất lượng thời gian toàn trình (SLA)
mekong postal sla VNPOST-ABC123 10000 70000 1.8 --service EXPRESS_PARCEL --json

# Soi chiếu an ninh bưu gửi
mekong postal security VNPOST-ABC123 --station TRAM-SOI-NOI-BAI --json

# Tính mức bồi thường thiệt hại sự cố bưu phẩm
mekong postal indemnity VNPOST-ABC123 --incident LOST_TOTAL --postage 45000 --declared 1500000 --json

# Tra cứu danh mục
mekong postal list licenses --json
mekong postal list waybills --json
mekong postal list sla --json
mekong postal list screenings --json
mekong postal list indemnities --json
```

---

## MCP Tools Integration

Mekong CLI provides dual FastMCP and pure-Python JSON-RPC 2.0 stdio tools:
- `mekong_postal_license`: Issue commercial postal & express delivery enterprise license under Postal Law 2010.
- `mekong_postal_waybill`: Create express consignment waybill, compute volumetric weight and tariffs.
- `mekong_postal_sla`: Audit end-to-end delivery transit time against statutory SLA standards under QCVN 01:2018/BTTTT.
- `mekong_postal_security`: Inspect postal consignment for prohibited items under Postal Law 2010.
- `mekong_postal_indemnity`: Calculate statutory compensation for lost, damaged, or delayed parcels.
- `mekong_postal_list`: Query postal licenses, consignments, SLA audits, security screenings, or indemnity claims.
- `mekong_postal_status`: Retrieve Vietnamese postal & express courier system telemetry and compliance metrics.
