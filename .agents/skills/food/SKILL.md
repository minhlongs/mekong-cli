---
name: food
description: Vietnamese Food Safety, Dietary Supplements, Functional Foods & Hygiene Certification Suite.
---

# mekong food — Autonomous Vietnamese Food Safety, Dietary Supplements & Hygiene Certification Suite

## Căn Cứ Pháp Lý & Chuẩn Mực Nghiệp Vụ
1. **Luật An toàn thực phẩm 2010 (Luật số 55/2010/QH12)**:
   - Quy định quyền và nghĩa vụ của tổ chức, cá nhân trong bảo đảm an toàn thực phẩm; điều kiện bảo đảm an toàn đối với thực phẩm, sản xuất, kinh doanh thực phẩm và nhập khẩu, xuất khẩu thực phẩm.
   - Thẩm quyền quản lý liên ngành: Bộ Y tế, Bộ Nông nghiệp & PTNT, Bộ Công Thương.
2. **Nghị định số 15/2018/NĐ-CP** hướng dẫn thi hành một số điều của Luật An toàn thực phẩm:
   - **Tự công bố sản phẩm (Điều 4, 5)**: Thực phẩm đã qua chế biến bao gói sẵn, phụ gia thực phẩm, chất hỗ trợ chế biến, dụng cụ bao gói chứa đựng thực phẩm tiếp xúc trực tiếp. Có hiệu lực ngay khi tổ chức cá nhân công bố công khai.
   - **Đăng ký bản công bố sản phẩm (Điều 6, 7, 8)**: Bắt buộc thẩm định và cấp Giấy tiếp nhận bởi Cục An toàn thực phẩm - Bộ Y tế đối với:
     * Thực phẩm bảo vệ sức khỏe (Health Supplements / Dietary Supplements);
     * Thực phẩm dinh dưỡng y học (Medical Foods);
     * Thực phẩm dùng cho chế độ ăn đặc biệt;
     * Sản phẩm dinh dưỡng dùng cho trẻ đến 36 tháng tuổi;
     * Phụ gia thực phẩm hỗn hợp có công dụng mới hoặc chưa có trong danh mục.
   - **Giấy chứng nhận cơ sở đủ điều kiện ATTP (Điều 11, 12)**: Hiệu lực 3 năm (36 tháng). Miễn cấp GCN đối với các cơ sở đã có chứng nhận:
     * GMP (Thực hành sản xuất tốt - bắt buộc với TPBVSK từ 01/07/2019);
     * HACCP (Hệ thống phân tích mối nguy và điểm kiểm soát tới hạn);
     * ISO 22000, FSSC 22000, IFS, BRC hoặc cơ sở sản xuất nông nghiệp ban đầu nhỏ lẻ.
   - **Kiểm tra nhà nước về ATTP nhập khẩu (Điều 16, 17, 18, 19)**:
     * Kiểm tra giảm (Reduced): Tối đa 5% xác suất lấy mẫu ngẫu nhiên (áp dụng khi có GMP/HACCP/ISO hoặc 3 lần đạt chuẩn liên tiếp);
     * Kiểm tra thông thường (Normal): Kiểm tra hồ sơ lô hàng 100%;
     * Kiểm tra chặt (Tightened): Kiểm tra hồ sơ kết hợp lấy mẫu kiểm nghiệm 100% (áp dụng với lô hàng không đạt lần trước hoặc có cảnh báo khẩn cấp).
   - **Thu hồi và xử lý thực phẩm không an toàn**:
     * Mức độ 1 (Class 1 - Tử vong / Ngộ độc cấp tính): Thông báo <= 24 giờ, hoàn tất thu hồi <= 3 ngày.
     * Mức độ 2 (Class 2 - Ảnh hưởng sức khỏe tạm thời): Thông báo <= 3 ngày, hoàn tất thu hồi <= 7 ngày.
     * Mức độ 3 (Class 3 - Lỗi nhãn mác, chỉ tiêu định lượng): Thông báo <= 5 ngày, hoàn tất thu hồi <= 15 ngày.
3. **Tiêu chuẩn TCVN ISO 22000:2018 & Codex Alimentarius (HACCP 7 Nguyên Tắc)**:
   - Phân tích mối nguy sinh học/hóa học/vật lý, xác định CCPs, thiết lập giới hạn tới hạn, quy trình giám sát, hành động khắc phục, thẩm tra và lưu trữ hồ sơ.
4. **Lưu trữ SQLite WAL**: Bảng `food_declarations`, `food_facilities`, `food_inspections`, `food_recalls`, `haccp_audits` tại `.mekong/food.db`.

---

## CLI Invocations

```bash
# Báo cáo tổng quan telemetry hệ thống an toàn thực phẩm
mekong food

# Tự công bố hoặc đăng ký bản công bố sản phẩm (Nghị định 15/2018/NĐ-CP)
mekong food declare "Viên uống Nano Curcumin Gold" DIETARY_SUPPLEMENT --enterprise "Công ty CP Dược Mekong" --tax-id "0109988776" --gmp-cert "GMP-MOH-2026-0045" --shelf-life 36

# Đăng ký cơ sở thực phẩm và xác nhận miễn trừ chuẩn GMP/HACCP/ISO 22000
mekong food facility "Nhà máy Chế biến Thực phẩm Sạch Mekong" "Công ty CP Thực phẩm Mekong" "0108877665" --activity MANUFACTURING --exemption HACCP --rating EXCELLENT

# Kiểm tra nhà nước về an toàn thực phẩm đối với lô hàng nhập khẩu
mekong food inspect "SHP-AUS-2026-001" "Thịt bò đông lạnh Úc cao cấp" --importer "Công ty TNHH Nhập khẩu Mekong" --origin "Úc" --qty 12000 --mode REDUCED

# Ban hành quyết định thu hồi thực phẩm khẩn cấp (Mức độ 1, 2 hoặc 3)
mekong food recall "Pate Gan Đóng Hộp Mekong" "LOT-2026-P01" --class CLASS_1 --reason "Nhiễm độc tố Botulinum" --affected 2500 --disposal DESTROY

# Đánh giá và thẩm định hệ thống quản lý an toàn thực phẩm 7 nguyên tắc HACCP
mekong food haccp "Nhà máy Chế biến Thực phẩm Sạch Mekong" --auditor "Nguyễn Văn Hùng (Lead Auditor)" --ccps 4 --critical-nc 0 --major-nc 0 --minor-nc 1

# Tra cứu dữ liệu hồ sơ công bố, cơ sở, kiểm tra nhập khẩu và thu hồi
mekong food list --type declarations
mekong food list --type facilities
mekong food list --type inspections
mekong food list --type recalls
mekong food list --type haccp

# Xuất báo cáo telemetry toàn diện định dạng JSON
mekong food status --json
```

---

## MCP Tools Integration

| Tool Name | Engine Method | Mục Tiêu & Mô Tả Nghiệp Vụ |
|---|---|---|
| `mekong_food_declare` | `declare_product` | Tự công bố hoặc đăng ký bản công bố sản phẩm thực phẩm theo Nghị định 15/2018/NĐ-CP. |
| `mekong_food_facility` | `register_facility` | Cấp Giấy chứng nhận cơ sở đủ điều kiện ATTP hoặc xác nhận miễn trừ (GMP/HACCP/ISO 22000). |
| `mekong_food_inspect` | `inspect_imported_food` | Kiểm tra nhà nước về an toàn thực phẩm đối với hàng nhập khẩu (Kiểm tra giảm / thông thường / chặt). |
| `mekong_food_recall` | `initiate_recall` | Ban hành lệnh thu hồi thực phẩm không bảo đảm an toàn theo hạn chót Mức độ 1, 2, 3. |
| `mekong_food_haccp` | `audit_haccp_system` | Đánh giá và thẩm định hệ thống quản lý an toàn thực phẩm theo 7 nguyên tắc HACCP và kiểm soát CCP. |
| `mekong_food_list` | `list_*` | Tra cứu danh sách hồ sơ công bố, cơ sở kiểm tra, lô hàng nhập khẩu và lệnh thu hồi. |
| `mekong_food_status` | `get_status` | Báo cáo telemetry tổng hợp tình hình an toàn thực phẩm, tỷ lệ thông quan và tuân thủ. |
