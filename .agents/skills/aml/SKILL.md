---
name: aml
description: Vietnamese Anti-Money Laundering, Counter-Terrorist Financing & Sanctions Suite.
---

# /aml — Vietnamese Anti-Money Laundering & Sanctions Suite

Giám sát phòng, chống rửa tiền (AML), chống tài trợ khủng bố (CTF) và thực thi lệnh cấm vận tài chính có mục tiêu (TFS) theo quy định pháp luật Việt Nam và chuẩn mực FATF.

## Căn cứ Pháp lý & Khung Quy chuẩn

1. **Luật Phòng, chống rửa tiền 2022** (Luật số 14/2022/QH15, có hiệu lực từ ngày 01/03/2023).
2. **Nghị định số 19/2023/NĐ-CP** quy định chi tiết một số điều của Luật Phòng, chống rửa tiền.
3. **Quyết định số 11/2023/QĐ-TTg** của Thủ tướng Chính phủ quy định mức giao dịch có giá trị lớn phải báo cáo (từ 400.000.000 VNĐ).
4. **Thông tư số 09/2023/TT-NHNN** của Ngân hàng Nhà nước Việt Nam hướng dẫn thực hiện Luật PCRT.
5. **Kế hoạch hành động quốc gia FATF** nhằm đưa Việt Nam ra khỏi Danh sách Xám (FATF Grey List).

---

## Tính năng Nghiệp vụ Cốt lõi

### 1. Định danh Khách hàng & Chủ hưởng lợi cuối cùng (CDD / KYC & UBO)
- Thẩm định danh tính cá nhân/tổ chức, phân tầng rủi ro (`LOW`, `MEDIUM`, `HIGH`).
- Xác minh người hưởng lợi cuối cùng (Ultimate Beneficial Owner - UBO) nắm giữ $\ge 25\%$ vốn điều lệ hoặc quyền chi phối tối hậu (Điều 10 Luật 14/2022/QH15).
- Tự động áp dụng quy trình thẩm định tăng cường (Enhanced Due Diligence - EDD) đối với cá nhân có ảnh hưởng chính trị (PEPs) hoặc ngành nghề rủi ro cao (BĐS, kinh doanh vàng, casino, tài sản số).

### 2. Báo cáo Giao dịch Tiền mặt Giá trị lớn (LCTR)
- Tự động phát hiện và lập báo cáo giao dịch tiền mặt $\ge 400.000.000$ VNĐ (Điều 25 & QĐ 11/2023/QĐ-TTg).
- Sinh mã tham chiếu điện tử chuẩn gửi Cục Phòng, chống rửa tiền (`SBV-AMLD-LCTR-...`).

### 3. Phát hiện & Lập Báo cáo Giao dịch Đáng ngờ (STR)
- Bộ chỉ số phát hiện giao dịch chia nhỏ (Smurfing/Structuring), doanh nghiệp bình phong (Shell companies), doanh số đột biến hoặc nguồn gốc bất minh (Điều 26-33).
- Tính toán hạn nộp luật định: 48 giờ đối với giao dịch thông thường, 24 giờ đối với giao dịch khẩn cấp/chặn luồng tiền (Điều 37).

### 4. Rà soát Cấm vận & Tài trợ Khủng bố (TFS & Blacklist Screening)
- Rà soát tự động danh sách đen UNSC (ISIL/Da'esh, Al-Qaeda, DPRK WMD) và Bộ Công an Việt Nam.
- Kích hoạt cơ chế phong tỏa tài sản tức thời (Asset Freeze) không cần báo trước trong 03 ngày làm việc (Điều 34-37).
- Cơ chế bảo hộ miễn trừ trách nhiệm (Safe Harbor) theo Điều 36.

### 5. Đánh giá Quản trị Nội bộ & Sẵn sàng Chuẩn FATF
- Đánh giá bổ nhiệm Cán bộ tuân thủ AML (Điều 20), cập nhật quy chế nội bộ, đào tạo hàng năm và kiểm toán độc lập.
- Xếp hạng mức độ sẵn sàng FATF: `COMPLIANT`, `LARGELY_COMPLIANT`, `PARTIALLY_COMPLIANT`, `NON_COMPLIANT`.

---

## Hướng dẫn Sử dụng CLI (`mekong aml`)

```bash
# Xem báo cáo tổng quan telemetry AML quốc gia
mekong aml

# Định danh khách hàng CDD & xác minh UBO
mekong aml cdd "Công ty TNHH Vận tải Sông Hồng" --type ORGANIZATION --id "0109988776" --industry "REAL_ESTATE" --ubo "Nguyễn Văn A" --ubo-pct 35.0 --source "Lợi nhuận kinh doanh" --mgmt-approved

# Ghi nhận giao dịch tiền mặt & kiểm tra ngưỡng LCTR 400M
mekong aml lctr "Trần Thị Mai" 650000000 --currency VND --type CASH_DEPOSIT --channel OVER_THE_COUNTER --notes "Nộp tiền mặt mua bất động sản"

# Lập báo cáo giao dịch đáng ngờ STR
mekong aml str "Công ty CP Đầu tư Nam Hải" SMURFING_STRUCTURING 1200000000 --indicator "CHIA_NHO_GIAO_DICH" --indicator "LUONG_TIEN_CAO_BAT_THUONG" --rationale "Nhiều lần nộp rút tiền mặt dưới 400 triệu trong cùng ngày" --urgent

# Rà soát đối tượng với danh sách đen cấm vận TFS
mekong aml screening "ISIL (DA'ESH)" --type ORGANIZATION

# Đánh giá thể chế và quy chế kiểm soát nội bộ AML
mekong aml assess "Ngân hàng TMCP Phương Nam" --type COMMERCIAL_BANK --officer --rules --training --audit

# Tra cứu danh mục hồ sơ đã lưu trữ
mekong aml list all --limit 20
```

---

## Công cụ MCP (FastMCP & JSON-RPC 2.0 Parity)

- `mekong_aml_cdd`: Perform Customer Due Diligence, Risk Profiling & UBO verification.
- `mekong_aml_lctr`: Detect, validate & record Large Cash Transactions $\ge 400,000,000\text{ VND}$.
- `mekong_aml_str`: Evaluate suspicious indicators and file Suspicious Transaction Reports.
- `mekong_aml_screening`: Screen against UNSC & domestic sanctions blacklists, PEPs & initiate asset freeze.
- `mekong_aml_assess`: Audit institutional AML internal controls and calculate FATF readiness tier.
- `mekong_aml_list`: Query stored CDD profiles, LCTRs, STRs, screenings, or institutional reviews.
- `mekong_aml_status`: Aggregate telemetry summary of national AML/CTF/TFS compliance.
