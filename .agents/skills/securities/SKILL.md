---
name: securities
description: Vietnamese Securities, Stock Exchanges, IPO, Margin Trading & Capital Markets Suite.
---

# mekong securities — Autonomous Vietnamese Securities, Stock Exchanges & Capital Markets Suite

## Căn Cứ Pháp Lý & Chuẩn Mực Nghiệp Vụ
1. **Luật Chứng khoán 2019 (Luật số 54/2019/QH14)**:
   - Quy định về các hoạt động chào bán, niêm yết, giao dịch, kinh doanh, đầu tư chứng khoán, cung cấp dịch vụ về chứng khoán và thị trường chứng khoán.
   - Thẩm quyền quản lý nhà nước: **Bộ Tài chính** & **Ủy ban Chứng khoán Nhà nước (UBCKNN - SSC)**.
2. **Nghị định số 155/2020/NĐ-CP** quy định chi tiết thi hành một số điều của Luật Chứng khoán:
   - **Điều kiện chào bán cổ phiếu lần đầu ra công chúng (IPO) (Điều 15 Luật CK 2019)**:
     * Vốn điều lệ thực góp tại thời điểm đăng ký: $\ge 30,000,000,000\text{ VND}$ (30 tỷ VND).
     * Hoạt động kinh doanh 02 năm liên tục có lãi, không có lỗ lũy kế.
     * Tỷ suất lợi nhuận sau thuế trên vốn chủ sở hữu (ROE) năm liền trước $\ge 5\%$.
     * Tối thiểu 15% số cổ phiếu có quyền biểu quyết bán cho ít nhất 100 nhà đầu tư không phải cổ đông lớn (20% nếu vốn $< 100\text{ tỷ VND}$).
     * Cổ đông lớn cam kết nắm giữ tối thiểu 20% vốn điều lệ trong ít nhất 1 năm kể từ ngày hoàn tất chào bán.
   - **Điều kiện niêm yết cổ phiếu trên HOSE (Điều 109)**:
     * Vốn điều lệ thực góp: $\ge 120,000,000,000\text{ VND}$ (120 tỷ VND).
     * Tối thiểu 02 năm hoạt động dưới hình thức công ty cổ phần.
     * ROE năm liền trước $\ge 5\%$, hoạt động 02 năm có lãi, không có nợ quá hạn trên 01 năm, không có lỗ lũy kế.
     * Tối thiểu 15% cổ phiếu có quyền biểu quyết do ít nhất 300 cổ đông không phải cổ đông lớn nắm giữ.
   - **Điều kiện niêm yết cổ phiếu trên HNX (Điều 110)**:
     * Vốn điều lệ thực góp: $\ge 30,000,000,000\text{ VND}$ (30 tỷ VND).
     * Tối thiểu 01 năm hoạt động dưới hình thức CTCP.
     * ROE năm liền trước $\ge 5\%$, kinh doanh có lãi, không có nợ quá hạn trên 01 năm, không lỗ lũy kế.
     * Tối thiểu 10% cổ phiếu biểu quyết do ít nhất 100 cổ đông nhỏ nắm giữ.
   - **Đăng ký giao dịch UPCoM (Điều 133)**: Công ty đại chúng chưa niêm yết trên HOSE/HNX.
3. **Thông tư số 120/2020/TT-BTC & Quyết định 87/QĐ-UBCK về Giao Dịch Ký Quỹ (Margin Trading)**:
   - Tỷ lệ ký quỹ ban đầu (Initial Margin Ratio): tối thiểu $50\%$.
   - Tỷ lệ ký quỹ duy trì (Maintenance Margin Ratio - MMR): tối thiểu $30\%$.
   - Kích hoạt **Margin Call** khi tỷ lệ thực tế $R < 30\%$ (thời hạn bổ sung 03 phiên giao dịch).
   - Kích hoạt **Force Sell** khi tỷ lệ $R \le 25\%$ hoặc quá hạn margin call đưa về tỷ lệ an toàn $\ge 35\%$.
4. **Thông tư số 121/2020/TT-BTC về Tỷ lệ An toàn Tài chính (CAR) của CTCK**:
   - Vốn khả dụng / Tổng giá trị rủi ro $\ge 180\%$.
   - Phân loại: $\ge 220\%$ (Vững mạnh), $180\% - 220\%$ (Đạt chuẩn), $150\% - 180\%$ (Cảnh báo sớm), $< 150\%$ (Kiểm soát đặc biệt).
5. **Chứng chỉ hành nghề chứng khoán (Điều 97 Luật Chứng khoán 2019)**:
   - Môi giới chứng khoán, Phân tích tài chính, Quản lý quỹ, Tư vấn tài chính doanh nghiệp.
6. **Lưu trữ SQLite WAL**: Bảng `securities_offerings`, `securities_listings`, `margin_accounts`, `securities_firm_safety`, `practitioner_licenses` tại `.mekong/securities.db`.

---

## CLI Invocations

```bash
# Báo cáo tổng quan telemetry thị trường vốn và chứng khoán
mekong securities

# Thẩm định điều kiện chào bán cổ phiếu ra công chúng / IPO (Nghị định 155/2020/NĐ-CP)
mekong securities offering "Công ty Cổ phần Công nghệ Mekong" "MKT" "0108877665" --type IPO --capital 50000000000 --shares 5000000 --price 25000 --roe 12.5

# Thẩm định tiêu chuẩn niêm yết cổ phiếu trên sàn HOSE / HNX / UPCoM
mekong securities listing "MKT" "Công ty CP Công nghệ Mekong" --exchange HOSE --shares 50000000 --price 35000 --capital 500000000000 --roe 15.0 --years 5 --shareholders 500

# Quản lý rủi ro giao dịch ký quỹ, giám sát Margin Call và Force Sell
mekong securities margin "Nguyễn Văn Hùng" "026C123456" --firm "Chứng khoán Mekong" --assets 500000000 --loan 380000000

# Kiểm tra tỷ lệ an toàn tài chính (CAR) của công ty chứng khoán (Thông tư 121/2020/TT-BTC)
mekong securities safety "Công ty CP Chứng khoán Mekong" "0109988776" --liquid 1500000000000 --market-risk 300000000000 --settle-risk 100000000000 --op-risk 200000000000

# Cấp chứng chỉ hành nghề chứng khoán chuyên nghiệp (UBCKNN)
mekong securities license "Trần Quốc Tuấn" "001099008877" --type BROKERAGE --firm "Công ty CP Chứng khoán Mekong"

# Tra cứu dữ liệu đợt chào bán, mã niêm yết, tài khoản margin, an toàn vốn
mekong securities list --type offerings
mekong securities list --type listings
mekong securities list --type margin
mekong securities list --type safety
mekong securities list --type practitioners

# Xuất báo cáo trạng thái hệ thống định dạng JSON
mekong securities status --json
```

---

## MCP Tools Integration

| Tool Name | Engine Method | Mục Tiêu & Mô Tả Nghiệp Vụ |
|---|---|---|
| `mekong_securities_offering` | `audit_public_offering` | Thẩm định điều kiện chào bán cổ phiếu ra công chúng hoặc IPO theo Luật Chứng khoán 2019. |
| `mekong_securities_listing` | `verify_listing_qualification` | Thẩm tra tiêu chuẩn niêm yết cổ phiếu trên HOSE, HNX hoặc UPCoM theo Nghị định 155/2020/NĐ-CP. |
| `mekong_securities_margin` | `audit_margin_account` | Giám sát tỷ lệ ký quỹ tài khoản, phát hiện Margin Call hoặc bán giải chấp Force Sell. |
| `mekong_securities_safety` | `audit_firm_financial_safety` | Thẩm tra Tỷ lệ an toàn tài chính (CAR) của công ty chứng khoán theo Thông tư 121/2020/TT-BTC. |
| `mekong_securities_license` | `issue_practitioner_license` | Cấp Chứng chỉ hành nghề chứng khoán chuyên nghiệp theo quy chuẩn UBCKNN. |
| `mekong_securities_list` | `list_*` | Tra cứu danh mục hồ sơ chào bán, mã niêm yết, tài khoản margin, an toàn vốn CTCK. |
| `mekong_securities_status` | `get_status` | Báo cáo telemetry tổng hợp tình hình thị trường chứng khoán, vốn hóa và an toàn vốn. |
