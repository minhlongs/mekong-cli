---
name: banking
description: Vietnamese Commercial Banking, Credit Institutions, Underwriting, Basel II CAR & CIC Suite.
---

# mekong banking — Autonomous Vietnamese Commercial Banking, Credit Institutions & Basel II/III Suite

## Căn Cứ Pháp Lý & Chuẩn Mực Nghiệp Vụ
1. **Luật Các tổ chức tín dụng 2024 (Luật số 32/2024/QH15)**:
   - Quy định về thành lập, tổ chức, hoạt động, can thiệp sớm, kiểm soát đặc biệt và phá sản tổ chức tín dụng.
   - Thẩm quyền quản lý nhà nước: **Ngân hàng Nhà nước Việt Nam (NHNN - State Bank of Vietnam - SBV)**.
   - **Mức vốn pháp định tối thiểu (Nghị định 86/2019/NĐ-CP & Luật Các TCTD 2024)**:
     * Ngân hàng thương mại (NHTM): $\ge 3,000,000,000,000\text{ VND}$ (3,000 tỷ VND).
     * Ngân hàng chính sách: $\ge 5,000,000,000,000\text{ VND}$ (5,000 tỷ VND).
     * Công ty tài chính: $\ge 500,000,000,000\text{ VND}$ (500 tỷ VND).
     * Công ty cho thuê tài chính: $\ge 150,000,000,000\text{ VND}$ (150 tỷ VND).
     * Chi nhánh ngân hàng nước ngoài: $\ge 15,000,000\text{ USD}$ (tương đương $\sim 375\text{ tỷ VND}$).
2. **Giới hạn cấp tín dụng & tập trung rủi ro (Điều 136 Luật Các TCTD 2024)**:
   - Dư nợ cấp tín dụng tối đa đối với **một khách hàng**: không vượt quá **14% vốn tự có** của ngân hàng thương mại (lộ trình giảm dần từ 14% năm 2024 xuống 10% năm 2029).
   - Dư nợ cấp tín dụng tối đa đối với **một khách hàng và người có liên quan**: không vượt quá **23% vốn tự có** (lộ trình giảm dần từ 23% xuống 15%).
3. **Thông tư số 41/2016/TT-NHNN về Tỷ lệ An toàn Vốn (CAR Basel II)**:
   - Tỷ lệ an toàn vốn (Capital Adequacy Ratio):
     $$\text{CAR} = \frac{\text{Vốn tự có (Tier 1 + Tier 2)}}{\text{Tổng tài sản có rủi ro (RWA tín dụng + thị trường + hoạt động)}} \ge 8.0\%$$
   - Phân loại: $\ge 12.0\%$ (Vững mạnh), $8.0\% - 12.0\%$ (Đạt chuẩn luật định), $6.0\% - 8.0\%$ (Can thiệp sớm), $< 6.0\%$ (Kiểm soát đặc biệt).
4. **Thông tư số 11/2021/TT-NHNN về Phân loại nợ CIC & Trích lập dự phòng rủi ro**:
   - **Nhóm 1 (Nợ đủ tiêu chuẩn)**: Quá hạn $< 10$ ngày $\rightarrow$ Dự phòng cụ thể: $0\%$.
   - **Nhóm 2 (Nợ cần chú ý)**: Quá hạn từ 10 đến 90 ngày $\rightarrow$ Dự phòng cụ thể: $5\%$.
   - **Nhóm 3 (Nợ dưới tiêu chuẩn - NPL)**: Quá hạn từ 91 đến 180 ngày $\rightarrow$ Dự phòng cụ thể: $20\%$.
   - **Nhóm 4 (Nợ nghi ngờ - NPL)**: Quá hạn từ 181 đến 360 ngày $\rightarrow$ Dự phòng cụ thể: $50\%$.
   - **Nhóm 5 (Nợ có khả năng mất vốn - NPL)**: Quá hạn $> 360$ ngày $\rightarrow$ Dự phòng cụ thể: $100\%$.
   - **Dự phòng chung (General Provision)**: $0.75\%$ trên tổng số dư nợ từ Nhóm 1 đến Nhóm 4.
   - Nợ xấu (NPL): Bao gồm Nhóm 3, Nhóm 4, Nhóm 5.
5. **Thông tư số 22/2019/TT-NHNN về Giới hạn thanh khoản**:
   - Tỷ lệ dư nợ cho vay so với tổng tiền gửi (LDR): tối đa $85\%$.
   - Tỷ lệ tối đa của nguồn vốn ngắn hạn được sử dụng để cho vay trung và dài hạn: tối đa $30\%$.
6. **Lưu trữ SQLite WAL**: Bảng `banking_licenses`, `credit_facilities`, `car_audits`, `debt_classifications`, `liquidity_audits` tại `.mekong/banking.db`.

---

## CLI Invocations

```bash
# Báo cáo tổng quan telemetry hệ thống ngân hàng, an toàn vốn và nợ xấu
mekong banking

# Thẩm tra vốn pháp định và cấp giấy phép thành lập TCTD (Luật Các TCTD 2024)
mekong banking license "Ngân hàng TMCP Phát triển Mekong" --type COMMERCIAL_BANK --capital 3500000000000 --tax-id "0108877112" --address "Tòa nhà Mekong, Hà Nội"

# Thẩm định hạn mức tín dụng và giới hạn rủi ro 14% vốn tự có (Điều 136)
mekong banking credit "Tập đoàn Nông nghiệp Mekong" "0109988776" 1500000000000 --rate 8.5 --term 24 --collateral REAL_ESTATE --value 2500000000000 --bank-equity 20000000000000

# Kiểm tra Tỷ lệ an toàn vốn CAR theo chuẩn mực Basel II (Thông tư 41/2016)
mekong banking car "Ngân hàng TMCP Mekong" 20000000000000 5000000000000 180000000000000 10000000000000 10000000000000 --quarter Q3/2026

# Phân loại 5 nhóm nợ CIC và tính trích lập dự phòng rủi ro (Thông tư 11/2021)
mekong banking debt "HDTD-2026-MK001" "Công ty TNHH Vận tải Sông Tiền" 5000000000 --overdue 45 --collateral 3000000000

# Thẩm tra giới hạn an toàn thanh khoản LDR (<=85%) và vốn ngắn hạn cho vay trung dài hạn (<=30%)
mekong banking liquidity "Ngân hàng TMCP Mekong" 150000000000000 190000000000000 100000000000000 25000000000000

# Tra cứu dữ liệu ngân hàng, tín dụng, an toàn vốn CAR, phân loại nợ
mekong banking list --type licenses
mekong banking list --type credit
mekong banking list --type car
mekong banking list --type debt
mekong banking list --type liquidity

# Xuất báo cáo trạng thái hệ thống định dạng JSON
mekong banking status --json
```

---

## MCP Tools Integration

| Tool Name | Engine Method | Mục Tiêu & Mô Tả Nghiệp Vụ |
|---|---|---|
| `mekong_banking_license` | `license_institution` | Thẩm tra vốn pháp định và cấp giấy phép thành lập tổ chức tín dụng theo Luật Các TCTD 2024. |
| `mekong_banking_credit` | `underwrite_credit` | Thẩm định khoản tín dụng, kiểm tra giới hạn tập trung rủi ro 14% vốn tự có và định giá LTV TSBĐ. |
| `mekong_banking_car` | `audit_capital_adequacy` | Kiểm tra tỷ lệ an toàn vốn CAR theo chuẩn mực Basel II (Thông tư 41/2016/TT-NHNN). |
| `mekong_banking_debt` | `classify_credit_debt` | Phân loại 5 nhóm nợ CIC, phát hiện nợ xấu NPL và trích lập dự phòng rủi ro cụ thể + chung. |
| `mekong_banking_liquidity` | `audit_liquidity_ratios` | Thẩm tra giới hạn an toàn thanh khoản: LDR tối đa 85% và vốn ngắn hạn cho vay trung dài hạn tối đa 30%. |
| `mekong_banking_list` | `list_*` | Tra cứu danh mục giấy phép ngân hàng, khoản cấp tín dụng, đợt kiểm tra CAR, phân loại nợ CIC. |
| `mekong_banking_status` | `get_status` | Báo cáo telemetry tổng hợp hoạt động ngân hàng, an toàn vốn Basel II và rủi ro tín dụng. |
