---
name: insurance
description: Vietnamese Insurance Business, Actuarial Solvency, Life & Non-Life Underwriting Suite.
---

# mekong insurance — Autonomous Vietnamese Insurance, Actuarial & Underwriting Suite

## Căn Cứ Pháp Lý & Chuẩn Mực Nghiệp Vụ
1. **Luật Kinh doanh bảo hiểm 2022 (Luật số 08/2022/QH15)** (có hiệu lực từ ngày 01/01/2023):
   - Thay thế toàn diện Luật Kinh doanh bảo hiểm 2000, thiết lập khung quản lý giám sát trên cơ sở rủi ro (RBS - Risk-Based Supervision).
   - Thẩm quyền cấp Giấy phép thành lập và hoạt động: **Bộ Tài chính** (Cục Quản lý, giám sát bảo hiểm).
2. **Nghị định số 46/2023/NĐ-CP**:
   - Quy định chi tiết thi hành một số điều của Luật Kinh doanh bảo hiểm:
     * Điều kiện cấp phép & vốn điều lệ tối thiểu:
       - Bảo hiểm phi nhân thọ & sức khỏe: Tối thiểu $400,000,000,000\text{ VND}$ (400 tỷ đồng). Thêm hàng không/vệ tinh: $450,000,000,000\text{ VND}$.
       - Bảo hiểm nhân thọ & sức khỏe: Tối thiểu $750,000,000,000\text{ VND}$ (750 tỷ đồng). Thêm liên kết đơn vị/hưu trí: $1,000,000,000,000\text{ VND}$ (1,000 tỷ đồng).
       - Tái bảo hiểm: $500,000,000,000\text{ VND}$ (phi nhân thọ) hoặc $700,000,000,000\text{ VND}$ (nhân thọ/cả hai).
       - Môi giới bảo hiểm: $50,000,000,000\text{ VND}$ (gốc & tái) hoặc $70,000,000,000\text{ VND}$.
     * Biên khả năng thanh toán (Solvency Margin) & Tỷ lệ an toàn vốn:
       - Phi nhân thọ: $\max(25\% \times \text{Phí giữ lại}, 16\% \times \text{Bồi thường bình quân 3 năm})$.
       - Nhân thọ: $4\% \times \text{Dự phòng toán học} + 0.1\%\text{ - }0.3\% \times \text{Số tiền bảo hiểm chịu rủi ro}$.
       - Biên khả năng thanh toán thực tế / Biên tối thiểu $\ge 100\%$. Dưới $100\%$ thuộc diện kiểm soát đặc biệt.
3. **Thông tư số 67/2023/TT-BTC & Thông tư số 68/2023/TT-BTC**:
   - Quy định về trích lập dự phòng nghiệp vụ:
     * Dự phòng phí chưa được hưởng (UPR) theo tỷ lệ ngày 1/365 hoặc 80/20.
     * Dự phòng bồi thường khiếu nại (OCR) theo từng vụ tổn thất.
     * Dự phòng bồi thường cho tổn thất đã phát sinh nhưng chưa khiếu nại (IBNR).
     * Dự phòng dao động lớn và dự phòng toán học.
   - Thẩm định bảo hiểm, quyền từ chối, thời gian cân nhắc (Free-look 21 ngày).
4. **Lưu trữ SQLite WAL**: Bảng `insurance_licenses`, `insurance_policies`, `solvency_audits`, `claims_settlements`, `actuarial_reserves` tại `.mekong/insurance.db`.

---

## CLI Invocations

```bash
# Báo cáo tổng quan telemetry thị trường bảo hiểm
mekong insurance

# Cấp phép hoạt động doanh nghiệp bảo hiểm theo Luật Kinh doanh bảo hiểm 2022
mekong insurance license "Tổng Công ty Cổ phần Bảo hiểm Bảo Việt" "0100111761" --type NON_LIFE_INSURANCE --capital 400000000000

# Thẩm định và phát hành hợp đồng bảo hiểm (Underwrite Policy)
mekong insurance policy "Tập đoàn Vingroup" MOTOR_VEHICLE --sum-insured 2000000000 --premium 30000000 --deductible 5000000 --term-months 12

# Kiểm tra biên khả năng thanh toán & tỷ lệ an toàn vốn (Solvency Audit)
mekong insurance solvency "Bảo hiểm Bảo Việt" --actual-margin 1200000000000 --net-premium 3000000000000 --avg-claims 1500000000000

# Giải quyết bồi thường tổn thất bảo hiểm (Claims Settlement)
mekong insurance claim POL-MV-010011 "Va chạm giao thông xe tải gây hỏng đầu kéo" 45000000 --is-approved

# Trích lập dự phòng nghiệp vụ kỹ thuật (Technical Reserves)
mekong insurance reserve "Bảo hiểm Bảo Việt" MOTOR_VEHICLE --written-premium 50000000000 --unearned-ratio 0.45 --outstanding-claims 8000000000

# Tra cứu danh mục nghiệp vụ bảo hiểm
mekong insurance list licenses
mekong insurance list policies
mekong insurance list solvency
mekong insurance list claims
mekong insurance list reserves

# Báo cáo telemetry chi tiết định dạng JSON
mekong insurance status --json
```

---

## MCP Tools Integration

| Tool Name | Engine Method | Mục Tiêu & Mô Tả Nghiệp Vụ |
|---|---|---|
| `mekong_insurance_license` | `issue_insurer_license` | Thẩm định điều kiện vốn pháp định và cấp phép doanh nghiệp bảo hiểm theo Luật Kinh doanh bảo hiểm 2022. |
| `mekong_insurance_policy` | `underwrite_policy` | Thẩm định rủi ro, biểu phí, mức khấu trừ và phát hành đơn hợp đồng bảo hiểm. |
| `mekong_insurance_solvency` | `audit_solvency_margin` | Kiểm tra biên khả năng thanh toán tối thiểu và tỷ lệ an toàn vốn luật định (Bộ Tài chính). |
| `mekong_insurance_claim` | `settle_claim` | Xử lý giám định tổn thất, khấu trừ mức miễn thường và chi trả bồi thường bảo hiểm. |
| `mekong_insurance_reserve` | `calculate_technical_reserves` | Tính toán trích lập dự phòng phí chưa được hưởng (UPR), dự phòng bồi thường (OCR, IBNR). |
| `mekong_insurance_list` | `list_*` | Tra cứu dữ liệu giấy phép, hợp đồng, an toàn vốn, khiếu nại bồi thường và dự phòng. |
| `mekong_insurance_status` | `get_status` | Báo cáo telemetry an toàn vốn, quy mô thị trường bảo hiểm và tỷ lệ chi trả bồi thường. |
