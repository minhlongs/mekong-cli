---
name: ecom
description: Vietnamese Cross-Border E-Commerce, Overseas Supplier Tax (FCT), Marketplace Platform Licensing & Order Invoicing (Decree 52/2013, Decree 85/2021 & Decree 91/2022).
---

# 🛒 E-Commerce — Vietnamese Cross-Border E-Commerce, Platform Tax Invoicing & Marketplace Compliance

Autonomous operations engine for Vietnamese cross-border e-commerce, digital platform taxation, marketplace licensing, and electronic order invoicing.

## Statutory Legal Framework

1. **Luật Quản lý Thuế 2019 & Nghị định 126/2020/NĐ-CP (Điều 30, 42)**:
   - Thuế Nhà thầu Nước ngoài (Foreign Contractor Tax - FCT) trên dịch vụ kỹ thuật số (Google, Meta, Netflix, TikTok, Shopee, Amazon).
   - Tỷ lệ khấu trừ trực tiếp trên doanh thu:
     - Thuế Giá trị gia tăng (GTGT / VAT): **5.0%**
     - Thuế Thu nhập doanh nghiệp (TNDN / CIT): **5.0%**
     - Tổng nghĩa vụ FCT: **10.0%** doanh thu (Phần mềm Cloud SaaS miễn thuế GTGT, chịu 5.0% TNDN).
   - Kê khai trực tiếp qua Cổng thông tin điện tử Tổng cục Thuế dành cho Nhà cung cấp nước ngoài: `etaxvn.gdt.gov.vn`.

2. **Nghị định 52/2013/NĐ-CP & Nghị định 85/2021/NĐ-CP**:
   - Phân loại mô hình thương mại điện tử quản lý bởi Bộ Công Thương (`online.gov.vn`):
     - `SALES_WEBSITE`: Website/ứng dụng bán hàng trực tuyến của doanh nghiệp $\to$ Thủ tục **Thông báo** (Notification).
     - `MARKETPLACE`: Sàn giao dịch thương mại điện tử $\to$ Thủ tục **Đăng ký** Giấy phép thiết lập sàn (Registration).
     - `SOCIAL_COMMERCE`: Mạng xã hội có hoạt động TMĐT $\to$ Thủ tục **Đăng ký**.
     - `PROMOTION_APP`: Website/ứng dụng dịch vụ khuyến mại trực tuyến $\to$ Thủ tục **Đăng ký**.
   - Điều kiện bắt buộc:
     - Ban hành Quy chế hoạt động sàn TMĐT theo mẫu Bộ Công Thương.
     - Cơ chế tiếp nhận & giải quyết khiếu nại của người tiêu dùng (thời hạn phản hồi $\le 3$ ngày).
     - Quy trình định danh và thu thập thông tin người bán (KYC).
     - Lưu trữ dữ liệu lịch sử đơn hàng tối thiểu **3 năm** (Điều 36).

3. **Nghị định 91/2022/NĐ-CP (sửa đổi Nghị định 126/2020/NĐ-CP)**:
   - Trách nhiệm của chủ sở hữu sàn TMĐT cung cấp thông tin người bán (doanh thu, tài khoản ngân hàng, CCCD/MST) định kỳ hàng quý cho Tổng cục Thuế.

4. **Nghị định 123/2020/NĐ-CP & Thông tư 78/2021/TT-BTC**:
   - Xuất hóa đơn điện tử từng đơn hàng giao dịch thành công trên sàn thương mại điện tử.

5. **Bưu kiện chuyển phát nhanh TMĐT Xuyên biên giới**:
   - Ngưỡng miễn thuế bưu kiện chuyển phát nhanh trị giá thấp: $\le 1,000,000\text{ VND}$ (1 triệu đồng).
   - Bưu kiện trên 1 triệu đồng: Tính thuế Nhập khẩu và thuế GTGT (10%).

---

## Typer CLI Commands

```bash
# 1. Bảng điều khiển tổng quan TMĐT & thuế nền tảng số
mekong ecom
mekong ecom --json

# 2. Tính thuế Nhà thầu Nước ngoài (FCT) dịch vụ số xuyên biên giới
mekong ecom fct "Google Asia Pacific" "0109887766" "ONLINE_ADVERTISING" --usd 50000 --quarter "Q1-2026"
mekong ecom fct "Meta Ireland" "0109887755" "DIGITAL_SERVICES" --vnd 1272500000 --json

# 3. Thẩm định điều kiện cấp phép và tuân thủ pháp luật sàn/website TMĐT
mekong ecom audit "Shopee Vietnam" "https://shopee.vn" --type MARKETPLACE --tax-id "0106773786"
mekong ecom audit "TechShop VN" "https://techshop.vn" --type SALES_WEBSITE --tax-id "0109998888" --json

# 4. Quyết toán đơn hàng sàn TMĐT, tính thực nhận của shop & xuất hóa đơn điện tử
mekong ecom order "240929-SHOPEE-9988" "SHOPEE_VN" "SHOP-888" "USER-999" 500000 --commission 6.0 --pay-fee 2.5 --shipping 30000 --json

# 5. Thẩm định nghĩa vụ thuế bưu kiện chuyển phát nhanh TMĐT xuyên biên giới
mekong ecom parcel "SPX12345678" "China" "Nguyễn Văn A" "Tai nghe Bluetooth" --vnd 450000 --json
mekong ecom parcel "VN987654321HK" "Hong Kong" "Trần Thị B" "Đồng hồ thông minh" --vnd 2500000 --duty 15 --json

# 6. Truy vấn danh mục bản ghi
mekong ecom list --type platforms
mekong ecom list --type fct
mekong ecom list --type orders
mekong ecom list --type parcels --limit 20 --json

# 7. Trạng thái điều hành TMĐT & nghĩa vụ thuế
mekong ecom status --json
```

---

## Native MCP Tools

Parity across FastMCP and JSON-RPC 2.0 stdio engines:
- `mekong_ecom_fct`: Calculate digital services Foreign Contractor Tax (FCT - VAT & CIT) under Decree 126/2020.
- `mekong_ecom_audit`: Audit e-commerce platform compliance and statutory licensing under Decree 52/2013 & Decree 85/2021.
- `mekong_ecom_order`: Settle marketplace order finances, compute seller net payout, and generate electronic invoice under Decree 123/2020.
- `mekong_ecom_parcel`: Evaluate cross-border express parcel customs duty & VAT exemption threshold.
- `mekong_ecom_list`: Query registered platforms, FCT declarations, marketplace orders, or parcels.
- `mekong_ecom_status`: Retrieve aggregated e-commerce and digital platform telemetry.
