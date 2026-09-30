---
name: price
description: Vietnamese Price Management, Anti-Price Gouging & Valuation Compliance Suite.
---

# mekong price — Autonomous Vietnamese Price Management, Anti-Price Gouging & Valuation Suite

## Căn Cứ Pháp Lý & Chuẩn Mực Nghiệp Vụ
1. **Luật Giá 2023 (Luật số 16/2023/QH15, có hiệu lực từ ngày 01/07/2024)**:
   - Thống nhất quản lý hoạt động giá, bình ổn giá, định giá của Nhà nước, kê khai giá, niêm yết giá và thẩm định giá.
   - Thẩm quyền quản lý: **Bộ Tài chính (Cục Quản lý giá)**, Sở Tài chính các tỉnh, thành phố trực thuộc Trung ương.
   - Danh mục hàng hóa, dịch vụ **Bình ổn giá (Price Stabilization)** (Điều 17):
     * Xăng, dầu thành phẩm;
     * Điện sinh hoạt;
     * Khí dầu mỏ hóa lỏng (LPG);
     * Sữa dành cho trẻ em dưới 06 tuổi;
     * Thóc, gạo tẻ thường;
     * Phân đạm, phân DAP, phân NPK;
     * Thuốc bảo vệ thực vật, vắc-xin phòng bệnh cho gia súc, gia cầm;
     * Thuốc phòng bệnh, chữa bệnh cho người thuộc danh mục thiết yếu;
     * Muối ăn, đường ăn.
   - **Kê khai giá (Price Declaration - Điều 28)**: Doanh nghiệp sản xuất, kinh doanh hàng hóa trong danh mục phải kê khai giá với cơ quan có thẩm quyền trước khi điều chỉnh giá bán.
   - **Niêm yết giá (Price Posting - Điều 29)**: Bắt buộc niêm yết công khai bằng Đồng Việt Nam, rõ ràng; nghiêm cấm bán cao hơn giá niêm yết.
   - **Hành vi bị nghiêm cấm (Điều 7)**: Nghiêm cấm lợi dụng tình trạng khẩn cấp, thiên tai, dịch bệnh để tăng giá bất hợp lý (Anti-Price Gouging), đầu cơ găm hàng, thông đồng định giá.
2. **Chuẩn mực Thẩm định giá Việt Nam (TĐGVN) & Nghị định số 87/2024/NĐ-CP**:
   - Điều kiện doanh nghiệp thẩm định giá: Tối thiểu 03 Thẩm định viên về giá (TĐV), vốn điều lệ tối thiểu 5 tỷ VND, tham gia bảo hiểm trách nhiệm nghề nghiệp.
   - Các phương pháp thẩm định giá: Phương pháp so sánh (Market Comparison), Phương pháp chi phí (Cost Approach), Phương pháp thu nhập / dòng tiền chiết khấu (DCF).
   - Chứng thư thẩm định giá có hiệu lực 06 tháng, làm căn cứ pháp lý cho thu hồi bồi thường đất đai, cổ phần hóa, bán đấu giá tài sản công và vay vốn tín dụng.
3. **Nghị định số 109/2013/NĐ-CP & Nghị định số 49/2016/NĐ-CP**:
   - Phạt 500.000 - 1.000.000 VND đối với hành vi không niêm yết giá rõ ràng.
   - Phạt 20.000.000 - 30.000.000 VND đối với hành vi bán cao hơn giá niêm yết.
   - Phạt 30.000.000 - 50.000.000 VND đối với hành vi không kê khai giá.
   - Phạt 50.000.000 - 100.000.000 VND và thu hồi toàn bộ số tiền thu lợi bất chính đối với hành vi tăng giá bất hợp lý trong thời kỳ bình ổn giá hoặc thiên tai, dịch bệnh.
4. **Lưu trữ SQLite WAL**: Bảng `price_declarations`, `price_postings`, `valuation_certificates`, `anti_gouging_audits` tại `.mekong/price.db`.

---

## CLI Invocations

```bash
# Báo cáo tổng quan hoạt động quản lý giá, bình ổn giá và thẩm định giá
mekong price

# Kê khai giá hàng hóa, dịch vụ theo Điều 28 Luật Giá 2023
mekong price declare "Công ty Sữa Mekong Dinh Dưỡng" --product "Sữa bột trẻ em dưới 6 tuổi 900g" --unit "Hộp" --old 450000 --new 480000 --date "2026-10-01" --stabilized

# Hậu kiểm niêm yết giá bán lẻ và xử phạt bán cao hơn giá niêm yết (Điều 29 Luật Giá 2023)
mekong price posting "Siêu thị Tiện lợi Mekong Mart" --product "Gạo thơm ST25 5kg" --listed 180000 --actual 180000 --posted --curr "VND"

# Thẩm tra và cấp Chứng thư thẩm định giá theo Chuẩn mực TĐGVN & Luật Giá 2023
mekong price valuation "Công ty CP Thẩm định giá Mekong Value" --client "VietinBank Chi nhánh 1" --asset "Tòa nhà văn phòng 12 tầng tại Q1, TP.HCM" --value 320000000000 --method MARKET_COMPARISON --appraiser "TĐV. Lê Quốc Doanh" --appraisers 5 --insurance

# Thanh tra xử lý hành vi đầu cơ găm hàng, tăng giá bất hợp lý trong thiên tai dịch bệnh
mekong price gouge "Cửa hàng Lương thực Bình Dân" --product "Bao gạo tẻ 10kg" --base 150000 --gouged 250000 --units 800 --crisis

# Tra cứu danh mục hồ sơ kê khai giá, niêm yết, thẩm định và xử phạt
mekong price list declarations
mekong price list postings
mekong price list valuations
mekong price list gouging

# Giám sát trạng thái và xuất JSON headless
mekong price status --json
```

---

## MCP Tools Integration
- `mekong_price_declare`: Tiếp nhận và thẩm định hồ sơ kê khai giá hàng hóa, dịch vụ theo Điều 28 Luật Giá 2023.
- `mekong_price_posting`: Kiểm tra tuân thủ niêm yết giá và phát hiện bán cao hơn giá niêm yết (Điều 29 Luật Giá 2023).
- `mekong_price_valuation`: Ban hành và thẩm tra Chứng thư Thẩm định giá theo Chuẩn mực Thẩm định giá Việt Nam (TĐGVN).
- `mekong_price_gouge`: Thanh tra hành vi tăng giá bất hợp lý, tính toán số tiền thu lợi bất chính và tiền phạt theo Nghị định 109/2013/NĐ-CP.
- `mekong_price_list`: Tra cứu danh mục kê khai giá, niêm yết giá, chứng thư thẩm định và xử phạt vi phạm giá.
- `mekong_price_status`: Báo cáo chỉ số telemetry tổng hợp hệ sinh thái quản lý giá và bình ổn thị trường.
